import os
import logging
from motor import motor_asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
import requests
import asyncio


# Set up logging
logging.basicConfig(filename=f'{os.path.dirname(__file__)}/logs/tracker.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RIOT_API_KEY = 'RGAPI-ae90db68-b6b2-4f00-9817-33414cc2869c'

client = motor_asyncio.AsyncIOMotorClient('localhost', 27017)
db = client['realm-warp']
summoners_c = db['summoners']
matches_c = db['matches']
timelines_c = db['timelines']

scheduler = AsyncIOScheduler()


platform2regions = {
    'br1': 'americas',
    'eun1': 'europe',
    'euw1': 'europe',
    'jp1': 'asia',
    'kr': 'asia',
    'la1': 'americas',
    'la2': 'americas',
    'na1': 'americas',
    'oc1': 'sea',
    'tr1': 'europe',
    'ru': 'europe',
    'ph2': 'sea',
    'sg2': 'sea',
    'th2': 'sea',
    'tw2': 'sea',
    'vn2': 'sea',
}

queueType2queueId = {
    'RANKED_FLEX_SR': 440,
    'RANKED_SOLO_5x5': 420,
}

queueId2queueType = {
    440: 'RANKED_FLEX_SR',
    420: 'RANKED_SOLO_5x5',
}

# Get all summoners from db
async def get_summoners():
    summoners = []
    async for summoner in summoners_c.find():
        summoners.append(summoner)
    return summoners


# Check for new match
async def check_for_new_match(summoner):
    summoner_puuid = summoner['puuid']
    region = platform2regions[summoner['platform']]
    last_match_id = summoner['lastMatchId']
    
    # Get the latest match ID
    url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_puuid}/ids?start=0&count=1&api_key={RIOT_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        match_id = response.json()[0]
        
        # If the match ID is different, return it
        if match_id != last_match_id:
            logging.info(f'New match found for summoner {summoner["name"]} ({summoner["id"]})')
            return match_id
        else:
            logging.info(f'No new match found for summoner {summoner["name"]} ({summoner["id"]})')
    else:
        logging.error(f'Error getting match history for summoner {summoner["name"]} ({summoner["id"]}): {response.json()}')

    # Otherwise, return None
    return None


# Get match data
async def get_match_data(match_id, platform):
    region = platform2regions[platform]
    url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


# Get timeline data
async def get_timeline_data(match_id, platform):
    region = platform2regions[platform]
    url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline?api_key={RIOT_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


# Get summoner leagues
async def get_summoner_leagues(summoner_id, platform):
    url = f'https://{platform}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={RIOT_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


# Enrich match data with league data
async def enrich_match_data(match_data):
    queue_id = match_data['info']['queueId']
    for participant in match_data['info']['participants']:
        summoner_id = participant['summonerId']
        summoner_puuid = participant['puuid']

        # if the summoner is in the db
        summoner = await summoners_c.find_one({'puuid': summoner_puuid})
        if summoner:
            if queue_id not in queueId2queueType:
                summoner['lastMatchId'] = match_data['metadata']['matchId']
                await summoners_c.update_one({'puuid': summoner_puuid}, {'$set': summoner})
                return match_data
            # get summoner leagues
            league_entries = await get_summoner_leagues(summoner_id, summoner['platform'])
            for league in league_entries:
                if league['queueType'] == queueId2queueType[queue_id]:            
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


asyncio.run(main())
