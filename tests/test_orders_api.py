"""Tests for the Orders API endpoints."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.grid.order_tracker import OrderStatus, OrderTracker, TrackedOrder


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_order_tracker():
    """Create a mock OrderTracker with sample orders."""
    tracker = OrderTracker()

    # Add some sample orders
    tracker._orders = {
        "order_001": TrackedOrder(
            order_id="order_001",
            entry_price=95000.0,
            tp_price=95500.0,
            quantity=0.001,
            status=OrderStatus.PENDING,
            created_at=datetime(2026, 1, 5, 10, 0, 0),
        ),
        "order_002": TrackedOrder(
            order_id="order_002",
            entry_price=94500.0,
            tp_price=95000.0,
            quantity=0.001,
            status=OrderStatus.FILLED,
            created_at=datetime(2026, 1, 5, 9, 0, 0),
            filled_at=datetime(2026, 1, 5, 9, 30, 0),
            exchange_tp_order_id="tp_002",
        ),
        "order_003": TrackedOrder(
            order_id="order_003",
            entry_price=94000.0,
            tp_price=94500.0,
            quantity=0.001,
            status=OrderStatus.PENDING,
            created_at=datetime(2026, 1, 5, 8, 0, 0),
        ),
    }

    return tracker


class TestGetOrders:
    """Tests for GET /api/v1/orders endpoint."""

    def test_get_orders_no_tracker(self, client):
        """Test endpoint returns 503 when OrderTracker is not available."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=None):
            response = client.get("/api/v1/orders")

        assert response.status_code == 503
        assert "OrderTracker not available" in response.json()["detail"]

    def test_get_orders_empty(self, client):
        """Test endpoint returns empty list when no orders."""
        empty_tracker = OrderTracker()

        with patch("src.api.routes.orders.get_order_tracker", return_value=empty_tracker):
            response = client.get("/api/v1/orders")

        assert response.status_code == 200
        data = response.json()
        assert data["orders"] == []
        assert data["total"] == 0
        assert data["pending_count"] == 0
        assert data["filled_count"] == 0

    def test_get_orders_all(self, client, mock_order_tracker):
        """Test endpoint returns all orders."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            response = client.get("/api/v1/orders")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["orders"]) == 3
        assert data["pending_count"] == 2
        assert data["filled_count"] == 1

    def test_get_orders_filter_pending(self, client, mock_order_tracker):
        """Test filtering orders by PENDING status."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            response = client.get("/api/v1/orders?status=PENDING")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(o["status"] == "PENDING" for o in data["orders"])

    def test_get_orders_filter_filled(self, client, mock_order_tracker):
        """Test filtering orders by FILLED status."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            response = client.get("/api/v1/orders?status=FILLED")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["orders"][0]["status"] == "FILLED"
        assert data["orders"][0]["exchange_tp_order_id"] == "tp_002"

    def test_get_orders_filter_invalid_status(self, client, mock_order_tracker):
        """Test invalid status filter returns 400."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            response = client.get("/api/v1/orders?status=INVALID")

        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    def test_get_orders_pagination(self, client, mock_order_tracker):
        """Test pagination with limit and offset."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            # Get first 2 orders
            response = client.get("/api/v1/orders?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 2
        assert data["total"] == 3
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_get_orders_pagination_offset(self, client, mock_order_tracker):
        """Test pagination with offset."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            # Skip first 2, get rest
            response = client.get("/api/v1/orders?limit=10&offset=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 1
        assert data["total"] == 3

    def test_get_orders_sorted_by_created_at(self, client, mock_order_tracker):
        """Test orders are sorted by created_at descending."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            response = client.get("/api/v1/orders")

        assert response.status_code == 200
        data = response.json()

        # Verify descending order (newest first)
        dates = [o["created_at"] for o in data["orders"]]
        assert dates == sorted(dates, reverse=True)

    def test_get_orders_schema_fields(self, client, mock_order_tracker):
        """Test order schema has all required fields."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            response = client.get("/api/v1/orders")

        assert response.status_code == 200
        order = response.json()["orders"][0]

        # Check all required fields exist
        assert "order_id" in order
        assert "price" in order
        assert "tp_price" in order
        assert "quantity" in order
        assert "side" in order
        assert "status" in order
        assert "created_at" in order

    def test_get_orders_decimal_values(self, client, mock_order_tracker):
        """Test decimal values are properly formatted."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            response = client.get("/api/v1/orders?status=PENDING")

        assert response.status_code == 200
        order = response.json()["orders"][0]

        # Values should be serializable (string or number)
        assert Decimal(str(order["price"])) > 0
        assert Decimal(str(order["quantity"])) > 0

    def test_get_orders_case_insensitive_status(self, client, mock_order_tracker):
        """Test status filter is case insensitive."""
        with patch("src.api.routes.orders.get_order_tracker", return_value=mock_order_tracker):
            # Test lowercase
            response = client.get("/api/v1/orders?status=pending")

        assert response.status_code == 200
        data = response.json()
        assert all(o["status"] == "PENDING" for o in data["orders"])
