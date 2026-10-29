
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company


class LeaveAccrualMode(str, Enum):
    NONE = "none"
    ANNUAL_UPFRONT = "annual_upfront"
    MONTHLY = "monthly"


class LeavePolicy(Base):
    """A versioned leave policy belonging to one company."""

    __tablename__ = "leave_policies"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_leave_policy_company_id_id",
        ),
        UniqueConstraint(
            "company_id",
            "code",
            "version",
            name="uq_leave_policy_company_code_version",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_leave_policy_company",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "length(trim(code)) > 0",
            name="ck_leave_policy_code_not_blank",
        ),
        CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_leave_policy_name_not_blank",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_leave_policy_version_positive",
        ),
        CheckConstraint(
            "annual_entitlement_units IS NULL "
            "OR annual_entitlement_units >= 0",
            name="ck_leave_policy_entitlement_nonnegative",
        ),
        CheckConstraint(
            "NOT tracks_balance OR annual_entitlement_units IS NOT NULL",
            name="ck_leave_policy_balance_requires_entitlement",
        ),
        CheckConstraint(
            "carry_forward_limit_units >= 0",
            name="ck_leave_policy_carry_forward_nonnegative",
        ),
        CheckConstraint(
            "max_consecutive_days IS NULL OR max_consecutive_days >= 1",
            name="ck_leave_policy_max_consecutive_positive",
        ),
        CheckConstraint(
            "jsonb_typeof(approval_steps) = 'array'",
            name="ck_leave_policy_approval_steps_array",
        ),
        Index(
            "uq_leave_policy_current_version",
            "company_id",
            "code",
            unique=True,
            postgresql_where=text("is_current IS TRUE"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    is_paid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    tracks_balance: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    annual_entitlement_units: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    accrual_mode: Mapped[LeaveAccrualMode] = mapped_column(
        SQLAlchemyEnum(
            LeaveAccrualMode,
            name="leave_accrual_mode",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=LeaveAccrualMode.ANNUAL_UPFRONT,
        server_default=LeaveAccrualMode.ANNUAL_UPFRONT.value,
    )

    carry_forward_limit_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    allow_half_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    max_consecutive_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    approval_steps: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: ["manager", "hr"],
        server_default=text("""'["manager", "hr"]'::jsonb"""),
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
        primaryjoin=lambda: LeavePolicy.company_id == Company.id,
    )
