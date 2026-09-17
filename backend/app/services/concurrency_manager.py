import time
from threading import Lock
from typing import Dict, Set, Any, Tuple, Optional
from app.config import settings
from app.services.resource_monitor import (
    resource_monitor,
    JobCostEstimate,
    JobResourceClass,
    SystemResourceSnapshot
)
from app.utils.logger import logger

class AdaptiveConcurrencyManager:
    """
    Dynamically determines job admission and concurrency based on real-time
    system metrics (CPU, RAM, Disk) and job resource cost classes.
    Enforces hard safety ceilings as emergency guardrails while allowing
    lightweight tasks to scale efficiently when resources are idle.
    """

    def __init__(self):
        self._active_jobs: Dict[str, JobCostEstimate] = {}
        self._job_sessions: Dict[str, str] = {}
        self._session_jobs: Dict[str, Set[str]] = {}
        self._total_completed: int = 0
        self._total_failed: int = 0
        self._job_start_times: Dict[str, float] = {}
        self._recent_durations: list = []
        self._lock = Lock()

    def evaluate_admission(
        self,
        cost: JobCostEstimate,
        session_id: str,
        snapshot: Optional[SystemResourceSnapshot] = None
    ) -> Tuple[bool, str]:
        """
        Evaluates whether a job can safely be admitted right now.
        Must be called while holding self._lock or via try_reserve.
        """
        if snapshot is None:
            snapshot = resource_monitor.get_snapshot()

        # 1. Emergency Hard Limits
        total_active = len(self._active_jobs)
        if total_active >= settings.MAX_ACTIVE_JOBS_HARD_LIMIT:
            return False, f"Server capacity ceiling reached ({total_active}/{settings.MAX_ACTIVE_JOBS_HARD_LIMIT})"

        # 2. Per-Session Limits
        current_session_jobs = self._session_jobs.get(session_id, set())
        if len(current_session_jobs) >= settings.MAX_CONCURRENT_JOBS_PER_SESSION:
            return False, f"Maximum {settings.MAX_CONCURRENT_JOBS_PER_SESSION} concurrent downloads allowed per session"

        # 3. Disk Safety Threshold
        required_disk_gb = cost.estimated_disk_required_bytes / (1024 * 1024 * 1024)
        if snapshot.free_disk_gb < (required_disk_gb + settings.MIN_FREE_DISK_SPACE_GB):
            return False, f"STORAGE_FULL: Insufficient disk space ({snapshot.free_disk_gb:.1f}GB available, {required_disk_gb + settings.MIN_FREE_DISK_SPACE_GB:.1f}GB required)"

        # 4. Critical CPU Sched-Out
        if snapshot.cpu_percent >= settings.CPU_CRITICAL_THRESHOLD:
            return False, f"CPU utilization is critical ({snapshot.cpu_percent:.1f}% >= {settings.CPU_CRITICAL_THRESHOLD}%)"

        # 5. RAM Safety Threshold
        if snapshot.available_ram_mb < settings.MIN_AVAILABLE_RAM_MB:
            return False, f"Available RAM is critical ({snapshot.available_ram_mb:.0f}MB < {settings.MIN_AVAILABLE_RAM_MB:.0f}MB)"

        # 6. Heavy Transcode Limiting
        active_heavy = sum(
            1 for c in self._active_jobs.values()
            if c.resource_class in (JobResourceClass.HEAVY, JobResourceClass.VERY_HEAVY)
        )

        if cost.resource_class in (JobResourceClass.HEAVY, JobResourceClass.VERY_HEAVY):
            if active_heavy >= settings.MAX_ACTIVE_HEAVY_TRANSCODES:
                return False, f"Active heavy transcodes saturated ({active_heavy}/{settings.MAX_ACTIVE_HEAVY_TRANSCODES})"
            if snapshot.cpu_percent >= settings.CPU_HIGH_THRESHOLD:
                return False, f"CPU too high for additional heavy transcode ({snapshot.cpu_percent:.1f}% >= {settings.CPU_HIGH_THRESHOLD}%)"

        # 7. Adaptive Concurrency Soft Load Threshold
        # If CPU is elevated (>75%), prevent adding new MEDIUM jobs if already running multiple jobs
        if snapshot.cpu_percent > 75.0 and cost.resource_class == JobResourceClass.MEDIUM and total_active >= 3:
            return False, f"System load elevated ({snapshot.cpu_percent:.1f}%), deferring MEDIUM job"

        return True, "ADMIT"

    def try_reserve(
        self,
        job_id: str,
        session_id: str,
        cost: JobCostEstimate
    ) -> Tuple[bool, str]:
        """
        Atomically evaluates admission and reserves resource budget.
        Prevents race conditions where concurrent jobs evaluate resources at the same time.
        """
        with self._lock:
            if job_id in self._active_jobs:
                return True, "ALREADY_RESERVED"

            snapshot = resource_monitor.get_snapshot()
            can_admit, reason = self.evaluate_admission(cost, session_id, snapshot)

            # Structured audit logging of admission decisions
            decision_str = "ADMIT" if can_admit else "REJECT"
            logger.info(
                f"[admission] job={job_id} class={cost.resource_class.value} "
                f"cpu={snapshot.cpu_percent:.1f}% ram={snapshot.available_ram_mb:.0f}MB "
                f"disk={snapshot.free_disk_gb:.1f}GB active_jobs={len(self._active_jobs)} "
                f"decision={decision_str} reason='{reason}'"
            )

            if not can_admit:
                return False, reason

            # Record atomic reservation
            self._active_jobs[job_id] = cost
            self._job_sessions[job_id] = session_id
            if session_id not in self._session_jobs:
                self._session_jobs[session_id] = set()
            self._session_jobs[session_id].add(job_id)
            self._job_start_times[job_id] = time.time()

            return True, "ADMIT"

    def release(self, job_id: str, success: bool = True) -> None:
        """Atomically releases reserved resources for a completed, failed, or cancelled job."""
        with self._lock:
            cost = self._active_jobs.pop(job_id, None)
            session_id = self._job_sessions.pop(job_id, None)

            if session_id and session_id in self._session_jobs:
                self._session_jobs[session_id].discard(job_id)
                if not self._session_jobs[session_id]:
                    del self._session_jobs[session_id]

            start_time = self._job_start_times.pop(job_id, None)
            if start_time:
                duration = time.time() - start_time
                self._recent_durations.append(duration)
                if len(self._recent_durations) > 100:
                    self._recent_durations.pop(0)

            if success:
                self._total_completed += 1
            else:
                self._total_failed += 1

            cls_name = cost.resource_class.value if cost else "UNKNOWN"
            logger.info(
                f"[resource_release] job={job_id} class={cls_name} "
                f"remaining_active={len(self._active_jobs)}"
            )

    @property
    def active_jobs_count(self) -> int:
        with self._lock:
            return len(self._active_jobs)

    @property
    def active_heavy_transcodes(self) -> int:
        with self._lock:
            return sum(
                1 for c in self._active_jobs.values()
                if c.resource_class in (JobResourceClass.HEAVY, JobResourceClass.VERY_HEAVY)
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Provides real-time telemetry for administrative observability."""
        with self._lock:
            snapshot = resource_monitor.get_snapshot()
            class_counts = {
                JobResourceClass.LIGHT.value: 0,
                JobResourceClass.MEDIUM.value: 0,
                JobResourceClass.HEAVY.value: 0,
                JobResourceClass.VERY_HEAVY.value: 0,
            }
            transcode_count = 0
            for cost in self._active_jobs.values():
                class_counts[cost.resource_class.value] = class_counts.get(cost.resource_class.value, 0) + 1
                if cost.requires_transcode:
                    transcode_count += 1

            avg_duration = (
                sum(self._recent_durations) / len(self._recent_durations)
                if self._recent_durations else 0.0
            )

            return {
                "active_jobs_total": len(self._active_jobs),
                "active_jobs_by_class": class_counts,
                "active_transcodes": transcode_count,
                "active_sessions": len(self._session_jobs),
                "system": {
                    "cpu_percent": snapshot.cpu_percent,
                    "available_ram_mb": round(snapshot.available_ram_mb, 1),
                    "total_ram_mb": round(snapshot.total_ram_mb, 1),
                    "free_disk_gb": round(snapshot.free_disk_gb, 2),
                },
                "guardrails": {
                    "max_hard_limit": settings.MAX_ACTIVE_JOBS_HARD_LIMIT,
                    "max_heavy_transcodes": settings.MAX_ACTIVE_HEAVY_TRANSCODES,
                    "max_per_session": settings.MAX_CONCURRENT_JOBS_PER_SESSION,
                    "cpu_critical_threshold": settings.CPU_CRITICAL_THRESHOLD,
                    "cpu_high_threshold": settings.CPU_HIGH_THRESHOLD,
                },
                "stats": {
                    "total_completed": self._total_completed,
                    "total_failed": self._total_failed,
                    "average_duration_seconds": round(avg_duration, 2),
                }
            }

concurrency_manager = AdaptiveConcurrencyManager()
