from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator

class DownloadRequest(BaseModel):
    analysis_id: str = Field(..., description="The analysis_id returned from POST /api/analyze")
    format_id: Optional[str] = Field(None, description="The format_id selected from available formats or quality key")
    quality: Optional[str] = Field(None, description="Target consumer quality: 360p, 480p, 720p, 1080p, 1440p, 2160p")
    output_format: Optional[str] = Field("mp4", description="Desired target container: mp4, m4a, mp3, webm")
    audio_only: Optional[bool] = Field(False, description="Whether to extract audio only")

    @model_validator(mode="before")
    @classmethod
    def reconcile_format_and_quality(cls, data: Any) -> Any:
        if isinstance(data, dict):
            fmt = data.get("format_id")
            qual = data.get("quality")
            if not fmt and qual:
                data["format_id"] = qual
            elif not qual and fmt:
                data["quality"] = fmt
            elif not fmt and not qual:
                raise ValueError("Either 'format_id' or 'quality' must be provided.")
        return data

class DownloadResponse(BaseModel):
    job_id: str = Field(..., description="The unique download job identifier")
    status: str = Field("QUEUED", description="Initial status of the download job")
    message: str = Field("Download job created and enqueued successfully")
