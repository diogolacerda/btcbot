"""Repository for TradingConfig persistence.

DEPRECATED: Use StrategyRepository instead. This repository will be removed in a future release.
"""

import warnings
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.trading_config import TradingConfig
from src.database.repositories.base_repository import BaseRepository


class TradingConfigRepository(BaseRepository[TradingConfig]):
    """Repository for managing trading configuration persistence.

    DEPRECATED: Use StrategyRepository instead. Will be removed in v2.0.

    Provides CRUD operations for trading configurations, with special
    focus on account-based configuration retrieval and upsert operations.

    Migration Instructions:
    - Use StrategyRepository for unified configuration management
    - All trading configuration methods are available in StrategyRepository
    - See src/database/repositories/strategy_repository.py (create if needed)

    Methods:
        get_by_account: Get configuration for a specific account.
        create_or_update: Create new config or update existing one.
        update_config: Update specific configuration fields.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async database session.
        """
        warnings.warn(
            "TradingConfigRepository is deprecated. Use StrategyRepository instead. "
            "See src/database/repositories/strategy_repository.py for migration guide.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(session, TradingConfig)

    async def get_by_account(self, account_id: UUID) -> TradingConfig | None:
        """Get trading configuration for a specific account.

        DEPRECATED: Use StrategyRepository.get_active_by_account instead.

        Args:
            account_id: UUID of the account.

        Returns:
            TradingConfig instance if found, None otherwise.

        Raises:
            Exception: If database operation fails.

        Example:
            config = await repo.get_by_account(account_id)
            if config:
                print(f"Leverage: {config.leverage}x")
        """
        try:
            result = await self.session.execute(
                select(TradingConfig).where(TradingConfig.account_id == account_id)
            )
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except Exception as e:
            raise Exception(f"Error fetching trading config for account {account_id}: {e}") from e

    async def create_or_update(
        self,
        account_id: UUID,
        symbol: str | None = None,
        leverage: int | None = None,
        order_size_usdt: Decimal | None = None,
        margin_mode: str | None = None,
        take_profit_percent: Decimal | None = None,
        tp_dynamic_enabled: bool | None = None,
        tp_base_percent: Decimal | None = None,
        tp_min_percent: Decimal | None = None,
        tp_max_percent: Decimal | None = None,
        tp_safety_margin: Decimal | None = None,
        tp_check_interval_min: int | None = None,
    ) -> TradingConfig:
        """Create new trading config or update existing one.

        DEPRECATED: Use StrategyRepository.create_or_update instead.

        If config exists for the account, updates only provided fields.
        If config doesn't exist, creates with defaults for unprovided fields.

        Args:
            account_id: UUID of the account.
            symbol: Trading pair (e.g., 'BTC-USDT'). Optional.
            leverage: Leverage multiplier. Optional.
            order_size_usdt: Order size in USDT. Optional.
            margin_mode: Margin mode ('CROSSED' or 'ISOLATED'). Optional.
            take_profit_percent: Take profit percentage. Optional.
            tp_dynamic_enabled: Enable dynamic TP. Optional.
            tp_base_percent: Base TP percentage. Optional.
            tp_min_percent: Minimum TP percentage. Optional.
            tp_max_percent: Maximum TP percentage. Optional.
            tp_safety_margin: Safety margin above funding cost. Optional.
            tp_check_interval_min: Check interval in minutes. Optional.

        Returns:
            Created or updated TradingConfig instance.

        Raises:
            Exception: If database operation fails.

        Example:
            # Create with defaults
            config = await repo.create_or_update(account_id)

            # Update only leverage
            config = await repo.create_or_update(account_id, leverage=20)
        """
        try:
            existing = await self.get_by_account(account_id)

            if existing:
                # Update existing config
                if symbol is not None:
                    existing.symbol = symbol
                if leverage is not None:
                    existing.leverage = leverage
                if order_size_usdt is not None:
                    existing.order_size_usdt = order_size_usdt
                if margin_mode is not None:
                    existing.margin_mode = margin_mode
                if take_profit_percent is not None:
                    existing.take_profit_percent = take_profit_percent
                if tp_dynamic_enabled is not None:
                    existing.tp_dynamic_enabled = tp_dynamic_enabled
                if tp_base_percent is not None:
                    existing.tp_base_percent = tp_base_percent
                if tp_min_percent is not None:
                    existing.tp_min_percent = tp_min_percent
                if tp_max_percent is not None:
                    existing.tp_max_percent = tp_max_percent
                if tp_safety_margin is not None:
                    existing.tp_safety_margin = tp_safety_margin
                if tp_check_interval_min is not None:
                    existing.tp_check_interval_min = tp_check_interval_min

                return await super().update(existing)
            else:
                # Create new config with defaults
                new_config = TradingConfig(
                    account_id=account_id,
                    symbol=symbol or "BTC-USDT",
                    leverage=leverage or 10,
                    order_size_usdt=order_size_usdt or Decimal("100.00"),
                    margin_mode=margin_mode or "CROSSED",
                    take_profit_percent=take_profit_percent or Decimal("0.50"),
                    # Dynamic TP fields (BE-035)
                    tp_dynamic_enabled=tp_dynamic_enabled
                    if tp_dynamic_enabled is not None
                    else False,
                    tp_base_percent=tp_base_percent or Decimal("0.30"),
                    tp_min_percent=tp_min_percent or Decimal("0.30"),
                    tp_max_percent=tp_max_percent or Decimal("1.00"),
                    tp_safety_margin=tp_safety_margin or Decimal("0.05"),
                    tp_check_interval_min=tp_check_interval_min or 60,
                )
                return await super().create(new_config)
        except Exception as e:
            await self.session.rollback()
            raise Exception(
                f"Error creating/updating trading config for account {account_id}: {e}"
            ) from e

    async def update_config(
        self,
        account_id: UUID,
        **kwargs: str | int | Decimal | bool,
    ) -> TradingConfig:
        """Update specific configuration fields for an account.

        DEPRECATED: Use StrategyRepository.update instead.

        Args:
            account_id: UUID of the account.
            **kwargs: Field-value pairs to update.
                Valid fields: symbol, leverage, order_size_usdt, margin_mode,
                             take_profit_percent, tp_dynamic_enabled, tp_base_percent,
                             tp_min_percent, tp_max_percent, tp_safety_margin,
                             tp_check_interval_min.

        Returns:
            Updated TradingConfig instance.

        Raises:
            ValueError: If account has no configuration.
            Exception: If database operation fails.

        Example:
            config = await repo.update_config(
                account_id,
                leverage=15,
                take_profit_percent=Decimal("0.8")
            )
        """
        try:
            existing = await self.get_by_account(account_id)
            if not existing:
                raise ValueError(f"No trading config found for account {account_id}")

            # Update fields
            for field, value in kwargs.items():
                if hasattr(existing, field):
                    setattr(existing, field, value)

            return await super().update(existing)
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error updating trading config for account {account_id}: {e}") from e
