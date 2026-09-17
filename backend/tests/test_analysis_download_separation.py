import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone, timedelta
from app.main import app
from app.database import repository

@pytest.mark.asyncio
async def test_analysis_and_download_separation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Reject invalid analysis ID on download
        fake_analysis_id = str(uuid.uuid4())
        d_resp_invalid = await client.post("/api/download", json={
            "analysis_id": fake_analysis_id,
            "format_id": "18",
            "output_format": "mp4"
        })
        assert d_resp_invalid.status_code == 404
        assert d_resp_invalid.json()["detail"]["error_code"] == "ANALYSIS_NOT_FOUND"

        # 2. Reject expired analysis
        past = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        expired_analysis_id = str(uuid.uuid4())
        await repository.create_analysis({
            "id": expired_analysis_id,
            "session_id": "test_sep_sess",
            "source_url": "https://youtube.com/watch?v=test",
            "platform": "youtube",
            "title": "Expired Analysis",
            "normalized_formats": [{"format_id": "18", "type": "video+audio", "container": "mp4"}],
            "created_at": past,
            "expires_at": past,
        })
        # Try to download using expired analysis
        # First cleanup expired analyses to test rejection
        await repository.cleanup_expired_analyses(datetime.now(timezone.utc))
        d_resp_expired = await client.post("/api/download", json={
            "analysis_id": expired_analysis_id,
            "format_id": "18",
            "output_format": "mp4"
        })
        assert d_resp_expired.status_code == 404

        # 3. Create valid analysis and test format validation
        valid_analysis_id = str(uuid.uuid4())
        future = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        await repository.create_analysis({
            "id": valid_analysis_id,
            "session_id": "test_sep_sess",
            "source_url": "https://youtube.com/watch?v=test",
            "platform": "youtube",
            "title": "Valid Analysis",
            "normalized_formats": [
                {"format_id": "18", "type": "video+audio", "container": "mp4"},
                {"format_id": "140", "type": "audio", "container": "m4a"},
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": future,
        })

        # (a) Reject unlisted format ID
        d_resp_unlisted = await client.post("/api/download", json={
            "analysis_id": valid_analysis_id,
            "format_id": "999_fake_format",
            "output_format": "mp4"
        })
        assert d_resp_unlisted.status_code == 400
        assert d_resp_unlisted.json()["detail"]["error_code"] in ("FORMAT_NOT_FOUND", "INVALID_FORMAT")


        # (b) Accept valid listed format ID
        d_resp_valid = await client.post("/api/download", json={
            "analysis_id": valid_analysis_id,
            "format_id": "18",
            "output_format": "mp4"
        })
        assert d_resp_valid.status_code == 200
        data = d_resp_valid.json()
        assert "job_id" in data
        assert data["status"] == "QUEUED"

        # Verify job was created in database
        job = await repository.get_job(data["job_id"])
        assert job is not None
        assert job["analysis_id"] == valid_analysis_id
        assert job["requested_format"] == "18"
        assert job["status"] in ("QUEUED", "PROCESSING")

        # Cleanup
        await repository.delete_job(data["job_id"])
        if hasattr(repository, "client"):
            repository.client.table("media_analyses").delete().eq("id", valid_analysis_id).execute()
