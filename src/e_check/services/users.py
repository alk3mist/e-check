from dataclasses import dataclass, field
from typing import Final, Protocol

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from e_check.db.models import User as UserInDb
from e_check.dto import User


class UsernameIsAlreadyTakenError(Exception): ...


class IUserService(Protocol):
    async def create_user(
        self, username: str, full_name: str, password: str
    ) -> User: ...
    async def get_by_username(self, username: str) -> User | None: ...
    async def authenticate_user(self, username: str, password: str) -> User | None: ...


@dataclass(unsafe_hash=True)
class InMemoryUserService:
    _users: tuple[tuple[str, UserInDb], ...] = field(default_factory=tuple)

    @property
    def users(self) -> dict[str, UserInDb]:
        return dict(self._users)

    def _get_by_username(self, username: str) -> UserInDb | None:
        if username in self.users:
            return self.users[username]
        else:
            return None

    async def get_by_username(self, username: str) -> User | None:
        user = self._get_by_username(username)
        if user is None:
            return None
        else:
            return _dto_user(user)

    async def create_user(self, username: str, full_name: str, password: str) -> User:
        hashed_password = get_password_hash(password)
        existing_user = await self.get_by_username(username)
        if existing_user is not None:
            raise UsernameIsAlreadyTakenError(username)

        new_user = (
            username,
            UserInDb(
                username=username,
                full_name=full_name,
                password=hashed_password,
            ),
        )
        self._users = (*self._users, new_user)

        return _dto_user(self.users[username])

    async def authenticate_user(self, username: str, password: str) -> User | None:
        user = self._get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None

        return _dto_user(user)


@dataclass
class DbUserService:
    session: AsyncSession

    async def create_user(self, username: str, full_name: str, password: str) -> User:
        hashed_password = get_password_hash(password)
        user = UserInDb(
            username=username,
            full_name=full_name,
            password=hashed_password,
        )
        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        except IntegrityError:
            raise UsernameIsAlreadyTakenError

        return _dto_user(user)

    async def _get_by_username(self, username: str) -> UserInDb | None:
        user = await self.session.scalar(
            select(UserInDb).where(UserInDb.username == username)
        )
        return user

    async def get_by_username(self, username: str) -> User | None:
        user = await self._get_by_username(username)
        if user is None:
            return None

        return _dto_user(user)

    async def authenticate_user(self, username: str, password: str) -> User | None:
        user = await self._get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None

        return _dto_user(user)


def _dto_user(db_user: UserInDb) -> User:
    user = User.model_validate(db_user, from_attributes=True)
    return user


pwd_context: Final = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
