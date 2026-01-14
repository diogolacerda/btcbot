"""Tests for TPAdjustment model."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.models import Account, TPAdjustment, Trade, User


class TestTPAdjustmentModel:
    """Test cases for TPAdjustment model."""

    @pytest.fixture
    def user(self, session: Session) -> User:
        """Create a test user."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password_123",  # pragma: allowlist secret
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @pytest.fixture
    def account(self, session: Session, user: User) -> Account:
        """Create a test account."""
        account = Account(
            user_id=user.id,
            exchange="BingX",
            name="Test Account",
            is_demo=True,
        )
        session.add(account)
        session.commit()
        session.refresh(account)
        return account

    @pytest.fixture
    def trade(self, session: Session, account: Account) -> Trade:
        """Create a test trade."""
        trade = Trade(
            account_id=account.id,
            symbol="BTC-USDT",
            side="LONG",
            leverage=10,
            entry_price=Decimal("90000.00"),
            quantity=Decimal("0.001"),
            tp_price=Decimal("90300.00"),
            tp_percent=Decimal("0.3333"),
            status="OPEN",
        )
        session.add(trade)
        session.commit()
        session.refresh(trade)
        return trade

    def test_create_tp_adjustment_full(self, session: Session, trade: Trade):
        """Test creating a TP adjustment with all fields."""
        # Arrange
        adjustment = TPAdjustment(
            trade_id=trade.id,
            old_tp_price=Decimal("90300.00"),
            new_tp_price=Decimal("90450.00"),
            old_tp_percent=Decimal("0.3333"),
            new_tp_percent=Decimal("0.5000"),
            funding_rate=Decimal("0.0001"),
            funding_accumulated=Decimal("0.0600"),
            hours_open=Decimal("16.00"),
        )

        # Act
        session.add(adjustment)
        session.commit()
        session.refresh(adjustment)

        # Assert
        assert adjustment.id is not None
        assert isinstance(adjustment.id, UUID)
        assert adjustment.trade_id == trade.id
        assert adjustment.old_tp_price == Decimal("90300.00")
        assert adjustment.new_tp_price == Decimal("90450.00")
        assert adjustment.old_tp_percent == Decimal("0.3333")
        assert adjustment.new_tp_percent == Decimal("0.5000")
        assert adjustment.funding_rate == Decimal("0.0001")
        assert adjustment.funding_accumulated == Decimal("0.0600")
        assert adjustment.hours_open == Decimal("16.00")
        assert isinstance(adjustment.adjusted_at, datetime)

    def test_create_tp_adjustment_minimal(self, session: Session, trade: Trade):
        """Test creating a TP adjustment with only required fields."""
        # Arrange
        adjustment = TPAdjustment(
            trade_id=trade.id,
            old_tp_price=Decimal("90300.00"),
            new_tp_price=Decimal("90450.00"),
            old_tp_percent=Decimal("0.3333"),
            new_tp_percent=Decimal("0.5000"),
        )

        # Act
        session.add(adjustment)
        session.commit()
        session.refresh(adjustment)

        # Assert
        assert adjustment.id is not None
        assert adjustment.trade_id == trade.id
        assert adjustment.old_tp_price == Decimal("90300.00")
        assert adjustment.new_tp_price == Decimal("90450.00")
        assert adjustment.funding_rate is None
        assert adjustment.funding_accumulated is None
        assert adjustment.hours_open is None

    def test_trade_id_required(self, session: Session):
        """Test that trade_id is required."""
        # Arrange
        adjustment = TPAdjustment(
            old_tp_price=Decimal("90300.00"),
            new_tp_price=Decimal("90450.00"),
            old_tp_percent=Decimal("0.3333"),
            new_tp_percent=Decimal("0.5000"),
        )

        # Act & Assert
        session.add(adjustment)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_foreign_key_constraint(self, session: Session):
        """Test that trade_id must reference an existing trade."""
        # Arrange
        adjustment = TPAdjustment(
            trade_id=uuid4(),  # Non-existent trade
            old_tp_price=Decimal("90300.00"),
            new_tp_price=Decimal("90450.00"),
            old_tp_percent=Decimal("0.3333"),
            new_tp_percent=Decimal("0.5000"),
        )

        # Act & Assert
        session.add(adjustment)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_old_tp_price_required(self, session: Session, trade: Trade):
        """Test that old_tp_price is required."""
        # Arrange
        adjustment = TPAdjustment(
            trade_id=trade.id,
            new_tp_price=Decimal("90450.00"),
            old_tp_percent=Decimal("0.3333"),
            new_tp_percent=Decimal("0.5000"),
        )

        # Act & Assert
        session.add(adjustment)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_new_tp_price_required(self, session: Session, trade: Trade):
        """Test that new_tp_price is required."""
        # Arrange
        adjustment = TPAdjustment(
            trade_id=trade.id,
            old_tp_price=Decimal("90300.00"),
            old_tp_percent=Decimal("0.3333"),
            new_tp_percent=Decimal("0.5000"),
        )

        # Act & Assert
        session.add(adjustment)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_adjusted_at_auto_generated(self, session: Session, trade: Trade):
        """Test that adjusted_at is automatically generated."""
        # Arrange
        adjustment = TPAdjustment(
            trade_id=trade.id,
            old_tp_price=Decimal("90300.00"),
            new_tp_price=Decimal("90450.00"),
            old_tp_percent=Decimal("0.3333"),
            new_tp_percent=Decimal("0.5000"),
        )

        # Act
        session.add(adjustment)
        session.commit()
        session.refresh(adjustment)

        # Assert
        assert adjustment.adjusted_at is not None
        assert isinstance(adjustment.adjusted_at, datetime)

    def test_query_by_trade_id(self, session: Session, trade: Trade):
        """Test querying adjustments by trade_id."""
        # Arrange
        adjustment1 = TPAdjustment(
            trade_id=trade.id,
            old_tp_price=Decimal("90300.00"),
            new_tp_price=Decimal("90450.00"),
            old_tp_percent=Decimal("0.3333"),
            new_tp_percent=Decimal("0.5000"),
        )
        adjustment2 = TPAdjustment(
            trade_id=trade.id,
            old_tp_price=Decimal("90450.00"),
            new_tp_price=Decimal("90600.00"),
            old_tp_percent=Decimal("0.5000"),
            new_tp_percent=Decimal("0.6667"),
        )
        session.add_all([adjustment1, adjustment2])
        session.commit()

        # Act
        stmt = select(TPAdjustment).where(TPAdjustment.trade_id == trade.id)
        result = session.execute(stmt)
        adjustments = result.scalars().all()

        # Assert
        assert len(adjustments) == 2

    def test_cascade_delete(self, session: Session, trade: Trade):
        """Test that adjustments are deleted when trade is deleted."""
        # Arrange
        adjustment = TPAdjustment(
            trade_id=trade.id,
            old_tp_price=Decimal("90300.00"),
            new_tp_price=Decimal("90450.00"),
            old_tp_percent=Decimal("0.3333"),
            new_tp_percent=Decimal("0.5000"),
        )
        session.add(adjustment)
        session.commit()

        # Act - Delete the trade
        session.delete(trade)
        session.commit()

        # Assert - Adjustment should be deleted
        stmt = select(TPAdjustment).where(TPAdjustment.id == adjustment.id)
        result = session.execute(stmt)
        found_adjustment = result.scalar_one_or_none()
        assert found_adjustment is None

    def test_tp_adjustment_repr(self, session: Session, trade: Trade):
        """Test TPAdjustment __repr__ method."""
        # Arrange
        adjustment = TPAdjustment(
            trade_id=trade.id,
            old_tp_price=Decimal("90300.00"),
            new_tp_price=Decimal("90450.00"),
            old_tp_percent=Decimal("0.3333"),
            new_tp_percent=Decimal("0.5000"),
        )
        session.add(adjustment)
        session.commit()
        session.refresh(adjustment)

        # Act
        repr_str = repr(adjustment)

        # Assert
        assert "TPAdjustment" in repr_str
        assert str(adjustment.id) in repr_str
        assert str(trade.id) in repr_str
        assert "0.3333" in repr_str
        assert "0.5000" in repr_str
