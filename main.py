#!/usr/bin/env python3
"""
BTC Grid Bot - Sistema de Grid Trading para BingX

Grid trading com estratégia MACD para futuros perpétuos BTC-USDT.
"""

import asyncio
import sys

import uvicorn

from config import load_config
from src.api.dependencies import set_global_account_id
from src.client.bingx_client import BingXClient
from src.database.engine import get_session
from src.database.helpers import get_or_create_account
from src.database.repositories.bot_state_repository import BotStateRepository
from src.database.repositories.grid_config_repository import GridConfigRepository
from src.database.repositories.trade_repository import TradeRepository
from src.grid.grid_manager import GridManager
from src.health.health_server import HealthServer
from src.strategy.macd_strategy import GridState
from src.ui.alerts import AudioAlerts
from src.utils.logger import main_logger


async def run_api_server() -> None:
    """Run FastAPI server on port 8081."""
    config = uvicorn.Config(
        "src.api.main:app",
        host="0.0.0.0",
        port=8081,
        log_level="info",
        access_log=False,  # Reduce noise, we have our own logging
    )
    server = uvicorn.Server(config)
    main_logger.info("FastAPI server starting on http://0.0.0.0:8081")
    main_logger.info("API docs available at http://localhost:8081/docs")
    await server.serve()


async def run_bot() -> None:
    """Main bot execution loop."""
    config = load_config()

    # Validate configuration
    if not config.bingx.api_key or not config.bingx.secret_key:
        main_logger.error("Erro: API_KEY e SECRET_KEY não configurados!")
        main_logger.error("Copie .env.example para .env e configure suas credenciais.")
        sys.exit(1)

    # Initialize components
    client = BingXClient(config.bingx)
    alerts = AudioAlerts(enabled=True)

    # Initialize health server (starts early for Docker healthcheck)
    health_server = HealthServer()
    health_server.set_bingx_client(client)
    await health_server.start()

    # Initialize database and restore state
    account_id = None
    restored_state = None
    db_trading_config = None  # Will hold config from database
    try:
        # Get/create account
        async for session in get_session():
            account_id = await get_or_create_account(
                session=session,
                bingx_config=config.bingx,
                trading_config=config.trading,
            )
            main_logger.info(f"Using account ID: {account_id}")

            # Configure HealthServer with account_id for API operations
            health_server.set_account_id(account_id)

            # Configure global account ID for FastAPI endpoints
            set_global_account_id(account_id)
            main_logger.info("Global account ID configured for FastAPI endpoints")

        # Fetch trading config from database for startup display
        if account_id:
            try:
                async for session in get_session():
                    from src.database.repositories.trading_config_repository import (
                        TradingConfigRepository,
                    )

                    trading_config_repo = TradingConfigRepository(session)
                    db_trading_config = await trading_config_repo.get_by_account(account_id)
                    if db_trading_config:
                        main_logger.info("Loaded trading config from database for startup display")
                    break
            except Exception as e:
                main_logger.warning(
                    f"Failed to load trading config from database: {e}. "
                    "Using environment variables for display."
                )

        # Try to restore previous state (using a new session)
        assert account_id is not None, "Account ID must be set before restoring state"
        async for session in get_session():
            bot_state_repository = BotStateRepository(session)
            bot_state = await bot_state_repository.get_by_account(account_id)
            if bot_state and await bot_state_repository.is_state_valid(
                bot_state, max_age_hours=config.bot_state.restore_max_age_hours
            ):
                main_logger.info(
                    f"Restaurando estado anterior: cycle_activated={bot_state.cycle_activated}, "
                    f"last_state={bot_state.last_state}"
                )
                # Save state for restoration after GridManager init
                restored_state = {
                    "cycle_activated": bot_state.cycle_activated,
                    "last_state": bot_state.last_state,
                }
            else:
                if bot_state:
                    main_logger.info(
                        "Estado anterior encontrado mas é muito antigo, começando do zero"
                    )
                else:
                    main_logger.info("Nenhum estado anterior encontrado, começando do zero")
    except Exception as e:
        main_logger.warning(
            f"Erro ao inicializar banco de dados: {e}. Continuando sem persistência."
        )
        account_id = None

    # Grid Manager with callbacks
    def on_state_change(old_state: GridState, new_state: GridState):
        if new_state == GridState.ACTIVATE:
            alerts.grid_activated()
        elif new_state == GridState.PAUSE:
            alerts.grid_paused()
        elif new_state == GridState.INACTIVE:
            alerts.grid_inactive()

    def on_order_filled(order):
        alerts.order_filled()

    def on_tp_hit(trade):
        alerts.tp_hit()

    # Create bot state repository for GridManager (will create sessions as needed)
    # Note: We pass None here because repository needs a session, which will be created
    # when needed via get_session() inside MACDStrategy._schedule_persist_state
    grid_manager = GridManager(
        config=config,
        client=client,
        on_state_change=on_state_change,
        on_order_filled=on_order_filled,
        on_tp_hit=on_tp_hit,
        account_id=account_id,
        bot_state_repository=None,  # Will be set after
        trade_repository=None,  # Will be set after
        trading_config_repository=None,  # Will be set after
    )

    # Set up bot state repository with a session factory
    if account_id:
        # Create a wrapper repository that creates sessions on demand
        async def _save_state_with_session(account_id, cycle_activated, last_state, **kwargs):
            """Helper to save state with a new session."""
            async for session in get_session():
                repo = BotStateRepository(session)
                return await repo.save_state(account_id, cycle_activated, last_state, **kwargs)

        # Monkey-patch the repository into the strategy
        # This is a workaround since we can't pass a session directly
        grid_manager.strategy._bot_state_repository = type(
            "BotStateRepositoryWrapper",
            (),
            {"save_state": lambda self, *args, **kwargs: _save_state_with_session(*args, **kwargs)},
        )()

        # Create a wrapper trade repository that creates sessions on demand
        async def _save_trade_with_session(trade_data):
            """Helper to save trade with a new session."""
            async for session in get_session():
                repo = TradeRepository(session)
                return await repo.save_trade(trade_data)

        # Monkey-patch the repository into the tracker
        grid_manager.tracker._trade_repository = type(
            "TradeRepositoryWrapper",
            (),
            {"save_trade": lambda self, *args, **kwargs: _save_trade_with_session(*args, **kwargs)},
        )()

        # Create a wrapper trading config repository that creates sessions on demand
        async def _get_trading_config_with_session(account_id):
            """Helper to get trading config with a new session."""
            async for session in get_session():
                repo = TradingConfigRepository(session)
                return await repo.get_by_account(account_id)

        async def _create_or_update_trading_config_with_session(account_id, **kwargs):
            """Helper to create/update trading config with a new session."""
            async for session in get_session():
                repo = TradingConfigRepository(session)
                return await repo.create_or_update(account_id, **kwargs)

        # Create wrapper repository for session management
        trading_config_wrapper = type(
            "TradingConfigRepositoryWrapper",
            (),
            {
                "get_by_account": lambda self, *args, **kwargs: _get_trading_config_with_session(
                    *args, **kwargs
                ),
                "create_or_update": lambda self,
                *args,
                **kwargs: _create_or_update_trading_config_with_session(*args, **kwargs),
            },
        )()

        # Configure wrapper in both GridManager and HealthServer
        grid_manager._trading_config_repository = trading_config_wrapper
        health_server.set_trading_config_repo(trading_config_wrapper)

        # Create a wrapper grid config repository that creates sessions on demand
        async def _get_grid_config_with_session(account_id):
            """Helper to get grid config with a new session."""
            async for session in get_session():
                repo = GridConfigRepository(session)
                return await repo.get_or_create(account_id)

        async def _save_grid_config_with_session(account_id, **kwargs):
            """Helper to save grid config with a new session."""
            async for session in get_session():
                repo = GridConfigRepository(session)
                return await repo.save_config(account_id, **kwargs)

        # Monkey-patch the repository into the grid manager
        grid_manager._grid_config_repo = type(
            "GridConfigRepositoryWrapper",
            (),
            {
                "get_or_create": lambda self, *args, **kwargs: _get_grid_config_with_session(
                    *args, **kwargs
                ),
                "save_config": lambda self, *args, **kwargs: _save_grid_config_with_session(
                    *args, **kwargs
                ),
                "to_dict": lambda self, config: {
                    "spacing_type": config.spacing_type,
                    "spacing_value": float(config.spacing_value),
                    "range_percent": float(config.range_percent),
                    "max_total_orders": config.max_total_orders,
                    "anchor_mode": config.anchor_mode,
                    "anchor_value": float(config.anchor_value),
                },
            },
        )()

    # Restore state if available
    if restored_state:
        grid_manager.strategy.restore_state(
            cycle_activated=bool(restored_state["cycle_activated"]),
            last_state=str(restored_state["last_state"]),
        )

    # Load trade history if enabled
    if account_id and config.bot_state.load_history_on_start:
        try:
            main_logger.info("Loading trade history from database...")
            async for session in get_session():
                # Get only CLOSED trades, ordered by most recent first
                from sqlalchemy import select

                from src.database.models.trade import Trade

                stmt = (
                    select(Trade)
                    .where(Trade.account_id == account_id, Trade.status == "CLOSED")
                    .order_by(Trade.closed_at.desc())
                    .limit(config.bot_state.history_limit)
                )
                result = await session.execute(stmt)
                historical_trades = list(result.scalars().all())

                if historical_trades:
                    stats = grid_manager.tracker.load_trade_history(historical_trades)
                    main_logger.info(
                        f"Trade history loaded: {stats['trades_loaded']} trades, "
                        f"Total PnL: ${stats['total_pnl']:.2f}, "
                        f"Win Rate: {stats['win_rate']:.1f}%"
                    )
                else:
                    main_logger.info("No historical trades found in database")
                break  # Only use first session
        except Exception as e:
            main_logger.warning(f"Failed to load trade history: {e}. Starting with empty history.")

    # Link grid manager to health server for status reporting
    health_server.set_grid_manager(grid_manager)

    # Set grid config repository and account ID on health server
    if account_id and hasattr(grid_manager, "_grid_config_repo"):
        health_server.set_grid_config_repo(grid_manager._grid_config_repo)  # type: ignore[arg-type]
        health_server.set_account_id(account_id)

    # Print startup info
    main_logger.info("═══════════════════════════════════════════")
    main_logger.info("       BTC Grid Bot - BingX Futures        ")
    main_logger.info("═══════════════════════════════════════════")

    # Show trading mode prominently
    if config.trading.is_demo:
        main_logger.info("🎮 MODO DEMO - Usando VST (tokens virtuais)")
        main_logger.info("Seus fundos reais NÃO serão afetados")
    else:
        main_logger.warning("⚠️  MODO LIVE - Usando USDT REAL!")
        main_logger.warning("Cuidado: Operações afetarão seus fundos reais!")

    # Use database config values if available, otherwise fall back to env vars
    display_symbol = db_trading_config.symbol if db_trading_config else config.trading.symbol
    display_leverage = db_trading_config.leverage if db_trading_config else config.trading.leverage
    display_order_size = (
        float(db_trading_config.order_size_usdt)
        if db_trading_config
        else config.trading.order_size_usdt
    )
    display_take_profit = (
        float(db_trading_config.take_profit_percent)
        if db_trading_config
        else config.grid.take_profit_percent
    )

    main_logger.info("Configuração:")
    main_logger.info(f"  Modo: {config.trading.mode.value.upper()}")
    main_logger.info(f"  Symbol: {display_symbol}")
    main_logger.info(f"  Leverage: {display_leverage}x")
    main_logger.info(f"  Order size: ${display_order_size} USDT")
    main_logger.info(
        f"  Grid spacing: {config.grid.spacing_value} ({config.grid.spacing_type.value})"
    )
    main_logger.info(f"  Range: {config.grid.range_percent}% abaixo do preço")
    main_logger.info(
        f"  Take profit: {display_take_profit}%"
        + (" (from database)" if db_trading_config else " (from env)")
    )
    main_logger.info(
        f"  MACD: {config.macd.fast}/{config.macd.slow}/{config.macd.signal} ({config.macd.timeframe})"
    )

    # Test connection
    try:
        main_logger.info("Testando conexão com BingX...")
        price = await client.get_price(config.trading.symbol)
        main_logger.info(f"Conectado! Preço atual: ${price:,.2f}")
    except Exception as e:
        main_logger.error(f"Erro de conexão: {e}")
        sys.exit(1)

    # Start grid manager
    await grid_manager.start()

    # Link WebSocket to health server (after grid_manager.start() creates it)
    if grid_manager._account_ws:
        health_server.set_account_websocket(grid_manager._account_ws)

    main_logger.info("Bot iniciado. Pressione Ctrl+C para encerrar.")

    try:
        # Main loop
        while True:
            try:
                # Update grid manager
                await grid_manager.update()

                # Wait before next update (5s with caching)
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                main_logger.error(f"Erro no loop principal: {e}")
                await asyncio.sleep(5)

    except KeyboardInterrupt:
        pass
    finally:
        main_logger.info("Encerrando bot...")
        await grid_manager.stop()
        await health_server.stop()
        await client.close()
        main_logger.info("Bot encerrado com sucesso.")


async def main():
    """Entry point - runs both bot and FastAPI server concurrently."""
    try:
        # Run both bot and API server concurrently
        await asyncio.gather(
            run_bot(),
            run_api_server(),
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        main_logger.error(f"Erro fatal: {e}")
        main_logger.exception("Erro fatal")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        main_logger.info("Encerrado pelo usuário.")
