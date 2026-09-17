import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.database.repositories.base import BaseRepository
from app.database.supabase import supabase_provider
from app.utils.logger import logger

class SupabaseRepository(BaseRepository):
    """
    Supabase PostgreSQL repository implementation.
    Operates strictly against Supabase tables without silent fallback.
    All synchronous PostgREST client executions are dispatched via asyncio.to_thread
    to prevent blocking the main asyncio event loop.
    """

    def __init__(self):
        self.client = supabase_provider.get_client()

    @staticmethod
    async def _execute_async(query):
        for attempt in range(3):
            try:
                return await asyncio.to_thread(query.execute)
            except Exception as e:
                err_str = str(e)
                if ("10035" in err_str or "ReadError" in err_str) and attempt < 2:
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                raise

    async def create_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        query = self.client.table("media_analyses").insert(analysis_data)
        response = await self._execute_async(query)
        if response.data:
            return response.data[0]
        raise RuntimeError("Failed to insert media analysis record into Supabase.")

    @staticmethod
    def _is_valid_uuid(val: str) -> bool:
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    async def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        if not self._is_valid_uuid(analysis_id):
            return None
        try:
            query = self.client.table("media_analyses").select("*").eq("id", analysis_id)
            response = await self._execute_async(query)
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            if "22P02" in str(e):
                return None
            raise

    async def cleanup_expired_analyses(self, now: datetime) -> int:
        iso_now = now.isoformat()
        query = self.client.table("media_analyses").delete().lt("expires_at", iso_now)
        response = await self._execute_async(query)
        return len(response.data) if response.data else 0

    async def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        query = self.client.table("download_jobs").insert(job_data)
        response = await self._execute_async(query)
        if response.data:
            return response.data[0]
        raise RuntimeError("Failed to insert download job record into Supabase.")

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        if not self._is_valid_uuid(job_id):
            return None
        try:
            query = self.client.table("download_jobs").select("*").eq("id", job_id)
            response = await self._execute_async(query)
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            if "22P02" in str(e):
                return None
            raise

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
        update_data: Dict[str, Any] = {"status": status}
        if error_code is not None:
            update_data["error_code"] = error_code
        if error_message is not None:
            update_data["error_message"] = error_message
        if file_size is not None:
            update_data["file_size"] = file_size
        if temporary_file_key is not None:
            update_data["temporary_file_key"] = temporary_file_key
        if completed_at is not None:
            update_data["completed_at"] = completed_at
        if started_at is not None:
            update_data["started_at"] = started_at

        query = self.client.table("download_jobs").update(update_data).eq("id", job_id)
        response = await self._execute_async(query)
        if response.data:
            return response.data[0]
        return None

    async def update_job_progress(
        self,
        job_id: str,
        progress: float,
        downloaded_bytes: Optional[int] = None,
        total_bytes: Optional[int] = None,
        speed: Optional[str] = None,
        eta: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        update_data: Dict[str, Any] = {"progress": progress}
        if downloaded_bytes is not None:
            update_data["downloaded_bytes"] = downloaded_bytes
        if total_bytes is not None:
            update_data["total_bytes"] = total_bytes
        if speed is not None:
            update_data["speed"] = speed
        if eta is not None:
            update_data["eta"] = eta

        query = self.client.table("download_jobs").update(update_data).eq("id", job_id)
        response = await self._execute_async(query)
        if response.data:
            return response.data[0]
        return None

    async def get_expired_jobs(self, now: datetime) -> List[Dict[str, Any]]:
        iso_now = now.isoformat()
        query = self.client.table("download_jobs").select("*").lt("expires_at", iso_now).neq("status", "EXPIRED").neq("status", "PROCESSING")
        response = await self._execute_async(query)
        return response.data or []

    async def delete_job(self, job_id: str) -> bool:
        query = self.client.table("download_jobs").delete().eq("id", job_id)
        response = await self._execute_async(query)
        return bool(response.data)

    async def check_health(self) -> bool:
        try:
            # Perform a minimal lightweight select
            query = self.client.table("download_jobs").select("id").limit(1)
            await self._execute_async(query)
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {str(e)}")
            return False
