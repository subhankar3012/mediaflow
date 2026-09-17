import time
import pytest
from app.config import settings
from app.services.resource_monitor import (
    job_cost_estimator,
    JobResourceClass,
    SystemResourceSnapshot
)
from app.services.concurrency_manager import AdaptiveConcurrencyManager

def test_job_cost_classification():
    # 1. 360p video -> LIGHT
    cost_360 = job_cost_estimator.estimate_cost(
        {"height": 360, "vcodec": "avc1.4d401e", "acodec": "mp4a.40.2", "filesize": 5000000},
        output_format="mp4"
    )
    assert cost_360.resource_class == JobResourceClass.LIGHT
    assert cost_360.requires_transcode is False

    # 2. Audio-only -> LIGHT
    cost_audio = job_cost_estimator.estimate_cost(
        {"height": 1080, "vcodec": "av01.0.08M.08", "acodec": "opus", "filesize": 15000000},
        output_format="mp3"
    )
    assert cost_audio.resource_class == JobResourceClass.LIGHT
    assert cost_audio.is_audio_only is True

    # 3. 720p H264 copy -> LIGHT
    cost_720_copy = job_cost_estimator.estimate_cost(
        {"height": 720, "vcodec": "avc1.4d401f", "acodec": "mp4a.40.2", "filesize": 25000000},
        output_format="mp4"
    )
    assert cost_720_copy.resource_class == JobResourceClass.LIGHT
    assert cost_720_copy.requires_transcode is False

    # 4. 1080p H264 copy -> MEDIUM
    cost_1080_copy = job_cost_estimator.estimate_cost(
        {"height": 1080, "vcodec": "avc1.640028", "acodec": "mp4a.40.2", "filesize": 60000000},
        output_format="mp4"
    )
    assert cost_1080_copy.resource_class == JobResourceClass.MEDIUM
    assert cost_1080_copy.requires_transcode is False

    # 5. 1080p VP9 transcode -> HEAVY
    cost_1080_transcode = job_cost_estimator.estimate_cost(
        {"height": 1080, "vcodec": "vp9", "acodec": "opus", "filesize": 50000000},
        output_format="mp4"
    )
    assert cost_1080_transcode.resource_class == JobResourceClass.HEAVY
    assert cost_1080_transcode.requires_transcode is True

    # 6. 4K / 2160p -> VERY_HEAVY
    cost_4k = job_cost_estimator.estimate_cost(
        {"height": 2160, "vcodec": "vp09.00.51.08.01.01.01.01.00", "acodec": "opus", "filesize": 350000000},
        output_format="mp4"
    )
    assert cost_4k.resource_class == JobResourceClass.VERY_HEAVY
    assert cost_4k.requires_transcode is True

def test_adaptive_concurrency_admission():
    mgr = AdaptiveConcurrencyManager()

    # Normal healthy system snapshot
    snapshot_healthy = SystemResourceSnapshot(
        cpu_percent=25.0,
        available_ram_mb=3000.0,
        total_ram_mb=8000.0,
        free_disk_gb=40.0,
        timestamp=time.time()
    )

    cost_light = job_cost_estimator.estimate_cost({"height": 360, "filesize": 5000000}, "mp4")
    cost_heavy = job_cost_estimator.estimate_cost({"height": 1080, "vcodec": "vp9", "acodec": "opus", "filesize": 50000000}, "mp4")

    # 1. Admit multiple LIGHT jobs
    admitted, reason = mgr.evaluate_admission(cost_light, "sess_1", snapshot_healthy)
    assert admitted is True
    assert reason == "ADMIT"

    # Reserve 2 jobs for session 1
    res1, _ = mgr.try_reserve("job_1", "sess_1", cost_light)
    res2, _ = mgr.try_reserve("job_2", "sess_1", cost_light)
    assert res1 is True
    assert res2 is True

    # 2. Per-session limit: 3rd job for sess_1 should be rejected
    res3, reason3 = mgr.try_reserve("job_3", "sess_1", cost_light)
    assert res3 is False
    assert "concurrent downloads allowed per session" in reason3

    # But sess_2 can still reserve
    res_s2, _ = mgr.try_reserve("job_4", "sess_2", cost_light)
    assert res_s2 is True

    # 3. Critical CPU (>95%) prevents new jobs
    snapshot_cpu_critical = SystemResourceSnapshot(
        cpu_percent=96.5,
        available_ram_mb=3000.0,
        total_ram_mb=8000.0,
        free_disk_gb=40.0,
        timestamp=time.time()
    )
    admitted_crit, reason_crit = mgr.evaluate_admission(cost_light, "sess_3", snapshot_cpu_critical)
    assert admitted_crit is False
    assert "critical" in reason_crit.lower()

    # 4. Low RAM (<500MB) rejects admission
    snapshot_ram_critical = SystemResourceSnapshot(
        cpu_percent=30.0,
        available_ram_mb=350.0,
        total_ram_mb=8000.0,
        free_disk_gb=40.0,
        timestamp=time.time()
    )
    admitted_ram, reason_ram = mgr.evaluate_admission(cost_light, "sess_3", snapshot_ram_critical)
    assert admitted_ram is False
    assert "ram is critical" in reason_ram.lower()

    # 5. Heavy transcode limit
    mgr_transcode = AdaptiveConcurrencyManager()
    mgr_transcode.try_reserve("heavy_1", "sess_a", cost_heavy)
    mgr_transcode.try_reserve("heavy_2", "sess_b", cost_heavy)

    # 3rd heavy transcode rejected (MAX_ACTIVE_HEAVY_TRANSCODES = 2)
    can_admit_3rd_heavy, reason_heavy = mgr_transcode.evaluate_admission(cost_heavy, "sess_c", snapshot_healthy)
    assert can_admit_3rd_heavy is False
    assert "heavy transcodes saturated" in reason_heavy.lower()

    # But light job can still be admitted
    can_admit_light, _ = mgr_transcode.evaluate_admission(cost_light, "sess_c", snapshot_healthy)
    assert can_admit_light is True

    # 6. Releasing restores capacity
    mgr_transcode.release("heavy_1")
    can_admit_after_release, _ = mgr_transcode.evaluate_admission(cost_heavy, "sess_c", snapshot_healthy)
    assert can_admit_after_release is True
