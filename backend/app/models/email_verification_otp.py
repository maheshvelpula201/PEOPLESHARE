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
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OTPDeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class EmailVerificationOTP(Base):
    """Stores hashed email verification OTPs for company accounts."""

    __tablename__ = "email_verification_otps"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_email_verification_otps_company_id_id",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_email_verification_otps_company",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "user_id"],
            ["users.company_id", "users.id"],
            name="fk_email_verification_otps_company_user",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "length(otp_hash) = 64",
            name="ck_email_verification_otp_hash_length",
        ),
        CheckConstraint(
            "attempts_count >= 0 AND attempts_count <= 5",
            name="ck_email_verification_otp_attempts",
        ),
        CheckConstraint(
            "NOT (consumed_at IS NOT NULL AND invalidated_at IS NOT NULL)",
            name="ck_email_verification_otp_terminal_state",
        ),
        CheckConstraint(
            "(delivery_status = 'sent' AND delivered_at IS NOT NULL) "
            "OR (delivery_status != 'sent' AND delivered_at IS NULL)",
            name="ck_email_verification_otp_delivery_consistency",
        ),
        Index(
            "uq_email_verification_one_usable_per_user",
            "company_id",
            "user_id",
            unique=True,
            postgresql_where=text(
                "consumed_at IS NULL AND invalidated_at IS NULL"
            ),
        ),
        Index(
            "ix_email_verification_otps_user_created",
            "company_id",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_email_verification_otps_expiry",
            "expires_at",
        ),
        Index(
            "uq_email_verification_otps_hash",
            "otp_hash",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    user_id: Mapped[int] = mapped_column(nullable=False)

    otp_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    attempts_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    delivery_status: Mapped[OTPDeliveryStatus] = mapped_column(
        SQLAlchemyEnum(
            OTPDeliveryStatus,
            name="otp_delivery_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=OTPDeliveryStatus.PENDING,
        server_default=OTPDeliveryStatus.PENDING.value,
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

    invalidated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )