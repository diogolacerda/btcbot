"""Tests for strategy API endpoints."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_account_id, get_current_active_user, get_db, get_session
from src.api.main import app
from src.api.routes.strategy import get_strategy_repo
from src.database.base import Base
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
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_strategy_repo(sample_strategy):
    """Create a mock StrategyRepository."""
    mock = MagicMock()
    mock.get_by_account = AsyncMock(return_value=[sample_strategy])
    mock.get_active_by_account = AsyncMock(return_value=None)
    mock.get_by_id = AsyncMock(return_value=sample_strategy)
    mock.create_strategy = AsyncMock(return_value=sample_strategy)
    mock.update_strategy = AsyncMock(return_value=sample_strategy)
    mock.delete = AsyncMock(return_value=True)
    mock.activate_strategy = AsyncMock(return_value=sample_strategy)
    mock.deactivate_all = AsyncMock()
    return mock


@pytest.fixture
def mock_user(account_id):
    """Create a mock user with account."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.is_active = True
    # Mock account relationship
    account = MagicMock()
    account.id = account_id
    user.accounts = [account]
    return user


@pytest.fixture
def client(async_session, mock_strategy_repo, mock_user, account_id):
    """Create test client with overridden dependencies."""

    async def override_get_db():
        yield async_session

    async def override_get_session():
        yield async_session

    async def override_get_current_user():
        return mock_user

    async def override_get_account_id():
        return account_id

    async def override_get_strategy_repo(session=None):
        return mock_strategy_repo

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    app.dependency_overrides[get_account_id] = override_get_account_id
    app.dependency_overrides[get_strategy_repo] = override_get_strategy_repo

    yield TestClient(app)

    app.dependency_overrides.clear()


class TestListStrategies:
    """Tests for GET /api/v1/strategies endpoint."""

    def test_list_strategies_success(self, client, auth_token, mock_strategy_repo):
        """Test successful list of strategies."""
        response = client.get(
            "/api/v1/strategies",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Test Strategy"
        assert data[0]["symbol"] == "BTC-USDT"
        mock_strategy_repo.get_by_account.assert_called_once()

    def test_list_strategies_unauthorized(self, client):
        """Test list strategies without auth token."""
        # Clear overrides to test real auth
        app.dependency_overrides.clear()

        with TestClient(app) as c:
            response = c.get("/api/v1/strategies")
            assert response.status_code == 401


class TestGetActiveStrategy:
    """Tests for GET /api/v1/strategies/active endpoint."""

    def test_get_active_strategy_none(self, client, auth_token, mock_strategy_repo):
        """Test when no active strategy exists."""
        response = client.get(
            "/api/v1/strategies/active",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        assert response.json() is None
        mock_strategy_repo.get_active_by_account.assert_called_once()

    def test_get_active_strategy_exists(
        self, client, auth_token, mock_strategy_repo, sample_strategy
    ):
        """Test when active strategy exists."""
        sample_strategy.is_active = True
        mock_strategy_repo.get_active_by_account.return_value = sample_strategy

        response = client.get(
            "/api/v1/strategies/active",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Strategy"
        assert data["is_active"] is True


class TestGetStrategy:
    """Tests for GET /api/v1/strategies/{strategy_id} endpoint."""

    def test_get_strategy_success(self, client, auth_token, mock_strategy_repo, sample_strategy):
        """Test successful strategy retrieval."""
        response = client.get(
            f"/api/v1/strategies/{sample_strategy.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Strategy"
        assert data["leverage"] == 10
        mock_strategy_repo.get_by_id.assert_called_once()

    def test_get_strategy_not_found(self, client, auth_token, mock_strategy_repo):
        """Test strategy not found."""
        mock_strategy_repo.get_by_id.return_value = None

        response = client.get(
            f"/api/v1/strategies/{uuid4()}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_strategy_forbidden(self, client, auth_token, mock_strategy_repo, sample_strategy):
        """Test accessing strategy from another account."""
        # Change strategy's account_id to something different
        sample_strategy.account_id = uuid4()

        response = client.get(
            f"/api/v1/strategies/{sample_strategy.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403
        assert "does not belong" in response.json()["detail"].lower()


class TestCreateStrategy:
    """Tests for POST /api/v1/strategies endpoint."""

    def test_create_strategy_success(self, client, auth_token, mock_strategy_repo):
        """Test successful strategy creation."""
        response = client.post(
            "/api/v1/strategies",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "New Strategy",
                "symbol": "BTC-USDT",
                "leverage": 20,
                "order_size_usdt": "150.00",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Strategy"  # From mock
        mock_strategy_repo.create_strategy.assert_called_once()

    def test_create_strategy_invalid_leverage(self, client, auth_token):
        """Test strategy creation with invalid leverage."""
        response = client.post(
            "/api/v1/strategies",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Invalid Strategy",
                "leverage": 200,  # Max is 125
            },
        )

        assert response.status_code == 422

    def test_create_strategy_invalid_margin_mode(self, client, auth_token):
        """Test strategy creation with invalid margin mode."""
        response = client.post(
            "/api/v1/strategies",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Invalid Strategy",
                "margin_mode": "invalid",
            },
        )

        assert response.status_code == 422

    def test_create_strategy_tp_constraint_violation(self, client, auth_token, mock_strategy_repo):
        """Test strategy creation with TP constraint violation (min > base)."""
        response = client.post(
            "/api/v1/strategies",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Invalid TP Strategy",
                "tp_dynamic_min": "0.5",
                "tp_dynamic_base": "0.3",  # base < min violates constraint
                "tp_dynamic_max": "1.0",
            },
        )

        assert response.status_code == 400
        assert "min <= base <= max" in response.json()["detail"]

    def test_create_strategy_with_is_active_deactivates_others(
        self, client, auth_token, mock_strategy_repo
    ):
        """Test creating active strategy deactivates others."""
        response = client.post(
            "/api/v1/strategies",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Active Strategy",
                "is_active": True,
            },
        )

        assert response.status_code == 201
        mock_strategy_repo.deactivate_all.assert_called_once()


class TestUpdateStrategy:
    """Tests for PATCH /api/v1/strategies/{strategy_id} endpoint."""

    def test_update_strategy_success(self, client, auth_token, mock_strategy_repo, sample_strategy):
        """Test successful strategy update."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"leverage": 25},
        )

        assert response.status_code == 200
        mock_strategy_repo.update_strategy.assert_called_once()

    def test_update_strategy_no_fields(
        self, client, auth_token, mock_strategy_repo, sample_strategy
    ):
        """Test update with no fields provided."""
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={},
        )

        assert response.status_code == 400
        assert "No fields provided" in response.json()["detail"]

    def test_update_strategy_not_found(self, client, auth_token, mock_strategy_repo):
        """Test update non-existent strategy."""
        mock_strategy_repo.get_by_id.return_value = None

        response = client.patch(
            f"/api/v1/strategies/{uuid4()}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"leverage": 25},
        )

        assert response.status_code == 404

    def test_update_strategy_forbidden(
        self, client, auth_token, mock_strategy_repo, sample_strategy
    ):
        """Test update strategy from another account."""
        sample_strategy.account_id = uuid4()

        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"leverage": 25},
        )

        assert response.status_code == 403

    def test_update_strategy_tp_constraint_violation(
        self, client, auth_token, mock_strategy_repo, sample_strategy
    ):
        """Test update with TP constraint violation."""
        # Set current values that will be used for validation
        sample_strategy.tp_dynamic_min = Decimal("0.3")
        sample_strategy.tp_dynamic_base = Decimal("0.5")
        sample_strategy.tp_dynamic_max = Decimal("1.0")

        response = client.patch(
            f"/api/v1/strategies/{sample_strategy.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"tp_dynamic_max": "0.2"},  # max < current base violates constraint
        )

        assert response.status_code == 400
        assert "min <= base <= max" in response.json()["detail"]


class TestDeleteStrategy:
    """Tests for DELETE /api/v1/strategies/{strategy_id} endpoint."""

    def test_delete_strategy_success(self, client, auth_token, mock_strategy_repo, sample_strategy):
        """Test successful strategy deletion."""
        response = client.delete(
            f"/api/v1/strategies/{sample_strategy.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 204
        mock_strategy_repo.delete.assert_called_once_with(sample_strategy.id)

    def test_delete_strategy_not_found(self, client, auth_token, mock_strategy_repo):
        """Test delete non-existent strategy."""
        mock_strategy_repo.get_by_id.return_value = None

        response = client.delete(
            f"/api/v1/strategies/{uuid4()}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404

    def test_delete_strategy_forbidden(
        self, client, auth_token, mock_strategy_repo, sample_strategy
    ):
        """Test delete strategy from another account."""
        sample_strategy.account_id = uuid4()

        response = client.delete(
            f"/api/v1/strategies/{sample_strategy.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403


class TestActivateStrategy:
    """Tests for POST /api/v1/strategies/{strategy_id}/activate endpoint."""

    def test_activate_strategy_success(
        self, client, auth_token, mock_strategy_repo, sample_strategy
    ):
        """Test successful strategy activation."""
        sample_strategy.is_active = True
        mock_strategy_repo.activate_strategy.return_value = sample_strategy

        response = client.post(
            f"/api/v1/strategies/{sample_strategy.id}/activate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "is now active" in data["message"]
        assert data["strategy"]["is_active"] is True
        mock_strategy_repo.activate_strategy.assert_called_once_with(sample_strategy.id)

    def test_activate_strategy_not_found(self, client, auth_token, mock_strategy_repo):
        """Test activate non-existent strategy."""
        mock_strategy_repo.get_by_id.return_value = None

        response = client.post(
            f"/api/v1/strategies/{uuid4()}/activate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404

    def test_activate_strategy_forbidden(
        self, client, auth_token, mock_strategy_repo, sample_strategy
    ):
        """Test activate strategy from another account."""
        sample_strategy.account_id = uuid4()

        response = client.post(
            f"/api/v1/strategies/{sample_strategy.id}/activate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403


class TestStrategySchemaValidation:
    """Tests for strategy schema validation."""

    def test_invalid_spacing_type(self, client, auth_token):
        """Test creation with invalid spacing type."""
        response = client.post(
            "/api/v1/strategies",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Invalid Strategy",
                "spacing_type": "invalid",
            },
        )

        assert response.status_code == 422

    def test_negative_order_size(self, client, auth_token):
        """Test creation with negative order size."""
        response = client.post(
            "/api/v1/strategies",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Invalid Strategy",
                "order_size_usdt": "-100",
            },
        )

        assert response.status_code == 422

    def test_leverage_out_of_range(self, client, auth_token):
        """Test creation with leverage out of range."""
        # Test 0
        response = client.post(
            "/api/v1/strategies",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Invalid Strategy",
                "leverage": 0,
            },
        )
        assert response.status_code == 422

        # Test 126
        response = client.post(
            "/api/v1/strategies",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Invalid Strategy",
                "leverage": 126,
            },
        )
        assert response.status_code == 422
