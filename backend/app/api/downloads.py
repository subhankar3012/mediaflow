from fastapi import APIRouter, Request, Response, HTTPException, status
from app.config import settings
from app.schemas.download import DownloadRequest, DownloadResponse
from app.security.ip import get_client_ip
from app.security.rate_limiter import rate_limiter
from app.security.session import get_or_create_session_id
from app.services.job_service import job_service
from app.services.resource_monitor import resource_monitor, job_cost_estimator
from app.workers.queue import job_queue
from app.utils.logger import logger, log_job

router = APIRouter(tags=["downloads"])

@router.post("/download", response_model=DownloadResponse)
async def create_download_job(req: DownloadRequest, request: Request, response: Response):
    """
    Creates a real media download job from an active analysis:
    1. Verifies analysis exists and format exists in analysis results
    2. Validates session ownership and concurrency limits
    3. Verifies free disk space safety threshold (STORAGE_FULL guard)
    4. Enqueues job to the asynchronous DownloadWorker
    5. Returns job_id
    """
    client_ip = get_client_ip(request)
    rate_limiter.check_rate_limit(client_ip)

    session_id = get_or_create_session_id(request, response)

    # 1. Fetch analysis record
    analysis = await job_service.get_analysis(req.analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ANALYSIS_NOT_FOUND", "message": "Analysis record expired or does not exist. Please analyze URL again."}
        )

    # 2. Verify format_id/quality exists in normalized formats (never trust client blindly)
    raw_formats = analysis.get("normalized_formats", [])
    target_format = req.format_id or req.quality or "best"
    valid_format = False
    chosen_format_dict = {}
    for fmt in raw_formats:
        fmt_id = str(fmt.get("format_id")) if isinstance(fmt, dict) else getattr(fmt, "format_id", "")
        quality = str(fmt.get("quality")) if isinstance(fmt, dict) else getattr(fmt, "quality", "")
        if target_format in (fmt_id, quality, "best"):
            valid_format = True
            chosen_format_dict = fmt if isinstance(fmt, dict) else fmt.model_dump()
            break

    if not valid_format:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "FORMAT_NOT_FOUND", "message": f"Format '{target_format}' is not in the analyzed formats list."}
        )

    # 3. Queue depth check
    if job_queue.qsize() >= settings.MAX_QUEUE_DEPTH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "QUEUE_FULL",
                "message": "There's high traffic right now. Please try again in a moment."
            }
        )

    # 4. Pre-download Disk-Space Safety Guard
    output_ext = req.output_format or "mp4"
    cost = job_cost_estimator.estimate_cost(
        format_info=chosen_format_dict,
        output_format=output_ext,
        duration_seconds=analysis.get("duration")
    )
    free_disk_gb = resource_monitor.get_free_disk_gb()
    required_disk_gb = cost.estimated_disk_required_bytes / (1024 * 1024 * 1024)
    if free_disk_gb < (required_disk_gb + settings.MIN_FREE_DISK_SPACE_GB):
        logger.warning(
            f"Pre-download disk safety guard triggered: free={free_disk_gb:.2f}GB, "
            f"required={required_disk_gb:.2f}GB + buffer={settings.MIN_FREE_DISK_SPACE_GB}GB"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "STORAGE_FULL",
                "message": "Not enough temporary storage is available to prepare this download. Please try a smaller quality."
            }
        )

    # 5. Check session concurrency slot
    rate_limiter.acquire_job_slot(session_id)

    # 4. Create QUEUED download job
    try:
        job = await job_service.create_download_job(
            analysis=analysis,
            format_id=target_format,
            output_format=req.output_format or "mp4",
            session_id=session_id
        )
        job_id = job["id"]

        # 5. Enqueue to background worker
        await job_queue.enqueue(job_id)
        log_job(job_id, "Job enqueued to background worker queue")

        return DownloadResponse(
            job_id=job_id,
            status="QUEUED",
            message="Download job created and enqueued successfully"
        )
    except Exception as e:
        # Release concurrency slot on error
        rate_limiter.release_job_slot(session_id)
        logger.exception("Failed to create download job")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "JOB_CREATION_FAILED", "message": "Failed to create and enqueue download job."}
        )
