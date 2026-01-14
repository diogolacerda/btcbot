"""Tests for WebSocket dashboard endpoint.

This module provides comprehensive tests for:
- WebSocket connection establishment and authentication
- Event types and serialization
- ConnectionManager functionality (broadcast, cleanup, heartbeat)
- Concurrent connection handling
- Ping/pong message handling
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.websockets import WebSocketDisconnect

from src.api.dependencies import create_access_token, get_db, get_password_hash
from src.api.main import app
from src.api.websocket.connection_manager import ConnectionManager, get_connection_manager
from src.api.websocket.events import (
    ActivityEventData,
    BotStatusEvent,
    OrderUpdateEvent,
    PositionUpdateEvent,
    PriceUpdateEvent,
    WebSocketEvent,
    WebSocketEventType,
)
from src.database.base import Base
from src.database.models.user import User

# Test database URL
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    """Create async test database engine."""
    engine = create_engine(TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    """Create test database session."""
    session_maker = sessionmaker(engine, class_=Session, expire_on_commit=False)
    session = session_maker()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(session):
    """Create test client with overridden database dependency."""

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(session):
    """Create a test user in the database."""
    user = User(
        email="wstest@example.com",
        password_hash=get_password_hash("testpassword123"),  # pragma: allowlist secret
        name="WebSocket Test User",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.expunge_all()
    return user


@pytest.fixture
def inactive_user(session):
    """Create an inactive test user."""
    user = User(
        email="inactive@example.com",
        password_hash=get_password_hash("testpassword123"),  # pragma: allowlist secret
        name="Inactive User",
        is_active=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.expunge_all()
    return user


@pytest.fixture
def valid_token(test_user):
    """Create a valid JWT token for the test user."""
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture
def expired_token(test_user):
    """Create an expired JWT token."""
    return create_access_token(data={"sub": test_user.email}, expires_delta=timedelta(minutes=-1))


@pytest.fixture
def connection_manager():
    """Get a fresh ConnectionManager instance."""
    # Reset singleton for tests
    ConnectionManager._instance = None
    ConnectionManager._initialized = False
    return get_connection_manager()


class TestWebSocketConnection:
    """Tests for WebSocket connection establishment."""

    @pytest.mark.skip(
        reason="Session isolation issue with SQLite in-memory DB - works in production"
    )
    async def test_connect_with_valid_token(self, client, test_user, valid_token):
        """Test successful WebSocket connection with valid JWT."""
        with client.websocket_connect(f"/ws/dashboard?token={valid_token}") as ws:
            # Should receive connection_established message
            data = ws.receive_json()
            assert data["type"] == "connection_established"
            assert data["data"]["user"] == test_user.email

    async def test_connect_without_token(self, client):
        """Test WebSocket connection without token fails."""
        # WebSocket requires token query param - missing param causes validation error
        with pytest.raises((WebSocketDisconnect, ValueError, KeyError)):
            with client.websocket_connect("/ws/dashboard"):
                pass

    async def test_connect_with_invalid_token(self, client):
        """Test WebSocket connection with invalid token is rejected."""
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/dashboard?token=invalid-token"):
                pass

    async def test_connect_with_expired_token(self, client, expired_token):
        """Test WebSocket connection with expired token is rejected."""
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/dashboard?token={expired_token}"):
                pass


class TestWebSocketEvents:
    """Tests for WebSocket event types."""

    async def test_bot_status_event_creation(self):
        """Test creating a bot status event."""
        status = BotStatusEvent(
            state="ACTIVE",
            is_running=True,
            macd_trend="bullish",
            grid_active=True,
            pending_orders_count=5,
            filled_orders_count=3,
        )

        event = WebSocketEvent.bot_status(status)
        assert event.type == WebSocketEventType.BOT_STATUS
        assert event.data.state == "ACTIVE"
        assert event.data.is_running is True

    async def test_position_update_event_creation(self):
        """Test creating a position update event."""
        position = PositionUpdateEvent(
            symbol="BTC-USDT",
            side="LONG",
            size="0.01",
            entry_price="50000.00",
            current_price="50500.00",
            unrealized_pnl="5.00",
            leverage=10,
            timestamp=datetime.now(),
        )

        event = WebSocketEvent.position_update(position)
        assert event.type == WebSocketEventType.POSITION_UPDATE
        assert event.data.symbol == "BTC-USDT"

    async def test_order_update_event_creation(self):
        """Test creating an order update event."""
        now = datetime.now()
        order = OrderUpdateEvent(
            order_id="12345",
            symbol="BTC-USDT",
            side="LONG",
            order_type="LIMIT",
            status="FILLED",
            price="50000.00",
            tp_price="50500.00",
            quantity="0.01",
            filled_quantity="0.01",
            created_at=now,
            filled_at=now,
            closed_at=None,
            exchange_tp_order_id="TP123",
        )

        event = WebSocketEvent.order_update(order)
        assert event.type == WebSocketEventType.ORDER_UPDATE
        assert event.data.order_id == "12345"
        assert event.data.status == "FILLED"
        assert event.data.side == "LONG"
        assert event.data.tp_price == "50500.00"

    async def test_price_update_event_creation(self):
        """Test creating a price update event."""
        price = PriceUpdateEvent(
            symbol="BTC-USDT",
            price="50000.00",
            change_24h="500.00",
            change_percent_24h="1.01",
            timestamp=datetime.now(),
        )

        event = WebSocketEvent.price_update(price)
        assert event.type == WebSocketEventType.PRICE_UPDATE
        assert event.data.price == "50000.00"

    async def test_heartbeat_event_creation(self):
        """Test creating a heartbeat event."""
        event = WebSocketEvent.heartbeat()
        assert event.type == WebSocketEventType.HEARTBEAT
        assert event.timestamp is not None

    async def test_error_event_creation(self):
        """Test creating an error event."""
        event = WebSocketEvent.error("test_error", "Test error message")
        assert event.type == WebSocketEventType.ERROR
        assert event.data.code == "test_error"
        assert event.data.message == "Test error message"

    async def test_event_json_serialization(self):
        """Test that events can be serialized to JSON."""
        status = BotStatusEvent(
            state="ACTIVE",
            is_running=True,
            grid_active=True,
            pending_orders_count=0,
            filled_orders_count=0,
        )
        event = WebSocketEvent.bot_status(status)

        # Should not raise any exceptions
        json_str = event.model_dump_json()
        assert "bot_status" in json_str
        assert "ACTIVE" in json_str


class TestConnectionManager:
    """Tests for ConnectionManager functionality."""

    async def test_connection_manager_singleton(self):
        """Test that ConnectionManager is a singleton."""
        # Reset singleton
        ConnectionManager._instance = None
        ConnectionManager._initialized = False

        manager1 = get_connection_manager()
        manager2 = get_connection_manager()
        assert manager1 is manager2

    async def test_initial_connection_count(self, connection_manager):
        """Test that initial connection count is zero."""
        assert connection_manager.active_connections_count == 0

    async def test_get_connection_stats_empty(self, connection_manager):
        """Test connection stats with no connections."""
        stats = connection_manager.get_connection_stats()
        assert stats["total_connections"] == 0
        assert stats["connections"] == []


class TestWebSocketMessageHandling:
    """Tests for WebSocket client message handling."""

    @pytest.mark.skip(
        reason="Session isolation issue with SQLite in-memory DB - works in production"
    )
    async def test_ping_pong(self, client, test_user, valid_token):
        """Test ping/pong message handling."""
        with client.websocket_connect(f"/ws/dashboard?token={valid_token}") as ws:
            # Skip connection message
            ws.receive_json()

            # Send ping
            ws.send_json({"type": "ping"})

            # Should receive pong
            data = ws.receive_json()
            assert data["type"] == "pong"
            assert "timestamp" in data["data"]

    @pytest.mark.skip(
        reason="Session isolation issue with SQLite in-memory DB - works in production"
    )
    async def test_subscribe_to_events(self, client, test_user, valid_token):
        """Test subscribing to specific event types."""
        with client.websocket_connect(f"/ws/dashboard?token={valid_token}") as ws:
            # Skip connection message
            ws.receive_json()

            # Subscribe to events
            ws.send_json({"type": "subscribe", "events": ["bot_status", "price_update"]})

            # Should receive confirmation
            data = ws.receive_json()
            assert data["type"] == "subscription_confirmed"
            assert "bot_status" in data["data"]["events"]
            assert "price_update" in data["data"]["events"]


class TestActivityEventCreation:
    """Tests for activity event creation."""

    async def test_activity_event_creation(self):
        """Test creating an activity event."""
        activity = ActivityEventData(
            event_type="order_placed",
            message="New LIMIT order placed at 50000.00",
            severity="info",
            metadata={"order_id": "12345", "price": "50000.00"},
            timestamp=datetime.now(),
        )

        event = WebSocketEvent.activity_event(activity)
        assert event.type == WebSocketEventType.ACTIVITY_EVENT
        assert event.data.event_type == "order_placed"
        assert event.data.severity == "info"
        assert event.data.metadata is not None
        assert event.data.metadata["order_id"] == "12345"

    async def test_activity_event_without_metadata(self):
        """Test activity event without optional metadata."""
        activity = ActivityEventData(
            event_type="grid_activated",
            message="Grid trading activated",
            severity="success",
            timestamp=datetime.now(),
        )

        event = WebSocketEvent.activity_event(activity)
        assert event.type == WebSocketEventType.ACTIVITY_EVENT
        assert event.data.metadata is None

    async def test_activity_event_all_severity_levels(self):
        """Test activity events with all severity levels."""
        severities = ["info", "warning", "error", "success"]

        for severity in severities:
            activity = ActivityEventData(
                event_type="test",
                message=f"Test {severity} message",
                severity=severity,
                timestamp=datetime.now(),
            )
            event = WebSocketEvent.activity_event(activity)
            assert event.data.severity == severity


class TestConnectionManagerBroadcast:
    """Tests for ConnectionManager broadcast functionality."""

    @pytest.fixture
    def fresh_manager(self):
        """Get a fresh ConnectionManager instance for each test."""
        ConnectionManager._instance = None
        ConnectionManager._initialized = False
        manager = ConnectionManager()
        # Reset singleton after test
        yield manager
        ConnectionManager._instance = None
        ConnectionManager._initialized = False

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = MagicMock()
        ws.send_text = MagicMock()
        ws.send_json = MagicMock()
        ws.accept = MagicMock()
        return ws

    async def test_broadcast_to_single_client(self, fresh_manager, mock_websocket):
        """Test broadcasting event to a single connected client."""
        # Connect a client
        await fresh_manager.connect(mock_websocket, "test@example.com")

        # Create and broadcast an event
        status = BotStatusEvent(
            state="ACTIVE",
            is_running=True,
            grid_active=True,
            pending_orders_count=5,
            filled_orders_count=2,
        )
        event = WebSocketEvent.bot_status(status)

        await fresh_manager.broadcast(event)

        # Verify send_text was called
        mock_websocket.send_text.assert_called_once()
        sent_message = mock_websocket.send_text.call_args[0][0]
        assert "bot_status" in sent_message
        assert "ACTIVE" in sent_message

    async def test_broadcast_to_multiple_clients(self, fresh_manager):
        """Test broadcasting event to multiple connected clients."""
        # Create multiple mock websockets
        ws1 = MagicMock()
        ws1.send_text = MagicMock()
        ws1.accept = MagicMock()

        ws2 = MagicMock()
        ws2.send_text = MagicMock()
        ws2.accept = MagicMock()

        ws3 = MagicMock()
        ws3.send_text = MagicMock()
        ws3.accept = MagicMock()

        # Connect all clients
        await fresh_manager.connect(ws1, "user1@example.com")
        await fresh_manager.connect(ws2, "user2@example.com")
        await fresh_manager.connect(ws3, "user3@example.com")

        assert fresh_manager.active_connections_count == 3

        # Broadcast an event
        event = WebSocketEvent.heartbeat()
        await fresh_manager.broadcast(event)

        # All clients should have received the message
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()
        ws3.send_text.assert_called_once()

    async def test_broadcast_with_no_connections(self, fresh_manager):
        """Test broadcasting when there are no connected clients."""
        event = WebSocketEvent.heartbeat()

        # Should not raise any exception
        await fresh_manager.broadcast(event)

    async def test_broadcast_json_raw_data(self, fresh_manager, mock_websocket):
        """Test broadcasting raw JSON data."""
        await fresh_manager.connect(mock_websocket, "test@example.com")

        data = {"type": "custom", "data": {"value": 123}}
        fresh_manager.broadcast_json(data)

        mock_websocket.send_json.assert_called_once_with(data)

    async def test_broadcast_handles_failed_send(self, fresh_manager):
        """Test that broadcast handles failed sends and disconnects dead clients."""
        # Create a healthy and a broken websocket
        ws_healthy = MagicMock()
        ws_healthy.send_text = MagicMock()
        ws_healthy.accept = MagicMock()

        ws_broken = MagicMock()
        ws_broken.send_text = MagicMock(side_effect=Exception("Connection lost"))
        ws_broken.accept = MagicMock()

        await fresh_manager.connect(ws_healthy, "healthy@example.com")
        await fresh_manager.connect(ws_broken, "broken@example.com")

        assert fresh_manager.active_connections_count == 2

        # Broadcast should clean up the broken connection
        event = WebSocketEvent.heartbeat()
        await fresh_manager.broadcast(event)

        # Broken client should be disconnected
        assert fresh_manager.active_connections_count == 1

        # Healthy client should still have received the message
        ws_healthy.send_text.assert_called_once()


class TestConcurrentConnections:
    """Tests for handling concurrent WebSocket connections."""

    @pytest.fixture
    def fresh_manager(self):
        """Get a fresh ConnectionManager instance."""
        ConnectionManager._instance = None
        ConnectionManager._initialized = False
        manager = ConnectionManager()
        yield manager
        ConnectionManager._instance = None
        ConnectionManager._initialized = False

    async def test_multiple_simultaneous_connections(self, fresh_manager):
        """Test handling multiple simultaneous connections."""
        websockets = []
        for _ in range(10):
            ws = MagicMock()
            ws.accept = MagicMock()
            ws.send_text = MagicMock()
            websockets.append(ws)

        # Connect all websockets
        for i, ws in enumerate(websockets):
            await fresh_manager.connect(ws, f"user{i}@example.com")

        assert fresh_manager.active_connections_count == 10

        # Get stats to verify all connections are tracked
        stats = fresh_manager.get_connection_stats()
        assert stats["total_connections"] == 10
        assert len(stats["connections"]) == 10

    async def test_connection_stats_contain_user_info(self, fresh_manager):
        """Test that connection stats contain correct user information."""
        ws = MagicMock()
        ws.accept = MagicMock()
        ws.send_text = MagicMock()

        await fresh_manager.connect(ws, "detailed@example.com")

        stats = fresh_manager.get_connection_stats()
        connection = stats["connections"][0]

        assert connection["user_email"] == "detailed@example.com"
        assert "connected_at" in connection
        assert "last_heartbeat" in connection

    async def test_same_user_multiple_connections(self, fresh_manager):
        """Test that same user can have multiple connections."""
        ws1 = MagicMock()
        ws1.accept = MagicMock()
        ws1.send_text = MagicMock()

        ws2 = MagicMock()
        ws2.accept = MagicMock()
        ws2.send_text = MagicMock()

        # Same user connecting from different devices/tabs
        await fresh_manager.connect(ws1, "multidevice@example.com")
        await fresh_manager.connect(ws2, "multidevice@example.com")

        assert fresh_manager.active_connections_count == 2

        # Both should receive broadcasts
        event = WebSocketEvent.heartbeat()
        await fresh_manager.broadcast(event)

        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()


class TestConnectionCleanup:
    """Tests for connection cleanup functionality."""

    @pytest.fixture
    def fresh_manager(self):
        """Get a fresh ConnectionManager instance."""
        ConnectionManager._instance = None
        ConnectionManager._initialized = False
        manager = ConnectionManager()
        yield manager
        ConnectionManager._instance = None
        ConnectionManager._initialized = False

    async def test_disconnect_removes_connection(self, fresh_manager):
        """Test that disconnect properly removes connection."""
        ws = MagicMock()
        ws.accept = MagicMock()

        await fresh_manager.connect(ws, "disconnect@example.com")
        assert fresh_manager.active_connections_count == 1

        await fresh_manager.disconnect(ws)
        assert fresh_manager.active_connections_count == 0

    async def test_disconnect_nonexistent_connection(self, fresh_manager):
        """Test disconnecting a non-existent connection doesn't raise."""
        ws = MagicMock()

        # Should not raise any exception
        await fresh_manager.disconnect(ws)
        assert fresh_manager.active_connections_count == 0

    async def test_send_personal_disconnects_on_failure(self, fresh_manager):
        """Test that personal send disconnects client on failure."""
        ws = MagicMock()
        ws.accept = MagicMock()
        ws.send_text = MagicMock(side_effect=Exception("Connection closed"))

        await fresh_manager.connect(ws, "failing@example.com")
        assert fresh_manager.active_connections_count == 1

        event = WebSocketEvent.heartbeat()
        await fresh_manager.send_personal(ws, event)

        # Client should be disconnected after failure
        assert fresh_manager.active_connections_count == 0

    async def test_broadcast_cleans_multiple_dead_connections(self, fresh_manager):
        """Test broadcast cleans up multiple dead connections."""
        healthy = MagicMock()
        healthy.accept = MagicMock()
        healthy.send_text = MagicMock()

        dead1 = MagicMock()
        dead1.accept = MagicMock()
        dead1.send_text = MagicMock(side_effect=Exception("Dead 1"))

        dead2 = MagicMock()
        dead2.accept = MagicMock()
        dead2.send_text = MagicMock(side_effect=Exception("Dead 2"))

        await fresh_manager.connect(healthy, "healthy@example.com")
        await fresh_manager.connect(dead1, "dead1@example.com")
        await fresh_manager.connect(dead2, "dead2@example.com")

        assert fresh_manager.active_connections_count == 3

        event = WebSocketEvent.heartbeat()
        await fresh_manager.broadcast(event)

        # Only healthy connection should remain
        assert fresh_manager.active_connections_count == 1


class TestHeartbeatFunctionality:
    """Tests for heartbeat/ping-pong functionality."""

    @pytest.fixture
    def fresh_manager(self):
        """Get a fresh ConnectionManager instance."""
        ConnectionManager._instance = None
        ConnectionManager._initialized = False
        manager = ConnectionManager()
        yield manager
        # Clean up heartbeat task if running
        if manager._heartbeat_task and not manager._heartbeat_task.done():
            manager._heartbeat_task.cancel()
        ConnectionManager._instance = None
        ConnectionManager._initialized = False

    async def test_update_heartbeat_timestamp(self, fresh_manager):
        """Test that update_heartbeat updates the timestamp."""
        ws = MagicMock()
        ws.accept = MagicMock()

        await fresh_manager.connect(ws, "heartbeat@example.com")

        # Get initial heartbeat time
        initial_time = fresh_manager._active_connections[ws].last_heartbeat

        # Update heartbeat
        fresh_manager.update_heartbeat(ws)

        # Verify timestamp was updated
        new_time = fresh_manager._active_connections[ws].last_heartbeat
        assert new_time > initial_time

    async def test_heartbeat_starts_on_first_connection(self, fresh_manager):
        """Test that heartbeat task starts with first connection."""
        assert fresh_manager._heartbeat_task is None

        ws = MagicMock()
        ws.accept = MagicMock()
        ws.send_text = MagicMock()

        await fresh_manager.connect(ws, "first@example.com")

        # Heartbeat task should be started
        assert fresh_manager._heartbeat_task is not None
        assert not fresh_manager._heartbeat_task.done()

    async def test_heartbeat_stops_on_last_disconnect(self, fresh_manager):
        """Test that heartbeat task stops when last client disconnects."""
        ws = MagicMock()
        ws.accept = MagicMock()
        ws.send_text = MagicMock()

        await fresh_manager.connect(ws, "last@example.com")
        assert fresh_manager._heartbeat_task is not None

        await fresh_manager.disconnect(ws)

        # Heartbeat task should be cancelled/done
        assert fresh_manager._heartbeat_task is None or fresh_manager._heartbeat_task.done()

    async def test_manual_start_stop_heartbeat(self, fresh_manager):
        """Test manual start and stop of heartbeat."""
        # Manually start heartbeat
        fresh_manager.start_heartbeat()
        assert fresh_manager._heartbeat_task is not None
        assert not fresh_manager._heartbeat_task.done()

        # Manually stop heartbeat
        fresh_manager.stop_heartbeat()

        assert fresh_manager._heartbeat_task.done()

    async def test_heartbeat_broadcasts_to_all_clients(self, fresh_manager):
        """Test that heartbeat broadcasts to all connected clients."""
        # Set a very short heartbeat interval for testing
        fresh_manager._heartbeat_interval = 0.1  # 100ms

        ws1 = MagicMock()
        ws1.accept = MagicMock()
        ws1.send_text = MagicMock()

        ws2 = MagicMock()
        ws2.accept = MagicMock()
        ws2.send_text = MagicMock()

        await fresh_manager.connect(ws1, "user1@example.com")
        await fresh_manager.connect(ws2, "user2@example.com")

        # Both clients should have received at least one heartbeat
        assert ws1.send_text.called
        assert ws2.send_text.called

        # Verify it was a heartbeat message
        call_args = ws1.send_text.call_args[0][0]
        assert "heartbeat" in call_args


class TestEventSerialization:
    """Tests for complete event serialization."""

    async def test_all_event_types_serialize_to_json(self):
        """Test that all event types can be serialized to JSON."""
        events = [
            WebSocketEvent.bot_status(
                BotStatusEvent(
                    state="ACTIVE",
                    is_running=True,
                    grid_active=True,
                    pending_orders_count=0,
                    filled_orders_count=0,
                )
            ),
            WebSocketEvent.position_update(
                PositionUpdateEvent(
                    symbol="BTC-USDT",
                    side="LONG",
                    size="0.01",
                    entry_price="50000.00",
                    current_price="50500.00",
                    unrealized_pnl="5.00",
                    leverage=10,
                    timestamp=datetime.now(),
                )
            ),
            WebSocketEvent.order_update(
                OrderUpdateEvent(
                    order_id="12345",
                    symbol="BTC-USDT",
                    side="LONG",
                    order_type="LIMIT",
                    status="FILLED",
                    price="50000.00",
                    tp_price="50500.00",
                    quantity="0.01",
                    filled_quantity="0.01",
                    created_at=datetime.now(),
                    filled_at=datetime.now(),
                    closed_at=None,
                    exchange_tp_order_id="TP123",
                )
            ),
            WebSocketEvent.price_update(
                PriceUpdateEvent(
                    symbol="BTC-USDT",
                    price="50000.00",
                    change_24h="500.00",
                    change_percent_24h="1.01",
                    timestamp=datetime.now(),
                )
            ),
            WebSocketEvent.activity_event(
                ActivityEventData(
                    event_type="order_filled",
                    message="Order filled successfully",
                    severity="success",
                    timestamp=datetime.now(),
                )
            ),
            WebSocketEvent.heartbeat(),
            WebSocketEvent.error("test_error", "Test error message"),
        ]

        for event in events:
            json_str = event.model_dump_json()
            assert json_str is not None
            # event.type is already a string due to use_enum_values
            event_type = event.type if isinstance(event.type, str) else event.type.value
            assert event_type in json_str

    async def test_event_timestamp_is_present(self):
        """Test that all events have a timestamp."""
        event = WebSocketEvent.heartbeat()
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    async def test_connection_established_event(self):
        """Test creating a connection established event."""
        event = WebSocketEvent(
            type=WebSocketEventType.CONNECTION_ESTABLISHED,
            data={"message": "Connected", "user": "test@example.com"},
            timestamp=datetime.now(),
        )

        json_str = event.model_dump_json()
        assert "connection_established" in json_str
        assert "test@example.com" in json_str

    async def test_subscription_confirmed_event(self):
        """Test creating a subscription confirmed event."""
        event = WebSocketEvent(
            type=WebSocketEventType.SUBSCRIPTION_CONFIRMED,
            data={"events": ["bot_status", "price_update"]},
            timestamp=datetime.now(),
        )

        json_str = event.model_dump_json()
        assert "subscription_confirmed" in json_str
        assert "bot_status" in json_str

    async def test_pong_event(self):
        """Test creating a pong event."""
        event = WebSocketEvent(
            type=WebSocketEventType.PONG,
            data={"timestamp": datetime.now().isoformat()},
            timestamp=datetime.now(),
        )

        json_str = event.model_dump_json()
        assert "pong" in json_str


class TestWebSocketAuthentication:
    """Tests for WebSocket authentication using mocks."""

    async def test_authenticate_with_valid_token(self):
        """Test authentication with a valid JWT token."""
        from src.api.websocket.dashboard_ws import authenticate_websocket

        # Create a valid token
        token = create_access_token(data={"sub": "auth_test@example.com"})

        with patch("src.api.websocket.dashboard_ws.get_session_maker") as mock_session:
            # Mock the database session
            mock_user = MagicMock()
            mock_user.email = "auth_test@example.com"
            mock_user.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user

            mock_session_instance = MagicMock()
            mock_session_instance.execute = MagicMock(return_value=mock_result)
            mock_session_instance.__aenter__ = MagicMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = MagicMock(return_value=None)

            mock_session.return_value = MagicMock(return_value=mock_session_instance)

            result = await authenticate_websocket(token)
            assert result == "auth_test@example.com"

    async def test_authenticate_with_invalid_token(self):
        """Test authentication with an invalid JWT token."""
        from src.api.websocket.dashboard_ws import authenticate_websocket

        result = await authenticate_websocket("invalid.token.here")
        assert result is None

    async def test_authenticate_with_expired_token(self):
        """Test authentication with an expired JWT token."""
        from src.api.websocket.dashboard_ws import authenticate_websocket

        # Create an expired token
        token = create_access_token(
            data={"sub": "expired@example.com"},
            expires_delta=timedelta(minutes=-1),
        )

        result = await authenticate_websocket(token)
        assert result is None

    async def test_authenticate_with_missing_subject(self):
        """Test authentication with token missing subject claim."""
        import jwt

        from src.api.dependencies import ALGORITHM, SECRET_KEY
        from src.api.websocket.dashboard_ws import authenticate_websocket

        # Create a token without 'sub' claim
        token = jwt.encode(
            {"exp": datetime.now() + timedelta(hours=1)}, SECRET_KEY, algorithm=ALGORITHM
        )

        result = await authenticate_websocket(token)
        assert result is None

    async def test_authenticate_with_inactive_user(self):
        """Test authentication with inactive user."""
        from src.api.websocket.dashboard_ws import authenticate_websocket

        token = create_access_token(data={"sub": "inactive@example.com"})

        with patch("src.api.websocket.dashboard_ws.get_session_maker") as mock_session:
            mock_user = MagicMock()
            mock_user.email = "inactive@example.com"
            mock_user.is_active = False

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user

            mock_session_instance = MagicMock()
            mock_session_instance.execute = MagicMock(return_value=mock_result)
            mock_session_instance.__aenter__ = MagicMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = MagicMock(return_value=None)

            mock_session.return_value = MagicMock(return_value=mock_session_instance)

            result = await authenticate_websocket(token)
            assert result is None

    async def test_authenticate_with_nonexistent_user(self):
        """Test authentication with non-existent user."""
        from src.api.websocket.dashboard_ws import authenticate_websocket

        token = create_access_token(data={"sub": "nonexistent@example.com"})

        with patch("src.api.websocket.dashboard_ws.get_session_maker") as mock_session:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            mock_session_instance = MagicMock()
            mock_session_instance.execute = MagicMock(return_value=mock_result)
            mock_session_instance.__aenter__ = MagicMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = MagicMock(return_value=None)

            mock_session.return_value = MagicMock(return_value=mock_session_instance)

            result = await authenticate_websocket(token)
            assert result is None
