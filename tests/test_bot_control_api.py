"""Tests for bot control API endpoints."""

from unittest.mock import MagicMock, PropertyMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.dependencies import get_db, get_grid_manager
from src.api.main import app
from src.database.base import Base
from src.database.models.user import User
from src.strategy.macd_strategy import GridState

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
def test_user(session):
    """Create a test user in the database."""
    from src.api.dependencies import get_password_hash

    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.expunge_all()
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
    mock.start = MagicMock()
    mock.stop = MagicMock()

    return mock


@pytest.fixture
def auth_token(session, test_user):
    """Get auth token for test user."""
    from src.api.dependencies import create_access_token

    return create_access_token(data={"sub": "test@example.com"})


@pytest.fixture
def client(session, mock_grid_manager):
    """Create test client with overridden dependencies."""

    def override_get_db():
        yield session

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
