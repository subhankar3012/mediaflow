import asyncio
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Set, List
from app.config import settings
from app.database import repository
from app.schemas.job import JobStatus
from app.utils.logger import logger, log_job

# Valid state machine transitions
VALID_TRANSITIONS = {
    JobStatus.QUEUED: {JobStatus.PROCESSING, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.PROCESSING: {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.COMPLETED: {JobStatus.EXPIRED},
    JobStatus.FAILED: set(),
    JobStatus.EXPIRED: set(),
    JobStatus.CANCELLED: set(),
}

class InvalidStateTransitionError(Exception):
    pass

class JobService:
    """
    Coordinates job lifecycle, state transitions, progress throttling,
    and Server-Sent Events (SSE) broadcasting.
    """

    def __init__(self):
        # job_id -> set of asyncio.Queue for SSE listeners
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        # job_id -> last database update timestamp
        self._last_db_updates: Dict[str, float] = {}

    def _validate_transition(self, current_status: JobStatus, new_status: JobStatus) -> None:
        if current_status == new_status:
            return
        allowed = VALID_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"Invalid job state transition from {current_status.value} to {new_status.value}"
            )

    async def create_analysis(
        self,
        session_id: str,
        source_url: str,
        platform: str,
        title: Optional[str],
        thumbnail: Optional[str],
        duration: Optional[int],
        uploader: Optional[str],
        formats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        analysis_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.ANALYSIS_EXPIRATION_MINUTES)

        analysis_data = {
            "id": analysis_id,
            "session_id": session_id,
            "source_url": source_url,
            "platform": platform,
            "title": title,
            "thumbnail": thumbnail,
            "duration": duration,
            "uploader": uploader,
            "normalized_formats": formats,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
        return await repository.create_analysis(analysis_data)

    async def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        return await repository.get_analysis(analysis_id)

    async def create_download_job(
        self,
        analysis: Dict[str, Any],
        format_id: str,
        output_format: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.JOB_EXPIRATION_MINUTES)

        job_data = {
            "id": job_id,
            "analysis_id": analysis.get("id"),
            "user_id": user_id,
            "session_id": session_id,
            "source_url": analysis.get("source_url"),
            "platform": analysis.get("platform"),
            "title": analysis.get("title"),
            "status": JobStatus.QUEUED.value,
            "requested_format": format_id,
            "output_format": output_format,
            "progress": 0.0,
            "downloaded_bytes": 0,
            "total_bytes": None,
            "speed": None,
            "eta": None,
            "file_size": None,
            "temporary_file_key": None,
            "error_code": None,
            "error_message": None,
            "created_at": now.isoformat(),
            "started_at": None,
            "completed_at": None,
            "expires_at": expires_at.isoformat(),
        }

        created = await repository.create_job(job_data)
        log_job(job_id, "Created download job in QUEUED status", format_id=format_id)
        await self._broadcast_event(job_id, {
            "event": "status",
            "status": JobStatus.QUEUED.value,
            "progress": 0.0
        })
        return created

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return await repository.get_job(job_id)

    async def update_status(
        self,
        job_id: str,
        new_status: JobStatus,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        file_size: Optional[int] = None,
        temporary_file_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        job = await repository.get_job(job_id)
        if not job:
            return None

        current = JobStatus(job["status"])
        self._validate_transition(current, new_status)

        now_iso = datetime.now(timezone.utc).isoformat()
        started_at = now_iso if new_status == JobStatus.PROCESSING and not job.get("started_at") else None
        completed_at = now_iso if new_status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED) else None

        updated = await repository.update_job_status(
            job_id=job_id,
            status=new_status.value,
            error_code=error_code,
            error_message=error_message,
            file_size=file_size,
            temporary_file_key=temporary_file_key,
            started_at=started_at,
            completed_at=completed_at,
        )

        log_job(job_id, f"Transitioned status to {new_status.value}")

        # Broadcast status update immediately to all SSE listeners
        payload: Dict[str, Any] = {
            "event": "status",
            "status": new_status.value,
            "progress": 100.0 if new_status == JobStatus.COMPLETED else (job.get("progress") or 0.0),
        }
        if error_message:
            payload["error_code"] = error_code
            payload["error_message"] = error_message
        if file_size:
            payload["file_size"] = file_size

        await self._broadcast_event(job_id, payload)
        return updated

    async def update_progress(
        self,
        job_id: str,
        progress: float,
        downloaded_bytes: Optional[int] = None,
        total_bytes: Optional[int] = None,
        speed: Optional[str] = None,
        eta: Optional[str] = None,
        force_db_update: bool = False
    ) -> None:
        """
        Broadcasts progress to SSE immediately;
        Throttles database writes to at most once per 1.5 seconds.
        """
        # Always broadcast to realtime SSE clients
        await self._broadcast_event(job_id, {
            "event": "progress",
            "progress": progress,
            "downloaded_bytes": downloaded_bytes,
            "total_bytes": total_bytes,
            "speed": speed,
            "eta": eta,
        })

        now = time.time()
        last_update = self._last_db_updates.get(job_id, 0.0)

        if force_db_update or (now - last_update >= 1.5):
            self._last_db_updates[job_id] = now
            await repository.update_job_progress(
                job_id=job_id,
                progress=progress,
                downloaded_bytes=downloaded_bytes,
                total_bytes=total_bytes,
                speed=speed,
                eta=eta,
            )

    async def subscribe_events(self, job_id: str) -> asyncio.Queue:
        """Registers a new SSE client subscriber for a job."""
        queue: asyncio.Queue = asyncio.Queue()
        if job_id not in self._subscribers:
            self._subscribers[job_id] = set()
        self._subscribers[job_id].add(queue)
        return queue

    def unsubscribe_events(self, job_id: str, queue: asyncio.Queue) -> None:
        """Removes an SSE client subscriber."""
        if job_id in self._subscribers:
            self._subscribers[job_id].discard(queue)
            if not self._subscribers[job_id]:
                del self._subscribers[job_id]

    async def _broadcast_event(self, job_id: str, data: Dict[str, Any]) -> None:
        """Pushes event payload to all active SSE queues for this job."""
        if job_id in self._subscribers:
            dead_queues = set()
            for queue in self._subscribers[job_id]:
                try:
                    queue.put_nowait(data)
                except asyncio.QueueFull:
                    dead_queues.add(queue)
            for dead in dead_queues:
                self._subscribers[job_id].discard(dead)

job_service = JobService()
