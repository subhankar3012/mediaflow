from typing import Optional
from app.config import settings
from app.utils.logger import logger

class SupabaseClientProvider:
    """Manages the official Supabase client connection."""

    def __init__(self):
        self._client = None

    def get_client(self):
        if self._client is not None:
            return self._client

        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError(
                "Supabase is configured as DB_ADAPTER, but SUPABASE_URL or "
                "SUPABASE_SERVICE_ROLE_KEY is missing from environment."
            )

        try:
            from supabase import create_client, Client
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            logger.info("Supabase PostgreSQL client successfully initialized.")
            return self._client
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise

supabase_provider = SupabaseClientProvider()
