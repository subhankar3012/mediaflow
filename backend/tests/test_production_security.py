import pytest
from pathlib import Path
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.config import settings
from app.security.session import verify_job_session, get_or_create_session_id
from app.security.ip import get_client_ip, is_trusted_proxy
from app.security.rate_limiter import RateLimiter

def test_gitignore_covers_sensitive_files():
    root_dir = Path(__file__).resolve().parent.parent.parent
    root_gitignore = root_dir / ".gitignore"
    backend_gitignore = root_dir / "backend" / ".gitignore"

    assert root_gitignore.exists(), "Root .gitignore must exist"
    assert backend_gitignore.exists(), "Backend .gitignore must exist"

    root_content = root_gitignore.read_text(encoding="utf-8")
    backend_content = backend_gitignore.read_text(encoding="utf-8")

    for pattern in [".env", "*.db", "tmp_downloader/", "logs/", ".venv/", "node_modules/", "dist/"]:
        assert pattern in root_content, f"Root .gitignore must ignore {pattern}"

    for pattern in [".env", "*.db", "tmp_downloader/", "logs/", ".venv/"]:
        assert pattern in backend_content, f"Backend .gitignore must ignore {pattern}"

def test_production_cookie_security_flag(monkeypatch):
    from fastapi import Response

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    req = MagicMock()
    req.headers.get.return_value = None
    req.cookies.get.return_value = None
    req.query_params.get.return_value = None

    resp = MagicMock(spec=Response)
    session_id = get_or_create_session_id(req, resp)

    assert session_id.startswith("sess_")
    resp.set_cookie.assert_called_once()
    kwargs = resp.set_cookie.call_args[1]
    assert kwargs["secure"] is True, "Production cookie must have secure=True"
    assert kwargs["httponly"] is True
    assert kwargs["samesite"] == "lax"

def test_development_cookie_security_flag(monkeypatch):
    from fastapi import Response

    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    req = MagicMock()
    req.headers.get.return_value = None
    req.cookies.get.return_value = None
    req.query_params.get.return_value = None

    resp = MagicMock(spec=Response)
    session_id = get_or_create_session_id(req, resp)

    assert session_id.startswith("sess_")
    kwargs = resp.set_cookie.call_args[1]
    assert kwargs["secure"] is False, "Development cookie should allow secure=False"

def test_session_ownership_verification():
    req_match = MagicMock()
    req_match.headers.get.return_value = "sess_owner"
    req_match.cookies.get.return_value = None
    req_match.query_params.get.return_value = None

    job = {"id": "test_id", "session_id": "sess_owner"}
    # Matching session should pass without exception
    verify_job_session(job, req_match)

    req_intruder = MagicMock()
    req_intruder.headers.get.return_value = "sess_intruder"
    req_intruder.cookies.get.return_value = None
    req_intruder.query_params.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        verify_job_session(job, req_intruder)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error_code"] == "UNAUTHORIZED_SESSION"

def test_client_ip_trusted_proxy(monkeypatch):
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", "127.0.0.1,10.0.0.0/8")

    # 1. Untrusted direct client -> header spoofing ignored
    req_direct = MagicMock()
    req_direct.client.host = "198.51.100.5"
    req_direct.headers.get.side_effect = lambda h: "203.0.113.195" if h == "X-Forwarded-For" else None

    assert get_client_ip(req_direct) == "198.51.100.5"

    # 2. Trusted proxy peer -> parses X-Forwarded-For safely
    req_proxy = MagicMock()
    req_proxy.client.host = "127.0.0.1"
    req_proxy.headers.get.side_effect = lambda h: "203.0.113.50, 10.0.0.1" if h == "X-Forwarded-For" else None

    # Rightmost untrusted IP in chain should be 203.0.113.50
    assert get_client_ip(req_proxy) == "203.0.113.50"

    # 3. Trusted proxy peer with CF-Connecting-IP
    req_cf = MagicMock()
    req_cf.client.host = "127.0.0.1"
    req_cf.headers.get.side_effect = lambda h: "198.51.100.77" if h == "CF-Connecting-IP" else None

    assert get_client_ip(req_cf) == "198.51.100.77"

def test_rate_limiter_eviction():
    limiter = RateLimiter()
    # Add dummy old timestamps
    limiter._requests["stale_ip_1"] = [1000.0, 1005.0]
    limiter._requests["stale_ip_2"] = [1010.0]

    # Evict with age cutoff
    evicted = limiter.evict_expired(max_age_seconds=10.0)
    assert evicted == 2
    assert "stale_ip_1" not in limiter._requests
    assert "stale_ip_2" not in limiter._requests
