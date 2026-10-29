
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompanyStatus(str, Enum):
    SETUP_PENDING = "setup_pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class Company(Base):
    """A company is the tenant boundary for PeopleSphere."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    timezone_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="UTC",
        server_default="UTC",
    )

    status: Mapped[CompanyStatus] = mapped_column(
        SQLAlchemyEnum(
            CompanyStatus,
            name="company_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=CompanyStatus.SETUP_PENDING,
        server_default=CompanyStatus.SETUP_PENDING.value,
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

    users: Mapped[list["User"]] = relationship(
        back_populates="company",
        passive_deletes="all",
    )
