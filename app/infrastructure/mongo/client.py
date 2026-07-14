from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings
from app.infrastructure.logging import create_logger

logger = create_logger(__name__)

_client: AsyncMongoClient | None = None


def get_client() -> AsyncMongoClient:
    if _client is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _client


def get_db() -> AsyncDatabase:
    client = get_client()
    return client[settings.DB_NAME]


async def init_db():
    global _client
    logger.info(
        "connecting_mongodb",
        uri=settings.MONGODB_URI.split("@")[-1]
        if "@" in settings.MONGODB_URI
        else settings.MONGODB_URI,
    )
    _client = AsyncMongoClient(
        settings.MONGODB_URI,
        maxPoolSize=10,
        minPoolSize=2,
        serverSelectionTimeoutMS=5000,
        socketTimeoutMS=45000,
    )
    await _client.admin.command("ping")
    logger.info("mongodb_connected")


async def close_db():
    global _client
    if _client:
        await _client.close()
        _client = None
        logger.info("mongodb_disconnected")
