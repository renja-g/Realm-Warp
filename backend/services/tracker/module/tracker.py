import os
import logging
import asyncio
from motor import motor_asyncio
from dotenv import load_dotenv
from typing import List
from pyot.core.queue import Queue
from pyot.models import lol
from pyot.utils.lol.routing import platform_to_region
from pyot.core.exceptions import NotFound

# Constants
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'tracker.log')
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
SLEEP_INTERVAL = 20

QUEUE_ID_TO_QUEUE_TYPE = {
    440: 'RANKED_FLEX_SR',
    420: 'RANKED_SOLO_5x5',
}


# Configuration
load_dotenv(CONFIG_FILE_PATH)
RIOT_API_KEY = os.getenv('RIOT_API_KEY')
if RIOT_API_KEY is None:
    raise ValueError("RIOT_API_KEY is not set in the environment")


# Database
client = motor_asyncio.AsyncIOMotorClient('localhost', 27017)
db = client['realm-warp']
summoners_c = db['summoners']
matches_c = db['matches']
timelines_c = db['timelines']


# Initialize Logger
def initialize_logger():
    logging.basicConfig(
        filename=LOG_FILE_PATH,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


async def get_summoners():
    summoners = await summoners_c.find().to_list(None)
    return summoners


async def check_for_new_match(summoner):
    last_match_id = summoner['lastMatchId']
    summoner_platform = summoner['platform']
    summoner_puuid = summoner['puuid']
    
    async with Queue() as queue:
        summoner = await lol.Summoner(puuid=summoner_puuid, platform=summoner_platform).get()
        history = await summoner.match_history.get()
        for match in history.matches[:1]:
            await queue.put(match.get())
        first_match: List[lol.Match] = await queue.join()
    
    match_id = first_match[0].id
    if match_id != last_match_id:
        logging.info(f'New match found for summoner {summoner["name"]} ({summoner["id"]})')
        return match_id
    else:
        logging.info(f'No new match found for summoner {summoner["name"]} ({summoner["id"]})')
        return None


async def get_match_data_from_riot(match_id, summoner_platform) -> lol.Match:
    match = await lol.Match(id=match_id, region=platform_to_region(summoner_platform)).get()
    logging.info(f'Retrieved match data from Riot API for match ID: {match_id}')
    return match


async def get_match_data_from_db(match_id) -> lol.Match:
    match = await matches_c.find_one({'metadata.matchId': match_id})
    logging.info(f'Retrieved match data from the database for match ID: {match_id}')
    return match


async def get_timeline_data(match_id, summoner_platform) -> lol.Timeline:
    timeline = await lol.Timeline(id=match_id, region=platform_to_region(summoner_platform)).get()
    logging.info(f'Retrieved timeline data from Riot API for match ID: {match_id}')
    return timeline


async def get_summoner_leagues(summoner_id, summoner_platform) -> lol.SummonerLeague:
    leagues = await lol.SummonerLeague(summoner_id=summoner_id, platform=summoner_platform).get()
    logging.info(f'Retrieved summoner leagues data from Riot API for summoner ID: {summoner_id}')
    return leagues


async def enrich_match_data(match_data: lol.Match | dict, db_summoner):
    if type(match_data) != dict:
        enrich_match_data_dict = match_data.dict()
    else:
        enrich_match_data_dict = match_data
    queue_id = enrich_match_data_dict['info']['queueId']

    summoner_leagues = await get_summoner_leagues(db_summoner['summonerId'], db_summoner['platform'])
    for league in summoner_leagues:
        if league.queue == QUEUE_ID_TO_QUEUE_TYPE.get(queue_id):
            summoner_league = league

    for participant in enrich_match_data_dict['info']['participants']:
        if participant['summonerId'] == db_summoner['summonerId']:
            participant['league'] = {
                'tier': summoner_league.tier,
                'rank': summoner_league.rank,
                'league_points': summoner_league.league_points,
            }

            db_summoner['lastMatchId'] = enrich_match_data_dict['metadata']['matchId']
            
            summoner_league = summoner_league.dict()
            summoner_league.pop('summonerId')
            summoner_league.pop('summonerName')
            db_summoner['leagueEntries'][str(queue_id)] = summoner_league
            await summoners_c.update_one({'puuid': db_summoner['puuid']}, {'$set': db_summoner})
            break

    logging.info(f'Enriched match data with summoner league information for match ID: {enrich_match_data_dict["metadata"]["matchId"]}')
    return enrich_match_data_dict


async def save_match_data(match_data):
    if type(match_data) != dict:
        match_data = match_data.dict()
    await matches_c.insert_one(match_data)
    logging.info(f'Saved match data to the database for match ID: {match_data["metadata"]["matchId"]}')

async def update_match_data(match_data):
    if type(match_data) != dict:
        match_data = match_data.dict()
    match_id = match_data['metadata']['matchId']
    await matches_c.update_one({'metadata.matchId': match_id}, {'$set': match_data})
    logging.info(f'Updated match data in the database for match ID: {match_id}')


async def save_timeline_data(timeline_data):
    if type(timeline_data) != dict:
        timeline_data = timeline_data.dict()
    await timelines_c.insert_one(timeline_data)
    logging.info(f'Saved timeline data to the database for match ID: {timeline_data["metadata"]["matchId"]}')


async def update_timeline_data(timeline_data):
    if type(timeline_data) != dict:
        timeline_data = timeline_data.dict()
    match_id = timeline_data['metadata']['matchId']
    await timelines_c.update_one({'metadata.matchId': match_id}, {'$set': timeline_data})
    logging.info(f'Updated timeline data in the database for match ID: {match_id}')

async def tracker():
    initialize_logger()
    while True:
        summoners = await get_summoners()
        for summoner in summoners:
            try:
                match_id = await check_for_new_match(summoner)
                if match_id:
                    update_match = False
                    if match_id in await matches_c.distinct('metadata.matchId'):
                        match_data = await get_match_data_from_db(match_id)
                        update_match = True
                    else:
                        match_data = await get_match_data_from_riot(match_id, summoner['platform'])
                    
                    if match_data['info']['queueId'] in QUEUE_ID_TO_QUEUE_TYPE:
                        match_data = await enrich_match_data(match_data, summoner)

                    if update_match:
                        await update_match_data(match_data)
                    else:
                        await save_match_data(match_data)


                    if match_id not in await timelines_c.distinct('metadata.matchId'):
                        timeline_data = await get_timeline_data(match_id, summoner['platform'])
                        await save_timeline_data(timeline_data)
            except NotFound as e:
                logging.error(f'Summoner not found: {e}')
            except Exception as e:
                logging.error(f'An unexpected error occurred: {e} in line {e.__traceback__.tb_lineno}')
        await asyncio.sleep(SLEEP_INTERVAL)
