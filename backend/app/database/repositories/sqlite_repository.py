import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.config import settings
from app.database.repositories.base import BaseRepository
from app.utils.logger import logger

class SQLiteRepository(BaseRepository):
    """
    Explicit SQLite/In-memory repository implementation for local development.
    Guarantees exact schema parity with Supabase PostgreSQL tables.
    Dispatches synchronous database I/O to worker threads via asyncio.to_thread.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media_analyses (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    source_url TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    title TEXT,
                    thumbnail TEXT,
                    duration INTEGER,
                    uploader TEXT,
                    normalized_formats TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    is_gallery INTEGER DEFAULT 0,
                    gallery_items TEXT DEFAULT '[]'
                );
            """)
            # Auto-migrate SQLite if columns are missing in an existing database
            try:
                cursor.execute("ALTER TABLE media_analyses ADD COLUMN is_gallery INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE media_analyses ADD COLUMN gallery_items TEXT DEFAULT '[]'")
            except Exception:
                pass
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_jobs (
                    id TEXT PRIMARY KEY,
                    analysis_id TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    source_url TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    title TEXT,
                    status TEXT NOT NULL,
                    requested_format TEXT,
                    output_format TEXT,
                    progress REAL NOT NULL DEFAULT 0,
                    downloaded_bytes INTEGER,
                    total_bytes INTEGER,
                    speed TEXT,
                    eta TEXT,
                    file_size INTEGER,
                    temporary_file_key TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    expires_at TEXT
                );
            """)
            conn.commit()
            logger.info(f"SQLite repository initialized at {self.db_path}")

    def _sync_create_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(analysis_data)
        if isinstance(data.get("normalized_formats"), (list, dict)):
            data["normalized_formats"] = json.dumps(data["normalized_formats"])
        if isinstance(data.get("gallery_items"), (list, dict)):
            data["gallery_items"] = json.dumps(data["gallery_items"])
        if "is_gallery" in data:
            data["is_gallery"] = 1 if data["is_gallery"] else 0

        keys = list(data.keys())
        placeholders = [f":{k}" for k in keys]
        sql = f"INSERT INTO media_analyses ({', '.join(keys)}) VALUES ({', '.join(placeholders)})"

        with self._get_connection() as conn:
            conn.cursor().execute(sql, data)
            conn.commit()
        return self._sync_get_analysis(data["id"]) or analysis_data

    async def create_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        return await asyncio.to_thread(self._sync_create_analysis, analysis_data)

    def _sync_get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM media_analyses WHERE id = ?", (analysis_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            if "normalized_formats" in res and isinstance(res["normalized_formats"], str):
                try:
                    res["normalized_formats"] = json.loads(res["normalized_formats"])
                except Exception:
                    pass
            if "gallery_items" in res and isinstance(res["gallery_items"], str):
                try:
                    res["gallery_items"] = json.loads(res["gallery_items"])
                except Exception:
                    res["gallery_items"] = []
            if "is_gallery" in res:
                res["is_gallery"] = bool(res["is_gallery"])
            return res

    async def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._sync_get_analysis, analysis_id)

    def _sync_cleanup_expired_analyses(self, iso_now: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM media_analyses WHERE expires_at < ?", (iso_now,))
            conn.commit()
            return cursor.rowcount

    async def cleanup_expired_analyses(self, now: datetime) -> int:
        return await asyncio.to_thread(self._sync_cleanup_expired_analyses, now.isoformat())

    def _sync_create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(job_data)
        keys = list(data.keys())
        placeholders = [f":{k}" for k in keys]
        sql = f"INSERT INTO download_jobs ({', '.join(keys)}) VALUES ({', '.join(placeholders)})"

        with self._get_connection() as conn:
            conn.cursor().execute(sql, data)
            conn.commit()
        return self._sync_get_job(data["id"]) or job_data

    async def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        return await asyncio.to_thread(self._sync_create_job, job_data)

    def _sync_get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM download_jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._sync_get_job, job_id)

    def _sync_update_job_status(self, job_id: str, updates_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = []
        params = {"id": job_id}
        for k, v in updates_dict.items():
            updates.append(f"{k} = :{k}")
            params[k] = v

        sql = f"UPDATE download_jobs SET {', '.join(updates)} WHERE id = :id"
        with self._get_connection() as conn:
            conn.cursor().execute(sql, params)
            conn.commit()
        return self._sync_get_job(job_id)

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
        updates_dict = {"status": status}
        if error_code is not None:
            updates_dict["error_code"] = error_code
        if error_message is not None:
            updates_dict["error_message"] = error_message
        if file_size is not None:
            updates_dict["file_size"] = file_size
        if temporary_file_key is not None:
            updates_dict["temporary_file_key"] = temporary_file_key
        if completed_at is not None:
            updates_dict["completed_at"] = completed_at
        if started_at is not None:
            updates_dict["started_at"] = started_at

        return await asyncio.to_thread(self._sync_update_job_status, job_id, updates_dict)

    def _sync_update_job_progress(self, job_id: str, updates_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = []
        params = {"id": job_id}
        for k, v in updates_dict.items():
            updates.append(f"{k} = :{k}")
            params[k] = v

        sql = f"UPDATE download_jobs SET {', '.join(updates)} WHERE id = :id"
        with self._get_connection() as conn:
            conn.cursor().execute(sql, params)
            conn.commit()
        return self._sync_get_job(job_id)

    async def update_job_progress(
        self,
        job_id: str,
        progress: float,
        downloaded_bytes: Optional[int] = None,
        total_bytes: Optional[int] = None,
        speed: Optional[str] = None,
        eta: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        updates_dict = {"progress": progress}
        if downloaded_bytes is not None:
            updates_dict["downloaded_bytes"] = downloaded_bytes
        if total_bytes is not None:
            updates_dict["total_bytes"] = total_bytes
        if speed is not None:
            updates_dict["speed"] = speed
        if eta is not None:
            updates_dict["eta"] = eta

        return await asyncio.to_thread(self._sync_update_job_progress, job_id, updates_dict)

    def _sync_get_expired_jobs(self, iso_now: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM download_jobs WHERE expires_at < ? AND status NOT IN ('EXPIRED', 'PROCESSING')",
                (iso_now,)
            )
            return [dict(r) for r in cursor.fetchall()]

    async def get_expired_jobs(self, now: datetime) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._sync_get_expired_jobs, now.isoformat())

    def _sync_delete_job(self, job_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM download_jobs WHERE id = ?", (job_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def delete_job(self, job_id: str) -> bool:
        return await asyncio.to_thread(self._sync_delete_job, job_id)

    async def check_health(self) -> bool:
        def _check():
            try:
                with self._get_connection() as conn:
                    conn.cursor().execute("SELECT 1")
                    return True
            except Exception:
                return False
        return await asyncio.to_thread(_check)
