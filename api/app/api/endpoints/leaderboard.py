from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api import deps
from app.schemas.requests import QueueType
from app.core.utils import serialize_mongo_doc

router = APIRouter()

@router.get(
    "",
    response_model=list[dict],
    description="Get a leaderboard of all summoners in the database",
)
async def get_leaderboard(
    queue_type: QueueType,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
) -> list[dict]:
    pipeline = [
        {
            "$lookup": {
                "from": "league_entries",
                "localField": "_id",
                "foreignField": "ref_summoner",
                "as": "league",
            }
        },
        {"$unwind": "$league"},
        {"$match": {"league.queueType": queue_type.value}},
        {
            "$addFields": {
                "tierScore": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$league.tier", "IRON"]}, "then": 0},
                            {"case": {"$eq": ["$league.tier", "BRONZE"]}, "then": 400},
                            {"case": {"$eq": ["$league.tier", "SILVER"]}, "then": 800},
                            {"case": {"$eq": ["$league.tier", "GOLD"]}, "then": 1200},
                            {
                                "case": {"$eq": ["$league.tier", "PLATINUM"]},
                                "then": 1600,
                            },
                            {
                                "case": {"$eq": ["$league.tier", "EMERALD"]},
                                "then": 2000,
                            },
                            {
                                "case": {"$eq": ["$league.tier", "DIAMOND"]},
                                "then": 2400,
                            },
                            {"case": {"$eq": ["$league.tier", "MASTER"]}, "then": 2800},
                            {
                                "case": {"$eq": ["$league.tier", "GRANDMASTER"]},
                                "then": 2800,
                            },
                            {
                                "case": {"$eq": ["$league.tier", "CHALLENGER"]},
                                "then": 2800,
                            },
                        ],
                        "default": 0,
                    }
                },
                "rankScore": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$league.rank", "IV"]}, "then": 0},
                            {"case": {"$eq": ["$league.rank", "III"]}, "then": 100},
                            {"case": {"$eq": ["$league.rank", "II"]}, "then": 200},
                            {"case": {"$eq": ["$league.rank", "I"]}, "then": 300},
                        ],
                        "default": 0,
                    }
                },
            }
        },
        {"$sort": {"tierScore": -1, "rankScore": -1, "league.leaguePoints": -1}},
        {
            "$project": {
                "summoner": {
                    "$mergeObjects": [
                        {
                            "$arrayToObject": {
                                "$filter": {
                                    "input": {"$objectToArray": "$$ROOT"},
                                    "cond": {
                                        "$and": [
                                            {"$ne": ["$$this.k", "tierScore"]},
                                            {"$ne": ["$$this.k", "rankScore"]},
                                            {"$ne": ["$$this.k", "league"]},
                                        ]
                                    },
                                }
                            }
                        },
                        {"_id": {"$toString": "$_id"}},
                    ]
                },
                "league": {
                    "$mergeObjects": [
                        "$league",
                        {
                            "_id": {"$toString": "$league._id"},
                            "ref_summoner": {"$toString": "$league.ref_summoner"},
                        },
                    ]
                },
            }
        },
    ]

    result = await db.summoners.aggregate(pipeline).to_list(length=None)
    return serialize_mongo_doc(result)
