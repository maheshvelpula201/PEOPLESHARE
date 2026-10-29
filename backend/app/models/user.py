
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, Enum):
    OWNER = "owner"
    COMPANY_ADMIN = "company_admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class AccountStatus(str, Enum):
    PENDING_ACTIVATION = "pending_activation"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class User(Base):
    """A login identity belonging to exactly one company."""

    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_users_company_id_id",
        ),
        UniqueConstraint(
            "company_id",
            "normalized_email",
            name="uq_users_company_normalized_email",
        ),
        Index(
            "ix_users_company_role_status",
            "company_id",
            "role",
            "account_status",
        ),
        Index(
            "uq_users_one_active_owner_per_company",
            "company_id",
            unique=True,
            postgresql_where=text(
                "role = 'owner' AND account_status = 'active'"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
    )

    normalized_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
    )

    account_status: Mapped[AccountStatus] = mapped_column(
        SQLAlchemyEnum(
            AccountStatus,
            name="account_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=AccountStatus.PENDING_ACTIVATION,
        server_default=AccountStatus.PENDING_ACTIVATION.value,
        nullable=False,
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
        back_populates="users",
    )
