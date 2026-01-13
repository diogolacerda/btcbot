"""
EMA filter for grid trading.

Implements EMA direction-based filtering for the Impulse System (Alexander Elder).
Determines if orders should be created based on EMA trend direction.
"""

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from src.filters.base import Filter, FilterState
from src.utils.logger import main_logger

if TYPE_CHECKING:
    from src.database.repositories.ema_filter_config_repository import (
        EMAFilterConfigRepository,
    )


class EMADirection(str, Enum):
    """Direction of EMA movement."""

    RISING = "rising"
    FALLING = "falling"
    FLAT = "flat"


class EMAFilter(Filter):
    """
    Filter based on EMA direction.

    Part of the Impulse System (Alexander Elder). Uses EMA direction
    to determine if trading should be allowed:
    - Rising EMA: Bullish trend, typically allow trades
    - Falling EMA: Bearish trend, typically protect orders
    - Flat EMA: Neutral, behavior configurable

    When enabled:
    - Calculates EMA from klines data
    - Determines direction by comparing current vs previous EMA
    - Allows/blocks trades based on direction and configuration

    When disabled:
    - Always allows trades (bypasses EMA logic)
    """

    def __init__(
        self,
        period: int = 13,
        timeframe: str = "1h",
        allow_on_rising: bool = True,
        allow_on_falling: bool = False,
        *,
        enabled: bool | None = None,
    ):
        """
        Initialize EMA filter.

        Args:
            period: EMA period for calculation (default 13, Elder's recommendation)
            timeframe: Candle timeframe for EMA calculation
            allow_on_rising: Allow trades when EMA is rising (default True)
            allow_on_falling: Allow trades when EMA is falling (default False)
            enabled: Initial enabled state. If None, defaults to True.
        """
        super().__init__(
            name="ema",
            description="EMA Direction Filter (Impulse System)",
        )
        self._period = period
        self._timeframe = timeframe
        self._allow_on_rising = allow_on_rising
        self._allow_on_falling = allow_on_falling

        # EMA state
        self._current_ema: float | None = None
        self._previous_ema: float | None = None
        self._direction = EMADirection.FLAT
        self._last_close: float | None = None

        # Set initial enabled state if provided
        if enabled is not None:
            self._enabled = enabled

    @property
    def period(self) -> int:
        """Get EMA period."""
        return self._period

    @period.setter
    def period(self, value: int) -> None:
        """Set EMA period."""
        self._period = value

    @property
    def timeframe(self) -> str:
        """Get calculation timeframe."""
        return self._timeframe

    @timeframe.setter
    def timeframe(self, value: str) -> None:
        """Set calculation timeframe."""
        self._timeframe = value

    @property
    def allow_on_rising(self) -> bool:
        """Get allow_on_rising setting."""
        return self._allow_on_rising

    @allow_on_rising.setter
    def allow_on_rising(self, value: bool) -> None:
        """Set allow_on_rising setting."""
        self._allow_on_rising = value

    @property
    def allow_on_falling(self) -> bool:
        """Get allow_on_falling setting."""
        return self._allow_on_falling

    @allow_on_falling.setter
    def allow_on_falling(self, value: bool) -> None:
        """Set allow_on_falling setting."""
        self._allow_on_falling = value

    @property
    def direction(self) -> EMADirection:
        """Get current EMA direction."""
        return self._direction

    @property
    def current_ema(self) -> float | None:
        """Get current EMA value."""
        return self._current_ema

    def _calculate_ema(self, closes: list[float]) -> float | None:
        """
        Calculate EMA from closing prices.

        Uses the standard EMA formula:
        EMA = Close * multiplier + Previous_EMA * (1 - multiplier)
        where multiplier = 2 / (period + 1)

        Args:
            closes: List of closing prices (oldest first)

        Returns:
            EMA value or None if not enough data
        """
        if len(closes) < self._period:
            return None

        multiplier = 2 / (self._period + 1)

        # Initialize with SMA for the first period
        ema = sum(closes[: self._period]) / self._period

        # Calculate EMA for remaining data points
        for close in closes[self._period :]:
            ema = close * multiplier + ema * (1 - multiplier)

        return ema

    def _determine_direction(self) -> EMADirection:
        """
        Determine EMA direction based on current and previous values.

        Returns:
            EMADirection enum value
        """
        if self._current_ema is None or self._previous_ema is None:
            return EMADirection.FLAT

        # Use a small threshold to avoid noise (0.001% change)
        threshold = self._previous_ema * 0.00001

        if self._current_ema > self._previous_ema + threshold:
            return EMADirection.RISING
        elif self._current_ema < self._previous_ema - threshold:
            return EMADirection.FALLING
        else:
            return EMADirection.FLAT

    def update(self, klines: list) -> None:
        """
        Update EMA calculation with new klines data.

        Extracts closing prices from klines and calculates EMA.
        Updates direction based on current vs previous EMA.

        Args:
            klines: List of klines data. Each kline should have close price at index 4.
                   Format: [open_time, open, high, low, close, volume, ...]
        """
        if not klines or len(klines) < self._period + 1:
            main_logger.debug(
                f"EMA filter: insufficient klines ({len(klines) if klines else 0} < {self._period + 1})"
            )
            return

        try:
            # Extract closing prices (index 4 in standard kline format)
            closes = [float(kline[4]) for kline in klines]

            # Store previous EMA for direction calculation
            self._previous_ema = self._current_ema

            # Calculate current EMA with all data except last candle (for previous)
            if len(closes) > self._period:
                # Calculate EMA up to second-to-last candle first
                prev_closes = closes[:-1]
                self._previous_ema = self._calculate_ema(prev_closes)

            # Calculate current EMA with all data
            self._current_ema = self._calculate_ema(closes)
            self._last_close = closes[-1] if closes else None

            # Determine direction
            self._direction = self._determine_direction()

            main_logger.debug(
                f"EMA filter updated: period={self._period}, "
                f"ema={f'{self._current_ema:.2f}' if self._current_ema is not None else 'N/A'}, "
                f"direction={self._direction.value}"
            )

        except (IndexError, ValueError, TypeError) as e:
            main_logger.warning(f"EMA filter: error processing klines: {e}")

    def should_allow_trade(self) -> bool:
        """
        Check if trade should be allowed based on EMA direction.

        When filter is disabled, always returns True.
        When filter is enabled, checks direction against configuration.

        Returns:
            True if trade is allowed, False otherwise
        """
        if not self.enabled:
            return True

        # If no EMA calculated yet, allow trades (fail-open)
        if self._current_ema is None:
            return True

        if self._direction == EMADirection.RISING:
            return self._allow_on_rising
        elif self._direction == EMADirection.FALLING:
            return self._allow_on_falling
        else:  # FLAT
            # For flat, use the more permissive setting
            return self._allow_on_rising or self._allow_on_falling

    def should_protect_orders(self) -> bool:
        """
        Check if existing orders should be protected (not cancelled).

        When EMA is rising (bullish), existing orders should be protected.
        This is the inverse of the falling trade logic.

        Returns:
            True if orders should be protected, False otherwise
        """
        if not self.enabled:
            return False

        return self._direction == EMADirection.RISING

    def get_state(self) -> FilterState:
        """
        Get current filter state with EMA details.

        Returns:
            FilterState with EMA indicators and configuration
        """
        details = {
            "period": self._period,
            "timeframe": self._timeframe,
            "current_ema": round(self._current_ema, 2) if self._current_ema else None,
            "previous_ema": round(self._previous_ema, 2) if self._previous_ema else None,
            "direction": self._direction.value,
            "last_close": round(self._last_close, 2) if self._last_close else None,
            "allow_on_rising": self._allow_on_rising,
            "allow_on_falling": self._allow_on_falling,
        }

        return FilterState(
            enabled=self.enabled,
            description=self.description,
            details=details,
        )

    async def load_config_from_db(
        self,
        strategy_id: UUID,
        repository: "EMAFilterConfigRepository",  # noqa: F821
    ) -> bool:
        """
        Load EMA filter configuration from database.

        Args:
            strategy_id: UUID of the strategy to load config for.
            repository: EMAFilterConfigRepository instance.

        Returns:
            True if config loaded successfully, False otherwise.
        """
        try:
            config = repository.get_by_strategy(strategy_id)
            if not config:
                main_logger.debug(f"No EMA filter config found for strategy {strategy_id}")
                return False

            # Update instance with DB values
            self._enabled = config.enabled
            self._period = config.period
            self._timeframe = config.timeframe
            self._allow_on_rising = config.allow_on_rising
            self._allow_on_falling = config.allow_on_falling

            main_logger.info(
                f"EMA filter config loaded: enabled={config.enabled}, "
                f"period={config.period}, timeframe={config.timeframe}"
            )
            return True

        except Exception as e:
            main_logger.error(f"Error loading EMA filter config: {e}")
            return False

    def sync_config(
        self,
        enabled: bool,
        period: int,
        timeframe: str,
        allow_on_rising: bool,
        allow_on_falling: bool,
    ) -> None:
        """
        Sync filter configuration with provided values.

        Used when config is already loaded by another component.

        Args:
            enabled: Whether the filter is enabled.
            period: EMA period.
            timeframe: Calculation timeframe.
            allow_on_rising: Allow trades when EMA is rising.
            allow_on_falling: Allow trades when EMA is falling.
        """
        old_enabled = self._enabled
        self._enabled = enabled
        self._period = period
        self._timeframe = timeframe
        self._allow_on_rising = allow_on_rising
        self._allow_on_falling = allow_on_falling

        if old_enabled != enabled:
            action = "enabled" if enabled else "disabled"
            main_logger.info(f"EMA filter {action}")
