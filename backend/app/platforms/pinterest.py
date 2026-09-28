import re
from urllib.parse import urlparse
from typing import Dict, Any
from app.platforms.base import PlatformHandler
from app.services.ytdlp_service import ytdlp_service
from app.services.format_service import format_normalizer

class PinterestHandler(PlatformHandler):
    @property
    def name(self) -> str:
        return "pinterest"

    def matches(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            return (
                host == "pinterest.com"
                or host.endswith(".pinterest.com")
                or host == "pin.it"
                or host.endswith(".pin.it")
            )
        except Exception:
            return False

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        data = await ytdlp_service.extract_metadata_async(url)
        raw_formats = data.get("raw_formats", [])
        
        has_video = any(
            f.get("vcodec") and str(f.get("vcodec")).lower() != "none"
            for f in raw_formats
        )
        data["media_type"] = "video" if has_video else "image"
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

        if format_id and format_id not in ("best", "default", "original_image"):
            m = re.match(r"^(\d+)p$", str(format_id))
            if m:
                h = int(m.group(1))
                return f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/{format_id}/best"
            return f"{format_id}+bestaudio/{format_id}/best"

        return "bestvideo+bestaudio/best"

pinterest_handler = PinterestHandler()
