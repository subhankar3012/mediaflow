import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import api_router
from app.schemas.error import ErrorCode, ErrorResponse
from app.security.url_validator import SecurityError
from app.database import repository
from app.services.cleanup_service import cleanup_service
from app.workers.download_worker import download_worker
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Initializing Media Downloader Engine...")
    logger.info(f"Environment: {settings.ENVIRONMENT} | DB Adapter: {settings.DB_ADAPTER}")

    # 1. Startup cleanup sweep for any stale temporary directories
    cleaned = cleanup_service.startup_cleanup()
    logger.info(f"Startup sweep removed {cleaned} stale directories.")

    # 2. Start background worker
    download_worker.start()

    # 3. Start periodic cleanup task
    cleanup_task = asyncio.create_task(cleanup_service.run_periodic_cleanup(repository))

    yield

    # --- Shutdown ---
    logger.info("Shutting down Media Downloader Engine...")
    download_worker.stop()
    cleanup_service.stop()
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Shutdown complete.")

app = FastAPI(
    title="Media Downloader Engine",
    description="High-performance, secure media downloader backend engine powered by FastAPI, yt-dlp, FFmpeg, and Supabase.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*(\.vercel\.app|\.pages\.dev|\.workers\.dev)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-ID", "Content-Disposition"],
)

# Exception handlers for standardized, secure error responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    clean_errors = []
    messages = []
    for err in errors:
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        clean_errors.append({"field": field, "message": msg, "type": err.get("type")})
        messages.append(f"'{field}': {msg}")

    combined_msg = f"Request validation failed: {'; '.join(messages)}" if messages else "Invalid request body or parameters."
    err_resp = ErrorResponse.create(
        code=ErrorCode.VALIDATION_ERROR.value,
        message=combined_msg,
        details=clean_errors
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=err_resp.model_dump())

@app.exception_handler(SecurityError)
async def security_exception_handler(request: Request, exc: SecurityError):
    code = getattr(exc, "code", ErrorCode.INVALID_URL.value)
    err_resp = ErrorResponse.create(code=code, message=str(exc))
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=err_resp.model_dump())

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("error_code") or detail.get("code")
        message = detail.get("message") or "An error occurred."
        details = detail.get("details")
    elif isinstance(detail, str):
        message = detail
        status_to_code = {
            400: ErrorCode.INVALID_URL.value,
            403: ErrorCode.UNAUTHORIZED_SESSION.value,
            404: ErrorCode.JOB_NOT_FOUND.value,
            410: ErrorCode.JOB_EXPIRED.value,
            422: ErrorCode.VALIDATION_ERROR.value,
            429: ErrorCode.RATE_LIMIT_EXCEEDED.value,
            500: ErrorCode.INTERNAL_ERROR.value,
            503: "SERVICE_UNAVAILABLE",
        }
        code = status_to_code.get(exc.status_code, "HTTP_ERROR")
        details = None
    else:
        code = "HTTP_ERROR"
        message = str(detail)
        details = None

    if not code:
        code = "HTTP_ERROR"

    err_resp = ErrorResponse.create(code=code, message=message, details=details)
    return JSONResponse(status_code=exc.status_code, content=err_resp.model_dump(), headers=exc.headers)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error: {str(exc)}")
    err_resp = ErrorResponse.create(
        code=ErrorCode.INTERNAL_ERROR.value,
        message="An unexpected internal server error occurred."
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=err_resp.model_dump())

# Mount API routers
app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "engine": "Media Downloader Engine",
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health"
    }
