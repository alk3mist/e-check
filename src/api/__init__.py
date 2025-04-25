from fastapi import APIRouter

from api.routers import auth, users

router = APIRouter()
router.include_router(auth.router)
router.include_router(users.router)
