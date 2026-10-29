
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company


class CompanyWorkingWeekday(Base):
    """Recurring working-day configuration for a company.

    weekday: Monday = 0, Sunday = 6.
    """

    __tablename__ = "company_working_weekdays"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "weekday",
            name="uq_company_working_weekday",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_working_weekday_company",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "weekday >= 0 AND weekday <= 6",
            name="ck_working_weekday_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    weekday: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    is_working_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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
        primaryjoin=lambda: CompanyWorkingWeekday.company_id == Company.id,
    )
