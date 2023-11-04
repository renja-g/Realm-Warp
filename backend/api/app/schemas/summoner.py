from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field

class Platform(str, Enum):
    br1 = 'br1'
    eun1 = 'eun1'
    euw1 = 'euw1'
    jp1 = 'jp1'
    kr = 'kr'
    la1 = 'la1'
    la2 = 'la2'
    na1 = 'na1'
    oc1 = 'oc1'
    tr1 = 'tr1'
    ru = 'ru'
    ph2 = 'ph2'
    sg2 = 'sg2'
    th2 = 'th2'
    tw2 = 'tw2'
    vn2 = 'vn2'


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
    leaguePoints: int
    wins: int
    losses: int
    veteran: bool
    inactive: bool
    freshBlood: bool
    hotStreak: bool


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


# Shared properties
class SummonerBase(BaseModel):
    pass


# Properties to receive on summoner creation
class SummonerCreate(SummonerBase):
    name: str = Field(...)
    platform: Platform = Field(...)


# Properties to receive on summoner update
class SummonerUpdate(SummonerBase):
    puuid: str = Field(...)
    platform: Platform = Field(...)


# Properties shared by models stored in DB
class SummonerInDBBase(SummonerBase):
    summonerId: str = Field(...)
    puuid: str = Field(...)
    name: str = Field(...)
    profileIconId: int = Field(...)
    summonerLevel: int = Field(...)
    platform: Platform = Field(...)
    lastMatchId: Optional[str] = Field(None)
    leagueEntries: Optional[RankedEntries] = Field(None)


# Properties to return to client
class Summoner(SummonerInDBBase):
    pass


# Properties properties stored in DB
class SummonerInDB(SummonerInDBBase):
    pass