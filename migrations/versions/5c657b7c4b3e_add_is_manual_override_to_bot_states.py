"""add is_manual_override to bot_states

Revision ID: 5c657b7c4b3e
Revises: 67e90c16057f
Create Date: 2025-12-30 15:04:10.259412

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c657b7c4b3e"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "67e90c16057f"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add is_manual_override column to bot_state table.

    This column differentiates between manual (user-triggered) and automatic
    (MACD-triggered) state changes. Manual overrides are restored more aggressively
    on bot restart.
    """
    # Add column with default value False
    # SQLAlchemy will handle PostgreSQL (BOOLEAN) vs SQLite (INTEGER) automatically
    op.add_column(
        "bot_state",
        sa.Column("is_manual_override", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    """Remove is_manual_override column from bot_state table."""
    op.drop_column("bot_state", "is_manual_override")
