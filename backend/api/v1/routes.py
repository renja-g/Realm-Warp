from fastapi import APIRouter

from v1.endpoints import users

router = APIRouter()

router.include_router(users.router, prefix="/users", tags=["Users"])