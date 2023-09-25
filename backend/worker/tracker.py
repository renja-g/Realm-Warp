from motor import motor_asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
import requests

# every 5min
# get all summoners from db
# for summoner in summoners:
#   check for new games
#   if new games:
#       if ranked:
#           for participant in participants:
#               if participant in summoners:
#                   update summoner leagues
#                   enrich match data with league data
#       save match data to db


RIOT_API_KEY = "RGAPI-b05b24b2-8e2a-4ad7-a2ab-496ede27c3f1"

client = motor_asyncio.AsyncIOMotorClient('localhost', 27017)
db = client["realm-warp"]
summoners = db["summoners"]
matches = db["matches"]

scheduler = AsyncIOScheduler()


platform2regions = {
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

# Get all summoners from db
async def get_summoners():
    summoners = []
    async for summoner in summoners.find():
        summoners.append(summoner)
    return summoners


# Check for new match
async def check_for_new_match(summoner):
    summoner_id = summoner["id"]
    platform = summoner["platform"]
    last_match_id = summoner["lastMatchId"]
    
    # Get the latest match ID
    url = f"https://{platform}.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_id}/ids?start=0&count=1&api_key={RIOT_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        match_id = response.json()[0]
        
        # If the match ID is different, return it
        if match_id != last_match_id:
            return match_id
        
    # Otherwise, return None
    return None


# Get match data
async def get_match_data(match_id, platform):
    region = platform2regions[platform]
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


# Get summoner leagues
async def get_summoner_leagues(summoner_id, platform):
    url = f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={RIOT_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


# Enrich match data with league data
async def enrich_match_data(match_data):
    for participant in match_data["info"]["participants"]:
        summoner_id = participant["summonerId"]
        # if the summoner is in the db
        summoner = await summoners.find_one({"id": summoner_id})
