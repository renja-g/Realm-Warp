from fastapi import APIRouter

from v1.endpoints import summoner

router = APIRouter()

router.include_router(summoner.router, prefix="/summoner", tags=["Summoner"])
