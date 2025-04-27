import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from e_check.db import models as db
from e_check.dto import Check, CreateCheck, User
from e_check.services.check_printer import CheckPrinter
from e_check.services.users import IUserService


class CheckNotFoundError(Exception): ...


class ICheckService(ABC):
    @abstractmethod
    async def create_check(self, user: User, new_check: CreateCheck) -> Check: ...

    @abstractmethod
    async def count_checks(
        self,
        *,
        user: User,
        date_gt: date | None = None,
        check_total_gt: Decimal | None = None,
        payment_type: Literal["cash", "cashless"] | None = None,
    ) -> int: ...

    @abstractmethod
    async def get_checks(
        self,
        *,
        user: User,
        date_gt: date | None = None,
        check_total_gt: Decimal | None = None,
        payment_type: Literal["cash", "cashless"] | None = None,
        limit: int,
        offset: int,
    ) -> Iterable[Check]: ...

    @abstractmethod
    async def print_check(self, check_id: uuid.UUID) -> str: ...


@dataclass
class InMemoryCheckService(ICheckService):
    user_service: IUserService = field(hash=False)
    user_checks: defaultdict[str, list[Check]] = field(
        default_factory=lambda: defaultdict(list)
    )

    async def create_check(self, user: User, new_check: CreateCheck) -> Check:
        check = Check(
            id=uuid.uuid4(),
            products=new_check.products,
            payment=new_check.payment,
            created_at=datetime.now(),
        )

        self.user_checks[user.username].append(check)

        return check

    async def get_checks(
        self,
        *,
        user: User,
        date_gt: date | None = None,
        check_total_gt: Decimal | None = None,
        payment_type: None | Literal["cash"] | Literal["cashless"] = None,
        limit: int,
        offset: int,
    ) -> Iterable[Check]:
        checks = self._get_all_checks(
            user=user,
            date_gt=date_gt,
            check_total_gt=check_total_gt,
            payment_type=payment_type,
        )
        return list(checks)[offset : offset + limit]

    async def count_checks(
        self,
        *,
        user: User,
        date_gt: date | None = None,
        check_total_gt: Decimal | None = None,
        payment_type: Literal["cash", "cashless"] | None = None,
    ) -> int:
        checks = self._get_all_checks(
            user=user,
            date_gt=date_gt,
            check_total_gt=check_total_gt,
            payment_type=payment_type,
        )
        return len(list(checks))

    async def print_check(self, check_id: uuid.UUID) -> str:
        check_info = self._get_check_by_id_with_username(check_id)
        if check_info is None:
            raise CheckNotFoundError

        username, check = check_info
        user = await self.user_service.get_by_username(username)
        assert user is not None

        printer = CheckPrinter(width=32)
        content = printer.render_check(user, check)
        return content

    def _get_check_by_id_with_username(
        self, check_id: uuid.UUID
    ) -> tuple[str, Check] | None:
        for username, checks in self.user_checks.items():
            for check in checks:
                if check.id == check_id:
                    return username, check
        else:
            return None

    def _get_all_checks(
        self,
        *,
        user: User,
        date_gt: date | None = None,
        check_total_gt: Decimal | None = None,
        payment_type: None | Literal["cash"] | Literal["cashless"] = None,
    ) -> Iterable[Check]:
        satisfied = self._build_filters(
            date_gt=date_gt,
            check_total_gt=check_total_gt,
            payment_type=payment_type,
        )
        checks = filter(satisfied, self.user_checks[user.username])
        return checks

    def _build_filters(
        self,
        *,
        date_gt: date | None = None,
        check_total_gt: Decimal | None = None,
        payment_type: Literal["cash", "cashless"] | None = None,
    ) -> Callable[[Check], bool]:
        filters: list[Callable[[Check], bool]] = []
        if date_gt is not None:
            filters.append(lambda c: c.created_at.date() > date_gt)
        if check_total_gt is not None:
            filters.append(lambda c: c.total > check_total_gt)
        if payment_type is not None:
            filters.append(lambda c: c.payment.type == payment_type)

        return lambda c: all((f(c) for f in filters))


@dataclass
class DbCheckService(ICheckService):
    session: AsyncSession

    async def create_check(self, user: User, new_check: CreateCheck) -> Check:
        products = [
            db.Product(name=p.name, price=p.price, quantity=p.quantity)
            for p in new_check.products
        ]
        payment = db.Payment(
            type=new_check.payment.type, amount=new_check.payment.amount
        )
        db_user = await self.session.scalar(
            select(db.User).where(db.User.username == user.username)
        )
        db_check = db.Check(
            user=db_user,
            products=products,
            payment=payment,
            created_at=datetime.now(),
        )

        self.session.add(db_check)
        await self.session.commit()
        await self.session.refresh(db_check)

        check = Check.model_validate(db_check, from_attributes=True, by_alias=True)
        return check

    async def count_checks(
        self,
        *,
        user: User,
        date_gt: date | None = None,
        check_total_gt: Decimal | None = None,
        payment_type: Literal["cash", "cashless"] | None = None,
    ) -> int:
        stmt = (
            select(func.count(db.Check.id))
            .join(db.User)
            .where(db.User.username == user.username)
        )
        stmt = self._prepare_stmt(stmt, date_gt, check_total_gt, payment_type)
        count = await self.session.scalar(stmt)
        assert count is not None
        return count

    async def get_checks(
        self,
        *,
        user: User,
        date_gt: date | None = None,
        check_total_gt: Decimal | None = None,
        payment_type: Literal["cash", "cashless"] | None = None,
        limit: int,
        offset: int,
    ) -> Iterable[Check]:
        stmt = (
            select(db.Check)
            .join(db.User)
            .where(db.User.username == user.username)
            .order_by(db.Check.created_at)
            .limit(limit)
            .offset(offset)
        )
        stmt = self._prepare_stmt(stmt, date_gt, check_total_gt, payment_type)
        db_checks = await self.session.scalars(stmt)
        checks = (
            Check.model_validate(c, from_attributes=True, by_alias=True)
            for c in db_checks
        )
        return checks

    def _prepare_stmt[T](
        self,
        stmt: Select[tuple[T]],
        date_gt: date | None = None,
        check_total_gt: Decimal | None = None,
        payment_type: Literal["cash", "cashless"] | None = None,
    ):
        if date_gt:
            stmt = stmt.where(func.date(db.Check.created_at) > date_gt)
        if check_total_gt:
            stmt = stmt.where(db.Check.total > check_total_gt)
        if payment_type:
            stmt = stmt.join(db.Payment).where(db.Payment.type == payment_type)

        return stmt

    async def print_check(self, check_id: uuid.UUID) -> str:
        check = await self.session.scalar(
            select(db.Check).join(db.User).where(db.Check.external_id == check_id)
        )
        if not check:
            raise CheckNotFoundError

        printer = CheckPrinter()
        content = printer.render_check(
            User.model_validate(check.user, from_attributes=True),
            check=Check.model_validate(check, from_attributes=True, by_alias=True),
        )
        return content
