from pydantic import BaseModel
from typing import Optional

from enum import Enum


class Tiers(str, Enum):
    IRON = "IRON"
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"
    EMERALD = "EMERALD"
    DIAMOND = "DIAMOND"
    MASTER = "MASTER"
    GRANDMASTER = "GRANDMASTER"
    CHALLENGER = "CHALLENGER"


class Ranks(str, Enum):
    I = "I"
    II = "II"
    III = "III"
    IV = "IV"


class RankedEntry(BaseModel):
    leagueId: str
    tier: Tiers
    rank: Ranks
    lp: int
    wins: int
    losses: int
    veteran: bool
    inactive: bool
    freshBlood: bool
    hotStreak: bool

    def __init__(self, **args):
        args["lp"] = args["leaguePoints"]

        super().__init__(**args)


class RankedEntries(BaseModel):
    solo: Optional[RankedEntry]
    flex: Optional[RankedEntry]

    def __init__(self, **args):
        if "440" in args:
            args["flex"] = args["440"]
            del args["440"]

        if "420" in args:
            args["solo"] = args["420"]
            del args["420"]

        super().__init__(**args)
