from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document, Indexed, Link, before_event, Replace, Insert
from enum import Enum
from pydantic import BaseModel, Field
import pymongo



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


class Ranks(str, Enum):
    I = "I"
    II = "II"
    III = "III"
    IV = "IV"


class LeagueEntry(BaseModel):
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





class Summoner(Document):
    id: str = Field(...)
    puuid: str = Field(...)
    name: str = Field(...)
    profileIconId: int = Field(...)
    summonerLevel: int = Field(...)
    platform: Platform = Field(...)
    lastMatchId: Optional[str] = Field(None)
    leagueEntries: Optional[dict] = Field(None)

    def __repr__(self) -> str:
        return f"<Summoner {self.name} ({self.platform})>"
    
    def __str__(self) -> str:
        return self.name
    
    def __hash__(self) -> int:
        return hash(self.puuid)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Summoner):
            return self.puuid == other.puuid
        return False
    
    @classmethod
    async def by_puuid(self, puuid: str) -> Optional["Summoner"]:
        return await self.find_one(self.puuid == puuid)

    class Settings:
        name = "summoners"
        indexes = [
            [
                ("name", pymongo.ASCENDING),
                ("platform", pymongo.ASCENDING),
                ("puuid", pymongo.TEXT),
            ]
        ]