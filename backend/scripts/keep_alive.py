#!/usr/bin/env python3
"""
Supabase Keep-Alive Health-Check Bot for Media Downloader Engine.

Runs once every hour to send a lightweight, read-only, idempotent GET /api/health
request to keep the Supabase Free Plan project active and warm.

Guarantees:
- Strictly read-only: executes SELECT id FROM download_jobs LIMIT 1
- Zero database modifications: creates 0 jobs, 0 analyses, 0 rows
- Independent of users, admin, browser tabs, or active traffic
- Prevents overlapping runs via single-instance process lock
- Comprehensive logging with timestamp, HTTP status, and latency
- Zero credential exposure
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Configure paths
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DEFAULT_LOG_DIR = BACKEND_DIR / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "keep_alive.log"
DEFAULT_LOCK_FILE = DEFAULT_LOG_DIR / "keep_alive.lock"
DEFAULT_HEALTH_URL = os.getenv("HEALTH_CHECK_URL", "http://127.0.0.1:8000/api/health")

def setup_logger(log_file_path: Path) -> logging.Logger:
    """Configures console and rotating file logging."""
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("supabase_keep_alive")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s UTC] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Converter to UTC
    logging.Formatter.converter = time.gmtime

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (append mode)
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            str(log_file_path),
            maxBytes=2 * 1024 * 1024,  # 2 MB
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not initialize file logger: {e}")

    return logger

class ProcessLock:
    """Ensures only a single keep-alive instance executes at any given time."""
    def __init__(self, lock_file: Path):
        self.lock_file = lock_file
        self.acquired = False

    def acquire(self) -> bool:
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        if self.lock_file.exists():
            try:
                content = self.lock_file.read_text().strip()
                pid, start_time = content.split(":") if ":" in content else (content, "0")
                pid = int(pid)
                # Check if process is still alive
                if self._is_pid_running(pid):
                    return False
            except Exception:
                # Corrupt lock file; treat as stale
                pass

        # Write current PID and timestamp
        try:
            self.lock_file.write_text(f"{os.getpid()}:{int(time.time())}")
            self.acquired = True
            return True
        except Exception:
            return False

    def release(self) -> None:
        if self.acquired:
            try:
                if self.lock_file.exists():
                    self.lock_file.unlink()
            except Exception:
                pass
            self.acquired = False

    @staticmethod
    def _is_pid_running(pid: int) -> bool:
        """Cross-platform check if a process ID is currently active."""
        if pid <= 0:
            return False
        if os.name == "nt":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if process:
                kernel32.CloseHandle(process)
                return True
            return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Another keep-alive job is currently running.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

def ping_health_endpoint(url: str, timeout: float = 15.0, client: Optional[Any] = None) -> Tuple[bool, int, float, Optional[Dict[str, Any]], Optional[str]]:
    """
    Sends a lightweight GET request to the health endpoint.
    Returns (success, http_status, latency_ms, data, error_message).
    Supports injecting an ASGI TestClient or custom httpx.Client.
    """
    t_start = time.perf_counter()

    if client is not None:
        try:
            resp = client.get(url)
            latency_ms = (time.perf_counter() - t_start) * 1000.0
            try:
                data = resp.json()
            except Exception:
                data = None
            is_healthy = (resp.status_code == 200 and isinstance(data, dict) and data.get("status") == "healthy")
            err_msg = None if is_healthy else (data.get("message") if isinstance(data, dict) else resp.text[:100])
            return is_healthy, resp.status_code, round(latency_ms, 2), data, err_msg
        except Exception as e:
            latency_ms = (time.perf_counter() - t_start) * 1000.0
            return False, 0, round(latency_ms, 2), None, str(e)

    # Try httpx first if available, fallback to urllib.request
    try:
        import httpx
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(url)
                latency_ms = (time.perf_counter() - t_start) * 1000.0
                try:
                    data = resp.json()
                except Exception:
                    data = None

                is_healthy = (resp.status_code == 200 and isinstance(data, dict) and data.get("status") == "healthy")
                err_msg = None if is_healthy else (data.get("message") if isinstance(data, dict) else resp.text[:100])
                return is_healthy, resp.status_code, round(latency_ms, 2), data, err_msg
        except Exception as e:
            latency_ms = (time.perf_counter() - t_start) * 1000.0
            return False, 0, round(latency_ms, 2), None, str(e)
    except ImportError:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "MediaDownloader-SupabaseKeepAlive/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                latency_ms = (time.perf_counter() - t_start) * 1000.0
                body = resp.read().decode("utf-8")
                try:
                    data = json.loads(body)
                except Exception:
                    data = None
                is_healthy = (resp.status == 200 and isinstance(data, dict) and data.get("status") == "healthy")
                return is_healthy, resp.status, round(latency_ms, 2), data, None
        except urllib.error.HTTPError as e:
            latency_ms = (time.perf_counter() - t_start) * 1000.0
            return False, e.code, round(latency_ms, 2), None, f"HTTPError {e.code}"
        except Exception as e:
            latency_ms = (time.perf_counter() - t_start) * 1000.0
            return False, 0, round(latency_ms, 2), None, str(e)

def execute_keep_alive(url: str, logger: logging.Logger) -> bool:
    """Executes a single keep-alive ping and logs structured results."""
    success, status_code, latency_ms, data, err = ping_health_endpoint(url)

    if success and data:
        db_adapter = data.get("database_adapter", "unknown")
        db_status = data.get("database", "unknown")
        logger.info(
            f"Target: {url} | Status: {status_code} | Latency: {latency_ms}ms | "
            f"DB Adapter: {db_adapter} | DB Status: {db_status} | Health: {data.get('status')}"
        )
        return True
    else:
        logger.error(
            f"FAILED Target: {url} | Status: {status_code} | Latency: {latency_ms}ms | "
            f"Error: {err or 'Health check returned degraded/unhealthy status'}"
        )
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Media Downloader Engine — Supabase Hourly Keep-Alive Service"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_HEALTH_URL,
        help=f"Target health endpoint URL (default: {DEFAULT_HEALTH_URL})"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="Interval in seconds between keep-alive pings in daemon mode (default: 3600 = 1 hour)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single keep-alive ping and exit immediately (default mode for OS cron or Task Scheduler)"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously in a background loop once every interval"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate keep-alive configuration and process lock without sending network request"
    )
    parser.add_argument(
        "--log-file",
        default=str(DEFAULT_LOG_FILE),
        help=f"Path to rotating log file (default: {DEFAULT_LOG_FILE})"
    )

    args = parser.parse_args()
    log_path = Path(args.log_file)
    logger = setup_logger(log_path)
    lock = ProcessLock(DEFAULT_LOCK_FILE)

    if args.dry_run:
        with lock:
            logger.info("Keep-alive CLI dry-run verified successfully.")
            sys.exit(0)

    # 1. Single run mode (for cron, Task Scheduler, GitHub Actions)
    if args.once or not args.daemon:
        try:
            with lock:
                success = execute_keep_alive(args.url, logger)
                sys.exit(0 if success else 1)
        except RuntimeError as e:
            logger.warning(f"Skipping keep-alive execution: {e}")
            sys.exit(0)

    # 2. Daemon mode (continuous loop)
    logger.info(
        f"Starting persistent Keep-Alive Daemon. Target: {args.url} | Interval: {args.interval}s (1 hour)"
    )
    try:
        with lock:
            while True:
                execute_keep_alive(args.url, logger)
                time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Keep-Alive Daemon stopped by user.")
    except RuntimeError as e:
        logger.warning(f"Cannot start daemon: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
