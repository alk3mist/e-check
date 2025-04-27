from dataclasses import dataclass, field
from typing import Final, Protocol

from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict

from e_check.dto import User


class UserInDB(BaseModel):
    password: str
    username: str
    full_name: str

    model_config = ConfigDict(frozen=True)


class UsernameIsAlreadyTakenError(Exception): ...


class IUserService(Protocol):
    def create_user(self, username: str, full_name: str, password: str) -> User: ...
    def get_by_username(self, username: str) -> User | None: ...
    def authenticate_user(self, username: str, password: str) -> User | None: ...


@dataclass(unsafe_hash=True)
class InMemoryUserService:
    _users: tuple[tuple[str, UserInDB], ...] = field(default_factory=tuple)

    @property
    def users(self) -> dict[str, UserInDB]:
        return dict(self._users)

    def _get_by_username(self, username: str) -> UserInDB | None:
        if username in self.users:
            return self.users[username]
        else:
            return None

    def get_by_username(self, username: str) -> User | None:
        user = self._get_by_username(username)
        if user is None:
            return None
        else:
            return User.model_validate(user, from_attributes=True)

    def create_user(self, username: str, full_name: str, password: str) -> User:
        hashed_password = get_password_hash(password)
        existing_user = self.get_by_username(username)
        if existing_user is not None:
            raise UsernameIsAlreadyTakenError(username)
        new_user = (
            username,
            UserInDB(
                username=username,
                full_name=full_name,
                password=hashed_password,
            ),
        )
        self._users = (*self._users, new_user)
        return User.model_validate(self.users[username], from_attributes=True)

    def authenticate_user(self, username: str, password: str) -> User | None:
        user = self._get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return User.model_validate(user, from_attributes=True)


pwd_context: Final = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
