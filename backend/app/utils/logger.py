import logging
import sys
from typing import Optional

def setup_logger(name: str = "downloader", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger

logger = setup_logger()

def log_job(job_id: str, message: str, level: str = "info", **kwargs) -> None:
    """Helper to log structured messages with job_id."""
    extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items() if "key" not in k.lower() and "secret" not in k.lower())
    full_msg = f"[Job {job_id}] {message} {extra_info}".strip()
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(full_msg)
