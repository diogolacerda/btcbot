"""Trading data API endpoints for positions, trades, and statistics."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_account_id, get_trade_repository
from src.api.schemas.trading_data import (
    PositionSchema,
    PositionsListResponse,
    TradeSchema,
    TradesListResponse,
    TradeStatsSchema,
)
from src.database.models.trade import Trade
from src.database.repositories.trade_repository import TradeRepository


class ProfitFilter(str, Enum):
    """Filter trades by profit/loss status."""

    ALL = "all"
    PROFITABLE = "profitable"
    LOSSES = "losses"

router = APIRouter(prefix="/trading")


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


def _calculate_duration_seconds(trade: Trade) -> int | None:
    """Calculate trade duration in seconds.

    Args:
        trade: Trade instance.

    Returns:
        Duration in seconds, or None if trade is still open.
    """
    if trade.closed_at and trade.opened_at:
        return int((trade.closed_at - trade.opened_at).total_seconds())
    return None


def _apply_in_memory_filters(
    trades: list[Trade],
    *,
    profit_filter: ProfitFilter = ProfitFilter.ALL,
    min_duration: int | None = None,
    max_duration: int | None = None,
    search_query: str | None = None,
) -> list[Trade]:
    """Apply filters that require in-memory processing.

    Args:
        trades: List of trades to filter.
        profit_filter: Filter by profit/loss status.
        min_duration: Minimum duration in seconds.
        max_duration: Maximum duration in seconds.
        search_query: Search by exchange_order_id or exchange_tp_order_id.

    Returns:
        Filtered list of trades.
    """
    result = trades

    # Profit filter
    if profit_filter == ProfitFilter.PROFITABLE:
        result = [t for t in result if t.pnl is not None and t.pnl > 0]
    elif profit_filter == ProfitFilter.LOSSES:
        result = [t for t in result if t.pnl is not None and t.pnl < 0]

    # Duration filter
    if min_duration is not None or max_duration is not None:
        filtered_by_duration = []
        for trade in result:
            duration = _calculate_duration_seconds(trade)
            if duration is None:
                continue  # Skip open trades for duration filter
            if min_duration is not None and duration < min_duration:
                continue
            if max_duration is not None and duration > max_duration:
                continue
            filtered_by_duration.append(trade)
        result = filtered_by_duration

    # Search filter (exact match on exchange order IDs)
    if search_query:
        result = [
            t
            for t in result
            if (t.exchange_order_id and search_query in t.exchange_order_id)
            or (t.exchange_tp_order_id and search_query in t.exchange_tp_order_id)
        ]

    return result


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
    profit_filter: Annotated[
        ProfitFilter, Query(description="Filter by profit/loss (all, profitable, losses)")
    ] = ProfitFilter.ALL,
    min_entry_price: Annotated[
        Decimal | None, Query(description="Minimum entry price filter")
    ] = None,
    max_entry_price: Annotated[
        Decimal | None, Query(description="Maximum entry price filter")
    ] = None,
    min_duration: Annotated[
        int | None, Query(ge=0, description="Minimum trade duration in seconds")
    ] = None,
    max_duration: Annotated[
        int | None, Query(ge=0, description="Maximum trade duration in seconds")
    ] = None,
    min_quantity: Annotated[
        Decimal | None, Query(description="Minimum trade quantity filter")
    ] = None,
    max_quantity: Annotated[
        Decimal | None, Query(description="Maximum trade quantity filter")
    ] = None,
    search_query: Annotated[
        str | None, Query(description="Search by exchange_order_id or exchange_tp_order_id")
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Maximum number of trades to return")
    ] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of trades to skip")] = 0,
):
    """Get trades for the current account with advanced filtering and pagination.

    Supports 5 filter types:
    - profit_filter: Filter by profit/loss status (all, profitable, losses)
    - price range: Filter by min/max entry price
    - duration range: Filter by min/max trade duration in seconds
    - quantity range: Filter by min/max quantity
    - search: Search by exchange_order_id or exchange_tp_order_id

    All filters combine with AND logic.

    Args:
        account_id: Account UUID (injected via dependency)
        trade_repo: Injected trade repository
        status: Optional status filter (OPEN, CLOSED, CANCELLED)
        start_date: Optional start date filter
        end_date: Optional end date filter
        profit_filter: Filter by profit/loss status
        min_entry_price: Minimum entry price
        max_entry_price: Maximum entry price
        min_duration: Minimum duration in seconds
        max_duration: Maximum duration in seconds
        min_quantity: Minimum quantity
        max_quantity: Maximum quantity
        search_query: Search string for order IDs
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

        # Validate price range
        if min_entry_price is not None and max_entry_price is not None:
            if min_entry_price > max_entry_price:
                raise HTTPException(
                    status_code=400,
                    detail="min_entry_price cannot be greater than max_entry_price",
                )

        # Validate quantity range
        if min_quantity is not None and max_quantity is not None:
            if min_quantity > max_quantity:
                raise HTTPException(
                    status_code=400, detail="min_quantity cannot be greater than max_quantity"
                )

        # Validate duration range
        if min_duration is not None and max_duration is not None:
            if min_duration > max_duration:
                raise HTTPException(
                    status_code=400, detail="min_duration cannot be greater than max_duration"
                )

        # Check if any in-memory filters are applied
        has_in_memory_filters = (
            profit_filter != ProfitFilter.ALL
            or min_duration is not None
            or max_duration is not None
            or search_query is not None
        )

        # When in-memory filters are needed, fetch more records to filter
        # This is a trade-off: we fetch more from DB to apply filters in memory
        fetch_limit = limit * 10 if has_in_memory_filters else limit
        fetch_offset = 0 if has_in_memory_filters else offset

        # Fetch trades with SQL filters
        trades, sql_total = await trade_repo.get_trades_with_filters(
            account_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            min_entry_price=min_entry_price,
            max_entry_price=max_entry_price,
            min_quantity=min_quantity,
            max_quantity=max_quantity,
            limit=fetch_limit,
            offset=fetch_offset,
        )

        # Apply in-memory filters
        if has_in_memory_filters:
            trades = _apply_in_memory_filters(
                trades,
                profit_filter=profit_filter,
                min_duration=min_duration,
                max_duration=max_duration,
                search_query=search_query,
            )
            total = len(trades)
            trades = trades[offset : offset + limit]
        else:
            total = sql_total

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
