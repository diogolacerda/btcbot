"""create_ema_filter_configs_table

Revision ID: d3aed5818b8f
Revises: bae863d9d38d
Create Date: 2026-01-11 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3aed5818b8f"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "bae863d9d38d"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ema_filter_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("strategy_id", sa.Uuid(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("allow_on_rising", sa.Boolean(), nullable=False),
        sa.Column("allow_on_falling", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_id", name="uq_ema_filter_configs_strategy_id"),
    )
    op.create_index(
        op.f("ix_ema_filter_configs_strategy_id"),
        "ema_filter_configs",
        ["strategy_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_ema_filter_configs_strategy_id"), table_name="ema_filter_configs")
    op.drop_table("ema_filter_configs")
