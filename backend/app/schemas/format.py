from typing import Optional, Literal
from pydantic import BaseModel, Field

MediaType = Literal["video", "audio", "video+audio"]

class NormalizedFormat(BaseModel):
    """Internal normalized representation of an available media stream."""
    format_id: str = Field(..., description="The unique identifier for the format from yt-dlp")
    type: MediaType = Field(..., description="Media category: video, audio, or combined video+audio")
    container: str = Field(..., description="Container or extension: mp4, m4a, webm, mp3, etc.")
    width: Optional[int] = Field(None, description="Width in pixels for video streams")
    height: Optional[int] = Field(None, description="Height in pixels for video streams")
    fps: Optional[float] = Field(None, description="Frames per second")
    vcodec: Optional[str] = Field(None, description="Video codec name or 'none'")
    acodec: Optional[str] = Field(None, description="Audio codec name or 'none'")
    bitrate: Optional[float] = Field(None, description="Total, video, or audio bitrate in kbps")
    has_audio: bool = Field(False, description="True if the format stream contains audio")
    has_video: bool = Field(False, description="True if the format stream contains video")
    filesize: Optional[int] = Field(None, description="Exact file size in bytes if known")
    filesize_approx: Optional[int] = Field(None, description="Estimated file size in bytes")
    format_note: Optional[str] = Field(None, description="Human-readable quality summary, e.g. 1080p60, 128k")
    quality: Optional[str] = Field(None, description="Consumer-facing resolution label, e.g. 1080p, 720p")
    downloadable: bool = Field(True, description="Whether this format can be directly downloaded")
    source_video_format_id: Optional[str] = Field(None, description="Internal raw video format id")
    source_audio_format_id: Optional[str] = Field(None, description="Internal raw audio format id")
