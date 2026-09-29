from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional
from app.services.release_service import release_service
from app.utils.logger import logger

router = APIRouter(prefix="/app", tags=["app"])

class DeviceRegistrationRequest(BaseModel):
    device_id: str = Field(..., description="Unique anonymous device identifier")
    fcm_token: Optional[str] = Field(None, description="Firebase Cloud Messaging push token")
    app_version: str = Field(..., description="Currently installed app versionName, e.g. 1.5.8")
    version_code: int = Field(..., description="Currently installed versionCode, e.g. 23")
    platform: str = Field("android", description="Platform OS")
    android_version: Optional[str] = Field(None, description="Android OS version")
    notification_enabled: bool = Field(True, description="Whether notifications are permitted")

@router.get("/version")
async def get_app_version():
    """
    Returns latest published version metadata, changelog,
    and direct APK download link for in-app updates.
    """
    data = await release_service.get_latest_version()
    return JSONResponse(status_code=status.HTTP_200_OK, content=data)

@router.get("/download")
async def download_latest_apk():
    """
    Directly redirects (302) to the latest verified APK binary on CDN/GitHub.
    Zero bandwidth consumed on Render.
    """
    data = await release_service.get_latest_version()
    apk_url = data.get("apk_url", "https://github.com/subhankar3012/mediaflow/releases/latest/download/MediaFlow-release.apk")
    return RedirectResponse(url=apk_url, status_code=status.HTTP_302_FOUND)

@router.post("/register-device")
async def register_device(req: DeviceRegistrationRequest):
    """
    Registers an anonymous device installation for telemetry and push notifications.
    """
    success = await release_service.register_device(req.model_dump())
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "registered" if success else "deferred"}
    )
