"""Tests for MACD filter config API endpoints."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_account_id, get_current_active_user
from src.api.main import app
from src.api.routes.strategy import get_macd_filter_config_repo, get_strategy_repo
from src.database.base import Base
from src.database.engine import get_session
from src.database.models.macd_filter_config import MACDFilterConfig
from src.database.models.strategy import Strategy
from src.database.models.user import User

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
        anchor_mode="none",
        anchor_threshold=Decimal("100.0"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_macd_config(sample_strategy):
    """Create a sample MACD filter config for testing."""
    return MACDFilterConfig(
        id=uuid4(),
        strategy_id=sample_strategy.id,
        enabled=True,
        fast_period=12,
        slow_period=26,
        signal_period=9,
        timeframe="1h",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_strategy_repo(sample_strategy):
    """Create a mock StrategyRepository."""
    mock = MagicMock()
    mock.get_by_id = AsyncMock(return_value=sample_strategy)
    return mock


@pytest.fixture
def mock_macd_filter_repo(sample_macd_config):
    """Create a mock MACDFilterConfigRepository."""
    mock = MagicMock()
    mock.get_by_strategy = AsyncMock(return_value=sample_macd_config)
    mock.create_or_update = AsyncMock(return_value=sample_macd_config)
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
def client(async_session, mock_strategy_repo, mock_macd_filter_repo, mock_user, account_id):
    """Create test client with overridden dependencies."""

    async def override_get_session():
        yield async_session

    async def override_get_current_user():
        return mock_user

    async def override_get_account_id():
        return account_id

    async def override_get_strategy_repo(session=None):
        return mock_strategy_repo

    async def override_get_macd_filter_repo(session=None):
        return mock_macd_filter_repo

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    app.dependency_overrides[get_account_id] = override_get_account_id
    app.dependency_overrides[get_strategy_repo] = override_get_strategy_repo
    app.dependency_overrides[get_macd_filter_config_repo] = override_get_macd_filter_repo

    yield TestClient(app)

    app.dependency_overrides.clear()


class TestGetMACDFilterConfig:
    """Tests for GET /api/v1/strategies/{id}/macd-filter endpoint."""

    def test_get_macd_filter_success(
        self, client, auth_token, sample_strategy, sample_macd_config, mock_strategy_repo
    ):
        """Test GET returns MACD filter config successfully."""
        response = client.get(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_macd_config.id)
        assert data["strategy_id"] == str(sample_macd_config.strategy_id)
        assert data["enabled"] is True
        assert data["fast_period"] == 12
        assert data["slow_period"] == 26
        assert data["signal_period"] == 9
        assert data["timeframe"] == "1h"
        mock_strategy_repo.get_by_id.assert_called_once()

    def test_get_macd_filter_strategy_not_found(
        self, client, auth_token, mock_strategy_repo, mock_macd_filter_repo
    ):
        """Test GET with non-existent strategy returns 404."""
        fake_id = uuid4()
        mock_strategy_repo.get_by_id.return_value = None

        response = client.get(
            f"/api/v1/strategies/{fake_id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]

    def test_get_macd_filter_config_not_found(
        self, client, auth_token, sample_strategy, mock_strategy_repo, mock_macd_filter_repo
    ):
        """Test GET with strategy but no MACD config returns 404."""
        mock_macd_filter_repo.get_by_strategy.return_value = None

        response = client.get(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404
        assert "MACD filter configuration not found" in response.json()["detail"]

    def test_get_macd_filter_forbidden(
        self, client, auth_token, sample_strategy, mock_strategy_repo
    ):
        """Test GET for strategy belonging to different account returns 403."""
        sample_strategy.account_id = uuid4()

        response = client.get(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403
        assert "does not belong" in response.json()["detail"]


class TestPatchMACDFilterConfig:
    """Tests for PATCH /api/v1/strategies/{id}/macd-filter endpoint."""

    def test_update_macd_filter_success(
        self, client, auth_token, sample_strategy, sample_macd_config, mock_macd_filter_repo
    ):
        """Test PATCH updates MACD filter config successfully."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "fast_period": 15,
                "slow_period": 30,
                "timeframe": "4h",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["fast_period"] == 12  # From mock return value
        assert data["slow_period"] == 26
        mock_macd_filter_repo.create_or_update.assert_called_once()

    def test_update_macd_filter_partial(
        self, client, auth_token, sample_strategy, sample_macd_config, mock_macd_filter_repo
    ):
        """Test PATCH updates only provided fields."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"enabled": False},
        )

        assert response.status_code == 200
        mock_macd_filter_repo.create_or_update.assert_called_once()
        call_kwargs = mock_macd_filter_repo.create_or_update.call_args
        # Only enabled was set in the request, others should be None
        assert call_kwargs[1]["enabled"] is False
        assert call_kwargs[1]["fast_period"] is None
        assert call_kwargs[1]["slow_period"] is None

    def test_update_macd_filter_no_fields(
        self, client, auth_token, sample_strategy, mock_macd_filter_repo
    ):
        """Test PATCH with no fields returns 400."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={},
        )

        assert response.status_code == 400
        assert "No fields provided" in response.json()["detail"]
        mock_macd_filter_repo.create_or_update.assert_not_called()

    def test_update_macd_filter_invalid_timeframe(
        self, client, auth_token, sample_strategy, mock_macd_filter_repo
    ):
        """Test PATCH with invalid timeframe returns 422."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"timeframe": "invalid"},
        )

        assert response.status_code == 422
        mock_macd_filter_repo.create_or_update.assert_not_called()

    def test_update_macd_filter_fast_equals_slow(
        self, client, auth_token, sample_strategy, mock_macd_filter_repo
    ):
        """Test PATCH with fast == slow returns 422."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "fast_period": 26,
                "slow_period": 26,
            },
        )

        assert response.status_code == 422
        assert "slow_period must be greater than fast_period" in response.json()["detail"][0]["msg"]
        mock_macd_filter_repo.create_or_update.assert_not_called()

    def test_update_macd_filter_fast_greater_than_slow(
        self, client, auth_token, sample_strategy, mock_macd_filter_repo
    ):
        """Test PATCH with fast > slow returns 422."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "fast_period": 30,
                "slow_period": 20,
            },
        )

        assert response.status_code == 422
        assert "slow_period must be greater than fast_period" in response.json()["detail"][0]["msg"]
        mock_macd_filter_repo.create_or_update.assert_not_called()

    def test_update_macd_filter_negative_period(
        self, client, auth_token, sample_strategy, mock_macd_filter_repo
    ):
        """Test PATCH with negative period returns 422."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"fast_period": -5},
        )

        assert response.status_code == 422
        mock_macd_filter_repo.create_or_update.assert_not_called()

    def test_update_macd_filter_strategy_not_found(
        self, client, auth_token, mock_strategy_repo, mock_macd_filter_repo
    ):
        """Test PATCH with non-existent strategy returns 404."""
        fake_id = uuid4()
        mock_strategy_repo.get_by_id.return_value = None

        response = client.patch(
            f"/api/v1/strategies/{fake_id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"enabled": False},
        )

        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
        mock_macd_filter_repo.create_or_update.assert_not_called()

    def test_update_macd_filter_forbidden(
        self, client, auth_token, sample_strategy, mock_macd_filter_repo
    ):
        """Test PATCH for strategy belonging to different account returns 403."""
        sample_strategy.account_id = uuid4()

        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}/macd-filter",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"enabled": False},
        )

        assert response.status_code == 403
        assert "does not belong" in response.json()["detail"]
        mock_macd_filter_repo.create_or_update.assert_not_called()

    def test_update_macd_filter_unauthorized(self, async_session):
        """Test PATCH without auth returns 401."""
        app.dependency_overrides.clear()

        with TestClient(app) as c:
            response = c.patch(
                f"/api/v1/strategies/{uuid4()}/macd-filter",
                json={"enabled": False},
            )
            assert response.status_code == 401
