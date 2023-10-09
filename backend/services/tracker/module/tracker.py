import os
import logging
import asyncio
from motor import motor_asyncio
from dotenv import load_dotenv

from typing import List

from pyot.core.queue import Queue
from pyot.models import lol
from pyot.utils.lol.routing import  platform_to_region


# Logger config
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), '..', 'logs', 'tracker.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
RIOT_API_KEY = os.getenv('RIOT_API_KEY')

# Connect to db
client = motor_asyncio.AsyncIOMotorClient('localhost', 27017)
db = client['realm-warp']
summoners_c = db['summoners']
matches_c = db['matches']
timelines_c = db['timelines']


# Static data
QUEUE_ID_TO_QUEUE_TYPE = {
    440: 'RANKED_FLEX_SR',
    420: 'RANKED_SOLO_5x5',
    # TODO: Add more queue types
}


# Get all summoners from db
async def get_summoners():
    summoners = await summoners_c.find().to_list(None)
    return summoners


# Check for new match
async def check_for_new_match(summoner):
    last_match_id = summoner['lastMatchId']
    summone_platform = summoner['platform']
    summoner_puuid = summoner['puuid']
    async with Queue() as queue:
        summoner = await lol.Summoner(puuid=summoner_puuid, platform=summone_platform).get()
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



# Get match data
async def get_match_data(match_id, summoner_platform) -> lol.Match:
    match = await lol.Match(id=match_id, region=platform_to_region(summoner_platform)).get()
    return match


# Get timeline data
async def get_timeline_data(match_id, summoner_platform) -> lol.Timeline:
    timeline = await lol.Timeline(id=match_id, region=platform_to_region(summoner_platform)).get()
    return timeline


# Get summoner leagues
async def get_summoner_leagues(summoner_id, summoner_platform) -> lol.SummonerLeague:
    leagues = await lol.SummonerLeague(summoner_id=summoner_id, platform=summoner_platform).get()
    return leagues


# Enrich match data with league data
async def enrich_match_data(match_data: lol.Match):
    queue_id = match_data.info.queue_id
    for participant in match_data.info.participants:
        summoner_id = participant.summoner_id
        summoner_puuid = participant.puuid

        # if the summoner is in the db
        summoner = await summoners_c.find_one({'puuid': summoner_puuid})
        if summoner:
            if queue_id not in QUEUE_ID_TO_QUEUE_TYPE:
                summoner['lastMatchId'] = match_data.metadata.match_id
                await summoners_c.update_one({'puuid': summoner_puuid}, {'$set': summoner})
                return match_data
            # get summoner leagues
            league_entries = await get_summoner_leagues(summoner_id, summoner['platform'])
            for league in league_entries:
                if league.queue == QUEUE_ID_TO_QUEUE_TYPE[queue_id]:
                    participant.league = {
                        'tier': league.tier,
                        'rank': league.rank,
                        'league_points': league.league_points
                    }

                    # update summoner leagues
                    league = league.dict()
                    league.pop('summonerId')
                    league.pop('summonerName')
                    summoner['league_entries'][str(queue_id)] = league
                    summoner['lastMatchId'] = match_data.metadata.match_id
                    await summoners_c.update_one({'puuid': summoner_puuid}, {'$set': summoner})
                    break
    return match_data


# Save match data to db
async def save_match_data(match_data):
    await matches_c.insert_one(match_data.to_dict())


# Save timeline data to db
async def save_timeline_data(timeline_data):
    await timelines_c.insert_one(timeline_data)


# old main function
async def main_old():
    try:
        summoners = await get_summoners()
        for summoner in summoners:
            match_id = await check_for_new_match(summoner)
            if match_id:
                logging.info(f'Processing match {match_id} for summoner {summoner["name"]} ({summoner["id"]})')
                match_data = await get_match_data(match_id, summoner['platform'])
                match_data = await enrich_match_data(match_data)
                await save_match_data(match_data)
                timeline_data = await get_timeline_data(match_id, summoner['platform'])
                await save_timeline_data(timeline_data)
                logging.info(f'Match {match_id} for summoner {summoner["name"]} ({summoner["id"]}) processed successfully')
    except Exception as e:
        logging.error(f'Error in main function: {e}')


# Main function
async def tracker():
    while True:
        summoners = await get_summoners()
        for summoner in summoners:
            match_id = await check_for_new_match(summoner)
            if match_id:
                logging.info(f'Processing match {match_id} for summoner {summoner["name"]} ({summoner["id"]})')
                match_data = await get_match_data(match_id, summoner['platform'])
                match_data = await enrich_match_data(match_data)
                await save_match_data(match_data)
                timeline_data = await get_timeline_data(match_id, summoner['platform'])
                await save_timeline_data(timeline_data)
                logging.info(f'Match {match_id} for summoner {summoner["name"]} ({summoner["id"]}) processed successfully')
