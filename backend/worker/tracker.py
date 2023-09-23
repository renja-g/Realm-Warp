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


RIOT_API_KEY = "RGAPI-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

client = motor_asyncio.AsyncIOMotorClient('localhost', 27017)
db = client["realm-warp"]
summoners = db["summoners"]
matches = db["matches"]

scheduler = AsyncIOScheduler()


# Get all summoners from db
async def get_summoners():
    summoners = []
    async for summoner in summoners.find():
        summoners.append(summoner)
    return summoners


# Check for new match
async def check_new_match(summoner):
    summoner_id = summoner["id"]
    platform = summoner["platform"]
    last_match_id = summoner["lastMatchId"]
    url = f"https://{platform}.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_id}/ids?start=0&count=1&api_key={RIOT_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        match_id = response.json()[0]
        if match_id != last_match_id:
            return match_id
    return None

