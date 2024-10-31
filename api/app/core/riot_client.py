from contextlib import asynccontextmanager
import orjson
from pulsefire.clients import RiotAPIClient
from pulsefire.middlewares import (
    http_error_middleware,
    json_response_middleware,
    rate_limiter_middleware,
)
from pulsefire.ratelimiters import RiotAPIRateLimiter

from app.core.config import get_settings

@asynccontextmanager
async def get_riot_api_client():
    settings = get_settings()
    
    async with RiotAPIClient(
        default_headers={'X-Riot-Token': settings.riot.api_key.get_secret_value()},
        middlewares=[
            json_response_middleware(orjson.loads),
            http_error_middleware(3),
            rate_limiter_middleware(
                RiotAPIRateLimiter(
                    proxy=f'http://{settings.riot.rate_limiter_host}:{settings.riot.rate_limiter_port}'
                )
            ),
        ],
    ) as client:
        yield client
