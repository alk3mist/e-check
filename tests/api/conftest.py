from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from e_check.api.dependencies import get_check_service, get_user_service
from e_check.main import app
from e_check.services.checks import ICheckService, InMemoryCheckService
from e_check.services.users import InMemoryUserService, IUserService


# https://anyio.readthedocs.io/en/stable/testing.html#specifying-the-backends-to-run-on
@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
def user_service() -> IUserService:
    return InMemoryUserService()


@pytest.fixture(scope="function")
def check_service(user_service: IUserService) -> ICheckService:
    return InMemoryCheckService(user_service=user_service)


@pytest.fixture
def client(
    user_service: IUserService, check_service: ICheckService
) -> Iterator[TestClient]:
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_check_service] = lambda: check_service

    yield TestClient(app)

    app.dependency_overrides = {}
