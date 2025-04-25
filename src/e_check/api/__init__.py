from fastapi import APIRouter

from e_check.api.routers import auth, users

router = APIRouter()
router.include_router(auth.router)
router.include_router(users.router)
