
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company


class CompanyCalendarDay(Base):
    """Holiday or working-day override for a specific company date."""

    __tablename__ = "company_calendar_days"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "calendar_date",
            name="uq_company_calendar_company_date",
        ),
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_company_calendar_company_id_id",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_company_calendar_company",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "holiday_name IS NULL OR length(trim(holiday_name)) > 0",
            name="ck_company_calendar_holiday_name_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    calendar_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    is_working_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    holiday_name: Mapped[str | None] = mapped_column(
        String(150),
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
        primaryjoin=lambda: CompanyCalendarDay.company_id == Company.id,
    )
