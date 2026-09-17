import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List
from fastapi import HTTPException, status
from app.config import settings

class RateLimiter:
    """In-memory sliding window rate limiter and active concurrency tracker."""

    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._active_jobs: Dict[str, int] = defaultdict(int)
        self._total_active_jobs: int = 0
        self._last_cleanup: float = time.time()
        self._lock = Lock()

    def evict_expired(self, max_age_seconds: float = 60.0) -> int:
        """Purges client keys whose requests have all fallen outside the rate limit window."""
        now = time.time()
        cutoff = now - max_age_seconds
        evicted = 0
        with self._lock:
            stale_keys = [
                key for key, timestamps in self._requests.items()
                if not timestamps or timestamps[-1] <= cutoff
            ]
            for key in stale_keys:
                del self._requests[key]
                evicted += 1
            self._last_cleanup = now
        return evicted

    def check_rate_limit(self, client_key: str) -> None:
        """Enforces MAX_REQUESTS_PER_MINUTE per client with automatic TTL eviction."""
        now = time.time()
        window_start = now - 60.0

        with self._lock:
            # Trigger periodic garbage collection every 60 seconds
            if now - self._last_cleanup > 60.0:
                stale_keys = [
                    k for k, ts in self._requests.items()
                    if not ts or ts[-1] <= window_start
                ]
                for k in stale_keys:
                    if k != client_key:
                        del self._requests[k]
                self._last_cleanup = now

            # Filter timestamps outside the 60-second window
            valid_timestamps = [ts for ts in self._requests[client_key] if ts > window_start]
            if len(valid_timestamps) >= settings.MAX_REQUESTS_PER_MINUTE:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Maximum {settings.MAX_REQUESTS_PER_MINUTE} requests per minute."
                    }
                )
            valid_timestamps.append(now)
            self._requests[client_key] = valid_timestamps

    def acquire_job_slot(self, session_id: str) -> None:
        """Validates concurrency limits before starting a new download job."""
        with self._lock:
            if self._total_active_jobs >= settings.MAX_CONCURRENT_JOBS_GLOBAL:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error_code": "CONCURRENCY_LIMIT_EXCEEDED",
                        "message": "Global job capacity reached. Please retry in a few moments."
                    }
                )

            if self._active_jobs[session_id] >= settings.MAX_CONCURRENT_JOBS_PER_SESSION:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error_code": "CONCURRENCY_LIMIT_EXCEEDED",
                        "message": f"You have reached the maximum of {settings.MAX_CONCURRENT_JOBS_PER_SESSION} concurrent downloads."
                    }
                )

            self._active_jobs[session_id] += 1
            self._total_active_jobs += 1

    def release_job_slot(self, session_id: str) -> None:
        """Releases active job slot when job completes, fails, or is cancelled."""
        with self._lock:
            if self._active_jobs[session_id] > 0:
                self._active_jobs[session_id] -= 1
            if self._total_active_jobs > 0:
                self._total_active_jobs -= 1

    def get_active_count(self, session_id: str) -> int:
        with self._lock:
            return self._active_jobs.get(session_id, 0)

rate_limiter = RateLimiter()
