"""Tests for trading data API endpoints."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.main import app
from src.database import get_session
from src.database.models.trade import Trade


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async for session in get_session():
        yield session


@pytest.fixture
async def test_account_id():
    """Provide a test account ID."""
    return uuid4()


@pytest.fixture
async def sample_trades(db_session: AsyncSession, test_account_id: UUID):
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
        )
        db_session.add(trade)
        trades.append(trade)

    # Create 2 open trades
    for i in range(2):
        trade = Trade(
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
        )
        db_session.add(trade)
        trades.append(trade)

    await db_session.commit()
    return trades


@pytest.mark.asyncio
async def test_get_positions(sample_trades, test_account_id):
    """Test GET /trading/positions/{account_id} endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/trading/positions/{test_account_id}")

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


@pytest.mark.asyncio
async def test_get_trades_all(sample_trades, test_account_id):
    """Test GET /trading/trades/{account_id} without filters."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/trading/trades/{test_account_id}")

        assert response.status_code == 200
        data = response.json()

        assert "trades" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["total"] == 7  # 5 closed + 2 open
        assert len(data["trades"]) == 7


@pytest.mark.asyncio
async def test_get_trades_with_status_filter(sample_trades, test_account_id):
    """Test GET /trading/trades/{account_id} with status filter."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/trading/trades/{test_account_id}", params={"status": "CLOSED"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5  # 5 closed trades
        assert all(trade["status"] == "CLOSED" for trade in data["trades"])


@pytest.mark.asyncio
async def test_get_trades_with_pagination(sample_trades, test_account_id):
    """Test GET /trading/trades/{account_id} with pagination."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/trading/trades/{test_account_id}", params={"limit": 3, "offset": 2}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 3
        assert data["offset"] == 2
        assert len(data["trades"]) == 3


@pytest.mark.asyncio
async def test_get_trades_invalid_status(test_account_id):
    """Test GET /trading/trades/{account_id} with invalid status."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/trading/trades/{test_account_id}", params={"status": "INVALID"}
        )

        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_trade_stats(sample_trades, test_account_id):
    """Test GET /trading/stats/{account_id} endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/trading/stats/{test_account_id}")

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


@pytest.mark.asyncio
async def test_get_positions_empty(test_account_id):
    """Test GET /trading/positions/{account_id} with no positions."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Use a different account ID with no trades
        new_account_id = uuid4()
        response = await client.get(f"/trading/positions/{new_account_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["positions"]) == 0


@pytest.mark.asyncio
async def test_get_stats_empty(test_account_id):
    """Test GET /trading/stats/{account_id} with no trades."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Use a different account ID with no trades
        new_account_id = uuid4()
        response = await client.get(f"/trading/stats/{new_account_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["total_trades"] == 0
        assert data["open_trades"] == 0
        assert data["closed_trades"] == 0
        assert float(data["win_rate"]) == 0.0
        assert float(data["total_pnl"]) == 0.0
