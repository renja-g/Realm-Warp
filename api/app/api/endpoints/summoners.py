from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pulsefire.clients import RiotAPIClient

from app.api import deps
from app.schemas.requests import AddSummonerRequest
from app.schemas.responses import SummonerResponse

router = APIRouter()

PLATFORM_TO_REGION = {
    "br1": "americas",
    "eun1": "europe",
    "euw1": "europe",
    "jp1": "asia",
    "kr": "asia",
    "la1": "americas",
    "la2": "americas",
    "na1": "americas",
    "oc1": "sea",
    "tr1": "europe",
    "ru": "europe",
    "ph2": "sea",
    "sg2": "sea",
    "th2": "sea",
    "tw2": "sea",
    "vn2": "sea",
}


@router.post(
    "",
    response_model=SummonerResponse,
    status_code=status.HTTP_201_CREATED,
    description="Add a new summoner to be tracked",
)
async def add_summoner(
    request: AddSummonerRequest,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    riot_client: RiotAPIClient = Depends(deps.get_riot_client),
    current_user: dict = Depends(deps.get_current_user),
) -> SummonerResponse:
    # Check if summoner already exists
    existing_summoner = await db.summoners.find_one(
        {
            "gameName": request.game_name,
            "tagLine": request.tag_line,
            "platform": request.platform.lower(),
        },
        collation={"locale": "en", "strength": 2},
    )

    if existing_summoner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Summoner already exists",
        )

    try:
        # Get account info
        account = await riot_client.get_account_v1_by_riot_id(
            region=PLATFORM_TO_REGION[request.platform.lower()],
            game_name=request.game_name,
            tag_line=request.tag_line,
        )

        # Get summoner info
        summoner = await riot_client.get_lol_summoner_v4_by_puuid(
            region=request.platform.lower(), puuid=account["puuid"]
        )

        # Merge account and summoner info
        new_summoner = {
            "gameName": account["gameName"],
            "tagLine": account["tagLine"],
            "platform": request.platform.lower(),
            **summoner,
            "initial_rank_fetched": False,
        }
        new_summoner["summonerId"] = new_summoner.pop("id")

        await db.summoners.insert_one(new_summoner)

        return SummonerResponse(**new_summoner)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=list[SummonerResponse],
    description="Get a list of all tracked summoners",
)
async def get_all_summoners(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
) -> list[SummonerResponse]:
    summoners = await db.summoners.find().to_list(length=None)
    return [SummonerResponse(**summoner) for summoner in summoners]


@router.delete(
    "/{summoner_puuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Summoner not found"}},
    description="Delete a summoner",
)
async def delete_summoner(
    summoner_puuid: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user),
):
    try:
        # 1. Find summoner by puuid
        summoner_doc = await db.summoners.find_one(
            {"puuid": summoner_puuid}
        )
        if not summoner_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summoner not found",
            )

        summoner_doc_id = summoner_doc["_id"]

        # 1. Delete 'orphan' match documents
        await db.matches.delete_many(
            {
                "ref_summoners": [summoner_doc_id]
            },
        )

        # 2. Update 'shared' match documents: Pull summoner's ID from ref_summoners array
        await db.matches.update_many(
            {
                "ref_summoners": summoner_doc_id
            },
            {"$pull": {"ref_summoners": summoner_doc_id}},
        )

        # 3. Update 'shared' match documents: Unset the league field from the participant's data
        await db.matches.update_many(
            {
                "info.participants.puuid": summoner_puuid
            },
            {"$unset": {"info.participants.$.league": ""}},
        )

        # Delete Summoner Document
        await db.summoners.delete_one({"_id": summoner_doc_id})

        # Delete League Entries
        await db.league_entries.delete_many(
            {"ref_summoner": summoner_doc_id}
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during the transaction: {e}",
        )
