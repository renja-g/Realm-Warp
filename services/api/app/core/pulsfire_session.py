import orjson
from pulsefire.clients import RiotAPIClient
from pulsefire.middlewares import (
    http_error_middleware,
    json_response_middleware,
    rate_limiter_middleware,
)
from pulsefire.ratelimiters import RiotAPIRateLimiter

from app.core import config

ratelimiter_url = f'http://{config.settings.RATELIMITER_HOST}:{config.settings.RATELIMITER_PORT}'

riot_client = RiotAPIClient(
    default_headers={'X-Riot-Token': config.settings.RIOT_API_KEY},
    middlewares=[
        json_response_middleware(orjson.loads),
        http_error_middleware(3),
        rate_limiter_middleware(
            RiotAPIRateLimiter(
                proxy=ratelimiter_url,
            )
        ),
    ],
)
