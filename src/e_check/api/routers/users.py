from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from e_check.api.dependencies import get_current_user
from e_check.api.schema import RegisterUser, User
from e_check.services import auth, users

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", summary="Get profile of the authenticated user")
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return User.model_validate(current_user, from_attributes=True)


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, summary="Register a new user"
)
async def register_user(
    create_user: RegisterUser,
) -> User:
    hashed_password = auth.get_password_hash(create_user.password.get_secret_value())
    try:
        user = users.create_user(
            username=create_user.username,
            full_name=create_user.full_name,
            password=hashed_password,
        )
    except users.UsernameIsAlreadyTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username is already taken.")
    else:
        return User.model_validate(user, from_attributes=True)
