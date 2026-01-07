"""
Tests for MACDStrategy database configuration loading (BE-STRAT-012).

Tests the load_config_from_db method which loads MACD configuration
from the database Strategy and MACDFilterConfig models.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from config import MACDConfig
from src.strategy.macd_strategy import MACDStrategy


class TestLoadConfigFromDb:
    """Test load_config_from_db method."""

    @pytest.fixture
    def default_config(self):
        """Default MACD config from env vars."""
        return MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")

    @pytest.fixture
    def account_id(self):
        """Sample account ID."""
        return uuid4()

    @pytest.fixture
    def strategy_id(self):
        """Sample strategy ID."""
        return uuid4()

    @pytest.mark.asyncio
    async def test_load_config_no_account_id(self, default_config):
        """Test that load returns False when no account_id is set."""
        strategy = MACDStrategy(default_config)

        result = await strategy.load_config_from_db()

        assert result is False
        # Defaults should remain unchanged
        assert strategy.fast == 12
        assert strategy.slow == 26
        assert strategy.signal == 9
        assert strategy.timeframe == "1h"

    @pytest.mark.asyncio
    async def test_load_config_no_repositories(self, default_config, account_id):
        """Test that load returns False when repositories are not set."""
        strategy = MACDStrategy(default_config, account_id=account_id)

        result = await strategy.load_config_from_db()

        assert result is False
        # Defaults should remain unchanged
        assert strategy.fast == 12

    @pytest.mark.asyncio
    async def test_load_config_no_active_strategy(self, default_config, account_id):
        """Test that load returns False when no active strategy exists."""
        mock_strategy_repo = MagicMock()
        mock_strategy_repo.get_active_by_account = AsyncMock(return_value=None)
        mock_macd_repo = MagicMock()

        strategy = MACDStrategy(
            default_config,
            account_id=account_id,
            strategy_repository=mock_strategy_repo,
            macd_filter_config_repository=mock_macd_repo,
        )

        result = await strategy.load_config_from_db()

        assert result is False
        mock_strategy_repo.get_active_by_account.assert_called_once_with(account_id)
        # Defaults should remain unchanged
        assert strategy.fast == 12

    @pytest.mark.asyncio
    async def test_load_config_no_macd_filter_config(self, default_config, account_id, strategy_id):
        """Test that load returns False when no MACDFilterConfig exists."""
        mock_db_strategy = MagicMock()
        mock_db_strategy.id = strategy_id

        mock_strategy_repo = MagicMock()
        mock_strategy_repo.get_active_by_account = AsyncMock(return_value=mock_db_strategy)

        mock_macd_repo = MagicMock()
        mock_macd_repo.get_by_strategy = AsyncMock(return_value=None)

        strategy = MACDStrategy(
            default_config,
            account_id=account_id,
            strategy_repository=mock_strategy_repo,
            macd_filter_config_repository=mock_macd_repo,
        )

        result = await strategy.load_config_from_db()

        assert result is False
        mock_macd_repo.get_by_strategy.assert_called_once_with(strategy_id)
        # Defaults should remain unchanged
        assert strategy.fast == 12

    @pytest.mark.asyncio
    async def test_load_config_success(self, default_config, account_id, strategy_id):
        """Test successful config loading from database."""
        mock_db_strategy = MagicMock()
        mock_db_strategy.id = strategy_id

        mock_macd_config = MagicMock()
        mock_macd_config.fast_period = 15
        mock_macd_config.slow_period = 30
        mock_macd_config.signal_period = 10
        mock_macd_config.timeframe = "4h"
        mock_macd_config.enabled = True

        mock_strategy_repo = MagicMock()
        mock_strategy_repo.get_active_by_account = AsyncMock(return_value=mock_db_strategy)

        mock_macd_repo = MagicMock()
        mock_macd_repo.get_by_strategy = AsyncMock(return_value=mock_macd_config)

        strategy = MACDStrategy(
            default_config,
            account_id=account_id,
            strategy_repository=mock_strategy_repo,
            macd_filter_config_repository=mock_macd_repo,
        )

        result = await strategy.load_config_from_db()

        assert result is True
        # Values should be updated from DB
        assert strategy.fast == 15
        assert strategy.slow == 30
        assert strategy.signal == 10
        assert strategy.timeframe == "4h"
        assert strategy.is_macd_enabled is True

    @pytest.mark.asyncio
    async def test_load_config_disabled_macd(self, default_config, account_id, strategy_id):
        """Test config loading when MACD filter is disabled."""
        mock_db_strategy = MagicMock()
        mock_db_strategy.id = strategy_id

        mock_macd_config = MagicMock()
        mock_macd_config.fast_period = 12
        mock_macd_config.slow_period = 26
        mock_macd_config.signal_period = 9
        mock_macd_config.timeframe = "1h"
        mock_macd_config.enabled = False  # Disabled

        mock_strategy_repo = MagicMock()
        mock_strategy_repo.get_active_by_account = AsyncMock(return_value=mock_db_strategy)

        mock_macd_repo = MagicMock()
        mock_macd_repo.get_by_strategy = AsyncMock(return_value=mock_macd_config)

        strategy = MACDStrategy(
            default_config,
            account_id=account_id,
            strategy_repository=mock_strategy_repo,
            macd_filter_config_repository=mock_macd_repo,
        )

        result = await strategy.load_config_from_db()

        assert result is True
        assert strategy.is_macd_enabled is False

    @pytest.mark.asyncio
    async def test_load_config_only_loads_once(self, default_config, account_id, strategy_id):
        """Test that config is only loaded once (cached)."""
        mock_db_strategy = MagicMock()
        mock_db_strategy.id = strategy_id

        mock_macd_config = MagicMock()
        mock_macd_config.fast_period = 15
        mock_macd_config.slow_period = 30
        mock_macd_config.signal_period = 10
        mock_macd_config.timeframe = "4h"
        mock_macd_config.enabled = True

        mock_strategy_repo = MagicMock()
        mock_strategy_repo.get_active_by_account = AsyncMock(return_value=mock_db_strategy)

        mock_macd_repo = MagicMock()
        mock_macd_repo.get_by_strategy = AsyncMock(return_value=mock_macd_config)

        strategy = MACDStrategy(
            default_config,
            account_id=account_id,
            strategy_repository=mock_strategy_repo,
            macd_filter_config_repository=mock_macd_repo,
        )

        # Load twice
        result1 = await strategy.load_config_from_db()
        result2 = await strategy.load_config_from_db()

        assert result1 is True
        assert result2 is True
        # Repository should only be called once
        assert mock_strategy_repo.get_active_by_account.call_count == 1

    @pytest.mark.asyncio
    async def test_load_config_handles_exception(self, default_config, account_id):
        """Test that exceptions are handled gracefully."""
        mock_strategy_repo = MagicMock()
        mock_strategy_repo.get_active_by_account = AsyncMock(
            side_effect=Exception("Database error")
        )
        mock_macd_repo = MagicMock()

        strategy = MACDStrategy(
            default_config,
            account_id=account_id,
            strategy_repository=mock_strategy_repo,
            macd_filter_config_repository=mock_macd_repo,
        )

        result = await strategy.load_config_from_db()

        assert result is False
        # Defaults should remain unchanged
        assert strategy.fast == 12


class TestIsMacdEnabled:
    """Test is_macd_enabled property."""

    def test_default_enabled(self):
        """Test that MACD is enabled by default."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        strategy = MACDStrategy(config)

        assert strategy.is_macd_enabled is True

    @pytest.mark.asyncio
    async def test_enabled_after_load(self):
        """Test is_macd_enabled after loading from DB."""
        config = MACDConfig(fast=12, slow=26, signal=9, timeframe="1h")
        account_id = uuid4()
        strategy_id = uuid4()

        mock_db_strategy = MagicMock()
        mock_db_strategy.id = strategy_id

        mock_macd_config = MagicMock()
        mock_macd_config.fast_period = 12
        mock_macd_config.slow_period = 26
        mock_macd_config.signal_period = 9
        mock_macd_config.timeframe = "1h"
        mock_macd_config.enabled = False

        mock_strategy_repo = MagicMock()
        mock_strategy_repo.get_active_by_account = AsyncMock(return_value=mock_db_strategy)

        mock_macd_repo = MagicMock()
        mock_macd_repo.get_by_strategy = AsyncMock(return_value=mock_macd_config)

        strategy = MACDStrategy(
            config,
            account_id=account_id,
            strategy_repository=mock_strategy_repo,
            macd_filter_config_repository=mock_macd_repo,
        )

        await strategy.load_config_from_db()

        assert strategy.is_macd_enabled is False
