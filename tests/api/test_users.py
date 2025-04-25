import pytest
from fastapi import status
from fastapi.testclient import TestClient

from e_check.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_unauthenticated_user_can_register(client: TestClient):
    data = {
        "username": "john",
        "full_name": "d",
        "password": "secret-pass",
    }
    response = client.post(
        "/users/register",
        json=data,
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
