"""Defines the application service for the transaction domain."""

import logging
from typing import TYPE_CHECKING

from src.controller.api.schemas.transactions.transactions import FullDetailTransaction
from src.repository.models.transactions import Transaction
from src.service.transaction.mapper import map_api_transaction_from_db

if TYPE_CHECKING:
    from datetime import date

logger = logging.getLogger(__name__)


def transaction_list_details(
    db_data: list[Transaction | None],
) -> tuple[list[FullDetailTransaction], str, str]:
    """Extracts the transaction details from the database data.

    Args:
        db_data (list[Transaction]): The list of transactions from the database.

    Returns:
        tuple[list[FullDetailTransaction], str, str]: The list of transactions,
            the start date, and the end date in isoformat.
    """
    mapped_data = []
    from_date: date | None = None
    to_date: date | None = None
    for element in db_data:
        if element:
            api_transaction = map_api_transaction_from_db(element)
            mapped_data.append(api_transaction)
            if element.operation_original_date:
                if not from_date or element.operation_original_date < from_date:
                    from_date = element.operation_original_date
                    from_date_str = from_date.isoformat()
                if not to_date or element.operation_original_date > to_date:
                    to_date = element.operation_original_date
                    to_date_str = to_date.isoformat()
    return mapped_data, from_date_str, to_date_str
