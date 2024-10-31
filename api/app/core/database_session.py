# database_session.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from app.core.config import get_settings

_MONGO_CLIENT: Optional[AsyncIOMotorClient] = None
_MONGO_DB: Optional[AsyncIOMotorDatabase] = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _MONGO_CLIENT
    if _MONGO_CLIENT is None:
        settings = get_settings()
        _MONGO_CLIENT = AsyncIOMotorClient(
            settings.mongodb.uri,
            maxPoolSize=5,
            minPoolSize=1,
            maxIdleTimeMS=30000,  # 30 seconds
            connectTimeoutMS=30000,  # 30 seconds
            serverSelectionTimeoutMS=30000,  # 30 seconds
        )
    return _MONGO_CLIENT


def get_database() -> AsyncIOMotorDatabase:
    global _MONGO_DB
    if _MONGO_DB is None:
        settings = get_settings()
        client = get_mongo_client()
        _MONGO_DB = client[settings.mongodb.database]
    return _MONGO_DB


async def close_mongo_connection() -> None:
    global _MONGO_CLIENT
    if _MONGO_CLIENT is not None:
        _MONGO_CLIENT.close()
        _MONGO_CLIENT = None
