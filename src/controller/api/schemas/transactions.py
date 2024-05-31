"""This module contains the schemas for the transactions endpoint."""

from enum import Enum

from pydantic import BaseModel, Field

from src.controller.utils.pagination import Pagination


class OrderBy(str, Enum):
    """Enum to define the possible order by values for the Transactions endpoint."""

    id = "id"
    amount = "amount"
    balance = "balance"
    operation_original_date = "operation_date"
    created = "created_date"
    modified = "updated_date"


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

    data: list[FullDetailTransaction] | None = Field(default=None)
    pagination: Pagination | None = Field(default=None)


GetListTransactions.model_rebuild()
