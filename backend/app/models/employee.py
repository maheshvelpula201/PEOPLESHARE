
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
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
from app.models.department import Department
from app.models.user import User


class EmploymentStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class Employee(Base):
    """An employee profile belonging to one company."""

    __tablename__ = "employees"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_employees_company_id_id",
        ),
        UniqueConstraint(
            "company_id",
            "employee_number",
            name="uq_employees_company_employee_number",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_employees_company_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "department_id"],
            ["departments.company_id", "departments.id"],
            name="fk_employees_company_department",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "user_id"],
            ["users.company_id", "users.id"],
            name="fk_employees_company_user",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "length(trim(employee_number)) > 0",
            name="ck_employees_number_not_blank",
        ),
        CheckConstraint(
            "length(trim(first_name)) > 0",
            name="ck_employees_first_name_not_blank",
        ),
        CheckConstraint(
            "length(trim(last_name)) > 0",
            name="ck_employees_last_name_not_blank",
        ),
        CheckConstraint(
            "job_title IS NULL OR length(trim(job_title)) > 0",
            name="ck_employees_job_title_not_blank",
        ),
        Index(
            "uq_employees_company_user",
            "company_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index(
            "ix_employees_company_status",
            "company_id",
            "employment_status",
        ),
        Index(
            "ix_employees_company_department",
            "company_id",
            "department_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    user_id: Mapped[int | None] = mapped_column(nullable=True)

    department_id: Mapped[int] = mapped_column(nullable=False)

    employee_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    job_title: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    hire_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    employment_status: Mapped[EmploymentStatus] = mapped_column(
        SQLAlchemyEnum(
            EmploymentStatus,
            name="employment_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=EmploymentStatus.ACTIVE,
        server_default=EmploymentStatus.ACTIVE.value,
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
        primaryjoin=lambda: foreign(Employee.company_id) == Company.id,
    )

    department: Mapped["Department"] = relationship(
        primaryjoin=lambda: and_(
            Employee.company_id == Department.company_id,
            foreign(Employee.department_id) == Department.id,
        ),
    )

    user: Mapped["User | None"] = relationship(
        primaryjoin=lambda: and_(
            Employee.company_id == User.company_id,
            foreign(Employee.user_id) == User.id,
        ),
    )
