from functools import cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from e_check.dto import User
from e_check.services import auth
from e_check.services.checks import ICheckService, InMemoryCheckService
from e_check.services.users import InMemoryUserService, IUserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


@cache
def get_user_service():
    user_service = InMemoryUserService()
    user_service.create_user(
        username="john-boris",
        full_name="ФОП Джонсонюк Борис",
        password="super-secret",
    )
    return user_service


@cache
def get_check_service(
    user_service: IUserService = Depends(get_user_service),
) -> ICheckService:
    return InMemoryCheckService(user_service)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: IUserService = Depends(get_user_service),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_data = auth.validate_token(token)
    except auth.InvalidTokenError:
        raise credentials_exception

    user = user_service.get_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
