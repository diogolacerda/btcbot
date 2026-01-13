"""Tests for TPAdjustmentRepository."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.database.models.account import Account
from src.database.models.trade import Trade
from src.database.models.user import User
from src.database.repositories.tp_adjustment_repository import TPAdjustmentRepository


@pytest.fixture
def test_account(session):
    """Create a test account for trade foreign key."""
    # Create user first
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password",  # pragma: allowlist secret
    )
    session.add(user)
    session.flush()

    # Create account
    account = Account(
        user_id=user.id,
        exchange="bingx",
        name="Test Account",
        is_demo=True,
    )
    session.add(account)
    session.commit()
    return account


@pytest.fixture
def test_trade(session, test_account):
    """Create a test trade for TP adjustments."""
    trade = Trade(
        account_id=test_account.id,
        exchange_order_id="12345",
        symbol="BTC-USDT",
        side="LONG",
        leverage=10,
        entry_price=Decimal("50000.00"),
        quantity=Decimal("0.001"),
        tp_price=Decimal("50500.00"),
        tp_percent=Decimal("0.5"),
        status="OPEN",
    )
    session.add(trade)
    session.commit()
    return trade


def test_save_adjustment(session, test_trade):
    """Test saving a new TP adjustment."""
    repo = TPAdjustmentRepository(session)

    adjustment = repo.save_adjustment(
        trade_id=test_trade.id,
        old_tp_price=Decimal("50500.00"),
        new_tp_price=Decimal("50600.00"),
        old_tp_percent=Decimal("0.5"),
        new_tp_percent=Decimal("0.6"),
        funding_rate=Decimal("0.0001"),
        funding_accumulated=Decimal("0.1"),
        hours_open=Decimal("8.5"),
    )

    assert adjustment is not None
    assert adjustment.id is not None
    assert adjustment.trade_id == test_trade.id
    assert adjustment.old_tp_price == Decimal("50500.00")
    assert adjustment.new_tp_price == Decimal("50600.00")
    assert adjustment.old_tp_percent == Decimal("0.5")
    assert adjustment.new_tp_percent == Decimal("0.6")
    assert adjustment.funding_rate == Decimal("0.0001")
    assert adjustment.funding_accumulated == Decimal("0.1")
    assert adjustment.hours_open == Decimal("8.5")
    assert adjustment.adjusted_at is not None


def test_save_adjustment_minimal(session, test_trade):
    """Test saving adjustment with only required fields."""
    repo = TPAdjustmentRepository(session)

    adjustment = repo.save_adjustment(
        trade_id=test_trade.id,
        old_tp_price=Decimal("50500.00"),
        new_tp_price=Decimal("50600.00"),
        old_tp_percent=Decimal("0.5"),
        new_tp_percent=Decimal("0.6"),
    )

    assert adjustment is not None
    assert adjustment.trade_id == test_trade.id
    assert adjustment.funding_rate is None
    assert adjustment.funding_accumulated is None
    assert adjustment.hours_open is None


def test_get_by_trade(session, test_trade):
    """Test retrieving all adjustments for a trade."""
    repo = TPAdjustmentRepository(session)

    # Initially empty
    adjustments = repo.get_by_trade(test_trade.id)
    assert len(adjustments) == 0

    # Create first adjustment
    repo.save_adjustment(
        trade_id=test_trade.id,
        old_tp_price=Decimal("50500.00"),
        new_tp_price=Decimal("50600.00"),
        old_tp_percent=Decimal("0.5"),
        new_tp_percent=Decimal("0.6"),
    )

    # Create second adjustment
    repo.save_adjustment(
        trade_id=test_trade.id,
        old_tp_price=Decimal("50600.00"),
        new_tp_price=Decimal("50700.00"),
        old_tp_percent=Decimal("0.6"),
        new_tp_percent=Decimal("0.7"),
    )

    # Retrieve all
    adjustments = repo.get_by_trade(test_trade.id)
    assert len(adjustments) == 2
    # Should be ordered by most recent first
    assert adjustments[0].new_tp_percent == Decimal("0.7")
    assert adjustments[1].new_tp_percent == Decimal("0.6")


def test_get_by_trade_nonexistent(session):
    """Test retrieving adjustments for nonexistent trade."""
    repo = TPAdjustmentRepository(session)

    adjustments = repo.get_by_trade(uuid4())
    assert len(adjustments) == 0


def test_get_recent(session, test_trade):
    """Test retrieving recent adjustments."""
    repo = TPAdjustmentRepository(session)

    # Create multiple adjustments
    for i in range(5):
        repo.save_adjustment(
            trade_id=test_trade.id,
            old_tp_price=Decimal(f"5050{i}.00"),
            new_tp_price=Decimal(f"5060{i}.00"),
            old_tp_percent=Decimal(f"0.{i}"),
            new_tp_percent=Decimal(f"0.{i + 1}"),
        )

    # Get all recent
    adjustments = repo.get_recent(limit=100)
    assert len(adjustments) == 5

    # Get limited
    adjustments = repo.get_recent(limit=3)
    assert len(adjustments) == 3

    # Should be ordered by most recent first
    assert adjustments[0].new_tp_percent == Decimal("0.5")


def test_get_recent_with_date_filter(session, test_trade):
    """Test retrieving recent adjustments with date filter."""
    repo = TPAdjustmentRepository(session)

    # Create adjustment in the past
    old_adjustment = repo.save_adjustment(
        trade_id=test_trade.id,
        old_tp_price=Decimal("50500.00"),
        new_tp_price=Decimal("50600.00"),
        old_tp_percent=Decimal("0.5"),
        new_tp_percent=Decimal("0.6"),
    )

    # Manually set adjusted_at to 2 days ago
    old_adjustment.adjusted_at = datetime.now(UTC) - timedelta(days=2)
    session.commit()

    # Create recent adjustment
    repo.save_adjustment(
        trade_id=test_trade.id,
        old_tp_price=Decimal("50600.00"),
        new_tp_price=Decimal("50700.00"),
        old_tp_percent=Decimal("0.6"),
        new_tp_percent=Decimal("0.7"),
    )

    # Get all
    all_adjustments = repo.get_recent(limit=100)
    assert len(all_adjustments) == 2

    # Get only from last 24 hours
    yesterday = datetime.now(UTC) - timedelta(days=1)
    recent_adjustments = repo.get_recent(limit=100, start_date=yesterday)
    assert len(recent_adjustments) == 1
    assert recent_adjustments[0].new_tp_percent == Decimal("0.7")


def test_get_recent_empty(session):
    """Test retrieving recent adjustments when none exist."""
    repo = TPAdjustmentRepository(session)

    adjustments = repo.get_recent(limit=100)
    assert len(adjustments) == 0


def test_inherited_get_by_id(session, test_trade):
    """Test inherited get_by_id method from BaseRepository."""
    repo = TPAdjustmentRepository(session)

    # Create adjustment
    saved = repo.save_adjustment(
        trade_id=test_trade.id,
        old_tp_price=Decimal("50500.00"),
        new_tp_price=Decimal("50600.00"),
        old_tp_percent=Decimal("0.5"),
        new_tp_percent=Decimal("0.6"),
    )

    # Retrieve by ID
    found = repo.get_by_id(saved.id)
    assert found is not None
    assert found.id == saved.id
    assert found.trade_id == test_trade.id


def test_inherited_get_all(session, test_trade):
    """Test inherited get_all method from BaseRepository."""
    repo = TPAdjustmentRepository(session)

    # Create multiple adjustments
    for i in range(5):
        repo.save_adjustment(
            trade_id=test_trade.id,
            old_tp_price=Decimal(f"5050{i}.00"),
            new_tp_price=Decimal(f"5060{i}.00"),
            old_tp_percent=Decimal(f"0.{i}"),
            new_tp_percent=Decimal(f"0.{i + 1}"),
        )

    # Get all
    all_adjustments = repo.get_all(skip=0, limit=100)
    assert len(all_adjustments) == 5

    # Test pagination
    page1 = repo.get_all(skip=0, limit=2)
    assert len(page1) == 2

    page2 = repo.get_all(skip=2, limit=2)
    assert len(page2) == 2


def test_inherited_delete(session, test_trade):
    """Test inherited delete method from BaseRepository."""
    repo = TPAdjustmentRepository(session)

    # Create adjustment
    adjustment = repo.save_adjustment(
        trade_id=test_trade.id,
        old_tp_price=Decimal("50500.00"),
        new_tp_price=Decimal("50600.00"),
        old_tp_percent=Decimal("0.5"),
        new_tp_percent=Decimal("0.6"),
    )

    # Delete
    deleted = repo.delete(adjustment.id)
    assert deleted is True

    # Verify deleted
    found = repo.get_by_id(adjustment.id)
    assert found is None


def test_inherited_exists(session, test_trade):
    """Test inherited exists method from BaseRepository."""
    repo = TPAdjustmentRepository(session)

    # Create adjustment
    adjustment = repo.save_adjustment(
        trade_id=test_trade.id,
        old_tp_price=Decimal("50500.00"),
        new_tp_price=Decimal("50600.00"),
        old_tp_percent=Decimal("0.5"),
        new_tp_percent=Decimal("0.6"),
    )

    # Check exists
    exists = repo.exists(adjustment.id)
    assert exists is True

    # Check non-existent
    exists = repo.exists(uuid4())
    assert exists is False


def test_cascade_delete_with_trade(session, test_account):
    """Test that adjustments are deleted when trade is deleted (CASCADE)."""
    repo = TPAdjustmentRepository(session)

    # Create trade
    trade = Trade(
        account_id=test_account.id,
        exchange_order_id="99999",
        symbol="BTC-USDT",
        side="LONG",
        leverage=10,
        entry_price=Decimal("50000.00"),
        quantity=Decimal("0.001"),
        status="OPEN",
    )
    session.add(trade)
    session.commit()

    # Create adjustment for this trade
    adjustment = repo.save_adjustment(
        trade_id=trade.id,
        old_tp_price=Decimal("50500.00"),
        new_tp_price=Decimal("50600.00"),
        old_tp_percent=Decimal("0.5"),
        new_tp_percent=Decimal("0.6"),
    )

    # Verify adjustment exists
    found = repo.get_by_id(adjustment.id)
    assert found is not None

    # Delete the trade
    session.delete(trade)
    session.commit()

    # Adjustment should be cascade deleted
    found = repo.get_by_id(adjustment.id)
    assert found is None
