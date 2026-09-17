from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List

class BaseRepository(ABC):
    """Database-agnostic repository interface for media analyses and download jobs."""

    @abstractmethod
    async def create_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def cleanup_expired_analyses(self, now: datetime) -> int:
        pass

    @abstractmethod
    async def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        file_size: Optional[int] = None,
        temporary_file_key: Optional[str] = None,
        completed_at: Optional[str] = None,
        started_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_job_progress(
        self,
        job_id: str,
        progress: float,
        downloaded_bytes: Optional[int] = None,
        total_bytes: Optional[int] = None,
        speed: Optional[str] = None,
        eta: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_expired_jobs(self, now: datetime) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def delete_job(self, job_id: str) -> bool:
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        pass
