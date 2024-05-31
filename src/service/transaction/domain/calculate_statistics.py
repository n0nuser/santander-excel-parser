import pandas as pd
from pandas import DataFrame

from src.controller.api.schemas.transactions.statistics import (
    AccountBasedAnalysis,
    AdvancedInsights,
    BankTransactionStatistics,
    BasicStatistics,
    TimeBasedAnalysis,
    TransactionModel,
)


def calculate_statistics(transactions_df: DataFrame) -> BankTransactionStatistics:
    """Calculate statistics from a DataFrame of transactions.

    Args:
        transactions_df (DataFrame): DataFrame of transactions.

    Returns:
        BankTransactionStatistics: Statistics of the transactions.
    """
    # Basic Statistics
    total_transactions = len(transactions_df)
    total_deposited = transactions_df[transactions_df["amount"] > 0]["amount"].sum()
    total_withdrawn = transactions_df[transactions_df["amount"] < 0]["amount"].sum()
    average_transaction_amount = transactions_df["amount"].mean()
    transactions_per_concept = transactions_df["concept"].value_counts().to_dict()

    basic_statistics = BasicStatistics(
        total_transactions=total_transactions,
        total_deposited=total_deposited,
        total_withdrawn=total_withdrawn,
        total_balance=total_deposited + total_withdrawn,
        average_transaction_amount=average_transaction_amount,
        transactions_per_concept=transactions_per_concept,
    )

    # Time-Based Analysis
    transactions_df["operation_original_date"] = pd.to_datetime(
        transactions_df["operation_original_date"]
    )
    transactions_df["operation_effective_date"] = pd.to_datetime(
        transactions_df["operation_effective_date"]
    )
    daily_transactions = (
        transactions_df.groupby(transactions_df["operation_original_date"].dt.date).size().to_dict()
    )
    monthly_transactions = (
        transactions_df.groupby(transactions_df["operation_original_date"].dt.to_period("M"))
        .size()
        .to_dict()
    )

    time_based_analysis = TimeBasedAnalysis(
        daily_transactions=daily_transactions,
        monthly_transactions={str(k): v for k, v in monthly_transactions.items()},
    )

    account_based_analysis = AccountBasedAnalysis(
        average_balance=transactions_df["balance"].mean(),
        final_balance=transactions_df["balance"].iloc[-1],
    )

    # Aggregating transactions by account and date to ensure unique combinations
    aggregated_df = (
        transactions_df.groupby(["account_id", "operation_effective_date"])
        .agg({"amount": "sum", "balance": "last"})
        .reset_index()
    )

    # Advanced Insights
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

    daily_ending_balance_df = (
        aggregated_df.set_index("operation_effective_date")
        .groupby("account_id")["balance"]
        .resample("D")
        .ffill()
        .reset_index()
    )
    daily_ending_balance_dict = daily_ending_balance_df.pivot(
        index="operation_effective_date", columns="account_id", values="balance"
    ).to_dict()

    advanced_insights = AdvancedInsights(
        largest_deposit=largest_deposit_model,
        largest_withdrawal=largest_withdrawal_model,
        daily_ending_balance=daily_ending_balance_dict,
    )

    # Consolidate all statistics into one model
    return BankTransactionStatistics(
        basic_statistics=basic_statistics,
        time_based_analysis=time_based_analysis,
        account_based_analysis=account_based_analysis,
        advanced_insights=advanced_insights,
    )