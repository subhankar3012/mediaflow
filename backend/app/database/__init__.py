from app.config import settings
from app.database.repositories.base import BaseRepository
from app.database.repositories.supabase_repository import SupabaseRepository
from app.database.repositories.sqlite_repository import SQLiteRepository
from app.utils.logger import logger

def get_repository() -> BaseRepository:
    """
    Factory function returning the explicitly configured repository.
    Enforces that production environments MUST use Supabase PostgreSQL.
    """
    if settings.ENVIRONMENT == "production" and settings.DB_ADAPTER != "supabase":
        raise RuntimeError(
            "Production environment MUST use Supabase PostgreSQL (DB_ADAPTER='supabase'). "
            "Silent fallback is forbidden."
        )

    if settings.DB_ADAPTER == "supabase":
        settings.validate_credentials()
        logger.info("Using Supabase PostgreSQL repository.")
        return SupabaseRepository()
    elif settings.DB_ADAPTER in ("sqlite", "memory"):
        logger.info(f"Using local {settings.DB_ADAPTER.upper()} repository for development.")
        db_path = ":memory:" if settings.DB_ADAPTER == "memory" else settings.SQLITE_DB_PATH
        return SQLiteRepository(db_path=db_path)
    else:
        raise ValueError(f"Unsupported DB_ADAPTER: {settings.DB_ADAPTER}")

repository = get_repository()

__all__ = ["BaseRepository", "repository", "get_repository"]
