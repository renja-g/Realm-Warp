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

        if "440" in args["entries"]:
            args["entries"]["flex"] = args["entries"]["440"]
            del args["entries"]["440"]

        if "420" in args["entries"]:
            args["entries"]["solo"] = args["entries"]["420"]
            del args["entries"]["420"]

        for league in args["entries"]:
            args["entries"][league]["lp"] = args["entries"][league]["leaguePoints"]

        super().__init__(**args)
