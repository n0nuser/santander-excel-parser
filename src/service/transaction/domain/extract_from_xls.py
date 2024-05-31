"""Defines the application service for the transaction domain."""

import io
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def extract_from_xls(contents: bytes) -> tuple[str, str, float, pd.DataFrame]:
    """Extracts the account information and transactions from an Excel file.

    Args:
        contents (bytes): The contents of the Excel file.

    Returns:
        tuple[str, str, float, pd.DataFrame]: The account number, the account holder,
            the balance, and the transactions data.
    """
    excel_df = pd.read_excel(io.BytesIO(contents), engine="xlrd", header=None)

    # Extract the account information
    account_number = excel_df.iloc[1, 2]
    account_holder = excel_df.iloc[3, 2]
    balance = float(excel_df.iloc[3, 3].replace(" EUR", "").replace(".", "").replace(",", "."))
    transactions_data = excel_df.iloc[9:, :].dropna(how="all")
    return account_number, account_holder, balance, transactions_data
