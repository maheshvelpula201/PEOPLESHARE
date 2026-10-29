
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
from app.models.user import User


class InvitationRole(str, Enum):
    COMPANY_ADMIN = "company_admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class Invitation(Base):
    """A company invitation with a hashed, single-use acceptance token."""

    __tablename__ = "invitations"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_invitations_company_id_id",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_invitations_company_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "invited_by_user_id"],
            ["users.company_id", "users.id"],
            name="fk_invitations_company_inviter",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "accepted_user_id"],
            ["users.company_id", "users.id"],
            name="fk_invitations_company_accepted_user",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "length(trim(normalized_email)) > 0 "
            "AND normalized_email = lower(trim(normalized_email))",
            name="ck_invitations_normalized_email_format",
        ),
        CheckConstraint(
            "length(trim(token_hash)) > 0",
            name="ck_invitations_token_hash_not_blank",
        ),
        CheckConstraint(
            "(status = 'accepted' AND accepted_at IS NOT NULL "
            "AND accepted_user_id IS NOT NULL) "
            "OR (status != 'accepted' AND accepted_at IS NULL "
            "AND accepted_user_id IS NULL)",
            name="ck_invitations_acceptance_consistency",
        ),
        CheckConstraint(
            "(status = 'revoked' AND revoked_at IS NOT NULL) "
            "OR (status != 'revoked' AND revoked_at IS NULL)",
            name="ck_invitations_revocation_consistency",
        ),
        Index(
            "uq_invitations_token_hash",
            "token_hash",
            unique=True,
        ),
        Index(
            "uq_invitations_one_pending_per_email",
            "company_id",
            "normalized_email",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        Index(
            "ix_invitations_company_status_expiry",
            "company_id",
            "status",
            "expires_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    normalized_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    role: Mapped[InvitationRole] = mapped_column(
        SQLAlchemyEnum(
            InvitationRole,
            name="invitation_role",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[InvitationStatus] = mapped_column(
        SQLAlchemyEnum(
            InvitationStatus,
            name="invitation_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=InvitationStatus.PENDING,
        server_default=InvitationStatus.PENDING.value,
        nullable=False,
    )

    invited_by_user_id: Mapped[int] = mapped_column(nullable=False)

    accepted_user_id: Mapped[int | None] = mapped_column(nullable=True)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(
        primaryjoin=lambda: foreign(Invitation.company_id) == Company.id,
    )

    invited_by: Mapped["User"] = relationship(
        primaryjoin=lambda: and_(
            Invitation.company_id == User.company_id,
            foreign(Invitation.invited_by_user_id) == User.id,
        ),
    )

    accepted_user: Mapped["User | None"] = relationship(
        primaryjoin=lambda: and_(
            Invitation.company_id == User.company_id,
            foreign(Invitation.accepted_user_id) == User.id,
        ),
    )
