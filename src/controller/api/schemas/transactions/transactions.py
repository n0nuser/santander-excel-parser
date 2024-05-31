"""This module contains the schemas for the transactions endpoint."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from src.controller.api.schemas.transactions.statistics import BankTransactionStatistics
from src.controller.errors.exceptions import HTTP400BadRequestError
from src.controller.utils.pagination import Pagination
from src.repository.crud.base import Filter


class OrderBy(str, Enum):
    """Enum to define the possible order by values for the Transactions endpoint."""

    ID = "id"
    AMOUNT = "amount"
    BALANCE = "balance"
    OPERATION_ORIGINAL_DATE = "operation_date"
    CREATED = "created_date"
    MODIFIED = "updated_date"


class OrderDirection(str, Enum):
    """Enum to define the possible order direction values for the Transactions endpoint."""

    ASCENDING = "asc"
    DESCENDING = "desc"


class DetailTransaction(BaseModel):
    """Model to define the detail of a transaction. Used for POST and PUT."""

    amount: float
    concept: str
    balance: float
    operation_original_date: str
    operation_effective_date: str


class FullDetailTransaction(DetailTransaction):
    """Model to define the full detail of a transaction. Used for GET by ID."""

    transaction_id: str
    created: str
    modified: str


class GetListTransactions(BaseModel):
    """Model to define the list of transactions. Used for GET List Transactions.

    data (list[GetRulesList]): Data containing the transactions [Optional].
    pagination (Pagination): Pagination for the data [Optional].
    """

    from_date: str = Field(default="")
    to_date: str = Field(default="")
    statistics: BankTransactionStatistics | None = Field(default=None)
    transactions: list[FullDetailTransaction] | list[None] = Field(default=[])
    pagination: Pagination | None = Field(default=None)


def validate_transaction_input(
    amount: int | None,
    amount_start_range: int | None,
    amount_end_range: int | None,
    operation_date: str | None,
    operation_start_range_date: str | None,
    operation_end_range_date: str | None,
) -> None:
    """Validate the transaction input.

    Args:
        amount (int | None): Amount of the transaction.
        amount_start_range (int | None): Amount start range of the transaction.
        amount_end_range (int | None): Amount end range of the transaction.
        operation_date (str | None): Operation date of the transaction.
        operation_start_range_date (str | None): Operation start range date of the transaction.
        operation_end_range_date (str | None): Operation end range date of the transaction.

    Raises:
        HTTP400BadRequestError: Can't use amount and amount range at the same time.
        HTTP400BadRequestError: You must use both amount range fields.
        HTTP400BadRequestError: Can't use operation date and operation date range at the same time.
        HTTP400BadRequestError: You must use both operation date range fields.
    """
    if amount and (amount_start_range or amount_end_range):
        error_msg = "You can't use amount and amount range at the same time."
        raise HTTP400BadRequestError(error_msg)
    if (amount_start_range and not amount_end_range) or (
        not amount_start_range and amount_end_range
    ):
        error_msg = "You must use both amount range fields."
        raise HTTP400BadRequestError(error_msg)

    if operation_date and (operation_start_range_date or operation_end_range_date):
        error_msg = "You can't use operation date and operation date range at the same time."
        raise HTTP400BadRequestError(error_msg)
    if (operation_start_range_date and not operation_end_range_date) or (
        not operation_start_range_date and operation_end_range_date
    ):
        error_msg = "You must use both operation date range fields."
        raise HTTP400BadRequestError(error_msg)


def check_date_format(operation_date: str, operator: str, field: str) -> Field:
    """Check the date format.

    Args:
        operation_date (str): Operation date of the transaction.
        operator (str): Operator to use.
        field (str): Field to filter.

    Raises:
        HTTP400BadRequestError: Invalid operation date format. Please use YYYY-MM-DD.

    Returns:
        Field: Field to filter.
    """
    if (
        operation_date
        and not datetime.strptime(operation_date, "%Y-%m-%d")
        .replace(tzinfo=timezone.utc)
        .isoformat()
    ):
        error_msg = "Invalid operation date format. Please use YYYY-MM-DD."
        raise HTTP400BadRequestError(error_msg)
    return Filter(field=field, operator=operator, value=operation_date)
