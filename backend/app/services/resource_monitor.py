import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Optional
import psutil
from app.config import settings
from app.utils.logger import logger

class JobResourceClass(str, Enum):
    LIGHT = "LIGHT"
    MEDIUM = "MEDIUM"
    HEAVY = "HEAVY"
    VERY_HEAVY = "VERY_HEAVY"

@dataclass
class SystemResourceSnapshot:
    cpu_percent: float
    available_ram_mb: float
    total_ram_mb: float
    free_disk_gb: float
    timestamp: float

class ResourceMonitor:
    """
    Cross-platform real-time system resource monitor powered by psutil.
    Caches metric readings briefly to minimize CPU overhead from system calls.
    """

    def __init__(self, cache_ttl_seconds: float = 0.5):
        self._cache_ttl = cache_ttl_seconds
        self._last_snapshot: Optional[SystemResourceSnapshot] = None
        self._lock = Lock()
        # Initialize initial psutil cpu reading
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

    def get_snapshot(self) -> SystemResourceSnapshot:
        now = time.time()
        with self._lock:
            if self._last_snapshot and (now - self._last_snapshot.timestamp < self._cache_ttl):
                return self._last_snapshot

            try:
                cpu = float(psutil.cpu_percent(interval=None))
            except Exception as e:
                logger.warning(f"Error reading CPU metrics: {e}")
                cpu = 0.0

            try:
                mem = psutil.virtual_memory()
                avail_ram_mb = mem.available / (1024 * 1024)
                total_ram_mb = mem.total / (1024 * 1024)
            except Exception as e:
                logger.warning(f"Error reading RAM metrics: {e}")
                avail_ram_mb = 1024.0
                total_ram_mb = 4096.0

            try:
                disk_path = str(settings.temp_storage_dir)
                disk = psutil.disk_usage(disk_path)
                free_disk_gb = disk.free / (1024 * 1024 * 1024)
            except Exception as e:
                logger.warning(f"Error reading disk metrics: {e}")
                free_disk_gb = 50.0

            snapshot = SystemResourceSnapshot(
                cpu_percent=cpu,
                available_ram_mb=avail_ram_mb,
                total_ram_mb=total_ram_mb,
                free_disk_gb=free_disk_gb,
                timestamp=now,
            )
            self._last_snapshot = snapshot
            return snapshot

    def get_cpu_percent(self) -> float:
        return self.get_snapshot().cpu_percent

    def get_available_ram_mb(self) -> float:
        return self.get_snapshot().available_ram_mb

    def get_free_disk_gb(self) -> float:
        return self.get_snapshot().free_disk_gb

resource_monitor = ResourceMonitor()

@dataclass
class JobCostEstimate:
    resource_class: JobResourceClass
    requires_transcode: bool
    is_audio_only: bool
    height: Optional[int]
    video_codec: Optional[str]
    audio_codec: Optional[str]
    estimated_size_bytes: int
    estimated_disk_required_bytes: int

class JobCostEstimator:
    """
    Classifies the operational cost and hardware footprint of a download job
    using actual normalized format metadata, stream codecs, and resolution.
    """

    @staticmethod
    def estimate_cost(
        format_info: Dict[str, Any],
        output_format: str = "mp4",
        duration_seconds: Optional[int] = None
    ) -> JobCostEstimate:
        target_ext = output_format.lower().strip(".")
        is_audio_only = target_ext in ("mp3", "m4a", "aac", "wav", "flac")

        height = format_info.get("height")
        vcodec = (format_info.get("vcodec") or "").lower().strip()
        acodec = (format_info.get("acodec") or "").lower().strip()

        # Check codec compatibility with MP4 (H.264 + AAC)
        video_is_h264 = vcodec.startswith("avc1") or vcodec.startswith("h264") or vcodec.startswith("avc")
        audio_is_aac = acodec.startswith("mp4a") or acodec.startswith("aac")

        # Check if transcode is required
        if is_audio_only:
            requires_transcode = target_ext != "m4a" or not audio_is_aac
        else:
            requires_transcode = not (video_is_h264 and audio_is_aac)

        # Estimate size
        size = format_info.get("filesize") or format_info.get("filesize_approx")
        if not size or size <= 0:
            bitrate = format_info.get("bitrate")  # in kbps
            if bitrate and duration_seconds and duration_seconds > 0:
                # bitrate (kbps) * 1000 / 8 * seconds
                size = int((bitrate * 1000 / 8) * duration_seconds)
            else:
                # Conservative fallback: 50MB per 1080p, 100MB per 4K, 20MB for <=480p, 10MB audio
                if is_audio_only:
                    size = 10 * 1024 * 1024
                elif height and height >= 2160:
                    size = 200 * 1024 * 1024
                elif height and height >= 1080:
                    size = 75 * 1024 * 1024
                elif height and height >= 720:
                    size = 40 * 1024 * 1024
                else:
                    size = 20 * 1024 * 1024

        required_disk = int(
            (size * settings.DISK_SAFETY_MULTIPLIER)
            + (settings.DISK_SAFETY_BUFFER_MB * 1024 * 1024)
        )

        # Determine resource class
        if is_audio_only:
            cost_class = JobResourceClass.LIGHT
        elif not height or height <= 480:
            cost_class = JobResourceClass.LIGHT
        elif height == 720:
            if video_is_h264:
                cost_class = JobResourceClass.LIGHT
            else:
                cost_class = JobResourceClass.MEDIUM
        elif height == 1080:
            if video_is_h264 and audio_is_aac:
                cost_class = JobResourceClass.MEDIUM
            else:
                cost_class = JobResourceClass.HEAVY
        elif height == 1440:
            cost_class = JobResourceClass.HEAVY
        elif height >= 2160:
            cost_class = JobResourceClass.VERY_HEAVY
        else:
            cost_class = JobResourceClass.MEDIUM if not requires_transcode else JobResourceClass.HEAVY

        return JobCostEstimate(
            resource_class=cost_class,
            requires_transcode=requires_transcode,
            is_audio_only=is_audio_only,
            height=height,
            video_codec=vcodec or None,
            audio_codec=acodec or None,
            estimated_size_bytes=size,
            estimated_disk_required_bytes=required_disk,
        )

job_cost_estimator = JobCostEstimator()
