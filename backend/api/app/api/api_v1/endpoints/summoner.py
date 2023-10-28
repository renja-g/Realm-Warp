from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, status
import pymongo

from app.schemas.summoner import SummonerCreate, Summoner
from app.crud.crud_summoner import SummonerCRUD

router = APIRouter()


@router.get("/", summary="Returns a list of all summoners in the database.", response_model=List[Summoner])
async def get_all_summoners(
    skip: int = 0,
    limit: int = 100,
):
    return await SummonerCRUD.get_multi(skip=skip, limit=limit)


@router.get("/{summoner_puuid}", summary="Returns a summoner with the given puuid.", response_model=Summoner)
async def get_by_puuid(summoner_puuid: str):
    summoner = await SummonerCRUD.by_puuid(puuid=summoner_puuid)
    if not summoner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summoner not found."
        )
    return summoner



@router.post("/", summary="Adds a new summoner to the database.", response_model=Summoner)
async def add_summoner(data: SummonerCreate):
    try:
        return await SummonerCRUD.add_summoner(data)
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Summoner already exists in the database."
        )
