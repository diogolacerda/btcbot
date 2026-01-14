"""Integration tests for bot state restoration."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from config import MACDConfig
from src.database.helpers import get_or_create_account
from src.database.models.account import Account
from src.database.models.user import User
from src.database.repositories.bot_state_repository import BotStateRepository
from src.strategy.macd_strategy import GridState, MACDStrategy


@pytest.fixture
def macd_config():
    """Create MACD config for testing."""
    return MACDConfig(
        fast=12,
        slow=26,
        signal=9,
        timeframe="1h",
    )


def test_state_restoration_flow(session, macd_config):
    """Test complete state restoration flow."""
    # Create account
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password",  # pragma: allowlist secret
    )
    session.add(user)
    session.flush()

    account = Account(
        user_id=user.id,
        exchange="bingx",
        name="Test Account",
        is_demo=True,
    )
    session.add(account)
    session.commit()

    # Save bot state
    repo = BotStateRepository(session)
    repo.save_state(
        account_id=account.id,
        cycle_activated=True,
        last_state="active",
    )

    # Create new strategy instance (simulating restart)
    # Note: We need to mock the repository since it needs a session
    mock_repo = MagicMock()
    strategy = MACDStrategy(
        macd_config,
        account_id=account.id,
        bot_state_repository=mock_repo,
    )

    # Restore state
    bot_state = repo.get_by_account(account.id)
    strategy.restore_state(
        cycle_activated=bot_state.cycle_activated,
        last_state=bot_state.last_state,
    )

    # Verify state was restored
    assert strategy.is_cycle_activated is True
    assert strategy.is_trigger_activated is True
    assert strategy._prev_state == GridState.ACTIVE


def test_state_restoration_with_invalid_last_state(session, macd_config):
    """Test state restoration with invalid last_state value."""
    # Create account
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password",  # pragma: allowlist secret
    )
    session.add(user)
    session.flush()

    account = Account(
        user_id=user.id,
        exchange="bingx",
        name="Test Account",
        is_demo=True,
    )
    session.add(account)
    session.commit()

    # Create strategy
    strategy = MACDStrategy(macd_config, account_id=account.id)

    # Restore with invalid state
    strategy.restore_state(
        cycle_activated=True,
        last_state="invalid_state",
    )

    # Should default to WAIT
    assert strategy._prev_state == GridState.WAIT


def test_get_or_create_account_creates_user_and_account(session):
    """Test get_or_create_account helper creates user and account."""
    from config import BingXConfig, TradingConfig, TradingMode

    bingx_config = BingXConfig(
        api_key="test_key",  # pragma: allowlist secret
        secret_key="test_secret",  # pragma: allowlist secret
        is_demo=True,
    )
    trading_config = TradingConfig(
        symbol="BTC-USDT",
        leverage=10,
        order_size_usdt=100.0,
        mode=TradingMode.DEMO,
    )

    # Get/create account
    account_id = get_or_create_account(
        session=session,
        bingx_config=bingx_config,
        trading_config=trading_config,
    )

    assert account_id is not None

    # Verify account was created
    repo = BotStateRepository(session)
    bot_state = repo.get_by_account(account_id)
    # Should be None initially
    assert bot_state is None


def test_get_or_create_account_is_idempotent(session):
    """Test get_or_create_account is idempotent."""
    from config import BingXConfig, TradingConfig, TradingMode

    bingx_config = BingXConfig(
        api_key="test_key",  # pragma: allowlist secret
        secret_key="test_secret",  # pragma: allowlist secret
        is_demo=True,
    )
    trading_config = TradingConfig(
        symbol="BTC-USDT",
        leverage=10,
        order_size_usdt=100.0,
        mode=TradingMode.DEMO,
    )

    # Create account twice
    account_id1 = get_or_create_account(
        session=session,
        bingx_config=bingx_config,
        trading_config=trading_config,
    )
    account_id2 = get_or_create_account(
        session=session,
        bingx_config=bingx_config,
        trading_config=trading_config,
    )

    # Should return same account
    assert account_id1 == account_id2


def test_state_not_restored_if_too_old(session, macd_config):
    """Test that old state is not considered valid."""
    # Create account
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password",  # pragma: allowlist secret
    )
    session.add(user)
    session.flush()

    account = Account(
        user_id=user.id,
        exchange="bingx",
        name="Test Account",
        is_demo=True,
    )
    session.add(account)
    session.commit()

    # Save bot state with old timestamp
    repo = BotStateRepository(session)
    bot_state = repo.save_state(
        account_id=account.id,
        cycle_activated=True,
        last_state="active",
        activated_at=datetime.now(UTC) - timedelta(hours=25),
    )

    # Check validity (max 24 hours)
    is_valid = repo.is_state_valid(bot_state, max_age_hours=24)
    assert is_valid is False


def test_state_restored_if_recent(session, macd_config):
    """Test that recent state is considered valid."""
    # Create account
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password",  # pragma: allowlist secret
    )
    session.add(user)
    session.flush()

    account = Account(
        user_id=user.id,
        exchange="bingx",
        name="Test Account",
        is_demo=True,
    )
    session.add(account)
    session.commit()

    # Save recent bot state
    repo = BotStateRepository(session)
    bot_state = repo.save_state(
        account_id=account.id,
        cycle_activated=True,
        last_state="active",
    )

    # Check validity (max 24 hours)
    is_valid = repo.is_state_valid(bot_state, max_age_hours=24)
    assert is_valid is True
