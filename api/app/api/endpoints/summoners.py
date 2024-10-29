from aiohttp import ClientResponseError
from db_models.models import Summoner, User
from fastapi import APIRouter, Depends, HTTPException
from pulsefire.clients import RiotAPIClient

from app.api import deps
from app.core.utils import platform_to_region
from app.schemas.requests import SummonerCreateRequest

router = APIRouter()


@router.post('', response_model=Summoner)
async def create_summoner(
    summoner_in: SummonerCreateRequest,
    current_user: User = Depends(deps.get_current_user),
    client: RiotAPIClient = Depends(deps.get_riot_client),
):
    summoner = await Summoner.find_one(
        Summoner.gameName == summoner_in.gameName,
        Summoner.tagLine == summoner_in.tagLine,
        Summoner.platform == summoner_in.platform,
    )
    if summoner is not None:
        raise HTTPException(status_code=409, detail='Summoner already exists')

    try:
        riot_account = await client.get_account_v1_by_riot_id(
            region=platform_to_region(summoner_in.platform),
            game_name=summoner_in.gameName,
            tag_line=summoner_in.tagLine,
        )
    except ClientResponseError as e:
        if e.status == 404:
            raise HTTPException(status_code=404, detail='Account not found')
        elif e.status == 429:
            raise HTTPException(status_code=429, detail='Rate limit exceeded')
        else:
            raise HTTPException(status_code=500, detail=f'Internal Server Error: {e}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Internal Server Error: {e}')

    try:
        riot_summoner = await client.get_lol_summoner_v4_by_puuid(
            region=summoner_in.platform, puuid=riot_account['puuid']
        )
    except ClientResponseError as e:
        if e.status == 404:
            raise HTTPException(status_code=404, detail='Summoner not found')
        elif e.status == 429:
            raise HTTPException(status_code=429, detail='Rate limit exceeded')
        else:
            raise HTTPException(status_code=500, detail=f'Internal Server Error: {e}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Internal Server Error: {e}')

    summoner = Summoner(
        **riot_summoner,
        gameName=riot_account['gameName'],
        tagLine=riot_account['tagLine'],
        platform=summoner_in.platform.lower(),
    )

    return await summoner.insert()


@router.get('/{puuid}', response_model=Summoner)
async def get_summoner(
    puuid: str,
):
    summoner = await Summoner.find_one(Summoner.puuid == puuid)
    if summoner is None:
        raise HTTPException(status_code=404, detail='Summoner not found')
    return summoner


@router.get('', response_model=list[Summoner])
async def get_summoners():
    summoners = await Summoner.find_all().to_list()
    return summoners


@router.delete('/{puuid}', status_code=204)
async def delete_summoner(
    puuid: str,
    current_user: User = Depends(deps.get_current_user),
):
    summoner = await Summoner.find_one(Summoner.puuid == puuid)
    if summoner is None:
        raise HTTPException(status_code=404, detail='Summoner not found')
    await summoner.delete()
    return None
