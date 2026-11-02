
"""add user account origin

Revision ID: be9e9c293381
Revises: bfec4744b0ab
Create Date: 2026-11-02 23:54:13.551576
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "be9e9c293381"
down_revision: Union[str, None] = "bfec4744b0ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


account_origin_enum = sa.Enum(
    "registration",
    "invitation",
    "owner_provisioning",
    name="account_origin",
)


def upgrade() -> None:
    account_origin_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "account_origin",
            account_origin_enum,
            server_default="invitation",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "account_origin")

    account_origin_enum.drop(op.get_bind(), checkfirst=True)
