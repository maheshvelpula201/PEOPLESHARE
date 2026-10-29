
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DepartmentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Department(Base):
    """A department belonging to one company."""

    __tablename__ = "departments"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_departments_company_id_id",
        ),
        UniqueConstraint(
            "company_id",
            "normalized_name",
            name="uq_departments_company_normalized_name",
        ),
        UniqueConstraint(
            "company_id",
            "code",
            name="uq_departments_company_code",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_departments_company_id",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_departments_name_not_blank",
        ),
        
        CheckConstraint(
        "length(trim(normalized_name)) > 0 "
        "AND normalized_name = lower(trim(normalized_name))",
        name="ck_departments_normalized_name_format",
        )
,
        CheckConstraint(
            "code IS NULL OR length(trim(code)) > 0",
            name="ck_departments_code_not_blank",
        ),
        Index(
            "ix_departments_company_status",
            "company_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[DepartmentStatus] = mapped_column(
        SQLAlchemyEnum(
            DepartmentStatus,
            name="department_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=DepartmentStatus.ACTIVE,
        server_default=DepartmentStatus.ACTIVE.value,
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

    company: Mapped["Company"] = relationship()
