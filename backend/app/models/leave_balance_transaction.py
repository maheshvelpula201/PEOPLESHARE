
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    and_,
    func,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company
from app.models.leave_balance import LeaveBalance


class LeaveTransactionType(str, Enum):
    ACCRUAL = "accrual"
    RESERVATION = "reservation"
    RELEASE = "release"
    CONSUMPTION = "consumption"
    ADJUSTMENT = "adjustment"
    CARRY_FORWARD = "carry_forward"


class LeaveBalanceTransaction(Base):
    """Immutable ledger entry describing a leave balance change.

    Each delta is a signed number of half-day units.
    For example, reserved_delta=2 reserves one full day.
    """

    __tablename__ = "leave_balance_transactions"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_leave_transaction_company_id_id",
        ),
        UniqueConstraint(
            "company_id",
            "idempotency_key",
            name="uq_leave_transaction_idempotency",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_leave_transaction_company",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "balance_id"],
            ["leave_balances.company_id", "leave_balances.id"],
            name="fk_leave_transaction_company_balance",
            ondelete="RESTRICT",
        ),
        
        ForeignKeyConstraint(
            ["company_id", "created_by_user_id"],
            ["users.company_id", "users.id"],
            name="fk_leave_transaction_created_by",
            ondelete="RESTRICT",
        ),

        CheckConstraint(
            "entitled_delta <> 0 OR carry_forward_delta <> 0 "
            "OR adjustment_delta <> 0 OR reserved_delta <> 0 "
            "OR consumed_delta <> 0",
            name="ck_leave_transaction_has_delta",
        ),
        CheckConstraint(
    """
    (
        transaction_type = 'accrual'
        AND entitled_delta > 0
        AND carry_forward_delta = 0
        AND adjustment_delta = 0
        AND reserved_delta = 0
        AND consumed_delta = 0
    )
    OR
    (
        transaction_type = 'reservation'
        AND reserved_delta > 0
        AND entitled_delta = 0
        AND carry_forward_delta = 0
        AND adjustment_delta = 0
        AND consumed_delta = 0
    )
    OR
    (
        transaction_type = 'release'
        AND reserved_delta < 0
        AND entitled_delta = 0
        AND carry_forward_delta = 0
        AND adjustment_delta = 0
        AND consumed_delta = 0
    )
    OR
    (
        transaction_type = 'consumption'
        AND consumed_delta > 0
        AND entitled_delta = 0
        AND carry_forward_delta = 0
        AND adjustment_delta = 0
        AND reserved_delta = 0
    )
    OR
    (
        transaction_type = 'adjustment'
        AND adjustment_delta <> 0
        AND entitled_delta = 0
        AND carry_forward_delta = 0
        AND reserved_delta = 0
        AND consumed_delta = 0
    )
    OR
    (
        transaction_type = 'carry_forward'
        AND carry_forward_delta <> 0
        AND entitled_delta = 0
        AND adjustment_delta = 0
        AND reserved_delta = 0
        AND consumed_delta = 0
    )
    """,
    name="ck_leave_transaction_type_delta_consistency",
),
        CheckConstraint(
            "length(trim(idempotency_key)) > 0",
            name="ck_leave_transaction_idempotency_not_blank",
        ),
        CheckConstraint(
            "length(trim(reason)) > 0",
            name="ck_leave_transaction_reason_not_blank",
        ),
        Index(
            "ix_leave_transaction_company_balance_created",
            "company_id",
            "balance_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    balance_id: Mapped[int] = mapped_column(nullable=False)

    transaction_type: Mapped[LeaveTransactionType] = mapped_column(
        SQLAlchemyEnum(
            LeaveTransactionType,
            name="leave_transaction_type",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
    )

    entitled_delta: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    carry_forward_delta: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    adjustment_delta: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    reserved_delta: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    consumed_delta: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    reference_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    reference_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    company: Mapped["Company"] = relationship(
        primaryjoin=lambda: LeaveBalanceTransaction.company_id == Company.id,
    )

    balance: Mapped["LeaveBalance"] = relationship(
        primaryjoin=lambda: and_(
            LeaveBalanceTransaction.company_id == LeaveBalance.company_id,
            foreign(LeaveBalanceTransaction.balance_id) == LeaveBalance.id,
        ),
    )
