"""Module to calculate statistics from a DataFrame of transactions."""

import pandas as pd
from pandas import DataFrame

from src.controller.api.schemas.transactions.statistics import (
    AccountBasedAnalysis,
    AdvancedInsights,
    BankTransactionStatistics,
    BasicStatistics,
    TimeBasedAnalysis,
    TimeBasedAnalysisDate,
    TransactionModel,
    TransactionStatistics,
)


def basic_statistics(transactions_df: DataFrame) -> BasicStatistics:
    """Calculate basic statistics from a DataFrame of transactions.

    Args:
        transactions_df (DataFrame): DataFrame of transactions.

    Returns:
        BasicStatistics: Basic statistics of the transactions.
    """
    total_transactions = len(transactions_df)
    total_deposited = transactions_df[transactions_df["amount"] > 0]["amount"].sum()
    total_withdrawn = transactions_df[transactions_df["amount"] < 0]["amount"].sum()
    average_transaction_amount = transactions_df["amount"].mean()
    transactions_per_concept_df = (
        transactions_df.groupby("concept")
        .agg(num_transactions=("amount", "size"), total_balance=("amount", "sum"))
        .reset_index()
    )
    transactions_per_concept_dict = (
        transactions_per_concept_df.sort_values(by="total_balance", ascending=False)
        .set_index("concept")
        .T.apply(lambda x: [x["num_transactions"], x["total_balance"]])
        .to_dict()
    )
    transactions_per_concept_model = [
        TransactionStatistics(
            concept=key,
            num_transactions=value.get("num_transactions"),
            total_balance=value.get("total_balance"),
        )
        for key, value in transactions_per_concept_dict.items()
    ]

    return BasicStatistics(
        total_transactions=total_transactions,
        total_deposited=total_deposited,
        total_withdrawn=total_withdrawn,
        total_balance=total_deposited + total_withdrawn,
        average_transaction_amount=average_transaction_amount,
        transactions_per_concept=transactions_per_concept_model,
    )


def account_based_analysis(transactions_df: DataFrame) -> AccountBasedAnalysis:
    """Calculate account-based analysis from a DataFrame of transactions.

    Args:
        transactions_df (DataFrame): DataFrame of transactions.

    Returns:
        AccountBasedAnalysis: Account-based analysis of the transactions.
    """
    return AccountBasedAnalysis(
        average_balance=transactions_df["balance"].mean(),
        final_balance=transactions_df["balance"].iloc[-1],
    )


def time_based_analysis(transactions_df: DataFrame) -> TimeBasedAnalysis:
    """Calculate time-based analysis from a DataFrame of transactions.

    Args:
        transactions_df (DataFrame): DataFrame of transactions.

    Returns:
        TimeBasedAnalysis: Time-based analysis of the transactions.
    """
    transactions_df["operation_original_date"] = pd.to_datetime(
        transactions_df["operation_original_date"]
    )
    transactions_df["operation_effective_date"] = pd.to_datetime(
        transactions_df["operation_effective_date"]
    )
    daily_transactions_df = (
        transactions_df.groupby(transactions_df["operation_original_date"].dt.date)
        .agg(num_transactions=("amount", "size"), total_balance=("amount", "sum"))
        .reset_index()
    )
    daily_transactions_dict = daily_transactions_df.set_index("operation_original_date").T.to_dict()
    daily_transactions_model = [
        TimeBasedAnalysisDate(
            date=str(key),
            num_transactions=value.get("num_transactions"),
            total_balance=value.get("total_balance"),
        )
        for key, value in daily_transactions_dict.items()
    ]

    monthly_transactions_df = (
        transactions_df.groupby(transactions_df["operation_original_date"].dt.to_period("M"))
        .agg(num_transactions=("amount", "size"), total_balance=("amount", "sum"))
        .reset_index()
    )
    monthly_transactions_dict = monthly_transactions_df.set_index(
        "operation_original_date"
    ).T.to_dict()
    montly_transactions_model = [
        TimeBasedAnalysisDate(
            date=str(key),
            num_transactions=value.get("num_transactions"),
            total_balance=value.get("total_balance"),
        )
        for key, value in monthly_transactions_dict.items()
    ]

    return TimeBasedAnalysis(
        daily_transactions=daily_transactions_model,
        monthly_transactions=montly_transactions_model,
    )


def advanced_insights(transactions_df: DataFrame) -> AdvancedInsights:
    """Calculate advanced insights from a DataFrame of transactions.

    Args:
        transactions_df (DataFrame): DataFrame of transactions.

    Returns:
        AdvancedInsights: Advanced insights of the transactions.
    """
    largest_deposit = transactions_df[transactions_df["amount"] > 0].nlargest(1, "amount").iloc[0]
    largest_withdrawal = (
        transactions_df[transactions_df["amount"] < 0].nsmallest(1, "amount").iloc[0]
    )

    largest_deposit_model = TransactionModel(
        operation_original_date=largest_deposit["operation_original_date"],
        operation_effective_date=largest_deposit["operation_effective_date"],
        concept=largest_deposit["concept"],
        amount=largest_deposit["amount"],
        balance=largest_deposit["balance"],
    )

    largest_withdrawal_model = TransactionModel(
        operation_original_date=largest_withdrawal["operation_original_date"],
        operation_effective_date=largest_withdrawal["operation_effective_date"],
        concept=largest_withdrawal["concept"],
        amount=largest_withdrawal["amount"],
        balance=largest_withdrawal["balance"],
    )

    # Aggregating transactions by account and date to ensure unique combinations
    aggregated_df = (
        transactions_df.groupby(["account_id", "operation_effective_date"])
        .agg({"amount": "sum", "balance": "last"})
        .reset_index()
    )
    daily_ending_balance_df = (
        aggregated_df.set_index("operation_effective_date")
        .groupby("account_id")["balance"]
        .resample("D")
        .ffill()
        .reset_index()
    )
    daily_ending_balance_dict = daily_ending_balance_df.pivot_table(
        index="operation_effective_date", columns="account_id", values="balance"
    ).to_dict()

    return AdvancedInsights(
        largest_deposit=largest_deposit_model,
        largest_withdrawal=largest_withdrawal_model,
        daily_ending_balance=daily_ending_balance_dict,
    )


def calculate_statistics(transactions_df: DataFrame) -> BankTransactionStatistics:
    """Calculate statistics from a DataFrame of transactions.

    Args:
        transactions_df (DataFrame): DataFrame of transactions.

    Returns:
        BankTransactionStatistics: Statistics of the transactions.
    """
    basic_statistics_model = basic_statistics(transactions_df)
    time_based_analysis_model = time_based_analysis(transactions_df)
    account_based_analysis_model = account_based_analysis(transactions_df)
    advanced_insights_model = advanced_insights(transactions_df)
    # Consolidate all statistics into one model
    return BankTransactionStatistics(
        basic_statistics=basic_statistics_model,
        time_based_analysis=time_based_analysis_model,
        account_based_analysis=account_based_analysis_model,
        advanced_insights=advanced_insights_model,
    )
