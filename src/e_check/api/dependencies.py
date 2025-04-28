from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from e_check.db.session import get_session_maker
from e_check.dto import User
from e_check.services import auth
from e_check.services.checks import DbCheckService, ICheckService
from e_check.services.users import DbUserService, IUserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def _get_db_session() -> AsyncIterator[AsyncSession]:
    async_session = get_session_maker()
    async with async_session() as session:
        yield session


def get_user_service(session: AsyncSession = Depends(_get_db_session)) -> IUserService:
    user_service = DbUserService(session)
    return user_service


def get_check_service(
    session: AsyncSession = Depends(_get_db_session),
) -> ICheckService:
    return DbCheckService(session)


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

    user = await user_service.get_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception

    return user
