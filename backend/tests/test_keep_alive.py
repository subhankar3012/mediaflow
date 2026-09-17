import subprocess
import sys
import uuid
import pytest
from pathlib import Path
from app.database import repository
from scripts.keep_alive import ping_health_endpoint, ProcessLock

@pytest.mark.asyncio
async def test_health_check_read_only_and_idempotent():
    """
    Verifies that calling the health check:
    1. Executes successfully against the Supabase database
    2. Does NOT create or modify any analysis records
    3. Does NOT create or modify any download job records
    """
    # Count existing rows before health check
    res_jobs = repository.client.table("download_jobs").select("id").execute()
    initial_jobs_count = len(res_jobs.data or [])

    res_analyses = repository.client.table("media_analyses").select("id").execute()
    initial_analyses_count = len(res_analyses.data or [])

    # Call repository health check 3 times consecutively
    for _ in range(3):
        healthy = await repository.check_health()
        assert healthy is True

    # Count rows after health check
    res_jobs_after = repository.client.table("download_jobs").select("id").execute()
    after_jobs_count = len(res_jobs_after.data or [])

    res_analyses_after = repository.client.table("media_analyses").select("id").execute()
    after_analyses_count = len(res_analyses_after.data or [])

    # Assert zero row creation
    assert after_jobs_count == initial_jobs_count, "Health check must not create any download jobs"
    assert after_analyses_count == initial_analyses_count, "Health check must not create any media analyses"

def test_keep_alive_ping_function():
    """Verifies ping_health_endpoint against ASGI test client without live TCP socket."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    success, status_code, latency_ms, data, err = ping_health_endpoint("/api/health", client=client)

    assert success is True
    assert status_code == 200
    assert latency_ms > 0
    assert err is None
    assert isinstance(data, dict)
    assert data.get("status") == "healthy"
    assert data.get("database_adapter") == "supabase"

def test_process_lock_prevents_overlap(tmp_path):
    """Verifies that ProcessLock prevents multiple concurrent keep-alive jobs."""
    lock_file = tmp_path / "test_keep_alive.lock"
    lock1 = ProcessLock(lock_file)
    lock2 = ProcessLock(lock_file)

    # 1. First acquisition succeeds
    assert lock1.acquire() is True
    assert lock_file.exists()

    # 2. Concurrent acquisition while first is held must fail
    assert lock2.acquire() is False

    # 3. Release first lock
    lock1.release()
    assert not lock_file.exists()

    # 4. Subsequent acquisition succeeds
    assert lock2.acquire() is True
    lock2.release()

def test_cli_keep_alive_dry_run():
    """Verifies executing keep_alive.py --dry-run via command line returns exit code 0."""
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "keep_alive.py"
    res = subprocess.run(
        [sys.executable, str(script_path), "--dry-run"],
        capture_output=True,
        text=True,
        timeout=20
    )
    assert res.returncode == 0
    assert "Keep-alive CLI dry-run verified successfully" in res.stdout
