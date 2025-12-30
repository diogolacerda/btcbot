"""Tests for BotStateRepository."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.database.models.account import Account
from src.database.models.user import User
from src.database.repositories.bot_state_repository import BotStateRepository


@pytest.fixture
async def test_account(async_session):
    """Create a test account."""
    # Create user first
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password",  # pragma: allowlist secret
    )
    async_session.add(user)
    await async_session.flush()

    # Create account
    account = Account(
        user_id=user.id,
        exchange="bingx",
        name="Test Account",
        is_demo=True,
    )
    async_session.add(account)
    await async_session.commit()
    return account


@pytest.mark.asyncio
async def test_save_new_state(async_session, test_account):
    """Test saving a new bot state."""
    repo = BotStateRepository(async_session)

    # Save new state
    bot_state = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=True,
        last_state="activate",
    )

    assert bot_state is not None
    assert bot_state.account_id == test_account.id
    assert bot_state.cycle_activated is True
    assert bot_state.last_state == "activate"
    assert bot_state.activated_at is not None
    assert bot_state.last_state_change_at is not None


@pytest.mark.asyncio
async def test_save_update_existing_state(async_session, test_account):
    """Test updating an existing bot state."""
    repo = BotStateRepository(async_session)

    # Create initial state
    initial_state = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=True,
        last_state="activate",
    )
    initial_id = initial_state.id

    # Update state
    updated_state = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=True,
        last_state="active",
    )

    # Should be the same record
    assert updated_state.id == initial_id
    assert updated_state.last_state == "active"
    assert updated_state.cycle_activated is True


@pytest.mark.asyncio
async def test_deactivate_clears_activated_at(async_session, test_account):
    """Test that deactivating clears activated_at timestamp."""
    repo = BotStateRepository(async_session)

    # Activate
    bot_state = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=True,
        last_state="activate",
    )
    assert bot_state.activated_at is not None

    # Deactivate
    bot_state = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=False,
        last_state="inactive",
    )
    assert bot_state.activated_at is None


@pytest.mark.asyncio
async def test_get_by_account(async_session, test_account):
    """Test retrieving bot state by account."""
    repo = BotStateRepository(async_session)

    # No state initially
    state = await repo.get_by_account(test_account.id)
    assert state is None

    # Create state
    await repo.save_state(
        account_id=test_account.id,
        cycle_activated=True,
        last_state="activate",
    )

    # Retrieve state
    state = await repo.get_by_account(test_account.id)
    assert state is not None
    assert state.account_id == test_account.id


@pytest.mark.asyncio
async def test_get_by_nonexistent_account(async_session):
    """Test retrieving bot state for nonexistent account."""
    repo = BotStateRepository(async_session)

    # Non-existent account
    state = await repo.get_by_account(uuid4())
    assert state is None


@pytest.mark.asyncio
async def test_is_state_valid_recent(async_session, test_account):
    """Test state validity check for recent state."""
    repo = BotStateRepository(async_session)

    # Create recent state
    bot_state = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=True,
        last_state="activate",
    )

    # Should be valid
    is_valid = await repo.is_state_valid(bot_state, max_age_hours=24)
    assert is_valid is True


@pytest.mark.asyncio
async def test_is_state_valid_old(async_session, test_account):
    """Test state validity check for old state."""
    repo = BotStateRepository(async_session)

    # Create state
    bot_state = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=True,
        last_state="activate",
    )

    # Manually set activated_at to 25 hours ago
    bot_state.activated_at = datetime.now(UTC) - timedelta(hours=25)
    await async_session.commit()

    # Should be invalid
    is_valid = await repo.is_state_valid(bot_state, max_age_hours=24)
    assert is_valid is False


@pytest.mark.asyncio
async def test_is_state_valid_not_activated(async_session, test_account):
    """Test state validity check for non-activated state."""
    repo = BotStateRepository(async_session)

    # Create deactivated state
    bot_state = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=False,
        last_state="inactive",
    )

    # Should be invalid (not activated)
    is_valid = await repo.is_state_valid(bot_state, max_age_hours=24)
    assert is_valid is False


@pytest.mark.asyncio
async def test_clear_state(async_session, test_account):
    """Test clearing bot state."""
    repo = BotStateRepository(async_session)

    # Create state
    await repo.save_state(
        account_id=test_account.id,
        cycle_activated=True,
        last_state="activate",
    )

    # Verify state exists
    state = await repo.get_by_account(test_account.id)
    assert state is not None

    # Clear state
    await repo.clear_state(test_account.id)

    # Verify state is gone
    state = await repo.get_by_account(test_account.id)
    assert state is None


@pytest.mark.asyncio
async def test_to_dict(async_session, test_account):
    """Test converting bot state to dictionary."""
    repo = BotStateRepository(async_session)

    # Create state
    bot_state = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=True,
        last_state="activate",
    )

    # Convert to dict
    state_dict = repo.to_dict(bot_state)

    assert state_dict["id"] == str(bot_state.id)
    assert state_dict["account_id"] == str(test_account.id)
    assert state_dict["cycle_activated"] is True
    assert state_dict["last_state"] == "activate"
    assert "activated_at" in state_dict
    assert "last_state_change_at" in state_dict
    assert "created_at" in state_dict
    assert "updated_at" in state_dict


@pytest.mark.asyncio
async def test_one_state_per_account(async_session, test_account):
    """Test that only one state can exist per account."""
    repo = BotStateRepository(async_session)

    # Create first state
    state1 = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=True,
        last_state="activate",
    )

    # Create second state (should update first)
    state2 = await repo.save_state(
        account_id=test_account.id,
        cycle_activated=False,
        last_state="inactive",
    )

    # Should be the same record
    assert state1.id == state2.id

    # Verify only one state exists
    state = await repo.get_by_account(test_account.id)
    assert state.id == state1.id
    assert state.cycle_activated is False
    assert state.last_state == "inactive"
