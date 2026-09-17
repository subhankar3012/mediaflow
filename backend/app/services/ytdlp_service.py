import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from app.config import settings
from app.schemas.format import NormalizedFormat, MediaType
from app.utils.logger import logger

class YtDlpError(Exception):
    def __init__(self, message: str, code: str = "DOWNLOAD_ERROR"):
        super().__init__(message)
        self.code = code
        self.message = message

class YtDlpService:
    """
    Encapsulates yt-dlp Python API.
    Isolates extraction, normalization, and downloading logic.
    """

    @staticmethod
    def _get_cookiefile() -> Optional[str]:
        """Resolves active cookies file from environment variable, explicit path, or default location."""
        # 1. Plaintext cookies provided via YTDLP_COOKIES environment variable
        if getattr(settings, "YTDLP_COOKIES", None) and settings.YTDLP_COOKIES.strip():
            cookie_path = os.path.join(tempfile.gettempdir(), "ytdlp_cookies.txt")
            try:
                with open(cookie_path, "w", encoding="utf-8") as f:
                    f.write(settings.YTDLP_COOKIES.strip())
                return cookie_path
            except Exception as e:
                logger.warning(f"Failed to write YTDLP_COOKIES env var to file: {e}")

        # 2. Explicit path specified via YTDLP_COOKIES_PATH
        if getattr(settings, "YTDLP_COOKIES_PATH", None) and settings.YTDLP_COOKIES_PATH:
            if os.path.exists(settings.YTDLP_COOKIES_PATH):
                return settings.YTDLP_COOKIES_PATH

        # 3. Default fallback paths
        default_paths = [
            os.path.join(os.getcwd(), "cookies.txt"),
            os.path.join(os.path.dirname(__file__), "..", "..", "cookies.txt"),
            "/tmp/downloader/cookies.txt",
        ]
        for p in default_paths:
            if os.path.exists(p) and os.path.getsize(p) > 0:
                return p

        return None

    @staticmethod
    def _format_bytes(size: Optional[int]) -> str:
        if not size or size <= 0:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @staticmethod
    def _format_speed(speed_bytes: Optional[float]) -> Optional[str]:
        if not speed_bytes or speed_bytes <= 0:
            return None
        return f"{YtDlpService._format_bytes(int(speed_bytes))}/s"

    @staticmethod
    def _format_eta(seconds: Optional[int]) -> Optional[str]:
        if seconds is None or seconds < 0:
            return None
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    @staticmethod
    def _select_best_thumbnail(info: Dict[str, Any]) -> Optional[str]:
        """
        Ranks available thumbnails to select the highest-quality appropriate thumbnail.
        Prioritizes (width * height), then preference score.
        """
        thumbnails = info.get("thumbnails")
        if not thumbnails:
            return info.get("thumbnail")

        def thumb_key(t: Dict[str, Any]):
            w = t.get("width") or 0
            h = t.get("height") or 0
            pref = t.get("preference") or 0
            url = t.get("url") or ""
            is_compat = 1 if (url.endswith(".jpg") or url.endswith(".jpeg") or url.endswith(".png")) else 0
            return (w * h, pref, is_compat)

        sorted_thumbs = sorted(thumbnails, key=thumb_key, reverse=True)
        for t in sorted_thumbs:
            u = t.get("url")
            if u and u.startswith("http"):
                return u
        return info.get("thumbnail")

    def normalize_format(self, raw_fmt: Dict[str, Any]) -> Optional[NormalizedFormat]:
        """Converts a raw yt-dlp format dictionary into a clean NormalizedFormat."""
        format_id = str(raw_fmt.get("format_id", ""))
        if not format_id:
            return None

        vcodec = raw_fmt.get("vcodec")
        acodec = raw_fmt.get("acodec")
        ext = raw_fmt.get("ext", "mp4")

        has_video = bool(vcodec and vcodec.lower() != "none")
        has_audio = bool(acodec and acodec.lower() != "none")

        if not has_video and not has_audio:
            return None

        if has_video and has_audio:
            media_type: MediaType = "video+audio"
        elif has_video:
            media_type = "video"
        else:
            media_type = "audio"

        width = raw_fmt.get("width")
        height = raw_fmt.get("height")
        fps = raw_fmt.get("fps")
        tbr = raw_fmt.get("tbr") or raw_fmt.get("vbr") or raw_fmt.get("abr")
        filesize = raw_fmt.get("filesize")
        filesize_approx = raw_fmt.get("filesize_approx")
        format_note = raw_fmt.get("format_note") or raw_fmt.get("resolution")

        return NormalizedFormat(
            format_id=format_id,
            type=media_type,
            container=ext,
            width=int(width) if width else None,
            height=int(height) if height else None,
            fps=float(fps) if fps else None,
            vcodec=vcodec if vcodec != "none" else None,
            acodec=acodec if acodec != "none" else None,
            bitrate=float(tbr) if tbr else None,
            has_audio=has_audio,
            has_video=has_video,
            filesize=filesize,
            filesize_approx=filesize_approx,
            format_note=str(format_note) if format_note else None
        )

    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extracts metadata and formats without downloading media.
        Synchronous method intended to run within an executor.
        """
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "socket_timeout": 20,
            "no_color": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["visionos", "android"]
                }
            },
        }

        cookiefile = self._get_cookiefile()
        if cookiefile:
            ydl_opts["cookiefile"] = cookiefile

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise YtDlpError("Could not retrieve media info.", code="EXTRACTION_FAILED")

                # If playlist or multi-entry, take first entry
                if "_type" in info and info["_type"] == "playlist" and "entries" in info:
                    entries = list(info.get("entries", []))
                    if not entries:
                        raise YtDlpError("Playlist is empty.", code="EMPTY_PLAYLIST")
                    info = entries[0]

                raw_formats = info.get("formats", [])
                normalized_formats: List[NormalizedFormat] = []
                seen_format_ids = set()

                for raw_fmt in raw_formats:
                    norm = self.normalize_format(raw_fmt)
                    if norm and norm.format_id not in seen_format_ids:
                        seen_format_ids.add(norm.format_id)
                        normalized_formats.append(norm)

                # Sort formats: video+audio first, then highest resolution, then highest bitrate
                normalized_formats.sort(
                    key=lambda f: (
                        1 if f.type == "video+audio" else (2 if f.type == "video" else 3),
                        -(f.height or 0),
                        -(f.bitrate or 0)
                    )
                )

                return {
                    "source_url": url,
                    "title": info.get("title") or "Untitled Media",
                    "thumbnail": self._select_best_thumbnail(info),
                    "duration": int(info.get("duration", 0)) if info.get("duration") else None,
                    "uploader": info.get("uploader") or info.get("channel") or info.get("uploader_id"),
                    "raw_formats": raw_formats,
                    "formats": normalized_formats,
                }
        except yt_dlp.utils.DownloadError as e:
            err_str = str(e)
            if ("Private video" in err_str or "Sign in" in err_str) and "confirm you're not a bot" not in err_str and "bot" not in err_str.lower():
                raise YtDlpError("Media is private or requires authentication.", code="AUTHENTICATION_REQUIRED")
            elif "Video unavailable" in err_str:
                raise YtDlpError("Media is unavailable or was removed.", code="MEDIA_UNAVAILABLE")
            elif "Geo-restricted" in err_str:
                raise YtDlpError("Media is restricted in this region.", code="GEO_RESTRICTED")
            else:
                raise YtDlpError(f"Extraction error: {err_str}", code="DOWNLOAD_ERROR")
        except Exception as e:
            if isinstance(e, YtDlpError):
                raise
            logger.exception("Unexpected error during yt-dlp metadata extraction")
            raise YtDlpError(f"Unexpected extraction failure: {str(e)}", code="INTERNAL_ERROR")

    async def extract_metadata_async(self, url: str) -> Dict[str, Any]:
        """Asynchronous wrapper for extract_metadata."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.extract_metadata, url)

    def download_media(
        self,
        url: str,
        format_spec: str,
        output_template: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancellation_event: Optional[Any] = None
    ) -> str:
        """
        Downloads the specified format using yt-dlp.
        Synchronous execution inside worker thread/executor with active cancellation support.
        """
        import yt_dlp

        def _hook(d: Dict[str, Any]):
            if cancellation_event and cancellation_event.is_set():
                raise yt_dlp.utils.DownloadCancelled("Download cancelled by user or timeout")

            if not progress_callback:
                return

            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                speed = d.get("speed")
                eta = d.get("eta")

                pct = (downloaded / total * 100.0) if total > 0 else 0.0

                progress_callback({
                    "status": "downloading",
                    "progress": round(min(pct, 99.9), 1),
                    "downloaded_bytes": downloaded,
                    "total_bytes": total,
                    "speed": self._format_speed(speed),
                    "eta": self._format_eta(eta),
                })
            elif status == "finished":
                total = d.get("total_bytes") or d.get("downloaded_bytes") or 0
                progress_callback({
                    "status": "finished",
                    "progress": 100.0,
                    "downloaded_bytes": total,
                    "total_bytes": total,
                    "speed": None,
                    "eta": "00:00",
                })

        ydl_opts = {
            "format": format_spec,
            "outtmpl": output_template,
            "progress_hooks": [_hook],
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "retries": 10,
            "fragment_retries": 10,
            "continuedl": True,
            "no_color": True,
            # Prevent automatic merge here so FFmpegService manages post-processing explicitly
            "nopostoverwrites": True,
            "buffersize": 1024 * 1024,  # 1MB buffer ceiling
            "http_chunk_size": 5 * 1024 * 1024,  # 5MB download chunks
            "extractor_args": {
                "youtube": {
                    "player_client": ["visionos", "android"]
                }
            },
        }

        cookiefile = self._get_cookiefile()
        if cookiefile:
            ydl_opts["cookiefile"] = cookiefile

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if cancellation_event and cancellation_event.is_set():
                    raise YtDlpError("Download was cancelled.", code="CANCELLED")
                downloaded_file = ydl.prepare_filename(info)
                return downloaded_file
        except yt_dlp.utils.DownloadCancelled:
            raise YtDlpError("Download was cancelled.", code="CANCELLED")
        except yt_dlp.utils.DownloadError as e:
            if cancellation_event and cancellation_event.is_set():
                raise YtDlpError("Download was cancelled.", code="CANCELLED")
            raise YtDlpError(f"Download failed: {str(e)}", code="DOWNLOAD_FAILED")
        except Exception as e:
            if isinstance(e, YtDlpError):
                raise
            if cancellation_event and cancellation_event.is_set():
                raise YtDlpError("Download was cancelled.", code="CANCELLED")
            raise YtDlpError(f"Unexpected download error: {str(e)}", code="INTERNAL_ERROR")

    async def download_media_async(
        self,
        url: str,
        format_spec: str,
        output_template: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancellation_event: Optional[Any] = None
    ) -> str:
        """Asynchronous wrapper for download_media."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.download_media,
            url,
            format_spec,
            output_template,
            progress_callback,
            cancellation_event
        )

ytdlp_service = YtDlpService()
