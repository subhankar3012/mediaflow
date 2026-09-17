from typing import Optional, List
from app.platforms.base import PlatformHandler
from app.platforms.youtube import youtube_handler
from app.platforms.instagram import instagram_handler

PLATFORM_HANDLERS: List[PlatformHandler] = [
    youtube_handler,
    instagram_handler,
]

def get_platform_handler(url: str) -> Optional[PlatformHandler]:
    """Finds the matching platform handler for a given URL."""
    for handler in PLATFORM_HANDLERS:
        if handler.matches(url):
            return handler
    return None

__all__ = [
    "PlatformHandler",
    "youtube_handler",
    "instagram_handler",
    "get_platform_handler",
    "PLATFORM_HANDLERS",
]
