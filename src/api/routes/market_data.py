"""Market data API endpoints for BTC price, funding rate, MACD, and grid range."""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_bingx_client, get_grid_calculator, get_macd_strategy
from src.api.schemas.market_data import (
    FundingRateResponse,
    GridRangeResponse,
    MACDResponse,
    MACDSignal,
    PriceResponse,
)
from src.api.websocket.connection_manager import get_connection_manager
from src.api.websocket.events import PriceUpdateEvent, WebSocketEvent
from src.client.bingx_client import BingXClient
from src.grid.grid_calculator import GridCalculator
from src.strategy.macd_strategy import MACDStrategy

router = APIRouter(prefix="/api/v1/market", tags=["Market Data"])
logger = logging.getLogger(__name__)

DEFAULT_SYMBOL = "BTC-USDT"


class PriceBroadcastThrottler:
    """Throttles price update broadcasts to avoid spam.

    Implements two throttling strategies:
    - Time-based: Maximum 1 broadcast per second
    - Change-based: Only broadcast if price changed more than 0.01%

    This prevents overwhelming clients with price updates that can occur
    hundreds of times per minute.
    """

    def __init__(self, min_interval_seconds: float = 1.0, min_change_percent: float = 0.01):
        """Initialize throttler.

        Args:
            min_interval_seconds: Minimum seconds between broadcasts
            min_change_percent: Minimum price change % to trigger broadcast
        """
        self.min_interval_seconds = min_interval_seconds
        self.min_change_percent = Decimal(str(min_change_percent))
        self.last_broadcast_time: datetime | None = None
        self.last_broadcast_price: Decimal | None = None

    def should_broadcast(self, current_price: Decimal) -> tuple[bool, str | None]:
        """Check if price update should be broadcast.

        Args:
            current_price: Current BTC price

        Returns:
            Tuple of (should_broadcast, reason_if_throttled)
        """
        now = datetime.now(UTC)

        # First broadcast - always allow
        if self.last_broadcast_time is None or self.last_broadcast_price is None:
            self.last_broadcast_time = now
            self.last_broadcast_price = current_price
            return (True, None)

        # Check time throttle
        time_elapsed = (now - self.last_broadcast_time).total_seconds()
        if time_elapsed < self.min_interval_seconds:
            return (False, f"time_throttle:{time_elapsed:.2f}s<{self.min_interval_seconds}s")

        # Check price change throttle
        price_change_percent = abs(
            (current_price - self.last_broadcast_price) / self.last_broadcast_price * 100
        )
        if price_change_percent < self.min_change_percent:
            return (
                False,
                f"change_throttle:{price_change_percent:.4f}%<{self.min_change_percent}%",
            )

        # Both conditions met - allow broadcast
        self.last_broadcast_time = now
        self.last_broadcast_price = current_price
        return (True, None)


# Global throttler instance
_price_throttler = PriceBroadcastThrottler()


@router.get("/price", response_model=PriceResponse)
async def get_price(
    client: Annotated[BingXClient, Depends(get_bingx_client)],
    symbol: Annotated[str, Query(description="Trading symbol")] = DEFAULT_SYMBOL,
):
    """Get current price with 24-hour statistics.

    Returns the current price, 24-hour change, high/low, and volume.
    Data is cached for 30 seconds.

    Also broadcasts price updates via WebSocket with throttling to prevent spam:
    - Maximum 1 broadcast per second
    - Only broadcasts if price changed more than 0.01%

    Args:
        client: BingX API client
        symbol: Trading symbol (default: BTC-USDT)

    Returns:
        PriceResponse: Current price with 24h statistics

    Raises:
        HTTPException: If API request fails
    """
    try:
        ticker = client.get_ticker_24h(symbol)

        # Build response
        current_price = Decimal(str(ticker["lastPrice"]))
        response = PriceResponse(
            symbol=symbol,
            price=current_price,
            change_24h=Decimal(str(ticker["priceChange"])),
            change_24h_percent=Decimal(str(ticker["priceChangePercent"])),
            high_24h=Decimal(str(ticker["highPrice"])),
            low_24h=Decimal(str(ticker["lowPrice"])),
            volume_24h=Decimal(str(ticker["volume"])),
            timestamp=datetime.now(UTC),
        )

        # Broadcast price update via WebSocket with throttling
        connection_manager = get_connection_manager()
        if connection_manager.active_connections_count > 0:
            should_broadcast, throttle_reason = _price_throttler.should_broadcast(current_price)

            if should_broadcast:
                # Create price update event
                price_event = PriceUpdateEvent(
                    symbol=symbol,
                    price=str(current_price),
                    change_24h=str(response.change_24h),
                    change_percent_24h=str(response.change_24h_percent),
                    volume_24h=str(response.volume_24h),
                    timestamp=response.timestamp,
                )

                # Broadcast to all connected clients
                await connection_manager.broadcast(WebSocketEvent.price_update(price_event))
                logger.debug(f"Price update broadcast: {symbol} @ ${current_price}")
            else:
                # Log throttle reason for debugging
                logger.debug(f"Price update throttled: {throttle_reason}")

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch price: {str(e)}") from e


@router.get("/funding", response_model=FundingRateResponse)
async def get_funding_rate(
    client: Annotated[BingXClient, Depends(get_bingx_client)],
    symbol: Annotated[str, Query(description="Trading symbol")] = DEFAULT_SYMBOL,
):
    """Get current funding rate and next settlement time.

    Returns the current funding rate, next funding time, and mark price.
    Data is cached for 5 minutes (funding rate changes infrequently).

    Args:
        client: BingX API client
        symbol: Trading symbol (default: BTC-USDT)

    Returns:
        FundingRateResponse: Funding rate data

    Raises:
        HTTPException: If API request fails
    """
    try:
        funding_data = client.get_funding_rate(symbol)

        funding_rate = Decimal(str(funding_data["lastFundingRate"]))
        funding_rate_percent = funding_rate * 100
        next_funding_time = datetime.fromtimestamp(funding_data["nextFundingTime"] / 1000, tz=UTC)

        return FundingRateResponse(
            symbol=symbol,
            funding_rate=funding_rate,
            funding_rate_percent=funding_rate_percent.quantize(Decimal("0.0001")),
            next_funding_time=next_funding_time,
            funding_interval_hours=8,  # BingX uses 8-hour funding intervals
            mark_price=Decimal(str(funding_data["markPrice"])),
            timestamp=datetime.now(UTC),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch funding rate: {str(e)}"
        ) from e


@router.get("/macd", response_model=MACDResponse)
async def get_macd(
    client: Annotated[BingXClient, Depends(get_bingx_client)],
    strategy: Annotated[MACDStrategy, Depends(get_macd_strategy)],
    symbol: Annotated[str, Query(description="Trading symbol")] = DEFAULT_SYMBOL,
):
    """Get MACD indicator values and signal.

    Calculates MACD (12, 26, 9) from 1-hour klines and returns:
    - MACD line, signal line, histogram values
    - Overall signal (bullish/bearish/neutral)
    - Whether histogram is rising or falling

    Data is based on klines cached for 60 seconds.

    Args:
        client: BingX API client
        strategy: MACD strategy for calculations
        symbol: Trading symbol (default: BTC-USDT)

    Returns:
        MACDResponse: MACD indicator data

    Raises:
        HTTPException: If API request or calculation fails
    """
    try:
        # Fetch klines for MACD calculation
        klines = client.get_klines(symbol, interval=strategy.timeframe, limit=100)

        # Calculate MACD values
        macd_values = strategy.calculate_macd(klines)

        if macd_values is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to calculate MACD: insufficient data or calculation error",
            )

        # Determine signal based on histogram and lines
        if macd_values.is_histogram_positive and macd_values.is_histogram_rising:
            signal = MACDSignal.BULLISH
        elif macd_values.is_histogram_negative and macd_values.is_histogram_falling:
            signal = MACDSignal.BEARISH
        else:
            signal = MACDSignal.NEUTRAL

        return MACDResponse(
            symbol=symbol,
            macd_line=Decimal(str(macd_values.macd_line)).quantize(Decimal("0.01")),
            signal_line=Decimal(str(macd_values.signal_line)).quantize(Decimal("0.01")),
            histogram=Decimal(str(macd_values.histogram)).quantize(Decimal("0.01")),
            signal=signal,
            histogram_rising=macd_values.is_histogram_rising,
            both_lines_negative=macd_values.are_both_lines_negative,
            timeframe=strategy.timeframe,
            timestamp=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch MACD: {str(e)}") from e


@router.get("/grid-range", response_model=GridRangeResponse)
async def get_grid_range(
    client: Annotated[BingXClient, Depends(get_bingx_client)],
    calculator: Annotated[GridCalculator, Depends(get_grid_calculator)],
    symbol: Annotated[str, Query(description="Trading symbol")] = DEFAULT_SYMBOL,
):
    """Get current grid range based on price and configuration.

    Returns the grid low/high bounds, range percentage, and number of
    possible grid levels within the range.

    Args:
        client: BingX API client
        calculator: Grid calculator with config
        symbol: Trading symbol (default: BTC-USDT)

    Returns:
        GridRangeResponse: Grid range data

    Raises:
        HTTPException: If API request fails
    """
    try:
        current_price = client.get_price(symbol)
        min_price = calculator.calculate_min_price(current_price)

        # Calculate number of levels possible in range
        spacing = calculator.calculate_spacing(current_price)
        levels_possible = int((current_price - min_price) / spacing) if spacing > 0 else 0

        # Price is always at 100% position (top of range since grid goes down)
        price_position = Decimal("100.0")

        return GridRangeResponse(
            symbol=symbol,
            current_price=Decimal(str(current_price)).quantize(Decimal("0.01")),
            grid_low=Decimal(str(min_price)).quantize(Decimal("0.01")),
            grid_high=Decimal(str(current_price)).quantize(Decimal("0.01")),
            range_percent=Decimal(str(calculator.range_percent)),
            price_position_percent=price_position,
            levels_possible=levels_possible,
            timestamp=datetime.now(UTC),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch grid range: {str(e)}") from e
