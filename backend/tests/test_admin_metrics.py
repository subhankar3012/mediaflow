import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

def test_admin_metrics_unauthorized():
    client = TestClient(app)
    # No header or query param
    resp = client.get("/api/admin/metrics")
    assert resp.status_code == 403
    data = resp.json()
    assert data["error"]["code"] == "UNAUTHORIZED_ADMIN"

def test_admin_metrics_invalid_key(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "super_secret_admin_key_123")
    client = TestClient(app)
    resp = client.get("/api/admin/metrics", headers={"X-Admin-Key": "wrong_key"})
    assert resp.status_code == 403

def test_admin_metrics_authorized(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "super_secret_admin_key_123")
    client = TestClient(app)
    resp = client.get("/api/admin/metrics", headers={"X-Admin-Key": "super_secret_admin_key_123"})
    assert resp.status_code == 200
    data = resp.json()

    # Verify telemetry fields
    assert "active_jobs_total" in data
    assert "active_jobs_by_class" in data
    assert "active_transcodes" in data
    assert "system" in data
    assert "cpu_percent" in data["system"]
    assert "available_ram_mb" in data["system"]
    assert "free_disk_gb" in data["system"]
    assert "guardrails" in data
    assert "stats" in data

    # Verify zero secrets leaked
    content_str = resp.text
    assert "SUPABASE_SERVICE_ROLE_KEY" not in content_str
    assert "ADMIN_API_KEY" not in content_str
    assert "super_secret_admin_key_123" not in content_str
