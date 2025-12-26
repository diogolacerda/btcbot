#!/usr/bin/env python3
"""
BTC Grid Bot - Sistema de Grid Trading para BingX

Grid trading com estratégia MACD para futuros perpétuos BTC-USDT.
"""

import asyncio
import sys

from rich.console import Console
from rich.prompt import Confirm

from config import load_config
from src.client.bingx_client import BingXClient
from src.grid.grid_calculator import GridCalculator
from src.grid.grid_manager import GridManager
from src.strategy.macd_strategy import GridState
from src.ui.alerts import AudioAlerts
from src.ui.dashboard import Dashboard
from src.ui.keyboard_handler import KeyAction, KeyboardHandler
from src.utils.logger import main_logger

console = Console()


async def run_bot() -> None:
    """Main bot execution loop."""
    config = load_config()

    # Validate configuration
    if not config.bingx.api_key or not config.bingx.secret_key:
        console.print("[red]Erro: API_KEY e SECRET_KEY não configurados![/red]")
        console.print("Copie .env.example para .env e configure suas credenciais.")
        sys.exit(1)

    # Initialize components
    client = BingXClient(config.bingx)
    alerts = AudioAlerts(enabled=True)
    dashboard = Dashboard()
    calculator = GridCalculator(config.grid)

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

    grid_manager = GridManager(
        config=config,
        client=client,
        on_state_change=on_state_change,
        on_order_filled=on_order_filled,
        on_tp_hit=on_tp_hit,
    )

    # Keyboard handler for manual controls
    keyboard_handler = KeyboardHandler()
    should_quit = False

    def on_activate():
        if grid_manager.strategy.manual_activate():
            alerts.cycle_activated()

    def on_deactivate():
        grid_manager.strategy.manual_deactivate()
        alerts.cycle_deactivated()

    def on_quit():
        nonlocal should_quit
        should_quit = True

    keyboard_handler.set_callback(KeyAction.ACTIVATE_CYCLE, on_activate)
    keyboard_handler.set_callback(KeyAction.DEACTIVATE_CYCLE, on_deactivate)
    keyboard_handler.set_callback(KeyAction.QUIT, on_quit)

    # Print startup info
    console.print("\n[bold cyan]═══════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]        BTC Grid Bot - BingX Futures        [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════[/bold cyan]\n")

    # Show trading mode prominently
    if config.trading.is_demo:
        console.print("[bold green]🎮 MODO DEMO - Usando VST (tokens virtuais)[/bold green]")
        console.print("[dim]Seus fundos reais NÃO serão afetados[/dim]\n")
    else:
        console.print("[bold red]⚠️  MODO LIVE - Usando USDT REAL![/bold red]")
        console.print("[bold red]Cuidado: Operações afetarão seus fundos reais![/bold red]\n")

    console.print("[bold]Configuração:[/bold]")
    console.print(
        f"  Modo: [{'green' if config.trading.is_demo else 'red'}]{config.trading.mode.value.upper()}[/{'green' if config.trading.is_demo else 'red'}]"
    )
    console.print(f"  Symbol: [cyan]{config.trading.symbol}[/cyan]")
    console.print(f"  Leverage: [cyan]{config.trading.leverage}x[/cyan]")
    console.print(f"  Order size: [cyan]${config.trading.order_size_usdt} USDT[/cyan]")
    console.print(
        f"  Grid spacing: [cyan]{config.grid.spacing_value} ({config.grid.spacing_type.value})[/cyan]"
    )
    console.print(f"  Range: [cyan]{config.grid.range_percent}% abaixo do preço[/cyan]")
    console.print(f"  Take profit: [cyan]{config.grid.take_profit_percent}%[/cyan]")
    console.print(
        f"  MACD: [cyan]{config.macd.fast}/{config.macd.slow}/{config.macd.signal} ({config.macd.timeframe})[/cyan]"
    )
    console.print()

    # Test connection
    try:
        console.print("[yellow]Testando conexão com BingX...[/yellow]")
        price = await client.get_price(config.trading.symbol)
        console.print(f"[green]Conectado! Preço atual: ${price:,.2f}[/green]\n")
    except Exception as e:
        console.print(f"[red]Erro de conexão: {e}[/red]")
        sys.exit(1)

    # Confirm start
    if not Confirm.ask("[bold yellow]Iniciar o bot?[/bold yellow]"):
        console.print("[dim]Operação cancelada.[/dim]")
        await client.close()
        sys.exit(0)

    # Start grid manager
    await grid_manager.start()

    # Start keyboard handler
    keyboard_handler.start()

    try:
        # Main loop with dashboard
        with dashboard.start_live():
            while not should_quit:
                try:
                    # Update grid manager
                    await grid_manager.update()

                    # Get current status
                    status = grid_manager.get_status()
                    tracker = grid_manager.tracker
                    grid_summary = calculator.get_grid_summary(status.current_price)

                    # Get balance
                    try:
                        balance_data = await client.get_balance()
                        balance = float(balance_data.get("balance", {}).get("availableMargin", 0))
                    except Exception:
                        balance = 0

                    # Render dashboard
                    layout = dashboard.render(
                        status=status,
                        positions=tracker.filled_orders,
                        pending_orders=tracker.pending_orders,
                        trades=tracker._trades,
                        grid_summary=grid_summary,
                        balance=balance,
                        win_rate=tracker.win_rate,
                    )
                    dashboard.update(layout)

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
        console.print("\n[yellow]Encerrando bot...[/yellow]")
        keyboard_handler.stop()
        await grid_manager.stop()
        await client.close()
        console.print("[green]Bot encerrado com sucesso.[/green]")


async def main():
    """Entry point."""
    try:
        await run_bot()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]Erro fatal: {e}[/red]")
        main_logger.exception("Erro fatal")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[dim]Encerrado pelo usuário.[/dim]")
