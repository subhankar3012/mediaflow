from fastapi import APIRouter
from app.api.analyze import router as analyze_router
from app.api.downloads import router as downloads_router
from app.api.jobs import router as jobs_router
from app.api.health import router as health_router
from app.api.admin import router as admin_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(analyze_router)
api_router.include_router(downloads_router)
api_router.include_router(jobs_router)
api_router.include_router(admin_router)

__all__ = ["api_router"]
