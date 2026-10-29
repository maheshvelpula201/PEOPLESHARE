
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    UniqueConstraint,
    and_,
    func,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company
from app.models.employee import Employee
from app.models.leave_policy import LeavePolicy


class LeaveBalance(Base):
    """An employee's leave balance for one policy and leave period.

    All unit values use half-day units:
    2 units = one full day.
    """

    __tablename__ = "leave_balances"

    __table_args__ = (
        UniqueConstraint(
        "company_id",
        "employee_id",
        "policy_id",
        "period_start",
        name="uq_leave_balance_employee_policy_period",
        ),
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_leave_balance_company_id_id",
        ),
        UniqueConstraint(
            "company_id",
            "employee_id",
            "policy_id",
            "id",
            name="uq_leave_balance_company_employee_policy_id",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_leave_balance_company",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "employee_id"],
            ["employees.company_id", "employees.id"],
            name="fk_leave_balance_company_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "policy_id"],
            ["leave_policies.company_id", "leave_policies.id"],
            name="fk_leave_balance_company_policy",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="ck_leave_balance_period_valid",
        ),
        CheckConstraint(
            "entitled_units >= 0",
            name="ck_leave_balance_entitled_nonnegative",
        ),
        CheckConstraint(
            "carry_forward_units >= 0",
            name="ck_leave_balance_carry_forward_nonnegative",
        ),
        CheckConstraint(
            "reserved_units >= 0",
            name="ck_leave_balance_reserved_nonnegative",
        ),
        CheckConstraint(
            "consumed_units >= 0",
            name="ck_leave_balance_consumed_nonnegative",
        ),
        CheckConstraint(
            "entitled_units + carry_forward_units + adjustment_units "
            ">= reserved_units + consumed_units",
            name="ck_leave_balance_available_nonnegative",
        ),
        Index(
            "ix_leave_balance_company_employee",
            "company_id",
            "employee_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    employee_id: Mapped[int] = mapped_column(nullable=False)

    policy_id: Mapped[int] = mapped_column(nullable=False)

    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    entitled_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    carry_forward_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    adjustment_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    reserved_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    consumed_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    company: Mapped["Company"] = relationship(
        primaryjoin=lambda: LeaveBalance.company_id == Company.id,
    )

    employee: Mapped["Employee"] = relationship(
        primaryjoin=lambda: and_(
            LeaveBalance.company_id == Employee.company_id,
            foreign(LeaveBalance.employee_id) == Employee.id,
        ),
    )

    policy: Mapped["LeavePolicy"] = relationship(
        primaryjoin=lambda: and_(
            LeaveBalance.company_id == LeavePolicy.company_id,
            foreign(LeaveBalance.policy_id) == LeavePolicy.id,
        ),
    )

    @property
    def available_units(self) -> int:
        """Calculate available units from the stored balance components."""
        return (
            self.entitled_units
            + self.carry_forward_units
            + self.adjustment_units
            - self.reserved_units
            - self.consumed_units
        )
