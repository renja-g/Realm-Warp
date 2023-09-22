from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel


class Regions(str, Enum):
    br = "br"
    eune = "eune"
    euw = "euw"
    lan = "lan"
    las = "las"
    na = "na"
    oce = "oce"
    ru = "ru"
    tr = "tr"
    jp = "jp"
    kr = "kr"
    sg = "sg"
    th = "th"
    tw = "tw"
    vn = "vn"
    ph = "ph"


class PostUser(BaseModel):
    puuid: str
    server: Regions


router = APIRouter()


@router.get("")
async def listAll():
    return "all"


@router.get("/{puuid}")
async def getByPuuid():
    return "puuid"


@router.post("/{puuid}")
async def addUser(User: PostUser):
    return "new"


@router.delete("/{puuid}")
async def removeUser():
    return "delete"
