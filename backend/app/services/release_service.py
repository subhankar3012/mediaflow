import time
import asyncio
from typing import Optional, Dict, Any
import httpx
from app.config import settings
from app.utils.logger import logger
from app.database.supabase import supabase_provider

class ReleaseService:
    """
    Manages mobile app update metadata, release distribution,
    and anonymous device registrations.
    """

    CACHE_TTL_SECONDS = 300  # 5 minutes in-memory cache

    def __init__(self):
        self._cached_release: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0
        self._lock = asyncio.Lock()

    async def get_latest_version(self) -> Dict[str, Any]:
        """
        Retrieves the latest available version metadata.
        Priority:
        1. In-memory cache (if fresh)
        2. Supabase app_releases table
        3. GitHub Releases API
        4. Hardcoded baseline fallback
        """
        now = time.time()
        if self._cached_release and (now - self._cache_timestamp) < self.CACHE_TTL_SECONDS:
            return self._cached_release

        async with self._lock:
            # Re-check inside lock
            if self._cached_release and (time.time() - self._cache_timestamp) < self.CACHE_TTL_SECONDS:
                return self._cached_release

            # 1. Try Supabase
            release = await self._fetch_from_supabase()
            if not release:
                # 2. Try GitHub Releases API
                release = await self._fetch_from_github()

            if not release:
                # 3. Hardcoded fallback baseline
                release = self._get_default_release()

            self._cached_release = release
            self._cache_timestamp = time.time()
            return release

    async def _fetch_from_supabase(self) -> Optional[Dict[str, Any]]:
        """Queries the app_releases table from Supabase if configured."""
        try:
            client = supabase_provider.get_client()
            if not client:
                return None

            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(
                None,
                lambda: client.table("app_releases")
                .select("version_code, version_name, apk_url, release_notes, is_mandatory, min_supported_version")
                .order("version_code", desc=True)
                .limit(1)
                .execute()
            )

            if res and res.data and len(res.data) > 0:
                row = res.data[0]
                return {
                    "latest_version": str(row.get("version_name", "1.5.8")),
                    "version_code": int(row.get("version_code", 23)),
                    "apk_url": str(row.get("apk_url", "https://github.com/subhankar3012/mediaflow/releases/latest/download/MediaFlow-release.apk")),
                    "release_notes": str(row.get("release_notes", "")),
                    "is_mandatory": bool(row.get("is_mandatory", False)),
                    "min_supported_version": int(row.get("min_supported_version", 20)),
                }
        except Exception as e:
            logger.debug(f"Supabase release lookup skipped/failed: {e}")
        return None

    async def _fetch_from_github(self) -> Optional[Dict[str, Any]]:
        """Queries GitHub latest release API as an automatic fallback."""
        url = "https://api.github.com/repos/subhankar3012/mediaflow/releases/latest"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MediaFlow-UpdateService/1.0"
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    tag = data.get("tag_name", "v1.5.8").lstrip("v")
                    body = data.get("body", "")

                    # Locate APK asset URL if available
                    apk_url = "https://github.com/subhankar3012/mediaflow/releases/latest/download/MediaFlow-release.apk"
                    for asset in data.get("assets", []):
                        if asset.get("name", "").endswith(".apk"):
                            apk_url = asset.get("browser_download_url", apk_url)
                            break

                    # Guess version code or compute from tag
                    # e.g., 1.5.8 -> 23
                    parts = [int(p) for p in tag.split(".") if p.isdigit()]
                    code = 23
                    if len(parts) >= 3 and parts[0] == 1 and parts[1] == 5:
                        code = 15 + parts[2]  # 1.5.8 -> 23

                    return {
                        "latest_version": tag,
                        "version_code": code,
                        "apk_url": apk_url,
                        "release_notes": body or "• General performance & stability improvements.",
                        "is_mandatory": False,
                        "min_supported_version": 20
                    }
        except Exception as e:
            logger.debug(f"GitHub release lookup skipped/failed: {e}")
        return None

    def _get_default_release(self) -> Dict[str, Any]:
        """Baseline fallback when remote sources are unavailable."""
        return {
            "latest_version": "1.5.8",
            "version_code": 23,
            "apk_url": "https://github.com/subhankar3012/mediaflow/releases/latest/download/MediaFlow-release.apk",
            "release_notes": (
                "• In-app update system with native FileProvider installer\n"
                "• High-priority Android update notifications\n"
                "• Dynamic OS-level version detection\n"
                "• Fixed X/Twitter photo & video downloads with Syndication API\n"
                "• Reddit direct image and v.redd.it audio-video muxing\n"
                "• ImageQualityResolver: Original resolution for X, Reddit, Pinterest\n"
                "• Fast video thumbnails in Library via native MediaMetadataRetriever"
            ),
            "is_mandatory": False,
            "min_supported_version": 20
        }

    async def register_device(self, device_data: Dict[str, Any]) -> bool:
        """Upserts an anonymous device record into app_devices table in Supabase."""
        try:
            client = supabase_provider.get_client()
            if not client:
                return False

            device_id = device_data.get("device_id")
            if not device_id:
                return False

            payload = {
                "device_id": str(device_id),
                "fcm_token": device_data.get("fcm_token"),
                "app_version": str(device_data.get("app_version", "1.5.8")),
                "version_code": int(device_data.get("version_code", 23)),
                "platform": str(device_data.get("platform", "android")),
                "android_version": device_data.get("android_version"),
                "notification_enabled": bool(device_data.get("notification_enabled", True)),
                "last_seen": "now()"
            }

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: client.table("app_devices").upsert(payload, on_conflict="device_id").execute()
            )
            return True
        except Exception as e:
            logger.warning(f"Device registration failed: {e}")
            return False

release_service = ReleaseService()
