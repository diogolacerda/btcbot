"""create_activity_events_table

Revision ID: 34ade06a4bbd
Revises: f37c2c48dcb0
Create Date: 2026-01-05 17:54:40.365264

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "34ade06a4bbd"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "f37c2c48dcb0"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "activity_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("event_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create indexes for efficient queries
    op.create_index(
        "idx_activity_events_account_id",
        "activity_events",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "idx_activity_events_account_timestamp",
        "activity_events",
        ["account_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        "idx_activity_events_account_timestamp_desc",
        "activity_events",
        ["account_id", sa.text("timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "idx_activity_events_event_type",
        "activity_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "idx_activity_events_account_type",
        "activity_events",
        ["account_id", "event_type"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_activity_events_account_type", table_name="activity_events")
    op.drop_index("idx_activity_events_event_type", table_name="activity_events")
    op.drop_index("idx_activity_events_account_timestamp_desc", table_name="activity_events")
    op.drop_index("idx_activity_events_account_timestamp", table_name="activity_events")
    op.drop_index("idx_activity_events_account_id", table_name="activity_events")
    op.drop_table("activity_events")
