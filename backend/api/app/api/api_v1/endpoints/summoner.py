from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
import pymongo

from app.schemas.summoner import SummonerCreate, Summoner
from app.crud.crud_summoner import SummonerCRUD

router = APIRouter()


@router.get("/", summary="Returns a list of all summoners in the database.", response_model=List[Summoner])
async def get_all_summoners():
    return await SummonerCRUD.get_all_summoners()


@router.post("/", summary="Adds a new summoner to the database.", response_model=Summoner)
async def add_summoner(data: SummonerCreate):
    try:
        return await SummonerCRUD.add_summoner(data)
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Summoner already exists.")

