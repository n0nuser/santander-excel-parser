"""This module contains the schemas for the transactions endpoint."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class TransactionModel(BaseModel):
    """Model to define the detail of a transaction."""

    operation_original_date: datetime
    operation_effective_date: datetime
    concept: str
    amount: float
    balance: float


class TransactionStatistics(BaseModel):
    """Model to define the statistics of transactions."""

    concept: str
    num_transactions: int
    total_balance: float


class BasicStatistics(BaseModel):
    """Model to define the basic statistics of transactions."""

    total_transactions: int
    total_deposited: float
    total_withdrawn: float
    total_balance: float
    average_transaction_amount: float
    transactions_per_concept: list[TransactionStatistics]


class TimeBasedAnalysisDate(BaseModel):
    """Model to define the time-based analysis of transactions."""

    date: str  # Using period 'YYYY-MM' or 'YYYY-MM-DD'
    num_transactions: int
    total_balance: float


class TimeBasedAnalysis(BaseModel):
    """Model to define the time-based analysis of transactions."""

    daily_transactions: list[TimeBasedAnalysisDate]
    monthly_transactions: list[TimeBasedAnalysisDate]


class AccountBasedAnalysis(BaseModel):
    """Model to define the account-based analysis of transactions."""

    average_balance: float
    final_balance: float


class AdvancedInsights(BaseModel):
    """Model to define the advanced insights of transactions."""

    largest_deposit: TransactionModel
    largest_withdrawal: TransactionModel
    daily_ending_balance: dict[UUID, dict[date, float]]


class BankTransactionStatistics(BaseModel):
    """Model to define the statistics of transactions."""

    basic_statistics: BasicStatistics
    time_based_analysis: TimeBasedAnalysis
    account_based_analysis: AccountBasedAnalysis
    advanced_insights: AdvancedInsights
