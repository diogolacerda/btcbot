#!/usr/bin/env python3
"""
BTC Grid Bot - Sistema de Grid Trading para BingX

Grid trading com estratégia MACD para futuros perpétuos BTC-USDT.
"""

import asyncio
import sys

from config import load_config
from src.client.bingx_client import BingXClient
from src.database.engine import get_session
from src.database.helpers import get_or_create_account
from src.database.repositories.bot_state_repository import BotStateRepository
from src.grid.grid_manager import GridManager
from src.health.health_server import HealthServer
from src.strategy.macd_strategy import GridState
from src.ui.alerts import AudioAlerts
from src.utils.logger import main_logger


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
    try:
        # Get/create account
        async for session in get_session():
            account_id = await get_or_create_account(
                session=session,
                bingx_config=config.bingx,
                trading_config=config.trading,
            )
            main_logger.info(f"Using account ID: {account_id}")

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

    # Restore state if available
    if restored_state:
        grid_manager.strategy.restore_state(
            cycle_activated=bool(restored_state["cycle_activated"]),
            last_state=str(restored_state["last_state"]),
        )

    # Link grid manager to health server for status reporting
    health_server.set_grid_manager(grid_manager)

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

    main_logger.info("Configuração:")
    main_logger.info(f"  Modo: {config.trading.mode.value.upper()}")
    main_logger.info(f"  Symbol: {config.trading.symbol}")
    main_logger.info(f"  Leverage: {config.trading.leverage}x")
    main_logger.info(f"  Order size: ${config.trading.order_size_usdt} USDT")
    main_logger.info(
        f"  Grid spacing: {config.grid.spacing_value} ({config.grid.spacing_type.value})"
    )
    main_logger.info(f"  Range: {config.grid.range_percent}% abaixo do preço")
    main_logger.info(f"  Take profit: {config.grid.take_profit_percent}%")
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
    """Entry point."""
    try:
        await run_bot()
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
