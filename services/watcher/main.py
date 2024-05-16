import asyncio
import logging
import os

import orjson
from beanie import init_beanie
from beanie.odm.operators.find.array import ElemMatch
from db_models.models import LeagueEntry, Match, Summoner, Timeline, __all_models__
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pulsefire.clients import RiotAPIClient
from pulsefire.middlewares import (
    http_error_middleware,
    json_response_middleware,
    rate_limiter_middleware,
)
from pulsefire.ratelimiters import RiotAPIRateLimiter

load_dotenv()

RIOT_API_KEY = os.getenv('RIOT_API_KEY')

RATELIMITER_HOST = os.getenv('RATELIMITER_HOST', 'localhost')
RATELIMITER_PORT = os.getenv('RATELIMITER_PORT', '12227')

RATELIMITER_URI = f'http://{RATELIMITER_HOST}:{RATELIMITER_PORT}'

MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_USER = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'root')
MONGO_PASSWORD = os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'example')
MONGO_URI = f'mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:27017/'
MONGO_DB = os.getenv('MONGO_DB', 'watcher_db')

PLATFORM_TO_REGION = {
    'br1': 'americas',
    'eun1': 'europe',
    'euw1': 'europe',
    'jp1': 'asia',
    'kr': 'asia',
    'la1': 'americas',
    'la2': 'americas',
    'na1': 'americas',
    'oc1': 'sea',
    'tr1': 'europe',
    'ru': 'europe',
    'ph2': 'sea',
    'sg2': 'sea',
    'th2': 'sea',
    'tw2': 'sea',
    'vn2': 'sea',
}

QUEUE_TYPE_TO_QUEUE_ID = {
    'RANKED_SOLO_5x5': [420],
    'RANKED_FLEX_SR': [440],
    'CHERRY': [1700, 1710],
}


class CustomLogger(logging.Logger):
    def info(self, msg, *args, **kwargs):
        if 'tags' in kwargs:
            tags = kwargs.pop('tags')
            msg += f' - {tags}'
        super().info(msg, *args, **kwargs)


def setup_logging(
    log_file='watcher.log', log_level=logging.DEBUG, stream_handler=True, file_handler=False
):
    # Create a logger
    logger = CustomLogger(__name__)
    logger.setLevel(log_level)

    # Create a formatter and set the format for the logs
    formatter = logging.Formatter(
        '{asctime} - {name} - {levelname} - {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{',
    )

    # Create a file handler and set its level to DEBUG
    if file_handler:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Create a stream handler and set its level to DEBUG
    if stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


LOGGER = setup_logging()
LOGGER.info('Watcher service started')


async def init_mongo():
    client = AsyncIOMotorClient(MONGO_URI)
    try:
        await client.admin.command('ping')
        print('Pinged your deployment. You successfully connected to MongoDB!')
    except Exception as e:
        print(e)

    await init_beanie(database=client[MONGO_DB], document_models=__all_models__)


async def get_riot_league_entries(
    client: RiotAPIClient, summoner: Summoner
) -> list[LeagueEntry] | None:
    league_entries = await client.get_lol_league_v4_entries_by_summoner(
        region=summoner.platform.value, summoner_id=summoner.summonerId
    )
    if league_entries:
        return [
            LeagueEntry(**league_entry, ref_summoner=summoner.id) for league_entry in league_entries
        ]
    return None


async def get_riot_summoner_info(client: RiotAPIClient, summoner: Summoner) -> Summoner:
    riot_account = await client.get_account_v1_by_riot_id(
        region=PLATFORM_TO_REGION[summoner.platform.value],
        game_name=summoner.gameName,
        tag_line=summoner.tagLine,
    )
    riot_summoner = await client.get_lol_summoner_v4_by_puuid(
        region=summoner.platform.value, puuid=summoner.puuid
    )
    return Summoner(
        **riot_summoner,
        gameName=riot_account['gameName'],
        tagLine=riot_account['tagLine'],
        platform=summoner.platform,
    )


async def get_riot_match(client: RiotAPIClient, match_id: str, summoner: Summoner) -> Match:
    riot_match = await client.get_lol_match_v5_match(
        region=PLATFORM_TO_REGION[summoner.platform.value], id=match_id
    )
    return Match(**riot_match, ref_summoners=[summoner.id])


async def update_league_entries(
    riot_league_entries: list[LeagueEntry] | None, db_league_entries: list[LeagueEntry]
) -> list[LeagueEntry] | None:
    if not riot_league_entries:
        return
    for riot_league_entry in riot_league_entries:
        for db_league_entry in db_league_entries:
            if riot_league_entry.queueType == db_league_entry.queueType:
                # check if the db entry is outdated
                riot_league_entry_dict = riot_league_entry.model_dump(exclude={'id', 'summoner'})
                db_league_entry_dict = db_league_entry.model_dump(exclude={'id', 'summoner'})
                if riot_league_entry_dict == db_league_entry_dict:
                    LOGGER.info('League entry already up to date')
                    break
                else:
                    # if the db entry is outdated, update it
                    for key, value in riot_league_entry_dict.items():
                        setattr(db_league_entry, key, value)
                    await db_league_entry.save()
                    LOGGER.info('Updated league entry', tags=['UPDATE'])
                    break
        else:
            # if the db entry is not found, insert the riot entry
            await riot_league_entry.insert()
            db_league_entries.append(riot_league_entry)
            LOGGER.info('Inserted new league entry', tags=['INSERT'])
    return db_league_entries


async def update_summoner_info(riot_summoner: Summoner, db_summoner: Summoner) -> Summoner:
    riot_summoner_dict = riot_summoner.model_dump(exclude={'id'})
    db_summoner_dict = db_summoner.model_dump(exclude={'id'})
    if riot_summoner_dict == db_summoner_dict:
        LOGGER.info('Summoner info already up to date')
    else:
        for key, value in riot_summoner_dict.items():
            setattr(db_summoner, key, value)
        await db_summoner.save()
        LOGGER.info('Updated summoner info', tags=['UPDATE'])
    return db_summoner


async def update_matches(
    client: RiotAPIClient,
    riot_match_id: str,
    db_summoner: Summoner,
    db_league_entries: list[LeagueEntry],
) -> None:
    """
    Checks if the match is already in the database. If found:
        - Appends the current summoner to the list of linked summoners.
        - If it's a ranked match, updates the match information with the summoner's ranked data.

    If the match is not in the database:
        - Retrieves the match data from the Riot API.
        - If it's a ranked match, updates the match information with the summoner's ranked data.
        - Inserts the match into the database.
        - Retrieves and inserts the timeline data for the match.
    """

    # Check if the match is already in the database (not linked to the summoner)
    db_match = await Match.find_one(Match.metadata.matchId == riot_match_id)
    if db_match:
        # append the current summoner to the link list of the match
        db_match.ref_summoners.append(db_summoner.id)

        # check if the match is a ranked match
        if db_match.info.queueId in (420, 440):
            # add ranked information to the match
            for db_league_entry in db_league_entries:
                if db_match.info.queueId in QUEUE_TYPE_TO_QUEUE_ID[db_league_entry.queueType]:
                    for participant in db_match.info.participants:
                        if participant.puuid == db_summoner.puuid:
                            participant.league = {
                                'leaguePoints': db_league_entry.leaguePoints,
                                'rank': db_league_entry.rank,
                                'tier': db_league_entry.tier,
                            }
                            break
                    break
            else:
                LOGGER.info(f'League entry not found for match {riot_match_id} (placement match)')
        await db_match.save()
        LOGGER.info(f'Updated match {riot_match_id}', tags=['UPDATE'])
    else:
        # get the match from the riot api
        riot_match = await get_riot_match(client, riot_match_id, db_summoner)

        # check if the match is a ranked match
        if riot_match.info.queueId in (420, 440):
            # add ranked information to the match
            for db_league_entry in db_league_entries:
                if riot_match.info.queueId in QUEUE_TYPE_TO_QUEUE_ID[db_league_entry.queueType]:
                    for participant in riot_match.info.participants:
                        if participant.puuid == db_summoner.puuid:
                            participant.league = {
                                'leaguePoints': db_league_entry.leaguePoints,
                                'rank': db_league_entry.rank,
                                'tier': db_league_entry.tier,
                            }
                            break
                    break
            else:
                LOGGER.info(f'League entry not found for match {riot_match_id} (placement match)')
        await riot_match.insert()
        LOGGER.info(f'Inserted new match {riot_match_id}', tags=['INSERT'])
        # get the timeline of the match
        riot_timeline = await client.get_lol_match_v5_match_timeline(
            region=PLATFORM_TO_REGION[db_summoner.platform.value], id=riot_match_id
        )
        timeline = Timeline(**riot_timeline, ref_match=riot_match.id)
        await timeline.insert()
        LOGGER.info(f'Inserted new timeline for match {riot_match_id}', tags=['INSERT'])


async def main():
    await init_mongo()
    async with RiotAPIClient(
        default_headers={'X-Riot-Token': str(RIOT_API_KEY)},
        middlewares=[
            json_response_middleware(orjson.loads),
            http_error_middleware(3),
            rate_limiter_middleware(
                RiotAPIRateLimiter(
                    proxy=RATELIMITER_URI,
                )
            ),
        ],
    ) as client:
        while True:
            try:
                summoners = await Summoner.find().to_list()
                for db_summoner in summoners:
                    LOGGER.info(f'Updating summoner {db_summoner.gameName}#{db_summoner.tagLine}')

                    riot_summoner, db_league_entries = await asyncio.gather(
                        update_summoner_info(
                            await get_riot_summoner_info(client, db_summoner),
                            db_summoner,
                        ),
                        update_league_entries(
                            await get_riot_league_entries(client, db_summoner),
                            await LeagueEntry.find(
                                LeagueEntry.ref_summoner == db_summoner.id
                            ).to_list(),
                        ),
                    )

                    # check if summoner has played a new match
                    riot_last_match_id = await client.get_lol_match_v5_match_ids_by_puuid(
                        region=PLATFORM_TO_REGION[db_summoner.platform.value],
                        puuid=db_summoner.puuid,
                        queries={'start': 0, 'count': 1},
                    )
                    riot_last_match_id = riot_last_match_id[0]
                    last_db_match = await Match.find_one(
                        ElemMatch(Match.ref_summoners, {'$eq': db_summoner.id}),
                        sort=[('info.gameEndTimestamp', -1)],
                    )

                    if last_db_match and last_db_match.metadata.matchId == riot_last_match_id:
                        LOGGER.info('Matches already up to date')
                        continue
                    else:
                        await update_matches(
                            client, riot_last_match_id, db_summoner, db_league_entries
                        )
            except Exception as e:
                LOGGER.exception(e)
            finally:
                LOGGER.info('Sleeping for 60 seconds')
                LOGGER.info('-' * 50)
                await asyncio.sleep(60)


asyncio.run(main())
