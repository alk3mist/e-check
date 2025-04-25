from fastapi import APIRouter

from api.routers import users

router = APIRouter()
router.include_router(users.router)
