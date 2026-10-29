
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
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
    text,
    column,
    literal_column,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint, JSONB
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company
from app.models.employee import Employee
from app.models.leave_balance import LeaveBalance
from app.models.leave_policy import LeavePolicy


class LeaveRequestStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    WITHDRAWN = "withdrawn"


class HalfDayPeriod(str, Enum):
    AM = "am"
    PM = "pm"


class LeaveRequest(Base):
    """An employee's submitted leave request and approval state."""

    __tablename__ = "leave_requests"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_leave_request_company_id_id",
        ),
        
        ExcludeConstraint(
            (column("company_id"), "="),
            (column("employee_id"), "="),
            (
                func.daterange(
                    column("start_date"),
                    column("end_date"),
                    literal_column("'[]'"),
                ),
                "&&",
            ),
            where=text(
                "status IN ('pending_approval', 'approved')"
            ),
            using="gist",
            name="excl_leave_request_active_employee_dates",
        ),

        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_leave_request_company",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "employee_id"],
            ["employees.company_id", "employees.id"],
            name="fk_leave_request_company_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "policy_id"],
            ["leave_policies.company_id", "leave_policies.id"],
            name="fk_leave_request_company_policy",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "employee_id", "policy_id", "balance_id"],
            [
                "leave_balances.company_id",
                "leave_balances.employee_id",
                "leave_balances.policy_id",
                "leave_balances.id",
            ],
            name="fk_leave_request_matching_balance",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="ck_leave_request_date_range",
        ),
        CheckConstraint(
            "requested_units >= 1",
            name="ck_leave_request_units_positive",
        ),
        CheckConstraint(
            "policy_version >= 1",
            name="ck_leave_request_policy_version_positive",
        ),
        
        CheckConstraint(
            "current_approval_step >= 0",
            name="ck_leave_request_current_step_nonnegative",
        ),
        CheckConstraint(
            "jsonb_typeof(policy_snapshot) = 'object'",
            name="ck_leave_request_policy_snapshot_object",
        ),
        CheckConstraint(
            "jsonb_typeof(approval_route_snapshot) = 'array'",
            name="ck_leave_request_approval_route_array",
        ),

        CheckConstraint(
            "(requested_units = 1 AND start_date = end_date "
            "AND half_day_period IS NOT NULL) OR "
            "(requested_units >= 2 AND half_day_period IS NULL)",
            name="ck_leave_request_half_day_consistent",
        ),
        CheckConstraint(
            "status NOT IN ('approved', 'rejected') "
            "OR decided_at IS NOT NULL",
            name="ck_leave_request_decision_timestamp",
        ),
        CheckConstraint(
            "length(trim(idempotency_key)) > 0",
            name="ck_leave_request_idempotency_not_blank",
        ),
        Index(
            "ix_leave_request_company_employee_status",
            "company_id",
            "employee_id",
            "status",
        ),
        Index(
            "ix_leave_request_company_dates",
            "company_id",
            "start_date",
            "end_date",
        ),
        Index(
            "ix_leave_request_company_balance",
            "company_id",
            "balance_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    employee_id: Mapped[int] = mapped_column(nullable=False)

    policy_id: Mapped[int] = mapped_column(nullable=False)

    # Optional for policies that do not track a leave balance.
    balance_id: Mapped[int | None] = mapped_column(nullable=True)

    policy_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Snapshot of the policy rules applied when this request was submitted.
    policy_snapshot: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    # Snapshot of the approval route applicable to this request.
    approval_route_snapshot: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    current_approval_step: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    requested_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    half_day_period: Mapped[HalfDayPeriod | None] = mapped_column(
        SQLAlchemyEnum(
            HalfDayPeriod,
            name="half_day_period",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=True,
    )

    status: Mapped[LeaveRequestStatus] = mapped_column(
        SQLAlchemyEnum(
            LeaveRequestStatus,
            name="leave_request_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=LeaveRequestStatus.PENDING_APPROVAL,
        server_default=LeaveRequestStatus.PENDING_APPROVAL.value,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
        primaryjoin=lambda: LeaveRequest.company_id == Company.id,
    )

    employee: Mapped["Employee"] = relationship(
        primaryjoin=lambda: and_(
            LeaveRequest.company_id == Employee.company_id,
            foreign(LeaveRequest.employee_id) == Employee.id,
        ),
    )

    policy: Mapped["LeavePolicy"] = relationship(
        primaryjoin=lambda: and_(
            LeaveRequest.company_id == LeavePolicy.company_id,
            foreign(LeaveRequest.policy_id) == LeavePolicy.id,
        ),
    )

    balance: Mapped["LeaveBalance | None"] = relationship(
        primaryjoin=lambda: and_(
            LeaveRequest.company_id == LeaveBalance.company_id,
            foreign(LeaveRequest.balance_id) == LeaveBalance.id,
        ),
    )
