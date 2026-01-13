import os
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class SpacingType(Enum):
    FIXED = "fixed"
    PERCENT = "percent"


class ReactivationMode(Enum):
    IMMEDIATE = "immediate"
    FULL_CYCLE = "full_cycle"


class TradingMode(Enum):
    DEMO = "demo"  # Uses VST (virtual tokens)
    LIVE = "live"  # Uses real USDT


class MarginMode(Enum):
    CROSSED = "CROSSED"  # All positions share the same margin
    ISOLATED = "ISOLATED"  # Each position has separate margin


@dataclass
class BingXConfig:
    api_key: str
    secret_key: str
    is_demo: bool = True

    @property
    def base_url(self) -> str:
        if self.is_demo:
            return "https://open-api-vst.bingx.com"
        return "https://open-api.bingx.com"

    @property
    def ws_url(self) -> str:
        # WebSocket URL (same for both modes)
        return "wss://open-api-ws.bingx.com/market"


@dataclass
class TradingConfig:
    symbol: str
    leverage: int
    order_size_usdt: float  # Order size in USDT
    mode: TradingMode
    margin_mode: MarginMode = MarginMode.CROSSED

    @property
    def is_demo(self) -> bool:
        return self.mode == TradingMode.DEMO


@dataclass
class GridConfig:
    spacing_type: SpacingType
    spacing_value: float
    range_percent: float
    take_profit_percent: float
    max_total_orders: int = 10  # Total orders (pending LIMIT + open positions)
    enable_drift_repositioning: bool = True  # Enable grid repositioning when price drifts
    drift_threshold_multiplier: float = 1.5  # Reposition when gap > spacing * multiplier


@dataclass
class MACDConfig:
    fast: int
    slow: int
    signal: int
    timeframe: str


@dataclass
class DynamicTPConfig:
    """Configuration for dynamic take profit based on funding rate."""

    enabled: bool = False
    base_percent: float = 0.3  # Base TP percentage
    min_percent: float = 0.3  # Minimum TP (never below this)
    max_percent: float = 1.0  # Maximum TP (cap)
    safety_margin: float = 0.05  # Extra margin above funding cost (%)
    check_interval_minutes: int = 60  # How often to check positions


@dataclass
class BotStateConfig:
    """Configuration for bot state persistence."""

    restore_max_age_hours: int = 24  # Maximum hours to restore state after
    load_history_on_start: bool = True  # Load trade history on startup
    history_limit: int = 100  # Number of historical trades to load


@dataclass
class Config:
    bingx: BingXConfig
    trading: TradingConfig
    grid: GridConfig
    macd: MACDConfig
    dynamic_tp: DynamicTPConfig
    reactivation_mode: ReactivationMode
    bot_state: BotStateConfig


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config(
        bingx=BingXConfig(
            api_key=os.getenv("BINGX_API_KEY", ""),
            secret_key=os.getenv("BINGX_SECRET_KEY", ""),
            is_demo=os.getenv("TRADING_MODE", "demo").lower() == "demo",
        ),
        trading=TradingConfig(
            symbol=os.getenv("SYMBOL", "BTC-USDT"),
            leverage=int(os.getenv("LEVERAGE", "10")),
            order_size_usdt=float(os.getenv("ORDER_SIZE_USDT", "100")),
            mode=TradingMode(os.getenv("TRADING_MODE", "demo")),
            margin_mode=MarginMode(os.getenv("MARGIN_MODE", "CROSSED")),
        ),
        grid=GridConfig(
            spacing_type=SpacingType(os.getenv("GRID_SPACING_TYPE", "fixed")),
            spacing_value=float(os.getenv("GRID_SPACING_VALUE", "100")),
            range_percent=float(os.getenv("GRID_RANGE_PERCENT", "5")),
            take_profit_percent=float(os.getenv("TAKE_PROFIT_PERCENT", "1.0")),
            max_total_orders=int(os.getenv("MAX_TOTAL_ORDERS", "10")),
            enable_drift_repositioning=os.getenv("GRID_DRIFT_ENABLED", "true").lower() == "true",
            drift_threshold_multiplier=float(os.getenv("GRID_DRIFT_THRESHOLD", "1.5")),
        ),
        macd=MACDConfig(
            fast=int(os.getenv("MACD_FAST", "12")),
            slow=int(os.getenv("MACD_SLOW", "26")),
            signal=int(os.getenv("MACD_SIGNAL", "9")),
            timeframe=os.getenv("MACD_TIMEFRAME", "1h"),
        ),
        dynamic_tp=DynamicTPConfig(
            enabled=os.getenv("TP_DYNAMIC_ENABLED", "false").lower() == "true",
            base_percent=float(os.getenv("TP_BASE_PERCENT", "0.3")),
            min_percent=float(os.getenv("TP_MIN_PERCENT", "0.3")),
            max_percent=float(os.getenv("TP_MAX_PERCENT", "1.0")),
            safety_margin=float(os.getenv("TP_SAFETY_MARGIN", "0.05")),
            check_interval_minutes=int(os.getenv("TP_CHECK_INTERVAL_MIN", "60")),
        ),
        reactivation_mode=ReactivationMode(os.getenv("REACTIVATION_MODE", "immediate")),
        bot_state=BotStateConfig(
            restore_max_age_hours=int(os.getenv("STATE_RESTORE_MAX_AGE_HOURS", "24")),
            load_history_on_start=os.getenv("LOAD_HISTORY_ON_START", "true").lower() == "true",
            history_limit=int(os.getenv("HISTORY_LIMIT", "100")),
        ),
    )
