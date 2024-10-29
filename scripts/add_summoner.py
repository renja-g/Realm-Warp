import asyncio
import sys

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
)
from pulsefire.clients import RiotAPIClient
from pulsefire.schemas import RiotAPISchema


client: AsyncIOMotorClient = AsyncIOMotorClient(
    "mongodb://root:CHANGE_THIS@localhost:27017"
)
db: AsyncIOMotorDatabase = client["realm_warp"]
summoners_col: AsyncIOMotorCollection = db["summoners"]


if len(sys.argv) != 4:
    print("Usage: python add_summoner.py <game_name> <tag_line> <platform>")
    sys.exit(1)

game_name = sys.argv[1]
tag_line = sys.argv[2]
platform = sys.argv[3].lower()

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


async def main():
    async with RiotAPIClient(
        default_headers={"X-Riot-Token": "RGAPI-56d3e52c-f4b0-45f5-bc6b-fa26ec176581"}
    ) as client:
        summoner = await summoners_col.find_one(
            {
                "gameName": game_name,
                "tagLine": tag_line,
                "platform": platform
            },
            collation={"locale": "en", "strength": 2}
        )
        if summoner:
            print(f"{game_name}#{tag_line} already exists in the database.")
            sys.exit(0)

        account = await client.get_account_v1_by_riot_id(region=PLATFORM_TO_REGION[platform], game_name=game_name, tag_line=tag_line)
        summoner = await client.get_lol_summoner_v4_by_puuid(region=platform, puuid=account["puuid"])

        summoner["gameName"] = account["gameName"]
        summoner["tagLine"] = account["tagLine"]
        summoner["platform"] = platform

        await summoners_col.insert_one(summoner)
        print(f"Added {summoner['gameName']}#{summoner["tagLine"]} to the database.")

if __name__ == "__main__":
    asyncio.run(main())