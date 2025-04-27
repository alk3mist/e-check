import math
from collections.abc import Callable, Iterable, Sequence
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, Field


class Pagination(BaseModel):
    """Pagination parameters."""

    page: Annotated[int, Field(gt=0)]
    page_size: Annotated[int, Field(gt=0)]

    @staticmethod
    def query(
        default_page_size: int = 50, max_page_size: int = 200
    ) -> Callable[[], "Pagination"]:
        """Constructs query parameters for a paginated response."""

        if default_page_size > max_page_size:
            raise ValueError(
                f"default page {default_page_size} is greater than max {max_page_size}"
            )

        def extract_query(
            page: int = Query(1, ge=1),
            page_size: int = Query(default_page_size, ge=1, le=max_page_size),
        ) -> Pagination:
            return Pagination(page=page, page_size=page_size)

        return extract_query

    @property
    def offset(self) -> int:
        """Zero-based offset for collection."""
        return (self.page - 1) * self.page_size

    def slice[T](self, collection: Sequence[T]) -> Sequence[T]:
        """Get a fragment of the collection that matches the pagination parameters."""
        return collection[self.offset : self.offset + self.page_size]


class PaginatedResponse[T](BaseModel):
    page: Annotated[int, Field(ge=1)]
    page_size: Annotated[int, Field(ge=1)]
    last_page: Annotated[int, Field(ge=1)]
    items: list[T]

    @classmethod
    def from_iterable(
        cls: type["PaginatedResponse[T]"],
        pagination: Pagination,
        items: Iterable[T],
        total_count: int,
    ) -> "PaginatedResponse[T]":
        """Wraps the collection's page into a paginated response."""
        last_page = math.ceil(total_count / pagination.page_size) or 1
        if pagination.page > last_page:
            raise ValueError(
                f"Page {pagination.page} is out of boundary: last page is {last_page}."
            )
        return cls(
            page=pagination.page,
            page_size=pagination.page_size,
            last_page=last_page,
            items=list(items),
        )

    @classmethod
    def from_full_sequence(
        cls, pagination: Pagination, items: Sequence[T]
    ) -> "PaginatedResponse[T]":
        """Response for a specific page from a whole collection."""
        return cls.from_iterable(
            pagination,
            pagination.slice(items),
            len(items),
        )
