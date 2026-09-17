import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import repository
from app.schemas.job import JobStatus
from app.services.storage_service import storage_service

@pytest.mark.asyncio
async def test_validation_error_envelope():
    """Verify malformed JSON requests return standard VALIDATION_ERROR envelope without leaking internal paths."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Missing required 'url' field in POST /api/analyze
        response = await ac.post("/api/analyze", json={"unknown_key": "some_value"})
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "url" in data["error"]["message"]
    assert isinstance(data["error"]["details"], list)
    assert data["error_code"] == "VALIDATION_ERROR"

@pytest.mark.asyncio
async def test_url_validation_edge_cases():
    """Verify various invalid URL and domain edge cases return clean, standardized error responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Non-HTTP scheme
        r1 = await ac.post("/api/analyze", json={"url": "ftp://youtube.com/watch?v=abc"})
        assert r1.status_code == 400
        assert r1.json()["error"]["code"] == "INVALID_URL"

        # 2. Unsupported domain
        r2 = await ac.post("/api/analyze", json={"url": "https://vimeo.com/123456789"})
        assert r2.status_code == 400
        assert r2.json()["error"]["code"] == "UNSUPPORTED_PLATFORM"

        # 3. Localhost SSRF attempt
        r3 = await ac.post("/api/analyze", json={"url": "http://localhost:8000/media"})
        assert r3.status_code == 400
        assert r3.json()["error"]["code"] == "INVALID_URL"

        # 4. Cloud metadata SSRF attempt
        r4 = await ac.post("/api/analyze", json={"url": "http://169.254.169.254/latest/meta-data"})
        assert r4.status_code == 400
        assert r4.json()["error"]["code"] == "INVALID_URL"

@pytest.mark.asyncio
async def test_download_creation_edge_cases():
    """Verify validation when attempting to create download jobs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        fake_uuid = str(uuid.uuid4())

        # 1. Non-existent analysis record
        r1 = await ac.post("/api/download", json={
            "analysis_id": fake_uuid,
            "format_id": "137"
        })
        assert r1.status_code == 404
        assert r1.json()["error"]["code"] == "ANALYSIS_NOT_FOUND"

        # 2. Create valid analysis record directly in database
        analysis_id = str(uuid.uuid4())
        await repository.create_analysis({
            "id": analysis_id,
            "session_id": "sess_test_download_edge",
            "source_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
            "platform": "youtube",
            "title": "Test Video",
            "thumbnail": None,
            "duration": 19,
            "uploader": "Test Uploader",
            "normalized_formats": [
                {"format_id": "18", "type": "video+audio", "container": "mp4", "height": 360}
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
        })

        # 3. Requesting format_id that is NOT in the analyzed formats list
        r2 = await ac.post("/api/download", json={
            "analysis_id": analysis_id,
            "format_id": "999_invalid_format"
        })
        assert r2.status_code == 400
        assert r2.json()["error"]["code"] == "FORMAT_NOT_FOUND"

@pytest.mark.asyncio
async def test_file_delivery_session_authorization():
    """Verify session authorization on /api/jobs/{job_id}/file: unauthorized sessions are rejected with 403."""
    session_owner = "sess_owner_alice_123"
    session_stranger = "sess_stranger_bob_456"
    job_id = str(uuid.uuid4())

    # Create dummy output file in storage
    dirs = storage_service.create_job_dirs(job_id)
    dummy_file = dirs["output"] / "final.mp4"
    dummy_file.write_bytes(b"dummy mp4 media stream bytes")

    # Create completed job bound to session_owner
    now = datetime.now(timezone.utc)
    await repository.create_job({
        "id": job_id,
        "analysis_id": None,
        "user_id": None,
        "session_id": session_owner,
        "source_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "platform": "youtube",
        "title": "Session Protected Video",
        "status": JobStatus.COMPLETED.value,
        "requested_format": "18",
        "output_format": "mp4",
        "progress": 100.0,
        "downloaded_bytes": len(b"dummy mp4 media stream bytes"),
        "total_bytes": len(b"dummy mp4 media stream bytes"),
        "speed": None,
        "eta": None,
        "file_size": len(b"dummy mp4 media stream bytes"),
        "temporary_file_key": f"jobs/{job_id}/output/final.mp4",
        "error_code": None,
        "error_message": None,
        "created_at": now.isoformat(),
        "started_at": now.isoformat(),
        "completed_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=30)).isoformat(),
    })

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Access without session -> 403 Forbidden
            r_no_sess = await ac.get(f"/api/jobs/{job_id}/file")
            assert r_no_sess.status_code == 403
            assert r_no_sess.json()["error"]["code"] == "UNAUTHORIZED_SESSION"

            # 2. Access with wrong session in header -> 403 Forbidden
            r_wrong_header = await ac.get(
                f"/api/jobs/{job_id}/file",
                headers={"X-Session-ID": session_stranger}
            )
            assert r_wrong_header.status_code == 403
            assert r_wrong_header.json()["error"]["code"] == "UNAUTHORIZED_SESSION"

            # 3. Access with wrong session in cookie -> 403 Forbidden
            r_wrong_cookie = await ac.get(
                f"/api/jobs/{job_id}/file",
                cookies={"downloader_session": session_stranger}
            )
            assert r_wrong_cookie.status_code == 403
            assert r_wrong_cookie.json()["error"]["code"] == "UNAUTHORIZED_SESSION"

            # 4. Access with authorized session in header -> 200 OK
            r_auth_header = await ac.get(
                f"/api/jobs/{job_id}/file",
                headers={"X-Session-ID": session_owner}
            )
            assert r_auth_header.status_code == 200
            assert r_auth_header.headers["content-type"] == "video/mp4"
            assert "attachment" in r_auth_header.headers["content-disposition"]
            assert r_auth_header.content == b"dummy mp4 media stream bytes"

            # 5. Access with authorized session in query param -> 200 OK
            r_auth_query = await ac.get(f"/api/jobs/{job_id}/file?session_id={session_owner}")
            assert r_auth_query.status_code == 200
            assert r_auth_query.content == b"dummy mp4 media stream bytes"

    finally:
        storage_service.delete_job_dir(job_id)
        await repository.delete_job(job_id)

@pytest.mark.asyncio
async def test_file_delivery_status_checks():
    """Verify file download requests reject incomplete or expired jobs."""
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # 1. Create QUEUED job
    await repository.create_job({
        "id": job_id,
        "analysis_id": None,
        "session_id": "sess_status_test",
        "source_url": "https://www.youtube.com/watch?v=test",
        "platform": "youtube",
        "title": "Incomplete Job",
        "status": JobStatus.QUEUED.value,
        "requested_format": "18",
        "output_format": "mp4",
        "progress": 0.0,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=30)).isoformat(),
    })

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # File download on QUEUED job -> 400 JOB_NOT_READY
            r_queued = await ac.get(
                f"/api/jobs/{job_id}/file",
                headers={"X-Session-ID": "sess_status_test"}
            )
            assert r_queued.status_code == 400
            assert r_queued.json()["error"]["code"] == "JOB_NOT_READY"

            # Update to EXPIRED
            await repository.update_job_status(job_id, JobStatus.EXPIRED.value)
            r_expired = await ac.get(
                f"/api/jobs/{job_id}/file",
                headers={"X-Session-ID": "sess_status_test"}
            )
            assert r_expired.status_code == 410
            assert r_expired.json()["error"]["code"] == "JOB_EXPIRED"

    finally:
        await repository.delete_job(job_id)

@pytest.mark.asyncio
async def test_sse_event_stream_terminal_exit():
    """Verify SSE event stream delivers initial status and terminates immediately on completed jobs."""
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Create completed job
    await repository.create_job({
        "id": job_id,
        "session_id": "sess_sse_test",
        "source_url": "https://www.youtube.com/watch?v=test",
        "platform": "youtube",
        "title": "Completed Video",
        "status": JobStatus.COMPLETED.value,
        "requested_format": "18",
        "output_format": "mp4",
        "progress": 100.0,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=30)).isoformat(),
    })

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            async with ac.stream("GET", f"/api/jobs/{job_id}/events", headers={"X-Session-ID": "sess_sse_test"}) as response:
                assert response.status_code == 200
                assert "text/event-stream" in response.headers["content-type"]
                lines = []
                async for line in response.aiter_lines():
                    if line:
                        lines.append(line)
                
                # Verify that events were received and stream closed without hanging
                assert any("COMPLETED" in l for l in lines)
                assert any(f"/api/jobs/{job_id}/file" in l for l in lines)

    finally:
        await repository.delete_job(job_id)
