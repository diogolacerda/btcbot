"""Repository for GridConfig model operations."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.grid_config import GridConfig
from src.database.repositories.base_repository import BaseRepository
from src.utils.logger import main_logger


class GridConfigRepository(BaseRepository[GridConfig]):
    """Repository for managing GridConfig persistence.

    Inherits from BaseRepository to leverage common CRUD operations
    while providing grid-config-specific methods.

    Provides methods to save and retrieve grid configuration for accounts.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        super().__init__(session, GridConfig)

    async def get_by_account(self, account_id: UUID) -> GridConfig | None:
        """Get grid config for an account.

        Args:
            account_id: Account UUID

        Returns:
            GridConfig if found, None otherwise
        """
        try:
            stmt = select(GridConfig).where(GridConfig.account_id == account_id)
            result = await self.session.execute(stmt)
            grid_config = result.scalar_one_or_none()
            return grid_config if isinstance(grid_config, GridConfig) else None
        except Exception as e:
            main_logger.error(f"Error fetching grid config for account {account_id}: {e}")
            raise

    async def get_or_create(self, account_id: UUID) -> GridConfig:
        """Get existing grid config or create with defaults.

        This ensures every account has a grid configuration. If none exists,
        creates one with default values.

        Args:
            account_id: Account UUID

        Returns:
            GridConfig instance (existing or newly created)
        """
        try:
            # Try to get existing config
            grid_config = await self.get_by_account(account_id)

            if grid_config:
                return grid_config

            # Create with defaults
            grid_config = GridConfig(
                account_id=account_id,
                spacing_type="fixed",
                spacing_value=Decimal("100.0"),
                range_percent=Decimal("5.0"),
                max_total_orders=10,
                anchor_mode="none",
                anchor_value=Decimal("100.0"),
            )

            # Use inherited create method
            return await super().create(grid_config)

        except Exception as e:
            main_logger.error(
                f"Error getting or creating grid config for account {account_id}: {e}"
            )
            raise

    async def save_config(
        self,
        account_id: UUID,
        *,
        spacing_type: str | None = None,
        spacing_value: Decimal | None = None,
        range_percent: Decimal | None = None,
        max_total_orders: int | None = None,
        anchor_mode: str | None = None,
        anchor_value: Decimal | None = None,
    ) -> GridConfig:
        """Save or update grid config for an account.

        Uses BaseRepository methods internally for database operations.

        Args:
            account_id: Account UUID
            spacing_type: Type of grid spacing ("fixed" or "percentage")
            spacing_value: Grid spacing value
            range_percent: Grid range as percentage
            max_total_orders: Maximum number of orders
            anchor_mode: Grid anchor mode
            anchor_value: Anchor value for grid alignment

        Returns:
            Saved GridConfig instance
        """
        try:
            # Get existing config or create with defaults
            grid_config = await self.get_or_create(account_id)

            # Update fields if provided
            if spacing_type is not None:
                grid_config.spacing_type = spacing_type
            if spacing_value is not None:
                grid_config.spacing_value = spacing_value
            if range_percent is not None:
                grid_config.range_percent = range_percent
            if max_total_orders is not None:
                grid_config.max_total_orders = max_total_orders
            if anchor_mode is not None:
                grid_config.anchor_mode = anchor_mode
            if anchor_value is not None:
                grid_config.anchor_value = anchor_value

            # Use inherited update method
            return await super().update(grid_config)

        except Exception as e:
            main_logger.error(f"Error saving grid config for account {account_id}: {e}")
            raise

    def to_dict(self, grid_config: GridConfig) -> dict[str, Any]:
        """Convert GridConfig to dictionary representation.

        Args:
            grid_config: GridConfig instance

        Returns:
            Dictionary with config data
        """
        return {
            "id": str(grid_config.id),
            "account_id": str(grid_config.account_id),
            "spacing_type": grid_config.spacing_type,
            "spacing_value": float(grid_config.spacing_value),
            "range_percent": float(grid_config.range_percent),
            "max_total_orders": grid_config.max_total_orders,
            "anchor_mode": grid_config.anchor_mode,
            "anchor_value": float(grid_config.anchor_value),
            "created_at": grid_config.created_at.isoformat(),
            "updated_at": grid_config.updated_at.isoformat(),
        }
