"""Tests for bot control API endpoints."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_db, get_grid_manager
from src.api.main import app
from src.database.base import Base
from src.database.models.user import User
from src.strategy.macd_strategy import GridState

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


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
    from src.api.dependencies import get_password_hash

    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User",
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    async_session.expunge_all()
    return user


@pytest.fixture
def mock_grid_manager():
    """Create a mock GridManager."""
    mock = MagicMock()

    # Configure is_running property
    type(mock).is_running = PropertyMock(return_value=True)

    # Configure current_state property
    type(mock).current_state = PropertyMock(return_value=GridState.ACTIVE)

    # Configure strategy
    mock.strategy = MagicMock()
    mock.strategy.is_cycle_activated = True

    # Configure tracker with count properties
    mock.tracker = MagicMock()
    mock.tracker.pending_count = 5
    mock.tracker.position_count = 3

    # Configure get_status return value
    mock_status = MagicMock()
    mock_status.state = GridState.ACTIVE
    mock_status.current_price = 100000.0
    mock_status.pending_orders = 5
    mock_status.open_positions = 3
    mock_status.total_trades = 10
    mock_status.total_pnl = 150.50
    mock_status.macd_line = 100.5
    mock_status.histogram = 25.3
    mock_status.cycle_activated = True
    mock_status.margin_error = False
    mock_status.rate_limited = False
    mock.get_status.return_value = mock_status

    # Configure async methods
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock._log_activity_event = AsyncMock()

    # Configure sync methods
    mock._broadcast_bot_status = MagicMock()

    return mock


@pytest.fixture
def auth_token(async_session, test_user):
    """Get auth token for test user."""
    from src.api.dependencies import create_access_token

    return create_access_token(data={"sub": "test@example.com"})


@pytest.fixture
def client(async_session, mock_grid_manager):
    """Create test client with overridden dependencies."""

    async def override_get_db():
        yield async_session

    def override_get_grid_manager():
        return mock_grid_manager

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_grid_manager] = override_get_grid_manager
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestBotStatusEndpoint:
    """Tests for GET /api/v1/bot/status endpoint."""

    def test_get_status_success(self, client, auth_token):
        """Test successful status retrieval."""
        response = client.get(
            "/api/v1/bot/status",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "running"
        assert data["state"] == "ACTIVE"
        assert data["is_running"] is True
        assert data["cycle_activated"] is True
        assert data["current_price"] == 100000.0

        # Check MACD values
        assert data["macd"]["macd_line"] == 100.5
        assert data["macd"]["histogram"] == 25.3

        # Check order stats
        assert data["orders"]["pending_orders"] == 5
        assert data["orders"]["open_positions"] == 3
        assert data["orders"]["total_trades"] == 10
        assert data["orders"]["total_pnl"] == 150.50

        # Check error status
        assert data["errors"]["margin_error"] is False
        assert data["errors"]["rate_limited"] is False

    def test_get_status_unauthorized(self, client):
        """Test status retrieval without auth token."""
        response = client.get("/api/v1/bot/status")
        assert response.status_code == 401


class TestBotPauseEndpoint:
    """Tests for POST /api/v1/bot/pause endpoint."""

    def test_pause_success(self, client, auth_token, mock_grid_manager):
        """Test successful bot pause."""
        response = client.post(
            "/api/v1/bot/pause",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "paused" in data["message"].lower()
        assert mock_grid_manager._margin_error is True

    def test_pause_when_stopped(self, client, auth_token, mock_grid_manager):
        """Test pause when bot is stopped."""
        type(mock_grid_manager).is_running = PropertyMock(return_value=False)

        response = client.post(
            "/api/v1/bot/pause",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 400
        assert "not running" in response.json()["detail"].lower()


class TestBotResumeEndpoint:
    """Tests for POST /api/v1/bot/resume endpoint."""

    def test_resume_success(self, client, auth_token, mock_grid_manager):
        """Test successful bot resume."""
        mock_grid_manager._margin_error = True

        response = client.post(
            "/api/v1/bot/resume",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "resumed" in data["message"].lower()
        assert mock_grid_manager._margin_error is False

    def test_resume_when_stopped(self, client, auth_token, mock_grid_manager):
        """Test resume when bot is stopped."""
        type(mock_grid_manager).is_running = PropertyMock(return_value=False)

        response = client.post(
            "/api/v1/bot/resume",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 400
        assert "not running" in response.json()["detail"].lower()


class TestBotStopEndpoint:
    """Tests for POST /api/v1/bot/stop endpoint."""

    def test_stop_success(self, client, auth_token, mock_grid_manager):
        """Test successful bot stop."""
        response = client.post(
            "/api/v1/bot/stop",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "stopped" in data["message"].lower()
        mock_grid_manager.stop.assert_called_once()

    def test_stop_when_already_stopped(self, client, auth_token, mock_grid_manager):
        """Test stop when bot is already stopped."""
        type(mock_grid_manager).is_running = PropertyMock(return_value=False)

        response = client.post(
            "/api/v1/bot/stop",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 400
        assert "already stopped" in response.json()["detail"].lower()


class TestBotStartEndpoint:
    """Tests for POST /api/v1/bot/start endpoint."""

    def test_start_success(self, client, auth_token, mock_grid_manager):
        """Test successful bot start."""
        type(mock_grid_manager).is_running = PropertyMock(return_value=False)

        response = client.post(
            "/api/v1/bot/start",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "started" in data["message"].lower()
        mock_grid_manager.start.assert_called_once()

    def test_start_when_already_running(self, client, auth_token, mock_grid_manager):
        """Test start when bot is already running."""
        response = client.post(
            "/api/v1/bot/start",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 400
        assert "already running" in response.json()["detail"].lower()
