"""merge trading and grid configs heads

Revision ID: 8e4fcd3c3a40
Revises: 66a6855ef0ed, f7262dec4389
Create Date: 2026-01-01 21:45:03.716342

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "8e4fcd3c3a40"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = ("66a6855ef0ed", "f7262dec4389")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
