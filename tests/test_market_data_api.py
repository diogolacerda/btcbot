"""Tests for market data API endpoints."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_bingx_client, get_grid_calculator, get_macd_strategy
from src.api.main import app


@pytest.fixture
def mock_bingx_client():
    """Create a mock BingXClient."""
    mock = MagicMock()

    # Mock get_ticker_24h response
    mock.get_ticker_24h.return_value = {
        "lastPrice": "99500.00",
        "priceChange": "1500.00",
        "priceChangePercent": "1.53",
        "highPrice": "100200.00",
        "lowPrice": "97800.00",
        "volume": "12345.67",
    }

    # Mock get_funding_rate response
    mock.get_funding_rate.return_value = {
        "lastFundingRate": "0.0001",
        "nextFundingTime": 1704556800000,  # Unix timestamp in ms
        "markPrice": "99500.50",
    }

    # Mock get_price response
    mock.get_price.return_value = 99500.0

    # Mock get_klines response
    mock.get_klines.return_value = [{"close": 99000 + i * 100} for i in range(100)]

    return mock


@pytest.fixture
def mock_macd_strategy():
    """Create a mock MACDStrategy."""
    mock = MagicMock()
    mock.timeframe = "1h"

    # Mock MACD values
    macd_values = MagicMock()
    macd_values.macd_line = 150.75
    macd_values.signal_line = 125.50
    macd_values.histogram = 25.25
    macd_values.is_histogram_positive = True
    macd_values.is_histogram_rising = True
    macd_values.is_histogram_negative = False
    macd_values.is_histogram_falling = False
    macd_values.are_both_lines_negative = False

    mock.calculate_macd.return_value = macd_values

    return mock


@pytest.fixture
def mock_grid_calculator():
    """Create a mock GridCalculator."""
    mock = MagicMock()
    mock.range_percent = 2.0
    mock.calculate_min_price.return_value = 97510.0
    mock.calculate_spacing.return_value = 100.0

    return mock


@pytest.fixture
def client(mock_bingx_client, mock_macd_strategy, mock_grid_calculator):
    """Create test client with overridden dependencies."""

    def override_get_bingx_client():
        return mock_bingx_client

    def override_get_macd_strategy():
        return mock_macd_strategy

    def override_get_grid_calculator():
        return mock_grid_calculator

    app.dependency_overrides[get_bingx_client] = override_get_bingx_client
    app.dependency_overrides[get_macd_strategy] = override_get_macd_strategy
    app.dependency_overrides[get_grid_calculator] = override_get_grid_calculator

    yield TestClient(app)

    app.dependency_overrides.clear()


class TestGetPriceEndpoint:
    """Tests for GET /api/v1/market/price endpoint."""

    def test_get_price_success(self, client, mock_bingx_client):
        """Test successful price retrieval."""
        response = client.get("/api/v1/market/price")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "BTC-USDT"
        assert Decimal(str(data["price"])) == Decimal("99500.00")
        assert Decimal(str(data["change_24h"])) == Decimal("1500.00")
        assert Decimal(str(data["change_24h_percent"])) == Decimal("1.53")
        assert Decimal(str(data["high_24h"])) == Decimal("100200.00")
        assert Decimal(str(data["low_24h"])) == Decimal("97800.00")
        assert "timestamp" in data

        mock_bingx_client.get_ticker_24h.assert_called_once_with("BTC-USDT")

    def test_get_price_custom_symbol(self, client, mock_bingx_client):
        """Test price retrieval with custom symbol."""
        response = client.get("/api/v1/market/price", params={"symbol": "ETH-USDT"})

        assert response.status_code == 200
        mock_bingx_client.get_ticker_24h.assert_called_once_with("ETH-USDT")

    def test_get_price_api_error(self, client, mock_bingx_client):
        """Test price retrieval when API fails."""
        mock_bingx_client.get_ticker_24h.side_effect = Exception("API connection error")

        response = client.get("/api/v1/market/price")

        assert response.status_code == 500
        assert "Failed to fetch price" in response.json()["detail"]


class TestGetFundingRateEndpoint:
    """Tests for GET /api/v1/market/funding endpoint."""

    def test_get_funding_rate_success(self, client, mock_bingx_client):
        """Test successful funding rate retrieval."""
        response = client.get("/api/v1/market/funding")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "BTC-USDT"
        assert Decimal(str(data["funding_rate"])) == Decimal("0.0001")
        assert Decimal(str(data["funding_rate_percent"])) == Decimal("0.0100")
        assert data["funding_interval_hours"] == 8
        assert Decimal(str(data["mark_price"])) == Decimal("99500.50")
        assert "next_funding_time" in data
        assert "timestamp" in data

        mock_bingx_client.get_funding_rate.assert_called_once_with("BTC-USDT")

    def test_get_funding_rate_custom_symbol(self, client, mock_bingx_client):
        """Test funding rate retrieval with custom symbol."""
        response = client.get("/api/v1/market/funding", params={"symbol": "ETH-USDT"})

        assert response.status_code == 200
        mock_bingx_client.get_funding_rate.assert_called_once_with("ETH-USDT")

    def test_get_funding_rate_api_error(self, client, mock_bingx_client):
        """Test funding rate retrieval when API fails."""
        mock_bingx_client.get_funding_rate.side_effect = Exception("API timeout")

        response = client.get("/api/v1/market/funding")

        assert response.status_code == 500
        assert "Failed to fetch funding rate" in response.json()["detail"]


class TestGetMACDEndpoint:
    """Tests for GET /api/v1/market/macd endpoint."""

    def test_get_macd_success_bullish(self, client, mock_bingx_client, mock_macd_strategy):
        """Test successful MACD retrieval with bullish signal."""
        response = client.get("/api/v1/market/macd")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "BTC-USDT"
        assert Decimal(str(data["macd_line"])) == Decimal("150.75")
        assert Decimal(str(data["signal_line"])) == Decimal("125.50")
        assert Decimal(str(data["histogram"])) == Decimal("25.25")
        assert data["signal"] == "bullish"
        assert data["histogram_rising"] is True
        assert data["both_lines_negative"] is False
        assert data["timeframe"] == "1h"
        assert "timestamp" in data

        mock_bingx_client.get_klines.assert_called_once()
        mock_macd_strategy.calculate_macd.assert_called_once()

    def test_get_macd_bearish_signal(self, client, mock_bingx_client, mock_macd_strategy):
        """Test MACD with bearish signal."""
        # Configure bearish conditions
        macd_values = mock_macd_strategy.calculate_macd.return_value
        macd_values.is_histogram_positive = False
        macd_values.is_histogram_negative = True
        macd_values.is_histogram_rising = False
        macd_values.is_histogram_falling = True
        macd_values.histogram = -50.00

        response = client.get("/api/v1/market/macd")

        assert response.status_code == 200
        data = response.json()

        assert data["signal"] == "bearish"

    def test_get_macd_neutral_signal(self, client, mock_bingx_client, mock_macd_strategy):
        """Test MACD with neutral signal."""
        # Configure neutral conditions (positive but falling)
        macd_values = mock_macd_strategy.calculate_macd.return_value
        macd_values.is_histogram_positive = True
        macd_values.is_histogram_rising = False
        macd_values.is_histogram_negative = False
        macd_values.is_histogram_falling = True

        response = client.get("/api/v1/market/macd")

        assert response.status_code == 200
        data = response.json()

        assert data["signal"] == "neutral"

    def test_get_macd_custom_symbol(self, client, mock_bingx_client):
        """Test MACD retrieval with custom symbol."""
        response = client.get("/api/v1/market/macd", params={"symbol": "ETH-USDT"})

        assert response.status_code == 200
        # Verify symbol in response
        data = response.json()
        assert data["symbol"] == "ETH-USDT"

    def test_get_macd_calculation_error(self, client, mock_bingx_client, mock_macd_strategy):
        """Test MACD when calculation returns None."""
        mock_macd_strategy.calculate_macd.return_value = None

        response = client.get("/api/v1/market/macd")

        assert response.status_code == 500
        assert "Failed to calculate MACD" in response.json()["detail"]

    def test_get_macd_api_error(self, client, mock_bingx_client):
        """Test MACD retrieval when API fails."""
        mock_bingx_client.get_klines.side_effect = Exception("Network error")

        response = client.get("/api/v1/market/macd")

        assert response.status_code == 500
        assert "Failed to fetch MACD" in response.json()["detail"]


class TestGetGridRangeEndpoint:
    """Tests for GET /api/v1/market/grid-range endpoint."""

    def test_get_grid_range_success(self, client, mock_bingx_client, mock_grid_calculator):
        """Test successful grid range retrieval."""
        response = client.get("/api/v1/market/grid-range")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "BTC-USDT"
        assert Decimal(str(data["current_price"])) == Decimal("99500.00")
        assert Decimal(str(data["grid_low"])) == Decimal("97510.00")
        assert Decimal(str(data["grid_high"])) == Decimal("99500.00")
        assert Decimal(str(data["range_percent"])) == Decimal("2.0")
        assert Decimal(str(data["price_position_percent"])) == Decimal("100.0")
        assert data["levels_possible"] == 19  # (99500 - 97510) / 100 = 19
        assert "timestamp" in data

        mock_bingx_client.get_price.assert_called_once_with("BTC-USDT")
        mock_grid_calculator.calculate_min_price.assert_called_once_with(99500.0)
        mock_grid_calculator.calculate_spacing.assert_called_once_with(99500.0)

    def test_get_grid_range_custom_symbol(self, client, mock_bingx_client):
        """Test grid range retrieval with custom symbol."""
        response = client.get("/api/v1/market/grid-range", params={"symbol": "ETH-USDT"})

        assert response.status_code == 200
        mock_bingx_client.get_price.assert_called_once_with("ETH-USDT")

    def test_get_grid_range_zero_spacing(self, client, mock_bingx_client, mock_grid_calculator):
        """Test grid range when spacing is zero (edge case)."""
        mock_grid_calculator.calculate_spacing.return_value = 0

        response = client.get("/api/v1/market/grid-range")

        assert response.status_code == 200
        data = response.json()

        assert data["levels_possible"] == 0

    def test_get_grid_range_api_error(self, client, mock_bingx_client):
        """Test grid range retrieval when API fails."""
        mock_bingx_client.get_price.side_effect = Exception("API unavailable")

        response = client.get("/api/v1/market/grid-range")

        assert response.status_code == 500
        assert "Failed to fetch grid range" in response.json()["detail"]


class TestMarketDataSchemas:
    """Tests for market data response schema validation."""

    def test_price_response_has_all_fields(self, client):
        """Test price response has all required fields."""
        response = client.get("/api/v1/market/price")

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "symbol",
            "price",
            "change_24h",
            "change_24h_percent",
            "high_24h",
            "low_24h",
            "volume_24h",
            "timestamp",
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_funding_response_has_all_fields(self, client):
        """Test funding rate response has all required fields."""
        response = client.get("/api/v1/market/funding")

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "symbol",
            "funding_rate",
            "funding_rate_percent",
            "next_funding_time",
            "funding_interval_hours",
            "mark_price",
            "timestamp",
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_macd_response_has_all_fields(self, client):
        """Test MACD response has all required fields."""
        response = client.get("/api/v1/market/macd")

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "symbol",
            "macd_line",
            "signal_line",
            "histogram",
            "signal",
            "histogram_rising",
            "both_lines_negative",
            "timeframe",
            "timestamp",
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_grid_range_response_has_all_fields(self, client):
        """Test grid range response has all required fields."""
        response = client.get("/api/v1/market/grid-range")

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "symbol",
            "current_price",
            "grid_low",
            "grid_high",
            "range_percent",
            "price_position_percent",
            "levels_possible",
            "timestamp",
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestMarketDataCaching:
    """Tests related to caching behavior of market data endpoints."""

    def test_price_endpoint_calls_api(self, client, mock_bingx_client):
        """Test that price endpoint calls the BingX API."""
        response = client.get("/api/v1/market/price")

        assert response.status_code == 200
        assert mock_bingx_client.get_ticker_24h.call_count == 1

    def test_funding_endpoint_calls_api(self, client, mock_bingx_client):
        """Test that funding endpoint calls the BingX API."""
        response = client.get("/api/v1/market/funding")

        assert response.status_code == 200
        assert mock_bingx_client.get_funding_rate.call_count == 1

    def test_macd_endpoint_calls_api(self, client, mock_bingx_client):
        """Test that MACD endpoint fetches klines from API."""
        response = client.get("/api/v1/market/macd")

        assert response.status_code == 200
        assert mock_bingx_client.get_klines.call_count == 1
