"""Repository for TradingConfig persistence."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.trading_config import TradingConfig
from src.database.repositories.base_repository import BaseRepository


class TradingConfigRepository(BaseRepository[TradingConfig]):
    """Repository for managing trading configuration persistence.

    Provides CRUD operations for trading configurations, with special
    focus on account-based configuration retrieval and upsert operations.

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
        super().__init__(session, TradingConfig)

    async def get_by_account(self, account_id: UUID) -> TradingConfig | None:
        """Get trading configuration for a specific account.

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
    ) -> TradingConfig:
        """Create new trading config or update existing one.

        If config exists for the account, updates only provided fields.
        If config doesn't exist, creates with defaults for unprovided fields.

        Args:
            account_id: UUID of the account.
            symbol: Trading pair (e.g., 'BTC-USDT'). Optional.
            leverage: Leverage multiplier. Optional.
            order_size_usdt: Order size in USDT. Optional.
            margin_mode: Margin mode ('CROSSED' or 'ISOLATED'). Optional.
            take_profit_percent: Take profit percentage. Optional.

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
        **kwargs: str | int | Decimal,
    ) -> TradingConfig:
        """Update specific configuration fields for an account.

        Args:
            account_id: UUID of the account.
            **kwargs: Field-value pairs to update.
                Valid fields: symbol, leverage, order_size_usdt,
                             margin_mode, take_profit_percent.

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
