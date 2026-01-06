"""Trading data API endpoints for positions, trades, and statistics."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_account_id, get_trade_repository
from src.api.schemas.trading_data import (
    BestWorstTradeSchema,
    PerformanceMetricsSchema,
    PositionSchema,
    PositionsListResponse,
    TradeSchema,
    TradesListResponse,
    TradeStatsSchema,
)
from src.database.models.trade import Trade
from src.database.repositories.trade_repository import TradeRepository

router = APIRouter(prefix="/api/v1/trading")


class PeriodFilter(str, Enum):
    """Period options for performance metrics filtering."""

    TODAY = "today"
    SEVEN_DAYS = "7days"
    THIRTY_DAYS = "30days"
    CUSTOM = "custom"


@router.get("/positions", response_model=PositionsListResponse)
async def get_positions(
    account_id: Annotated[UUID, Depends(get_account_id)],
    trade_repo: Annotated[TradeRepository, Depends(get_trade_repository)],
):
    """Get all open positions for the current account.

    Args:
        account_id: Account UUID (injected via dependency)
        trade_repo: Injected trade repository

    Returns:
        PositionsListResponse: List of open positions

    Raises:
        HTTPException: If database operation fails
    """
    try:
        # Get open trades from database
        open_trades = await trade_repo.get_open_trades(account_id)

        # Convert trades to position schemas
        positions = [
            PositionSchema(
                symbol=trade.symbol,
                side=trade.side,
                leverage=trade.leverage,
                entry_price=trade.entry_price,
                quantity=trade.quantity,
                tp_price=trade.tp_price,
                tp_percent=trade.tp_percent,
                unrealized_pnl=trade.pnl,  # For open trades, pnl is unrealized
                opened_at=trade.opened_at,
                grid_level=trade.grid_level,
            )
            for trade in open_trades
        ]

        return PositionsListResponse(
            positions=positions,
            total=len(positions),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}") from e


@router.get("/trades", response_model=TradesListResponse)
async def get_trades(
    account_id: Annotated[UUID, Depends(get_account_id)],
    trade_repo: Annotated[TradeRepository, Depends(get_trade_repository)],
    status: Annotated[
        str | None, Query(description="Filter by status (OPEN, CLOSED, CANCELLED)")
    ] = None,
    start_date: Annotated[
        datetime | None, Query(description="Filter trades after this date")
    ] = None,
    end_date: Annotated[
        datetime | None, Query(description="Filter trades before this date")
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Maximum number of trades to return")
    ] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of trades to skip")] = 0,
):
    """Get trades for the current account with optional filtering and pagination.

    Args:
        account_id: Account UUID (injected via dependency)
        trade_repo: Injected trade repository
        status: Optional status filter (OPEN, CLOSED, CANCELLED)
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of trades to return (1-1000)
        offset: Number of trades to skip for pagination

    Returns:
        TradesListResponse: List of trades with pagination info

    Raises:
        HTTPException: If database operation fails or invalid parameters
    """
    try:
        # Validate status filter if provided
        if status and status not in ["OPEN", "CLOSED", "CANCELLED"]:
            raise HTTPException(
                status_code=400, detail="Invalid status. Must be one of: OPEN, CLOSED, CANCELLED"
            )

        # Fetch trades based on filters
        if start_date and end_date:
            trades = await trade_repo.get_trades_by_period(account_id, start_date, end_date)
        elif status:
            if status == "OPEN":
                trades = await trade_repo.get_open_trades(account_id)
            else:
                # Get all trades and filter by status
                all_trades = await trade_repo.get_trades_by_account(
                    account_id, limit=limit + offset, offset=0
                )
                trades = [t for t in all_trades if t.status == status]
        else:
            trades = await trade_repo.get_trades_by_account(
                account_id, limit=limit + offset, offset=0
            )

        # Apply pagination
        total = len(trades)
        trades = trades[offset : offset + limit]

        # Convert to schemas
        trade_schemas = [TradeSchema.model_validate(trade) for trade in trades]

        return TradesListResponse(
            trades=trade_schemas,
            total=total,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trades: {str(e)}") from e


@router.get("/stats", response_model=TradeStatsSchema)
async def get_trade_stats(
    account_id: Annotated[UUID, Depends(get_account_id)],
    trade_repo: Annotated[TradeRepository, Depends(get_trade_repository)],
    start_date: Annotated[
        datetime | None, Query(description="Calculate stats from this date")
    ] = None,
    end_date: Annotated[
        datetime | None, Query(description="Calculate stats until this date")
    ] = None,
):
    """Get trading statistics for the current account.

    Calculates comprehensive statistics including win rate, total P&L,
    fees, and average trade performance.

    Args:
        account_id: Account UUID (injected via dependency)
        trade_repo: Injected trade repository
        start_date: Optional start date for stats calculation
        end_date: Optional end date for stats calculation

    Returns:
        TradeStatsSchema: Trading statistics

    Raises:
        HTTPException: If database operation fails
    """
    try:
        # Fetch trades based on date filters
        if start_date and end_date:
            trades = await trade_repo.get_trades_by_period(account_id, start_date, end_date)
        else:
            trades = await trade_repo.get_trades_by_account(account_id, limit=10000, offset=0)

        # Calculate statistics
        total_trades = len(trades)
        open_trades = sum(1 for t in trades if t.status == "OPEN")
        closed_trades = sum(1 for t in trades if t.status == "CLOSED")

        # Only consider closed trades for P&L stats
        closed_trades_list = [t for t in trades if t.status == "CLOSED" and t.pnl is not None]

        # Calculate winning/losing trades (mypy safe - filtered by pnl is not None)
        winning_trades = sum(1 for t in closed_trades_list if t.pnl is not None and t.pnl > 0)
        losing_trades = sum(1 for t in closed_trades_list if t.pnl is not None and t.pnl < 0)

        win_rate = Decimal("0")
        if closed_trades > 0:
            win_rate = (Decimal(winning_trades) / Decimal(closed_trades)) * Decimal("100")

        # Total P&L (mypy safe - all trades have non-null pnl after filter)
        total_pnl_sum = sum(t.pnl for t in closed_trades_list if t.pnl is not None)
        total_pnl = Decimal(str(total_pnl_sum)) if total_pnl_sum else Decimal("0")
        total_fees_sum = sum(t.trading_fee + t.funding_fee for t in trades)
        total_fees = Decimal(str(total_fees_sum)) if total_fees_sum else Decimal("0")
        net_pnl = total_pnl - total_fees

        avg_pnl_per_trade = Decimal("0")
        if closed_trades > 0:
            avg_pnl_per_trade = total_pnl / Decimal(closed_trades)

        # Calculate average win/loss (mypy safe - filtered)
        winning_pnls: list[Decimal] = [
            t.pnl for t in closed_trades_list if t.pnl is not None and t.pnl > 0
        ]
        losing_pnls: list[Decimal] = [
            t.pnl for t in closed_trades_list if t.pnl is not None and t.pnl < 0
        ]

        avg_win = Decimal("0")
        if winning_pnls:
            avg_win = sum(winning_pnls) / Decimal(len(winning_pnls))

        avg_loss = Decimal("0")
        if losing_pnls:
            avg_loss = sum(losing_pnls) / Decimal(len(losing_pnls))

        largest_win = max(winning_pnls) if winning_pnls else Decimal("0")
        largest_loss = min(losing_pnls) if losing_pnls else Decimal("0")

        return TradeStatsSchema(
            total_trades=total_trades,
            open_trades=open_trades,
            closed_trades=closed_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate.quantize(Decimal("0.01")),
            total_pnl=total_pnl.quantize(Decimal("0.01")),
            total_fees=total_fees.quantize(Decimal("0.01")),
            net_pnl=net_pnl.quantize(Decimal("0.01")),
            avg_pnl_per_trade=avg_pnl_per_trade.quantize(Decimal("0.01")),
            avg_win=avg_win.quantize(Decimal("0.01")),
            avg_loss=avg_loss.quantize(Decimal("0.01")),
            largest_win=largest_win.quantize(Decimal("0.01")),
            largest_loss=largest_loss.quantize(Decimal("0.01")),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate stats: {str(e)}") from e


def _calculate_period_dates(
    period: PeriodFilter,
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[datetime, datetime]:
    """Calculate start and end dates based on period type.

    Args:
        period: The period filter enum value.
        start_date: Custom start date (required for CUSTOM period).
        end_date: Custom end date (required for CUSTOM period).

    Returns:
        Tuple of (start_datetime, end_datetime).

    Raises:
        HTTPException: If custom period is selected but dates are missing.
    """
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == PeriodFilter.TODAY:
        return today_start, now
    elif period == PeriodFilter.SEVEN_DAYS:
        return today_start - timedelta(days=6), now
    elif period == PeriodFilter.THIRTY_DAYS:
        return today_start - timedelta(days=29), now
    else:  # CUSTOM
        if not start_date or not end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date and end_date are required for custom period",
            )
        return start_date, end_date


def _find_best_worst_trades(
    trades: list[Trade],
) -> tuple[BestWorstTradeSchema, BestWorstTradeSchema]:
    """Find the best and worst trades from a list.

    Args:
        trades: List of closed Trade objects with non-null pnl.

    Returns:
        Tuple of (best_trade, worst_trade) schemas.

    Notes:
        - Empty list: both null
        - Single trade: appears only in best (if positive) or worst (if negative),
          not both. Break-even trades (pnl=0) result in both being null.
        - Multiple trades: standard max/min logic
    """
    null_trade = BestWorstTradeSchema(id=None, pnl=Decimal("0"), date=None)

    if not trades:
        return (null_trade, null_trade)

    # Special case: single trade should only appear in one field
    if len(trades) == 1:
        trade = trades[0]
        pnl = trade.pnl if trade.pnl is not None else Decimal("0")
        trade_schema = BestWorstTradeSchema(
            id=trade.id,
            pnl=Decimal(str(pnl)).quantize(Decimal("0.01")),
            date=trade.closed_at,
        )

        if pnl > 0:
            # Positive trade: it's the best, no worst
            return (trade_schema, null_trade)
        elif pnl < 0:
            # Negative trade: it's the worst, no best
            return (null_trade, trade_schema)
        else:
            # Break-even trade: neither best nor worst
            return (null_trade, null_trade)

    # Multiple trades: find best (max pnl) and worst (min pnl)
    best = max(trades, key=lambda t: t.pnl if t.pnl is not None else Decimal("-999999"))
    worst = min(trades, key=lambda t: t.pnl if t.pnl is not None else Decimal("999999"))

    return (
        BestWorstTradeSchema(
            id=best.id,
            pnl=Decimal(str(best.pnl)).quantize(Decimal("0.01")) if best.pnl else Decimal("0"),
            date=best.closed_at,
        ),
        BestWorstTradeSchema(
            id=worst.id,
            pnl=Decimal(str(worst.pnl)).quantize(Decimal("0.01")) if worst.pnl else Decimal("0"),
            date=worst.closed_at,
        ),
    )


@router.get("/performance-metrics", response_model=PerformanceMetricsSchema)
async def get_performance_metrics(
    account_id: Annotated[UUID, Depends(get_account_id)],
    trade_repo: Annotated[TradeRepository, Depends(get_trade_repository)],
    period: Annotated[
        PeriodFilter,
        Query(description="Time period for filtering (today, 7days, 30days, custom)"),
    ] = PeriodFilter.TODAY,
    start_date: Annotated[
        datetime | None,
        Query(description="Start date for custom period (required if period=custom)"),
    ] = None,
    end_date: Annotated[
        datetime | None,
        Query(description="End date for custom period (required if period=custom)"),
    ] = None,
):
    """Get performance metrics for the current account.

    Calculates comprehensive trading analytics including:
    - Total P&L and ROI based on capital employed
    - Win rate and trade counts
    - Best and worst trades with full details (id, pnl, date)

    The ROI is calculated as: (totalPnl / sum(entryPrice * quantity)) * 100

    Args:
        account_id: Account UUID (injected via get_account_id dependency).
        trade_repo: Injected trade repository.
        period: Time period filter (today, 7days, 30days, custom).
        start_date: Start date for custom period.
        end_date: End date for custom period.

    Returns:
        PerformanceMetricsSchema with all calculated metrics.

    Raises:
        HTTPException: If database operation fails or invalid parameters.
    """
    try:
        # Calculate period boundaries
        period_start, period_end = _calculate_period_dates(period, start_date, end_date)

        # Fetch trades for the period
        trades = await trade_repo.get_trades_by_period(account_id, period_start, period_end)

        # Filter to closed trades with P&L
        closed_trades = [t for t in trades if t.status == "CLOSED" and t.pnl is not None]

        # Calculate basic counts
        total_trades = len(closed_trades)
        winning_trades = sum(1 for t in closed_trades if t.pnl is not None and t.pnl > 0)
        losing_trades = sum(1 for t in closed_trades if t.pnl is not None and t.pnl < 0)

        # Calculate total P&L
        total_pnl_sum = sum(t.pnl for t in closed_trades if t.pnl is not None)
        total_pnl = Decimal(str(total_pnl_sum)) if total_pnl_sum else Decimal("0")

        # Calculate capital employed (sum of entry_price * quantity)
        capital_employed = sum(t.entry_price * t.quantity for t in closed_trades)
        capital_employed_decimal = (
            Decimal(str(capital_employed)) if capital_employed else Decimal("0")
        )

        # Calculate ROI: (totalPnl / capital_employed) * 100
        roi = Decimal("0")
        if capital_employed_decimal > 0:
            roi = (total_pnl / capital_employed_decimal) * Decimal("100")

        # Calculate win rate
        win_rate = Decimal("0")
        if total_trades > 0:
            win_rate = (Decimal(winning_trades) / Decimal(total_trades)) * Decimal("100")

        # Calculate average profit per trade
        avg_profit = Decimal("0")
        if total_trades > 0:
            avg_profit = total_pnl / Decimal(total_trades)

        # Find best and worst trades
        best_trade, worst_trade = _find_best_worst_trades(closed_trades)

        return PerformanceMetricsSchema(
            total_pnl=total_pnl.quantize(Decimal("0.01")),
            roi=roi.quantize(Decimal("0.01")),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate.quantize(Decimal("0.01")),
            avg_profit=avg_profit.quantize(Decimal("0.01")),
            best_trade=best_trade,
            worst_trade=worst_trade,
            period_start=period_start,
            period_end=period_end,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate performance metrics: {str(e)}"
        ) from e
