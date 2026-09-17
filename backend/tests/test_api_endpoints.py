import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["api"] == "ok"
    assert data["database"] == "ok"
    assert data["ytdlp"] == "ok"
    assert data["ffmpeg"] == "ok"
    assert data["ffprobe"] == "ok"
    assert data["storage"] == "ok"

@pytest.mark.asyncio
async def test_analyze_unsupported_domain():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/analyze", json={"url": "https://unsupported-site.com/video"})
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "UNSUPPORTED_PLATFORM"
    assert data["error"]["code"] == "UNSUPPORTED_PLATFORM"

@pytest.mark.asyncio
async def test_analyze_ssrf_block():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/analyze", json={"url": "http://127.0.0.1/video"})
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_URL"

@pytest.mark.asyncio
async def test_job_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/jobs/non-existent-uuid")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "JOB_NOT_FOUND"
    assert data["detail"]["error_code"] == "JOB_NOT_FOUND"

