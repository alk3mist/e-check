from datetime import datetime
from decimal import Decimal
from functools import cached_property
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    StringConstraints,
    computed_field,
    model_validator,
)

# Auth


class Token(BaseModel):
    access_token: str
    token_type: str


# Users


class User(BaseModel):
    username: str
    full_name: str


class RegisterUser(BaseModel):
    username: Annotated[
        str,
        StringConstraints(
            min_length=2, max_length=255, strict=True, strip_whitespace=True
        ),
    ]

    full_name: Annotated[
        str,
        StringConstraints(
            min_length=1, max_length=255, strict=True, strip_whitespace=True
        ),
    ]
    password: SecretStr = Field(
        min_length=8,
        max_length=255,
        strict=True,
    )


# Checks


class Product(BaseModel):
    name: Annotated[
        str, StringConstraints(min_length=2, max_length=255, strip_whitespace=True)
    ]
    price: Annotated[Decimal, Field(allow_inf_nan=False, gt=0, decimal_places=2)]
    quantity: Annotated[Decimal, Field(allow_inf_nan=False, gt=0, decimal_places=2)]

    @computed_field
    @cached_property
    def total(self) -> Decimal:
        return self.price * self.quantity


class Payment(BaseModel):
    type: Literal["cash", "cashless"]
    amount: Annotated[Decimal, Field(allow_inf_nan=False, gt=0, decimal_places=2)]


class CreateCheck(BaseModel):
    products: Annotated[list[Product], Field(min_length=1)]
    payment: Payment

    @model_validator(mode="after")
    def check_payment_amount_gt_products_total(self) -> Self:
        total = sum((p.total for p in self.products), start=Decimal(0))
        if self.payment.amount < total:
            raise ValueError(
                f"Payment amount({self.payment.amount:.2f}) cannot be lower than products total({total:.2f})."
            )
        return self


class Check(BaseModel):
    id: UUID
    products: Annotated[list[Product], Field(min_length=1)]
    payment: Payment

    @computed_field
    @cached_property
    def total(self) -> Decimal:
        return sum((p.total for p in self.products), start=Decimal(0))

    @computed_field
    @cached_property
    def rest(self) -> Decimal:
        return self.payment.amount - self.total

    created_at: datetime
