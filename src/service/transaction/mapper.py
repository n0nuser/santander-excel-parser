"""Module for mapping transaction data from the database or from the API body.

This module contains functions to transform transaction-related data from database models into
Pydantic schemas, as well as functions to parse and map transaction data into the required schemas
for insertion into the DB.
"""

import logging
from datetime import date

import pandas as pd
from pandas import DataFrame
from pydantic import UUID4

from src.controller.api.schemas.transactions.transactions import (
    DetailTransaction,
    FullDetailTransaction,
)
from src.repository.models.transactions import Transaction

# from src.controller.api.schemas.transactions import FullDetailTransaction, GetListTransactions
# from src.repository.models.transactions import Account, Transaction

logger = logging.getLogger(__name__)


def map_api_transaction_from_db(transaction: Transaction) -> FullDetailTransaction:
    """Maps a transaction model from the database to a Pydantic schema.

    Args:
        transaction (Transaction): The transaction model to map.

    Returns:
        FullDetailTransaction: The Pydantic schema representing the transaction.
    """
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


def map_db_transaction_from_api(data: DetailTransaction, account_id: UUID4) -> Transaction:
    """Maps a transaction schema from the API to a database model.

    Args:
        data (FullDetailTransaction): The transaction schema to map.
        account_id (UUID4): The account ID to associate the transaction with.

    Returns:
        Transaction: The database model representing the transaction.
    """
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


def map_dataframe_from_db(transactions: list[Transaction]) -> DataFrame:
    """Maps a list of transaction models from the database to a DataFrame.

    Args:
        transactions (list[Transaction]): The list of transaction models to map.

    Returns:
        DataFrame: The DataFrame representing the transactions.
    """
    dataframe = pd.DataFrame(
        [
            {
                "operation_original_date": t.operation_original_date,
                "operation_effective_date": t.operation_effective_date,
                "concept": t.concept,
                "amount": t.amount,
                "balance": t.balance,
                "account_id": t.account_id,
            }
            for t in transactions
        ]
    )
    # Ensure columns are correctly typed
    dataframe["operation_original_date"] = pd.to_datetime(dataframe["operation_original_date"])
    dataframe["operation_effective_date"] = pd.to_datetime(dataframe["operation_effective_date"])
    dataframe["amount"] = dataframe["amount"].astype(float)
    dataframe["balance"] = dataframe["balance"].astype(float)
    return dataframe
