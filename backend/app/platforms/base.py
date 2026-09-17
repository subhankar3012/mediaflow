from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class PlatformHandler(ABC):
    """Abstract base class for platform-specific extraction and downloading."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def matches(self, url: str) -> bool:
        """Determines if this platform handler can process the given URL."""
        pass

    @abstractmethod
    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """Extracts and normalizes metadata and formats."""
        pass

    @abstractmethod
    def build_format_spec(self, format_id: str, output_format: str = "mp4", audio_only: bool = False) -> str:
        """Constructs yt-dlp format specification string for downloading."""
        pass
