import shutil
from pathlib import Path
from typing import Optional, Dict
from app.config import settings
from app.utils.logger import logger

class StorageSecurityError(Exception):
    pass

class StorageService:
    """
    Manages isolated temporary filesystem directories per job:
        TEMP_STORAGE_PATH/{job_id}/
            ├── source/
            ├── working/
            └── output/
    Enforces strict path traversal defenses and server-generated filenames.
    """

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = (base_path or settings.temp_storage_dir).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_job_root(self, job_id: str) -> Path:
        # Sanitize job_id to prevent path traversal
        clean_id = Path(job_id).name
        job_root = (self.base_path / clean_id).resolve()
        if not str(job_root).startswith(str(self.base_path)):
            raise StorageSecurityError(f"Path traversal detected for job ID: {job_id}")
        return job_root

    def create_job_dirs(self, job_id: str) -> Dict[str, Path]:
        """Creates isolated subdirectories for a job: source, working, output."""
        job_root = self._get_job_root(job_id)
        dirs = {
            "root": job_root,
            "source": job_root / "source",
            "working": job_root / "working",
            "output": job_root / "output",
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        return dirs

    def get_job_dir(self, job_id: str, subfolder: str = "") -> Path:
        job_root = self._get_job_root(job_id)
        if subfolder:
            target = (job_root / subfolder).resolve()
            if not str(target).startswith(str(job_root)):
                raise StorageSecurityError("Illegal subfolder traversal attempt.")
            return target
        return job_root

    def get_output_file(self, job_id: str) -> Optional[Path]:
        """Locates the final processed media file in the job's output directory."""
        output_dir = self.get_job_dir(job_id, "output")
        if not output_dir.exists():
            return None

        # Find first non-empty file in output dir
        for item in output_dir.iterdir():
            if item.is_file() and item.stat().st_size > 0:
                return item
        return None

    def delete_job_dir(self, job_id: str) -> bool:
        """Completely purges a job's temporary directory and files."""
        try:
            job_root = self._get_job_root(job_id)
            if job_root.exists() and job_root.is_dir():
                shutil.rmtree(job_root, ignore_errors=True)
                logger.info(f"Purged storage directory for job {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error purging storage for job {job_id}: {str(e)}")
            return False

    def exists(self, path: Path) -> bool:
        return path.exists()

storage_service = StorageService()
