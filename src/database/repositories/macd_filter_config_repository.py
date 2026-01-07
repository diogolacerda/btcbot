"""Repository for MACDFilterConfig persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.macd_filter_config import MACDFilterConfig
from src.database.repositories.base_repository import BaseRepository

if TYPE_CHECKING:
    pass


class MACDFilterConfigRepository(BaseRepository[MACDFilterConfig]):
    """Repository for managing MACD filter configuration persistence.

    Provides CRUD operations for MACD filter configurations, with special
    focus on strategy-based configuration retrieval and upsert operations.

    Methods:
        get_by_strategy: Get configuration for a specific strategy.
        create_or_update: Create new config or update existing one.
        update_config: Update specific configuration fields.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async database session.
        """
        super().__init__(session, MACDFilterConfig)

    async def get_by_strategy(self, strategy_id: UUID) -> MACDFilterConfig | None:
        """Get MACD filter configuration for a specific strategy.

        Args:
            strategy_id: UUID of the strategy.

        Returns:
            MACDFilterConfig instance if found, None otherwise.

        Raises:
            Exception: If database operation fails.

        Example:
            config = await repo.get_by_strategy(strategy_id)
            if config:
                print(f"Fast period: {config.fast_period}")
        """
        try:
            result = await self.session.execute(
                select(MACDFilterConfig).where(MACDFilterConfig.strategy_id == strategy_id)
            )
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except Exception as e:
            raise Exception(
                f"Error fetching MACD filter config for strategy {strategy_id}: {e}"
            ) from e

    async def create_or_update(
        self,
        strategy_id: UUID,
        enabled: bool | None = None,
        fast_period: int | None = None,
        slow_period: int | None = None,
        signal_period: int | None = None,
        timeframe: str | None = None,
    ) -> MACDFilterConfig:
        """Create new MACD filter config or update existing one.

        If config exists for the strategy, updates only provided fields.
        If config doesn't exist, creates with defaults for unprovided fields.

        Args:
            strategy_id: UUID of the strategy.
            enabled: Whether the MACD filter is enabled. Optional.
            fast_period: Fast EMA period for MACD calculation. Optional.
            slow_period: Slow EMA period for MACD calculation. Optional.
            signal_period: Signal line EMA period. Optional.
            timeframe: Candle timeframe for MACD calculation. Optional.

        Returns:
            Created or updated MACDFilterConfig instance.

        Raises:
            Exception: If database operation fails.

        Example:
            # Create with defaults
            config = await repo.create_or_update(strategy_id)

            # Update only fast_period
            config = await repo.create_or_update(strategy_id, fast_period=15)
        """
        try:
            existing = await self.get_by_strategy(strategy_id)

            if existing:
                if enabled is not None:
                    existing.enabled = enabled
                if fast_period is not None:
                    existing.fast_period = fast_period
                if slow_period is not None:
                    existing.slow_period = slow_period
                if signal_period is not None:
                    existing.signal_period = signal_period
                if timeframe is not None:
                    existing.timeframe = timeframe

                return await super().update(existing)
            else:
                new_config = MACDFilterConfig(
                    strategy_id=strategy_id,
                    enabled=enabled if enabled is not None else True,
                    fast_period=fast_period or 12,
                    slow_period=slow_period or 26,
                    signal_period=signal_period or 9,
                    timeframe=timeframe or "1h",
                )
                return await super().create(new_config)
        except Exception as e:
            await self.session.rollback()
            raise Exception(
                f"Error creating/updating MACD filter config for strategy {strategy_id}: {e}"
            ) from e

    async def update_config(
        self,
        strategy_id: UUID,
        **kwargs: bool | int | str,
    ) -> MACDFilterConfig:
        """Update specific configuration fields for a strategy.

        Args:
            strategy_id: UUID of the strategy.
            **kwargs: Field-value pairs to update.
                Valid fields: enabled, fast_period, slow_period, signal_period, timeframe.

        Returns:
            Updated MACDFilterConfig instance.

        Raises:
            ValueError: If strategy has no configuration.
            Exception: If database operation fails.

        Example:
            config = await repo.update_config(
                strategy_id,
                fast_period=15,
                timeframe="4h"
            )
        """
        try:
            existing = await self.get_by_strategy(strategy_id)
            if not existing:
                raise ValueError(f"No MACD filter config found for strategy {strategy_id}")

            for field, value in kwargs.items():
                if hasattr(existing, field):
                    setattr(existing, field, value)

            return await super().update(existing)
        except Exception as e:
            await self.session.rollback()
            raise Exception(
                f"Error updating MACD filter config for strategy {strategy_id}: {e}"
            ) from e
