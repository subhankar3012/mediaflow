from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

class ErrorCode(str, Enum):
    INVALID_URL = "INVALID_URL"
    UNSUPPORTED_PLATFORM = "UNSUPPORTED_PLATFORM"
    VIDEO_UNAVAILABLE = "VIDEO_UNAVAILABLE"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    ANALYSIS_NOT_FOUND = "ANALYSIS_NOT_FOUND"
    FORMAT_NOT_FOUND = "FORMAT_NOT_FOUND"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    JOB_NOT_READY = "JOB_NOT_READY"
    JOB_FAILED = "JOB_FAILED"
    JOB_EXPIRED = "JOB_EXPIRED"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    STORAGE_FULL = "STORAGE_FULL"
    UNAUTHORIZED_SESSION = "UNAUTHORIZED_SESSION"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    CONCURRENCY_LIMIT_EXCEEDED = "CONCURRENCY_LIMIT_EXCEEDED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable standardized error code")
    message: str = Field(..., description="Human-readable explanation of the error")
    details: Optional[Any] = Field(None, description="Optional supplementary error context or field validation errors")

class ErrorResponse(BaseModel):
    error: ErrorDetail
    # Redundant top-level fields for universal frontend and client compatibility
    error_code: str
    message: str
    detail: Dict[str, Any]

    @classmethod
    def create(cls, code: str, message: str, details: Optional[Any] = None) -> "ErrorResponse":
        err_detail = ErrorDetail(code=code, message=message, details=details)
        return cls(
            error=err_detail,
            error_code=code,
            message=message,
            detail={"error_code": code, "message": message, "details": details}
        )
