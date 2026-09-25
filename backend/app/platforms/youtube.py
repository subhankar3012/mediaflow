import re
from urllib.parse import urlparse
from typing import Dict, Any
from app.platforms.base import PlatformHandler
from app.services.ytdlp_service import ytdlp_service
from app.services.format_service import format_normalizer

TIER_LOWER_BOUNDS = {
    2160: 1440,
    1440: 1080,
    1080: 720,
    720: 480,
    480: 360,
    360: 240,
    240: 144,
    144: 0,
}

class YouTubeHandler(PlatformHandler):
    @property
    def name(self) -> str:
        return "youtube"

    def matches(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            return host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")
        except Exception:
            return False

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        data = await ytdlp_service.extract_metadata_async(url)
        raw_formats = data.get("raw_formats", [])
        
        # Always run normalize_formats to ensure standardized consumer tiers (1080p, 720p, 480p, 360p, MP3)
        normalized = format_normalizer.normalize_formats(
            raw_formats,
            platform=self.name,
            duration=data.get("duration")
        )
        if normalized:
            data["formats"] = normalized

        data["platform"] = self.name
        data["media_type"] = "video"
        data["is_gallery"] = False

        # Enforce valid video formats: YouTube should never return an empty list or image
        playable_formats = [f for f in data.get("formats", []) if getattr(f, "type", "") != "image"]
        if not playable_formats:
            data["formats"] = format_normalizer.normalize_formats([], platform=self.name, duration=data.get("duration"))
        else:
            data["formats"] = playable_formats

        return data

    def build_format_spec(self, format_id: str, output_format: str = "mp4", audio_only: bool = False) -> str:
        if audio_only:
            if format_id in ("audio_best", "best", "mp3"):
                return "bestaudio[acodec^=mp4a]/bestaudio/best"
            return f"{format_id}/bestaudio[acodec^=mp4a]/bestaudio/best"

        # Check if format_id is a normalized resolution label like "1080p", "720p", etc.
        m = re.match(r"^(\d+)p$", str(format_id).strip().lower())
        if m:
            h = int(m.group(1))
            min_h = TIER_LOWER_BOUNDS.get(h, int(h * 0.8))
            # Aspect-ratio aware matching:
            # - For horizontal/landscape/square (aspect_ratio >= 1): resolution tier is determined by height (e.g. 1920x1080)
            # - For vertical/portrait/Shorts (aspect_ratio < 1): resolution tier is determined by width (e.g. 1080x1920)
            return (
                # 1. Exact match with H.264 + AAC
                f"bestvideo[aspect_ratio>=1][height<={h}][height>{min_h}][vcodec^=avc1]+bestaudio[acodec^=mp4a]/"
                f"bestvideo[aspect_ratio<1][width<={h}][width>{min_h}][vcodec^=avc1]+bestaudio[acodec^=mp4a]/"
                # 2. Exact tier match with any video codec + any audio
                f"bestvideo[aspect_ratio>=1][height<={h}][height>{min_h}]+bestaudio/"
                f"bestvideo[aspect_ratio<1][width<={h}][width>{min_h}]+bestaudio/"
                # 3. Progressive/combined stream at requested tier
                f"best[aspect_ratio>=1][height<={h}][height>{min_h}]/"
                f"best[aspect_ratio<1][width<={h}][width>{min_h}]/"
                # 4. Upper bound fallback
                f"bestvideo[aspect_ratio>=1][height<={h}]+bestaudio/"
                f"bestvideo[aspect_ratio<1][width<={h}]+bestaudio/"
                f"best[aspect_ratio>=1][height<={h}]/"
                f"best[aspect_ratio<1][width<={h}]/"
                f"bestvideo+bestaudio/best"
            )

        if str(format_id).lower() in ("best", "default"):
            return "bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo+bestaudio/best"

        # Specific legacy format ID (e.g. "18", "137")
        return f"{format_id}+bestaudio[acodec^=mp4a]/{format_id}+bestaudio/{format_id}/best"

youtube_handler = YouTubeHandler()
