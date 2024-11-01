from enum import Enum

from pydantic import BaseModel, EmailStr


class Platform(str, Enum):
    br1 = "br1"  # Brazil
    eun1 = "eun1"  # Europe Nordic & East
    euw1 = "euw1"  # Europe West
    jp1 = "jp1"  # Japan
    kr = "kr"  # Korea
    la1 = "la1"  # Latin America North
    la2 = "la2"  # Latin America South
    na1 = "na1"  # North America
    oc1 = "oc1"  # Oceania
    tr1 = "tr1"  # Turkey
    ru = "ru"  # Russia
    ph2 = "ph2"  # Philippines
    sg2 = "sg2"  # Singapore
    th2 = "th2"  # Thailand
    tw2 = "tw2"  # Taiwan
    vn2 = "vn2"  # Vietnam


class BaseRequest(BaseModel):
    pass


class RefreshTokenRequest(BaseRequest):
    refresh_token: str


class UserUpdatePasswordRequest(BaseRequest):
    password: str


class UserCreateRequest(BaseRequest):
    email: EmailStr
    password: str


class AddSummonerRequest(BaseModel):
    game_name: str
    tag_line: str
    platform: Platform
