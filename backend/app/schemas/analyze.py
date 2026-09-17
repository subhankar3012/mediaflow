from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from app.schemas.format import NormalizedFormat

class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="The user submitted public media URL to analyze", min_length=4)

class AnalyzeResponse(BaseModel):
    analysis_id: str = Field(..., description="Unique UUID identifier for this analysis session")
    platform: str = Field(..., description="Detected platform name, e.g. youtube, instagram")
    source_url: str = Field(..., description="Canonical source URL")
    title: Optional[str] = Field(None, description="Media title")
    thumbnail: Optional[str] = Field(None, description="Media thumbnail URL")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    uploader: Optional[str] = Field(None, description="Channel or uploader name")
    formats: List[NormalizedFormat] = Field(default_factory=list, description="List of normalized playable/downloadable formats")
    expires_at: str = Field(..., description="ISO 8601 timestamp when this analysis expires")
