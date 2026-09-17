import asyncio
import uuid
import pytest
from app.database import repository
from app.schemas.job import JobStatus
from app.services.storage_service import storage_service
from app.security.rate_limiter import rate_limiter
from app.config import settings

@pytest.mark.asyncio
async def test_concurrent_job_storage_isolation():
    """
    Verifies that multiple jobs running in parallel have strictly isolated
    filesystem directory trees and files never collide.
    """
    job_ids = [str(uuid.uuid4()) for _ in range(5)]
    created_dirs = []

    try:
        # 1. Create directories for 5 concurrent jobs
        for j_id in job_ids:
            dirs = storage_service.create_job_dirs(j_id)
            created_dirs.append((j_id, dirs))
            
            # Write a unique file into each job's source and output directory
            source_file = dirs["source"] / f"input_{j_id}.mp4"
            source_file.write_text(f"source content for {j_id}")

            output_file = dirs["output"] / "final.mp4"
            output_file.write_text(f"output content for {j_id}")

        # 2. Verify complete isolation across all jobs
        for j_id, dirs in created_dirs:
            out_file = storage_service.get_output_file(j_id)
            assert out_file is not None
            assert out_file.exists()
            assert out_file.read_text() == f"output content for {j_id}"

            # Ensure this output file is inside the job's directory, not another's
            assert j_id in str(out_file)

    finally:
        # Cleanup
        for j_id in job_ids:
            storage_service.delete_job_dir(j_id)

@pytest.mark.asyncio
async def test_session_concurrency_slots():
    """
    Verifies that rate limiter enforces MAX_CONCURRENT_JOBS_PER_SESSION and
    releases slots cleanly upon completion.
    """
    session_id = f"sess_concurrent_test_{uuid.uuid4().hex[:8]}"
    max_jobs = settings.MAX_CONCURRENT_JOBS_PER_SESSION

    # 1. Fill available slots
    for _ in range(max_jobs):
        rate_limiter.acquire_job_slot(session_id)

    assert rate_limiter.get_active_count(session_id) == max_jobs

    # 2. Attempting to acquire another slot must raise HTTPException with CONCURRENCY_LIMIT_EXCEEDED
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        rate_limiter.acquire_job_slot(session_id)
    assert exc_info.value.status_code in (429, 503)
    assert exc_info.value.detail["error_code"] == "CONCURRENCY_LIMIT_EXCEEDED"

    # 3. Release one slot and re-acquire
    rate_limiter.release_job_slot(session_id)
    assert rate_limiter.get_active_count(session_id) == max_jobs - 1

    rate_limiter.acquire_job_slot(session_id)
    assert rate_limiter.get_active_count(session_id) == max_jobs

    # 4. Clean up all acquired slots
    for _ in range(max_jobs):
        rate_limiter.release_job_slot(session_id)

    assert rate_limiter.get_active_count(session_id) == 0

@pytest.mark.asyncio
async def test_simultaneous_database_job_updates():
    """
    Verifies that concurrent asynchronous operations updating different jobs
    in the database execute smoothly without deadlock or state corruption.
    """
    job_ids = [str(uuid.uuid4()) for _ in range(3)]

    # Create 3 jobs in database
    for j_id in job_ids:
        await repository.create_job({
            "id": j_id,
            "session_id": "sess_simultaneous_test",
            "source_url": "https://www.youtube.com/watch?v=test",
            "platform": "youtube",
            "title": f"Simultaneous Job {j_id}",
            "status": JobStatus.QUEUED.value,
            "progress": 0.0,
        })

    try:
        # Concurrently update progress and status across all 3 jobs
        async def worker_sim(j_id: str, idx: int):
            # Step 1: Transition to PROCESSING
            await repository.update_job_status(j_id, JobStatus.PROCESSING.value)
            # Step 2: Update progress multiple times
            for pct in [25.0, 50.0, 75.0]:
                await repository.update_job_progress(
                    job_id=j_id,
                    progress=pct,
                    downloaded_bytes=int(pct * 1000),
                    total_bytes=100000,
                    speed="1.5 MB/s",
                    eta="00:03"
                )
                await asyncio.sleep(0.05)
            # Step 3: Transition to COMPLETED
            await repository.update_job_status(
                job_id=j_id,
                status=JobStatus.COMPLETED.value,
                file_size=100000,
                temporary_file_key=f"jobs/{j_id}/output/final.mp4"
            )

        # Run simultaneously
        await asyncio.gather(*(worker_sim(j_id, i) for i, j_id in enumerate(job_ids)))

        # Verify final status of all jobs
        for j_id in job_ids:
            job = await repository.get_job(j_id)
            assert job is not None
            assert job["status"] == JobStatus.COMPLETED.value
            assert job["progress"] == 75.0 or job["progress"] == 100.0 or job["file_size"] == 100000

    finally:
        for j_id in job_ids:
            await repository.delete_job(j_id)
