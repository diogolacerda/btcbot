"""GridConfig model for persisting grid configuration.

DEPRECATED: Use Strategy model instead. This model will be removed in a future release.

Migration Guide:
- Migrate to Strategy model using the unified configuration approach
- All grid parameters are now managed through the Strategy entity
- See src/database/models/strategy.py for the new configuration model
"""

import warnings
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.database.base import Base

if TYPE_CHECKING:
    from .account import Account


class GridConfig(Base):
    """GridConfig model for managing grid trading configuration.

    DEPRECATED: Use Strategy model instead. Will be removed in v2.0.

    Stores grid configuration parameters that control grid spacing, range,
    and order limits. Each account has a single grid configuration record.

    Migration Instructions:
    - Use Strategy model which unifies trading, grid, and filter configs
    - All grid fields map directly to Strategy model fields (spacing_type, spacing_value, etc.)
    - See src/database/models/strategy.py for replacement model

    Attributes:
        id: Unique grid config identifier (UUID).
        account_id: Foreign key to accounts table (one-to-one relationship).
        spacing_type: Type of grid spacing ("fixed" or "percentage").
        spacing_value: Grid spacing value (price for fixed, percentage for percentage).
        range_percent: Grid range as percentage from current price.
        max_total_orders: Maximum number of simultaneous limit orders.
        anchor_mode: Grid anchor mode ("none", "hundred", "thousand").
        anchor_value: Anchor value for grid alignment.
        created_at: Timestamp of record creation.
        updated_at: Timestamp of last update.
    """

    def __init__(self, *args: object, **kwargs: object):
        """Initialize GridConfig with deprecation warning."""
        warnings.warn(
            "GridConfig is deprecated. Use Strategy model instead. "
            "See src/database/models/strategy.py for migration guide.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    __tablename__ = "grid_configs"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to accounts (one-to-one)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One config per account
        index=True,
    )

    # Grid configuration
    spacing_type: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed")
    spacing_value: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("100.0")
    )
    range_percent: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False, default=Decimal("5.0")
    )
    max_total_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    anchor_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    anchor_value: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False, default=Decimal("100.0")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="grid_config")

    # Constraints (enforce one config per account at DB level)
    __table_args__ = (UniqueConstraint("account_id", name="uq_grid_config_account"),)

    def __repr__(self) -> str:
        """String representation of GridConfig."""
        return (
            f"<GridConfig(id={self.id}, account_id={self.account_id}, "
            f"spacing={self.spacing_type}:{self.spacing_value}, "
            f"max_orders={self.max_total_orders})>"
        )
