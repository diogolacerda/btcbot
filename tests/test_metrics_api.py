"""Tests for performance metrics API endpoints."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_account_id, get_trade_repository
from src.api.main import app
from src.database.models.trade import Trade


@pytest.fixture
def test_account_id():
    """Provide a test account ID."""
    return uuid4()


@pytest.fixture
def sample_trades(test_account_id):
    """Create sample trades for testing metrics."""
    trades = []
    now = datetime.now(UTC)

    # Create 5 closed trades (3 wins, 2 losses) - all from today
    for i in range(5):
        is_win = i < 3
        entry_price = Decimal("95000.00")
        exit_price = Decimal("95500.00") if is_win else Decimal("94500.00")
        pnl = (exit_price - entry_price) * Decimal("0.001")

        trade = Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=Decimal("0.001"),
            tp_price=exit_price,
            tp_percent=Decimal("0.5"),
            pnl=pnl,
            pnl_percent=(pnl / (entry_price * Decimal("0.001"))) * Decimal("100"),
            trading_fee=Decimal("0.05"),
            funding_fee=Decimal("0.01"),
            status="CLOSED",
            grid_level=i + 1,
            opened_at=now - timedelta(hours=i + 1),
            filled_at=now - timedelta(hours=i + 1),
            closed_at=now - timedelta(hours=i),
            created_at=now - timedelta(hours=i + 1),
            updated_at=now - timedelta(hours=i),
        )
        trades.append(trade)

    # Create 3 older closed trades (from 10 days ago)
    for i in range(3):
        is_win = i < 2
        entry_price = Decimal("94000.00")
        exit_price = Decimal("94500.00") if is_win else Decimal("93500.00")
        pnl = (exit_price - entry_price) * Decimal("0.001")

        trade = Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=Decimal("0.001"),
            tp_price=exit_price,
            tp_percent=Decimal("0.5"),
            pnl=pnl,
            pnl_percent=(pnl / (entry_price * Decimal("0.001"))) * Decimal("100"),
            trading_fee=Decimal("0.05"),
            funding_fee=Decimal("0.01"),
            status="CLOSED",
            grid_level=i + 6,
            opened_at=now - timedelta(days=10, hours=i + 1),
            filled_at=now - timedelta(days=10, hours=i + 1),
            closed_at=now - timedelta(days=10, hours=i),
            created_at=now - timedelta(days=10, hours=i + 1),
            updated_at=now - timedelta(days=10, hours=i),
        )
        trades.append(trade)

    return trades


def test_get_performance_metrics_today(sample_trades, test_account_id):
    """Test GET /api/v1/metrics/performance with today period."""
    # Filter trades opened today
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    today_trades = [t for t in sample_trades if t.opened_at >= today_start]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = today_trades
        mock_repo.get_trades_by_account.return_value = sample_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/metrics/performance",
            params={"period": "today"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "period_metrics" in data
        assert "total_metrics" in data

        # Verify period metrics
        period = data["period_metrics"]
        assert period["period"] == "today"
        assert "start_date" in period
        assert "end_date" in period
        assert "realized_pnl" in period
        assert "pnl_percent" in period
        assert "trades_closed" in period
        assert "winning_trades" in period
        assert "losing_trades" in period
        assert "win_rate" in period

        # Verify total metrics
        total = data["total_metrics"]
        assert "total_pnl" in total
        assert "total_trades" in total
        assert "avg_profit_per_trade" in total
        assert "total_fees" in total
        assert "net_pnl" in total
        assert "best_trade" in total
        assert "worst_trade" in total

        # Total should include all 8 closed trades
        assert total["total_trades"] == 8
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_7days(sample_trades, test_account_id):
    """Test GET /api/v1/metrics/performance with 7days period."""
    # All trades from last 7 days (only today's trades in our sample)
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = today_start - timedelta(days=6)
    period_trades = [t for t in sample_trades if t.opened_at >= seven_days_ago]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = period_trades
        mock_repo.get_trades_by_account.return_value = sample_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/metrics/performance",
            params={"period": "7days"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["period_metrics"]["period"] == "7days"
        # Period should have 5 trades (today's trades)
        assert data["period_metrics"]["trades_closed"] == 5
        # Total should have all 8 trades
        assert data["total_metrics"]["total_trades"] == 8
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_30days(sample_trades, test_account_id):
    """Test GET /api/v1/metrics/performance with 30days period."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        # All trades are within 30 days
        mock_repo.get_trades_by_period.return_value = sample_trades
        mock_repo.get_trades_by_account.return_value = sample_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/metrics/performance",
            params={"period": "30days"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["period_metrics"]["period"] == "30days"
        # All 8 closed trades should be in the period
        assert data["period_metrics"]["trades_closed"] == 8
        assert data["total_metrics"]["total_trades"] == 8
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_custom_period(sample_trades, test_account_id):
    """Test GET /api/v1/metrics/performance with custom period."""
    now = datetime.now(UTC)
    start_date = (now - timedelta(days=15)).isoformat()
    end_date = (now - timedelta(days=5)).isoformat()

    # Only older trades (from 10 days ago)
    older_trades = [t for t in sample_trades if t.opened_at <= now - timedelta(days=5)]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = older_trades
        mock_repo.get_trades_by_account.return_value = sample_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/metrics/performance",
            params={
                "period": "custom",
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["period_metrics"]["period"] == "custom"
        # 3 older trades should be in the custom period
        assert data["period_metrics"]["trades_closed"] == 3
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_custom_without_dates(test_account_id):
    """Test GET /api/v1/metrics/performance custom period without dates."""

    async def mock_get_trade_repository():
        return AsyncMock()

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/metrics/performance",
            params={"period": "custom"},
        )

        assert response.status_code == 400
        assert "start_date and end_date are required" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_empty(test_account_id):
    """Test GET /api/v1/metrics/performance with no trades."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = []
        mock_repo.get_trades_by_account.return_value = []
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/metrics/performance")

        assert response.status_code == 200
        data = response.json()

        # Period metrics should show zeros
        assert data["period_metrics"]["trades_closed"] == 0
        assert float(data["period_metrics"]["realized_pnl"]) == 0.0
        assert float(data["period_metrics"]["win_rate"]) == 0.0

        # Total metrics should show zeros
        assert data["total_metrics"]["total_trades"] == 0
        assert float(data["total_metrics"]["total_pnl"]) == 0.0
        assert float(data["total_metrics"]["avg_profit_per_trade"]) == 0.0
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_win_rate_calculation(test_account_id):
    """Test that win rate is calculated correctly."""
    now = datetime.now(UTC)

    # Create 10 trades: 7 wins, 3 losses (70% win rate)
    trades = []
    for i in range(10):
        is_win = i < 7
        pnl = Decimal("5.00") if is_win else Decimal("-3.00")

        trade = Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("95000.00"),
            exit_price=Decimal("95500.00") if is_win else Decimal("94500.00"),
            quantity=Decimal("0.001"),
            pnl=pnl,
            trading_fee=Decimal("0.01"),
            funding_fee=Decimal("0.00"),
            status="CLOSED",
            opened_at=now - timedelta(hours=i + 1),
            closed_at=now - timedelta(hours=i),
            created_at=now - timedelta(hours=i + 1),
            updated_at=now - timedelta(hours=i),
        )
        trades.append(trade)

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = trades
        mock_repo.get_trades_by_account.return_value = trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/metrics/performance")

        assert response.status_code == 200
        data = response.json()

        # Win rate should be 70%
        assert float(data["period_metrics"]["win_rate"]) == 70.0
        assert data["period_metrics"]["winning_trades"] == 7
        assert data["period_metrics"]["losing_trades"] == 3

        # Total P&L: 7 * 5 - 3 * 3 = 35 - 9 = 26
        assert float(data["total_metrics"]["total_pnl"]) == 26.0
        # Average: 26 / 10 = 2.6
        assert float(data["total_metrics"]["avg_profit_per_trade"]) == 2.6
        # Best trade: 5.00
        assert float(data["total_metrics"]["best_trade"]) == 5.0
        # Worst trade: -3.00
        assert float(data["total_metrics"]["worst_trade"]) == -3.0
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_default_period(test_account_id):
    """Test that default period is 'today'."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = []
        mock_repo.get_trades_by_account.return_value = []
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        # No period parameter - should default to today
        response = client.get("/api/v1/metrics/performance")

        assert response.status_code == 200
        data = response.json()

        assert data["period_metrics"]["period"] == "today"
    finally:
        app.dependency_overrides.clear()
