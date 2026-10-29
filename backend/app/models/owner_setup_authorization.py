
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
    and_,
    func,
    text,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company
from app.models.platform_operator import PlatformOperator
from app.models.user import User


class OwnerSetupPurpose(str, Enum):
    INITIAL_OWNER = "initial_owner"
    RECOVERY_OWNER = "recovery_owner"


class OwnerSetupStatus(str, Enum):
    ISSUED = "issued"
    CONSUMED = "consumed"
    REVOKED = "revoked"
    EXPIRED = "expired"


class OwnerSetupAuthorization(Base):
    """A time-limited authorization for initial ownership or recovery."""

    __tablename__ = "owner_setup_authorizations"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_owner_setup_authorizations_company_id_id",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_owner_setup_authorizations_company_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["issued_by_operator_id"],
            ["platform_operators.id"],
            name="fk_owner_setup_authorizations_issuer",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "consumed_by_user_id"],
            ["users.company_id", "users.id"],
            name="fk_owner_setup_authorizations_consumed_user",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "length(trim(intended_owner_email)) > 0 "
            "AND intended_owner_email = lower(trim(intended_owner_email))",
            name="ck_owner_setup_intended_email_format",
        ),
        CheckConstraint(
            "length(trim(token_hash)) > 0",
            name="ck_owner_setup_token_hash_not_blank",
        ),
        CheckConstraint(
            "(status = 'consumed' AND consumed_at IS NOT NULL "
            "AND consumed_by_user_id IS NOT NULL) "
            "OR (status != 'consumed' AND consumed_at IS NULL "
            "AND consumed_by_user_id IS NULL)",
            name="ck_owner_setup_consumption_consistency",
        ),
        Index(
            "uq_owner_setup_authorizations_token_hash",
            "token_hash",
            unique=True,
        ),
        Index(
            "uq_owner_setup_one_issued_per_company",
            "company_id",
            unique=True,
            postgresql_where=text("status = 'issued'"),
        ),
        Index(
            "ix_owner_setup_company_status_expiry",
            "company_id",
            "status",
            "expires_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    intended_owner_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    issued_by_operator_id: Mapped[int] = mapped_column(nullable=False)

    consumed_by_user_id: Mapped[int | None] = mapped_column(nullable=True)

    purpose: Mapped[OwnerSetupPurpose] = mapped_column(
        SQLAlchemyEnum(
            OwnerSetupPurpose,
            name="owner_setup_purpose",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
    )

    status: Mapped[OwnerSetupStatus] = mapped_column(
        SQLAlchemyEnum(
            OwnerSetupStatus,
            name="owner_setup_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=OwnerSetupStatus.ISSUED,
        server_default=OwnerSetupStatus.ISSUED.value,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
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

    company: Mapped["Company"] = relationship()

    issued_by_operator: Mapped["PlatformOperator"] = relationship()

    consumed_by_user: Mapped["User | None"] = relationship(
        primaryjoin=lambda: and_(
            OwnerSetupAuthorization.company_id == User.company_id,
            foreign(OwnerSetupAuthorization.consumed_by_user_id) == User.id,
        ),
    )
