from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from e_check.api.dependencies import get_check_service, get_current_user
from e_check.api.schemas import PaginatedResponse, Pagination
from e_check.dto import Check, CreateCheck, User
from e_check.services.checks import CheckNotFoundError, ICheckService

router = APIRouter(tags=["checks"])


@router.post("/checks", status_code=status.HTTP_201_CREATED)
async def create_check(
    create_check: CreateCheck,
    user: User = Depends(get_current_user),
    check_service: ICheckService = Depends(get_check_service),
) -> Check:
    check = check_service.create_check(user, create_check)
    return check


@router.get("/checks")
async def list_checks(
    user: User = Depends(get_current_user),
    check_service: ICheckService = Depends(get_check_service),
    *,
    date_gt: date | None = None,
    check_total_gt: Decimal | None = None,
    payment_type: Literal["cash", "cashless"] | None = None,
    pagination: Pagination = Depends(Pagination.query()),
) -> PaginatedResponse[Check]:
    total_count = check_service.count_checks(
        user=user,
        date_gt=date_gt,
        check_total_gt=check_total_gt,
        payment_type=payment_type,
    )
    checks = check_service.get_checks(
        user=user,
        date_gt=date_gt,
        check_total_gt=check_total_gt,
        payment_type=payment_type,
        limit=pagination.page_size,
        offset=pagination.offset,
    )
    return PaginatedResponse[Check].from_iterable(pagination, checks, total_count)


class PlainTextResponse(Response):
    media_type = "text/plain"


@router.get("/checks/{check_id}/print", response_class=PlainTextResponse)
async def print_check(
    check_service: ICheckService = Depends(get_check_service),
    *,
    check_id: UUID,
):
    try:
        check_print = check_service.print_check(check_id)
    except CheckNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return PlainTextResponse(content=check_print)
