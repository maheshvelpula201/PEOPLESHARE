
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKeyConstraint,
    Index,
    UniqueConstraint,
    and_,
    func,
    text,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.db.base import Base
from app.models.company import Company
from app.models.employee import Employee
from app.models.team import Team


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TeamMembership(Base):
    """Connects an employee to a team within their company."""

    __tablename__ = "team_memberships"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_team_memberships_company_id_id",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_team_memberships_company_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "employee_id"],
            ["employees.company_id", "employees.id"],
            name="fk_team_memberships_company_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "team_id"],
            ["teams.company_id", "teams.id"],
            name="fk_team_memberships_company_team",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status != 'active' OR ended_at IS NULL",
            name="ck_team_memberships_active_not_ended",
        ),
        Index(
            "uq_team_memberships_active_employee_team",
            "company_id",
            "employee_id",
            "team_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index(
            "uq_team_memberships_one_active_primary_per_employee",
            "company_id",
            "employee_id",
            unique=True,
            postgresql_where=text(
                "status = 'active' AND is_primary = true"
            ),
        ),
        Index(
            "ix_team_memberships_company_team_status",
            "company_id",
            "team_id",
            "status",
        ),
        Index(
            "ix_team_memberships_company_employee_status",
            "company_id",
            "employee_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    employee_id: Mapped[int] = mapped_column(nullable=False)

    team_id: Mapped[int] = mapped_column(nullable=False)

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )

    status: Mapped[MembershipStatus] = mapped_column(
        SQLAlchemyEnum(
            MembershipStatus,
            name="membership_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=MembershipStatus.ACTIVE,
        server_default=MembershipStatus.ACTIVE.value,
        nullable=False,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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
        primaryjoin=lambda: (
            foreign(TeamMembership.company_id) == Company.id
        ),
    )

    employee: Mapped["Employee"] = relationship(
        primaryjoin=lambda: and_(
            TeamMembership.company_id == Employee.company_id,
            foreign(TeamMembership.employee_id) == Employee.id,
        ),
    )

    team: Mapped["Team"] = relationship(
        primaryjoin=lambda: and_(
            TeamMembership.company_id == Team.company_id,
            foreign(TeamMembership.team_id) == Team.id,
        ),
    )
