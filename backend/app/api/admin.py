from fastapi import APIRouter, Request, HTTPException, status
from app.config import settings
from app.services.concurrency_manager import concurrency_manager

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/metrics")
async def get_admin_metrics(request: Request):
    """
    Administrative metrics and telemetry endpoint.
    Protected by ADMIN_API_KEY.
    Provides real-time visibility into active workloads, hardware utilization,
    concurrency guardrails, and job completion statistics without exposing
    system secrets, passwords, or filesystem paths.
    """
    admin_key = (
        request.headers.get("X-Admin-Key")
        or request.query_params.get("admin_key")
    )

    if not settings.ADMIN_API_KEY or admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "UNAUTHORIZED_ADMIN", "message": "Valid admin credentials required."}
        )

    return concurrency_manager.get_metrics()
