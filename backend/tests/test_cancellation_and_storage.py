import threading
import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from app.config import settings
from app.services.storage_service import storage_service
from app.services.cleanup_service import cleanup_service
from app.services.ytdlp_service import ytdlp_service, YtDlpError
from app.services.ffmpeg_service import ffmpeg_service
from app.services.resource_monitor import (
    job_cost_estimator,
    SystemResourceSnapshot
)
from app.services.concurrency_manager import concurrency_manager

def test_temp_directory_outside_project():
    project_root = Path(__file__).resolve().parent.parent.parent
    temp_dir = settings.temp_storage_dir

    # Must not be inside project root or OneDrive project folder
    assert temp_dir != project_root
    try:
        assert not temp_dir.is_relative_to(project_root), "Temp dir must not be inside project repository"
    except (ValueError, AttributeError):
        pass

def test_storage_full_disk_guard():
    # Simulate a huge 4K file requiring 10 GB
    cost_large = job_cost_estimator.estimate_cost(
        {"height": 2160, "filesize": 4000000000},
        output_format="mp4"
    )

    # Disk only has 4 GB free (less than required 10 GB + 3 GB buffer)
    snapshot_low_disk = SystemResourceSnapshot(
        cpu_percent=10.0,
        available_ram_mb=4000.0,
        total_ram_mb=8000.0,
        free_disk_gb=4.0,
        timestamp=time.time()
    )

    admitted, reason = concurrency_manager.evaluate_admission(cost_large, "sess_test", snapshot_low_disk)
    assert admitted is False
    assert "STORAGE_FULL" in reason

def test_ytdlp_cancellation_hook():
    cancel_event = threading.Event()
    cancel_event.set()

    # When cancellation_event is set, download should abort cleanly with CANCELLED code
    with pytest.raises(YtDlpError) as exc_info:
        ytdlp_service.download_media(
            url="https://www.youtube.com/watch?v=invalid",
            format_spec="best",
            output_template="./dummy",
            cancellation_event=cancel_event
        )
    assert exc_info.value.code == "CANCELLED"

def test_ffmpeg_process_tracking_and_kill():
    mock_proc = MagicMock()
    job_id = "test-job-cancel-99"

    ffmpeg_service.register_process(job_id, mock_proc)
    assert job_id in ffmpeg_service._active_processes

    # Kill process
    killed = ffmpeg_service.kill_job_process(job_id)
    assert killed is True
    mock_proc.terminate.assert_called_once()
    assert job_id not in ffmpeg_service._active_processes

def test_job_storage_lifecycle_and_cleanup(tmp_path):
    job_id = "test-lifecycle-1234"
    dirs = storage_service.create_job_dirs(job_id)

    assert dirs["source"].exists()
    assert dirs["working"].exists()
    assert dirs["output"].exists()

    # Create dummy output file
    dummy_out = dirs["output"] / "final.mp4"
    dummy_out.write_bytes(b"dummy mp4 content")
    assert storage_service.get_output_file(job_id) == dummy_out

    # Delete job directory
    cleanup_service.cleanup_job(job_id)
    assert not dirs["root"].exists()
    assert storage_service.get_output_file(job_id) is None
