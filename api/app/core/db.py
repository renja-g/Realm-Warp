from beanie import init_beanie
from db_models.models import __all_models__
from motor.motor_asyncio import AsyncIOMotorClient

from app.core import config


async def init_db() -> None:
    client = AsyncIOMotorClient(config.settings.DEFAULT_MONGODB_URI)
    db = client[config.settings.MONGO_DB]
    await init_beanie(database=db, document_models=__all_models__)
