"""Repository for EMAFilterConfig persistence."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.ema_filter_config import EMAFilterConfig
from src.database.repositories.base_repository import BaseRepository


class EMAFilterConfigRepository(BaseRepository[EMAFilterConfig]):
    """Repository for managing EMA filter configuration persistence.

    Provides CRUD operations for EMA filter configurations, with special
    focus on strategy-based configuration retrieval and upsert operations.

    Methods:
        get_by_strategy: Get configuration for a specific strategy.
        create_or_update: Create new config or update existing one.
        update_config: Update specific configuration fields.
    """

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: Async database session.
        """
        super().__init__(session, EMAFilterConfig)

    def get_by_strategy(self, strategy_id: UUID) -> EMAFilterConfig | None:
        """Get EMA filter configuration for a specific strategy.

        Args:
            strategy_id: UUID of the strategy.

        Returns:
            EMAFilterConfig instance if found, None otherwise.

        Raises:
            Exception: If database operation fails.

        Example:
            config = repo.get_by_strategy(strategy_id)
            if config:
                print(f"Period: {config.period}")
        """
        try:
            result = self.session.execute(
                select(EMAFilterConfig).where(EMAFilterConfig.strategy_id == strategy_id)
            )
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except Exception as e:
            raise Exception(
                f"Error fetching EMA filter config for strategy {strategy_id}: {e}"
            ) from e

    def create_or_update(
        self,
        strategy_id: UUID,
        enabled: bool | None = None,
        period: int | None = None,
        timeframe: str | None = None,
        allow_on_rising: bool | None = None,
        allow_on_falling: bool | None = None,
    ) -> EMAFilterConfig:
        """Create new EMA filter config or update existing one.

        If config exists for the strategy, updates only provided fields.
        If config doesn't exist, creates with defaults for unprovided fields.

        Args:
            strategy_id: UUID of the strategy.
            enabled: Whether the EMA filter is enabled. Optional.
            period: EMA period for calculation. Optional.
            timeframe: Candle timeframe for EMA calculation. Optional.
            allow_on_rising: Allow trades when EMA is rising. Optional.
            allow_on_falling: Allow trades when EMA is falling. Optional.

        Returns:
            Created or updated EMAFilterConfig instance.

        Raises:
            Exception: If database operation fails.

        Example:
            # Create with defaults
            config = repo.create_or_update(strategy_id)

            # Update only period
            config = repo.create_or_update(strategy_id, period=21)
        """
        try:
            existing = self.get_by_strategy(strategy_id)

            if existing:
                if enabled is not None:
                    existing.enabled = enabled
                if period is not None:
                    existing.period = period
                if timeframe is not None:
                    existing.timeframe = timeframe
                if allow_on_rising is not None:
                    existing.allow_on_rising = allow_on_rising
                if allow_on_falling is not None:
                    existing.allow_on_falling = allow_on_falling

                return super().update(existing)
            else:
                new_config = EMAFilterConfig(
                    strategy_id=strategy_id,
                    enabled=enabled if enabled is not None else True,
                    period=period or 13,
                    timeframe=timeframe or "1h",
                    allow_on_rising=allow_on_rising if allow_on_rising is not None else True,
                    allow_on_falling=allow_on_falling if allow_on_falling is not None else False,
                )
                return super().create(new_config)
        except Exception as e:
            self.session.rollback()
            raise Exception(
                f"Error creating/updating EMA filter config for strategy {strategy_id}: {e}"
            ) from e

    def update_config(
        self,
        strategy_id: UUID,
        **kwargs: bool | int | str,
    ) -> EMAFilterConfig:
        """Update specific configuration fields for a strategy.

        Args:
            strategy_id: UUID of the strategy.
            **kwargs: Field-value pairs to update.
                Valid fields: enabled, period, timeframe, allow_on_rising, allow_on_falling.

        Returns:
            Updated EMAFilterConfig instance.

        Raises:
            ValueError: If strategy has no configuration.
            Exception: If database operation fails.

        Example:
            config = repo.update_config(
                strategy_id,
                period=21,
                timeframe="4h"
            )
        """
        existing = self.get_by_strategy(strategy_id)
        if not existing:
            raise ValueError(f"No EMA filter config found for strategy {strategy_id}")

        try:
            for field, value in kwargs.items():
                if hasattr(existing, field):
                    setattr(existing, field, value)

            return super().update(existing)
        except Exception:
            self.session.rollback()
            raise
