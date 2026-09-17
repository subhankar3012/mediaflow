import pytest
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import repository
from app.services.job_service import job_service
from app.services.storage_service import storage_service
from app.schemas.job import JobStatus

@pytest.mark.asyncio
async def test_failure_handling_and_file_cleanup():
    # 1. Create a job simulating a failure
    job_id = str(uuid.uuid4())
    dirs = storage_service.create_job_dirs(job_id)

    # Put a scratch file in working and source
    (dirs["source"] / "temp_file.part").write_text("corrupted data")
    (dirs["working"] / "ffmpeg_temp.mp4").write_text("working data")
    assert storage_service.get_job_dir(job_id, "source").exists()

    job_data = {
        "id": job_id,
        "session_id": "test_failure_sess",
        "source_url": "https://youtube.com/watch?v=fail",
        "platform": "youtube",
        "status": JobStatus.QUEUED.value,
        "progress": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
    }
    await repository.create_job(job_data)

    # Transition to PROCESSING then FAILED
    await job_service.update_status(job_id, JobStatus.PROCESSING)
    await job_service.update_status(
        job_id,
        JobStatus.FAILED,
        error_code="MEDIA_UNAVAILABLE",
        error_message="Simulated download failure"
    )

    # Purge directory as worker does on failure
    storage_service.delete_job_dir(job_id)

    # Verify database state
    updated_job = await repository.get_job(job_id)
    assert updated_job["status"] == "FAILED"
    assert updated_job["error_code"] == "MEDIA_UNAVAILABLE"
    assert "Simulated download failure" in updated_job["error_message"]

    # Verify no orphaned temporary directories remain
    assert not storage_service.get_job_dir(job_id).exists()

    # Cleanup database
    await repository.delete_job(job_id)

@pytest.mark.asyncio
async def test_job_cancellation_and_cleanup():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a job
        job_id = str(uuid.uuid4())
        dirs = storage_service.create_job_dirs(job_id)
        (dirs["working"] / "in_progress.tmp").write_text("active bytes")

        job_data = {
            "id": job_id,
            "session_id": "test_cancel_sess",
            "source_url": "https://youtube.com/watch?v=cancel",
            "platform": "youtube",
            "status": JobStatus.PROCESSING.value,
            "progress": 25.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
        }
        await repository.create_job(job_data)

        # Call DELETE /api/jobs/{job_id} with authorized session header
        del_resp = await client.delete(
            f"/api/jobs/{job_id}",
            headers={"X-Session-ID": "test_cancel_sess"}
        )
        assert del_resp.status_code == 200

        # Verify job is cancelled and files are purged
        cancelled_job = await repository.get_job(job_id)
        assert cancelled_job["status"] == "CANCELLED"
        assert not storage_service.get_job_dir(job_id).exists()

        # Cleanup database
        await repository.delete_job(job_id)
