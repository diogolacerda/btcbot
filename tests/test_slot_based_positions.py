"""
Tests for slot-based position control to prevent multiple positions
in the same spacing range.
"""

import pytest

from src.grid.order_tracker import OrderTracker


class TestSlotCalculation:
    """Test slot floor calculation."""

    def test_get_slot_floor_basic(self):
        """Basic slot floor calculation with spacing=100."""
        assert OrderTracker.get_slot_floor(93972.30, 100) == 93900.0
        assert OrderTracker.get_slot_floor(93900.00, 100) == 93900.0
        assert OrderTracker.get_slot_floor(93999.99, 100) == 93900.0
        assert OrderTracker.get_slot_floor(94000.00, 100) == 94000.0
        assert OrderTracker.get_slot_floor(94050.50, 100) == 94000.0

    def test_get_slot_floor_different_spacings(self):
        """Slot floor calculation with different spacing values."""
        # Spacing = 50
        assert OrderTracker.get_slot_floor(93972.30, 50) == 93950.0
        assert OrderTracker.get_slot_floor(94025.00, 50) == 94000.0

        # Spacing = 200
        assert OrderTracker.get_slot_floor(93972.30, 200) == 93800.0
        assert OrderTracker.get_slot_floor(94150.00, 200) == 94000.0

    def test_get_slot_floor_edge_cases(self):
        """Slot floor calculation edge cases."""
        # Price exactly at slot boundary
        assert OrderTracker.get_slot_floor(94000.0, 100) == 94000.0

        # Very small price
        assert OrderTracker.get_slot_floor(150.50, 100) == 100.0

        # Very large price
        assert OrderTracker.get_slot_floor(99872.30, 100) == 99800.0


class TestSlotOccupancy:
    """Test slot occupancy tracking."""

    @pytest.fixture
    def tracker(self):
        """Create OrderTracker instance with spacing=100."""
        return OrderTracker(spacing=100.0)

    def test_slot_initially_not_occupied(self, tracker):
        """Slots should not be occupied initially."""
        assert not tracker.is_slot_occupied(93972.30)
        assert not tracker.is_slot_occupied(94050.00)
        assert not tracker.is_slot_occupied(93800.00)

    def test_mark_slot_occupied(self, tracker):
        """Marking a slot as occupied should work correctly."""
        # Mark slot for $93,972.30 (slot 93900-93999)
        tracker._mark_slot_occupied(93972.30)

        # All prices in the same slot should be considered occupied
        assert tracker.is_slot_occupied(93900.00)
        assert tracker.is_slot_occupied(93950.00)
        assert tracker.is_slot_occupied(93972.30)
        assert tracker.is_slot_occupied(93999.99)

        # Prices in other slots should not be occupied
        assert not tracker.is_slot_occupied(94000.00)
        assert not tracker.is_slot_occupied(93899.99)

    def test_mark_multiple_slots_occupied(self, tracker):
        """Multiple slots can be marked as occupied."""
        tracker._mark_slot_occupied(93972.30)  # Slot 93900
        tracker._mark_slot_occupied(94050.00)  # Slot 94000
        tracker._mark_slot_occupied(93750.00)  # Slot 93700

        assert tracker.is_slot_occupied(93972.30)
        assert tracker.is_slot_occupied(94050.00)
        assert tracker.is_slot_occupied(93750.00)

        # Unoccupied slots
        assert not tracker.is_slot_occupied(93650.00)  # Slot 93600
        assert not tracker.is_slot_occupied(94150.00)  # Slot 94100

    def test_release_slot(self, tracker):
        """Releasing a slot should make it available again."""
        # Occupy the slot
        tracker._mark_slot_occupied(93972.30)
        assert tracker.is_slot_occupied(93972.30)

        # Release it
        tracker._release_slot(93972.30)
        assert not tracker.is_slot_occupied(93972.30)
        assert not tracker.is_slot_occupied(93900.00)
        assert not tracker.is_slot_occupied(93999.99)

    def test_release_slot_different_price_same_range(self, tracker):
        """Releasing with different price in same slot should work."""
        # Occupy slot using one price
        tracker._mark_slot_occupied(93972.30)
        assert tracker.is_slot_occupied(93972.30)

        # Release using different price in same slot
        tracker._release_slot(93950.00)
        assert not tracker.is_slot_occupied(93972.30)
        assert not tracker.is_slot_occupied(93950.00)

    def test_release_unoccupied_slot_does_nothing(self, tracker):
        """Releasing an unoccupied slot should not raise error."""
        # Should not raise any exception
        tracker._release_slot(93972.30)
        assert not tracker.is_slot_occupied(93972.30)


class TestSlotOccupancyWithDifferentSpacings:
    """Test slot occupancy with different spacing values."""

    def test_spacing_50(self):
        """Test with spacing=50."""
        tracker = OrderTracker(spacing=50.0)

        tracker._mark_slot_occupied(93972.30)  # Slot 93950-93999

        assert tracker.is_slot_occupied(93972.30)
        assert tracker.is_slot_occupied(93950.00)
        assert tracker.is_slot_occupied(93999.99)
        assert not tracker.is_slot_occupied(94000.00)  # Next slot
        assert not tracker.is_slot_occupied(93949.99)  # Previous slot

    def test_spacing_200(self):
        """Test with spacing=200."""
        tracker = OrderTracker(spacing=200.0)

        tracker._mark_slot_occupied(93972.30)  # Slot 93800-93999

        assert tracker.is_slot_occupied(93972.30)
        assert tracker.is_slot_occupied(93800.00)
        assert tracker.is_slot_occupied(93900.00)
        assert tracker.is_slot_occupied(93999.99)
        assert not tracker.is_slot_occupied(94000.00)  # Next slot
        assert not tracker.is_slot_occupied(93799.99)  # Previous slot


class TestSlotBasedPositionControl:
    """Integration tests for slot-based position control."""

    @pytest.fixture
    def tracker(self):
        """Create OrderTracker instance with spacing=100."""
        return OrderTracker(spacing=100.0)

    def test_order_filled_marks_slot_occupied(self, tracker):
        """When an order is filled, its slot should be marked as occupied."""
        # Add and fill an order
        tracker.add_order(
            order_id="test_order_1",
            entry_price=93972.30,
            tp_price=94254.60,
            quantity=0.01,
        )

        tracker.order_filled("test_order_1")

        # Slot should be marked as occupied
        assert tracker.is_slot_occupied(93972.30)
        assert tracker.is_slot_occupied(93900.00)
        assert tracker.is_slot_occupied(93999.99)

    def test_tp_hit_releases_slot(self, tracker):
        """When TP is hit, the slot should be released."""
        # Add, fill, and close an order
        tracker.add_order(
            order_id="test_order_1",
            entry_price=93972.30,
            tp_price=94254.60,
            quantity=0.01,
        )

        tracker.order_filled("test_order_1")
        assert tracker.is_slot_occupied(93972.30)

        tracker.order_tp_hit("test_order_1", exit_price=94254.60)

        # Slot should be released
        assert not tracker.is_slot_occupied(93972.30)
        assert not tracker.is_slot_occupied(93900.00)

    def test_multiple_positions_different_slots(self, tracker):
        """Multiple positions can exist in different slots."""
        # Add and fill orders in different slots
        tracker.add_order(
            order_id="order_1",
            entry_price=93972.30,  # Slot 93900
            tp_price=94254.60,
            quantity=0.01,
        )
        tracker.add_order(
            order_id="order_2",
            entry_price=94050.00,  # Slot 94000
            tp_price=94332.30,
            quantity=0.01,
        )

        tracker.order_filled("order_1")
        tracker.order_filled("order_2")

        # Both slots should be occupied
        assert tracker.is_slot_occupied(93972.30)
        assert tracker.is_slot_occupied(94050.00)

        # Different slots
        assert not tracker.is_slot_occupied(93850.00)  # Slot 93800
        assert not tracker.is_slot_occupied(94150.00)  # Slot 94100

    def test_cannot_have_multiple_positions_in_same_slot(self, tracker):
        """Slot occupancy check should prevent multiple positions in same range."""
        # Fill first order in slot 93900
        tracker.add_order(
            order_id="order_1",
            entry_price=93972.30,
            tp_price=94254.60,
            quantity=0.01,
        )
        tracker.order_filled("order_1")

        # Check that slot is occupied for other prices in same range
        assert tracker.is_slot_occupied(93950.00)  # Should be blocked
        assert tracker.is_slot_occupied(93931.80)  # Should be blocked
        assert tracker.is_slot_occupied(93937.20)  # Should be blocked

    def test_loaded_position_marks_slot_occupied(self, tracker):
        """Positions loaded from exchange should mark slots as occupied."""
        # Simulate loading existing position
        tracker.load_existing_positions(
            positions=[{"symbol": "BTC-USDT", "positionAmt": "0.01"}],
            open_orders=[
                {
                    "type": "TAKE_PROFIT_MARKET",
                    "stopPrice": "94254.60",
                    "origQty": "0.01",
                    "orderId": "12345678",
                }
            ],
            tp_percent=0.3,
        )

        # Slot for the loaded position should be occupied
        # TP=94254.60, tp_percent=0.3 -> entry=94254.60/1.003=93972.38
        assert tracker.is_slot_occupied(93972.38)
