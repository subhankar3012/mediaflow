from typing import Optional
from urllib.parse import urlparse
import httpx
from fastapi import APIRouter, Request, Response, HTTPException, status
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.schemas.format import NormalizedFormat
from app.security.url_validator import validate_and_normalize_url, SecurityError
from app.security.ip import get_client_ip
from app.security.rate_limiter import rate_limiter
from app.security.session import get_or_create_session_id
from app.platforms import get_platform_handler
from app.services.job_service import job_service
from app.services.ytdlp_service import YtDlpError
from app.utils.logger import logger

router = APIRouter(tags=["analyze"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(req: AnalyzeRequest, request: Request, response: Response):
    """
    Analyzes a user-submitted URL:
    1. Validates URL and prevents SSRF
    2. Detects platform (YouTube / Instagram)
    3. Extracts metadata and available formats via yt-dlp
    4. Creates a short-lived analysis record
    5. Returns normalized format list and analysis_id
    """
    client_ip = get_client_ip(request)
    rate_limiter.check_rate_limit(client_ip)

    session_id = get_or_create_session_id(request, response)

    # 1. URL validation and domain check
    try:
        normalized_url, platform_name = validate_and_normalize_url(req.url)
    except SecurityError as e:
        code = getattr(e, "code", "INVALID_URL")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": code, "message": str(e)}
        )

    # 2. Platform handler resolution
    handler = get_platform_handler(normalized_url)
    if not handler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "UNSUPPORTED_PLATFORM", "message": f"Platform '{platform_name}' handler not found."}
        )

    # 3. Extract metadata and formats
    try:
        meta = await handler.extract_metadata(normalized_url)
    except YtDlpError as e:
        code = e.code
        if code in ("MEDIA_UNAVAILABLE", "GEO_RESTRICTED"):
            mapped_code = "VIDEO_UNAVAILABLE"
        elif code == "AUTHENTICATION_REQUIRED":
            mapped_code = "AUTHENTICATION_REQUIRED"
        else:
            mapped_code = "EXTRACTION_FAILED"

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": mapped_code, "message": e.message}
        )
    except Exception:
        logger.exception("Metadata extraction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "EXTRACTION_FAILED", "message": "Failed to extract media metadata from source."}
        )

    # Convert formats to dict for storage
    format_dicts = [fmt.model_dump() for fmt in meta["formats"]]

    # 4. Store analysis record
    analysis = await job_service.create_analysis(
        session_id=session_id,
        source_url=normalized_url,
        platform=platform_name,
        title=meta.get("title"),
        thumbnail=meta.get("thumbnail"),
        duration=meta.get("duration"),
        uploader=meta.get("uploader"),
        formats=format_dicts,
    )

    return AnalyzeResponse(
        analysis_id=analysis["id"],
        platform=analysis["platform"],
        source_url=analysis["source_url"],
        title=analysis.get("title"),
        thumbnail=analysis.get("thumbnail"),
        duration=analysis.get("duration"),
        uploader=analysis.get("uploader"),
        formats=meta["formats"],
        expires_at=analysis["expires_at"]
    )

@router.get("/thumbnail/download")
async def download_thumbnail(url: str, title: Optional[str] = "thumbnail"):
    """
    Direct thumbnail file download endpoint.
    Fetches the thumbnail from remote CDN, determines correct content type and filename,
    and returns it with Content-Disposition: attachment so the browser downloads
    the file directly instead of opening it in a new tab.
    """
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_THUMBNAIL_URL", "message": "Invalid thumbnail URL provided."}
        )

    parsed = urlparse(url)
    allowed_domains = ["ytimg.com", "youtube.com", "instagram.com", "cdninstagram.com", "fbcdn.net"]
    domain = (parsed.netloc or "").lower()
    if not any(domain == d or domain.endswith("." + d) for d in allowed_domains):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "DISALLOWED_DOMAIN", "message": "Thumbnail domain not permitted."}
        )

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error_code": "THUMBNAIL_NOT_FOUND", "message": "Could not fetch remote thumbnail."}
                )

            content_type = resp.headers.get("content-type", "image/jpeg")
            ext = "jpg"
            if "webp" in content_type:
                ext = "webp"
            elif "png" in content_type:
                ext = "png"
            elif "gif" in content_type:
                ext = "gif"

            safe_title = "".join(c for c in (title or "thumbnail") if c.isalnum() or c in ("-", "_", " ")).strip()
            safe_title = safe_title[:60] or "thumbnail"
            filename = f"{safe_title}-thumbnail.{ext}"

            return Response(
                content=resp.content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Cache-Control": "public, max-age=3600"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Failed to fetch thumbnail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "THUMBNAIL_FETCH_FAILED", "message": "Failed to retrieve thumbnail."}
        )
