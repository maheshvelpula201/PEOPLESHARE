
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
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company
from app.models.employee import Employee


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    HALF_DAY = "half_day"
    ABSENT = "absent"


class AttendanceRecord(Base):
    """One canonical attendance record per employee per company date."""

    __tablename__ = "attendance_records"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_attendance_company_id_id",
        ),
        UniqueConstraint(
            "company_id",
            "employee_id",
            "work_date",
            name="uq_attendance_employee_work_date",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_attendance_company",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "employee_id"],
            ["employees.company_id", "employees.id"],
            name="fk_attendance_company_employee",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "check_out_at IS NULL OR check_in_at IS NOT NULL",
            name="ck_attendance_checkout_requires_checkin",
        ),
        CheckConstraint(
            "check_out_at IS NULL OR check_out_at >= check_in_at",
            name="ck_attendance_checkout_after_checkin",
        ),
        CheckConstraint(
            "length(trim(source)) > 0",
            name="ck_attendance_source_not_blank",
        ),
        CheckConstraint(
            "correction_reason IS NULL OR length(trim(correction_reason)) > 0",
            name="ck_attendance_correction_reason_not_blank",
        ),
        CheckConstraint(
            "status <> 'absent' OR "
            "(check_in_at IS NULL AND check_out_at IS NULL)",
            name="ck_attendance_absent_without_timestamps",
        ),
        Index(
            "ix_attendance_company_date",
            "company_id",
            "work_date",
        ),
        Index(
            "ix_attendance_company_employee_date",
            "company_id",
            "employee_id",
            "work_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    employee_id: Mapped[int] = mapped_column(nullable=False)

    work_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[AttendanceStatus] = mapped_column(
        SQLAlchemyEnum(
            AttendanceStatus,
            name="attendance_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=AttendanceStatus.PRESENT,
        server_default=AttendanceStatus.PRESENT.value,
    )

    check_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    check_out_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="manual",
        server_default="manual",
    )

    correction_reason: Mapped[str | None] = mapped_column(
        String(500),
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
        primaryjoin=lambda: AttendanceRecord.company_id == Company.id,
    )

    employee: Mapped["Employee"] = relationship(
        primaryjoin=lambda: and_(
            AttendanceRecord.company_id == Employee.company_id,
            foreign(AttendanceRecord.employee_id) == Employee.id,
        ),
    )
