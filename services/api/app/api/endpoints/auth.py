import time

import jwt
from db_models.models import User
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

from app.core import config, security
from app.schemas.requests import RefreshTokenRequest
from app.schemas.responses import AccessTokenResponse

router = APIRouter()


@router.post('/access-token', response_model=AccessTokenResponse)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    OAuth2 compatible token,
    get an access token for future requests using username and password
    """

    user = await User.find_one(User.username == form_data.username)

    if user is None:
        raise HTTPException(status_code=400, detail='Incorrect username or password')

    if not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail='Incorrect username or password')

    return security.generate_access_token_response(str(user.id))


@router.post('/refresh-token', response_model=AccessTokenResponse)
async def refresh_token(
    input: RefreshTokenRequest,
):
    """OAuth2 compatible token, get an access token for future requests using refresh token"""
    try:
        payload = jwt.decode(
            input.refresh_token,
            config.settings.SECRET_KEY,
            algorithms=[security.JWT_ALGORITHM],
        )
    except (jwt.DecodeError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Could not validate credentials, unknown error',
        )

    # JWT guarantees payload will be unchanged (and thus valid), no errors here
    token_data = security.JWTTokenPayload(**payload)

    if not token_data.refresh:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Could not validate credentials, cannot use access token',
        )
    now = int(time.time())
    if now < token_data.issued_at or now > token_data.expires_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Could not validate credentials, token expired or not yet valid',
        )

    user = await User.find_one(User.id == token_data.sub)

    if user is None:
        raise HTTPException(status_code=404, detail='User not found')

    return security.generate_access_token_response(str(user.id))
