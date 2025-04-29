from collections.abc import Awaitable
from typing import Any, Protocol

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from e_check.services import auth
from e_check.services.users import IUserService


class UserTokenFactory(Protocol):
    def __call__(
        self, username: str = "", fullname: str = "", password: str = ""
    ) -> Awaitable[str]: ...


@pytest.fixture
async def create_user_token(
    user_service: IUserService,
) -> UserTokenFactory:
    async def _create_user_token(
        username: str = "john",
        fullname: str = "doe",
        password: str = "super-secret",
    ) -> str:
        user = await user_service.create_user(
            username=username,
            full_name=fullname,
            password=password,
        )
        token = auth.create_access_token(data={"sub": user.username})
        return token

    return _create_user_token


@pytest.fixture
async def valid_token(create_user_token: UserTokenFactory) -> str:
    token = await create_user_token()
    return token


class CheckFactory(Protocol):
    def __call__(
        self, *products: dict[str, Any], payment_type: str
    ) -> dict[str, Any]: ...


@pytest.fixture
def check_factory() -> CheckFactory:
    def _check_factory(*products: dict[str, Any], payment_type: str) -> dict[str, Any]:
        check_data: dict[str, Any] = {
            "products": products,
            "payment": {
                "type": payment_type,
                "amount": sum(p["quantity"] * p["price"] for p in products),
            },
        }
        return check_data

    return _check_factory


@pytest.mark.anyio
async def test_authenticated_user_can_create_check(
    client: TestClient, valid_token: str, check_factory: CheckFactory
):
    check_data = check_factory(
        {"name": "Mavic 3T", "price": 298870.00, "quantity": 3.00},
        payment_type="cashless",
    )
    response = client.post(
        "/checks",
        json=check_data,
        headers={"authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED, response.content


@pytest.mark.anyio
async def test_unauthenticated_user_cannot_create_check(client: TestClient):
    response = client.post("/checks", json={})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_payment_amount_cannot_be_lower_than_products_total(
    client: TestClient, valid_token: str
):
    check_data: dict[str, Any] = {
        "products": [
            {
                "name": "Mavic 3T",
                "price": 298870.00,
                "quantity": 3.00,
            }
        ],
        "payment": {
            "amount": 3.00 * 298870.00 - 200,
            "type": "cashless",
        },
    }

    response = client.post(
        "/checks",
        json=check_data,
        headers={"authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_payload = response.json()
    assert response_payload["detail"][0]["loc"] == ["body"]
    assert (
        response_payload["detail"][0]["msg"]
        == "Value error, Payment amount(896410.00) cannot be lower than products total(896610.00)."
    )


@pytest.mark.anyio
async def test_authenticated_user_can_list_own_checks(
    client: TestClient, valid_token: str, check_factory: CheckFactory
):
    check_one_data = check_factory(
        {"name": "Mavic 3T", "price": 298870.00, "quantity": 3.00},
        {"name": "Дрон FPV з акумулятором", "price": 31000.00, "quantity": 20.00},
        payment_type="cash",
    )
    check_two_data = check_factory(
        {"name": "Mavic 3T", "price": 298870.00, "quantity": 3.00},
        payment_type="cash",
    )
    _create_checks(client, valid_token, [check_one_data, check_two_data])

    response = client.get(
        "/checks",
        headers={"authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    items = response.json()["items"]
    assert len(items) == 2


@pytest.mark.anyio
async def test_authenticated_user_cannot_list_checks_from_other_users(
    client: TestClient,
    check_factory: CheckFactory,
    create_user_token: UserTokenFactory,
):
    mary_token = await create_user_token(username="mary")
    mary_check_data = check_factory(
        {"name": "Дрон FPV з акумулятором", "price": 31000.00, "quantity": 20.00},
        payment_type="cash",
    )
    steven_token = await create_user_token(username="steven")
    steven_check_data = check_factory(
        {"name": "Mavic 3T", "price": 298870.00, "quantity": 3.00},
        payment_type="cash",
    )
    _create_checks(client, mary_token, [mary_check_data])
    _create_checks(client, steven_token, [steven_check_data])

    response = client.get(
        "/checks",
        headers={"authorization": f"Bearer {steven_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["products"][0]["name"] == "Mavic 3T"


@pytest.mark.anyio
async def test_filter_list_of_checks_by_payment_type(
    client: TestClient, valid_token: str, check_factory: CheckFactory
):
    check_one_data = check_factory(
        {"name": "Mavic 3T", "price": 298870.00, "quantity": 3.00},
        {"name": "Дрон FPV з акумулятором", "price": 31000.00, "quantity": 20.00},
        payment_type="cash",
    )
    check_two_data = check_factory(
        {"name": "Mavic 3T", "price": 298870.00, "quantity": 3.00},
        payment_type="cashless",
    )
    _create_checks(client, valid_token, [check_one_data, check_two_data])

    response = client.get(
        "/checks",
        params={"payment_type": "cash"},
        headers={"authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    items = response.json()["items"]
    assert len(items) == 1
    assert float(items[0]["payment"]["amount"]) == check_one_data["payment"]["amount"]


@pytest.mark.anyio
async def test_pagination_for_list_of_checks(
    client: TestClient, valid_token: str, check_factory: CheckFactory
):
    checks: list[dict[str, Any]] = []
    for i in range(1, 21):
        check = check_factory(
            {"name": "Mavic 3T", "price": 298870.00, "quantity": i},
            {"name": "Дрон FPV з акумулятором", "price": 31000.00, "quantity": i},
            payment_type="cash",
        )
        checks.append(check)
    _create_checks(client, valid_token, checks)

    response = client.get(
        "/checks",
        params={"page": 2, "page_size": 3},
        headers={"authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["page"] == 2
    assert response.json()["page_size"] == 3
    assert response.json()["last_page"] == 7
    items = response.json()["items"]
    assert len(items) == 3
    assert float(items[0]["products"][0]["quantity"]) == 4


@pytest.mark.anyio
async def test_filter_list_of_checks_by_check_total(
    client: TestClient, valid_token: str, check_factory: CheckFactory
):
    check_one_data = check_factory(
        {"name": "Mavic 3T", "price": 100, "quantity": 3.00},
        {"name": "Дрон FPV з акумулятором", "price": 31000.00, "quantity": 20.00},
        payment_type="cash",
    )
    check_two_data = check_factory(
        {"name": "Mavic 3T", "price": 100.00, "quantity": 3.00},
        payment_type="cashless",
    )
    _create_checks(client, valid_token, [check_one_data, check_two_data])

    response = client.get(
        "/checks",
        params={"check_total_gt": 300},
        headers={"authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    items = response.json()["items"]
    assert len(items) == 1
    assert float(items[0]["payment"]["amount"]) == check_one_data["payment"]["amount"]


def _create_checks(client: TestClient, token: str, checks: list[dict[str, Any]]):
    for check in checks:
        response = client.post(
            "/checks",
            json=check,
            headers={"authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
