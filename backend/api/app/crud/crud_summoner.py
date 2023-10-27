from app.schemas.summoner import SummonerCreate, Summoner
from app.models.summoner import Summoner
from app.core.config import settings
import requests

class SummonerCRUD:
    @staticmethod
    async def add_summoner(data: SummonerCreate) -> Summoner:
        """
        Adds a new summoner to the database.
        """
        summoner_v4 = f"https://{data.platform.value}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{data.name}?api_key={settings.RIOT_API_KEY}"
        summoner_data = requests.get(summoner_v4)
        summoner_data = summoner_data.json()
        
        league_v4 = f"https://{data.platform.value}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_data['id']}?api_key={settings.RIOT_API_KEY}"
        league_data = requests.get(league_v4)
        league_data = league_data.json()


        formated_league_data = {}
        for league in league_data:
            if league['queueType'] == 'RANKED_SOLO_5x5':
                formated_league_data['420'] = {
                    'leagueId': league['leagueId'],
                    'queueType': league['queueType'],
                    'tier': league['tier'],
                    'rank': league['rank'],
                    'leaguePoints': league['leaguePoints'],
                    'wins': league['wins'],
                    'losses': league['losses'],
                    'veteran': league['veteran'],
                    'inactive': league['inactive'],
                    'freshBlood': league['freshBlood'],
                    'hotStreak': league['hotStreak']
                }
            elif league['queueType'] == 'RANKED_FLEX_SR':
                formated_league_data['440'] = {
                    'leagueId': league['leagueId'],
                    'queueType': league['queueType'],
                    'tier': league['tier'],
                    'rank': league['rank'],
                    'leaguePoints': league['leaguePoints'],
                    'wins': league['wins'],
                    'losses': league['losses'],
                    'veteran': league['veteran'],
                    'inactive': league['inactive'],
                    'freshBlood': league['freshBlood'],
                    'hotStreak': league['hotStreak']
                }

        summoner = Summoner(
            id=summoner_data["id"],
            puuid=summoner_data["puuid"],
            name=summoner_data["name"],
            profileIconId=summoner_data["profileIconId"],
            summonerLevel=summoner_data["summonerLevel"],
            platform=data.platform,
            lastMatchId=None,
            leagueEntries=formated_league_data
        )
        await summoner.insert()
        return summoner
    
    @staticmethod
    async def get_all_summoners() -> list[Summoner]:
        """
        Returns a list of all summoners in the database.
        """
        summoners = await Summoner.find_all().to_list()
        return summoners
    
