import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass

from config import Config
from src.client.bingx_client import BingXClient
from src.client.websocket_client import BingXAccountWebSocket
from src.filters.macd_filter import MACDFilter
from src.filters.registry import FilterRegistry
from src.grid.grid_calculator import GridCalculator, GridLevel
from src.grid.order_tracker import OrderTracker
from src.strategy.macd_strategy import GridState, MACDStrategy
from src.utils.logger import main_logger, orders_logger


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
    ):
        self.config = config
        self.client = client
        self.symbol = config.trading.symbol
        self.order_size = config.trading.order_size_usdt

        self.strategy = MACDStrategy(config.macd)
        self.calculator = GridCalculator(config.grid)
        self.tracker = OrderTracker()

        # Filter system
        self._filter_registry = FilterRegistry()
        self._macd_filter = MACDFilter(self.strategy)
        self._filter_registry.register(self._macd_filter)

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

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_state(self) -> GridState:
        return self._current_state

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

    async def stop(self) -> None:
        """Stop the grid manager and cancel pending LIMIT orders (preserves TPs)."""
        self._running = False
        main_logger.info("Grid Manager encerrando...")

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
            main_logger.error(f"Erro no update: {e}")

    async def _handle_state_change(self, new_state: GridState) -> None:
        """Handle transition to new state."""
        old_state = self._current_state
        main_logger.info(f"Estado: {old_state.value} → {new_state.value}")

        if self._on_state_change:
            self._on_state_change(old_state, new_state)

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

        # Get existing orders from exchange
        exchange_orders = await self.client.get_open_orders(self.symbol)

        # STEP 1: Cancel orders outside range FIRST
        # This frees up slots for new orders in the same cycle
        orders_to_cancel = self.calculator.get_orders_to_cancel(
            self._current_price,
            exchange_orders,
        )
        for order in orders_to_cancel:
            try:
                order_price = float(order.get("price", 0))
                order_id = str(order["orderId"])
                await self.client.cancel_order(self.symbol, order_id)

                # Log cancellation reason based on mode
                if self.calculator.anchor_mode.value != "none":
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
        levels = self.calculator.get_levels_to_create(
            self._current_price,
            exchange_orders,
        )

        # Also check local tracker
        levels = [
            level for level in levels if not self.tracker.has_order_at_price(level.entry_price)
        ]

        if not levels:
            return

        # Log if creating orders without active filters
        filter_states = self._filter_registry.get_all_states()
        if not filter_states.get("any_enabled", True):
            orders_logger.info(
                "Nenhum filtro ativo - criando ordens apenas com base no preço e MAX_ORDERS"
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
        # Convert USDT to BTC quantity (6 decimal places for precision)
        # Use current price for most accurate conversion
        quantity_btc = round(self.order_size / self._current_price, 6)

        # BingX minimum order: 0.0001 BTC
        if quantity_btc < 0.0001:
            orders_logger.warning(f"Quantidade muito pequena: {quantity_btc} BTC. Mínimo: 0.0001")
            return

        result = await self.client.create_limit_order_with_tp(
            symbol=self.symbol,
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
            if self.calculator.anchor_mode.value != "none":
                anchor_level = self.calculator.get_anchor_level(level.entry_price)
                orders_logger.info(f"Ordem criada (nível ancorado ${anchor_level:,.0f}): {level}")
            else:
                orders_logger.info(f"Ordem criada: {level}")

    async def _cancel_all_pending(self) -> None:
        """Cancel all pending LIMIT orders (preserves TPs)."""
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
                main_logger.info(f"{cancelled} ordem(ns) LIMIT cancelada(s) (INACTIVE)")
        except Exception as e:
            main_logger.error(f"Erro ao cancelar ordens: {e}")

    async def _sync_with_exchange(self) -> None:
        """Sync local state with exchange."""
        try:
            exchange_orders = await self.client.get_open_orders(self.symbol)
            positions = await self.client.get_positions(self.symbol)

            # 1. Check for filled orders (pending -> filled)
            exchange_order_ids = {str(o.get("orderId")) for o in exchange_orders}

            for order in list(self.tracker.pending_orders):
                if order.order_id not in exchange_order_ids:
                    # Order was filled or cancelled
                    self.tracker.order_filled(order.order_id)
                    if self._on_order_filled:
                        self._on_order_filled(order)
                    orders_logger.info(f"Ordem detectada como executada: {order.order_id}")

            # 2. Check for closed positions (filled positions that no longer exist)
            # Get current position amount from exchange
            current_position_amt = 0.0
            for pos in positions:
                amt = float(pos.get("positionAmt", 0))
                if amt != 0:
                    current_position_amt = abs(amt)
                    break

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
