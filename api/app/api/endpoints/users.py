from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api import deps
from app.core.security.password import get_password_hash
from app.schemas.requests import UserUpdatePasswordRequest
from app.schemas.responses import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse, description="Get current user")
async def read_current_user(
    current_user: dict = Depends(deps.get_current_user),
) -> dict:
    # Transform MongoDB document to match UserResponse schema
    return {
        "user_id": str(current_user["_id"]),  # Convert ObjectId to string
        "email": current_user["email"]
        # Add any other fields that are in your UserResponse model
    }


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete current user",
)
async def delete_current_user(
    current_user: dict = Depends(deps.get_current_user),
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
) -> None:
    # Delete the user
    await db.users.delete_one({"_id": current_user["_id"]})
    # Also delete associated refresh tokens
    await db.refresh_tokens.delete_many({"user_id": current_user["_id"]})


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Update current user password",
)
async def reset_current_user_password(
    user_update_password: UserUpdatePasswordRequest,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user),
) -> None:
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"hashed_password": get_password_hash(user_update_password.password)}}
    )
    # invalidate all refresh tokens for this user when password is changed
    await db.refresh_tokens.update_many(
        {"user_id": current_user["_id"], "used": False},
        {"$set": {"used": True}}
    )
