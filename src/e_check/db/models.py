from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, MetaData, String, Uuid, func, select
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    column_property,
    mapped_column,
    relationship,
)

meta = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class Base(AsyncAttrs, DeclarativeBase):
    metadata = meta


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)

    checks: Mapped[list["Check"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=True, lazy="raise"
    )


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[int] = mapped_column(ForeignKey("check.id"))
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column()
    quantity: Mapped[Decimal] = mapped_column()

    check: Mapped["Check"] = relationship(back_populates="products", lazy="raise")

    total: Mapped[Decimal] = column_property(quantity * price)


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[int] = mapped_column(ForeignKey("check.id"))
    type: Mapped[Literal["cash", "cashless"]] = mapped_column(
        Enum("cash", "cashless", name="payment_type_enum", native_enum=False)
    )
    amount: Mapped[Decimal] = mapped_column()
    check: Mapped["Check"] = relationship(back_populates="payment", lazy="raise")


class Check(Base):
    __tablename__ = "check"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=True), nullable=False, default=uuid4
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    user: Mapped[User] = relationship(back_populates="checks", lazy="joined")
    products: Mapped[list[Product]] = relationship(
        back_populates="check",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=True,
    )
    payment: Mapped[Payment] = relationship(
        back_populates="check",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )

    total: Mapped["Decimal"] = column_property(
        select(func.sum(Product.total))
        .where(Product.check_id == id)
        .correlate_except(Product)
        .scalar_subquery()
    )
