import re
from urllib.parse import urlparse
from typing import Dict, Any
from app.platforms.base import PlatformHandler
from app.services.ytdlp_service import ytdlp_service
from app.services.format_service import format_normalizer

class FacebookHandler(PlatformHandler):
    @property
    def name(self) -> str:
        return "facebook"

    def matches(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            return (
                host == "facebook.com"
                or host.endswith(".facebook.com")
                or host == "fb.watch"
                or host.endswith(".fb.watch")
            )
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
        data["media_type"] = "video"
        return data

    def build_format_spec(self, format_id: str, output_format: str = "mp4", audio_only: bool = False) -> str:
        if audio_only:
            return "bestaudio/best"

        if format_id and format_id not in ("best", "default"):
            if format_id.lower() in ("hd", "sd"):
                return f"{format_id}/bestvideo+bestaudio/best"
            m = re.match(r"^(\d+)p$", str(format_id))
            if m:
                h = int(m.group(1))
                return f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/{format_id}/best"
            return f"{format_id}+bestaudio/{format_id}/bestvideo+bestaudio/best"

        return "bestvideo+bestaudio/best"

facebook_handler = FacebookHandler()
