from fastapi import APIRouter
from pydantic import BaseModel

from classes.regions import Regions
from classes.summoner import Summoner


class PostSummoner(BaseModel):
    puuid: str
    server: Regions


exampleResponse = {
    "id": "p3c0E1zvbMUODVXzo-2Eo9RjKcwoR-VCp0_xJ_RZg-SmnHo",
    "puuid": "f5dHa2VhPzjzMQ1m_PpnCW7mYTYUssowM5UGJxYplGRCpQ0uS6UG9QZ4CLJzK0cYI4ocnPIAQNM9rw",
    "name": "G5 Easy",
    "profileIconId": 5641,
    "summonerLevel": 377,
    "platform": "euw",
    "lastMatchId": "EUW1_6581625862",
    "league_entries": {
        "440": {
            "leagueId": "416d3a16-4060-477c-b63e-a5a7ce029472",
            "queueType": "RANKED_FLEX_SR",
            "tier": "EMERALD",
            "rank": "IV",
            "leaguePoints": 26,
            "wins": 39,
            "losses": 49,
            "veteran": False,
            "inactive": False,
            "freshBlood": True,
            "hotStreak": False,
        },
        "420": {
            "leagueId": "2455c6d2-8648-4694-bf58-8ebaf9f9da70",
            "queueType": "RANKED_SOLO_5x5",
            "tier": "PLATINUM",
            "rank": "III",
            "leaguePoints": 0,
            "wins": 21,
            "losses": 26,
            "veteran": False,
            "inactive": False,
            "freshBlood": False,
            "hotStreak": False,
        },
    },
}

router = APIRouter()


@router.get("")
async def listAll():
    return [
        Summoner.model_validate(exampleResponse),
        Summoner.model_validate(exampleResponse),
        Summoner.model_validate(exampleResponse),
    ]


@router.get("/{puuid}")
async def getByPuuid():
    return Summoner.model_validate(exampleResponse)


@router.post("/{puuid}")
async def addUser(Summoner: PostSummoner):
    return "new"


@router.delete("/{puuid}")
async def removeUser():
    return "delete"
