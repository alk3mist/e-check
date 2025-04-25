from typing import Annotated

from pydantic import BaseModel, Field, SecretStr, StringConstraints


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    full_name: str


class RegisterUser(BaseModel):
    username: Annotated[
        str,
        StringConstraints(
            min_length=2, max_length=255, strict=True, strip_whitespace=True
        ),
    ]

    full_name: Annotated[
        str,
        StringConstraints(
            min_length=1, max_length=255, strict=True, strip_whitespace=True
        ),
    ]
    password: SecretStr = Field(
        min_length=8,
        max_length=255,
        strict=True,
    )
