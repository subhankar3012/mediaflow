import asyncio
import time
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from app.config import settings
from app.services.storage_service import storage_service
from app.utils.logger import logger

class CleanupService:
    """
    Handles lifecycle cleanup of temporary files:
    1. Startup sweep of stale directories
    2. Scheduled purge of expired jobs
    3. Failure / cancellation cleanup
    """

    def __init__(self):
        self._running = False

    def startup_cleanup(self) -> int:
        """Removes all stale directories in temp_storage_dir and legacy tmp directories on server boot."""
        base_dir = settings.temp_storage_dir
        count = 0
        logger.info(f"Initiating startup cleanup sweep on {base_dir}")
        try:
            if base_dir.exists():
                for item in base_dir.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                        count += 1

            # Clean any legacy tmp_downloader directory left inside the repository
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            legacy_dirs = [
                project_root / "backend" / "tmp_downloader",
                project_root / "tmp_downloader"
            ]
            for leg in legacy_dirs:
                if leg.exists() and leg.is_dir():
                    for item in leg.iterdir():
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                            count += 1
                    try:
                        leg.rmdir()
                    except Exception:
                        pass

            logger.info(f"Startup cleanup completed. Purged {count} stale directory/directories.")
        except Exception as e:
            logger.error(f"Failed during startup cleanup: {str(e)}")
        return count

    def cleanup_job(self, job_id: str) -> bool:
        """Deletes media files for a specific job."""
        return storage_service.delete_job_dir(job_id)

    async def run_periodic_cleanup(self, repository) -> None:
        """Background loop that periodically checks and removes expired jobs."""
        self._running = True
        logger.info("Started periodic cleanup background task.")
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                expired_jobs = await repository.get_expired_jobs(now)
                for job in expired_jobs:
                    job_id = job.get("id")
                    if job_id:
                        self.cleanup_job(job_id)
                        await repository.update_job_status(
                            job_id,
                            status="EXPIRED",
                            error_message="Job media expired and temporary files were cleaned."
                        )
                        logger.info(f"Cleaned expired job {job_id}")

                # Also cleanup expired analyses
                await repository.cleanup_expired_analyses(now)

            except Exception as e:
                logger.error(f"Error during periodic cleanup cycle: {str(e)}")

            # Check every 60 seconds
            await asyncio.sleep(60)

    def stop(self) -> None:
        self._running = False

cleanup_service = CleanupService()
