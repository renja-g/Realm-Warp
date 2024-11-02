from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api import deps
from app.schemas.responses import SummonerResponse
from app.schemas.requests import QueueType

router = APIRouter()


tier_dict = {
    "IRON": 0,
    "BRONZE": 400,
    "SILVER": 800,
    "GOLD": 1200,
    "PLATINUM": 1600,
    "EMERALD": 2000,
    "DIAMOND": 2400,
    "MASTER": 2800,
    "GRANDMASTER": 2800,
    "CHALLENGER": 2800,
}

rank_dict = {
    "IV": 0,
    "III": 100,
    "II": 200,
    "I": 300,
}


@router.get(
    "",
    response_model=list[dict],
    description="Get a leaderboard of all summoners in the database",
)
async def get_leaderboard(
    queue_type: QueueType,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
) -> list[dict]:
    summoners = await db.summoners.find().to_list(length=None)
    leaderboard = []

    for summoner in summoners:
        league = await db.league_entries.find_one({"ref_summoner": summoner["_id"], "queueType": queue_type.value})
        if league:
            leaderboard.append({
                "summoner": {**summoner, "_id": str(summoner["_id"])},
                "league": {**league, "_id": str(league["_id"]), "ref_summoner": str(league["ref_summoner"])},
            })

    leaderboard.sort(key=lambda x: (tier_dict[x["league"]["tier"]], rank_dict[x["league"]["rank"]], x["league"]["leaguePoints"]), reverse=True)
    return leaderboard
