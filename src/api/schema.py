from pydantic import BaseModel, Field, SecretStr


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    full_name: str | None = None


class CreateUser(BaseModel):
    username: str = Field(
        min_length=2, max_length=255, strict=True, strip_whitespaces=True
    )
    full_name: str = Field(
        min_length=1, max_length=255, strict=True, strip_whitespaces=True
    )
    password: SecretStr = Field(
        min_length=8,
        max_length=255,
        strict=True,
    )
