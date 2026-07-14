import asyncio

import cloudinary
import cloudinary.api
import cloudinary.uploader

from app.core.config import settings
from app.infrastructure.logging import create_logger

logger = create_logger(__name__)

_initialized = False


def init_cloudinary():
    global _initialized
    if _initialized:
        return
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )
    _initialized = True


async def upload_image(file_bytes: bytes, folder: str = "erp_products") -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _upload_sync(file_bytes, folder))


def _upload_sync(file_bytes: bytes, folder: str) -> dict:
    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        resource_type="image",
    )
    return {
        "secure_url": result.get("secure_url"),
        "public_id": result.get("public_id"),
    }


async def delete_image(public_id: str):
    if not public_id:
        return
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, lambda: cloudinary.uploader.destroy(public_id))
    except Exception as e:
        logger.warning("cloudinary_delete_failed", public_id=public_id, error=str(e))
