from bson import ObjectId
from pydantic import BaseModel, ConfigDict, GetJsonSchemaHandler
from pydantic_core import CoreSchema


class ObjectIdStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> dict[str, any]:
        return {'type': 'string', 'format': 'ObjectId'}


class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AccessTokenResponse(BaseResponse):
    token_type: str
    access_token: str
    expires_at: int
    issued_at: int
    refresh_token: str
    refresh_token_expires_at: int
    refresh_token_issued_at: int


class UserResponse(BaseResponse):
    id: ObjectIdStr
    username: str


class SummonerResponse(BaseResponse):
    id: ObjectIdStr
    puuid: str

    gameName: str
    tagLine: str
    summonerId: str
    name: str
    profileIconId: int
    summonerLevel: int
    platform: str


class LeagueEntryResponse(BaseResponse):
    id: ObjectIdStr

    leagueId: str
    queueType: str
    tier: str
    rank: str
    leaguePoints: int
    wins: int
    losses: int
    veteran: bool
    inactive: bool
    freshBlood: bool
    hotStreak: bool


class SummonerWithLeagueEntriesResponse(BaseResponse):
    summoner: SummonerResponse
    league_entries: list[LeagueEntryResponse]
