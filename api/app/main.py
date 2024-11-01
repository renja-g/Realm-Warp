from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.api_router import api_router, auth_router
from app.core.config import get_settings
from app.core.database import close_mongo_connection, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Realm Warp API",
    version="1.0.0",
    description="https://github.com/renja-g/Realm-Warp",
    openapi_url="/openapi.json",
    docs_url="/",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(api_router)

# Sets all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        str(origin).rstrip("/")
        for origin in get_settings().security.backend_cors_origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Guards against HTTP Host Header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=get_settings().security.allowed_hosts,
)
