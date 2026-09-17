import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.database.repositories.supabase_repository import SupabaseRepository

@pytest.mark.asyncio
async def test_supabase_live_crud():
    """Tests full CRUD operations against live Supabase PostgreSQL database."""
    # Ensure settings are loaded
    assert settings.DB_ADAPTER == "supabase"
    assert settings.SUPABASE_URL != ""
    assert settings.SUPABASE_SERVICE_ROLE_KEY != ""

    repo = SupabaseRepository()

    # Health check
    is_healthy = await repo.check_health()
    assert is_healthy is True, "Supabase health check failed"

    # 1. Create analysis
    analysis_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    analysis_data = {
        "id": analysis_id,
        "session_id": "test_sess_crud",
        "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "platform": "youtube",
        "title": "CRUD Test Video",
        "thumbnail": "https://example.com/thumb.jpg",
        "duration": 212,
        "uploader": "Test Channel",
        "normalized_formats": [
            {
                "format_id": "18",
                "type": "video+audio",
                "container": "mp4",
                "width": 640,
                "height": 360,
                "has_audio": True,
                "has_video": True
            }
        ],
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=30)).isoformat(),
    }

    created_analysis = await repo.create_analysis(analysis_data)
    assert created_analysis["id"] == analysis_id
    assert created_analysis["platform"] == "youtube"
    assert len(created_analysis["normalized_formats"]) == 1

    # 2. Read analysis
    fetched_analysis = await repo.get_analysis(analysis_id)
    assert fetched_analysis is not None
    assert fetched_analysis["id"] == analysis_id
    assert fetched_analysis["title"] == "CRUD Test Video"

    # 3. Create download job
    job_id = str(uuid.uuid4())
    job_data = {
        "id": job_id,
        "analysis_id": analysis_id,
        "user_id": None,
        "session_id": "test_sess_crud",
        "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "platform": "youtube",
        "title": "CRUD Test Video",
        "status": "QUEUED",
        "requested_format": "18",
        "output_format": "mp4",
        "progress": 0.0,
        "downloaded_bytes": 0,
        "total_bytes": 1048576,
        "speed": None,
        "eta": None,
        "file_size": None,
        "temporary_file_key": None,
        "error_code": None,
        "error_message": None,
        "created_at": now.isoformat(),
        "started_at": None,
        "completed_at": None,
        "expires_at": (now + timedelta(minutes=30)).isoformat(),
    }

    created_job = await repo.create_job(job_data)
    assert created_job["id"] == job_id
    assert created_job["status"] == "QUEUED"

    # 4. Read job
    fetched_job = await repo.get_job(job_id)
    assert fetched_job is not None
    assert fetched_job["id"] == job_id
    assert fetched_job["status"] == "QUEUED"

    # 5. Update job status to PROCESSING
    started_iso = datetime.now(timezone.utc).isoformat()
    updated_processing = await repo.update_job_status(job_id, status="PROCESSING", started_at=started_iso)
    assert updated_processing["status"] == "PROCESSING"
    assert updated_processing["started_at"] is not None

    # 6. Update progress
    updated_progress = await repo.update_job_progress(
        job_id=job_id,
        progress=55.5,
        downloaded_bytes=524288,
        total_bytes=1048576,
        speed="1.5 MB/s",
        eta="00:03"
    )
    assert updated_progress["progress"] == 55.5
    assert updated_progress["speed"] == "1.5 MB/s"

    # 7. Mark completed
    completed_iso = datetime.now(timezone.utc).isoformat()
    updated_completed = await repo.update_job_status(
        job_id=job_id,
        status="COMPLETED",
        file_size=1048576,
        temporary_file_key=f"{job_id}/output/final.mp4",
        completed_at=completed_iso
    )
    assert updated_completed["status"] == "COMPLETED"
    assert updated_completed["file_size"] == 1048576

    # 8. Mark failed on a secondary test job
    fail_job_id = str(uuid.uuid4())
    fail_job_data = dict(job_data, id=fail_job_id)
    await repo.create_job(fail_job_data)
    updated_failed = await repo.update_job_status(
        fail_job_id,
        status="FAILED",
        error_code="TEST_ERROR",
        error_message="Test failure simulation"
    )
    assert updated_failed["status"] == "FAILED"
    assert updated_failed["error_code"] == "TEST_ERROR"

    # 9. Test expired jobs query
    # Create job with past expires_at
    past_time = datetime.now(timezone.utc) - timedelta(hours=2)
    expired_job_id = str(uuid.uuid4())
    expired_job_data = dict(job_data, id=expired_job_id, expires_at=past_time.isoformat())
    await repo.create_job(expired_job_data)

    expired_list = await repo.get_expired_jobs(datetime.now(timezone.utc))
    expired_ids = [j["id"] for j in expired_list]
    assert expired_job_id in expired_ids

    # 10. Delete / cleanup jobs & analyses
    deleted_1 = await repo.delete_job(job_id)
    deleted_2 = await repo.delete_job(fail_job_id)
    deleted_3 = await repo.delete_job(expired_job_id)
    assert deleted_1 is True
    assert deleted_2 is True
    assert deleted_3 is True

    # Cleanup analysis
    repo.client.table("media_analyses").delete().eq("id", analysis_id).execute()
