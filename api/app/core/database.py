from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel
from pymongo.errors import DuplicateKeyError

from app.core.config import get_settings
from app.core.security.password import get_password_hash

_MONGO_CLIENT: AsyncIOMotorClient | None = None
_MONGO_DB: AsyncIOMotorDatabase | None = None


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


async def init_db() -> None:
    db = get_database()

    await db["users"].create_indexes([IndexModel([("email", ASCENDING)], unique=True)])

    settings = get_settings()
    try:
        await db["users"].update_one(
            {"email": settings.security.root_username},
            {
                "$setOnInsert": {
                    "email": settings.security.root_username,
                    "hashed_password": get_password_hash(
                        settings.security.root_password.get_secret_value()
                    ),
                }
            },
            upsert=True,
        )
    except DuplicateKeyError:
        # User already exists, no need to do anything
        pass
