"""This module contains the schemas for the transactions endpoint."""

from typing import Annotated

from fastapi import Query


def req_pagination(
    limit: Annotated[
        int | None,
        Query(
            description="Number of records returned per page."  # noqa: ISC003
            + " If specified on entry, this will be the value of the query,"
            + " otherwise it will be the value value set by default.",
            ge=1,
            le=100,
        ),
    ] = None,
    offset: Annotated[
        int | None,
        Query(
            description="Record number from which you want to receive"  # noqa: ISC003
            + " the number of records indicated in the limit."
            + " If it is indicated at the entry, it will be the value of the query."
            + " If it is not indicated at the input, as the query is on the first page,"
            + " its value will be 0.",
            ge=0,
            le=100,
        ),
    ] = None,
) -> tuple[int | None, int | None]:
    """Function to validate the transaction filters.

    Args:
        limit (_type_, optional): Number of records returned per page.
            If specified on entry, this will be the value of the query,
            otherwise it will be the value value set by default.
        offset (_type_, optional): Record number from which you want to receive the
            number of records indicated in the limit. If it is indicated at the entry,
            it will be the value of the query. If it is not indicated at the input,
            as the query is on the first page, its value will be 0.

    Returns:
        tuple[int | None, int | None]: Returns the limit and offset.
    """
    return limit, offset
