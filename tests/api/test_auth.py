from fastapi import status
from fastapi.testclient import TestClient


def test_existing_user_can_get_access_token(client: TestClient):
    user_data = {
        "username": "john",
        "full_name": "doe",
        "password": "super-secret",
    }
    registration_response = client.post("/users/register", json=user_data)
    assert registration_response.status_code == status.HTTP_201_CREATED

    token_data = user_data.copy()
    token_data.pop("full_name")
    token_response = client.post("/auth/token", data=token_data)

    assert token_response.status_code == status.HTTP_200_OK
    response_payload = token_response.json()
    assert "access_token" in response_payload
    assert response_payload["token_type"] == "bearer"


def test_if_existing_user_provides_wrong_password_then_login_fails(client: TestClient):
    user_data = {
        "username": "john",
        "full_name": "doe",
        "password": "super-secret",
    }
    registration_response = client.post("/users/register", json=user_data)
    assert registration_response.status_code == status.HTTP_201_CREATED

    token_data = {
        "username": user_data["username"],
        "password": "not-so-secret",
    }
    token_response = client.post("/auth/token", data=token_data)
    assert token_response.status_code == status.HTTP_401_UNAUTHORIZED
