
from datetime import datetime
from enum import Enum
from sqlalchemy import and_
from sqlalchemy.orm import foreign
from app.models.department import Department

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TeamStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Team(Base):
    """A team belonging to one company and optionally one department."""

    __tablename__ = "teams"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_teams_company_id_id",
        ),
        UniqueConstraint(
            "company_id",
            "normalized_name",
            name="uq_teams_company_normalized_name",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_teams_company_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "department_id"],
            ["departments.company_id", "departments.id"],
            name="fk_teams_company_department",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_teams_name_not_blank",
        ),
        CheckConstraint(
            "length(trim(normalized_name)) > 0 "
            "AND normalized_name = lower(trim(normalized_name))",
            name="ck_teams_normalized_name_format",
        ),
        Index(
            "ix_teams_company_status",
            "company_id",
            "status",
        ),
        Index(
            "ix_teams_company_department",
            "company_id",
            "department_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    department_id: Mapped[int | None] = mapped_column(nullable=True)

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    status: Mapped[TeamStatus] = mapped_column(
        SQLAlchemyEnum(
            TeamStatus,
            name="team_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=TeamStatus.ACTIVE,
        server_default=TeamStatus.ACTIVE.value,
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

    department: Mapped["Department | None"] = relationship(
    primaryjoin=lambda: and_(
        Team.company_id == Department.company_id,
        foreign(Team.department_id) == Department.id,
    )
)