from fastapi import APIRouter

from app.api.api_v1.endpoints import summoner

api_router = APIRouter()
api_router.include_router(summoner.router, prefix="/summoners", tags=["summoners"])

