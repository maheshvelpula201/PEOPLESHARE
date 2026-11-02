
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ActivationTokenStatus(str, Enum):
    PENDING = "pending"
    CONSUMED = "consumed"
    REVOKED = "revoked"


class ActivationDeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class AdminActivationToken(Base):
    """Single-use activation token for an initial Company Admin."""

    __tablename__ = "admin_activation_tokens"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_admin_activation_tokens_company_id_id",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_admin_activation_tokens_company",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "user_id"],
            ["users.company_id", "users.id"],
            name="fk_admin_activation_tokens_company_user",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "length(trim(token_hash)) > 0",
            name="ck_admin_activation_token_hash_not_blank",
        ),
        CheckConstraint(
            "(status = 'consumed' AND consumed_at IS NOT NULL) "
            "OR (status != 'consumed' AND consumed_at IS NULL)",
            name="ck_admin_activation_consumption_consistency",
        ),
        CheckConstraint(
            "(delivery_status = 'sent' AND delivered_at IS NOT NULL) "
            "OR (delivery_status != 'sent' AND delivered_at IS NULL)",
            name="ck_admin_activation_delivery_consistency",
        ),
        Index(
            "uq_admin_activation_tokens_token_hash",
            "token_hash",
            unique=True,
        ),
        Index(
            "uq_admin_activation_one_pending_per_user",
            "company_id",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        Index(
            "ix_admin_activation_tokens_expiry",
            "expires_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    user_id: Mapped[int] = mapped_column(nullable=False)

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    status: Mapped[ActivationTokenStatus] = mapped_column(
        SQLAlchemyEnum(
            ActivationTokenStatus,
            name="admin_activation_token_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=ActivationTokenStatus.PENDING,
        server_default=ActivationTokenStatus.PENDING.value,
        nullable=False,
    )

    delivery_status: Mapped[ActivationDeliveryStatus] = mapped_column(
        SQLAlchemyEnum(
            ActivationDeliveryStatus,
            name="admin_activation_delivery_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=ActivationDeliveryStatus.PENDING,
        server_default=ActivationDeliveryStatus.PENDING.value,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
