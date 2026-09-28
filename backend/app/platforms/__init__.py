from typing import Optional, List, Dict, Any
from app.platforms.base import PlatformHandler
from app.platforms.youtube import youtube_handler
from app.platforms.instagram import instagram_handler
from app.platforms.x import x_handler
from app.platforms.facebook import facebook_handler
from app.platforms.pinterest import pinterest_handler
from app.platforms.reddit import reddit_handler

PLATFORM_HANDLERS: List[PlatformHandler] = [
    youtube_handler,
    instagram_handler,
    x_handler,
    facebook_handler,
    pinterest_handler,
    reddit_handler,
]

PLATFORM_REGISTRY: Dict[str, PlatformHandler] = {
    "youtube": youtube_handler,
    "instagram": instagram_handler,
    "x": x_handler,
    "facebook": facebook_handler,
    "pinterest": pinterest_handler,
    "reddit": reddit_handler,
}

PLATFORM_METADATA: Dict[str, Dict[str, Any]] = {
    "youtube": {
        "id": "youtube",
        "name": "YouTube",
        "domains": ["youtube.com", "youtu.be"],
        "media_types": ["video", "audio"],
        "capabilities": ["video_download", "audio_extraction", "thumbnail_download"],
        "theme": "youtube",
    },
    "instagram": {
        "id": "instagram",
        "name": "Instagram",
        "domains": ["instagram.com"],
        "media_types": ["video", "image", "carousel"],
        "capabilities": ["video_download", "reels_download", "carousel_zip", "photo_download"],
        "theme": "instagram",
    },
    "x": {
        "id": "x",
        "name": "X (Twitter)",
        "domains": ["x.com", "twitter.com"],
        "media_types": ["video", "audio"],
        "capabilities": ["video_download", "audio_extraction"],
        "theme": "x",
    },
    "facebook": {
        "id": "facebook",
        "name": "Facebook",
        "domains": ["facebook.com", "fb.watch"],
        "media_types": ["video", "audio"],
        "capabilities": ["video_download", "audio_extraction"],
        "theme": "facebook",
    },
    "pinterest": {
        "id": "pinterest",
        "name": "Pinterest",
        "domains": ["pinterest.com", "pin.it"],
        "media_types": ["video", "image"],
        "capabilities": ["video_download", "photo_download"],
        "theme": "pinterest",
    },
    "reddit": {
        "id": "reddit",
        "name": "Reddit",
        "domains": ["reddit.com", "redd.it"],
        "media_types": ["video", "image", "audio"],
        "capabilities": ["video_download", "audio_extraction", "photo_download"],
        "theme": "reddit",
    },
}

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
    "x_handler",
    "facebook_handler",
    "pinterest_handler",
    "reddit_handler",
    "get_platform_handler",
    "PLATFORM_HANDLERS",
    "PLATFORM_REGISTRY",
    "PLATFORM_METADATA",
]
