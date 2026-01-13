"""Tests for the migrate_to_strategy data migration script."""

from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.migrations.migrate_to_strategy import (
    create_default_macd_config,
    create_strategy_from_configs,
    has_existing_strategy,
    map_margin_mode,
    migrate_account,
)
from src.database.models.account import Account
from src.database.models.grid_config import GridConfig
from src.database.models.macd_filter_config import MACDFilterConfig
from src.database.models.strategy import Strategy
from src.database.models.trading_config import TradingConfig
from src.database.models.user import User


@pytest_asyncio.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed_password_123",  # pragma: allowlist secret
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest_asyncio.fixture
def account(session: Session, user: User) -> Account:
    """Create a test account."""
    account = Account(
        id=uuid4(),
        user_id=user.id,
        exchange="bingx",
        name="Test Account",
        is_demo=True,
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@pytest_asyncio.fixture
def trading_config(session: Session, account: Account) -> TradingConfig:
    """Create a test trading config."""
    config = TradingConfig(
        id=uuid4(),
        account_id=account.id,
        symbol="BTC-USDT",
        leverage=10,
        order_size_usdt=Decimal("100.00"),
        margin_mode="CROSSED",
        take_profit_percent=Decimal("0.50"),
        tp_dynamic_enabled=True,
        tp_base_percent=Decimal("0.30"),
        tp_min_percent=Decimal("0.20"),
        tp_max_percent=Decimal("1.00"),
        tp_safety_margin=Decimal("0.05"),
        tp_check_interval_min=60,
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


@pytest_asyncio.fixture
def grid_config(session: Session, account: Account) -> GridConfig:
    """Create a test grid config."""
    config = GridConfig(
        id=uuid4(),
        account_id=account.id,
        spacing_type="fixed",
        spacing_value=Decimal("100.0"),
        range_percent=Decimal("5.0"),
        max_total_orders=10,
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


class TestMapMarginMode:
    """Tests for map_margin_mode function."""

    def test_crossed_to_lowercase(self):
        """Should convert CROSSED to crossed."""
        assert map_margin_mode("CROSSED") == "crossed"

    def test_isolated_to_lowercase(self):
        """Should convert ISOLATED to isolated."""
        assert map_margin_mode("ISOLATED") == "isolated"

    def test_already_lowercase(self):
        """Should keep lowercase as is."""
        assert map_margin_mode("crossed") == "crossed"


class TestCreateStrategyFromConfigs:
    """Tests for create_strategy_from_configs function."""

    def test_creates_strategy_with_correct_values(
        self,
        session: Session,
        account: Account,
        trading_config: TradingConfig,
        grid_config: GridConfig,
    ):
        """Should create strategy with all values mapped correctly."""
        strategy = create_strategy_from_configs(account, trading_config, grid_config)

        # Verify core fields
        assert strategy.account_id == account.id
        assert strategy.name == f"Migrated Strategy - {account.name}"
        assert strategy.is_active is True
        assert strategy.symbol == "BTC-USDT"

        # Verify TradingConfig fields
        assert strategy.leverage == 10
        assert strategy.order_size_usdt == Decimal("100.00")
        assert strategy.margin_mode == "crossed"  # lowercase
        assert strategy.take_profit_percent == Decimal("0.50")
        assert strategy.tp_dynamic_enabled is True
        assert strategy.tp_dynamic_base == Decimal("0.30")
        assert strategy.tp_dynamic_min == Decimal("0.20")
        assert strategy.tp_dynamic_max == Decimal("1.00")
        assert strategy.tp_dynamic_safety_margin == Decimal("0.05")
        assert strategy.tp_dynamic_check_interval == 60

        # Verify GridConfig fields
        assert strategy.spacing_type == "fixed"
        assert strategy.spacing_value == Decimal("100.0")
        assert strategy.range_percent == Decimal("5.0")
        assert strategy.max_total_orders == 10


class TestCreateDefaultMacdConfig:
    """Tests for create_default_macd_config function."""

    def test_creates_default_config(
        self,
        session: Session,
        account: Account,
        trading_config: TradingConfig,
        grid_config: GridConfig,
    ):
        """Should create MACD config with default values."""
        strategy = create_strategy_from_configs(account, trading_config, grid_config)
        session.add(strategy)
        session.flush()

        macd_config = create_default_macd_config(strategy)

        assert macd_config.strategy_id == strategy.id
        assert macd_config.enabled is True
        assert macd_config.fast_period == 12
        assert macd_config.slow_period == 26
        assert macd_config.signal_period == 9
        assert macd_config.timeframe == "1h"


class TestHasExistingStrategy:
    """Tests for has_existing_strategy function."""

    def test_returns_false_when_no_strategy(self, session: Session, account: Account):
        """Should return False when account has no strategy."""
        result = has_existing_strategy(session, account.id)
        assert result is False

    def test_returns_true_when_strategy_exists(
        self,
        session: Session,
        account: Account,
        trading_config: TradingConfig,
        grid_config: GridConfig,
    ):
        """Should return True when account has a strategy."""
        strategy = create_strategy_from_configs(account, trading_config, grid_config)
        session.add(strategy)
        session.flush()

        result = has_existing_strategy(session, account.id)
        assert result is True


class TestMigrateAccount:
    """Tests for migrate_account function."""

    def test_migrates_account_successfully(
        self,
        session: Session,
        account: Account,
        trading_config: TradingConfig,
        grid_config: GridConfig,
    ):
        """Should migrate account and create Strategy + MACDFilterConfig."""
        result = migrate_account(
            session=session,
            account=account,
            trading_config=trading_config,
            grid_config=grid_config,
            dry_run=False,
        )

        assert result.status == "migrated"
        assert result.account_id == account.id
        assert result.strategy_id is not None

        # Verify Strategy was created
        stmt = select(Strategy).where(Strategy.id == result.strategy_id)
        strategy = session.scalar(stmt)
        assert strategy is not None
        assert strategy.account_id == account.id

        # Verify MACDFilterConfig was created
        macd_stmt = select(MACDFilterConfig).where(
            MACDFilterConfig.strategy_id == result.strategy_id
        )
        macd_config = session.scalar(macd_stmt)
        assert macd_config is not None

    def test_dry_run_does_not_create_records(
        self,
        session: Session,
        account: Account,
        trading_config: TradingConfig,
        grid_config: GridConfig,
    ):
        """Should not create records in dry run mode."""
        result = migrate_account(
            session=session,
            account=account,
            trading_config=trading_config,
            grid_config=grid_config,
            dry_run=True,
        )

        assert result.status == "migrated"
        assert result.strategy_id is None  # No ID in dry run

        # Verify no Strategy was created
        stmt = select(Strategy).where(Strategy.account_id == account.id)
        strategy = session.scalar(stmt)
        assert strategy is None

    def test_skips_when_strategy_exists(
        self,
        session: Session,
        account: Account,
        trading_config: TradingConfig,
        grid_config: GridConfig,
    ):
        """Should skip migration when Strategy already exists (idempotent)."""
        # First migration
        migrate_account(
            session=session,
            account=account,
            trading_config=trading_config,
            grid_config=grid_config,
            dry_run=False,
        )

        # Second migration should skip
        result = migrate_account(
            session=session,
            account=account,
            trading_config=trading_config,
            grid_config=grid_config,
            dry_run=False,
        )

        assert result.status == "skipped"
        assert result.error_message is not None
        assert "already exists" in result.error_message

    def test_skips_when_missing_trading_config(
        self,
        session: Session,
        account: Account,
        grid_config: GridConfig,
    ):
        """Should skip migration when TradingConfig is missing."""
        result = migrate_account(
            session=session,
            account=account,
            trading_config=None,
            grid_config=grid_config,
            dry_run=False,
        )

        assert result.status == "skipped"
        assert result.error_message is not None
        assert "TradingConfig" in result.error_message

    def test_skips_when_missing_grid_config(
        self,
        session: Session,
        account: Account,
        trading_config: TradingConfig,
    ):
        """Should skip migration when GridConfig is missing."""
        result = migrate_account(
            session=session,
            account=account,
            trading_config=trading_config,
            grid_config=None,
            dry_run=False,
        )

        assert result.status == "skipped"
        assert result.error_message is not None
        assert "GridConfig" in result.error_message

    def test_skips_when_missing_both_configs(
        self,
        session: Session,
        account: Account,
    ):
        """Should skip migration when both configs are missing."""
        result = migrate_account(
            session=session,
            account=account,
            trading_config=None,
            grid_config=None,
            dry_run=False,
        )

        assert result.status == "skipped"
        assert result.error_message is not None
        assert "TradingConfig" in result.error_message
        assert "GridConfig" in result.error_message
