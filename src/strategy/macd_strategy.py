import warnings
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
import pandas_ta as ta

from config import MACDConfig
from src.utils.logger import macd_logger

# Suppress numpy overflow warnings - we'll handle them explicitly
warnings.filterwarnings("ignore", category=RuntimeWarning, message="overflow encountered")


class GridState(Enum):
    """Estados do grid baseado no MACD."""

    ACTIVATE = "activate"  # Vermelho claro + MACD < 0 → começa criar ordens
    ACTIVE = "active"  # Verde escuro ou verde claro com MACD <= 0 → continua criando
    PAUSE = "pause"  # Verde claro + MACD > 0 → para de criar, mantém existentes
    INACTIVE = "inactive"  # Vermelho escuro → cancela ordens pendentes
    WAIT = "wait"  # Vermelho claro + MACD >= 0 → aguarda


@dataclass
class MACDValues:
    """Current MACD indicator values."""

    macd_line: float
    signal_line: float
    histogram: float
    prev_histogram: float

    @property
    def is_histogram_negative(self) -> bool:
        return self.histogram < 0

    @property
    def is_histogram_positive(self) -> bool:
        return self.histogram > 0

    @property
    def is_histogram_rising(self) -> bool:
        return self.histogram > self.prev_histogram

    @property
    def is_histogram_falling(self) -> bool:
        return self.histogram < self.prev_histogram

    @property
    def is_macd_negative(self) -> bool:
        return self.macd_line < 0

    @property
    def is_macd_positive(self) -> bool:
        return self.macd_line > 0


class MACDStrategy:
    """
    Estratégia baseada no MACD para controlar o grid.

    Regras:
    - ATIVAR: hist < 0 e subindo, MACD < 0
    - PAUSA: hist > 0 e descendo, MACD > 0
    - Se verde claro mas MACD <= 0 → continua ATIVO
    - Se vermelho claro mas MACD >= 0 → ESPERA
    """

    def __init__(self, config: MACDConfig):
        self.fast = config.fast
        self.slow = config.slow
        self.signal = config.signal
        self.timeframe = config.timeframe
        self._prev_state: GridState | None = None
        self._cycle_activated: bool = False  # Só True após passar por ACTIVATE

    def calculate_macd(self, klines: pd.DataFrame) -> MACDValues | None:
        """
        Calculate MACD values from kline data.

        Args:
            klines: DataFrame with 'close' column

        Returns:
            MACDValues with current indicator values
        """
        if len(klines) < self.slow + self.signal:
            macd_logger.warning(
                f"Not enough data for MACD calculation. Need {self.slow + self.signal}, got {len(klines)}"
            )
            return None

        try:
            # Validate input data
            if klines["close"].isnull().any():
                macd_logger.warning("Klines contain null values, skipping MACD calculation")
                return None

            # Check for extreme values that might cause overflow
            close_max = klines["close"].max()
            close_min = klines["close"].min()
            if close_max > 1e10 or close_min < 0:
                macd_logger.warning(
                    f"Extreme close prices detected (min: {close_min}, max: {close_max}), skipping"
                )
                return None

            macd_df = ta.macd(
                klines["close"],
                fast=self.fast,
                slow=self.slow,
                signal=self.signal,
            )

            if macd_df is None or macd_df.empty:
                macd_logger.error("Failed to calculate MACD")
                return None

            macd_col = f"MACD_{self.fast}_{self.slow}_{self.signal}"
            signal_col = f"MACDs_{self.fast}_{self.slow}_{self.signal}"
            hist_col = f"MACDh_{self.fast}_{self.slow}_{self.signal}"

            # Safely extract values with overflow protection
            def safe_float(value):
                """Convert to float with overflow protection."""
                try:
                    result = float(value)
                    if np.isnan(result) or np.isinf(result):
                        return 0.0
                    # Clamp extreme values
                    if abs(result) > 1e10:
                        macd_logger.warning(f"Extreme MACD value detected: {result}, clamping to 0")
                        return 0.0
                    return result
                except (ValueError, OverflowError):
                    return 0.0

            return MACDValues(
                macd_line=safe_float(macd_df[macd_col].iloc[-1]),
                signal_line=safe_float(macd_df[signal_col].iloc[-1]),
                histogram=safe_float(macd_df[hist_col].iloc[-1]),
                prev_histogram=safe_float(macd_df[hist_col].iloc[-2]),
            )
        except Exception as e:
            macd_logger.error(f"Error calculating MACD: {e}")
            return None

    def get_state(self, klines: pd.DataFrame) -> GridState:
        """
        Determine grid state based on MACD values.

        Args:
            klines: DataFrame with OHLCV data

        Returns:
            GridState indicating what action the grid should take
        """
        macd = self.calculate_macd(klines)

        if macd is None:
            return GridState.WAIT

        # Determinar estado baseado nas regras
        state = self._determine_state(macd)

        # Controlar flag do ciclo
        if state == GridState.ACTIVATE:
            if not self._cycle_activated:
                self._cycle_activated = True
                macd_logger.info("Ciclo ATIVADO - Ordens podem ser criadas")
        elif state == GridState.INACTIVE:
            if self._cycle_activated:
                self._cycle_activated = False
                macd_logger.info("Ciclo DESATIVADO - Aguardando novo ACTIVATE")

        # Log mudanças de estado
        if state != self._prev_state:
            self._log_state_change(macd, state)
            self._prev_state = state

        return state

    def _determine_state(self, macd: MACDValues) -> GridState:
        """Determine state based on MACD values."""

        # Histograma negativo e subindo (vermelho claro)
        if macd.is_histogram_negative and macd.is_histogram_rising:
            if macd.is_macd_negative:
                return GridState.ACTIVATE  # Vermelho claro + MACD < 0 → ATIVA
            else:
                return GridState.WAIT  # Vermelho claro + MACD >= 0 → ESPERA

        # Histograma positivo e subindo (verde escuro)
        elif macd.is_histogram_positive and macd.is_histogram_rising:
            return GridState.ACTIVE  # Verde escuro → ATIVO

        # Histograma positivo e descendo (verde claro)
        elif macd.is_histogram_positive and macd.is_histogram_falling:
            if macd.is_macd_positive:
                return GridState.PAUSE  # Verde claro + MACD > 0 → PAUSA
            else:
                return GridState.ACTIVE  # Verde claro + MACD <= 0 → continua ATIVO

        # Histograma negativo e descendo (vermelho escuro)
        else:
            return GridState.INACTIVE  # Vermelho escuro → INATIVO

    def _log_state_change(self, macd: MACDValues, new_state: GridState) -> None:
        """Log state change with MACD values."""
        direction = "↑" if macd.is_histogram_rising else "↓"
        color = "verde" if macd.is_histogram_positive else "vermelho"
        shade = (
            "escuro"
            if (
                (macd.is_histogram_positive and macd.is_histogram_rising)
                or (macd.is_histogram_negative and macd.is_histogram_falling)
            )
            else "claro"
        )

        macd_logger.info(
            f"Estado: {new_state.value.upper()} | "
            f"Histograma: {macd.histogram:.2f} ({color} {shade} {direction}) | "
            f"MACD: {macd.macd_line:.2f}"
        )

    @property
    def is_cycle_activated(self) -> bool:
        """Check if cycle has been activated (passed through ACTIVATE state)."""
        return self._cycle_activated

    def manual_activate(self) -> bool:
        """
        Manually activate the cycle.

        Returns:
            True if activated successfully, False if not allowed
        """
        if self._prev_state == GridState.INACTIVE:
            macd_logger.warning("Não é possível ativar manualmente em INACTIVE (mercado em queda)")
            return False

        if not self._cycle_activated:
            self._cycle_activated = True
            macd_logger.info("Ciclo ATIVADO MANUALMENTE pelo usuário")
            return True
        else:
            macd_logger.info("Ciclo já está ativo")
            return True

    def manual_deactivate(self) -> None:
        """Manually deactivate the cycle."""
        if self._cycle_activated:
            self._cycle_activated = False
            macd_logger.info("Ciclo DESATIVADO MANUALMENTE pelo usuário")
        else:
            macd_logger.info("Ciclo já está inativo")

    def should_create_orders(self, state: GridState) -> bool:
        """Check if grid should create new orders."""
        # Só cria ordens se o ciclo foi ativado (passou por ACTIVATE)
        if not self._cycle_activated:
            return False
        return state in [GridState.ACTIVATE, GridState.ACTIVE]

    def should_cancel_pending(self, state: GridState) -> bool:
        """Check if grid should cancel pending orders."""
        return state == GridState.INACTIVE

    def should_wait(self, state: GridState) -> bool:
        """Check if grid should wait without action."""
        return state in [GridState.WAIT, GridState.PAUSE]

    def get_state_description(self, state: GridState) -> str:
        """Get human-readable description of state."""
        cycle_status = "🟢" if self._cycle_activated else "🔴"
        descriptions = {
            GridState.ACTIVATE: f"{cycle_status} ATIVANDO - Vermelho claro + MACD negativo",
            GridState.ACTIVE: f"{cycle_status} ATIVO - Criando ordens"
            if self._cycle_activated
            else f"{cycle_status} ATIVO - Aguardando ciclo",
            GridState.PAUSE: f"{cycle_status} PAUSADO - Verde claro + MACD positivo",
            GridState.INACTIVE: f"{cycle_status} INATIVO - Cancelando ordens pendentes",
            GridState.WAIT: f"{cycle_status} AGUARDANDO - Condições não atendidas",
        }
        return descriptions.get(state, "Desconhecido")
