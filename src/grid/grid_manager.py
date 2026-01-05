import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from config import Config
from src.client.bingx_client import BingXClient
from src.client.websocket_client import BingXAccountWebSocket
from src.filters.macd_filter import MACDFilter
from src.filters.registry import FilterRegistry
from src.grid.dynamic_tp_manager import DynamicTPManager
from src.grid.grid_calculator import GridCalculator, GridLevel
from src.grid.order_tracker import OrderTracker
from src.strategy.macd_strategy import GridState, MACDStrategy
from src.utils.logger import main_logger, orders_logger

if TYPE_CHECKING:
    from src.database.repositories.activity_event_repository import (
        ActivityEventRepository,
    )
    from src.database.repositories.bot_state_repository import BotStateRepository
    from src.database.repositories.grid_config_repository import GridConfigRepository
    from src.database.repositories.trade_repository import TradeRepository
    from src.database.repositories.trading_config_repository import TradingConfigRepository


@dataclass
class GridStatus:
    """Current status of the grid."""

    state: GridState
    current_price: float
    pending_orders: int
    open_positions: int
    total_trades: int
    total_pnl: float
    macd_line: float
    histogram: float
    cycle_activated: bool = False  # True if cycle has been activated
    margin_error: bool = False  # True if paused due to margin error
    rate_limited: bool = False  # True if rate limited


class GridManager:
    """
    Manages the grid trading system.

    Coordinates:
    - MACD strategy for grid activation
    - Grid calculator for level determination
    - Order tracker for state management
    - BingX client for order execution
    """

    def __init__(
        self,
        config: Config,
        client: BingXClient,
        on_order_created: Callable | None = None,
        on_order_filled: Callable | None = None,
        on_tp_hit: Callable | None = None,
        on_state_change: Callable | None = None,
        account_id: UUID | None = None,
        bot_state_repository: "BotStateRepository | None" = None,
        trade_repository: "TradeRepository | None" = None,
        grid_config_repository: "GridConfigRepository | None" = None,
        trading_config_repository: "TradingConfigRepository | None" = None,
        activity_event_repository: "ActivityEventRepository | None" = None,
    ):
        self.config = config
        self.client = client
        self.symbol = config.trading.symbol
        self.order_size = config.trading.order_size_usdt

        # Database repositories for dynamic config
        self._account_id = account_id
        self._grid_config_repo = grid_config_repository
        self._trading_config_repository = trading_config_repository

        self.strategy = MACDStrategy(
            config.macd,
            account_id=account_id,
            bot_state_repository=bot_state_repository,
        )
        self.calculator = GridCalculator(config.grid)
        self.tracker = OrderTracker(
            trade_repository=trade_repository,
            account_id=account_id,
        )

        # Database repositories for dynamic config
        self._account_id = account_id
        self._grid_config_repo = grid_config_repository
        self._trading_config_repo = trading_config_repository
        self._activity_event_repository = activity_event_repository

        # Filter system
        self._filter_registry = FilterRegistry()
        self._macd_filter = MACDFilter(self.strategy)
        self._filter_registry.register(self._macd_filter)

        # Register callbacks for filter state changes
        self._filter_registry.set_on_filter_change_callback(self._on_filter_change)
        self._macd_filter.set_on_state_change_callback(self._on_macd_state_change)

        self._current_state = GridState.WAIT
        self._current_price = 0.0
        self._last_macd_line = 0.0
        self._last_histogram = 0.0
        self._running = False

        # Error handling
        self._margin_error = False  # Pause order creation on margin error
        self._margin_error_time = 0.0  # When the error occurred
        self._rate_limited_until = 0.0  # Rate limit backoff
        self._consecutive_errors = 0  # Track consecutive errors

        # WebSocket
        self._account_ws: BingXAccountWebSocket | None = None
        self._listen_key: str = ""
        self._ws_task: asyncio.Task | None = None
        self._keepalive_task: asyncio.Task | None = None

        # Callbacks
        self._on_order_created = on_order_created
        self._on_order_filled = on_order_filled
        self._on_tp_hit = on_tp_hit
        self._on_state_change = on_state_change

        # Dynamic TP Manager
        self.dynamic_tp: DynamicTPManager | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_state(self) -> GridState:
        return self._current_state

    def _log_activity_event(
        self,
        event_type: str,
        description: str,
        event_data: dict | None = None,
    ) -> None:
        """Log an activity event to the database (non-blocking).

        Creates an activity event record for the dashboard timeline.
        Runs asynchronously to avoid blocking the main bot loop.

        Args:
            event_type: Type of event (from EventType enum).
            description: Human-readable description of the event.
            event_data: Optional additional event data as dictionary.
        """
        if not self._activity_event_repository or not self._account_id:
            return

        # Capture values for closure (type narrowing)
        repo = self._activity_event_repository
        account_id = self._account_id

        async def _persist_event() -> None:
            try:
                await repo.create_event(
                    account_id=account_id,
                    event_type=event_type,
                    description=description,
                    event_data=event_data,
                )
            except Exception as e:
                main_logger.warning(f"Failed to log activity event: {e}")

        # Schedule task in background (fire and forget)
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(_persist_event())
        except RuntimeError:
            main_logger.debug("No event loop, skipping activity event logging")

    def _get_anchor_mode_value(self) -> str:
        """
        Get anchor mode value, handling both string and enum types.

        Returns string value regardless of whether anchor_mode is stored as
        a string (from database) or GridAnchorMode enum (from config).

        Returns:
            Anchor mode value as string ("none", "hundred", etc.)
        """
        anchor_mode = self.calculator.anchor_mode
        # If it's already a string (from database), return it directly
        if isinstance(anchor_mode, str):
            return anchor_mode
        # If it's an enum (from config), return its value
        return anchor_mode.value

    async def _refresh_grid_calculator(self) -> None:
        """
        Refresh grid calculator with latest config from database.

        Fetches grid config and trading config from database (if repositories are set)
        and updates the calculator's properties.

        Falls back to config.py values if repositories are not set or database is unavailable.
        """
        if (
            not self._grid_config_repo
            or not self._trading_config_repository
            or not self._account_id
        ):
            # No database integration - use config.py values (already set)
            return

        try:
            # Fetch grid config from database (or create with defaults)
            grid_config = await self._grid_config_repo.get_or_create(self._account_id)

            # Fetch trading config from database
            trading_config = await self._trading_config_repository.get_by_account(self._account_id)

            # Update calculator properties with database values
            self.calculator.spacing_type = grid_config.spacing_type  # type: ignore[assignment]
            self.calculator.spacing_value = float(grid_config.spacing_value)
            self.calculator.range_percent = float(grid_config.range_percent)
            self.calculator.max_total_orders = grid_config.max_total_orders
            self.calculator.anchor_mode = grid_config.anchor_mode  # type: ignore[assignment]
            self.calculator.anchor_value = float(grid_config.anchor_value)

            # Update take_profit_percent from trading config
            if trading_config:
                self.calculator.tp_percent = float(trading_config.take_profit_percent)

        except Exception as e:
            main_logger.warning(
                f"Failed to refresh grid config from database: {e}. Using config.py values."
            )

    def get_status(self) -> GridStatus:
        """Get current grid status."""
        stats = self.tracker.get_stats()
        return GridStatus(
            state=self._current_state,
            current_price=self._current_price,
            pending_orders=stats["pending_orders"],
            open_positions=stats["open_positions"],
            total_trades=stats["total_trades"],
            total_pnl=stats["total_pnl"],
            macd_line=self._last_macd_line,
            histogram=self._last_histogram,
            cycle_activated=self.strategy.is_cycle_activated,
            margin_error=self._margin_error,
            rate_limited=time.time() < self._rate_limited_until,
        )

    async def start(self) -> None:
        """Start the grid manager."""
        self._running = True
        main_logger.info("Grid Manager iniciando...")

        # Set leverage
        try:
            await self.client.set_leverage(
                self.symbol,
                self.config.trading.leverage,
            )
            main_logger.info(f"Leverage configurado: {self.config.trading.leverage}x")
        except Exception as e:
            main_logger.warning(f"Falha ao configurar leverage: {e}")

        # Set margin mode
        try:
            # Get current margin mode
            current_mode = await self.client.get_margin_mode(self.symbol)
            desired_mode = self.config.trading.margin_mode.value

            if current_mode != desired_mode:
                # Only try to change if different
                await self.client.set_margin_mode(self.symbol, desired_mode)
                main_logger.info(f"Modo de margem configurado: {desired_mode}")
            else:
                main_logger.info(f"Modo de margem já está configurado: {current_mode}")
        except Exception as e:
            main_logger.warning(
                f"Falha ao configurar modo de margem: {e}. "
                "Certifique-se de que não há posições abertas ao alterar o modo de margem."
            )

        # Load existing positions and orders
        try:
            positions = await self.client.get_positions(self.symbol)
            open_orders = await self.client.get_open_orders(self.symbol)

            # Get realized PnL from exchange (source of truth)
            for pos in positions:
                realised_pnl = float(pos.get("realisedProfit", 0))
                if realised_pnl != 0:
                    self.tracker.set_initial_pnl(realised_pnl)
                    break

            # Load positions (pass open_orders to find existing TPs)
            positions_loaded = self.tracker.load_existing_positions(
                positions,
                open_orders,
                self.config.grid.take_profit_percent,
            )

            # Load only LIMIT orders (not TPs)
            limit_orders = [o for o in open_orders if o.get("type") == "LIMIT"]
            orders_loaded = self.tracker.load_existing_orders(
                limit_orders,
                self.config.grid.take_profit_percent,
            )

            if positions_loaded > 0:
                main_logger.info(f"{positions_loaded} posição(ões) existente(s) carregada(s)")
            if orders_loaded > 0:
                main_logger.info(f"{orders_loaded} ordem(ns) pendente(s) carregada(s)")
        except Exception as e:
            main_logger.warning(f"Falha ao carregar dados existentes: {e}")

        # Instanciar DynamicTPManager
        # Note: tp_adjustment_repository is optional (graceful degradation)
        self.dynamic_tp = DynamicTPManager(
            config=self.config.dynamic_tp,
            client=self.client,
            order_tracker=self.tracker,
            symbol=self.symbol,
            tp_adjustment_repository=None,  # Will be integrated in future task
            account_id=self._account_id,
            activity_event_repository=self._activity_event_repository,
        )

        # Iniciar monitoramento
        if self.config.dynamic_tp.enabled is True:
            await self.dynamic_tp.start()
            orders_logger.info("DynamicTPManager started")

        # Start WebSocket for real-time order updates
        await self._start_websocket()

    async def _start_websocket(self) -> None:
        """Start WebSocket for real-time order updates."""
        try:
            # Generate listenKey
            self._listen_key = await self.client.generate_listen_key()
            if not self._listen_key:
                main_logger.warning("Falha ao gerar listenKey - usando apenas polling")
                return

            main_logger.info("ListenKey gerado para WebSocket")

            # Create WebSocket client
            self._account_ws = BingXAccountWebSocket(self._listen_key)

            # Set callbacks
            self._account_ws.set_order_callback(self._on_ws_order_update)
            self._account_ws.set_position_callback(self._on_ws_position_update)
            self._account_ws.set_listen_key_expired_callback(self._on_listen_key_expired)

            # Start WebSocket in background task
            self._ws_task = asyncio.create_task(self._account_ws.connect())

            # Start keepalive task (renew listenKey every 20 minutes)
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())

        except Exception as e:
            main_logger.warning(f"Falha ao iniciar WebSocket: {e} - usando apenas polling")

    async def _keepalive_loop(self) -> None:
        """Keep listenKey alive every 20 minutes."""
        # Wait 5 seconds before first keepalive to let WebSocket connect
        await asyncio.sleep(5)

        while self._running:
            if self._listen_key:
                try:
                    success = await self.client.keep_alive_listen_key(self._listen_key)
                    if success:
                        main_logger.debug("ListenKey keepalive OK")
                    else:
                        main_logger.warning("ListenKey keepalive falhou - renovando...")
                        await self._renew_listen_key_with_retry()
                except Exception as e:
                    main_logger.warning(f"Erro no keepalive: {e} - renovando...")
                    await self._renew_listen_key_with_retry()

            # Wait 20 minutes before next keepalive
            await asyncio.sleep(20 * 60)

    def _on_listen_key_expired(self) -> None:
        """Handle listenKey expiration - schedule renewal."""
        main_logger.warning("ListenKey expirado! Agendando renovação...")
        asyncio.create_task(self._renew_listen_key_with_retry())

    async def _renew_listen_key_with_retry(self, max_retries: int = 3) -> bool:
        """Generate new listenKey with retry logic."""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = min(
                        5 * (2**attempt), 30
                    )  # Exponential backoff: 5s, 10s, 20s, max 30s
                    main_logger.info(f"Aguardando {wait_time}s antes de tentar novamente...")
                    await asyncio.sleep(wait_time)

                success = await self._renew_listen_key()
                if success:
                    return True

                main_logger.warning(f"Tentativa {attempt + 1}/{max_retries} falhou")

            except Exception as e:
                main_logger.error(f"Erro na tentativa {attempt + 1}/{max_retries}: {e}")

        main_logger.error(f"Falha ao renovar listenKey após {max_retries} tentativas")
        return False

    async def _renew_listen_key(self) -> bool:
        """Generate new listenKey and update WebSocket. Returns True on success."""
        try:
            main_logger.info("Gerando novo listenKey...")
            new_key = await self.client.generate_listen_key()

            if not new_key:
                main_logger.error("Falha ao gerar listenKey - retorno vazio")
                return False

            old_key_prefix = self._listen_key[:10] if self._listen_key else "none"
            new_key_prefix = new_key[:10]
            main_logger.info(f"Novo listenKey: {old_key_prefix}... -> {new_key_prefix}...")

            self._listen_key = new_key

            if self._account_ws:
                self._account_ws.update_listen_key(new_key)

                # Force reconnect with new key
                if self._account_ws._ws and self._account_ws._ws.open:
                    main_logger.info("Forçando reconexão do WebSocket com nova key...")
                    await self._account_ws._ws.close()
                    # The _connect_loop will auto-reconnect with the new key

            main_logger.info("ListenKey renovado com sucesso!")
            return True

        except Exception as e:
            main_logger.error(f"Erro ao renovar listenKey: {e}")
            return False

    def _on_ws_order_update(self, order_data: dict) -> None:
        """Handle order update from WebSocket."""
        order_id = str(order_data.get("i", ""))
        status = order_data.get("X", "")  # NEW, FILLED, CANCELED, etc.
        order_type = order_data.get("o", "")  # LIMIT, MARKET, etc.

        orders_logger.info(f"WS: Ordem {order_id} -> {status} (tipo: {order_type})")

        # Order filled
        if status == "FILLED":
            order = self.tracker.get_order(order_id)
            if order:
                self.tracker.order_filled(order_id)
                if self._on_order_filled:
                    self._on_order_filled(order)
                orders_logger.info(f"WS: Ordem executada em tempo real: {order_id}")

                # Log ORDER_FILLED activity event
                self._log_activity_event(
                    event_type="ORDER_FILLED",
                    description=f"Grid order filled at ${order.entry_price:,.2f}",
                    event_data={
                        "order_id": order_id,
                        "entry_price": order.entry_price,
                        "quantity": order.quantity,
                        "tp_price": order.tp_price,
                        "side": "LONG",  # Grid bot only does LONG positions
                    },
                )

        # Order canceled
        elif status == "CANCELED":
            self.tracker.cancel_order(order_id)
            orders_logger.info(f"WS: Ordem cancelada: {order_id}")

    def _on_ws_position_update(self, pos_data: dict) -> None:
        """Handle position update from WebSocket."""
        symbol = pos_data.get("s", "")
        position_amt = float(pos_data.get("pa", 0))

        orders_logger.info(f"WS: Posição {symbol} atualizada: {position_amt}")

        # If position closed (amt = 0), mark as TP hit
        if position_amt == 0 and self.tracker.filled_orders:
            for order in list(self.tracker.filled_orders):
                self.tracker.order_tp_hit(order.order_id, self._current_price)
                if self._on_tp_hit:
                    self._on_tp_hit(order)
                orders_logger.info(f"WS: TP detectado em tempo real: {order.order_id}")

                # Log TRADE_CLOSED activity event
                profit = (self._current_price - order.entry_price) * order.quantity
                self._log_activity_event(
                    event_type="TRADE_CLOSED",
                    description=f"Take profit hit at ${self._current_price:,.2f} (+${profit:,.2f})",
                    event_data={
                        "order_id": order.order_id,
                        "entry_price": order.entry_price,
                        "exit_price": self._current_price,
                        "quantity": order.quantity,
                        "profit_usdt": profit,
                    },
                )

    async def _stop_websocket(self) -> None:
        """Stop WebSocket and cleanup."""
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass

        if self._account_ws:
            await self._account_ws.disconnect()

        if self._listen_key:
            try:
                await self.client.close_listen_key(self._listen_key)
            except Exception:
                pass

        main_logger.info("WebSocket encerrado")

    async def _get_trading_config(self):
        """Fetch current trading config from database.

        Returns config from DB or creates with defaults if not exists.
        Falls back to env vars if DB unavailable.

        Returns:
            TradingConfig object if successful, None if fallback needed.
        """
        if not self._trading_config_repository or not self._account_id:
            # No repository configured - use env vars
            return None

        try:
            config = await self._trading_config_repository.get_by_account(self._account_id)

            if not config:
                # Create with defaults from current Config
                config = await self._trading_config_repository.create_or_update(
                    self._account_id,
                    symbol=self.config.trading.symbol,
                    leverage=self.config.trading.leverage,
                    order_size_usdt=Decimal(str(self.config.trading.order_size_usdt)),
                    margin_mode=self.config.trading.margin_mode.value,
                    take_profit_percent=Decimal(str(self.config.grid.take_profit_percent)),
                )
                main_logger.info(f"Created default TradingConfig for account {self._account_id}")

            return config

        except Exception as e:
            main_logger.warning(f"Failed to fetch TradingConfig from DB, using env vars: {e}")
            # Fallback to env vars (return None to signal fallback)
            return None

    async def stop(self) -> None:
        """Stop the grid manager and cancel pending LIMIT orders (preserves TPs)."""
        self._running = False
        main_logger.info("Grid Manager encerrando...")

        # Parar DynamicTPManager
        if self.dynamic_tp:
            await self.dynamic_tp.stop()

        # Stop WebSocket
        await self._stop_websocket()

        # Cancel only LIMIT orders (grid orders), preserve TP/SL orders
        try:
            open_orders = await self.client.get_open_orders(self.symbol)
            if open_orders:
                cancelled = 0
                preserved = 0
                for order in open_orders:
                    order_type = order.get("type", "")
                    order_id = str(order.get("orderId", ""))

                    # Only cancel LIMIT orders (grid entry orders)
                    # Preserve: TAKE_PROFIT_MARKET, STOP_MARKET, TAKE_PROFIT, STOP
                    if order_type == "LIMIT" and order_id:
                        try:
                            await self.client.cancel_order(self.symbol, order_id)
                            cancelled += 1
                        except Exception:
                            pass
                    else:
                        preserved += 1

                if cancelled > 0:
                    main_logger.info(f"{cancelled} ordem(ns) LIMIT cancelada(s)")
                if preserved > 0:
                    main_logger.info(f"{preserved} TP/SL preservado(s) para posições abertas")
            else:
                main_logger.info("Nenhuma ordem para processar")
            self.tracker.clear_all()
        except Exception as e:
            main_logger.warning(f"Aviso ao verificar ordens: {e}")
            self.tracker.clear_all()

    async def update(self) -> None:
        """
        Main update cycle - called periodically.

        1. Fetch current price and klines
        2. Calculate MACD state
        3. Execute actions based on state
        """
        if not self._running:
            return

        try:
            # Get current price
            self._current_price = await self.client.get_price(self.symbol)

            # Get klines for MACD calculation
            klines = await self.client.get_klines(
                self.symbol,
                interval=self.config.macd.timeframe,
                limit=100,
            )

            # Calculate MACD state
            macd_values = self.strategy.calculate_macd(klines)
            if macd_values:
                self._last_macd_line = macd_values.macd_line
                self._last_histogram = macd_values.histogram

            new_state = self.strategy.get_state(klines)

            # Update MACD filter with current state
            self._macd_filter.set_current_state(new_state)

            # Handle state change
            if new_state != self._current_state:
                await self._handle_state_change(new_state)
                self._current_state = new_state

            # Execute state-specific actions
            await self._execute_state_actions()

            # Sync with exchange
            await self._sync_with_exchange()

        except Exception as e:
            main_logger.error(f"Erro no update: {e}", exc_info=True)

    async def _handle_state_change(self, new_state: GridState) -> None:
        """Handle transition to new state."""
        old_state = self._current_state
        main_logger.info(f"Estado: {old_state.value} → {new_state.value}")

        if self._on_state_change:
            self._on_state_change(old_state, new_state)

        # Log activity events for state changes
        if new_state == GridState.ACTIVE and old_state != GridState.ACTIVE:
            # CYCLE_ACTIVATED - entering ACTIVE state
            self._log_activity_event(
                event_type="CYCLE_ACTIVATED",
                description="Grid cycle activated (MACD bullish)",
                event_data={
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "macd_line": self._last_macd_line,
                    "histogram": self._last_histogram,
                },
            )
        elif new_state in (GridState.PAUSE, GridState.INACTIVE) and old_state == GridState.ACTIVE:
            # STRATEGY_PAUSED - leaving ACTIVE state
            self._log_activity_event(
                event_type="STRATEGY_PAUSED",
                description="Grid cycle paused (MACD bearish)",
                event_data={
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "macd_line": self._last_macd_line,
                    "histogram": self._last_histogram,
                },
            )

        # Cancel pending orders on INACTIVE
        if new_state == GridState.INACTIVE:
            await self._cancel_all_pending()

    async def _execute_state_actions(self) -> None:
        """Execute actions based on current state."""
        # Check if filters allow trade creation
        if self._filter_registry.should_allow_trade():
            await self._create_grid_orders()
        elif self._current_state == GridState.INACTIVE:
            await self._cancel_all_pending()

    def _count_filled_orders_awaiting_tp(self, orders: list[dict]) -> int:
        """
        Count filled orders awaiting TP by counting TP orders.

        BingX consolidates multiple filled LIMIT orders into a single position
        with average price, but creates a separate TP for each fill. Therefore,
        counting TP orders gives the accurate count of filled orders awaiting
        take profit execution.

        Args:
            orders: List of open orders from exchange

        Returns:
            Number of filled orders awaiting TP (count of TP orders)
        """
        tp_orders = [o for o in orders if "TAKE_PROFIT" in o.get("type", "")]
        return len(tp_orders)

    def _get_entry_prices_from_tp_orders(self, orders: list[dict]) -> set[float]:
        """
        Calculate entry prices from TP orders by reverse calculation.

        BUG-004 FIX: BingX consolidates multiple fills into a single position
        with average price, but keeps separate TP orders for each fill.
        We can reverse-calculate the original entry price from each TP:

            entry_price = tp_price / (1 + TAKE_PROFIT_PERCENT / 100)

        This allows us to know which price levels are "occupied" even after
        bot restart, without needing to persist data locally.

        Note: When anchor mode is enabled, the entry price is rounded to the
        nearest anchor value (e.g., $100 multiples) to match the grid levels.
        This is necessary because BingX may round the TP price slightly
        differently than our calculation.

        Args:
            orders: List of open orders from exchange

        Returns:
            Set of entry prices that have fills awaiting TP
        """
        occupied_prices: set[float] = set()
        tp_multiplier = 1 + (self.config.grid.take_profit_percent / 100)

        # Check if anchor mode is enabled
        use_anchor = self._get_anchor_mode_value() != "none"
        anchor_value = self.calculator.anchor_value if use_anchor else 0

        for order in orders:
            if "TAKE_PROFIT" in order.get("type", ""):
                # TP orders use stopPrice field
                tp_price = float(order.get("stopPrice", 0))
                if tp_price > 0:
                    # Reverse calculate the entry price
                    entry_price = tp_price / tp_multiplier

                    # Round to anchor value if anchor mode is enabled
                    # This handles BingX rounding differences (e.g., $87,799.90 → $87,800)
                    if use_anchor and anchor_value > 0:
                        rounded_price = round(entry_price / anchor_value) * anchor_value
                    else:
                        rounded_price = round(entry_price, 2)

                    occupied_prices.add(rounded_price)

        return occupied_prices

    async def _create_grid_orders(self) -> None:
        """Create grid orders based on current price."""
        # Check for margin error (reset after 5 minutes)
        if self._margin_error:
            if time.time() - self._margin_error_time > 300:  # 5 minutes
                self._margin_error = False
                self._consecutive_errors = 0
                main_logger.info("Tentando criar ordens novamente após pausa por margem")
            else:
                return  # Still paused

        # Check rate limiting
        if time.time() < self._rate_limited_until:
            return  # Still rate limited

        # Refresh grid calculator with latest config from database
        await self._refresh_grid_calculator()

        # Get existing orders from exchange
        exchange_orders = await self.client.get_open_orders(self.symbol)

        # BE-008: Count filled orders awaiting TP for dynamic slot calculation
        # Note: We count TP orders, not positions, because BingX consolidates
        # multiple fills into one position but keeps separate TPs
        filled_orders_count = self._count_filled_orders_awaiting_tp(exchange_orders)

        # BUG-004 FIX: Calculate entry prices from TP orders
        # BingX consolidates multiple fills into one position with avgPrice,
        # but keeps separate TPs. We reverse-calculate entry prices from TPs
        # to know which levels are occupied, even after bot restart.
        occupied_entry_prices = self._get_entry_prices_from_tp_orders(exchange_orders)

        # STEP 1: Cancel orders outside range FIRST
        # This frees up slots for new orders in the same cycle
        orders_to_cancel = self.calculator.get_orders_to_cancel(
            self._current_price,
            exchange_orders,
            filled_orders_count,  # BE-008: pass filled orders (TP count)
        )
        for order in orders_to_cancel:
            try:
                order_price = float(order.get("price", 0))
                order_id = str(order["orderId"])
                await self.client.cancel_order(self.symbol, order_id)

                # Log cancellation reason based on mode
                if self._get_anchor_mode_value() != "none":
                    orders_logger.info(
                        f"Ordem cancelada (muito distante): ${order_price:,.2f} - ID: {order_id}"
                    )
                else:
                    orders_logger.info(
                        f"Ordem cancelada (fora do range): ${order_price:,.2f} - ID: {order_id}"
                    )
            except Exception as e:
                orders_logger.error(f"Erro ao cancelar ordem: {e}")

        # STEP 2: Refresh orders after cancellations
        # This ensures get_levels_to_create() sees the freed-up slots
        if orders_to_cancel:
            exchange_orders = await self.client.get_open_orders(self.symbol)

        # STEP 3: Calculate levels to create (now with freed-up slots)
        # BE-008: Pass filled_orders_count to limit new orders
        levels = self.calculator.get_levels_to_create(
            self._current_price,
            exchange_orders,
            filled_orders_count,
        )

        # Also check local tracker AND TP-derived entry prices (BUG-003 + BUG-004 FIX)
        # This triple-check ensures no duplicates:
        # 1. get_levels_to_create() already filters by exchange LIMIT orders
        # 2. has_order_at_price() filters by local tracker (pending + filled)
        # 3. occupied_entry_prices filters by reverse-calculated entry prices from TPs
        levels = [
            level
            for level in levels
            if not self.tracker.has_order_at_price(level.entry_price)
            and round(level.entry_price, 2) not in occupied_entry_prices
        ]

        if not levels:
            return

        # BE-008: Log available slots
        max_total = self.config.grid.max_total_orders
        limit_orders_count = len([o for o in exchange_orders if o.get("type") == "LIMIT"])
        available_slots = max(0, max_total - filled_orders_count - limit_orders_count)
        orders_logger.info(
            f"Slots: {available_slots}/{max_total} disponíveis "
            f"({filled_orders_count} aguardando TP, {limit_orders_count} ordens LIMIT)"
        )

        # Log if creating orders without active filters
        filter_states = self._filter_registry.get_all_states()
        if not filter_states.get("any_enabled", True):
            orders_logger.info(
                "Nenhum filtro ativo - criando ordens apenas com base no preço e MAX_TOTAL_ORDERS"
            )

        # STEP 4: Create orders (with rate limiting)
        for level in levels[:10]:  # Max 10 orders per cycle
            try:
                await self._create_order(level)
                self._consecutive_errors = 0  # Reset on success
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                error_msg = str(e)
                self._consecutive_errors += 1

                # Handle specific errors
                if "Insufficient margin" in error_msg:
                    self._margin_error = True
                    self._margin_error_time = time.time()
                    main_logger.warning(
                        "Margem insuficiente - pausando criação de ordens por 5 min"
                    )
                    break
                elif "over 20 error" in error_msg or "rate limit" in error_msg.lower():
                    # Rate limited - backoff for 8 minutes
                    self._rate_limited_until = time.time() + 480
                    main_logger.warning("Rate limit atingido - pausando por 8 min")
                    break
                elif self._consecutive_errors >= 3:
                    # Too many consecutive errors - pause briefly
                    main_logger.warning(f"3 erros consecutivos - pausando brevemente: {e}")
                    await asyncio.sleep(5)
                    break

                orders_logger.error(f"Erro ao criar ordem: {e}")

    async def _create_order(self, level: GridLevel) -> None:
        """Create a single grid order."""
        # Fetch fresh config from DB (or fallback to env vars)
        db_config = await self._get_trading_config()

        if db_config:
            order_size = float(db_config.order_size_usdt)
            symbol = db_config.symbol
            # Note: leverage and margin_mode are set on account setup, not per-order
        else:
            # Fallback to env vars
            order_size = self.order_size
            symbol = self.symbol

        # Convert USDT to BTC quantity (6 decimal places for precision)
        # Use current price for most accurate conversion
        quantity_btc = round(order_size / self._current_price, 6)

        # BingX minimum order: 0.0001 BTC
        if quantity_btc < 0.0001:
            orders_logger.warning(f"Quantidade muito pequena: {quantity_btc} BTC. Mínimo: 0.0001")
            return

        result = await self.client.create_limit_order_with_tp(
            symbol=symbol,
            side="BUY",
            position_side="BOTH",  # One-way mode
            price=level.entry_price,
            quantity=quantity_btc,
            tp_price=level.tp_price,
        )

        order_id = str(result.get("orderId", result.get("order", {}).get("orderId", "")))
        if order_id:
            self.tracker.add_order(
                order_id=order_id,
                entry_price=level.entry_price,
                tp_price=level.tp_price,
                quantity=quantity_btc,
            )

            if self._on_order_created:
                self._on_order_created(level)

            # Log with additional context for anchored mode
            if self._get_anchor_mode_value() != "none":
                anchor_level = self.calculator.get_anchor_level(level.entry_price)
                orders_logger.info(f"Ordem criada (nível ancorado ${anchor_level:,.0f}): {level}")
            else:
                orders_logger.info(f"Ordem criada: {level}")

    async def _cancel_all_limit_orders(self, reason: str = "filter change") -> None:
        """
        Cancel all pending LIMIT orders (preserves TPs).

        Args:
            reason: Reason for cancellation (for logging)
        """
        try:
            open_orders = await self.client.get_open_orders(self.symbol)
            cancelled = 0

            for open_order in open_orders:
                order_type = open_order.get("type", "")
                order_id = str(open_order.get("orderId", ""))

                # Only cancel LIMIT orders, preserve TP/SL
                if order_type == "LIMIT" and order_id:
                    try:
                        await self.client.cancel_order(self.symbol, order_id)
                        cancelled += 1
                    except Exception:
                        pass

            # Update tracker
            for pending_order in self.tracker.pending_orders:
                self.tracker.cancel_order(pending_order.order_id)

            if cancelled > 0:
                main_logger.info(f"{cancelled} ordem(ns) LIMIT cancelada(s) ({reason})")
        except Exception as e:
            main_logger.error(f"Erro ao cancelar ordens: {e}")

    async def _cancel_all_pending(self) -> None:
        """Cancel all pending LIMIT orders (preserves TPs)."""
        await self._cancel_all_limit_orders(reason="INACTIVE")

    async def _sync_with_exchange(self) -> None:
        """Sync local state with exchange."""
        try:
            exchange_orders = await self.client.get_open_orders(self.symbol)
            positions = await self.client.get_positions(self.symbol)

            # Get current position amount from exchange
            current_position_amt = 0.0
            for pos in positions:
                amt = float(pos.get("positionAmt", 0))
                if amt != 0:
                    current_position_amt = abs(amt)
                    break

            # 1. Check for filled/cancelled orders (pending orders no longer on exchange)
            exchange_order_ids = {str(o.get("orderId")) for o in exchange_orders}

            # Calculate expected position from filled orders in tracker
            expected_position = sum(o.quantity for o in self.tracker.filled_orders)

            for order in list(self.tracker.pending_orders):
                if order.order_id not in exchange_order_ids:
                    # Order disappeared - determine if it was FILLED or CANCELLED
                    # If current position > expected, this order was likely filled
                    position_delta = current_position_amt - expected_position

                    if position_delta >= order.quantity * 0.99:  # 1% tolerance for rounding
                        # Order was FILLED - position increased
                        self.tracker.order_filled(order.order_id)
                        expected_position += order.quantity  # Update expected for next iteration
                        if self._on_order_filled:
                            self._on_order_filled(order)
                        orders_logger.info(f"Ordem detectada como EXECUTADA: {order.order_id}")
                    else:
                        # Order was CANCELLED - no position increase
                        self.tracker.cancel_order(order.order_id)
                        orders_logger.info(f"Ordem detectada como CANCELADA: {order.order_id}")

            # 2. Check for closed positions (filled positions that no longer exist)
            # If no position on exchange but we have filled orders in tracker, they were closed
            if current_position_amt == 0 and self.tracker.filled_orders:
                for order in list(self.tracker.filled_orders):
                    # Position was closed (TP hit or manual close)
                    self.tracker.order_tp_hit(order.order_id, self._current_price)
                    if self._on_tp_hit:
                        self._on_tp_hit(order)
                    orders_logger.info(f"Posição fechada detectada: {order.order_id}")

            # 3. Sync position count - if exchange has fewer positions than tracker
            elif current_position_amt > 0:
                # Calculate total quantity in tracker
                tracker_qty = sum(o.quantity for o in self.tracker.filled_orders)

                # If exchange has less than tracker, some positions were closed
                if tracker_qty > 0 and current_position_amt < tracker_qty * 0.99:  # 1% tolerance
                    # Remove excess positions from tracker (oldest first)
                    excess = tracker_qty - current_position_amt
                    for order in list(self.tracker.filled_orders):
                        if excess <= 0:
                            break
                        self.tracker.order_tp_hit(order.order_id, self._current_price)
                        excess -= order.quantity
                        orders_logger.info(f"Posição parcial fechada: {order.order_id}")

        except Exception as e:
            main_logger.error(f"Erro no sync: {e}")

    async def recreate_order_after_tp(self, entry_price: float, tp_price: float) -> None:
        """
        Recreate an order after take profit is hit.

        Only recreates if filters allow.
        """
        if not self._filter_registry.should_allow_trade():
            main_logger.info(f"Não recriando ordem em ${entry_price:,.2f} - filtros não permitem")
            return

        level = GridLevel(
            entry_price=entry_price,
            tp_price=tp_price,
            level_index=0,
        )

        try:
            await self._create_order(level)
            main_logger.info(f"Ordem recriada após TP: ${entry_price:,.2f}")
        except Exception as e:
            main_logger.error(f"Erro ao recriar ordem: {e}")

    def _on_filter_change(self, filter_name: str, action: str) -> None:
        """
        Callback when filter state changes via API.

        Args:
            filter_name: Name of the filter that changed
            action: 'enabled' or 'disabled'
        """
        main_logger.info(f"Filter '{filter_name}' {action} - scheduling order cancellation")
        # Schedule cancellation in event loop (only if running)
        try:
            asyncio.create_task(self._cancel_all_limit_orders(reason=f"filter {action}"))
        except RuntimeError:
            # No event loop running (e.g., during tests without async context)
            main_logger.debug("No event loop running - skipping async cancellation")

    def _on_macd_state_change(self, old_state: GridState, new_state: GridState) -> None:
        """
        Callback when MACD state changes.

        Cancels orders when transitioning from ACTIVATE/ACTIVE to PAUSE/INACTIVE/WAIT.

        Args:
            old_state: Previous MACD state
            new_state: New MACD state
        """
        # States that allow trading
        active_states = {GridState.ACTIVATE, GridState.ACTIVE}

        # States that don't allow trading
        inactive_states = {GridState.PAUSE, GridState.INACTIVE, GridState.WAIT}

        # Cancel orders if transitioning from active to inactive
        if old_state in active_states and new_state in inactive_states:
            main_logger.info(
                f"MACD state change {old_state.value} -> {new_state.value} - scheduling order cancellation"
            )
            # Schedule cancellation in event loop (only if running)
            try:
                asyncio.create_task(self._cancel_all_limit_orders(reason=f"MACD {new_state.value}"))
            except RuntimeError:
                # No event loop running (e.g., during tests without async context)
                main_logger.debug("No event loop running - skipping async cancellation")
