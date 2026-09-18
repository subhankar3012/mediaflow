from typing import Optional, Any, List
from pydantic import BaseModel, Field, model_validator

class DownloadRequest(BaseModel):
    analysis_id: str = Field(..., description="The analysis_id returned from POST /api/analyze")
    format_id: Optional[str] = Field(None, description="The format_id selected from available formats or quality key")
    quality: Optional[str] = Field(None, description="Target consumer quality: 360p, 480p, 720p, 1080p, 1440p, 2160p, zip")
    output_format: Optional[str] = Field("mp4", description="Desired target container: mp4, m4a, mp3, webm, zip, jpg")
    audio_only: Optional[bool] = Field(False, description="Whether to extract audio only")
    selected_indices: Optional[List[int]] = Field(None, description="1-based item indices to include for gallery/carousel downloads")

    @model_validator(mode="before")
    @classmethod
    def reconcile_format_and_quality(cls, data: Any) -> Any:
        if isinstance(data, dict):
            fmt = data.get("format_id")
            qual = data.get("quality")
            out_fmt = data.get("output_format")
            if out_fmt == "zip" or fmt == "zip" or qual == "zip":
                data["format_id"] = "zip"
                data["quality"] = "zip"
                data["output_format"] = "zip"
            elif not fmt and qual:
                data["format_id"] = qual
            elif not qual and fmt:
                data["quality"] = fmt
            elif not fmt and not qual:
                # Default to best
                data["format_id"] = "best"
                data["quality"] = "best"
        return data

class DownloadResponse(BaseModel):
    job_id: str = Field(..., description="The unique download job identifier")
    status: str = Field("QUEUED", description="Initial status of the download job")
    message: str = Field("Download job created and enqueued successfully")
