from typing import Annotated
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api import api_messages
from app.core.database_session import get_database
from app.core.security.jwt import verify_jwt_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/access-token")


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    token_payload = verify_jwt_token(token)
    
    try:
        user_id = ObjectId(token_payload.sub)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=api_messages.JWT_ERROR_INVALID_FORMAT,
        )
    
    user = await db.users.find_one({"_id": user_id})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=api_messages.JWT_ERROR_USER_REMOVED,
        )
    return user
