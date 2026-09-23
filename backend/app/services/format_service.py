from typing import Dict, Any, List, Optional
from app.schemas.format import NormalizedFormat
from app.utils.logger import logger

STANDARD_HEIGHTS = [2160, 1440, 1080, 720, 480, 360]
SUB_TIER_HEIGHTS = [240, 144]
ALL_KNOWN_HEIGHTS = [2160, 1440, 1080, 720, 480, 360, 240, 144]

def is_h264(vcodec: Optional[str]) -> bool:
    """Checks whether the video codec identifier is H.264 / AVC."""
    if not vcodec or vcodec.lower() == "none":
        return False
    vc = vcodec.lower()
    return vc.startswith("avc1") or vc.startswith("h264") or vc.startswith("avc")

def is_aac(acodec: Optional[str]) -> bool:
    """Checks whether the audio codec identifier is AAC."""
    if not acodec or acodec.lower() == "none":
        return False
    ac = acodec.lower()
    return ac.startswith("mp4a") or ac.startswith("aac")

class FormatNormalizer:
    """
    Normalizes raw yt-dlp extracted formats into consumer-facing quality options.
    Enforces resolution grouping, deduplication, and H.264 / AAC compatibility policy.
    """

    @staticmethod
    def map_to_standard_height(raw_height: Optional[int]) -> Optional[int]:
        """
        Maps raw height to standard resolution if within standard bounds.
        Prevents fabricating missing resolutions while handling aspect ratios (e.g. 1072 -> 1080).
        """
        if not raw_height or raw_height <= 0:
            return None
        
        for std in ALL_KNOWN_HEIGHTS:
            # Within 4% tolerance (e.g. 1080 vs 1072 or 720 vs 718)
            if abs(raw_height - std) <= (std * 0.04):
                return std
        
        # If it matches an exact known height
        if raw_height in ALL_KNOWN_HEIGHTS:
            return raw_height
            
        return raw_height

    @staticmethod
    def rank_video_format(fmt: Dict[str, Any]) -> float:
        """
        Ranks video format candidates at a specific resolution.
        Priority:
        1. H.264 / AVC video codec (+10,000)
        2. MP4 container (+2,000)
        3. Combined video+audio with AAC (+1,000)
        4. Higher bitrate (tbr/vbr)
        5. Higher fps
        """
        score = 0.0
        vcodec = fmt.get("vcodec") or ""
        acodec = fmt.get("acodec") or ""
        ext = fmt.get("ext") or ""

        if is_h264(vcodec):
            score += 10000.0
        elif "av01" in vcodec.lower() or "av1" in vcodec.lower():
            score += 2000.0  # AV1 is preferred by yt-dlp when H.264 is unavailable
        elif "vp9" in vcodec.lower() or "vp09" in vcodec.lower():
            score += 1000.0

        if ext.lower() == "mp4":
            score += 2000.0

        if is_aac(acodec):
            score += 1000.0

        # Bitrate contribution
        tbr = fmt.get("tbr") or fmt.get("vbr") or 0.0
        score += float(tbr)

        # FPS bonus
        fps = fmt.get("fps") or 0.0
        score += float(fps)

        return score

    @staticmethod
    def rank_audio_format(fmt: Dict[str, Any]) -> float:
        """
        Ranks audio format candidates across the source media.
        Priority:
        1. AAC / mp4a audio codec (+10,000)
        2. M4A / MP4 container (+2,000)
        3. Higher bitrate (abr/tbr)
        """
        score = 0.0
        acodec = fmt.get("acodec") or ""
        ext = fmt.get("ext") or ""

        if is_aac(acodec):
            score += 10000.0
        elif "opus" in acodec.lower():
            score += 2000.0

        if ext.lower() in ("m4a", "mp4"):
            score += 2000.0

        abr = fmt.get("abr") or fmt.get("tbr") or 0.0
        score += float(abr)

        return score

    @staticmethod
    def estimate_stream_size(fmt: Optional[Dict[str, Any]], duration: Optional[int] = None) -> Optional[int]:
        """
        Calculates an accurate estimated byte size for a stream.
        1. Exact filesize if provided by yt-dlp
        2. Approximate filesize if provided
        3. Bitrate (kbps) * duration (s) / 8 fallback
        4. None if unavailable (avoids fabricating misleading numbers)
        """
        if not fmt:
            return None

        # 1. Exact filesize
        size = fmt.get("filesize")
        if size and size > 0:
            return int(size)

        # 2. Approximate filesize
        size_approx = fmt.get("filesize_approx")
        if size_approx and size_approx > 0:
            return int(size_approx)

        # 3. Bitrate * duration fallback (tbr, vbr, abr are in kbps)
        bitrate = fmt.get("tbr") or fmt.get("vbr") or fmt.get("abr")
        if bitrate and duration and duration > 0:
            calc_bytes = int((float(bitrate) * 1000.0 / 8.0) * float(duration))
            if calc_bytes > 0:
                return calc_bytes

        return None

    def normalize_formats(
        self,
        raw_formats: List[Dict[str, Any]],
        platform: str = "youtube",
        duration: Optional[int] = None
    ) -> List[NormalizedFormat]:
        """
        Normalizes a raw yt-dlp format list into a clean, deduplicated, consumer-facing list.
        """
        if not raw_formats:
            if platform == "youtube":
                return self._normalize_youtube([], duration=duration)
            return []

        # Platform-specific handling for Instagram
        if platform == "instagram":
            return self._normalize_instagram(raw_formats, duration=duration)

        return self._normalize_youtube(raw_formats, duration=duration)

    def _normalize_instagram(
        self,
        raw_formats: List[Dict[str, Any]],
        duration: Optional[int] = None
    ) -> List[NormalizedFormat]:
        """
        For Instagram: Expose a single unified high-definition video option
        and guarantee video+audio presence.
        """
        best_video = None
        best_video_score = -1.0
        best_audio = None
        best_audio_score = -1.0

        for f in raw_formats:
            vcodec = f.get("vcodec")
            acodec = f.get("acodec")
            has_video = bool(vcodec and vcodec.lower() != "none")
            has_audio = bool(acodec and acodec.lower() != "none")

            if has_video:
                score = self.rank_video_format(f)
                if score > best_video_score:
                    best_video_score = score
                    best_video = f

            if has_audio:
                score = self.rank_audio_format(f)
                if score > best_audio_score:
                    best_audio_score = score
                    best_audio = f

        # Fallback to first available if score ranking found none
        if not best_video and raw_formats:
            best_video = raw_formats[0]

        vid_id = str(best_video.get("format_id", "best")) if best_video else "best"
        aud_id = str(best_audio.get("format_id", "bestaudio")) if best_audio else None

        vid_size = self.estimate_stream_size(best_video, duration) if best_video else None
        aud_size = self.estimate_stream_size(best_audio, duration) if best_audio else None
        combined_size = (vid_size + aud_size) if (vid_size is not None and aud_size is not None) else (vid_size or aud_size)

        inst_format = NormalizedFormat(
            format_id="best",
            type="video+audio",
            container="mp4",
            width=best_video.get("width") if best_video else None,
            height=best_video.get("height") if best_video else None,
            fps=best_video.get("fps") if best_video else None,
            vcodec="h264",
            acodec="aac",
            bitrate=best_video.get("tbr") or best_video.get("vbr") if best_video else None,
            has_audio=True,
            has_video=True,
            filesize=None,
            filesize_approx=combined_size,
            quality="Best Quality",
            format_note="High Definition MP4 with Audio",
            downloadable=True,
            source_video_format_id=vid_id,
            source_audio_format_id=aud_id
        )

        return [inst_format]

    def _normalize_youtube(
        self,
        raw_formats: List[Dict[str, Any]],
        duration: Optional[int] = None
    ) -> List[NormalizedFormat]:
        """
        For YouTube: Group by genuine resolution height, pick the best compatible stream
        for each height, and guarantee all standard consumer tiers.
        """
        # Determine maximum available height from video formats
        max_source_height = 0
        for f in raw_formats:
            vcodec = f.get("vcodec")
            if vcodec and vcodec.lower() != "none":
                h = f.get("height") or 0
                if h > max_source_height:
                    max_source_height = h

        # If source has standard tiers (>= 360p) or empty, only expose standard consumer tiers
        # If source max resolution is lower (e.g. vintage 240p/144p), expose lower tiers
        if max_source_height == 0 or max_source_height >= 360:
            allowed_heights = set(STANDARD_HEIGHTS)
        else:
            allowed_heights = set(ALL_KNOWN_HEIGHTS)

        # 1. Identify all video streams and group by height bucket
        resolution_candidates: Dict[int, List[Dict[str, Any]]] = {}
        all_audio_formats: List[Dict[str, Any]] = []

        for f in raw_formats:
            vcodec = f.get("vcodec")
            acodec = f.get("acodec")
            has_video = bool(vcodec and vcodec.lower() != "none")
            has_audio = bool(acodec and acodec.lower() != "none")

            if has_audio:
                all_audio_formats.append(f)

            if has_video:
                raw_height = f.get("height")
                std_height = self.map_to_standard_height(raw_height)
                if std_height and std_height in allowed_heights:
                    resolution_candidates.setdefault(std_height, []).append(f)

        # Guarantee all standard consumer tiers (1080p, 720p, 480p, 360p) for YouTube videos.
        # YouTube videos are modern HD media. Even when cloud/datacenter IP throttling initially omits
        # DASH manifests, we guarantee consumer tiers so users can choose 1080p, 720p, 480p, or 360p.
        # During download, the worker requests bestvideo[height<=h]+bestaudio and FFmpeg produces the tier.
        standard_tiers = [1080, 720, 480, 360]
        for tier in standard_tiers:
            if tier not in resolution_candidates:
                higher = [cand_h for cand_h in resolution_candidates.keys() if cand_h > tier]
                if higher:
                    source_h = min(higher)
                    resolution_candidates[tier] = list(resolution_candidates[source_h])
                elif resolution_candidates:
                    max_h = max(resolution_candidates.keys())
                    resolution_candidates[tier] = list(resolution_candidates[max_h])
                elif raw_formats:
                    resolution_candidates[tier] = [raw_formats[0]]
                else:
                    resolution_candidates[tier] = [{
                        "format_id": f"{tier}p",
                        "ext": "mp4",
                        "vcodec": "avc1",
                        "acodec": "mp4a",
                        "height": tier,
                        "width": int(tier * 16 / 9),
                        "fps": 30,
                    }]

        # 2. Select the best audio format across the media
        best_audio = None
        if all_audio_formats:
            all_audio_formats.sort(key=self.rank_audio_format, reverse=True)
            best_audio = all_audio_formats[0]
        else:
            best_audio = {
                "format_id": "audio_best",
                "ext": "m4a",
                "acodec": "mp4a",
                "abr": 128.0
            }

        normalized_video_formats: List[NormalizedFormat] = []

        # Standard bitrate mapping (kbps) for accurate filesize estimation across tiers
        STANDARD_BITRATES = {
            2160: 12000.0,
            1440: 6000.0,
            1080: 2500.0,
            720: 1200.0,
            480: 600.0,
            360: 350.0,
            240: 200.0,
            144: 100.0
        }

        # 3. For each available standard height, pick the best video candidate
        # Sort heights descending: 2160p down to 360p
        for h in sorted(resolution_candidates.keys(), reverse=True):
            candidates = resolution_candidates[h]
            candidates.sort(key=self.rank_video_format, reverse=True)
            chosen = candidates[0]

            quality_label = f"{h}p"
            note = f"{h}p"
            if h == 2160:
                note = "2160p (4K UHD)"
            elif h == 1440:
                note = "1440p (2K QHD)"
            elif h == 1080:
                note = "1080p (Full HD)"
            elif h == 720:
                note = "720p (HD)"
            elif h == 480:
                note = "480p (SD)"
            elif h == 360:
                note = "360p (Fast)"
            elif h == 240:
                note = "240p (Mobile)"
            elif h == 144:
                note = "144p (Low)"

            # Estimate total file size (video + audio)
            if chosen.get("height") == h:
                vid_size = self.estimate_stream_size(chosen, duration)
            else:
                target_bitrate = STANDARD_BITRATES.get(h, 1000.0)
                vid_size = int((target_bitrate * 1000.0 / 8.0) * float(duration)) if duration else self.estimate_stream_size(chosen, duration)

            aud_size = self.estimate_stream_size(best_audio, duration) if best_audio else None

            if vid_size is not None and aud_size is not None:
                combined_size = vid_size + aud_size
            elif vid_size is not None:
                combined_size = vid_size
            elif aud_size is not None:
                combined_size = aud_size
            else:
                combined_size = None

            norm_fmt = NormalizedFormat(
                format_id=quality_label,  # Consumer-facing identifier
                type="video+audio",
                container="mp4",
                width=chosen.get("width"),
                height=h,
                fps=chosen.get("fps"),
                vcodec="h264",  # Promised output compatibility
                acodec="aac",   # Promised output compatibility
                bitrate=chosen.get("tbr") or chosen.get("vbr"),
                has_audio=True,
                has_video=True,
                filesize=None,
                filesize_approx=combined_size,
                quality=quality_label,
                format_note=note,
                downloadable=True,
                source_video_format_id=str(chosen.get("format_id")),
                source_audio_format_id=str(best_audio.get("format_id")) if best_audio else None
            )
            normalized_video_formats.append(norm_fmt)

        # 4. Add standardized Audio (MP3) extraction entry
        if best_audio:
            audio_size = self.estimate_stream_size(best_audio, duration)
            audio_format = NormalizedFormat(
                format_id="audio_best",
                type="audio",
                container="mp3",
                width=None,
                height=None,
                fps=None,
                vcodec=None,
                acodec="mp3",
                bitrate=best_audio.get("abr") or best_audio.get("tbr") or 320.0,
                has_audio=True,
                has_video=False,
                filesize=None,
                filesize_approx=audio_size,
                quality="MP3 Audio",
                format_note="High Fidelity MP3 Audio",
                downloadable=True,
                source_video_format_id=None,
                source_audio_format_id=str(best_audio.get("format_id"))
            )
            normalized_video_formats.append(audio_format)

        return normalized_video_formats

format_normalizer = FormatNormalizer()
