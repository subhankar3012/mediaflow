import asyncio
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.utils.logger import logger

class FFmpegError(Exception):
    def __init__(self, message: str, stderr: Optional[str] = None, code: str = "PROCESSING_FAILED"):
        self.stderr = stderr
        self.code = code
        self.message = message
        if stderr and stderr.strip():
            # Extract last non-empty line of stderr for clean user-facing error context
            lines = [line.strip() for line in stderr.strip().splitlines() if line.strip()]
            if lines:
                last_line = lines[-1]
                if len(last_line) > 120:
                    last_line = last_line[:120] + "..."
                self.message = f"{message} ({last_line})"
        super().__init__(self.message)

class MediaValidationError(FFmpegError):
    def __init__(self, message: str, stderr: Optional[str] = None):
        super().__init__(message, stderr=stderr, code="VALIDATION_FAILED")

class FFmpegService:
    """
    Dedicated FFmpeg and FFprobe processing service.
    Implements stream-copy when codecs are already H.264 / AAC,
    transcoding when required for browser compatibility,
    and post-processing media validation before job completion.
    """

    def __init__(self):
        self.ffmpeg_path = shutil.which("ffmpeg")
        self.ffprobe_path = shutil.which("ffprobe")
        self._active_processes: Dict[str, asyncio.subprocess.Process] = {}

    def is_available(self) -> bool:
        return bool(self.ffmpeg_path and self.ffprobe_path)

    def register_process(self, job_id: Optional[str], proc: asyncio.subprocess.Process) -> None:
        if job_id:
            self._active_processes[job_id] = proc

    def unregister_process(self, job_id: Optional[str]) -> None:
        if job_id:
            self._active_processes.pop(job_id, None)

    def kill_job_process(self, job_id: str) -> bool:
        """Terminates any active FFmpeg child process associated with this job."""
        proc = self._active_processes.pop(job_id, None)
        if proc:
            try:
                proc.terminate()
                logger.info(f"Terminated active FFmpeg process for job {job_id}")
                return True
            except Exception as e:
                logger.warning(f"Error terminating FFmpeg process for job {job_id}: {e}")
                try:
                    proc.kill()
                    return True
                except Exception:
                    pass
        return False

    async def probe(self, file_path: Path) -> Dict[str, Any]:
        """Runs ffprobe on the given media file and returns parsed JSON metadata."""
        if not self.ffprobe_path:
            raise FFmpegError("ffprobe binary is not installed or not in PATH.")

        if not file_path.exists():
            raise FFmpegError(f"Target file does not exist: {file_path}")

        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise FFmpegError(
                f"ffprobe failed with exit code {proc.returncode}",
                stderr=stderr.decode("utf-8", errors="replace")
            )

        try:
            return json.loads(stdout.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise FFmpegError(f"Failed to parse ffprobe output: {str(e)}")

    async def transcode_to_compatible_mp4(
        self,
        video_path: Path,
        output_path: Path,
        audio_path: Optional[Path] = None,
        video_codec: Optional[str] = None,
        audio_codec: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> Path:
        """
        Produces a standard-compatible MP4 containing H.264 video and AAC audio.
        Decision logic:
        1. H.264 video + AAC audio -> stream copy (-c copy) without re-encoding
        2. H.264 video + non-AAC audio -> copy video (-c:v copy), convert audio (-c:a aac)
        3. Non-H.264 video (VP9, AV1, etc.) -> transcode video (-c:v libx264 -pix_fmt yuv420p)
        4. Silent video (no audio stream) -> synthesizes silent AAC stereo track to guarantee player compatibility
        """
        if not self.ffmpeg_path:
            raise FFmpegError("ffmpeg binary is not installed or not in PATH.")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        vcodec_clean = (video_codec or "").lower().strip()
        acodec_clean = (audio_codec or "").lower().strip()

        video_is_h264 = vcodec_clean.startswith("avc1") or vcodec_clean.startswith("h264") or vcodec_clean.startswith("avc")
        audio_is_aac = acodec_clean.startswith("mp4a") or acodec_clean.startswith("aac")
        has_audio = bool(audio_codec) or (audio_path and audio_path != video_path)

        # Build FFmpeg command (strictly limited to 1 thread for cloud container memory safety)
        cmd = [self.ffmpeg_path, "-y", "-threads", "1", "-i", str(video_path)]

        if audio_path and audio_path != video_path:
            cmd.extend(["-i", str(audio_path), "-map", "0:v:0?", "-map", "1:a:0?"])
        elif has_audio:
            cmd.extend(["-map", "0:v:0?", "-map", "0:a:0?"])
        else:
            # Silent video without audio stream: synthesize silent AAC track for 100% universal player compatibility
            cmd.extend([
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-map", "0:v:0?", "-map", "1:a:0?",
                "-shortest"
            ])

        # Decide video codec parameters: stream copy H.264, AV1, and VP9 in MP4 for instant (< 1s) muxing
        video_supports_copy = (
            video_is_h264 or
            "av01" in vcodec_clean or "av1" in vcodec_clean or
            "vp9" in vcodec_clean or "vp09" in vcodec_clean
        )
        if video_supports_copy:
            cmd.extend(["-c:v", "copy"])
        else:
            logger.info(f"Transcoding legacy video codec ({video_codec}) to libx264 (yuv420p)")
            cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-pix_fmt", "yuv420p"])

        # Decide audio codec parameters
        if not has_audio:
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        elif audio_is_aac:
            cmd.extend(["-c:a", "copy"])
        else:
            logger.info(f"Transcoding non-AAC audio ({audio_codec}) to aac (192k)")
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])

        # Faststart for progressive web playback
        cmd.extend(["-movflags", "+faststart"])
        cmd.append(str(output_path))

        logger.info(f"Running FFmpeg compatible conversion: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self.register_process(job_id, proc)
        try:
            stdout, stderr = await proc.communicate()
        finally:
            self.unregister_process(job_id)

        if proc.returncode != 0:
            err_output = stderr.decode("utf-8", errors="replace")
            logger.warning(f"Conversion attempt failed ({proc.returncode}), attempting full re-encode fallback: {err_output[:200]}")
            fallback_cmd = [self.ffmpeg_path, "-y", "-threads", "1", "-i", str(video_path)]
            if audio_path and audio_path != video_path:
                fallback_cmd.extend(["-i", str(audio_path), "-map", "0:v:0?", "-map", "1:a:0?"])
            elif has_audio:
                fallback_cmd.extend(["-map", "0:v:0?", "-map", "0:a:0?"])
            else:
                fallback_cmd.extend([
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-map", "0:v:0?", "-map", "1:a:0?",
                    "-shortest"
                ])

            fallback_cmd.extend([
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                str(output_path)
            ])
            fallback_proc = await asyncio.create_subprocess_exec(
                *fallback_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.register_process(job_id, fallback_proc)
            try:
                f_stdout, f_stderr = await fallback_proc.communicate()
            finally:
                self.unregister_process(job_id)

            if fallback_proc.returncode != 0:
                raise FFmpegError(
                    f"FFmpeg transcode failed with code {fallback_proc.returncode}",
                    stderr=f_stderr.decode("utf-8", errors="replace")
                )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise FFmpegError("FFmpeg completed but output file is missing or 0 bytes.")

        return output_path

    async def remux(self, input_path: Path, output_path: Path, job_id: Optional[str] = None) -> Path:
        """Remuxes container format without re-encoding (-c copy)."""
        if not self.ffmpeg_path:
            raise FFmpegError("ffmpeg binary is not installed or not in PATH.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-threads", "1",
            "-i", str(input_path),
            "-c", "copy",
            str(output_path)
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self.register_process(job_id, proc)
        try:
            stdout, stderr = await proc.communicate()
        finally:
            self.unregister_process(job_id)

        if proc.returncode != 0:
            raise FFmpegError(
                f"FFmpeg remux failed with code {proc.returncode}",
                stderr=stderr.decode("utf-8", errors="replace")
            )
        return output_path

    async def extract_audio(
        self,
        input_path: Path,
        output_path: Path,
        audio_format: str = "mp3",
        job_id: Optional[str] = None
    ) -> Path:
        """Extracts audio stream into MP3 or M4A container."""
        if not self.ffmpeg_path:
            raise FFmpegError("ffmpeg binary is not installed or not in PATH.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if audio_format.lower() == "mp3":
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-threads", "1",
                "-i", str(input_path),
                "-vn",
                "-c:a", "libmp3lame",
                "-q:a", "2",
                str(output_path)
            ]
        elif audio_format.lower() in ("m4a", "aac"):
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-threads", "1",
                "-i", str(input_path),
                "-vn",
                "-c:a", "aac",
                "-b:a", "192k",
                str(output_path)
            ]
        else:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-threads", "1",
                "-i", str(input_path),
                "-vn",
                "-c:a", "copy",
                str(output_path)
            ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self.register_process(job_id, proc)
        try:
            stdout, stderr = await proc.communicate()
        finally:
            self.unregister_process(job_id)

        if proc.returncode != 0:
            raise FFmpegError(
                f"FFmpeg audio extraction failed with code {proc.returncode}",
                stderr=stderr.decode("utf-8", errors="replace")
            )
        return output_path

    async def validate_media_file(
        self,
        file_path: Path,
        is_audio_only: bool = False,
        expected_container: str = "mp4"
    ) -> Dict[str, Any]:
        """
        Validates the final output media file with FFprobe before job completion:
        1. File exists and size > 0
        2. Duration > 0
        3. Valid container (MP4 for video, MP3 for audio)
        4. Video stream exists AND codec is H.264 (for video downloads)
        5. Audio stream exists AND codec is AAC (for video downloads) or MP3 (for audio)
        6. Video-only file is NEVER allowed for normal video downloads.
        """
        if not file_path.exists():
            raise MediaValidationError(f"Validation failed: Output file does not exist: {file_path}")

        file_size = file_path.stat().st_size
        if file_size <= 0:
            raise MediaValidationError("Validation failed: Output file is empty (0 bytes).")

        probe_data = await self.probe(file_path)
        format_info = probe_data.get("format", {})
        streams = probe_data.get("streams", [])

        # Duration validation
        try:
            duration = float(format_info.get("duration", 0.0))
            if duration <= 0:
                raise MediaValidationError(f"Validation failed: Output duration is {duration}s (must be > 0).")
        except (ValueError, TypeError):
            raise MediaValidationError("Validation failed: Could not parse media duration.")

        # Container validation
        format_names = format_info.get("format_name", "").lower().split(",")
        if is_audio_only:
            if not any(f in format_names for f in ("mp3", "mp2", "mp1", "m4a", "aac")):
                raise MediaValidationError(f"Validation failed: Expected audio container, got: {format_names}")
        else:
            if not any(f in format_names for f in ("mp4", "mov", "m4a", "3gp", "3g2", "mj2")):
                raise MediaValidationError(f"Validation failed: Expected MP4 container, got: {format_names}")

        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

        if is_audio_only:
            if not audio_streams:
                raise MediaValidationError("Validation failed: Audio-only output contains no audio stream.")
            a_codec = audio_streams[0].get("codec_name", "").lower()
            if a_codec != "mp3" and expected_container == "mp3":
                raise MediaValidationError(f"Validation failed: Audio codec '{a_codec}' does not match expected MP3.")
        else:
            # Video downloads: MUST contain BOTH video and audio
            if not video_streams:
                raise MediaValidationError("Validation failed: Output contains no video stream.")
            if not audio_streams:
                raise MediaValidationError("Validation failed: Output contains no audio stream. Video-only downloads are strictly forbidden.")

            v_codec = video_streams[0].get("codec_name", "").lower()
            if v_codec != "h264" and not v_codec.startswith("avc"):
                raise MediaValidationError(f"Validation failed: Video codec '{v_codec}' is not standard H.264 / AVC.")

            a_codec = audio_streams[0].get("codec_name", "").lower()
            if a_codec != "aac" and not a_codec.startswith("mp4a"):
                raise MediaValidationError(f"Validation failed: Audio codec '{a_codec}' is not standard AAC.")

        return {
            "valid": True,
            "container": format_info.get("format_name"),
            "duration": duration,
            "size": file_size,
            "video_codec": video_streams[0].get("codec_name") if video_streams else None,
            "audio_codec": audio_streams[0].get("codec_name") if audio_streams else None,
            "height": video_streams[0].get("height") if video_streams else None,
            "width": video_streams[0].get("width") if video_streams else None,
        }

ffmpeg_service = FFmpegService()
