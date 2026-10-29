
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLAlchemyEnum,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlatformOperatorStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class PlatformOperator(Base):
    """A platform-level operator identity from a trusted identity provider."""

    __tablename__ = "platform_operators"

    __table_args__ = (
        UniqueConstraint(
            "external_subject",
            name="uq_platform_operators_external_subject",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    external_subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[PlatformOperatorStatus] = mapped_column(
        SQLAlchemyEnum(
            PlatformOperatorStatus,
            name="platform_operator_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=PlatformOperatorStatus.ACTIVE,
        server_default=PlatformOperatorStatus.ACTIVE.value,
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
