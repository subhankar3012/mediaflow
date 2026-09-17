from urllib.parse import urlparse
from typing import Dict, Any
from app.platforms.base import PlatformHandler
from app.services.ytdlp_service import ytdlp_service
from app.services.format_service import format_normalizer

class InstagramHandler(PlatformHandler):
    @property
    def name(self) -> str:
        return "instagram"

    def matches(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            return host == "instagram.com" or host.endswith(".instagram.com")
        except Exception:
            return False

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        data = await ytdlp_service.extract_metadata_async(url)
        raw_formats = data.get("raw_formats", [])
        if raw_formats:
            data["formats"] = format_normalizer.normalize_formats(
                raw_formats,
                platform=self.name,
                duration=data.get("duration")
            )
        data["platform"] = self.name
        return data

    def build_format_spec(self, format_id: str, output_format: str = "mp4", audio_only: bool = False) -> str:
        if audio_only:
            return "bestaudio/best"
        # Always request both video and audio streams for Instagram to prevent missing audio bug
        if format_id and format_id not in ("best", "default"):
            return f"{format_id}+bestaudio/bestvideo+bestaudio/{format_id}/best"
        return "bestvideo+bestaudio/best"

instagram_handler = InstagramHandler()
