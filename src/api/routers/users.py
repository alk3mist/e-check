from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_current_user
from api.schema import CreateUser, User
from services import auth, users

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.post("/register", response_model=User)
async def register(
    create_user: CreateUser,
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
        return user
