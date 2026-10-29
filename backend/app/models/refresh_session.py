
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    and_,
    func,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company
from app.models.user import User


class RefreshSession(Base):
    """Stores refresh-token hashes and session revocation state."""

    __tablename__ = "refresh_sessions"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_refresh_sessions_company_id_id",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_refresh_sessions_company_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "user_id"],
            ["users.company_id", "users.id"],
            name="fk_refresh_sessions_company_user",
            ondelete="RESTRICT",
        ),
        Index(
            "uq_refresh_sessions_token_hash",
            "token_hash",
            unique=True,
        ),
        Index(
            "ix_refresh_sessions_company_user",
            "company_id",
            "user_id",
        ),
        Index(
            "ix_refresh_sessions_expiry",
            "expires_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    user_id: Mapped[int] = mapped_column(nullable=False)

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
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

    company: Mapped["Company"] = relationship(
        primaryjoin=lambda: foreign(RefreshSession.company_id) == Company.id,
    )

    user: Mapped["User"] = relationship(
        primaryjoin=lambda: and_(
            RefreshSession.company_id == User.company_id,
            foreign(RefreshSession.user_id) == User.id,
        ),
    )
