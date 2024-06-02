"""Defines the application service for the transaction domain."""

import io
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def extract_from_xls(contents: bytes) -> tuple[str, str, pd.DataFrame]:
    """Extracts the account information and transactions from an Excel file.

    Args:
        contents (bytes): The contents of the Excel file.

    Returns:
        tuple[str, str, pd.DataFrame]: The account number, the account holder,
            and the transactions data.
    """
    excel_df = pd.read_excel(io.BytesIO(contents), engine="xlrd", header=None)

    # Extract the account information
    account_number = excel_df.iloc[1, 2]
    account_holder = excel_df.iloc[3, 2]
    transactions_data = excel_df.iloc[9:, :].dropna(how="all")
    return account_number, account_holder, transactions_data
