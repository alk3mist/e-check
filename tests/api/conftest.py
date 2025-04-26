from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from e_check.api.dependencies import get_user_service
from e_check.main import app
from e_check.services.users import InMemoryUserService, IUserService


@pytest.fixture(scope="function")
def user_service() -> IUserService:
    return InMemoryUserService(users={})


@pytest.fixture(scope="function")
def override_dependencies(user_service: IUserService) -> Iterator[None]:
    app.dependency_overrides[get_user_service] = lambda: user_service
    yield
    app.dependency_overrides = {}


@pytest.fixture
def client(override_dependencies: None) -> TestClient:
    return TestClient(app)
