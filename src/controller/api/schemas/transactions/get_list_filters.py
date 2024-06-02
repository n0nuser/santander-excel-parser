"""This module contains the schemas for the transactions endpoint."""

from typing import Annotated

from fastapi import Query

from src.controller.api.schemas.transactions.transactions import (
    OrderBy,
    OrderDirection,
    check_date_format,
    validate_transaction_input,
)
from src.repository.crud.base import Filter


def req_transaction_filters(
    stastistics: Annotated[  # noqa: FBT002
        bool, Query(description="Flag to indicate if the statistics should be calculated.")
    ] = False,
    concept: Annotated[
        str | None,
        Query(
            description="Concept of the transaction.",
            example="Compra Apple.com/bill, Itunes.com, Tarjeta 543719440150905 , Comision 0,00",
        ),
    ] = None,
    amount: Annotated[
        int | None,
        Query(description="Amount of the transaction.", example="0.00"),
    ] = None,
    amount_start_range: Annotated[
        int | None,
        Query(description="Amount start range of the transaction.", example="0.00"),
    ] = None,
    amount_end_range: Annotated[
        int | None,
        Query(description="Amount end range of the transaction.", example="0.00"),
    ] = None,
    operation_date: Annotated[
        str | None,
        Query(description="Operation date of the transaction.", example="2021-07-27"),
    ] = None,
    operation_start_range_date: Annotated[
        str | None,
        Query(description="Operation start range date of the transaction.", example="2021-07-27"),
    ] = None,
    operation_end_range_date: Annotated[
        str | None,
        Query(description="Operation end range date of the transaction.", example="2021-07-27"),
    ] = None,
    order_by: Annotated[
        OrderBy,
        Query(description="Order by field. Default is operation date."),
    ] = OrderBy.OPERATION_ORIGINAL_DATE,
    order_direction: Annotated[
        OrderDirection,
        Query(description="Order direction. Default is descending."),
    ] = OrderDirection.DESCENDING,
) -> tuple[list[Filter], OrderBy, OrderDirection]:
    """Function to validate the transaction filters.

    Args:
        stastistics (Annotated[ bool, Query, optional):
            Flag to indicate if the statistics should be calculated.
        concept (Annotated[ str  |  None, Query, optional): Concept of the transaction.
        amount (Annotated[ int  |  None, Query, optional): Amount of the transaction.
        amount_start_range (Annotated[ int  |  None, Query, optional):
            Amount start range of the transaction.
        amount_end_range (Annotated[ int  |  None, Query, optional):
            Amount end range of the transaction.
        operation_date (Annotated[ str  |  None, Query, optional):
            Operation date of the transaction.
        operation_start_range_date (Annotated[ str  |  None, Query, optional):
            Operation start range date of the transaction.
        operation_end_range_date (Annotated[ str  |  None, Query, optional):
            Operation end range date of the transaction.
        order_by (Annotated[ OrderBy, Query, optional): Order by field. Default is operation date.
        order_direction (Annotated[ OrderDirection, Query, optional): Order direction.
            Default is descending.

    Raises:
        HTTP400BadRequestError: Amount and amount range can't be used at the same time.
        HTTP400BadRequestError: You must use both amount range fields.
        HTTP400BadRequestError: Operation date and operation date range
            can't be used at the same time.
        HTTP400BadRequestError: You must use both operation date range fields.
        HTTP400BadRequestError: Invalid operation date format. Please use YYYY-MM-DD.
        HTTP400BadRequestError: Invalid operation date format. Please use YYYY-MM-DD.
        HTTP400BadRequestError: Invalid operation date format. Please use YYYY-MM-DD.

    Returns:
        tuple[list[Filter], OrderBy, OrderDirection]:
            Returns the transaction filters, order by and order direction.
    """
    validate_transaction_input(
        amount,
        amount_start_range,
        amount_end_range,
        operation_date,
        operation_start_range_date,
        operation_end_range_date,
    )

    transaction_filters: list[Filter] = []
    if concept:
        transaction_filters.append(Filter(field="concept", operator="contains", value=concept))
    if amount:
        transaction_filters.append(Filter(field="amount", operator="eq", value=amount))
    if amount_start_range:
        transaction_filters.append(Filter(field="amount", operator="gte", value=amount_start_range))
    if amount_end_range:
        transaction_filters.append(Filter(field="amount", operator="lte", value=amount_end_range))
    if operation_date:
        field = "operation_original_date"
        transaction_filters.append(check_date_format(operation_date, "eq", field))
    if operation_start_range_date:
        field = "operation_original_date"
        transaction_filters.append(check_date_format(operation_start_range_date, "gte", field))
    if operation_end_range_date:
        field = "operation_original_date"
        transaction_filters.append(check_date_format(operation_end_range_date, "lte", field))
    return stastistics, transaction_filters, order_by, order_direction
