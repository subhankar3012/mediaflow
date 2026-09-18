import asyncio
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from starlette.background import BackgroundTask

from app.config import settings
from app.schemas.job import JobResponse, JobStatus
from app.security.session import get_session_id, verify_job_session
from app.services.job_service import job_service
from app.services.storage_service import storage_service
from app.services.cleanup_service import cleanup_service
from app.workers.download_worker import download_worker
from app.utils.logger import logger, log_job

router = APIRouter(prefix="/jobs", tags=["jobs"])

def is_valid_uuid(val: str) -> bool:
    """Verifies that a string is a valid UUID to prevent database errors."""
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False

def sanitize_filename(name: str) -> str:
    """Sanitizes title for safe Content-Disposition attachment filename."""
    clean = re.sub(r'[^a-zA-Z0-9_\-\. ]', '', name)
    return clean.strip() or "media"

def determine_mime_type(ext: str) -> str:
    """Returns the standard MIME type for supported media container extensions."""
    mime_map = {
        "mp4": "video/mp4",
        "mkv": "video/x-matroska",
        "webm": "video/webm",
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "wav": "audio/wav",
        "flac": "audio/flac",
        "ogg": "audio/ogg",
        "zip": "application/zip",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "png": "image/png",
    }
    return mime_map.get(ext.lower().strip("."), "application/octet-stream")

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, request: Request):
    """
    Polling fallback endpoint to fetch job state, progress, speed, ETA, and errors.
    Enforces session verification so users only inspect their own jobs.
    """
    if not is_valid_uuid(job_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' does not exist."}
        )

    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' does not exist."}
        )

    verify_job_session(job, request)

    job_session = job.get("session_id")
    sess_query = f"?session_id={job_session}" if job_session and job_session not in ("", "default") else ""
    download_url = f"/api/jobs/{job_id}/file{sess_query}" if job["status"] == JobStatus.COMPLETED.value else None

    return JobResponse(
        id=job["id"],
        analysis_id=job.get("analysis_id"),
        source_url=job["source_url"],
        platform=job["platform"],
        title=job.get("title"),
        status=JobStatus(job["status"]),
        requested_format=job.get("requested_format"),
        output_format=job.get("output_format"),
        progress=float(job.get("progress") or 0.0),
        downloaded_bytes=job.get("downloaded_bytes"),
        total_bytes=job.get("total_bytes"),
        speed=job.get("speed"),
        eta=job.get("eta"),
        file_size=job.get("file_size"),
        error_code=job.get("error_code"),
        error_message=job.get("error_message"),
        download_url=download_url,
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        expires_at=job.get("expires_at")
    )

@router.get("/{job_id}/events")
async def job_events_stream(job_id: str, request: Request):
    """
    Server-Sent Events (SSE) endpoint providing real-time progress and status updates.
    Ensures:
    1. Immediate current status on connect
    2. Clean terminal events (COMPLETED, FAILED, CANCELLED, EXPIRED) without hanging
    3. Throttled/deduplicated progress events
    4. Keep-alive heartbeat comments for long downloads
    5. Graceful handling of client disconnects and reconnects
    """
    if not is_valid_uuid(job_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' does not exist."}
        )

    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' does not exist."}
        )

    verify_job_session(job, request)

    async def event_generator() -> AsyncGenerator[dict, None]:
        # 1. Send initial current state immediately upon client connection
        initial_job = await job_service.get_job(job_id)
        if not initial_job:
            return

        current_status = initial_job["status"]
        job_session = initial_job.get("session_id")
        sess_query = f"?session_id={job_session}" if job_session and job_session not in ("", "default") else ""
        initial_payload = {
            "job_id": job_id,
            "event": "status",
            "status": current_status,
            "progress": float(initial_job.get("progress") or 0.0),
            "downloaded_bytes": initial_job.get("downloaded_bytes"),
            "total_bytes": initial_job.get("total_bytes"),
            "speed": initial_job.get("speed"),
            "eta": initial_job.get("eta"),
            "download_url": f"/api/jobs/{job_id}/file{sess_query}" if current_status == JobStatus.COMPLETED.value else None,
            "error_code": initial_job.get("error_code"),
            "error_message": initial_job.get("error_message"),
        }

        yield {
            "event": "message",
            "data": json.dumps(initial_payload)
        }

        # If job is already in a terminal state, terminate SSE stream cleanly
        terminal_states = {
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
            JobStatus.EXPIRED.value
        }
        if current_status in terminal_states:
            return

        # 2. Subscribe to real-time events from the worker
        queue = await job_service.subscribe_events(job_id)
        last_sent_progress = initial_payload["progress"]
        last_sent_status = current_status

        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Timeout after 15s to send keep-alive heartbeat comment
                    event_data = await asyncio.wait_for(queue.get(), timeout=15.0)

                    # Augment event with job_id and download_url if completed
                    event_data["job_id"] = job_id
                    status_val = event_data.get("status")
                    if status_val == JobStatus.COMPLETED.value:
                        event_data["download_url"] = f"/api/jobs/{job_id}/file{sess_query}"

                    # Deduplicate progress events if status and progress haven't changed
                    new_progress = event_data.get("progress")
                    if (
                        status_val == last_sent_status
                        and new_progress == last_sent_progress
                        and status_val not in terminal_states
                    ):
                        continue

                    last_sent_status = status_val
                    last_sent_progress = new_progress

                    yield {
                        "event": "message",
                        "data": json.dumps(event_data)
                    }

                    # Clean termination on terminal state
                    if status_val in terminal_states:
                        break

                except asyncio.TimeoutError:
                    # Keep-alive SSE comment
                    yield {"comment": "keepalive"}
        finally:
            job_service.unsubscribe_events(job_id, queue)

    return EventSourceResponse(event_generator())

def _schedule_post_delivery_cleanup(target_job_id: str, delay_seconds: float = 1800.0):
    """Schedules removal of output media after a grace buffer without blocking the response."""
    async def _delayed_cleanup():
        try:
            await asyncio.sleep(delay_seconds)
            cleanup_service.cleanup_job(target_job_id)
        except Exception as e:
            logger.warning(f"Error during delayed cleanup of job {target_job_id}: {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_delayed_cleanup())
    except RuntimeError:
        pass

@router.get("/{job_id}/file")
async def download_job_file(job_id: str, request: Request):
    """
    Secure file streaming endpoint.
    1. Validates UUID and existence
    2. Validates session authorization (session matching)
    3. Verifies status is COMPLETED
    4. Rejects expired jobs and purges stale media
    5. Returns FileResponse with safe attachment filename and MIME type
    6. Schedules post-delivery cleanup via BackgroundTask
    """
    if not is_valid_uuid(job_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' does not exist."}
        )

    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "JOB_NOT_FOUND", "message": "Job not found."}
        )

    # 1. Session authorization validation
    verify_job_session(job, request)

    # 2. Check job status
    status_val = job["status"]
    if status_val == JobStatus.EXPIRED.value:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error_code": "JOB_EXPIRED", "message": "This download job has expired."}
        )
    elif status_val in (JobStatus.QUEUED.value, JobStatus.PROCESSING.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "JOB_NOT_READY", "message": f"Job is currently in state '{status_val}'; file is not ready."}
        )
    elif status_val != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "JOB_FAILED", "message": f"Job cannot be downloaded because its state is '{status_val}'."}
        )

    # 3. Check expiration timestamp
    expires_at_str = job.get("expires_at")
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now(timezone.utc) > expires_at:
                cleanup_service.cleanup_job(job_id)
                await job_service.update_status(job_id, JobStatus.EXPIRED)
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail={"error_code": "JOB_EXPIRED", "message": "This download has expired and its temporary file was removed."}
                )
        except ValueError:
            pass

    # 4. Check physical output file
    output_file = storage_service.get_output_file(job_id)
    if not output_file or not output_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "FILE_NOT_FOUND", "message": "Output media file was not found or has been purged."}
        )

    # 5. Build Content-Disposition filename and MIME type
    ext = output_file.suffix.lstrip(".") or job.get("output_format") or "mp4"
    title_safe = sanitize_filename(job.get("title") or "download")
    attachment_name = f"{title_safe}.{ext}"
    media_type = determine_mime_type(ext)

    return FileResponse(
        path=output_file,
        media_type=media_type,
        filename=attachment_name,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "private, no-cache, no-store, must-revalidate",
        },
        background=BackgroundTask(_schedule_post_delivery_cleanup, job_id)
    )

@router.delete("/{job_id}")
async def cancel_or_delete_job(job_id: str, request: Request):
    """
    Cancels an active job or purges temporary files for a completed job.
    Enforces session matching if job belongs to a session.
    Actively aborts yt-dlp downloading and FFmpeg processes.
    """
    if not is_valid_uuid(job_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' does not exist."}
        )

    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "JOB_NOT_FOUND", "message": "Job not found."}
        )

    # Session authorization validation
    verify_job_session(job, request)

    current_status = JobStatus(job["status"])
    if current_status in (JobStatus.QUEUED, JobStatus.PROCESSING):
        await download_worker.cancel_job(job_id)
    else:
        cleanup_service.cleanup_job(job_id)
        await job_service.delete_job(job_id)

    return {"job_id": job_id, "status": "deleted"}
