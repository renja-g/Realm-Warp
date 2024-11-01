import secrets
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.api import api_messages, deps
from app.core.config import get_settings
from app.core.security.jwt import create_jwt_token
from app.core.security.password import (
    DUMMY_PASSWORD,
    get_password_hash,
    verify_password,
)
from app.schemas.requests import RefreshTokenRequest, UserCreateRequest
from app.schemas.responses import AccessTokenResponse, UserResponse

router = APIRouter()

ACCESS_TOKEN_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Invalid email or password",
        "content": {
            "application/json": {"example": {"detail": api_messages.PASSWORD_INVALID}}
        },
    },
}

REFRESH_TOKEN_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Refresh token expired or is already used",
        "content": {
            "application/json": {
                "examples": {
                    "refresh token expired": {
                        "summary": api_messages.REFRESH_TOKEN_EXPIRED,
                        "value": {"detail": api_messages.REFRESH_TOKEN_EXPIRED},
                    },
                    "refresh token already used": {
                        "summary": api_messages.REFRESH_TOKEN_ALREADY_USED,
                        "value": {"detail": api_messages.REFRESH_TOKEN_ALREADY_USED},
                    },
                }
            }
        },
    },
    404: {
        "description": "Refresh token does not exist",
        "content": {
            "application/json": {
                "example": {"detail": api_messages.REFRESH_TOKEN_NOT_FOUND}
            }
        },
    },
}


@router.post(
    "/access-token",
    response_model=AccessTokenResponse,
    responses=ACCESS_TOKEN_RESPONSES,
    description="OAuth2 compatible token, get an access token for future requests using username and password",
)
async def login_access_token(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> AccessTokenResponse:
    user = await db.users.find_one({"email": form_data.username})

    if user is None:
        # this is naive method to not return early
        verify_password(form_data.password, DUMMY_PASSWORD)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=api_messages.PASSWORD_INVALID,
        )

    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=api_messages.PASSWORD_INVALID,
        )

    jwt_token = create_jwt_token(user_id=str(user["_id"]))

    refresh_token = {
        "user_id": user["_id"],
        "refresh_token": secrets.token_urlsafe(32),
        "exp": int(time.time() + get_settings().security.refresh_token_expire_secs),
        "used": False,
    }
    
    await db.refresh_tokens.insert_one(refresh_token)

    return AccessTokenResponse(
        access_token=jwt_token.access_token,
        expires_at=jwt_token.payload.exp,
        refresh_token=refresh_token["refresh_token"],
        refresh_token_expires_at=refresh_token["exp"],
    )


@router.post(
    "/refresh-token",
    response_model=AccessTokenResponse,
    responses=REFRESH_TOKEN_RESPONSES,
    description="OAuth2 compatible token, get an access token for future requests using refresh token",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
) -> AccessTokenResponse:
    # Use findOneAndUpdate to atomically find and mark the token as used
    token = await db.refresh_tokens.find_one_and_update(
        {
            "refresh_token": data.refresh_token,
            "used": False,
        },
        {"$set": {"used": True}},
        return_document=True
    )

    if token is None:
        # Check if token exists but was already used
        existing_token = await db.refresh_tokens.find_one(
            {"refresh_token": data.refresh_token}
        )
        if existing_token and existing_token.get("used"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=api_messages.REFRESH_TOKEN_ALREADY_USED,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=api_messages.REFRESH_TOKEN_NOT_FOUND,
        )
    
    if time.time() > token["exp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=api_messages.REFRESH_TOKEN_EXPIRED,
        )

    jwt_token = create_jwt_token(user_id=str(token["user_id"]))

    new_refresh_token = {
        "user_id": token["user_id"],
        "refresh_token": secrets.token_urlsafe(32),
        "exp": int(time.time() + get_settings().security.refresh_token_expire_secs),
        "used": False,
    }
    
    await db.refresh_tokens.insert_one(new_refresh_token)

    return AccessTokenResponse(
        access_token=jwt_token.access_token,
        expires_at=jwt_token.payload.exp,
        refresh_token=new_refresh_token["refresh_token"],
        refresh_token_expires_at=new_refresh_token["exp"],
    )


@router.post(
    "/register",
    response_model=UserResponse,
    description="Create new user",
    status_code=status.HTTP_201_CREATED,
)
async def register_new_user(
    new_user: UserCreateRequest,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> UserResponse:
    if current_user["email"] != get_settings().security.root_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=api_messages.ADMIN_ONLY,
        )

    if await db.users.find_one({"email": new_user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=api_messages.EMAIL_ADDRESS_ALREADY_USED,
        )

    user = {
        "email": new_user.email,
        "hashed_password": get_password_hash(new_user.password),
    }

    try:
        result = await db.users.insert_one(user)
        return UserResponse(
            user_id=str(result.inserted_id),
            email=new_user.email
        )
    except DuplicateKeyError:  # In case of race condition
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=api_messages.EMAIL_ADDRESS_ALREADY_USED,
        )
