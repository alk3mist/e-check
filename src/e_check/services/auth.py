from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pydantic import BaseModel

from e_check.config import settings

ALGORITHM = "HS256"


class InvalidTokenError(Exception): ...


class TokenData(BaseModel):
    username: str


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    # Typedefs in pyjwt should be fixed in the next release, see
    # https://github.com/jpadilla/pyjwt/issues/660
    encoded_jwt = jwt.encode(  # type: ignore
        payload=to_encode, key=settings.SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt


def validate_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
        username = payload.get("sub")
        if username is None:
            raise InvalidTokenError
        token_data = TokenData(username=username)
    except jwt.exceptions.InvalidTokenError:
        raise InvalidTokenError
    else:
        return token_data
