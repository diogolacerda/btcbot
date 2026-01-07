"""Tests for trading data API endpoints."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_account_id,
    get_tp_adjustment_repository,
    get_trade_repository,
)
from src.api.main import app
from src.database.models.tp_adjustment import TPAdjustment
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

    # Create 5 closed trades (3 wins, 2 losses) with varying prices and quantities
    for i in range(5):
        is_win = i < 3
        entry_price = Decimal("95000.00") + Decimal(i * 100)  # 95000-95400
        exit_price = entry_price + Decimal("500") if is_win else entry_price - Decimal("500")
        quantity = Decimal("0.001") + Decimal(i) * Decimal("0.0001")  # 0.001-0.0014
        pnl = (exit_price - entry_price) * quantity

        trade = Trade(
            id=uuid4(),
            account_id=test_account_id,
            exchange_order_id=f"ORDER-{i + 1:04d}",
            exchange_tp_order_id=f"TP-{i + 1:04d}",
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            tp_price=exit_price,
            tp_percent=Decimal("0.5"),
            pnl=pnl,
            pnl_percent=(pnl / (entry_price * quantity)) * Decimal("100"),
            trading_fee=Decimal("0.05"),
            funding_fee=Decimal("0.01"),
            status="CLOSED",
            grid_level=i + 1,
            opened_at=now - timedelta(hours=i + 2),
            filled_at=now - timedelta(hours=i + 2),
            closed_at=now - timedelta(hours=i + 1),  # Duration: 1 hour each
            created_at=now - timedelta(hours=i + 2),
            updated_at=now - timedelta(hours=i + 1),
        )
        trades.append(trade)

    # Create 2 open trades
    for i in range(2):
        trade = Trade(
            id=uuid4(),
            account_id=test_account_id,
            exchange_order_id=f"ORDER-OPEN-{i + 1:04d}",
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("96000.00"),
            quantity=Decimal("0.002"),
            tp_price=Decimal("96500.00"),
            tp_percent=Decimal("0.5"),
            trading_fee=Decimal("0.05"),
            funding_fee=Decimal("0.01"),
            status="OPEN",
            grid_level=i + 6,
            opened_at=now - timedelta(minutes=30 * (i + 1)),
            filled_at=now - timedelta(minutes=30 * (i + 1)),
            created_at=now - timedelta(minutes=30 * (i + 1)),
            updated_at=now - timedelta(minutes=30 * (i + 1)),
        )
        trades.append(trade)

    return trades


def _create_mock_repository(trades: list[Trade]):
    """Create a mock repository with get_trades_with_filters method."""

    async def mock_get_trade_repository():
        mock_repo = AsyncMock()

        async def mock_get_trades_with_filters(
            account_id,
            *,
            start_date=None,
            end_date=None,
            status=None,
            min_entry_price=None,
            max_entry_price=None,
            min_quantity=None,
            max_quantity=None,
            limit=100,
            offset=0,
            sort_by=None,
            sort_direction=None,
        ):
            result = trades

            # Apply SQL-level filters
            if status:
                result = [t for t in result if t.status == status]
            if min_entry_price is not None:
                result = [t for t in result if t.entry_price >= min_entry_price]
            if max_entry_price is not None:
                result = [t for t in result if t.entry_price <= max_entry_price]
            if min_quantity is not None:
                result = [t for t in result if t.quantity >= min_quantity]
            if max_quantity is not None:
                result = [t for t in result if t.quantity <= max_quantity]

            # Apply SQL-level sorting (simulating database behavior)
            if sort_by is not None:
                sort_value = sort_by.value if hasattr(sort_by, "value") else str(sort_by)
                is_desc = (
                    sort_direction.value == "desc"
                    if hasattr(sort_direction, "value")
                    else str(sort_direction) == "desc"
                ) if sort_direction else True

                sort_key_map = {
                    "closedAt": lambda t: (t.closed_at is None, t.closed_at or datetime.min),
                    "entryPrice": lambda t: t.entry_price,
                    "exitPrice": lambda t: (t.exit_price is None, t.exit_price or Decimal(0)),
                    "quantity": lambda t: t.quantity,
                    "pnl": lambda t: (t.pnl is None, t.pnl or Decimal(0)),
                    "pnlPercent": lambda t: (t.pnl_percent is None, t.pnl_percent or Decimal(0)),
                }

                if sort_value in sort_key_map:
                    result = sorted(result, key=sort_key_map[sort_value], reverse=is_desc)

            total = len(result)
            result = result[offset : offset + limit]
            return result, total

        mock_repo.get_trades_with_filters = mock_get_trades_with_filters
        mock_repo.get_open_trades.return_value = [t for t in trades if t.status == "OPEN"]
        return mock_repo

    return mock_get_trade_repository


def _create_mock_tp_adjustment_repository(adjustments_by_trade_id: dict | None = None):
    """Create a mock TP adjustment repository.

    Args:
        adjustments_by_trade_id: Dict mapping trade_id (UUID) to list of TPAdjustment objects.
                                 If None, returns empty list for all trades.
    """
    if adjustments_by_trade_id is None:
        adjustments_by_trade_id = {}

    async def mock_get_tp_adjustment_repository():
        mock_repo = AsyncMock()
        mock_repo.get_by_trade.side_effect = lambda trade_id: adjustments_by_trade_id.get(
            trade_id, []
        )
        return mock_repo

    return mock_get_tp_adjustment_repository


def test_get_positions(sample_trades, test_account_id):
    """Test GET /trading/positions endpoint."""
    app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
    app.dependency_overrides[get_account_id] = lambda: test_account_id

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
    app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
    app.dependency_overrides[get_account_id] = lambda: test_account_id
    app.dependency_overrides[get_tp_adjustment_repository] = _create_mock_tp_adjustment_repository()

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
    app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
    app.dependency_overrides[get_account_id] = lambda: test_account_id
    app.dependency_overrides[get_tp_adjustment_repository] = _create_mock_tp_adjustment_repository()

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
    app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
    app.dependency_overrides[get_account_id] = lambda: test_account_id
    app.dependency_overrides[get_tp_adjustment_repository] = _create_mock_tp_adjustment_repository()

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
    app.dependency_overrides[get_trade_repository] = _create_mock_repository([])
    app.dependency_overrides[get_account_id] = lambda: test_account_id
    app.dependency_overrides[get_tp_adjustment_repository] = _create_mock_tp_adjustment_repository()

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

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = lambda: test_account_id

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
    app.dependency_overrides[get_trade_repository] = _create_mock_repository([])
    app.dependency_overrides[get_account_id] = lambda: test_account_id

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

    app.dependency_overrides[get_trade_repository] = mock_get_trade_repository
    app.dependency_overrides[get_account_id] = lambda: test_account_id

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
# BE-TRADE-001: Advanced Filter Tests
# ============================================================================


class TestProfitFilter:
    """Tests for profit_filter query parameter."""

    def test_profit_filter_profitable(self, sample_trades, test_account_id):
        """Test filtering for profitable trades only."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades", params={"profit_filter": "profitable"})

            assert response.status_code == 200
            data = response.json()

            # 3 trades have positive pnl in sample data
            assert data["total"] == 3
            for trade in data["trades"]:
                assert float(trade["pnl"]) > 0
        finally:
            app.dependency_overrides.clear()

    def test_profit_filter_losses(self, sample_trades, test_account_id):
        """Test filtering for losing trades only."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades", params={"profit_filter": "losses"})

            assert response.status_code == 200
            data = response.json()

            # 2 trades have negative pnl in sample data
            assert data["total"] == 2
            for trade in data["trades"]:
                assert float(trade["pnl"]) < 0
        finally:
            app.dependency_overrides.clear()

    def test_profit_filter_all(self, sample_trades, test_account_id):
        """Test profit_filter=all returns all trades."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades", params={"profit_filter": "all"})

            assert response.status_code == 200
            data = response.json()

            assert data["total"] == 7  # All trades
        finally:
            app.dependency_overrides.clear()


class TestPriceRangeFilter:
    """Tests for min/max entry_price query parameters."""

    def test_min_entry_price_filter(self, sample_trades, test_account_id):
        """Test filtering by minimum entry price."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades", params={"min_entry_price": "95200"})

            assert response.status_code == 200
            data = response.json()

            # Only trades with entry_price >= 95200 (indices 2,3,4 + 2 open at 96000)
            for trade in data["trades"]:
                assert float(trade["entry_price"]) >= 95200
        finally:
            app.dependency_overrides.clear()

    def test_max_entry_price_filter(self, sample_trades, test_account_id):
        """Test filtering by maximum entry price."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades", params={"max_entry_price": "95100"})

            assert response.status_code == 200
            data = response.json()

            # Only trades with entry_price <= 95100 (indices 0,1)
            for trade in data["trades"]:
                assert float(trade["entry_price"]) <= 95100
        finally:
            app.dependency_overrides.clear()

    def test_price_range_filter(self, sample_trades, test_account_id):
        """Test filtering by price range."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"min_entry_price": "95100", "max_entry_price": "95300"},
            )

            assert response.status_code == 200
            data = response.json()

            for trade in data["trades"]:
                assert 95100 <= float(trade["entry_price"]) <= 95300
        finally:
            app.dependency_overrides.clear()

    def test_invalid_price_range(self, sample_trades, test_account_id):
        """Test that min > max price returns 400 error."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"min_entry_price": "96000", "max_entry_price": "95000"},
            )

            assert response.status_code == 400
            assert "min_entry_price cannot be greater" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestDurationFilter:
    """Tests for min/max duration query parameters."""

    def test_min_duration_filter(self, sample_trades, test_account_id):
        """Test filtering by minimum duration."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            # 1 hour = 3600 seconds, all closed trades have 1h duration
            response = client.get("/api/v1/trading/trades", params={"min_duration": "3600"})

            assert response.status_code == 200
            data = response.json()

            # Only closed trades (5) have duration, open trades are excluded
            assert data["total"] == 5
            for trade in data["trades"]:
                assert trade["closed_at"] is not None
        finally:
            app.dependency_overrides.clear()

    def test_max_duration_filter(self, sample_trades, test_account_id):
        """Test filtering by maximum duration."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            # Less than 1 hour (3600 seconds) should return nothing
            response = client.get("/api/v1/trading/trades", params={"max_duration": "1800"})

            assert response.status_code == 200
            data = response.json()

            # No trades have duration < 30 minutes
            assert data["total"] == 0
        finally:
            app.dependency_overrides.clear()

    def test_invalid_duration_range(self, sample_trades, test_account_id):
        """Test that min > max duration returns 400 error."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades", params={"min_duration": "7200", "max_duration": "3600"}
            )

            assert response.status_code == 400
            assert "min_duration cannot be greater" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestQuantityFilter:
    """Tests for min/max quantity query parameters."""

    def test_min_quantity_filter(self, sample_trades, test_account_id):
        """Test filtering by minimum quantity."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades", params={"min_quantity": "0.0012"})

            assert response.status_code == 200
            data = response.json()

            for trade in data["trades"]:
                assert float(trade["quantity"]) >= 0.0012
        finally:
            app.dependency_overrides.clear()

    def test_max_quantity_filter(self, sample_trades, test_account_id):
        """Test filtering by maximum quantity."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades", params={"max_quantity": "0.0011"})

            assert response.status_code == 200
            data = response.json()

            for trade in data["trades"]:
                assert float(trade["quantity"]) <= 0.0011
        finally:
            app.dependency_overrides.clear()

    def test_invalid_quantity_range(self, sample_trades, test_account_id):
        """Test that min > max quantity returns 400 error."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades", params={"min_quantity": "0.002", "max_quantity": "0.001"}
            )

            assert response.status_code == 400
            assert "min_quantity cannot be greater" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestSearchFilter:
    """Tests for search_query query parameter."""

    def test_search_by_order_id(self, sample_trades, test_account_id):
        """Test searching by exchange_order_id."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades", params={"search_query": "ORDER-0001"})

            assert response.status_code == 200
            data = response.json()

            assert data["total"] == 1
            assert "ORDER-0001" in data["trades"][0]["exchange_order_id"]
        finally:
            app.dependency_overrides.clear()

    def test_search_by_tp_order_id(self, sample_trades, test_account_id):
        """Test searching by exchange_tp_order_id."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades", params={"search_query": "TP-0003"})

            assert response.status_code == 200
            data = response.json()

            assert data["total"] == 1
        finally:
            app.dependency_overrides.clear()

    def test_search_partial_match(self, sample_trades, test_account_id):
        """Test partial match search."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            # Search for "ORDER-000" should match ORDER-0001 through ORDER-0005
            response = client.get("/api/v1/trading/trades", params={"search_query": "ORDER-000"})

            assert response.status_code == 200
            data = response.json()

            assert data["total"] == 5  # All closed trades
        finally:
            app.dependency_overrides.clear()

    def test_search_no_match(self, sample_trades, test_account_id):
        """Test search with no matches."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades", params={"search_query": "NONEXISTENT"})

            assert response.status_code == 200
            data = response.json()

            assert data["total"] == 0
        finally:
            app.dependency_overrides.clear()


class TestCombinedFilters:
    """Tests for multiple filters combined."""

    def test_profit_and_price_filter(self, sample_trades, test_account_id):
        """Test combining profit and price filters."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"profit_filter": "profitable", "min_entry_price": "95100"},
            )

            assert response.status_code == 200
            data = response.json()

            # Only profitable trades with entry_price >= 95100
            for trade in data["trades"]:
                assert float(trade["pnl"]) > 0
                assert float(trade["entry_price"]) >= 95100
        finally:
            app.dependency_overrides.clear()

    def test_status_and_duration_filter(self, sample_trades, test_account_id):
        """Test combining status and duration filters."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"status": "CLOSED", "min_duration": "3600"},
            )

            assert response.status_code == 200
            data = response.json()

            # All closed trades with duration >= 1 hour
            assert data["total"] == 5
            for trade in data["trades"]:
                assert trade["status"] == "CLOSED"
        finally:
            app.dependency_overrides.clear()

    def test_all_filters_combined(self, sample_trades, test_account_id):
        """Test applying all filters at once."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sample_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={
                    "status": "CLOSED",
                    "profit_filter": "profitable",
                    "min_entry_price": "95000",
                    "max_entry_price": "95200",
                    "min_quantity": "0.001",
                    "max_quantity": "0.0012",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify all filters are applied (AND logic)
            for trade in data["trades"]:
                assert trade["status"] == "CLOSED"
                assert float(trade["pnl"]) > 0
                assert 95000 <= float(trade["entry_price"]) <= 95200
                assert 0.001 <= float(trade["quantity"]) <= 0.0012
        finally:
            app.dependency_overrides.clear()


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


# ============================================================================
# Trade Enrichment Tests (BE-TRADE-003)
# ============================================================================


class TestTradeEnrichment:
    """Tests for trade enrichment with duration, fees, and TP adjustments."""

    def test_trade_includes_duration_for_closed_trade(self, test_account_id):
        """Test that closed trades include calculated duration in seconds."""
        now = datetime.now(UTC)
        trade = Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("95000.00"),
            exit_price=Decimal("95500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("0.50"),
            pnl_percent=Decimal("0.53"),
            trading_fee=Decimal("0.05"),
            funding_fee=Decimal("0.01"),
            status="CLOSED",
            opened_at=now - timedelta(hours=2, minutes=30),  # 2.5 hours = 9000 seconds
            closed_at=now,
            created_at=now - timedelta(hours=3),
            updated_at=now,
        )

        app.dependency_overrides[get_trade_repository] = _create_mock_repository([trade])
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades")

            assert response.status_code == 200
            data = response.json()
            assert len(data["trades"]) == 1

            trade_data = data["trades"][0]
            assert "duration" in trade_data
            assert trade_data["duration"] == 9000  # 2.5 hours in seconds
        finally:
            app.dependency_overrides.clear()

    def test_trade_includes_fees_breakdown(self, test_account_id):
        """Test that trades include fees breakdown with net P&L."""
        now = datetime.now(UTC)
        trade = Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("95000.00"),
            exit_price=Decimal("95500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("0.50"),  # Gross PnL
            pnl_percent=Decimal("0.53"),
            trading_fee=Decimal("0.05"),  # Trading fee
            funding_fee=Decimal("0.02"),  # Funding fee
            status="CLOSED",
            opened_at=now - timedelta(hours=1),
            closed_at=now,
            created_at=now - timedelta(hours=1),
            updated_at=now,
        )

        app.dependency_overrides[get_trade_repository] = _create_mock_repository([trade])
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades")

            assert response.status_code == 200
            data = response.json()
            trade_data = data["trades"][0]

            assert "fees" in trade_data
            fees = trade_data["fees"]
            assert float(fees["trading_fee"]) == 0.05
            assert float(fees["funding_fee"]) == 0.02
            # Net P&L = 0.50 - 0.05 - 0.02 = 0.43
            assert float(fees["net_pnl"]) == 0.43
        finally:
            app.dependency_overrides.clear()

    def test_trade_includes_tp_adjustments_empty(self, test_account_id):
        """Test that trades include empty tp_adjustments when none exist."""
        now = datetime.now(UTC)
        trade = Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("95000.00"),
            exit_price=Decimal("95500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("0.50"),
            pnl_percent=Decimal("0.53"),
            trading_fee=Decimal("0.05"),
            funding_fee=Decimal("0.01"),
            status="CLOSED",
            opened_at=now - timedelta(hours=1),
            closed_at=now,
            created_at=now - timedelta(hours=1),
            updated_at=now,
        )

        app.dependency_overrides[get_trade_repository] = _create_mock_repository([trade])
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades")

            assert response.status_code == 200
            data = response.json()
            trade_data = data["trades"][0]

            assert "tp_adjustments" in trade_data
            assert trade_data["tp_adjustments"] == []
        finally:
            app.dependency_overrides.clear()

    def test_trade_includes_tp_adjustments_with_data(self, test_account_id):
        """Test that trades include TP adjustments when they exist."""
        now = datetime.now(UTC)
        trade_id = uuid4()
        trade = Trade(
            id=trade_id,
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("95000.00"),
            exit_price=Decimal("95500.00"),
            quantity=Decimal("0.001"),
            pnl=Decimal("0.50"),
            pnl_percent=Decimal("0.53"),
            trading_fee=Decimal("0.05"),
            funding_fee=Decimal("0.01"),
            status="CLOSED",
            opened_at=now - timedelta(hours=2),
            closed_at=now,
            created_at=now - timedelta(hours=2),
            updated_at=now,
        )

        # Mock TP adjustments
        adjustments = [
            TPAdjustment(
                id=uuid4(),
                trade_id=trade_id,
                old_tp_percent=Decimal("0.50"),
                new_tp_percent=Decimal("0.55"),
                funding_rate=Decimal("0.01"),
                funding_accumulated=Decimal("0.2"),
                hours_open=Decimal("1.5"),
                adjusted_at=now - timedelta(hours=1),
            ),
            TPAdjustment(
                id=uuid4(),
                trade_id=trade_id,
                old_tp_percent=Decimal("0.55"),
                new_tp_percent=Decimal("0.60"),
                funding_rate=Decimal("0.02"),
                funding_accumulated=Decimal("0.4"),
                hours_open=Decimal("2.0"),
                adjusted_at=now - timedelta(minutes=30),
            ),
        ]

        app.dependency_overrides[get_trade_repository] = _create_mock_repository([trade])
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository({trade_id: adjustments})
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades")

            assert response.status_code == 200
            data = response.json()
            trade_data = data["trades"][0]

            assert "tp_adjustments" in trade_data
            assert len(trade_data["tp_adjustments"]) == 2

            # Check first adjustment
            adj1 = trade_data["tp_adjustments"][0]
            assert float(adj1["old_tp"]) == 0.50
            assert float(adj1["new_tp"]) == 0.55
            assert "Funding rate: 0.0100%" in adj1["reason"]
            assert "accumulated: 0.20%" in adj1["reason"]
            assert "1.5h open" in adj1["reason"]

            # Check second adjustment
            adj2 = trade_data["tp_adjustments"][1]
            assert float(adj2["old_tp"]) == 0.55
            assert float(adj2["new_tp"]) == 0.60
        finally:
            app.dependency_overrides.clear()

    def test_open_trade_duration_is_none(self, test_account_id):
        """Test that open trades have null duration."""
        now = datetime.now(UTC)
        trade = Trade(
            id=uuid4(),
            account_id=test_account_id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("95000.00"),
            exit_price=None,
            quantity=Decimal("0.001"),
            pnl=None,
            pnl_percent=None,
            trading_fee=Decimal("0.00"),
            funding_fee=Decimal("0.00"),
            status="OPEN",
            opened_at=now - timedelta(hours=1),
            closed_at=None,  # Open trade
            created_at=now - timedelta(hours=1),
            updated_at=now,
        )

        app.dependency_overrides[get_trade_repository] = _create_mock_repository([trade])
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades")

            assert response.status_code == 200
            data = response.json()
            trade_data = data["trades"][0]

            # Open trade should have null duration
            assert trade_data["duration"] is None
        finally:
            app.dependency_overrides.clear()


class TestTradeSorting:
    """Tests for BE-TRADE-002: Sorting functionality on GET /trading/trades."""

    @pytest.fixture
    def sorting_trades(self, test_account_id):
        """Create trades with varied values for sorting tests."""
        now = datetime.now(UTC)
        trades = []

        # Trade 1: Highest entry price, lowest PNL, oldest closed
        trades.append(
            Trade(
                id=uuid4(),
                account_id=test_account_id,
                symbol="BTC-USDT",
                side="LONG",
                leverage=10,
                entry_price=Decimal("98000.00"),
                exit_price=Decimal("97500.00"),
                quantity=Decimal("0.003"),
                pnl=Decimal("-1.50"),
                pnl_percent=Decimal("-0.51"),
                trading_fee=Decimal("0.05"),
                funding_fee=Decimal("0.01"),
                status="CLOSED",
                opened_at=now - timedelta(hours=10),
                closed_at=now - timedelta(hours=8),  # Duration: 2h
                created_at=now - timedelta(hours=10),
                updated_at=now - timedelta(hours=8),
            )
        )

        # Trade 2: Middle entry price, middle PNL, middle closed
        trades.append(
            Trade(
                id=uuid4(),
                account_id=test_account_id,
                symbol="BTC-USDT",
                side="LONG",
                leverage=10,
                entry_price=Decimal("95000.00"),
                exit_price=Decimal("95500.00"),
                quantity=Decimal("0.002"),
                pnl=Decimal("1.00"),
                pnl_percent=Decimal("0.53"),
                trading_fee=Decimal("0.05"),
                funding_fee=Decimal("0.01"),
                status="CLOSED",
                opened_at=now - timedelta(hours=6),
                closed_at=now - timedelta(hours=4),  # Duration: 2h
                created_at=now - timedelta(hours=6),
                updated_at=now - timedelta(hours=4),
            )
        )

        # Trade 3: Lowest entry price, highest PNL, newest closed
        trades.append(
            Trade(
                id=uuid4(),
                account_id=test_account_id,
                symbol="BTC-USDT",
                side="LONG",
                leverage=10,
                entry_price=Decimal("93000.00"),
                exit_price=Decimal("94000.00"),
                quantity=Decimal("0.001"),
                pnl=Decimal("1.50"),
                pnl_percent=Decimal("1.08"),
                trading_fee=Decimal("0.05"),
                funding_fee=Decimal("0.01"),
                status="CLOSED",
                opened_at=now - timedelta(hours=2),
                closed_at=now - timedelta(hours=1),  # Duration: 1h (shortest)
                created_at=now - timedelta(hours=2),
                updated_at=now - timedelta(hours=1),
            )
        )

        return trades

    def test_default_sorting_closed_at_desc(self, sorting_trades, test_account_id):
        """Test default sorting is by closedAt DESC (newest first)."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sorting_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get("/api/v1/trading/trades")

            assert response.status_code == 200
            data = response.json()
            trades = data["trades"]

            # Default: closedAt DESC - newest first (Trade 3)
            assert len(trades) == 3
            assert Decimal(trades[0]["entry_price"]) == Decimal("93000.00")  # Newest
            assert Decimal(trades[2]["entry_price"]) == Decimal("98000.00")  # Oldest
        finally:
            app.dependency_overrides.clear()

    def test_sort_by_entry_price_asc(self, sorting_trades, test_account_id):
        """Test sorting by entry price ascending."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sorting_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"sort_by": "entryPrice", "sort_direction": "asc"},
            )

            assert response.status_code == 200
            data = response.json()
            trades = data["trades"]

            # entryPrice ASC: 93000 -> 95000 -> 98000
            assert Decimal(trades[0]["entry_price"]) == Decimal("93000.00")
            assert Decimal(trades[1]["entry_price"]) == Decimal("95000.00")
            assert Decimal(trades[2]["entry_price"]) == Decimal("98000.00")
        finally:
            app.dependency_overrides.clear()

    def test_sort_by_entry_price_desc(self, sorting_trades, test_account_id):
        """Test sorting by entry price descending."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sorting_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"sort_by": "entryPrice", "sort_direction": "desc"},
            )

            assert response.status_code == 200
            data = response.json()
            trades = data["trades"]

            # entryPrice DESC: 98000 -> 95000 -> 93000
            assert Decimal(trades[0]["entry_price"]) == Decimal("98000.00")
            assert Decimal(trades[1]["entry_price"]) == Decimal("95000.00")
            assert Decimal(trades[2]["entry_price"]) == Decimal("93000.00")
        finally:
            app.dependency_overrides.clear()

    def test_sort_by_pnl_asc(self, sorting_trades, test_account_id):
        """Test sorting by PNL ascending (losses first)."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sorting_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"sort_by": "pnl", "sort_direction": "asc"},
            )

            assert response.status_code == 200
            data = response.json()
            trades = data["trades"]

            # pnl ASC: -1.50 -> 1.00 -> 1.50
            assert Decimal(trades[0]["pnl"]) == Decimal("-1.50")
            assert Decimal(trades[1]["pnl"]) == Decimal("1.00")
            assert Decimal(trades[2]["pnl"]) == Decimal("1.50")
        finally:
            app.dependency_overrides.clear()

    def test_sort_by_pnl_desc(self, sorting_trades, test_account_id):
        """Test sorting by PNL descending (profits first)."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sorting_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"sort_by": "pnl", "sort_direction": "desc"},
            )

            assert response.status_code == 200
            data = response.json()
            trades = data["trades"]

            # pnl DESC: 1.50 -> 1.00 -> -1.50
            assert Decimal(trades[0]["pnl"]) == Decimal("1.50")
            assert Decimal(trades[1]["pnl"]) == Decimal("1.00")
            assert Decimal(trades[2]["pnl"]) == Decimal("-1.50")
        finally:
            app.dependency_overrides.clear()

    def test_sort_by_quantity_asc(self, sorting_trades, test_account_id):
        """Test sorting by quantity ascending."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sorting_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"sort_by": "quantity", "sort_direction": "asc"},
            )

            assert response.status_code == 200
            data = response.json()
            trades = data["trades"]

            # quantity ASC: 0.001 -> 0.002 -> 0.003
            assert Decimal(trades[0]["quantity"]) == Decimal("0.001")
            assert Decimal(trades[1]["quantity"]) == Decimal("0.002")
            assert Decimal(trades[2]["quantity"]) == Decimal("0.003")
        finally:
            app.dependency_overrides.clear()

    def test_sort_by_duration_asc(self, sorting_trades, test_account_id):
        """Test sorting by duration ascending (computed field, in-memory sort)."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sorting_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"sort_by": "duration", "sort_direction": "asc"},
            )

            assert response.status_code == 200
            data = response.json()
            trades = data["trades"]

            # Duration is computed: Trade 3 (1h) < Trade 1, 2 (2h each)
            # Trade 3 has entry_price 93000, shortest duration
            assert Decimal(trades[0]["entry_price"]) == Decimal("93000.00")
            assert trades[0]["duration"] == 3600  # 1 hour in seconds
        finally:
            app.dependency_overrides.clear()

    def test_sort_by_closed_at_asc(self, sorting_trades, test_account_id):
        """Test sorting by closedAt ascending (oldest first)."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sorting_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"sort_by": "closedAt", "sort_direction": "asc"},
            )

            assert response.status_code == 200
            data = response.json()
            trades = data["trades"]

            # closedAt ASC: oldest first (Trade 1 with entry 98000)
            assert Decimal(trades[0]["entry_price"]) == Decimal("98000.00")
            assert Decimal(trades[2]["entry_price"]) == Decimal("93000.00")
        finally:
            app.dependency_overrides.clear()

    def test_sorting_with_filters(self, sorting_trades, test_account_id):
        """Test that sorting works correctly with filters applied."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sorting_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            # Filter by profitable trades and sort by pnl desc
            response = client.get(
                "/api/v1/trading/trades",
                params={
                    "profit_filter": "profitable",
                    "sort_by": "pnl",
                    "sort_direction": "desc",
                },
            )

            assert response.status_code == 200
            data = response.json()
            trades = data["trades"]

            # Only 2 profitable trades: pnl 1.50 and 1.00
            assert len(trades) == 2
            assert Decimal(trades[0]["pnl"]) == Decimal("1.50")
            assert Decimal(trades[1]["pnl"]) == Decimal("1.00")
        finally:
            app.dependency_overrides.clear()

    def test_sorting_with_pagination(self, sorting_trades, test_account_id):
        """Test that sorting works correctly with pagination."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository(sorting_trades)
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            # Sort by entry price desc, limit 2
            response = client.get(
                "/api/v1/trading/trades",
                params={
                    "sort_by": "entryPrice",
                    "sort_direction": "desc",
                    "limit": 2,
                    "offset": 0,
                },
            )

            assert response.status_code == 200
            data = response.json()
            trades = data["trades"]

            # Should get top 2 by entry price: 98000, 95000
            assert len(trades) == 2
            assert Decimal(trades[0]["entry_price"]) == Decimal("98000.00")
            assert Decimal(trades[1]["entry_price"]) == Decimal("95000.00")
        finally:
            app.dependency_overrides.clear()

    def test_invalid_sort_by_returns_422(self, test_account_id):
        """Test that invalid sort_by value returns 422 validation error."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository([])
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"sort_by": "invalidField"},
            )

            # FastAPI returns 422 for enum validation errors
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_invalid_sort_direction_returns_422(self, test_account_id):
        """Test that invalid sort_direction value returns 422 validation error."""
        app.dependency_overrides[get_trade_repository] = _create_mock_repository([])
        app.dependency_overrides[get_account_id] = lambda: test_account_id
        app.dependency_overrides[get_tp_adjustment_repository] = (
            _create_mock_tp_adjustment_repository()
        )

        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/trading/trades",
                params={"sort_direction": "invalid"},
            )

            # FastAPI returns 422 for enum validation errors
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()
