from fastapi import APIRouter
from app.config import settings
from app.database import repository
from app.services.ffmpeg_service import ffmpeg_service
from app.utils.system import check_system_binaries

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """
    Returns the health status of all core components:
    API, Database, yt-dlp, FFmpeg, FFprobe, and Temporary Storage.
    """
    db_ok = await repository.check_health()
    binaries = check_system_binaries()

    # Check temp storage writeability
    storage_ok = False
    try:
        test_file = settings.temp_storage_dir / ".health_check"
        test_file.write_text("health")
        test_file.unlink()
        storage_ok = True
    except Exception:
        storage_ok = False

    all_ok = (
        db_ok
        and binaries["ytdlp"] != "not installed"
        and binaries["ffmpeg"] != "not found"
        and binaries["ffprobe"] != "not found"
        and storage_ok
    )

    from app.services.ytdlp_service import ytdlp_service
    cookie_status = ytdlp_service.get_cookies_status()

    return {
        "status": "healthy" if all_ok else "degraded",
        "api": "ok",
        "database": "ok" if db_ok else "error",
        "database_adapter": settings.DB_ADAPTER,
        "ytdlp": "ok" if binaries["ytdlp"] != "not installed" else "error",
        "ytdlp_version": binaries["ytdlp"],
        "ffmpeg": "ok" if binaries["ffmpeg"] != "not found" else "error",
        "ffprobe": "ok" if binaries["ffprobe"] != "not found" else "error",
        "node": binaries.get("node"),
        "node_version": binaries.get("node_version"),
        "deno": binaries.get("deno"),
        "deno_version": binaries.get("deno_version"),
        "cookies_loaded": cookie_status["loaded"],
        "cookies_count": cookie_status["count"],
        "cookies_valid": cookie_status["valid"],
        "storage": "ok" if storage_ok else "error",
        "build_version": "v1.0.4-deno-node22",
    }
