from fastapi import APIRouter

from e_check.api.routers import auth, checks, users

router = APIRouter()
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(checks.router)
