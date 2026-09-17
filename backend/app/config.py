import os
from pathlib import Path
from typing import List, Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    LOG_LEVEL: str = "INFO"

    # Database Adapter: 'supabase' (required in prod), 'sqlite', or 'memory'
    DB_ADAPTER: Literal["supabase", "sqlite", "memory"] = "sqlite"
    SQLITE_DB_PATH: str = "./downloader.db"

    # Supabase Credentials
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Admin & Security
    ADMIN_API_KEY: str = ""
    TRUSTED_PROXIES: str = "127.0.0.1,::1"

    # Storage & Temporary Directories
    DOWNLOADER_TEMP_ROOT: Optional[str] = None
    TEMP_STORAGE_PATH: str = ""
    MAX_OUTPUT_SIZE_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB

    # Limits and Expiration
    MAX_JOB_DURATION_SECONDS: int = 1800      # 30 mins
    JOB_EXPIRATION_MINUTES: int = 60          # 60 mins
    ANALYSIS_EXPIRATION_MINUTES: int = 60     # 60 mins

    # Concurrency and Rate Limiting
    MAX_CONCURRENT_JOBS_GLOBAL: int = 5
    MAX_CONCURRENT_JOBS_PER_SESSION: int = 2
    MAX_REQUESTS_PER_MINUTE: int = 60

    # Adaptive Concurrency Guardrails & Resource Thresholds
    MAX_ACTIVE_JOBS_HARD_LIMIT: int = 10
    MAX_ACTIVE_HEAVY_TRANSCODES: int = 2
    MAX_QUEUE_DEPTH: int = 25
    MIN_FREE_DISK_SPACE_GB: float = 3.0
    MIN_AVAILABLE_RAM_MB: float = 500.0
    CPU_HIGH_THRESHOLD: float = 85.0
    CPU_CRITICAL_THRESHOLD: float = 95.0
    DISK_SAFETY_MULTIPLIER: float = 2.5
    DISK_SAFETY_BUFFER_MB: float = 500.0

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def temp_storage_dir(self) -> Path:
        import tempfile
        # Determine project root
        project_root = Path(__file__).resolve().parent.parent.parent

        candidate = None
        if self.DOWNLOADER_TEMP_ROOT:
            candidate = Path(self.DOWNLOADER_TEMP_ROOT).resolve()
        elif self.TEMP_STORAGE_PATH:
            candidate = Path(self.TEMP_STORAGE_PATH).resolve()

        # If candidate is within the project root, prevent storing inside repo/OneDrive
        if candidate:
            try:
                if candidate == project_root or candidate.is_relative_to(project_root):
                    candidate = None
            except (ValueError, AttributeError):
                pass

        if candidate is None:
            candidate = Path(tempfile.gettempdir()) / "media_downloader"

        candidate.mkdir(parents=True, exist_ok=True)
        return candidate

    @field_validator("DB_ADAPTER")
    @classmethod
    def validate_production_db(cls, v: str, info) -> str:
        # Prevent non-Supabase db in production
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production" and v != "supabase":
            raise ValueError(
                "Production environment MUST use Supabase PostgreSQL (DB_ADAPTER='supabase'). "
                "Silent fallback to local databases is strictly forbidden."
            )
        return v

    def validate_credentials(self) -> None:
        if self.DB_ADAPTER == "supabase":
            if not self.SUPABASE_URL or not self.SUPABASE_SERVICE_ROLE_KEY:
                raise ValueError(
                    "DB_ADAPTER is set to 'supabase' but SUPABASE_URL or "
                    "SUPABASE_SERVICE_ROLE_KEY is missing."
                )

settings = Settings()
