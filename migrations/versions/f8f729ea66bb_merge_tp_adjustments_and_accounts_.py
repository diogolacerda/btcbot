"""merge tp_adjustments and accounts branches

Revision ID: f8f729ea66bb
Revises: 788c951939a4
Create Date: 2025-12-30 14:38:03.689072

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "f8f729ea66bb"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "788c951939a4"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
