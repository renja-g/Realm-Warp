from contextlib import asynccontextmanager
from beanie import init_beanie
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.api_v1.router import api_router
from app.core.config import settings
from app.models.summoner import Summoner

async def load_app_resources():
    """
    Load application resources before the application starts taking requests.
    """
    db_client = AsyncIOMotorClient(settings.MONGODB_URI)
    
    await init_beanie(
        database=db_client[settings.DB_NAME],
        document_models=[
            Summoner
        ]
    )

async def unload_app_resources():
    """
    Unload application resources after the application finishes handling requests.
    """
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager for application lifespan.
    """
    await load_app_resources()
    try:
        yield
    finally:
        await unload_app_resources()

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
