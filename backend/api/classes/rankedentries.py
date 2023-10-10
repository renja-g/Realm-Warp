from pydantic import BaseModel
from typing import Optional


class RankedEntry(BaseModel):
    leagueId: str
    tier: str
    rank: str
    lp: int
    wins: int
    losses: int
    veteran: bool
    inactive: bool
    freshBlood: bool
    hotStreak: bool


class RankedEntries(BaseModel):
    solo: Optional[RankedEntry]
    flex: Optional[RankedEntry]
