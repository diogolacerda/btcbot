"""Performance metrics API endpoints."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_account_id, get_trade_repository
from src.api.schemas.metrics import (
    PerformanceMetricsResponse,
    PeriodMetrics,
    TimePeriod,
    TotalMetrics,
)
from src.database.models.trade import Trade
from src.database.repositories.trade_repository import TradeRepository

router = APIRouter(prefix="/api/v1/metrics", tags=["Metrics"])


def _calculate_period_dates(
    period: TimePeriod,
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[datetime, datetime]:
    """Calculate start and end dates based on period type.

    Args:
        period: The time period enum value.
        start_date: Custom start date (required for CUSTOM period).
        end_date: Custom end date (required for CUSTOM period).

    Returns:
        Tuple of (start_datetime, end_datetime).

    Raises:
        HTTPException: If custom period is selected but dates are missing.
    """
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == TimePeriod.TODAY:
        return today_start, now
    elif period == TimePeriod.SEVEN_DAYS:
        return today_start - timedelta(days=6), now
    elif period == TimePeriod.THIRTY_DAYS:
        return today_start - timedelta(days=29), now
    else:  # CUSTOM
        if not start_date or not end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date and end_date are required for custom period",
            )
        return start_date, end_date


def _calculate_metrics_from_trades(
    trades: list[Trade],
    period_label: str,
    start_date: datetime,
    end_date: datetime,
) -> PeriodMetrics:
    """Calculate period metrics from a list of trades.

    Args:
        trades: List of Trade objects.
        period_label: Label for the period (e.g., 'today', '7days').
        start_date: Period start datetime.
        end_date: Period end datetime.

    Returns:
        PeriodMetrics with calculated values.
    """
    closed_trades = [t for t in trades if t.status == "CLOSED" and t.pnl is not None]

    trades_closed = len(closed_trades)
    winning_trades = sum(1 for t in closed_trades if t.pnl is not None and t.pnl > 0)
    losing_trades = sum(1 for t in closed_trades if t.pnl is not None and t.pnl < 0)

    realized_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)
    realized_pnl_decimal = Decimal(str(realized_pnl)) if realized_pnl else Decimal("0")

    # Calculate P&L percentage relative to trade volume
    total_volume = sum(t.entry_price * t.quantity for t in closed_trades)
    pnl_percent = Decimal("0")
    if total_volume > 0:
        pnl_percent = (realized_pnl_decimal / Decimal(str(total_volume))) * Decimal("100")

    win_rate = Decimal("0")
    if trades_closed > 0:
        win_rate = (Decimal(winning_trades) / Decimal(trades_closed)) * Decimal("100")

    return PeriodMetrics(
        period=period_label,
        start_date=start_date,
        end_date=end_date,
        realized_pnl=realized_pnl_decimal.quantize(Decimal("0.01")),
        pnl_percent=pnl_percent.quantize(Decimal("0.01")),
        trades_closed=trades_closed,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate.quantize(Decimal("0.01")),
    )


def _calculate_total_metrics(trades: list[Trade]) -> TotalMetrics:
    """Calculate total metrics from all trades.

    Args:
        trades: List of all Trade objects.

    Returns:
        TotalMetrics with calculated values.
    """
    closed_trades = [t for t in trades if t.status == "CLOSED" and t.pnl is not None]
    total_trades = len(closed_trades)

    pnls = [t.pnl for t in closed_trades if t.pnl is not None]
    total_pnl = sum(pnls) if pnls else Decimal("0")
    total_pnl_decimal = Decimal(str(total_pnl))

    avg_profit = Decimal("0")
    if total_trades > 0:
        avg_profit = total_pnl_decimal / Decimal(total_trades)

    total_fees = sum(t.trading_fee + t.funding_fee for t in closed_trades)
    total_fees_decimal = Decimal(str(total_fees)) if total_fees else Decimal("0")

    net_pnl = total_pnl_decimal - total_fees_decimal

    best_trade = max(pnls) if pnls else Decimal("0")
    worst_trade = min(pnls) if pnls else Decimal("0")

    return TotalMetrics(
        total_pnl=total_pnl_decimal.quantize(Decimal("0.01")),
        total_trades=total_trades,
        avg_profit_per_trade=avg_profit.quantize(Decimal("0.01")),
        total_fees=total_fees_decimal.quantize(Decimal("0.01")),
        net_pnl=net_pnl.quantize(Decimal("0.01")),
        best_trade=Decimal(str(best_trade)).quantize(Decimal("0.01")),
        worst_trade=Decimal(str(worst_trade)).quantize(Decimal("0.01")),
    )


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics_current(
    account_id: Annotated[UUID, Depends(get_account_id)],
    trade_repo: Annotated[TradeRepository, Depends(get_trade_repository)],
    period: Annotated[
        TimePeriod,
        Query(description="Time period for filtering (today, 7days, 30days, custom)"),
    ] = TimePeriod.TODAY,
    start_date: Annotated[
        datetime | None,
        Query(description="Start date for custom period (required if period=custom)"),
    ] = None,
    end_date: Annotated[
        datetime | None,
        Query(description="End date for custom period (required if period=custom)"),
    ] = None,
):
    """Get performance metrics for the current bot account.

    Uses the global account ID configured at bot startup via get_account_id dependency.
    This is a convenience endpoint for single-account mode.

    Returns both period-specific metrics and all-time total metrics.

    Args:
        account_id: Account UUID (injected via get_account_id dependency).
        trade_repo: Injected trade repository.
        period: Time period filter (today, 7days, 30days, custom).
        start_date: Start date for custom period.
        end_date: End date for custom period.

    Returns:
        PerformanceMetricsResponse with period and total metrics.

    Raises:
        HTTPException: If account not configured or database operation fails.
    """

    try:
        # Calculate period boundaries
        period_start, period_end = _calculate_period_dates(period, start_date, end_date)

        # Fetch period trades and all trades in parallel
        period_trades = trade_repo.get_trades_by_period(account_id, period_start, period_end)
        all_trades = trade_repo.get_trades_by_account(account_id, limit=100000, offset=0)

        # Calculate metrics
        period_metrics = _calculate_metrics_from_trades(
            period_trades,
            period.value,
            period_start,
            period_end,
        )
        total_metrics = _calculate_total_metrics(all_trades)

        return PerformanceMetricsResponse(
            period_metrics=period_metrics,
            total_metrics=total_metrics,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch performance metrics: {str(e)}"
        ) from e


@router.get("/performance/{account_id}", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    account_id: UUID,
    trade_repo: Annotated[TradeRepository, Depends(get_trade_repository)],
    period: Annotated[
        TimePeriod,
        Query(description="Time period for filtering (today, 7days, 30days, custom)"),
    ] = TimePeriod.TODAY,
    start_date: Annotated[
        datetime | None,
        Query(description="Start date for custom period (required if period=custom)"),
    ] = None,
    end_date: Annotated[
        datetime | None,
        Query(description="End date for custom period (required if period=custom)"),
    ] = None,
):
    """Get performance metrics for a specific account.

    Returns both period-specific metrics and all-time total metrics.

    Args:
        account_id: Account UUID to get metrics for.
        trade_repo: Injected trade repository.
        period: Time period filter (today, 7days, 30days, custom).
        start_date: Start date for custom period.
        end_date: End date for custom period.

    Returns:
        PerformanceMetricsResponse with period and total metrics.

    Raises:
        HTTPException: If database operation fails or invalid parameters.
    """
    try:
        # Calculate period boundaries
        period_start, period_end = _calculate_period_dates(period, start_date, end_date)

        # Fetch period trades and all trades in parallel
        period_trades = trade_repo.get_trades_by_period(account_id, period_start, period_end)
        all_trades = trade_repo.get_trades_by_account(account_id, limit=100000, offset=0)

        # Calculate metrics
        period_metrics = _calculate_metrics_from_trades(
            period_trades,
            period.value,
            period_start,
            period_end,
        )
        total_metrics = _calculate_total_metrics(all_trades)

        return PerformanceMetricsResponse(
            period_metrics=period_metrics,
            total_metrics=total_metrics,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch performance metrics: {str(e)}"
        ) from e
