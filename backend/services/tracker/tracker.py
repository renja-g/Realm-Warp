import os
import logging
import requests
import asyncio
from motor import motor_asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from utils import routing


# Logger config
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'logs', 'tracker.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
RIOT_API_KEY = os.getenv('RIOT_API_KEY')

# Connect to db
client = motor_asyncio.AsyncIOMotorClient('mongodb', 27017)
db = client['realm-warp']
summoners_c = db['summoners']
matches_c = db['matches']
timelines_c = db['timelines']

# Scheduler config
scheduler = AsyncIOScheduler()


# Utility function to make API requests
async def make_api_request(url):
    response = await asyncio.to_thread(requests.get, url)
    response.raise_for_status()
    return response.json()


# Get all summoners from db
async def get_summoners():
    summoners = await summoners_c.find().to_list(None)
    return summoners


# Check for new match
async def check_for_new_match(summoner):
    summoner_puuid = summoner['puuid']
    region = routing.platform_to_region(summoner['platform'])
    last_match_id = summoner['lastMatchId']

    url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_puuid}/ids?start=0&count=1&api_key={RIOT_API_KEY}'
    try:
        match_ids = await make_api_request(url)
        match_id = match_ids[0]
        if match_id != last_match_id:
            logging.info(f'New match found for summoner {summoner["name"]} ({summoner["id"]})')
            return match_id
        else:
            logging.info(f'No new match found for summoner {summoner["name"]} ({summoner["id"]})')
            return None
    except Exception as e:
        logging.error(f'Error getting match history for summoner {summoner["name"]} ({summoner["id"]}): {str(e)}')
        return None


# Get match data
async def get_match_data(match_id, platform):
    region = routing.platform_to_region(platform)
    url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}'
    return await make_api_request(url)


# Get timeline data
async def get_timeline_data(match_id, platform):
    region = routing.platform_to_region(platform)
    url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline?api_key={RIOT_API_KEY}'
    return await make_api_request(url)


# Get summoner leagues
async def get_summoner_leagues(summoner_id, platform):
    url = f'https://{platform}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={RIOT_API_KEY}'
    return await make_api_request(url)


# Enrich match data with league data
async def enrich_match_data(match_data):
    queue_id = match_data['info']['queueId']
    for participant in match_data['info']['participants']:
        summoner_id = participant['summonerId']
        summoner_puuid = participant['puuid']

        # if the summoner is in the db
        summoner = await summoners_c.find_one({'puuid': summoner_puuid})
        if summoner:
            if queue_id not in routing.queueId2queueType:
                summoner['lastMatchId'] = match_data['metadata']['matchId']
                await summoners_c.update_one({'puuid': summoner_puuid}, {'$set': summoner})
                return match_data
            # get summoner leagues
            league_entries = await get_summoner_leagues(summoner_id, summoner['platform'])
            for league in league_entries:
                if league['queueType'] == routing.queueId_to_queueType(queue_id):
                    participant['league'] = {
                        'tier': league['tier'],
                        'rank': league['rank'],
                        'leaguePoints': league['leaguePoints']
                    }

                    # update summoner leagues
                    league.pop('summonerId')
                    league.pop('summonerName')
                    summoner['league_entries'][str(queue_id)] = league
                    summoner['lastMatchId'] = match_data['metadata']['matchId']
                    await summoners_c.update_one({'puuid': summoner_puuid}, {'$set': summoner})
                    break
    return match_data


# Save match data to db
async def save_match_data(match_data):
    await matches_c.insert_one(match_data)


# Save timeline data to db
async def save_timeline_data(timeline_data):
    await timelines_c.insert_one(timeline_data)


async def main():
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



if __name__ == '__main__':
    scheduler.add_job(main, 'cron', minute='*/1')
    scheduler.start()
    asyncio.get_event_loop().run_forever()
