"""Tests for trading data API endpoints."""

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
    """Create sample trades for testing."""
    trades = []
    now = datetime.now(UTC)

    # Create 5 closed trades (3 wins, 2 losses)
    for i in range(5):
        is_win = i < 3
        entry_price = Decimal("95000.00")
        exit_price = Decimal("95500.00") if is_win else Decimal("94500.00")
        pnl = (exit_price - entry_price) * Decimal("0.001")

        trade = Trade(
            id=uuid4(),  # Add UUID
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
            created_at=now - timedelta(hours=i + 1),  # Add created_at
            updated_at=now - timedelta(hours=i),  # Add updated_at
        )
        trades.append(trade)

    # Create 2 open trades
    for i in range(2):
        trade = Trade(
            id=uuid4(),  # Add UUID
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("95000.00"),
            quantity=Decimal("0.001"),
            tp_price=Decimal("95500.00"),
            tp_percent=Decimal("0.5"),
            trading_fee=Decimal("0.05"),
            funding_fee=Decimal("0.01"),
            status="OPEN",
            grid_level=i + 6,
            opened_at=now - timedelta(minutes=30 * (i + 1)),
            filled_at=now - timedelta(minutes=30 * (i + 1)),
            created_at=now - timedelta(minutes=30 * (i + 1)),  # Add created_at
            updated_at=now - timedelta(minutes=30 * (i + 1)),  # Add updated_at
        )
        trades.append(trade)

    return trades


def test_get_positions(sample_trades, test_account_id):
    """Test GET /api/v1/trading/positions endpoint."""
    # Mock the repository to return only open trades
    open_trades = [t for t in sample_trades if t.status == "OPEN"]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_open_trades.return_value = open_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/positions")

        assert response.status_code == 200
        data = response.json()

        assert "positions" in data
        assert "total" in data
        assert data["total"] == 2  # 2 open trades
        assert len(data["positions"]) == 2

        # Verify position schema
        position = data["positions"][0]
        assert "symbol" in position
        assert "side" in position
        assert "entry_price" in position
        assert "quantity" in position
        assert position["symbol"] == "BTC-USDT"
    finally:
        app.dependency_overrides.clear()


def test_get_trades_all(sample_trades, test_account_id):
    """Test GET /trading/trades without filters."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_account.return_value = sample_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/trades")

        assert response.status_code == 200
        data = response.json()

        assert "trades" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["total"] == 7  # 5 closed + 2 open
        assert len(data["trades"]) == 7
    finally:
        app.dependency_overrides.clear()


def test_get_trades_with_status_filter(sample_trades, test_account_id):
    """Test GET /trading/trades with status filter."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_account.return_value = sample_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/trades", params={"status": "CLOSED"})

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5  # 5 closed trades
        assert all(trade["status"] == "CLOSED" for trade in data["trades"])
    finally:
        app.dependency_overrides.clear()


def test_get_trades_with_pagination(sample_trades, test_account_id):
    """Test GET /trading/trades with pagination."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_account.return_value = sample_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/trades", params={"limit": 3, "offset": 2})

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 3
        assert data["offset"] == 2
        assert len(data["trades"]) == 3
    finally:
        app.dependency_overrides.clear()


def test_get_trades_invalid_status(test_account_id):
    """Test GET /trading/trades with invalid status."""

    async def mock_get_trade_repository():
        return AsyncMock()

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/trades", params={"status": "INVALID"})

        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_get_trade_stats(sample_trades, test_account_id):
    """Test GET /api/v1/trading/stats endpoint."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_account.return_value = sample_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/stats")

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields
        assert "total_trades" in data
        assert "open_trades" in data
        assert "closed_trades" in data
        assert "winning_trades" in data
        assert "losing_trades" in data
        assert "win_rate" in data
        assert "total_pnl" in data
        assert "total_fees" in data
        assert "net_pnl" in data

        # Verify values
        assert data["total_trades"] == 7
        assert data["open_trades"] == 2
        assert data["closed_trades"] == 5
        assert data["winning_trades"] == 3
        assert data["losing_trades"] == 2

        # Win rate should be 60% (3 wins out of 5 closed)
        assert float(data["win_rate"]) == 60.0
    finally:
        app.dependency_overrides.clear()


def test_get_positions_empty(test_account_id):
    """Test GET /api/v1/trading/positions with no positions."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_open_trades.return_value = []
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/positions")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["positions"]) == 0
    finally:
        app.dependency_overrides.clear()


def test_get_stats_empty(test_account_id):
    """Test GET /api/v1/trading/stats with no trades."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_account.return_value = []
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total_trades"] == 0
        assert data["open_trades"] == 0
        assert data["closed_trades"] == 0
        assert float(data["win_rate"]) == 0.0
        assert float(data["total_pnl"]) == 0.0
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# Performance Metrics Endpoint Tests
# ============================================================================


def test_get_performance_metrics_default_period(sample_trades, test_account_id):
    """Test GET /api/v1/trading/performance-metrics with default period (today)."""
    closed_trades = [t for t in sample_trades if t.status == "CLOSED"]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = closed_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/performance-metrics")

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields
        assert "total_pnl" in data
        assert "roi" in data
        assert "total_trades" in data
        assert "winning_trades" in data
        assert "losing_trades" in data
        assert "win_rate" in data
        assert "avg_profit" in data
        assert "best_trade" in data
        assert "worst_trade" in data
        assert "period_start" in data
        assert "period_end" in data

        # Verify best/worst trade schema
        assert "id" in data["best_trade"]
        assert "pnl" in data["best_trade"]
        assert "date" in data["best_trade"]
        assert "id" in data["worst_trade"]
        assert "pnl" in data["worst_trade"]
        assert "date" in data["worst_trade"]

        # Verify counts (5 closed trades: 3 wins, 2 losses)
        assert data["total_trades"] == 5
        assert data["winning_trades"] == 3
        assert data["losing_trades"] == 2

        # Win rate should be 60% (3 wins out of 5 closed)
        assert float(data["win_rate"]) == 60.0
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_7days_period(sample_trades, test_account_id):
    """Test GET /api/v1/trading/performance-metrics with 7days period."""
    closed_trades = [t for t in sample_trades if t.status == "CLOSED"]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = closed_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/performance-metrics", params={"period": "7days"})

        assert response.status_code == 200
        data = response.json()

        # Period dates should be set
        assert data["period_start"] is not None
        assert data["period_end"] is not None
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_custom_period(sample_trades, test_account_id):
    """Test GET /api/v1/trading/performance-metrics with custom period."""
    closed_trades = [t for t in sample_trades if t.status == "CLOSED"]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = closed_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/trading/performance-metrics",
            params={
                "period": "custom",
                "start_date": "2026-01-01T00:00:00Z",
                "end_date": "2026-01-05T23:59:59Z",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["period_start"] is not None
        assert data["period_end"] is not None
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_custom_period_missing_dates(test_account_id):
    """Test GET /api/v1/trading/performance-metrics with custom period but missing dates."""

    async def mock_get_trade_repository():
        return AsyncMock()

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/trading/performance-metrics",
            params={"period": "custom"},
        )

        assert response.status_code == 400
        assert "start_date and end_date are required" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_empty_trades(test_account_id):
    """Test GET /api/v1/trading/performance-metrics with no trades."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = []
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/performance-metrics")

        assert response.status_code == 200
        data = response.json()

        # All values should be zero/empty
        assert data["total_trades"] == 0
        assert data["winning_trades"] == 0
        assert data["losing_trades"] == 0
        assert float(data["total_pnl"]) == 0.0
        assert float(data["roi"]) == 0.0
        assert float(data["win_rate"]) == 0.0
        assert float(data["avg_profit"]) == 0.0

        # Best/worst trade should be null/zero
        assert data["best_trade"]["id"] is None
        assert float(data["best_trade"]["pnl"]) == 0.0
        assert data["best_trade"]["date"] is None
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_roi_calculation(test_account_id):
    """Test that ROI is correctly calculated as (totalPnl / capital_employed) * 100."""
    now = datetime.now(UTC)

    # Create trades with known values for ROI calculation
    # Trade 1: entry_price=100, quantity=1, pnl=5 -> capital=100
    # Trade 2: entry_price=200, quantity=0.5, pnl=3 -> capital=100
    # Total capital: 200, Total PnL: 8, ROI: 4%
    trades = [
        Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("100.00"),
            exit_price=Decimal("105.00"),
            quantity=Decimal("1.00"),
            pnl=Decimal("5.00"),
            pnl_percent=Decimal("5.00"),
            trading_fee=Decimal("0.00"),
            funding_fee=Decimal("0.00"),
            status="CLOSED",
            opened_at=now - timedelta(hours=1),
            closed_at=now,
            created_at=now - timedelta(hours=1),
            updated_at=now,
        ),
        Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("200.00"),
            exit_price=Decimal("206.00"),
            quantity=Decimal("0.50"),
            pnl=Decimal("3.00"),
            pnl_percent=Decimal("3.00"),
            trading_fee=Decimal("0.00"),
            funding_fee=Decimal("0.00"),
            status="CLOSED",
            opened_at=now - timedelta(hours=2),
            closed_at=now - timedelta(hours=1),
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=1),
        ),
    ]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/performance-metrics")

        assert response.status_code == 200
        data = response.json()

        # Total PnL: 5 + 3 = 8
        assert float(data["total_pnl"]) == 8.0

        # Capital employed: (100 * 1) + (200 * 0.5) = 100 + 100 = 200
        # ROI: (8 / 200) * 100 = 4%
        assert float(data["roi"]) == 4.0
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_best_worst_trade_with_id(sample_trades, test_account_id):
    """Test that best/worst trades include id, pnl, and date."""
    closed_trades = [t for t in sample_trades if t.status == "CLOSED"]

    # Find expected best and worst
    best = max(closed_trades, key=lambda t: t.pnl if t.pnl else Decimal(0))
    worst = min(closed_trades, key=lambda t: t.pnl if t.pnl else Decimal(0))

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = closed_trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/performance-metrics")

        assert response.status_code == 200
        data = response.json()

        # Best trade should have positive pnl
        assert float(data["best_trade"]["pnl"]) > 0
        assert data["best_trade"]["id"] is not None
        assert data["best_trade"]["id"] == str(best.id)

        # Worst trade should have negative pnl
        assert float(data["worst_trade"]["pnl"]) < 0
        assert data["worst_trade"]["id"] is not None
        assert data["worst_trade"]["id"] == str(worst.id)
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# Single Trade Edge Case Tests (BUG-013)
# ============================================================================


def test_get_performance_metrics_single_positive_trade(test_account_id):
    """Test that single positive trade appears only in best_trade, not worst_trade."""
    now = datetime.now(UTC)

    # Single trade with positive PnL
    trades = [
        Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("95000.00"),
            exit_price=Decimal("95500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("5.00"),
            pnl_percent=Decimal("0.53"),
            trading_fee=Decimal("0.05"),
            funding_fee=Decimal("0.01"),
            status="CLOSED",
            opened_at=now - timedelta(hours=1),
            closed_at=now,
            created_at=now - timedelta(hours=1),
            updated_at=now,
        ),
    ]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/performance-metrics")

        assert response.status_code == 200
        data = response.json()

        # Positive trade should be best_trade only
        assert float(data["best_trade"]["pnl"]) == 5.00
        assert data["best_trade"]["id"] == str(trades[0].id)

        # worst_trade should be null
        assert data["worst_trade"]["id"] is None
        assert float(data["worst_trade"]["pnl"]) == 0.0
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_single_negative_trade(test_account_id):
    """Test that single negative trade appears only in worst_trade, not best_trade."""
    now = datetime.now(UTC)

    # Single trade with negative PnL
    trades = [
        Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("95000.00"),
            exit_price=Decimal("94500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("-5.00"),
            pnl_percent=Decimal("-0.53"),
            trading_fee=Decimal("0.05"),
            funding_fee=Decimal("0.01"),
            status="CLOSED",
            opened_at=now - timedelta(hours=1),
            closed_at=now,
            created_at=now - timedelta(hours=1),
            updated_at=now,
        ),
    ]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/performance-metrics")

        assert response.status_code == 200
        data = response.json()

        # best_trade should be null
        assert data["best_trade"]["id"] is None
        assert float(data["best_trade"]["pnl"]) == 0.0

        # Negative trade should be worst_trade only
        assert float(data["worst_trade"]["pnl"]) == -5.00
        assert data["worst_trade"]["id"] == str(trades[0].id)
    finally:
        app.dependency_overrides.clear()


def test_get_performance_metrics_single_breakeven_trade(test_account_id):
    """Test that single break-even trade (pnl=0) results in both fields being null."""
    now = datetime.now(UTC)

    # Single trade with zero PnL (break-even)
    trades = [
        Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("95000.00"),
            exit_price=Decimal("95000.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("0.00"),
            pnl_percent=Decimal("0.00"),
            trading_fee=Decimal("0.00"),
            funding_fee=Decimal("0.00"),
            status="CLOSED",
            opened_at=now - timedelta(hours=1),
            closed_at=now,
            created_at=now - timedelta(hours=1),
            updated_at=now,
        ),
    ]

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()
        mock_repo.get_trades_by_period.return_value = trades
        return mock_repo

    async def mock_get_account_id():
        return test_account_id

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = mock_get_account_id

    try:
        client = TestClient(app)
        response = client.get("/api/v1/trading/performance-metrics")

        assert response.status_code == 200
        data = response.json()

        # Both should be null for break-even trade
        assert data["best_trade"]["id"] is None
        assert float(data["best_trade"]["pnl"]) == 0.0
        assert data["worst_trade"]["id"] is None
        assert float(data["worst_trade"]["pnl"]) == 0.0
    finally:
        app.dependency_overrides.clear()
