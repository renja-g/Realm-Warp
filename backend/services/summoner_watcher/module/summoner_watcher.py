import os
import asyncio
from motor import motor_asyncio
from dotenv import load_dotenv
from typing import List
from pyot.core.queue import Queue
from pyot.models import lol
from pyot.utils.lol.routing import platform_to_region
from pyot.core.exceptions import NotFound


# Constants
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
SLEEP_INTERVAL = 60 * 10  # Time to sleep between checking for updates (in seconds)


# Configuration
load_dotenv(CONFIG_FILE_PATH)

RIOT_API_KEY = os.getenv('RIOT_API_KEY')
if RIOT_API_KEY is None:
    raise ValueError("RIOT_API_KEY is not set in the environment")


# Database
client = motor_asyncio.AsyncIOMotorClient('localhost', 27017)
db = client['realm-warp']
summoners_c = db['summoners']


# Get all summoners from db
async def get_summoners():
    summoners = await summoners_c.find().to_list(None)
    return summoners


# Get summoner
async def get_summoner(summoner_puuid: str, platform: str) -> lol.Summoner:
    summoner = await lol.Summoner(puuid=summoner_puuid, platform=platform).get()
    return summoner


# Update summoner
async def update_summoner(db_summoner: dict, summoner: lol.Summoner) -> None:
    # load lazy fields
    summoner_id = summoner.id
    summoner_name = summoner.name
    summoner_profile_icon_id = summoner.profile_icon_id
    summoner_level = summoner.level

    if db_summoner['id'] != summoner.id:
        db_summoner['id'] = summoner.id
    if db_summoner['name'] != summoner.name:
        db_summoner['name'] = summoner.name
    if db_summoner['profileIconId'] != summoner.profile_icon_id:
        db_summoner['profileIconId'] = summoner.profile_icon_id
    if db_summoner['summonerLevel'] != summoner.level:
        db_summoner['summonerLevel'] = summoner.level
    
    # Update summoner in db
    await summoners_c.update_one({'puuid': db_summoner['puuid']}, {'$set': db_summoner})


# Main function
async def watcher():
    while True:
        # Get all summoners from db
        summoners = await get_summoners()
        
        # Get summoners from riot api
        for summoner in summoners:
            try:
                summoner_obj = await get_summoner(summoner['puuid'], summoner['platform'])
            except NotFound:
                continue
            
            # Update summoner in db
            await update_summoner(summoner, summoner_obj)

        # Sleep
        await asyncio.sleep(SLEEP_INTERVAL)
