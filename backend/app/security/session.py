import secrets
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from app.config import settings

SESSION_COOKIE_NAME = "downloader_session"

def generate_session_id() -> str:
    """Generate a high-entropy cryptographically secure random session ID."""
    return f"sess_{secrets.token_urlsafe(32)}"

def get_session_id(request: Request) -> Optional[str]:
    """
    Extracts existing session ID without generating a new one.
    Checks:
    1. 'X-Session-ID' header
    2. 'downloader_session' cookie
    3. 'session_id' query parameter (for direct browser file downloads)
    """
    return (
        request.headers.get("X-Session-ID")
        or request.cookies.get(SESSION_COOKIE_NAME)
        or request.query_params.get("session_id")
    )

def get_or_create_session_id(request: Request, response: Optional[Response] = None) -> str:
    """
    Extracts session ID from 'X-Session-ID' header, cookie, or query param.
    If not present, generates a new session ID and sets cookie if response object provided.
    """
    session_id = get_session_id(request)

    if not session_id:
        session_id = generate_session_id()
        if response:
            is_secure = settings.ENVIRONMENT == "production" or request.url.scheme == "https"
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session_id,
                httponly=True,
                samesite="none" if is_secure else "lax",
                secure=is_secure,
                max_age=86400 * 7
            )
            response.headers["X-Session-ID"] = session_id
    elif response:
        response.headers["X-Session-ID"] = session_id

    return session_id

def verify_job_session(job: Dict[str, Any], request: Request) -> None:
    """
    Validates that the requesting client owns the job session.
    Prevents unauthorized clients from reading status, streaming events, or downloading media.
    """
    job_session = job.get("session_id")
    if job_session and job_session not in ("", "default"):
        client_session = get_session_id(request)
        if not client_session or client_session != job_session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error_code": "UNAUTHORIZED_SESSION", "message": "You are not authorized to access this job."}
            )

