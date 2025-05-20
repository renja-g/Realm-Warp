from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api import deps
from app.core.utils import serialize_mongo_doc
from app.schemas.requests import QueueType

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
    if queue_type == QueueType.SOLO:
        queue_id = 420
    elif queue_type == QueueType.FLEX:
        queue_id = 440

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
                "_id": 1,
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
                                            {"$ne": ["$$this.k", "matches"]},
                                        ]
                                    },
                                }
                            }
                        }
                    ]
                },
                "league": "$league",
            }
        },
        {
            "$lookup": {
                "from": "matches",
                "foreignField": "ref_summoners",
                "localField": "_id",
                "let": {"summoner_puuid": "$summoner.puuid"},
                "pipeline": [
                    {"$match": {"info.queueId": queue_id}},
                    {"$sort": {"info.gameEndTimestamp": -1}},
                    {"$limit": 20},
                    {
                        "$project": {
                            "_id": 0,
                            "metadata.matchId": 1,
                            "info.gameEndTimestamp": 1,
                            "info.gameDuration": 1,
                            "participant": {
                                "$let": {
                                    "vars": {
                                        "participant": {
                                            "$arrayElemAt": [
                                                {
                                                    "$filter": {
                                                        "input": "$info.participants",
                                                        "cond": {
                                                            "$eq": [
                                                                "$$this.puuid",
                                                                "$$summoner_puuid",
                                                            ]
                                                        },
                                                    }
                                                },
                                                0,
                                            ]
                                        }
                                    },
                                    "in": {
                                        "championId": "$$participant.championId",
                                        "win": "$$participant.win",
                                        "kills": "$$participant.kills",
                                        "deaths": "$$participant.deaths",
                                        "assists": "$$participant.assists",
                                        "teamPosition": "$$participant.teamPosition",
                                        "individualPosition": "$$participant.individualPosition",
                                        "gameEndedInEarlySurrender": "$$participant.gameEndedInEarlySurrender",
                                        "league": {
                                            "leaguePoints": "$$participant.league.leaguePoints",
                                            "tier": "$$participant.league.tier",
                                            "rank": "$$participant.league.rank",
                                        },
                                    },
                                }
                            },
                        }
                    },
                ],
                "as": "matches",
            }
        },
        {
            "$project": {
                "_id": 1,
                "summoner": 1,
                "league": 1,
                "matches": {
                    "$map": {
                        "input": "$matches",
                        "as": "match",
                        "in": {
                            "matchId": "$$match.metadata.matchId",
                            "gameEndTimestamp": "$$match.info.gameEndTimestamp",
                            "remake": {
                                "$and": [
                                    {"$lt": ["$$match.info.gameDuration", "300"]},
                                    {
                                        "$eq": [
                                            "$$match.participant.gameEndedInEarlySurrender",
                                            True,
                                        ]
                                    },
                                ]
                            },
                            "championId": "$$match.participant.championId",
                            "win": "$$match.participant.win",
                            "kills": "$$match.participant.kills",
                            "deaths": "$$match.participant.deaths",
                            "assists": "$$match.participant.assists",
                            "teamPosition": "$$match.participant.teamPosition",
                            "individualPosition": "$$match.participant.individualPosition",
                            "league": "$$match.participant.league",
                        },
                    }
                },
            }
        },
    ]

    result = await db.summoners.aggregate(pipeline).to_list(length=None)
    return serialize_mongo_doc(result)
