from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from e_check.api.dependencies import get_current_user, get_user_service
from e_check.api.schema import RegisterUser, User
from e_check.services import users

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, summary="Register a new user"
)
async def register_user(
    register_user: RegisterUser,
    user_service: users.IUserService = Depends(get_user_service),
) -> User:
    try:
        user = user_service.create_user(
            username=register_user.username,
            full_name=register_user.full_name,
            password=register_user.password.get_secret_value(),
        )
    except users.UsernameIsAlreadyTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username is already taken.")
    else:
        return User.model_validate(user, from_attributes=True)


@router.get("/me", summary="Get profile of the authenticated user")
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return User.model_validate(current_user, from_attributes=True)
