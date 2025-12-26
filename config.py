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

    @property
    def is_demo(self) -> bool:
        return self.mode == TradingMode.DEMO


@dataclass
class GridConfig:
    spacing_type: SpacingType
    spacing_value: float
    range_percent: float
    take_profit_percent: float
    max_orders: int = 10  # Maximum number of grid orders


@dataclass
class MACDConfig:
    fast: int
    slow: int
    signal: int
    timeframe: str


@dataclass
class Config:
    bingx: BingXConfig
    trading: TradingConfig
    grid: GridConfig
    macd: MACDConfig
    reactivation_mode: ReactivationMode


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
        ),
        grid=GridConfig(
            spacing_type=SpacingType(os.getenv("GRID_SPACING_TYPE", "fixed")),
            spacing_value=float(os.getenv("GRID_SPACING_VALUE", "100")),
            range_percent=float(os.getenv("GRID_RANGE_PERCENT", "5")),
            take_profit_percent=float(os.getenv("TAKE_PROFIT_PERCENT", "1.0")),
            max_orders=int(os.getenv("MAX_ORDERS", "10")),
        ),
        macd=MACDConfig(
            fast=int(os.getenv("MACD_FAST", "12")),
            slow=int(os.getenv("MACD_SLOW", "26")),
            signal=int(os.getenv("MACD_SIGNAL", "9")),
            timeframe=os.getenv("MACD_TIMEFRAME", "1h"),
        ),
        reactivation_mode=ReactivationMode(os.getenv("REACTIVATION_MODE", "immediate")),
    )
