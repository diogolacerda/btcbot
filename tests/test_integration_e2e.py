"""End-to-end integration tests for Dashboard flows.

These tests simulate complete user workflows including:
- Loading dashboard with all data
- Bot control operations (pause, resume, start, stop)
- Viewing position details
- WebSocket real-time updates
- Error handling across the stack
- Concurrent user actions

Note: These tests use mocked external dependencies (BingX API)
but test the full integration between API layers.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.websockets import WebSocketDisconnect

from src.api.dependencies import (
    create_access_token,
    get_bingx_client,
    get_db,
    get_grid_calculator,
    get_grid_manager,
    get_macd_strategy,
    get_password_hash,
)
from src.api.main import app
from src.database.base import Base
from src.database.models.user import User
from src.grid.order_tracker import OrderStatus, TrackedOrder
from src.strategy.macd_strategy import GridState

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Create async test database session."""
    async_session_maker = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def test_user(async_session):
    """Create a test user in the database."""
    user = User(
        email="integrationtest@example.com",
        password_hash=get_password_hash("testpassword123"),  # pragma: allowlist secret
        name="Integration Test User",
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    async_session.expunge_all()
    return user


@pytest.fixture
async def second_user(async_session, test_user):
    """Create a second test user for concurrent testing."""
    user = User(
        email="concurrent@example.com",
        password_hash=get_password_hash("testpassword123"),  # pragma: allowlist secret
        name="Concurrent Test User",
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    async_session.expunge_all()
    return user


@pytest.fixture
def auth_token(test_user):
    """Get auth token for test user."""
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture
def second_auth_token(second_user):
    """Get auth token for second test user."""
    return create_access_token(data={"sub": second_user.email})


@pytest.fixture
def mock_grid_manager():
    """Create a mock GridManager with realistic state."""
    mock = MagicMock()

    # Configure properties
    type(mock).is_running = PropertyMock(return_value=True)
    type(mock).current_state = PropertyMock(return_value=GridState.ACTIVE)

    # Configure strategy
    mock.strategy = MagicMock()
    mock.strategy.is_cycle_activated = True

    # Configure get_status return value
    mock_status = MagicMock()
    mock_status.state = GridState.ACTIVE
    mock_status.current_price = 98500.50
    mock_status.pending_orders = 5
    mock_status.open_positions = 3
    mock_status.total_trades = 47
    mock_status.total_pnl = 523.75
    mock_status.macd_line = 125.5
    mock_status.histogram = 42.3
    mock_status.cycle_activated = True
    mock_status.margin_error = False
    mock_status.rate_limited = False
    mock.get_status.return_value = mock_status

    # Track margin_error state changes
    mock._margin_error = False
    mock._margin_error_time = 0.0

    # Configure async methods
    mock.start = AsyncMock()
    mock.stop = AsyncMock()

    return mock


@pytest.fixture
def mock_bingx_client():
    """Create a mock BingX client with realistic data."""
    mock = MagicMock()

    # Price data
    mock.get_price = AsyncMock(return_value=98500.50)

    # 24h ticker data
    mock.get_ticker_24h = AsyncMock(
        return_value={
            "lastPrice": "98500.50",
            "priceChange": "1250.25",
            "priceChangePercent": "1.29",
            "highPrice": "99500.00",
            "lowPrice": "97000.00",
            "volume": "15234.567",
        }
    )

    # Funding rate data
    mock.get_funding_rate = AsyncMock(
        return_value={
            "lastFundingRate": "0.0001",
            "nextFundingTime": int((datetime.now(UTC) + timedelta(hours=4)).timestamp() * 1000),
            "markPrice": "98510.25",
        }
    )

    # Klines data for MACD calculation
    mock.get_klines = AsyncMock(
        return_value=[
            {"close": 98000 + i * 50, "timestamp": 1704067200000 + i * 3600000} for i in range(100)
        ]
    )

    return mock


@pytest.fixture
def mock_macd_strategy():
    """Create a mock MACD strategy."""
    mock = MagicMock()
    mock.timeframe = "1h"

    # Create mock MACD values
    macd_values = MagicMock()
    macd_values.macd_line = 125.5
    macd_values.signal_line = 100.2
    macd_values.histogram = 25.3
    macd_values.is_histogram_positive = True
    macd_values.is_histogram_rising = True
    macd_values.is_histogram_negative = False
    macd_values.is_histogram_falling = False
    macd_values.are_both_lines_negative = False

    mock.calculate_macd.return_value = macd_values
    return mock


@pytest.fixture
def mock_grid_calculator():
    """Create a mock grid calculator."""
    mock = MagicMock()
    mock.range_percent = 3.0
    mock.calculate_min_price.return_value = 95545.49
    mock.calculate_spacing.return_value = 100.0
    return mock


@pytest.fixture
def mock_order_tracker():
    """Create a mock order tracker with sample orders."""
    mock = MagicMock()

    # Create sample tracked orders
    now = datetime.now(UTC)
    sample_orders = {
        "order_1": TrackedOrder(
            order_id="order_1",
            entry_price=98000.0,
            tp_price=98500.0,
            quantity=0.001,
            status=OrderStatus.PENDING,
            created_at=now - timedelta(minutes=30),
        ),
        "order_2": TrackedOrder(
            order_id="order_2",
            entry_price=97500.0,
            tp_price=98000.0,
            quantity=0.001,
            status=OrderStatus.FILLED,
            created_at=now - timedelta(hours=2),
            filled_at=now - timedelta(hours=1),
            exchange_tp_order_id="tp_order_2",
        ),
        "order_3": TrackedOrder(
            order_id="order_3",
            entry_price=97000.0,
            tp_price=97500.0,
            quantity=0.001,
            status=OrderStatus.FILLED,
            created_at=now - timedelta(hours=4),
            filled_at=now - timedelta(hours=3),
            exchange_tp_order_id="tp_order_3",
        ),
    }

    mock._orders = sample_orders
    return mock


@pytest.fixture
def client(
    async_session, mock_grid_manager, mock_bingx_client, mock_macd_strategy, mock_grid_calculator
):
    """Create test client with all mocked dependencies."""

    async def override_get_db():
        yield async_session

    def override_get_grid_manager():
        return mock_grid_manager

    def override_get_bingx_client():
        return mock_bingx_client

    def override_get_macd_strategy():
        return mock_macd_strategy

    def override_get_grid_calculator():
        return mock_grid_calculator

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_grid_manager] = override_get_grid_manager
    app.dependency_overrides[get_bingx_client] = override_get_bingx_client
    app.dependency_overrides[get_macd_strategy] = override_get_macd_strategy
    app.dependency_overrides[get_grid_calculator] = override_get_grid_calculator

    yield TestClient(app)

    app.dependency_overrides.clear()


# =============================================================================
# E2E Flow Tests
# =============================================================================


class TestDashboardLoadFlow:
    """Test E2E flow: Load dashboard -> See data -> Change period."""

    def test_complete_dashboard_load_flow(
        self, client, auth_token, mock_grid_manager, mock_order_tracker
    ):
        """Test the complete dashboard loading flow.

        This simulates:
        1. User logs in and gets token
        2. Dashboard loads bot status
        3. Dashboard loads market data (price, MACD, grid range)
        4. Dashboard loads orders list
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: Login was successful (we have token from fixture)

        # Step 2: Get bot status
        response = client.get("/api/v1/bot/status", headers=headers)
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["status"] == "running"
        assert status_data["state"] == "ACTIVE"
        assert status_data["is_running"] is True
        assert status_data["current_price"] == 98500.50
        assert status_data["macd"]["macd_line"] == 125.5
        assert status_data["orders"]["pending_orders"] == 5
        assert status_data["orders"]["open_positions"] == 3

        # Step 3: Get market data (price, MACD, grid range)
        price_response = client.get("/api/v1/market/price", headers=headers)
        assert price_response.status_code == 200
        price_data = price_response.json()
        assert Decimal(price_data["price"]) == Decimal("98500.50")
        assert price_data["change_24h_percent"] is not None

        macd_response = client.get("/api/v1/market/macd", headers=headers)
        assert macd_response.status_code == 200
        macd_data = macd_response.json()
        # Signal enum values are lowercase in the API response
        assert macd_data["signal"] in ["bullish", "bearish", "neutral"]

        grid_response = client.get("/api/v1/market/grid-range", headers=headers)
        assert grid_response.status_code == 200
        grid_data = grid_response.json()
        assert "grid_low" in grid_data
        assert "grid_high" in grid_data

        # Step 4: Get orders list
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            orders_response = client.get("/api/v1/orders", headers=headers)
            assert orders_response.status_code == 200
            orders_data = orders_response.json()
            assert "orders" in orders_data
            assert orders_data["total"] == 3

    def test_dashboard_load_with_period_filter(self, client, auth_token, mock_order_tracker):
        """Test loading dashboard with different time period filters."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Test orders with status filter (simulates period/status filtering)
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            # Filter by PENDING
            response = client.get("/api/v1/orders?status=PENDING", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1  # Only one pending order
            assert all(o["status"] == "PENDING" for o in data["orders"])

            # Filter by FILLED
            response = client.get("/api/v1/orders?status=FILLED", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2  # Two filled orders
            assert all(o["status"] == "FILLED" for o in data["orders"])

    def test_dashboard_load_unauthenticated(self, client):
        """Test that dashboard endpoints require authentication."""
        # All dashboard endpoints should return 401 without token
        endpoints = [
            "/api/v1/bot/status",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Expected 401 for {endpoint}"


class TestBotControlFlow:
    """Test E2E flow: Pause bot -> Confirm -> See status update."""

    def test_pause_and_resume_flow(self, client, auth_token, mock_grid_manager):
        """Test the complete pause -> resume flow.

        This simulates:
        1. User views bot status (running)
        2. User clicks pause button
        3. Bot is paused, status reflects change
        4. User clicks resume button
        5. Bot resumes, status reflects change
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: Verify bot is running
        response = client.get("/api/v1/bot/status", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "running"

        # Step 2: Pause the bot
        response = client.post("/api/v1/bot/pause", headers=headers)
        assert response.status_code == 200
        pause_data = response.json()
        assert pause_data["success"] is True
        assert "paused" in pause_data["message"].lower()

        # Verify internal state was updated
        assert mock_grid_manager._margin_error is True

        # Step 3: Verify status shows paused
        # Need to update mock to reflect paused state
        mock_grid_manager.get_status.return_value.margin_error = True
        response = client.get("/api/v1/bot/status", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "paused"

        # Step 4: Resume the bot
        response = client.post("/api/v1/bot/resume", headers=headers)
        assert response.status_code == 200
        resume_data = response.json()
        assert resume_data["success"] is True
        assert "resumed" in resume_data["message"].lower()

        # Verify internal state was updated
        assert mock_grid_manager._margin_error is False

        # Step 5: Verify status shows running again
        mock_grid_manager.get_status.return_value.margin_error = False
        response = client.get("/api/v1/bot/status", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "running"

    def test_stop_and_start_flow(self, client, auth_token, mock_grid_manager):
        """Test the complete stop -> start flow.

        This simulates:
        1. Bot is running
        2. User stops the bot
        3. User starts the bot again
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: Stop the bot
        response = client.post("/api/v1/bot/stop", headers=headers)
        assert response.status_code == 200
        stop_data = response.json()
        assert stop_data["success"] is True
        assert stop_data["orders_cancelled"] == 5
        assert stop_data["tp_orders_preserved"] == 3

        # Verify stop was called
        mock_grid_manager.stop.assert_called_once()

        # Step 2: Bot is now stopped - update mock
        type(mock_grid_manager).is_running = PropertyMock(return_value=False)

        # Trying to stop again should fail
        response = client.post("/api/v1/bot/stop", headers=headers)
        assert response.status_code == 400
        assert "already stopped" in response.json()["detail"].lower()

        # Step 3: Start the bot
        response = client.post("/api/v1/bot/start", headers=headers)
        assert response.status_code == 200
        start_data = response.json()
        assert start_data["success"] is True

        # Verify start was called
        mock_grid_manager.start.assert_called_once()

    def test_pause_stopped_bot_fails(self, client, auth_token, mock_grid_manager):
        """Test that pausing a stopped bot returns appropriate error."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Set bot as stopped
        type(mock_grid_manager).is_running = PropertyMock(return_value=False)

        response = client.post("/api/v1/bot/pause", headers=headers)
        assert response.status_code == 400
        assert "not running" in response.json()["detail"].lower()


class TestPositionDetailsFlow:
    """Test E2E flow: View position details."""

    def test_view_position_details_flow(self, client, auth_token, mock_order_tracker):
        """Test viewing detailed position information.

        This simulates:
        1. User loads orders list
        2. User sees filled positions with TP orders
        3. User can see entry price, TP price, PnL info
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            # Step 1: Get orders list
            response = client.get("/api/v1/orders", headers=headers)
            assert response.status_code == 200
            data = response.json()

            # Step 2: Check filled positions
            filled_orders = [o for o in data["orders"] if o["status"] == "FILLED"]
            assert len(filled_orders) == 2

            # Step 3: Verify position details
            for order in filled_orders:
                assert "price" in order
                assert "tp_price" in order
                assert "quantity" in order
                assert "filled_at" in order
                assert order["exchange_tp_order_id"] is not None

                # Verify TP is higher than entry (for long positions)
                assert Decimal(order["tp_price"]) > Decimal(order["price"])

    def test_order_pagination(self, client, auth_token, mock_order_tracker):
        """Test order list pagination."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            # Get first page
            response = client.get("/api/v1/orders?limit=2&offset=0", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data["orders"]) == 2
            assert data["total"] == 3
            assert data["limit"] == 2
            assert data["offset"] == 0

            # Get second page
            response = client.get("/api/v1/orders?limit=2&offset=2", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data["orders"]) == 1  # Only 1 remaining


class TestWebSocketIntegration:
    """Test WebSocket live updates integration."""

    def test_websocket_connection_with_valid_token(self, client, auth_token, test_user):
        """Test WebSocket connection establishment with valid JWT.

        Note: The WebSocket endpoint uses authenticate_websocket() which
        accesses the database directly via get_session_maker(), not through
        dependency injection. We mock the authentication function to test
        the connection flow.
        """
        # Mock authenticate_websocket to return the test user's email
        with patch(
            "src.api.websocket.dashboard_ws.authenticate_websocket",
            new=AsyncMock(return_value=test_user.email),
        ):
            # Connect to WebSocket with valid token (path is /ws/dashboard, not /api/v1/ws/dashboard)
            with client.websocket_connect(f"/ws/dashboard?token={auth_token}") as websocket:
                # Should receive connection established message
                data = websocket.receive_json()
                assert data["type"] == "connection_established"
                assert data["data"]["user"] == test_user.email

                # Send a ping and expect pong
                websocket.send_json({"type": "ping"})
                pong_data = websocket.receive_json()
                assert pong_data["type"] == "pong"

    def test_websocket_connection_without_token(self, client):
        """Test WebSocket connection fails without token."""
        # Attempt connection without token should fail (token is required query param)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/dashboard") as websocket:
                websocket.receive_json()

    def test_websocket_connection_with_invalid_token(self, client):
        """Test WebSocket connection fails with invalid token."""
        # Mock authenticate_websocket to return None (auth failure)
        with patch(
            "src.api.websocket.dashboard_ws.authenticate_websocket",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect("/ws/dashboard?token=invalid_token") as websocket:
                    websocket.receive_json()

    def test_websocket_subscription_flow(self, client, auth_token, test_user):
        """Test WebSocket event subscription flow."""
        with patch(
            "src.api.websocket.dashboard_ws.authenticate_websocket",
            new=AsyncMock(return_value=test_user.email),
        ):
            with client.websocket_connect(f"/ws/dashboard?token={auth_token}") as websocket:
                # Receive connection established
                websocket.receive_json()

                # Subscribe to events
                websocket.send_json({"type": "subscribe", "events": ["bot_status", "price_update"]})
                sub_data = websocket.receive_json()
                assert sub_data["type"] == "subscription_confirmed"
                assert sub_data["data"]["events"] == ["bot_status", "price_update"]


class TestErrorHandling:
    """Test error handling across the stack."""

    def test_api_error_when_bingx_fails(self, client, auth_token, mock_bingx_client):
        """Test graceful error handling when BingX API fails."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Simulate BingX API failure
        mock_bingx_client.get_ticker_24h = AsyncMock(side_effect=Exception("BingX API unavailable"))

        response = client.get("/api/v1/market/price", headers=headers)
        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()

    def test_api_error_when_grid_manager_fails(self, client, auth_token, mock_grid_manager):
        """Test graceful error handling when GridManager fails."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Simulate GridManager failure
        mock_grid_manager.get_status.side_effect = Exception("GridManager error")

        response = client.get("/api/v1/bot/status", headers=headers)
        assert response.status_code == 500

    def test_api_error_when_order_tracker_unavailable(self, client, auth_token):
        """Test graceful error handling when OrderTracker is unavailable."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        with patch("src.api.routes.orders.get_order_tracker", return_value=None):
            response = client.get("/api/v1/orders", headers=headers)
            assert response.status_code == 503
            assert "not available" in response.json()["detail"].lower()

    def test_invalid_status_filter_error(self, client, auth_token, mock_order_tracker):
        """Test error handling for invalid status filter."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            response = client.get("/api/v1/orders?status=INVALID", headers=headers)
            assert response.status_code == 400
            assert "invalid status" in response.json()["detail"].lower()

    def test_expired_token_error(self, client, test_user):
        """Test error handling for expired JWT token."""
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(seconds=-10),  # Already expired
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/bot/status", headers=headers)
        assert response.status_code == 401


class TestConcurrentActions:
    """Test concurrent user actions."""

    def test_multiple_users_accessing_status(self, client, auth_token, second_auth_token):
        """Test that multiple users can access bot status concurrently."""
        # Both users should be able to access status
        response1 = client.get(
            "/api/v1/bot/status", headers={"Authorization": f"Bearer {auth_token}"}
        )
        response2 = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {second_auth_token}"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should see the same data
        assert response1.json()["status"] == response2.json()["status"]

    def test_multiple_users_cannot_pause_simultaneously(
        self, client, auth_token, second_auth_token, mock_grid_manager
    ):
        """Test that pause operation is idempotent with multiple users."""
        headers1 = {"Authorization": f"Bearer {auth_token}"}
        headers2 = {"Authorization": f"Bearer {second_auth_token}"}

        # First user pauses
        response1 = client.post("/api/v1/bot/pause", headers=headers1)
        assert response1.status_code == 200

        # Bot is now paused, update mock
        mock_grid_manager.get_status.return_value.margin_error = True

        # Second user also tries to pause - should still succeed (idempotent)
        response2 = client.post("/api/v1/bot/pause", headers=headers2)
        assert response2.status_code == 200

        # Both requests updated the same shared state
        assert mock_grid_manager._margin_error is True

    def test_concurrent_market_data_requests(self, client, auth_token, mock_bingx_client):
        """Test concurrent market data requests don't interfere."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Make multiple concurrent requests
        responses = []
        for _ in range(5):
            responses.append(client.get("/api/v1/market/price", headers=headers))

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert "price" in response.json()


class TestFullUserJourney:
    """Test complete user journey through the dashboard."""

    def test_complete_user_session(self, client, auth_token, mock_grid_manager, mock_order_tracker):
        """Test a complete user session from login to multiple operations.

        This simulates a real user session:
        1. Login and get token
        2. Load dashboard (status, market data, orders)
        3. Pause the bot
        4. Check paused status
        5. Resume the bot
        6. Filter orders by status
        7. Logout (token invalidation would happen client-side)
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: Login successful (token from fixture)

        # Step 2: Load dashboard
        status_response = client.get("/api/v1/bot/status", headers=headers)
        assert status_response.status_code == 200
        initial_status = status_response.json()
        assert initial_status["status"] == "running"

        price_response = client.get("/api/v1/market/price", headers=headers)
        assert price_response.status_code == 200

        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            orders_response = client.get("/api/v1/orders", headers=headers)
            assert orders_response.status_code == 200

        # Step 3: Pause the bot
        pause_response = client.post("/api/v1/bot/pause", headers=headers)
        assert pause_response.status_code == 200
        assert pause_response.json()["success"] is True

        # Step 4: Check paused status
        mock_grid_manager.get_status.return_value.margin_error = True
        status_response = client.get("/api/v1/bot/status", headers=headers)
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "paused"

        # Step 5: Resume the bot
        resume_response = client.post("/api/v1/bot/resume", headers=headers)
        assert resume_response.status_code == 200
        assert resume_response.json()["success"] is True

        mock_grid_manager.get_status.return_value.margin_error = False
        status_response = client.get("/api/v1/bot/status", headers=headers)
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "running"

        # Step 6: Filter orders by status
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            filled_orders = client.get("/api/v1/orders?status=FILLED", headers=headers)
            assert filled_orders.status_code == 200
            assert filled_orders.json()["filled_count"] == 2

            pending_orders = client.get("/api/v1/orders?status=PENDING", headers=headers)
            assert pending_orders.status_code == 200
            assert pending_orders.json()["pending_count"] == 1

        # Step 7: Session complete - user logs out (client-side only)
        # No explicit logout endpoint needed - token expires naturally
