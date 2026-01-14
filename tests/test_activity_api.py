"""Tests for activity events API endpoints."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_activity_event_repository
from src.api.main import app
from src.database.models.activity_event import ActivityEvent, EventType


@pytest.fixture
def test_account_id():
    """Provide a test account ID."""
    return uuid4()


@pytest.fixture
def sample_events(test_account_id):
    """Create sample activity events for testing."""
    events = []
    now = datetime.now(UTC)

    # Create 5 events from today
    event_types = [
        (EventType.ORDER_FILLED, "Grid order filled at $95,000.00"),
        (EventType.TRADE_CLOSED, "Trade closed with profit +$50.00"),
        (EventType.TP_ADJUSTED, "Take profit adjusted from 0.5% to 0.6%"),
        (EventType.CYCLE_ACTIVATED, "Grid cycle activated"),
        (EventType.STRATEGY_PAUSED, "Strategy paused due to MACD bearish"),
    ]

    for i, (event_type, description) in enumerate(event_types):
        event = ActivityEvent(
            id=uuid4(),
            account_id=test_account_id,
            event_type=event_type.value,
            description=description,
            event_data={"order_id": f"12345{i}", "price": "95000.00"} if i < 2 else None,
            timestamp=now - timedelta(hours=i),
            created_at=now - timedelta(hours=i),
        )
        events.append(event)

    # Create 3 older events (from 10 days ago)
    older_types = [
        (EventType.BOT_STARTED, "Bot started successfully"),
        (EventType.ORDER_FILLED, "Grid order filled at $92,000.00"),
        (EventType.TRADE_CLOSED, "Trade closed with loss -$20.00"),
    ]

    for i, (event_type, description) in enumerate(older_types):
        event = ActivityEvent(
            id=uuid4(),
            account_id=test_account_id,
            event_type=event_type.value,
            description=description,
            event_data=None,
            timestamp=now - timedelta(days=10, hours=i),
            created_at=now - timedelta(days=10, hours=i),
        )
        events.append(event)

    return events


def test_get_activity_events_default(sample_events, test_account_id):
    """Test GET /api/v1/activity with default parameters (7 days)."""

    def mock_get_activity_event_repository():
        mock_repo = MagicMock()
        mock_repo.get_events_by_period.return_value = sample_events[:5]  # Today's events
        return mock_repo

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=test_account_id):
        try:
            client = TestClient(app)
            response = client.get("/api/v1/activity")

            assert response.status_code == 200
            data = response.json()

            assert "events" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data

            assert data["limit"] == 50
            assert data["offset"] == 0
            assert len(data["events"]) <= data["total"]
        finally:
            app.dependency_overrides.clear()


def test_get_activity_events_today_period(sample_events, test_account_id):
    """Test GET /api/v1/activity with period=today."""
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    today_events = [e for e in sample_events if e.timestamp >= today_start]

    def mock_get_activity_event_repository():
        mock_repo = MagicMock()
        mock_repo.get_events_by_period.return_value = today_events
        return mock_repo

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=test_account_id):
        try:
            client = TestClient(app)
            response = client.get("/api/v1/activity", params={"period": "today"})

            assert response.status_code == 200
            data = response.json()

            assert "events" in data
            # All events should have today's timestamp
            for event in data["events"]:
                event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                assert event_time >= today_start
        finally:
            app.dependency_overrides.clear()


def test_get_activity_events_7days_period(sample_events, test_account_id):
    """Test GET /api/v1/activity with period=7days."""

    def mock_get_activity_event_repository():
        mock_repo = MagicMock()
        # Return today's events (within 7 days)
        mock_repo.get_events_by_period.return_value = sample_events[:5]
        return mock_repo

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=test_account_id):
        try:
            client = TestClient(app)
            response = client.get("/api/v1/activity", params={"period": "7days"})

            assert response.status_code == 200
            data = response.json()

            assert data["total"] == 5
        finally:
            app.dependency_overrides.clear()


def test_get_activity_events_30days_period(sample_events, test_account_id):
    """Test GET /api/v1/activity with period=30days."""

    def mock_get_activity_event_repository():
        mock_repo = MagicMock()
        # Return all events (all within 30 days)
        mock_repo.get_events_by_period.return_value = sample_events
        return mock_repo

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=test_account_id):
        try:
            client = TestClient(app)
            response = client.get("/api/v1/activity", params={"period": "30days"})

            assert response.status_code == 200
            data = response.json()

            # All 8 events should be in 30 days
            assert data["total"] == 8
        finally:
            app.dependency_overrides.clear()


def test_get_activity_events_custom_period(sample_events, test_account_id):
    """Test GET /api/v1/activity with custom period."""
    now = datetime.now(UTC)
    start_date = (now - timedelta(days=15)).isoformat()
    end_date = (now - timedelta(days=5)).isoformat()

    # Only older events (from 10 days ago)
    older_events = sample_events[5:]  # Last 3 events

    def mock_get_activity_event_repository():
        mock_repo = MagicMock()
        mock_repo.get_events_by_period.return_value = older_events
        return mock_repo

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=test_account_id):
        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/activity",
                params={
                    "period": "custom",
                    "startDate": start_date,
                    "endDate": end_date,
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["total"] == 3
        finally:
            app.dependency_overrides.clear()


def test_get_activity_events_custom_without_dates(test_account_id):
    """Test GET /api/v1/activity with custom period without required dates."""

    def mock_get_activity_event_repository():
        return MagicMock()

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=test_account_id):
        try:
            client = TestClient(app)
            response = client.get("/api/v1/activity", params={"period": "custom"})

            assert response.status_code == 400
            assert "start_date and end_date are required" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


def test_get_activity_events_with_event_type_filter(sample_events, test_account_id):
    """Test GET /api/v1/activity with event type filter."""
    order_filled_events = [e for e in sample_events if e.event_type == "ORDER_FILLED"]

    def mock_get_activity_event_repository():
        mock_repo = MagicMock()
        mock_repo.get_events_by_period.return_value = order_filled_events
        return mock_repo

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=test_account_id):
        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/activity",
                params={"event_type": "ORDER_FILLED"},
            )

            assert response.status_code == 200
            data = response.json()

            # All returned events should be ORDER_FILLED type
            for event in data["events"]:
                assert event["event_type"] == "ORDER_FILLED"
        finally:
            app.dependency_overrides.clear()


def test_get_activity_events_pagination(sample_events, test_account_id):
    """Test GET /api/v1/activity pagination."""

    def mock_get_activity_event_repository():
        mock_repo = MagicMock()
        mock_repo.get_events_by_period.return_value = sample_events
        return mock_repo

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=test_account_id):
        try:
            client = TestClient(app)

            # First page
            response = client.get(
                "/api/v1/activity",
                params={"limit": 3, "offset": 0},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["events"]) == 3
            assert data["limit"] == 3
            assert data["offset"] == 0

            # Second page
            response = client.get(
                "/api/v1/activity",
                params={"limit": 3, "offset": 3},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["offset"] == 3
        finally:
            app.dependency_overrides.clear()


def test_get_activity_events_empty(test_account_id):
    """Test GET /api/v1/activity with no events."""

    def mock_get_activity_event_repository():
        mock_repo = MagicMock()
        mock_repo.get_events_by_period.return_value = []
        return mock_repo

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=test_account_id):
        try:
            client = TestClient(app)
            response = client.get("/api/v1/activity")

            assert response.status_code == 200
            data = response.json()

            assert data["events"] == []
            assert data["total"] == 0
        finally:
            app.dependency_overrides.clear()


def test_get_activity_events_no_account():
    """Test GET /api/v1/activity when account not configured."""

    def mock_get_activity_event_repository():
        return MagicMock()

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=None):
        try:
            client = TestClient(app)
            response = client.get("/api/v1/activity")

            assert response.status_code == 503
            assert "Account not configured" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


def test_get_activity_events_schema_structure(sample_events, test_account_id):
    """Test that activity event schema has correct structure."""

    def mock_get_activity_event_repository():
        mock_repo = MagicMock()
        mock_repo.get_events_by_period.return_value = [sample_events[0]]
        return mock_repo

    app.dependency_overrides[get_activity_event_repository] = mock_get_activity_event_repository

    with patch("src.api.routes.activity.get_global_account_id", return_value=test_account_id):
        try:
            client = TestClient(app)
            response = client.get("/api/v1/activity")

            assert response.status_code == 200
            data = response.json()

            event = data["events"][0]
            assert "id" in event
            assert "event_type" in event
            assert "description" in event
            assert "event_data" in event
            assert "timestamp" in event
        finally:
            app.dependency_overrides.clear()
