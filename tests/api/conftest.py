import pytest
from fastapi.testclient import TestClient

from e_check.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
