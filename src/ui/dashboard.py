from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.grid.grid_manager import GridStatus
from src.grid.order_tracker import TrackedOrder, TradeRecord
from src.strategy.macd_strategy import GridState


class Dashboard:
    """Terminal dashboard using Rich library."""

    def __init__(self):
        self.console = Console()
        self._live = None

    def _get_state_color(self, state: GridState) -> str:
        """Get color for grid state."""
        colors = {
            GridState.ACTIVATE: "green",
            GridState.ACTIVE: "bright_green",
            GridState.PAUSE: "yellow",
            GridState.INACTIVE: "red",
            GridState.WAIT: "dim",
        }
        return colors.get(state, "white")

    def _get_state_display(self, state: GridState, cycle_activated: bool = False) -> str:
        """Get display text for grid state."""
        if not cycle_activated:
            # Cycle not activated yet - show waiting state
            return "AGUARDANDO CICLO"

        displays = {
            GridState.ACTIVATE: "ATIVANDO",
            GridState.ACTIVE: "ATIVO",
            GridState.PAUSE: "PAUSADO",
            GridState.INACTIVE: "INATIVO",
            GridState.WAIT: "AGUARDANDO",
        }
        return displays.get(state, state.value.upper())

    def _format_price(self, price: float) -> str:
        """Format price with separators."""
        return f"${price:,.2f}"

    def _format_pnl(self, pnl: float) -> Text:
        """Format PnL with color."""
        color = "green" if pnl >= 0 else "red"
        sign = "+" if pnl >= 0 else ""
        return Text(f"{sign}${pnl:.2f}", style=color)

    def create_header(self, status: GridStatus) -> Panel:
        """Create header panel with MACD status."""
        state_color = "dim" if not status.cycle_activated else self._get_state_color(status.state)
        state_text = self._get_state_display(status.state, status.cycle_activated)

        # Determine histogram direction
        hist_direction = "↑" if status.histogram > 0 else "↓"
        hist_color = "green" if status.histogram > 0 else "red"

        header = Table.grid(expand=True)
        header.add_column(justify="left")
        header.add_column(justify="right")

        # Build title with warnings
        title_parts = [("BTC Grid Bot", "bold cyan")]
        if status.margin_error:
            title_parts.append((" [MARGEM]", "bold red"))
        if status.rate_limited:
            title_parts.append((" [RATE LIMIT]", "bold red"))

        header.add_row(
            Text.assemble(*title_parts),
            Text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="dim"),
        )

        # Cycle status indicator
        if status.cycle_activated:
            cycle_text = Text.assemble(
                ("CICLO ATIVO", "bold green"),
                " | ",
                ("D", "bold red"),
                (" desativa", "dim"),
            )
        else:
            cycle_text = Text.assemble(
                ("AGUARDANDO", "bold yellow"),
                " | ",
                ("A", "bold green"),
                (" ativa", "dim"),
            )

        header.add_row(
            Text.assemble(
                "Estado: ",
                (state_text, f"bold {state_color}"),
                f" | MACD: {status.macd_line:.2f}",
            ),
            cycle_text,
        )

        header.add_row(
            Text.assemble(
                "Histograma: ",
                (f"{status.histogram:.2f} {hist_direction}", hist_color),
            ),
            Text(""),
        )

        return Panel(header, title="[bold]Status[/bold]", border_style="blue")

    def create_price_panel(self, status: GridStatus, balance: float = 0) -> Panel:
        """Create price and balance panel."""
        content = Table.grid(expand=True)
        content.add_column(justify="left")
        content.add_column(justify="right")

        content.add_row(
            Text(f"BTC-USDT: {self._format_price(status.current_price)}", style="bold"),
            Text(f"Saldo: ${balance:,.2f} USDT", style="cyan"),
        )

        return Panel(content, border_style="blue")

    def create_positions_table(self, positions: list[TrackedOrder], current_price: float) -> Panel:
        """Create positions table."""
        table = Table(expand=True, show_header=True, header_style="bold")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Entrada", justify="right")
        table.add_column("Qtd", justify="right")
        table.add_column("TP", justify="right")
        table.add_column("PnL", justify="right")
        table.add_column("Dist TP", justify="right")

        for pos in positions[:10]:  # Limit to 10
            pnl = (current_price - pos.entry_price) * pos.quantity
            dist_tp = ((pos.tp_price - current_price) / current_price) * 100

            pnl_text = self._format_pnl(pnl)
            dist_text = Text(f"{dist_tp:.2f}%", style="yellow" if dist_tp > 0 else "green")

            table.add_row(
                f"#{pos.order_id[:6]}",
                self._format_price(pos.entry_price),
                f"{pos.quantity:.4f}",
                self._format_price(pos.tp_price),
                pnl_text,
                dist_text,
            )

        title = f"[bold]Posições Abertas ({len(positions)})[/bold]"
        return Panel(table, title=title, border_style="green")

    def create_orders_table(self, orders: list[TrackedOrder], grid_summary: dict) -> Panel:
        """Create pending orders summary."""
        content = Table.grid(expand=True)
        content.add_column()

        min_price = grid_summary.get("min_price", 0)
        spacing = grid_summary.get("spacing", 0)

        content.add_row(
            Text(f"Range: {self._format_price(grid_summary.get('current_price', 0))} - "
                 f"{self._format_price(min_price)} ({grid_summary.get('range_percent', 0)}% abaixo)")
        )
        content.add_row(
            Text(f"Espaçamento: ${spacing:,.2f}")
        )

        if orders:
            prices = sorted([o.entry_price for o in orders[:5]], reverse=True)
            prices_str = " | ".join(self._format_price(p) for p in prices)
            content.add_row(Text(f"Próximas: {prices_str}...", style="dim"))

        title = f"[bold]Ordens Pendentes ({len(orders)})[/bold]"
        return Panel(content, title=title, border_style="yellow")

    def create_history_table(self, trades: list[TradeRecord]) -> Panel:
        """Create trade history."""
        table = Table(expand=True, show_header=False)
        table.add_column()

        for trade in trades[-10:][::-1]:  # Last 10, reversed
            pnl_text = self._format_pnl(trade.pnl)
            pct = (trade.pnl / (trade.entry_price * trade.quantity)) * 100

            table.add_row(
                Text.assemble(
                    (trade.exit_time.strftime("%H:%M:%S"), "dim"),
                    " ✓ TP em ",
                    (self._format_price(trade.exit_price), "bold"),
                    " → ",
                    pnl_text,
                    f" ({pct:.1f}%)",
                )
            )

        title = f"[bold]Histórico (últimos {len(trades)})[/bold]"
        return Panel(table, title=title, border_style="cyan")

    def create_summary(self, status: GridStatus, win_rate: float) -> Panel:
        """Create summary panel."""
        content = Table.grid(expand=True)
        content.add_column()
        content.add_column()
        content.add_column()

        pnl_text = self._format_pnl(status.total_pnl)

        content.add_row(
            Text(f"Trades: {status.total_trades}"),
            Text.assemble("Lucro: ", pnl_text),
            Text(f"Taxa acerto: {win_rate:.0f}%"),
        )
        content.add_row(
            Text(f"Ordens: {status.pending_orders}"),
            Text(f"Posições: {status.open_positions}"),
            Text(""),
        )

        return Panel(content, title="[bold]Resumo[/bold]", border_style="magenta")

    def create_controls(self, cycle_activated: bool = False) -> Panel:
        """Create controls hint panel."""
        if cycle_activated:
            controls = Text.assemble(
                ("[Q]", "bold yellow"), " Sair  ",
                ("[D]", "bold red"), " Desativar Ciclo  ",
                ("[R]", "bold yellow"), " Reiniciar  ",
            )
        else:
            controls = Text.assemble(
                ("[Q]", "bold yellow"), " Sair  ",
                ("[A]", "bold green"), " Ativar Ciclo  ",
                ("[R]", "bold yellow"), " Reiniciar  ",
            )
        return Panel(controls, border_style="dim")

    def render(
        self,
        status: GridStatus,
        positions: list[TrackedOrder],
        pending_orders: list[TrackedOrder],
        trades: list[TradeRecord],
        grid_summary: dict,
        balance: float = 0,
        win_rate: float = 0,
    ) -> Layout:
        """Render complete dashboard."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=6),
            Layout(name="price", size=3),
            Layout(name="main"),
            Layout(name="summary", size=5),
            Layout(name="controls", size=3),
        )

        layout["header"].update(self.create_header(status))
        layout["price"].update(self.create_price_panel(status, balance))

        # Split main into positions and orders/history
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )

        layout["main"]["left"].update(
            self.create_positions_table(positions, status.current_price)
        )

        layout["main"]["right"].split_column(
            Layout(name="orders"),
            Layout(name="history"),
        )
        layout["main"]["right"]["orders"].update(
            self.create_orders_table(pending_orders, grid_summary)
        )
        layout["main"]["right"]["history"].update(
            self.create_history_table(trades)
        )

        layout["summary"].update(self.create_summary(status, win_rate))
        layout["controls"].update(self.create_controls(status.cycle_activated))

        return layout

    def start_live(self):
        """Start live rendering context."""
        self._live = Live(
            console=self.console,
            refresh_per_second=1,
            screen=True,
        )
        return self._live

    def update(self, layout: Layout) -> None:
        """Update live display."""
        if self._live:
            self._live.update(layout)
