
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    and_,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company
from app.models.platform_operator import PlatformOperator
from app.models.user import User


class AuditEvent(Base):
    """Records security and business events without storing secrets."""

    __tablename__ = "audit_events"

    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_audit_events_company_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "actor_user_id"],
            ["users.company_id", "users.id"],
            name="fk_audit_events_company_actor",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["platform_operator_id"],
            ["platform_operators.id"],
            name="fk_audit_events_platform_operator",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "(actor_user_id IS NOT NULL AND platform_operator_id IS NULL "
            "AND company_id IS NOT NULL) "
            "OR (actor_user_id IS NULL AND platform_operator_id IS NOT NULL)",
            name="ck_audit_events_exactly_one_actor",
        ),
        CheckConstraint(
            "length(trim(action)) > 0",
            name="ck_audit_events_action_not_blank",
        ),
        CheckConstraint(
            "length(trim(target_type)) > 0",
            name="ck_audit_events_target_type_not_blank",
        ),
        Index(
            "ix_audit_events_company_created",
            "company_id",
            "created_at",
        ),
        Index(
            "ix_audit_events_company_action_created",
            "company_id",
            "action",
            "created_at",
        ),
        Index(
            "ix_audit_events_target",
            "target_type",
            "target_id",
        ),
        Index(
            "ix_audit_events_request_id",
            "request_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int | None] = mapped_column(
        #ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=True,
    )

    actor_user_id: Mapped[int | None] = mapped_column(nullable=True)

    platform_operator_id: Mapped[int | None] = mapped_column(nullable=True)

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    target_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    target_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    outcome: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    event_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )

    request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["Company | None"] = relationship(
        primaryjoin=lambda: foreign(AuditEvent.company_id) == Company.id,
    )

    actor_user: Mapped["User | None"] = relationship(
        primaryjoin=lambda: and_(
            AuditEvent.company_id == User.company_id,
            foreign(AuditEvent.actor_user_id) == User.id,
        ),
    )

    platform_operator: Mapped["PlatformOperator | None"] = relationship()
