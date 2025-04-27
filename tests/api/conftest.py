import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from e_check.api.dependencies import get_check_service, get_user_service
from e_check.db.models import Base
from e_check.main import app
from e_check.services.checks import DbCheckService, ICheckService
from e_check.services.users import DbUserService, IUserService


# https://anyio.readthedocs.io/en/stable/testing.html#specifying-the-backends-to-run-on
@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:17", driver="psycopg") as postgres:
        yield postgres


@pytest.fixture(scope="function")
async def session(postgres: PostgresContainer):
    sync_engine = create_engine(postgres.get_connection_url())
    Base.metadata.create_all(sync_engine)

    engine = create_async_engine(
        postgres.get_connection_url(),
        isolation_level="SERIALIZABLE",
    )
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine)
    async with async_session() as session:
        yield session

    Base.metadata.drop_all(sync_engine)


@pytest.fixture
async def user_service(session: AsyncSession) -> IUserService:
    return DbUserService(session=session)


@pytest.fixture
async def check_service(session: AsyncSession) -> ICheckService:
    return DbCheckService(session)


@pytest.fixture
async def client(user_service: IUserService, check_service: ICheckService):
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_check_service] = lambda: check_service

    yield TestClient(app)

    app.dependency_overrides = {}
