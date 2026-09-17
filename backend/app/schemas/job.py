from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class JobProgress(BaseModel):
    progress: float = Field(0.0, ge=0.0, le=100.0)
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    speed: Optional[str] = None
    eta: Optional[str] = None

class JobResponse(BaseModel):
    id: str
    analysis_id: Optional[str] = None
    source_url: str
    platform: str
    title: Optional[str] = None
    status: JobStatus
    requested_format: Optional[str] = None
    output_format: Optional[str] = None
    progress: float = 0.0
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    speed: Optional[str] = None
    eta: Optional[str] = None
    file_size: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    expires_at: Optional[str] = None
