from fastapi import status
from fastapi.testclient import TestClient

# /users/register


def test_unauthenticated_user_can_register(client: TestClient):
    data = {
        "username": "john",
        "full_name": "d",
        "password": "secret-pass",
    }

    response = client.post("/users/register", json=data)

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert response.json() == {
        "username": data["username"],
        "full_name": data["full_name"],
    }


def test_if_username_already_taken_then_registration_fails(client: TestClient):
    data = {
        "username": "john",
        "full_name": "d",
        "password": "secret-pass",
    }
    first_response = client.post("/users/register", json=data)
    assert first_response.status_code == status.HTTP_201_CREATED
    data.update(fullname="b")

    second_response = client.post("/users/register", json=data)

    assert second_response.status_code == status.HTTP_409_CONFLICT


# /users/me


def test_authenticated_user_can_access_own_profile(client: TestClient):
    user_data = {
        "username": "john",
        "full_name": "d",
        "password": "secret-pass",
    }
    response = client.post("/users/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED, response.json()

    login_data = {
        "username": "john",
        "password": "secret-pass",
    }
    token_response = client.post("/auth/token", data=login_data)
    assert token_response.status_code == status.HTTP_200_OK
    token = token_response.json()["access_token"]

    response = client.get("/users/me", headers={"authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK


def test_unauthenticated_user_cannot_access_profile(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
