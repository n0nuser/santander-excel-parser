import io
import logging
from datetime import date, datetime
from uuid import UUID

import pandas as pd
import pytz
from fastapi import UploadFile
from pydantic import UUID4
from sqlalchemy.orm import Session

from src.controller.api.schemas.transactions import (
    DetailTransaction,
    FullDetailTransaction,
    OrderBy,
    OrderDirection,
)
from src.repository.crud.base import Filter
from src.repository.crud.transactions import account_crud, transaction_crud
from src.repository.exceptions import ElementNotFoundError
from src.repository.models.transactions import Account, Transaction
from src.service.exceptions import TransactionServiceError
from src.service.transaction.mapper import map_transaction_from_api, map_transaction_from_db

logger = logging.getLogger(__name__)


class TransactionService:
    """Defines the application service for the transaction domain."""

    @staticmethod
    async def post_transactions_file(db_connection: Session, file: UploadFile) -> str:
        """Function to upload transactions to the database from a file.

        Args:
            db_connection (Session): database connection.
            file (UploadFile): file containing the transactions.
        """
        logger.info("Entering...")
        # Read the file contents
        contents = await file.read()

        # Read Excel file with Pandas
        excel_df = pd.read_excel(io.BytesIO(contents), engine="xlrd", header=None)

        # Extract the account information
        account_number = excel_df.iloc[1, 2]
        account_holder = excel_df.iloc[3, 2]
        balance = float(excel_df.iloc[3, 3].replace(" EUR", "").replace(".", "").replace(",", "."))
        transactions_data = excel_df.iloc[9:, :].dropna(how="all")

        try:
            account = account_crud.get_one_by_field(
                db=db_connection, field="account_number", value=account_number
            )
        except ElementNotFoundError:
            # Create the Account object
            account = Account(
                account_number=account_number,
                account_holder=account_holder,
                balance=balance,
            )
            account_crud.create(db=db_connection, data=account)

        for _, row in transactions_data.iterrows():
            transaction = Transaction(
                operation_original_date=datetime.strptime(row[0], "%d/%m/%Y").replace(
                    tzinfo=pytz.timezone("CET")
                ),
                operation_effective_date=datetime.strptime(row[1], "%d/%m/%Y").replace(
                    tzinfo=pytz.timezone("CET")
                ),
                concept=row[2],
                amount=float(row[3]),
                balance=float(row[4]),
                account_id=account.id,
            )
            transaction_crud.create(db=db_connection, data=transaction)

        return account.account_number
        logger.info("Exiting...")

    @staticmethod
    def get_transactions_list(
        db_connection: Session,
        account_number: str,
        limit: int,
        offset: int,
        order_by: OrderBy,
        order_direction: OrderDirection,
        filters: list[Filter],
    ) -> tuple[list[FullDetailTransaction], int]:
        """Retrieves a list of transactions from the database.

        Args:
            db_connection (Session): database connection.
            limit (int): limit of elements per page.
            offset (int): offset of elements per page.
            order_by (OrderBy): field to order the results by.
            order_direction (OrderDirection): direction to order the results by.
            filters (list[Filter]): list of filters to apply to the query.

        Raises:
            TransactionServiceError: If an error occurs while retrieving the transactions.

        Returns:
            tuple[list[FullDetailTransaction], int]: A tuple containing the list of transactions
                and the total count.
        """
        logger.info("Entering...")
        try:
            account_crud.get_one_by_field(
                db=db_connection, field="account_number", value=account_number
            )
            db_data = transaction_crud.get_list(
                db=db_connection,
                offset=offset,
                limit=limit,
                filters=filters,
                order_by=order_by.name,
                order_direction=order_direction.value,
            )
            logger.debug("Data retrieved: %s", db_data)
            if db_data:
                mapped_data = [map_transaction_from_db(element) for element in db_data if element]
            else:
                mapped_data = []
            logger.debug("Response data: %s", mapped_data)
            db_count = transaction_crud.count(db=db_connection, filters=filters)
            logger.debug("Total response count: %s", db_count)
        except ElementNotFoundError:
            logger.exception("No transactions found with these parameters")
            return [], 0
        except Exception as error:
            logger.exception("An error occurred while retrieving the transactions.")
            raise TransactionServiceError from error
        else:
            return mapped_data, db_count
        finally:
            logger.info("Exiting...")

    @staticmethod
    def get_transaction_id(
        db_connection: Session, transaction_id: UUID4, account_number: str
    ) -> FullDetailTransaction:
        """Function to retrieve a single transaction data from its id.

        Args:
            db_connection (Session): connection to the database.
            transaction_id (UUID4): transaction identifier.
            account_number (str): account number.

        Raises:
            TransactionServiceError: If an error occurs while creating the transaction.

        Returns:
            GetTransactionsDetails: pydantic model with the transaction data.
        """
        logger.info("Entering...")
        try:
            logger.debug("Account Number: %s", account_number)
            account_crud.get_one_by_field(
                db=db_connection, field="account_number", value=account_number
            )
            logger.debug("Transaction Id: %s", transaction_id)
            db_data = transaction_crud.get_by_id(db=db_connection, row_id=transaction_id)
            logger.debug("Data retrieved: %s", db_data)
            response_data = map_transaction_from_db(db_data)
            logger.debug("Transaction retrieved: %s", response_data)
        except ElementNotFoundError:
            logger.exception("Transaction not found.")
            raise
        except Exception as error:
            logger.exception("An error occurred while retrieving the transaction.")
            raise TransactionServiceError from error
        else:
            return response_data
        finally:
            logger.info("Exiting...")

    @staticmethod
    def post_transaction(
        db_connection: Session, data: DetailTransaction, account_number: str
    ) -> UUID:
        """Function to create a transaction in the db from the pydantic model.

        Args:
            db_connection (Session): connection to the database.
            data (DetailTransaction): pydantic model with the transaction data.
            account_number (str): account number.

        Raises:
            TransactionServiceError: If an error occurs while creating the transaction.

        Returns:
            UUID: transaction identifier.
        """
        logger.info("Entering...")
        try:
            logger.debug("Account Number: %s", account_number)
            account = account_crud.get_one_by_field(
                db=db_connection, field="account_number", value=account_number
            )
            db_data = map_transaction_from_api(data, account_id=account.id)
            db_transaction = transaction_crud.create(db=db_connection, data=db_data)
        except Exception as error:
            logger.exception("An error occurred while creating the transaction.")
            raise TransactionServiceError from error
        logger.info("Exiting...")
        return db_transaction.id

    @staticmethod
    def put_transaction(
        db_connection: Session, data: DetailTransaction, transaction_id: UUID4, account_number: str
    ) -> None:
        """Function to modify a transaction in the db from the pydantic model.

        Args:
            db_connection (Session): database connection.
            data (DetailTransaction): transaction data.
            transaction_id (UUID4): transaction ID.
            account_number (str): account number.
        """
        logger.info("Entering...")
        logger.debug("Account Number: %s", account_number)
        account_crud.get_one_by_field(
            db=db_connection, field="account_number", value=account_number
        )
        db_transaction: Transaction = transaction_crud.get_by_id(
            db=db_connection, row_id=transaction_id
        )
        logger.debug("Transaction retrieved: %s", db_transaction)
        db_transaction.amount = data.amount
        db_transaction.concept = data.concept
        db_transaction.balance = data.balance
        db_transaction.operation_original_date = date.fromisoformat(data.operation_original_date)
        db_transaction.operation_effective_date = date.fromisoformat(data.operation_effective_date)
        logger.debug("Transaction updated: %s", db_transaction)
        transaction_crud.update(db=db_connection, data=db_transaction)
        logger.info("Exiting...")

    @staticmethod
    def delete_transaction(
        db_connection: Session, transaction_id: UUID4, account_number: str
    ) -> None:
        """Deletes a transaction from the database.

        Args:
            db_connection (Session): Database connection.
            transaction_id (UUID4): transaction ID.
            account_number (str): account number.

        Raises:
            TransactionServiceException: If an error occurs while deleting the transaction.
        """
        logger.info("Entering...")
        try:
            logger.debug("Account Number: %s", account_number)
            account_crud.get_one_by_field(
                db=db_connection, field="account_number", value=account_number
            )
            logger.info("Deleting transaction.")
            db_transaction = transaction_crud.get_by_id(db=db_connection, row_id=transaction_id)
            transaction_crud.delete_row(db=db_connection, model_obj=db_transaction)
        except ElementNotFoundError:
            logger.exception("Transaction not found.")
            raise
        except Exception as error:
            logger.exception("An error occurred while deleting the transaction.")
            raise TransactionServiceError from error
        finally:
            logger.info("Exiting...")