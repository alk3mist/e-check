from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from e_check.api.dependencies import get_user_service
from e_check.main import app
from e_check.services.users import InMemoryUserService, IUserService


@pytest.fixture(scope="function")
def user_service() -> IUserService:
    return InMemoryUserService(users={})


@pytest.fixture
def client(user_service: IUserService) -> Iterator[TestClient]:
    app.dependency_overrides[get_user_service] = lambda: user_service

    yield TestClient(app)

    app.dependency_overrides = {}
