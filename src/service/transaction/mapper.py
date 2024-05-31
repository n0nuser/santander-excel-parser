"""Module for mapping transaction data from the database or from the API body.

This module contains functions to transform transaction-related data from database models into
Pydantic schemas, as well as functions to parse and map transaction data into the required schemas
for insertion into the DB.
"""

import logging
from datetime import date

from pydantic import UUID4

from src.controller.api.schemas.transactions import DetailTransaction, FullDetailTransaction
from src.repository.models.transactions import Transaction

# from src.controller.api.schemas.transactions import FullDetailTransaction, GetListTransactions
# from src.repository.models.transactions import Account, Transaction

logger = logging.getLogger(__name__)


def map_transaction_from_db(transaction: Transaction) -> FullDetailTransaction:
    """Maps a transaction model from the database to a Pydantic schema.

    Args:
        transaction (Transaction): The transaction model to map.

    Returns:
        FullDetailTransaction: The Pydantic schema representing the transaction.
    """
    logger.debug("Mapping transaction from database to schema")
    return FullDetailTransaction(
        transaction_id=str(transaction.id),
        amount=transaction.amount,
        balance=transaction.balance,
        operation_effective_date=str(transaction.operation_effective_date),
        operation_original_date=str(transaction.operation_original_date),
        concept=transaction.concept,
        created=str(transaction.created),
        modified=str(transaction.modified),
    )


def map_transaction_from_api(data: DetailTransaction, account_id: UUID4) -> Transaction:
    """Maps a transaction schema from the API to a database model.

    Args:
        data (FullDetailTransaction): The transaction schema to map.
        account_id (UUID4): The account ID to associate the transaction with.

    Returns:
        Transaction: The database model representing the transaction.
    """
    logger.debug("Mapping transaction from schema to database")
    operation_effective_date: date = date.fromisoformat(data.operation_effective_date)
    operation_original_date: date = date.fromisoformat(data.operation_original_date)
    return Transaction(
        amount=data.amount,
        balance=data.balance,
        operation_effective_date=operation_effective_date,
        operation_original_date=operation_original_date,
        concept=data.concept,
        account_id=account_id,
    )
