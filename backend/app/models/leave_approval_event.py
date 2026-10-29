
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
    text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company
from app.models.leave_request import LeaveRequest
from app.models.user import User


class LeaveApprovalEventType(str, Enum):
    SUBMITTED = "submitted"
    STEP_ASSIGNED = "step_assigned"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    REASSIGNED = "reassigned"
    REVISION_REQUESTED = "revision_requested"
    CANCELLED = "cancelled"
    WITHDRAWN = "withdrawn"


class LeaveApprovalEvent(Base):
    """Append-only history of leave request approval workflow events."""

    __tablename__ = "leave_approval_events"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_leave_approval_event_company_id_id",
        ),
        UniqueConstraint(
            "company_id",
            "idempotency_key",
            name="uq_leave_approval_event_idempotency",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_leave_approval_event_company",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "request_id"],
            ["leave_requests.company_id", "leave_requests.id"],
            name="fk_leave_approval_event_request",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "actor_user_id"],
            ["users.company_id", "users.id"],
            name="fk_leave_approval_event_actor",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "assigned_approver_user_id"],
            ["users.company_id", "users.id"],
            name="fk_leave_approval_event_approver",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "step_number >= 0",
            name="ck_leave_approval_event_step_nonnegative",
        ),
        
        CheckConstraint(
            "jsonb_typeof(event_data) = 'object'",
            name="ck_leave_approval_event_event_data_object",
        ),

        CheckConstraint(
            "length(trim(idempotency_key)) > 0",
            name="ck_leave_approval_event_idempotency_not_blank",
        ),
        CheckConstraint(
            "comment IS NULL OR length(trim(comment)) > 0",
            name="ck_leave_approval_event_comment_not_blank",
        ),
        Index(
            "ix_leave_approval_event_request_created",
            "company_id",
            "request_id",
            "created_at",
        ),
        Index(
            "ix_leave_approval_event_approver_created",
            "company_id",
            "assigned_approver_user_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    request_id: Mapped[int] = mapped_column(nullable=False)

    step_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    event_type: Mapped[LeaveApprovalEventType] = mapped_column(
        SQLAlchemyEnum(
            LeaveApprovalEventType,
            name="leave_approval_event_type",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
    )

    actor_user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    assigned_approver_user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    event_data: Mapped[dict] = mapped_column(
    JSONB,
    nullable=False,
    default=dict,
    server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    company: Mapped["Company"] = relationship(
        primaryjoin=lambda: LeaveApprovalEvent.company_id == Company.id,
    )

    leave_request: Mapped["LeaveRequest"] = relationship(
        primaryjoin=lambda: and_(
            LeaveApprovalEvent.company_id == LeaveRequest.company_id,
            foreign(LeaveApprovalEvent.request_id) == LeaveRequest.id,
        ),
    )

    actor: Mapped["User | None"] = relationship(
        primaryjoin=lambda: and_(
            LeaveApprovalEvent.company_id == User.company_id,
            foreign(LeaveApprovalEvent.actor_user_id) == User.id,
        ),
        foreign_keys=lambda: [LeaveApprovalEvent.actor_user_id],
    )

    assigned_approver: Mapped["User | None"] = relationship(
        primaryjoin=lambda: and_(
            LeaveApprovalEvent.company_id == User.company_id,
            foreign(LeaveApprovalEvent.assigned_approver_user_id) == User.id,
        ),
        foreign_keys=lambda: [LeaveApprovalEvent.assigned_approver_user_id],
    )
