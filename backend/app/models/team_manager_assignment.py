
from datetime import datetime
from enum import Enum

from sqlalchemy import (
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
from app.models.team import Team
from app.models.user import User


class AssignmentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TeamManagerAssignment(Base):
    """Assigns a company User to manage a team."""

    __tablename__ = "team_manager_assignments"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "id",
            name="uq_team_manager_assignments_company_id_id",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_team_manager_assignments_company_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "team_id"],
            ["teams.company_id", "teams.id"],
            name="fk_team_manager_assignments_company_team",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "manager_user_id"],
            ["users.company_id", "users.id"],
            name="fk_team_manager_assignments_company_manager",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status != 'active' OR ended_at IS NULL",
            name="ck_team_manager_assignments_active_not_ended",
        ),
        Index(
            "uq_team_manager_assignments_active_team_manager",
            "company_id",
            "team_id",
            "manager_user_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index(
            "ix_team_manager_assignments_company_team_status",
            "company_id",
            "team_id",
            "status",
        ),
        Index(
            "ix_team_manager_assignments_company_manager_status",
            "company_id",
            "manager_user_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(nullable=False)

    team_id: Mapped[int] = mapped_column(nullable=False)

    manager_user_id: Mapped[int] = mapped_column(nullable=False)

    status: Mapped[AssignmentStatus] = mapped_column(
        SQLAlchemyEnum(
            AssignmentStatus,
            name="assignment_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        default=AssignmentStatus.ACTIVE,
        server_default=AssignmentStatus.ACTIVE.value,
        nullable=False,
    )

    assigned_at: Mapped[datetime] = mapped_column(
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
            foreign(TeamManagerAssignment.company_id) == Company.id
        ),
    )

    team: Mapped["Team"] = relationship(
        primaryjoin=lambda: and_(
            TeamManagerAssignment.company_id == Team.company_id,
            foreign(TeamManagerAssignment.team_id) == Team.id,
        ),
    )

    manager: Mapped["User"] = relationship(
        primaryjoin=lambda: and_(
            TeamManagerAssignment.company_id == User.company_id,
            foreign(TeamManagerAssignment.manager_user_id) == User.id,
        ),
    )
