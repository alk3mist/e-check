from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from e_check.api.dependencies import get_user_service
from e_check.dto import Token
from e_check.services import auth
from e_check.services.users import IUserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: IUserService = Depends(get_user_service),
) -> Token:
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")
