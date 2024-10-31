import asyncio
import os
import logging

from dotenv import load_dotenv
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
)
from pulsefire.clients import RiotAPIClient
from pulsefire.schemas import RiotAPISchema
from pulsefire.ratelimiters import RiotAPIRateLimiter
from pulsefire.middlewares import (
    http_error_middleware,
    json_response_middleware,
    rate_limiter_middleware,
)
import orjson

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

ENV = os.getenv("ENV")

MONGODB__PORT = os.getenv("MONGODB__PORT")
MONGODB__HOST = os.getenv("MONGODB__HOST")
MONGODB__USERNAME = os.getenv("MONGODB__USERNAME")
MONGODB__PASSWORD = os.getenv("MONGODB__PASSWORD")

RIOT__API_KEY = os.getenv("RIOT__API_KEY")
RIOT__RATE_LIMITER_HOST = os.getenv("RIOT__RATE_LIMITER_HOST")
RIOT__RATE_LIMITER_PORT = os.getenv("RIOT__RATE_LIMITER_PORT")

if ENV == "DEV":
    MONGODB__HOST = "localhost"
    RIOT__RATE_LIMITER_HOST = "localhost"


client: AsyncIOMotorClient = AsyncIOMotorClient(
    f"mongodb://{MONGODB__USERNAME}:{MONGODB__PASSWORD}@{MONGODB__HOST}:{MONGODB__PORT}"
)
db: AsyncIOMotorDatabase = client["realm_warp"]
summoners_col: AsyncIOMotorCollection = db["summoners"]
matches_col: AsyncIOMotorCollection = db["matches"]
league_entries_col: AsyncIOMotorCollection = db["league_entries"]


PLATFORM_TO_REGION = {
    "br1": "americas",
    "eun1": "europe",
    "euw1": "europe",
    "jp1": "asia",
    "kr": "asia",
    "la1": "americas",
    "la2": "americas",
    "na1": "americas",
    "oc1": "sea",
    "tr1": "europe",
    "ru": "europe",
    "ph2": "sea",
    "sg2": "sea",
    "th2": "sea",
    "tw2": "sea",
    "vn2": "sea",
}

RANKED_QUEUE_IDS = [
    420,  # RANKED_SOLO_5x5
    440,  # RANKED_FLEX_SR
]

QUEUE_ID_TO_QUEUE_TYPE = {
    420: "RANKED_SOLO_5x5",
    440: "RANKED_FLEX_SR",
}


async def get_summoners_from_db() -> list[dict]:
    """Get all summoners from the db."""
    cursor = summoners_col.find({})
    summoners: list[dict] = await cursor.to_list(length=None)
    return summoners


async def update_summoner_profile(summoner) -> bool:
    """
    Check if the summoner profile has changed and update the db if necessary.

    Args:
    summoner (dict): The new summoner data to compare and potentially update.

    Returns:
    bool: True if the summoner was updated, False otherwise.
    """
    # Find the existing summoner in the database
    existing_summoner: dict | None = await summoners_col.find_one(
        {"_id": summoner["_id"]}
    )

    if not existing_summoner:
        # If the summoner doesn't exist in the database, insert it
        await summoners_col.insert_one(summoner)
        return True

    # Check if any fields have changed
    has_changed = any(
        existing_summoner.get(key) != value for key, value in summoner.items()
    )

    if has_changed:
        # Update the summoner in the database
        update_result = await summoners_col.update_one(
            {"_id": summoner["_id"]}, {"$set": summoner}
        )
        return update_result.modified_count > 0

    return False


async def get_summoner_from_api(client: RiotAPIClient, summoner: dict) -> dict:
    """Get the summoner data from the API."""
    api_account = await client.get_account_v1_by_puuid(
        region=PLATFORM_TO_REGION[summoner["platform"]], puuid=summoner["puuid"]
    )
    api_summoner = await client.get_lol_summoner_v4_by_puuid(
        region=summoner["platform"], puuid=summoner["puuid"]
    )

    # Merge the account and summoner data
    api_summoner = {
        **api_summoner,
        "gameName": api_account["gameName"],
        "tagLine": api_account["tagLine"],
        "platform": summoner["platform"],
        "_id": summoner["_id"],
    }
    api_summoner["summonerId"] = api_summoner.pop("id")
    return api_summoner


async def update_summoner_leagues(
    summoner, leagie_entries: list[RiotAPISchema.LolLeagueV4LeagueFullEntry]
) -> bool:
    """Update the summoner's leagues in the db."""
    for entry in leagie_entries:
        entry["ref_summoner"] = summoner["_id"]
        result = await league_entries_col.update_one(
            {"ref_summoner": summoner["_id"], "queueType": entry["queueType"]},
            {"$set": entry},
            upsert=True,
        )
        if result.modified_count > 0:
            return True
    return False


async def get_leagues_from_api(
    client: RiotAPIClient, summoner: dict
) -> list[RiotAPISchema.LolLeagueV4LeagueFullEntry]:
    """Get the summoner's leagues from the API."""
    leagues = await client.get_lol_league_v4_entries_by_summoner(
        region=summoner["platform"], summoner_id=summoner["summonerId"]
    )
    return leagues


async def transform_leagues(leagues: list[dict]) -> dict[str, dict[str, any]]:
    """
    Transform the leagues data to be saved in the db.
    {
        "RANKED_SOLO_5x5": {
            ...
        },
        "RANKED_FLEX_SR": {
            ...
        }
    }
    """
    return {
        league["queueType"]: {k: v for k, v in league.items() if k != "queueType"}
        for league in leagues
    }


async def update_summoner_matches(client: RiotAPIClient, summoner):
    """Update the summoner's matches in the db."""
    last_api_match_id = await client.get_lol_match_v5_match_ids_by_puuid(
        region=PLATFORM_TO_REGION[summoner["platform"]],
        puuid=summoner["puuid"],
        queries={"start": 0, "count": 1},
    )
    last_db_match = await matches_col.find_one(
        {"ref_summoners": {"$elemMatch": {"$eq": summoner["_id"]}}},
        sort=[("info.gameEndTimestamp", -1)],
    )

    if last_db_match and last_api_match_id[0] == last_db_match["metadata"]["matchId"]:
        return

    # Get the match details
    match_data = await matches_col.find_one({"metadata.matchId": last_api_match_id[0]})
    if not match_data:
        match_data = await client.get_lol_match_v5_match(
            region=PLATFORM_TO_REGION[summoner["platform"]],
            id=last_api_match_id[0],
        )

    # Link the match to the summoner
    if "ref_summoners" not in match_data:
        match_data["ref_summoners"] = []
    match_data["ref_summoners"].append(summoner["_id"])

    # Check if the match is a ranked match
    if match_data["info"]["queueId"] not in RANKED_QUEUE_IDS:
        # Save or update the match in the db
        await matches_col.update_one(
            {"metadata.matchId": match_data["metadata"]["matchId"]},
            {"$set": match_data},
            upsert=True,
        )
        return False

    # Get the summoner's leagues
    leagues = await get_leagues_from_api(client, summoner)

    # Update the summoner's leagues in the db
    await update_summoner_leagues(summoner, leagues)

    # Transform the leagues data for easier access
    leagues = await transform_leagues(leagues)

    # Enhance the match with the league info
    for participant in match_data["info"]["participants"]:
        if participant["puuid"] == summoner["puuid"]:
            queue_type = QUEUE_ID_TO_QUEUE_TYPE[match_data["info"]["queueId"]]
            league_info = leagues.get(queue_type, {})
            
            participant["league"] = {
                "leaguePoints": league_info.get("leaguePoints", None),
                "tier": league_info.get("tier", None),
                "rank": league_info.get("rank", None)
            }
            break

    # Save or update the match in the db
    await matches_col.update_one(
        {"metadata.matchId": match_data["metadata"]["matchId"]},
        {"$set": match_data},
        upsert=True,
    )


async def main():
    async with RiotAPIClient(
        default_headers={'X-Riot-Token': RIOT__API_KEY},
        middlewares=[
            json_response_middleware(orjson.loads),
            http_error_middleware(3),
            rate_limiter_middleware(
                RiotAPIRateLimiter(
                    proxy=f'http://{RIOT__RATE_LIMITER_HOST}:{RIOT__RATE_LIMITER_PORT}'
                )
            ),
        ],
    ) as client:
        while True:
            summoners = await get_summoners_from_db()
            for db_summoner in summoners:
                api_summoner = await get_summoner_from_api(client, db_summoner)
                logger.info(f"Checking summoner {api_summoner['gameName']}#{api_summoner['tagLine']}")
                if await update_summoner_profile(api_summoner):
                    logger.info(f"Updated summoner {api_summoner['gameName']}#{api_summoner['tagLine']}")
                if await update_summoner_matches(client, api_summoner):
                    logger.info(f"Updated matches for summoner {api_summoner['gameName']}#{api_summoner['tagLine']}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
