import pytest
from pathlib import Path
from app.services.storage_service import StorageService, StorageSecurityError

def test_isolated_directory_creation(tmp_path):
    storage = StorageService(base_path=tmp_path)
    dirs = storage.create_job_dirs("test-job-123")

    assert dirs["source"].exists()
    assert dirs["working"].exists()
    assert dirs["output"].exists()
    assert dirs["source"].parent == dirs["root"]

def test_path_traversal_prevention(tmp_path):
    storage = StorageService(base_path=tmp_path)

    # Attempt directory traversal via job_id
    # StorageService sanitizes job_id with Path(job_id).name
    dirs = storage.create_job_dirs("../../../etc")
    assert dirs["root"].parent == tmp_path.resolve()

def test_job_cleanup(tmp_path):
    storage = StorageService(base_path=tmp_path)
    dirs = storage.create_job_dirs("cleanup-job")
    (dirs["output"] / "final.mp4").write_text("dummy video")

    assert storage.get_output_file("cleanup-job") is not None
    assert storage.delete_job_dir("cleanup-job") is True
    assert not dirs["root"].exists()
