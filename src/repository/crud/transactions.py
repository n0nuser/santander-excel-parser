"""This module defines the CRUD (Create, Read, Update, Delete) operations for various models
related to transactions and their associated data in the database. It utilizes SQLAlchemy
sessions for database interactions and includes schemas for data validation and serialization.
"""

import logging

from src.repository.crud.base import CRUDBase
from src.repository.models.transactions import Account, Transaction

logger = logging.getLogger(__name__)


class CRUDAccount(CRUDBase[Account]):
    """CRUD operations for the Account model."""


class CRUDTransaction(CRUDBase[Transaction]):
    """CRUD operations for the Transaction model."""


account_crud = CRUDAccount(Account)
transaction_crud = CRUDTransaction(Transaction)
