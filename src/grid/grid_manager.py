from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from config import Config
from src.api.websocket.connection_manager import get_connection_manager
from src.api.websocket.events import (
    BotStatusEvent,
    OrderUpdateEvent,
    PositionUpdateEvent,
    WebSocketEvent,
)
from src.client.bingx_client import BingXClient
from src.client.websocket_client import BingXAccountWebSocket
from src.database.models.activity_event import EventType
from src.filters.macd_filter import MACDFilter
from src.filters.registry import FilterRegistry
from src.grid.dynamic_tp_manager import DynamicTPManager
from src.grid.grid_calculator import GridCalculator, GridLevel
from src.grid.order_tracker import OrderTracker, TrackedOrder
from src.strategy.macd_strategy import GridState, MACDStrategy
from src.utils.logger import main_logger, orders_logger

if TYPE_CHECKING:
    from src.database.repositories.activity_event_repository import ActivityEventRepository
    from src.database.repositories.bot_state_repository import BotStateRepository
    from src.database.repositories.macd_filter_config_repository import MACDFilterConfigRepository
    from src.database.repositories.strategy_repository import StrategyRepository
    from src.database.repositories.tp_adjustment_repository import TPAdjustmentRepository
    from src.database.repositories.trade_repository import TradeRepository


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
        bot_state_repository: BotStateRepository | None = None,
        trade_repository: TradeRepository | None = None,
        strategy_repository: StrategyRepository | None = None,
        macd_filter_config_repository: MACDFilterConfigRepository | None = None,
        activity_event_repository: ActivityEventRepository | None = None,
        tp_adjustment_repository: TPAdjustmentRepository | None = None,
    ):
        self.config = config
        self.client = client
        self.symbol = config.trading.symbol
        self.order_size = config.trading.order_size_usdt

        # Database repository for unified strategy config
        self._account_id = account_id
        self._strategy_repository = strategy_repository
        self._macd_filter_config_repository = macd_filter_config_repository
        self._activity_event_repository = activity_event_repository
        self._tp_adjustment_repository = tp_adjustment_repository

        self.strategy = MACDStrategy(
            config.macd,
            account_id=account_id,
            bot_state_repository=bot_state_repository,
            strategy_repository=strategy_repository,
            macd_filter_config_repository=macd_filter_config_repository,
        )
        self.calculator = GridCalculator(config.grid)
        self.tracker = OrderTracker(
            trade_repository=trade_repository,
            account_id=account_id,
        )

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

        # WebSocket Connection Manager for dashboard broadcasting
        self._connection_manager = get_connection_manager()

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
        event_type: EventType,
        description: str,
        event_data: dict | None = None,
    ) -> None:
        """Log an activity event to the database (fire-and-forget).

        This method is non-blocking and failures will not crash the bot.
        Uses asyncio.create_task for fire-and-forget behavior.

        Args:
            event_type: EventType enum value (e.g., EventType.BOT_STARTED)
            description: Human-readable description of the event
            event_data: Optional JSON-serializable dict with additional context
        """
        if not self._activity_event_repository or not self._account_id:
            return

        # Capture values for closure (type narrowing)
        repo = self._activity_event_repository
        account_id = self._account_id

        async def _do_log():
            try:
                await repo.create_event(
                    account_id=account_id,
                    event_type=event_type,
                    description=description,
                    event_data=event_data,
                )
                main_logger.debug(f"Activity event logged: {event_type}")
            except Exception as e:
                main_logger.warning(f"Failed to log activity event: {e}")

        # Fire and forget - don't await, just schedule
        try:
            asyncio.create_task(_do_log())
        except RuntimeError:
            # No event loop running (e.g., during tests without async context)
            main_logger.debug("No event loop running, skipping activity event logging")

    def _broadcast_bot_status(
        self,
        state: GridState,
        is_running: bool,
        macd_trend: str | None = None,
        grid_active: bool = False,
        pending_orders_count: int = 0,
        filled_orders_count: int = 0,
    ) -> None:
        """Broadcast bot status changes to connected dashboard clients.

        Args:
            state: Current grid state (WAIT, ACTIVATE, ACTIVE, PAUSE, INACTIVE)
            is_running: Whether the bot is currently running
            macd_trend: MACD trend (bullish, bearish, neutral)
            grid_active: Whether the grid is active
            pending_orders_count: Number of pending orders
            filled_orders_count: Number of filled orders
        """
        # Skip if no clients connected
        if self._connection_manager.active_connections_count == 0:
            return

        event_data = BotStatusEvent(
            state=state.value,
            is_running=is_running,
            macd_trend=macd_trend,
            grid_active=grid_active,
            pending_orders_count=pending_orders_count,
            filled_orders_count=filled_orders_count,
        )

        event = WebSocketEvent.bot_status(event_data)

        # Fire and forget - don't await, just schedule
        try:
            asyncio.create_task(self._connection_manager.broadcast(event))
        except RuntimeError:
            # No event loop running (e.g., during tests without async context)
            main_logger.debug("No event loop running, skipping bot status broadcast")

    def _broadcast_order_update(self, tracked_order: TrackedOrder) -> None:
        """Broadcast order update to connected dashboard clients.

        Args:
            tracked_order: TrackedOrder instance with order details
        """
        # Skip if no clients connected
        if self._connection_manager.active_connections_count == 0:
            main_logger.debug("Skipping order update broadcast - no clients connected")
            return

        from src.grid.order_tracker import OrderStatus

        # Map OrderStatus to WebSocket status
        status_map = {
            OrderStatus.PENDING: "PENDING",
            OrderStatus.FILLED: "FILLED",
            OrderStatus.TP_HIT: "TP_HIT",
            OrderStatus.CANCELLED: "CANCELLED",
        }

        event_data = OrderUpdateEvent(
            order_id=tracked_order.order_id,
            symbol=self.symbol,
            side="LONG",  # Grid bot only trades LONG
            order_type="LIMIT",  # Entry orders are always LIMIT
            status=status_map[tracked_order.status],
            price=str(tracked_order.entry_price),
            tp_price=str(tracked_order.tp_price) if tracked_order.tp_price else None,
            quantity=str(tracked_order.quantity),
            filled_quantity=str(tracked_order.quantity)
            if tracked_order.status != OrderStatus.PENDING
            else "0",
            created_at=tracked_order.created_at,
            filled_at=tracked_order.filled_at,
            closed_at=tracked_order.closed_at,
            exchange_tp_order_id=tracked_order.exchange_tp_order_id,
        )

        event = WebSocketEvent.order_update(event_data)

        main_logger.info(
            f"Broadcasting order update: order_id={tracked_order.order_id}, "
            f"status={status_map[tracked_order.status]}"
        )

        # Fire and forget - don't await, just schedule
        try:
            asyncio.create_task(self._connection_manager.broadcast(event))
        except RuntimeError:
            # No event loop running (e.g., during tests without async context)
            main_logger.debug("No event loop running, skipping order update broadcast")

    def _broadcast_position_update(
        self,
        symbol: str,
        side: str,
        size: str,
        entry_price: str,
        current_price: str,
        unrealized_pnl: str,
        leverage: int,
    ) -> None:
        """Broadcast position update to connected dashboard clients.

        Args:
            symbol: Trading symbol
            side: Position side (LONG, SHORT)
            size: Position size
            entry_price: Entry price
            current_price: Current price
            unrealized_pnl: Unrealized PnL
            leverage: Leverage
        """
        # Skip if no clients connected
        if self._connection_manager.active_connections_count == 0:
            return

        from datetime import datetime

        event_data = PositionUpdateEvent(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            leverage=leverage,
            timestamp=datetime.now(),
        )

        event = WebSocketEvent.position_update(event_data)

        # Fire and forget - don't await, just schedule
        try:
            asyncio.create_task(self._connection_manager.broadcast(event))
        except RuntimeError:
            # No event loop running (e.g., during tests without async context)
            main_logger.debug("No event loop running, skipping position update broadcast")

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

        Fetches active strategy from database (if repository is set)
        and updates the calculator's properties.

        Falls back to config.py values if repository is not set or database is unavailable.
        """
        if not self._strategy_repository or not self._account_id:
            # No database integration - use config.py values (already set)
            return

        try:
            # Fetch active strategy from database
            strategy = await self._strategy_repository.get_active_by_account(self._account_id)

            if not strategy:
                main_logger.debug("No active strategy found, using config.py values")
                return

            # Update calculator properties with strategy values
            self.calculator.spacing_type = strategy.spacing_type  # type: ignore[assignment]
            self.calculator.spacing_value = float(strategy.spacing_value)
            self.calculator.range_percent = float(strategy.range_percent)
            self.calculator.max_total_orders = strategy.max_total_orders
            self.calculator.anchor_mode = strategy.anchor_mode  # type: ignore[assignment]
            self.calculator.anchor_value = float(strategy.anchor_threshold)

            # Update take_profit_percent from strategy
            self.calculator.tp_percent = float(strategy.take_profit_percent)

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

        # Log BOT_STARTED event
        self._log_activity_event(
            EventType.BOT_STARTED,
            "Bot started",
            {
                "symbol": self.symbol,
                "leverage": self.config.trading.leverage,
                "order_size_usdt": self.order_size,
                "trading_mode": self.config.trading.mode.value,
            },
        )

        # Load MACD config from database (if available)
        await self.strategy.load_config_from_db()

        # Sync filter enabled state with strategy config from DB
        self._filter_registry.sync_macd_filter_with_strategy()

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

            # Load positions from TP orders (BUG-FIX-006: derive individual positions)
            # Get anchor value for proper price rounding
            use_anchor = self._get_anchor_mode_value() != "none"
            anchor_value = self.calculator.anchor_value if use_anchor else 0

            positions_loaded = self.tracker.load_existing_positions(
                positions,
                open_orders,
                self.config.grid.take_profit_percent,
                anchor_value=anchor_value,
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
            tp_adjustment_repository=self._tp_adjustment_repository,
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
                filled_order = self.tracker.order_filled(order_id)

                # Broadcast order filled to dashboard
                if filled_order:
                    self._broadcast_order_update(filled_order)

                if self._on_order_filled:
                    self._on_order_filled(order)
                orders_logger.info(f"WS: Ordem executada em tempo real: {order_id}")

                # Log ORDER_FILLED event
                self._log_activity_event(
                    EventType.ORDER_FILLED,
                    f"Order filled at ${order.entry_price:,.2f}",
                    {
                        "order_id": order_id,
                        "entry_price": order.entry_price,
                        "tp_price": order.tp_price,
                        "quantity": order.quantity,
                        "source": "websocket",
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
                exit_price = self._current_price
                pnl = (exit_price - order.entry_price) * order.quantity
                self.tracker.order_tp_hit(order.order_id, exit_price)

                # Broadcast TP hit to dashboard (order has been marked as TP_HIT)
                self._broadcast_order_update(order)

                if self._on_tp_hit:
                    self._on_tp_hit(order)
                orders_logger.info(f"WS: TP detectado em tempo real: {order.order_id}")

                # Log TRADE_CLOSED event
                self._log_activity_event(
                    EventType.TRADE_CLOSED,
                    f"Trade closed at ${exit_price:,.2f} (+${pnl:,.2f})",
                    {
                        "order_id": order.order_id,
                        "entry_price": order.entry_price,
                        "exit_price": exit_price,
                        "quantity": order.quantity,
                        "pnl": pnl,
                        "source": "websocket",
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

    async def _get_active_strategy(self):
        """Fetch active strategy from database.

        Returns active strategy from DB if available.
        Falls back to env vars if DB unavailable or no active strategy.

        Returns:
            Strategy object if successful, None if fallback needed.
        """
        if not self._strategy_repository or not self._account_id:
            # No repository configured - use env vars
            return None

        try:
            strategy = await self._strategy_repository.get_active_by_account(self._account_id)
            return strategy

        except Exception as e:
            main_logger.warning(f"Failed to fetch Strategy from DB, using env vars: {e}")
            # Fallback to env vars (return None to signal fallback)
            return None

    async def stop(self) -> None:
        """Stop the grid manager and cancel pending LIMIT orders (preserves TPs)."""
        self._running = False
        main_logger.info("Grid Manager encerrando...")

        # Log BOT_STOPPED event (capture state before clearing)
        self._log_activity_event(
            EventType.BOT_STOPPED,
            "Bot stopped",
            {
                "pending_orders": len(self.tracker.pending_orders),
                "open_positions": len(self.tracker.filled_orders),
                "total_trades": self.tracker.total_trades,
                "total_pnl": self.tracker.total_pnl,
            },
        )

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
            # Log ERROR_OCCURRED event for main loop errors
            self._log_activity_event(
                EventType.ERROR_OCCURRED,
                f"Error in update cycle: {str(e)[:100]}",
                {
                    "error_type": "UPDATE_CYCLE_ERROR",
                    "error_message": str(e)[:500],
                    "current_state": self._current_state.value,
                },
            )

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
                EventType.CYCLE_ACTIVATED,
                "Grid cycle activated (MACD bullish)",
                {
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "macd_line": self._last_macd_line,
                    "histogram": self._last_histogram,
                },
            )
        elif new_state in (GridState.PAUSE, GridState.INACTIVE) and old_state == GridState.ACTIVE:
            # STRATEGY_PAUSED - leaving ACTIVE state
            self._log_activity_event(
                EventType.STRATEGY_PAUSED,
                "Grid cycle paused (MACD bearish)",
                {
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
                    # Log ERROR_OCCURRED event for margin error
                    self._log_activity_event(
                        EventType.ERROR_OCCURRED,
                        "Insufficient margin - pausing order creation",
                        {
                            "error_type": "MARGIN_ERROR",
                            "pause_duration_seconds": 300,
                            "current_price": self._current_price,
                            "error_message": error_msg[:200],
                        },
                    )
                    break
                elif "over 20 error" in error_msg or "rate limit" in error_msg.lower():
                    # Rate limited - backoff for 8 minutes
                    self._rate_limited_until = time.time() + 480
                    main_logger.warning("Rate limit atingido - pausando por 8 min")
                    # Log ERROR_OCCURRED event for rate limit
                    self._log_activity_event(
                        EventType.ERROR_OCCURRED,
                        "Rate limit reached - pausing for 8 minutes",
                        {
                            "error_type": "RATE_LIMIT",
                            "pause_duration_seconds": 480,
                            "error_message": error_msg[:200],
                        },
                    )
                    break
                elif self._consecutive_errors >= 3:
                    # Too many consecutive errors - pause briefly
                    main_logger.warning(f"3 erros consecutivos - pausando brevemente: {e}")
                    await asyncio.sleep(5)
                    break

                orders_logger.error(f"Erro ao criar ordem: {e}")

    async def _create_order(self, level: GridLevel) -> None:
        """Create a single grid order."""
        # Fetch active strategy from DB (or fallback to env vars)
        strategy = await self._get_active_strategy()

        if strategy:
            order_size = float(strategy.order_size_usdt)
            symbol = strategy.symbol
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
            tracked_order = self.tracker.add_order(
                order_id=order_id,
                entry_price=level.entry_price,
                tp_price=level.tp_price,
                quantity=quantity_btc,
            )

            # Broadcast order creation to dashboard
            self._broadcast_order_update(tracked_order)

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

            # Update tracker and broadcast cancellations
            for pending_order in list(self.tracker.pending_orders):
                cancelled_order = self.tracker.cancel_order(pending_order.order_id)
                if cancelled_order:
                    self._broadcast_order_update(cancelled_order)

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
                        filled_order = self.tracker.order_filled(order.order_id)

                        # Broadcast order filled to dashboard
                        if filled_order:
                            self._broadcast_order_update(filled_order)

                        expected_position += order.quantity  # Update expected for next iteration
                        if self._on_order_filled:
                            self._on_order_filled(order)
                        orders_logger.info(f"Ordem detectada como EXECUTADA: {order.order_id}")

                        # Log ORDER_FILLED event (polling detection)
                        self._log_activity_event(
                            EventType.ORDER_FILLED,
                            f"Order filled at ${order.entry_price:,.2f}",
                            {
                                "order_id": order.order_id,
                                "entry_price": order.entry_price,
                                "tp_price": order.tp_price,
                                "quantity": order.quantity,
                                "source": "polling",
                            },
                        )
                    else:
                        # Order was CANCELLED - no position increase
                        cancelled_order = self.tracker.cancel_order(order.order_id)

                        # Broadcast order cancellation to dashboard
                        if cancelled_order:
                            self._broadcast_order_update(cancelled_order)

                        orders_logger.info(f"Ordem detectada como CANCELADA: {order.order_id}")

            # 2. Check for closed positions (filled positions that no longer exist)
            # If no position on exchange but we have filled orders in tracker, they were closed
            if current_position_amt == 0 and self.tracker.filled_orders:
                for order in list(self.tracker.filled_orders):
                    # Position was closed (TP hit or manual close)
                    exit_price = self._current_price
                    pnl = (exit_price - order.entry_price) * order.quantity
                    self.tracker.order_tp_hit(order.order_id, exit_price)

                    # Broadcast TP hit to dashboard (order has been marked as TP_HIT)
                    self._broadcast_order_update(order)

                    if self._on_tp_hit:
                        self._on_tp_hit(order)
                    orders_logger.info(f"Posição fechada detectada: {order.order_id}")

                    # Log TRADE_CLOSED event (polling detection)
                    self._log_activity_event(
                        EventType.TRADE_CLOSED,
                        f"Trade closed at ${exit_price:,.2f}",
                        {
                            "order_id": order.order_id,
                            "entry_price": order.entry_price,
                            "exit_price": exit_price,
                            "quantity": order.quantity,
                            "pnl": pnl,
                            "source": "polling",
                        },
                    )

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
                        exit_price = self._current_price
                        pnl = (exit_price - order.entry_price) * order.quantity
                        self.tracker.order_tp_hit(order.order_id, exit_price)

                        # Broadcast TP hit to dashboard (order has been marked as TP_HIT)
                        self._broadcast_order_update(order)

                        excess -= order.quantity
                        orders_logger.info(f"Posição parcial fechada: {order.order_id}")

                        # Log TRADE_CLOSED event (partial close via polling)
                        self._log_activity_event(
                            EventType.TRADE_CLOSED,
                            f"Trade closed (partial) at ${exit_price:,.2f}",
                            {
                                "order_id": order.order_id,
                                "entry_price": order.entry_price,
                                "exit_price": exit_price,
                                "quantity": order.quantity,
                                "pnl": pnl,
                                "source": "polling_partial",
                            },
                        )

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

        # Log activity events for state transitions
        event_data = {
            "old_state": old_state.value,
            "new_state": new_state.value,
            "macd_line": self._last_macd_line,
            "histogram": self._last_histogram,
            "pending_orders": self.tracker.pending_count,
            "open_positions": self.tracker.position_count,
        }

        # CYCLE_ACTIVATED: when transitioning TO ACTIVATE state (cycle begins)
        if new_state == GridState.ACTIVATE and old_state != GridState.ACTIVATE:
            self._log_activity_event(
                EventType.CYCLE_ACTIVATED,
                f"Cycle activated ({old_state.value} -> {new_state.value})",
                event_data,
            )

        # CYCLE_DEACTIVATED: when transitioning TO INACTIVE state (cycle ends)
        if new_state == GridState.INACTIVE and old_state != GridState.INACTIVE:
            self._log_activity_event(
                EventType.CYCLE_DEACTIVATED,
                f"Cycle deactivated ({old_state.value} -> {new_state.value})",
                event_data,
            )

        # STRATEGY_PAUSED: when transitioning TO PAUSE state
        if new_state == GridState.PAUSE and old_state != GridState.PAUSE:
            self._log_activity_event(
                EventType.STRATEGY_PAUSED,
                f"Strategy paused ({old_state.value} -> PAUSE)",
                event_data,
            )

        # STRATEGY_RESUMED: when transitioning FROM PAUSE to ACTIVE/ACTIVATE
        if old_state == GridState.PAUSE and new_state in active_states:
            self._log_activity_event(
                EventType.STRATEGY_RESUMED,
                f"Strategy resumed (PAUSE -> {new_state.value})",
                event_data,
            )
