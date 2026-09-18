import pytest
import uuid
import httpx
from datetime import datetime, timezone, timedelta
from supabase import create_client
from app.config import settings

@pytest.mark.asyncio
async def test_supabase_rls_isolation():
    """
    Verifies Row Level Security (RLS) enforcement:
    1. Service role has full access.
    2. Anon client cannot insert rows directly.
    3. Anon client with matching X-Session-ID can ONLY view its own session records.
    4. Unrelated session receives empty result and cannot view another session's records.
    """
    assert settings.DB_ADAPTER == "supabase"

    service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    now = datetime.now(timezone.utc).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

    session_alice = f"alice_{uuid.uuid4().hex[:8]}"
    session_bob = f"bob_{uuid.uuid4().hex[:8]}"

    job_alice_id = str(uuid.uuid4())
    job_bob_id = str(uuid.uuid4())

    job_alice = {
        "id": job_alice_id,
        "session_id": session_alice,
        "source_url": "https://youtube.com/watch?v=alice",
        "platform": "youtube",
        "title": "Alice Video",
        "status": "QUEUED",
        "progress": 0.0,
        "created_at": now,
        "expires_at": future,
    }
    job_bob = {
        "id": job_bob_id,
        "session_id": session_bob,
        "source_url": "https://youtube.com/watch?v=bob",
        "platform": "youtube",
        "title": "Bob Video",
        "status": "QUEUED",
        "progress": 0.0,
        "created_at": now,
        "expires_at": future,
    }

    try:
        # 1. Service role inserts both jobs (proves service role full access)
        res_a = service_client.table("download_jobs").insert(job_alice).execute()
        res_b = service_client.table("download_jobs").insert(job_bob).execute()
        assert len(res_a.data) == 1
        assert len(res_b.data) == 1

        # 2. Test direct REST API calls using anon key with headers
        rest_url = f"{settings.SUPABASE_URL}/rest/v1/download_jobs"

        # (a) Anon without session header -> Should see 0 records
        anon_headers_none = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp_none = await client.get(
                rest_url,
                headers=anon_headers_none,
                params={"id": f"in.({job_alice_id},{job_bob_id})"}
            )
            assert resp_none.status_code == 200
            assert resp_none.json() == []

        # (b) Anon with Alice's session header -> Should see Alice's job ONLY
        anon_headers_alice = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "x-session-id": session_alice,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp_alice = await client.get(
                rest_url,
                headers=anon_headers_alice,
                params={"id": f"in.({job_alice_id},{job_bob_id})"}
            )
            assert resp_alice.status_code == 200
            data_alice = resp_alice.json()
            assert len(data_alice) == 1
            assert data_alice[0]["id"] == job_alice_id
            assert data_alice[0]["session_id"] == session_alice

        # (c) Anon with Bob's session header -> Should see Bob's job ONLY
        anon_headers_bob = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "x-session-id": session_bob,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp_bob = await client.get(
                rest_url,
                headers=anon_headers_bob,
                params={"id": f"in.({job_alice_id},{job_bob_id})"}
            )
            assert resp_bob.status_code == 200
            data_bob = resp_bob.json()
            assert len(data_bob) == 1
            assert data_bob[0]["id"] == job_bob_id
            assert data_bob[0]["session_id"] == session_bob

        # (d) Anon trying to insert -> Must fail with RLS violation (42501 or 401/403)
        async with httpx.AsyncClient(timeout=30.0) as client:
            insert_attempt = await client.post(
                rest_url,
                headers=anon_headers_alice,
                json={
                    "id": str(uuid.uuid4()),
                    "session_id": session_alice,
                    "source_url": "https://youtube.com",
                    "platform": "youtube",
                    "created_at": now,
                    "expires_at": future
                }
            )
            # Must be rejected by RLS
            assert insert_attempt.status_code in (401, 403, 400)

    finally:
        # Cleanup
        service_client.table("download_jobs").delete().in_("id", [job_alice_id, job_bob_id]).execute()
