import time
from collections.abc import AsyncGenerator

import jwt
from db_models.models import User
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pulsefire.clients import RiotAPIClient

from app.core import config, security
from app.core.pulsfire_session import riot_client

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl='auth/access-token')


async def get_riot_client() -> AsyncGenerator[RiotAPIClient, None]:
    async with riot_client as client:
        yield client


async def get_current_user(token: str = Depends(reusable_oauth2)) -> User:
    try:
        payload = jwt.decode(token, config.settings.SECRET_KEY, algorithms=[security.JWT_ALGORITHM])
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Could not validate credentials.',
        )
    # JWT guarantees payload will be unchanged (and thus valid), no errors here
    token_data = security.JWTTokenPayload(**payload)

    if token_data.refresh:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Could not validate credentials, cannot use refresh token',
        )
    now = int(time.time())
    if now < token_data.issued_at or now > token_data.expires_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Could not validate credentials, token expired or not yet valid',
        )

    user = await User.get(token_data.sub)

    if not user:
        raise HTTPException(status_code=404, detail='User not found.')
    return user
