from dataclasses import dataclass
from typing import Final, Protocol

from passlib.context import CryptContext
from pydantic import BaseModel


class UserInDB(BaseModel):
    password: str
    username: str
    full_name: str


class UsernameIsAlreadyTakenError(Exception): ...


class IUserService(Protocol):
    def create_user(self, username: str, full_name: str, password: str) -> UserInDB: ...
    def get_by_username(self, username: str) -> UserInDB | None: ...
    def authenticate_user(self, username: str, password: str) -> UserInDB | None: ...


@dataclass
class InMemoryUserService:
    users: dict[str, UserInDB]

    def get_by_username(self, username: str) -> UserInDB | None:
        if username in self.users:
            return self.users[username]
        else:
            return None

    def create_user(self, username: str, full_name: str, password: str) -> UserInDB:
        hashed_password = get_password_hash(password)
        existing_user = self.get_by_username(username)
        if existing_user is not None:
            raise UsernameIsAlreadyTakenError(username)
        self.users[username] = UserInDB(
            username=username,
            full_name=full_name,
            password=hashed_password,
        )
        return self.users[username]

    def authenticate_user(self, username: str, password: str) -> UserInDB | None:
        user = self.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user


pwd_context: Final = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
