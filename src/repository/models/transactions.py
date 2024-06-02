"""
This module defines the database entities and their relationships
for managing transactions and their associated data.
"""

from datetime import date

from sqlalchemy import UUID, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repository.models.base import BaseTimestamps


class Account(BaseTimestamps):
    """Represents an account entity in the database."""

    account_number: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    account_holder: Mapped[str] = mapped_column(String, nullable=False)
    balance: Mapped[float] = mapped_column(Integer, nullable=False)
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="subquery",
    )

    def __str__(self) -> str:
        return f"{self.account_number} - {self.account_holder}"

    def __repr__(self) -> str:
        return f"{self.account_number} - {self.account_holder}"


class Transaction(BaseTimestamps):
    """Represents a transaction entity in the database."""

    operation_original_date: Mapped[date] = mapped_column(Date, nullable=False)
    operation_effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    concept: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(
        back_populates="transactions",
    )

    # Ensure that the combination of the following fields is unique
    __table_args__ = (
        UniqueConstraint(
            "operation_original_date",
            "operation_effective_date",
            "concept",
            "amount",
            "balance",
            name="uq__op_orig_date__op_eff_date__concept__amt__bal",
        ),
    )

    def __str__(self) -> str:
        return f"{self.id}"

    def __repr__(self) -> str:
        return f"{self.id}"
