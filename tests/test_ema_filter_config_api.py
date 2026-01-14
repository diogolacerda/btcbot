"""Tests for EMA filter config API endpoints."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.dependencies import get_account_id, get_current_active_user
from src.api.main import app
from src.api.routes.strategy import (
    get_ema_filter_config_repo,
    get_strategy_repo,
)
from src.database.base import Base
from src.database.engine import get_session
from src.database.models.ema_filter_config import EMAFilterConfig
from src.database.models.strategy import Strategy
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
def account_id():
    """Get test account ID."""
    return uuid4()


@pytest.fixture
def auth_token(test_user):
    """Get auth token for test user."""
    from src.api.dependencies import create_access_token

    return create_access_token(data={"sub": "test@example.com"})


@pytest.fixture
def sample_strategy(account_id):
    """Create a sample strategy for testing."""
    return Strategy(
        id=uuid4(),
        account_id=account_id,
        name="Test Strategy",
        is_active=False,
        symbol="BTC-USDT",
        leverage=10,
        order_size_usdt=Decimal("100.00"),
        margin_mode="crossed",
        take_profit_percent=Decimal("0.50"),
        tp_dynamic_enabled=False,
        tp_dynamic_base=Decimal("0.30"),
        tp_dynamic_min=Decimal("0.30"),
        tp_dynamic_max=Decimal("1.00"),
        tp_dynamic_safety_margin=Decimal("0.05"),
        tp_dynamic_check_interval=60,
        spacing_type="fixed",
        spacing_value=Decimal("100.0"),
        range_percent=Decimal("5.0"),
        max_total_orders=10,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_ema_config(sample_strategy):
    """Create a sample EMA filter config for testing."""
    return EMAFilterConfig(
        id=uuid4(),
        strategy_id=sample_strategy.id,
        enabled=True,
        period=13,
        timeframe="1h",
        allow_on_rising=True,
        allow_on_falling=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_strategy_repo(sample_strategy):
    """Create a mock StrategyRepository."""
    mock = MagicMock()
    mock.get_by_id = MagicMock(return_value=sample_strategy)
    return mock


@pytest.fixture
def mock_ema_filter_repo(sample_ema_config):
    """Create a mock EMAFilterConfigRepository."""
    mock = MagicMock()
    mock.get_by_strategy = MagicMock(return_value=sample_ema_config)
    mock.create_or_update = MagicMock(return_value=sample_ema_config)
    return mock


@pytest.fixture
def mock_user(account_id):
    """Create a mock user with account."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.is_active = True
    account = MagicMock()
    account.id = account_id
    user.accounts = [account]
    return user


@pytest.fixture
def client(session, mock_strategy_repo, mock_ema_filter_repo, mock_user, account_id):
    """Create test client with overridden dependencies."""

    def override_get_session():
        yield session

    def override_get_current_user():
        return mock_user

    def override_get_account_id():
        return account_id

    def override_get_strategy_repo(session=None):
        return mock_strategy_repo

    def override_get_ema_filter_repo(session=None):
        return mock_ema_filter_repo

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    app.dependency_overrides[get_account_id] = override_get_account_id
    app.dependency_overrides[get_strategy_repo] = override_get_strategy_repo
    app.dependency_overrides[get_ema_filter_config_repo] = override_get_ema_filter_repo

    yield TestClient(app)

    app.dependency_overrides.clear()


class TestGetEMAFilterConfig:
    """Tests for GET /api/v1/strategies/{id}/ema-filter endpoint."""

    def test_get_ema_filter_success(
        self, client, auth_token, sample_strategy, sample_ema_config, mock_strategy_repo
    ):
        """Test GET returns EMA filter config successfully."""
        response = client.get(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_ema_config.id)
        assert data["strategy_id"] == str(sample_ema_config.strategy_id)
        assert data["enabled"] is True
        assert data["period"] == 13
        assert data["timeframe"] == "1h"
        assert data["allow_on_rising"] is True
        assert data["allow_on_falling"] is False
        mock_strategy_repo.get_by_id.assert_called_once()

    def test_get_ema_filter_strategy_not_found(
        self, client, auth_token, mock_strategy_repo, mock_ema_filter_repo
    ):
        """Test GET with non-existent strategy returns 404."""
        fake_id = uuid4()
        mock_strategy_repo.get_by_id.return_value = None

        response = client.get(
            f"/api/v1/strategies/{fake_id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]

    def test_get_ema_filter_config_not_found(
        self, client, auth_token, sample_strategy, mock_strategy_repo, mock_ema_filter_repo
    ):
        """Test GET with strategy but no EMA config returns 404."""
        mock_ema_filter_repo.get_by_strategy.return_value = None

        response = client.get(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404
        assert "EMA filter configuration not found" in response.json()["detail"]

    def test_get_ema_filter_forbidden(
        self, client, auth_token, sample_strategy, mock_strategy_repo
    ):
        """Test GET for strategy belonging to different account returns 403."""
        sample_strategy.account_id = uuid4()

        response = client.get(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403
        assert "does not belong" in response.json()["detail"]


class TestPatchEMAFilterConfig:
    """Tests for PATCH /api/v1/strategies/{id}/ema-filter endpoint."""

    def test_update_ema_filter_success(
        self, client, auth_token, sample_strategy, sample_ema_config, mock_ema_filter_repo
    ):
        """Test PATCH updates EMA filter config successfully."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "period": 21,
                "timeframe": "4h",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == 13  # From mock return value
        assert data["timeframe"] == "1h"  # From mock return value
        mock_ema_filter_repo.create_or_update.assert_called_once()

    def test_update_ema_filter_partial(
        self, client, auth_token, sample_strategy, sample_ema_config, mock_ema_filter_repo
    ):
        """Test PATCH updates only provided fields."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"enabled": False},
        )

        assert response.status_code == 200
        mock_ema_filter_repo.create_or_update.assert_called_once()
        call_kwargs = mock_ema_filter_repo.create_or_update.call_args
        # Only enabled was set in the request, others should be None
        assert call_kwargs[1]["enabled"] is False
        assert call_kwargs[1]["period"] is None
        assert call_kwargs[1]["timeframe"] is None

    def test_update_ema_filter_no_fields(
        self, client, auth_token, sample_strategy, mock_ema_filter_repo
    ):
        """Test PATCH with no fields returns 400."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={},
        )

        assert response.status_code == 400
        assert "No fields provided" in response.json()["detail"]
        mock_ema_filter_repo.create_or_update.assert_not_called()

    def test_update_ema_filter_invalid_timeframe(
        self, client, auth_token, sample_strategy, mock_ema_filter_repo
    ):
        """Test PATCH with invalid timeframe returns 422."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"timeframe": "invalid"},
        )

        assert response.status_code == 422
        mock_ema_filter_repo.create_or_update.assert_not_called()

    def test_update_ema_filter_negative_period(
        self, client, auth_token, sample_strategy, mock_ema_filter_repo
    ):
        """Test PATCH with negative period returns 422."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"period": -5},
        )

        assert response.status_code == 422
        mock_ema_filter_repo.create_or_update.assert_not_called()

    def test_update_ema_filter_strategy_not_found(
        self, client, auth_token, mock_strategy_repo, mock_ema_filter_repo
    ):
        """Test PATCH with non-existent strategy returns 404."""
        fake_id = uuid4()
        mock_strategy_repo.get_by_id.return_value = None

        response = client.patch(
            f"/api/v1/strategies/{fake_id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"enabled": False},
        )

        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
        mock_ema_filter_repo.create_or_update.assert_not_called()

    def test_update_ema_filter_forbidden(
        self, client, auth_token, sample_strategy, mock_ema_filter_repo
    ):
        """Test PATCH for strategy belonging to different account returns 403."""
        sample_strategy.account_id = uuid4()

        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"enabled": False},
        )

        assert response.status_code == 403
        assert "does not belong" in response.json()["detail"]
        mock_ema_filter_repo.create_or_update.assert_not_called()

    def test_update_ema_filter_unauthorized(self, session):
        """Test PATCH without auth returns 401."""
        app.dependency_overrides.clear()

        with TestClient(app) as c:
            response = c.patch(
                f"/api/v1/strategies/{uuid4()}/ema-filter",
                json={"enabled": False},
            )
            assert response.status_code == 401

    def test_update_ema_filter_allow_on_rising(
        self, client, auth_token, sample_strategy, sample_ema_config, mock_ema_filter_repo
    ):
        """Test PATCH updates allow_on_rising."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"allow_on_rising": False},
        )

        assert response.status_code == 200
        mock_ema_filter_repo.create_or_update.assert_called_once()
        call_kwargs = mock_ema_filter_repo.create_or_update.call_args
        assert call_kwargs[1]["allow_on_rising"] is False

    def test_update_ema_filter_allow_on_falling(
        self, client, auth_token, sample_strategy, sample_ema_config, mock_ema_filter_repo
    ):
        """Test PATCH updates allow_on_falling."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/ema-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"allow_on_falling": True},
        )

        assert response.status_code == 200
        mock_ema_filter_repo.create_or_update.assert_called_once()
        call_kwargs = mock_ema_filter_repo.create_or_update.call_args
        assert call_kwargs[1]["allow_on_falling"] is True
