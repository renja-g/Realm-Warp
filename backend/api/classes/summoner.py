from pydantic import BaseModel

from .regions import Regions
from .rankedentries import RankedEntries


class Summoner(BaseModel):
    puuid: str
    name: str
    iconId: int
    level: int
    region: Regions
    entries: RankedEntries

    def __init__(self, **args):
        args["iconId"] = args["profileIconId"]
        args["level"] = args["summonerLevel"]
        args["entries"] = args["league_entries"]
        args["region"] = args["platform"]

        super().__init__(**args)
