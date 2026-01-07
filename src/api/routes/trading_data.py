"""Trading data API endpoints for positions, trades, and statistics."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_account_id, get_tp_adjustment_repository, get_trade_repository
from src.api.schemas.trading_data import (
    BestWorstTradeSchema,
    PerformanceMetricsSchema,
    PositionSchema,
    PositionsListResponse,
    TpAdjustmentSchema,
    TradeFeesSchema,
    TradeSchema,
    TradesListResponse,
    TradeStatsSchema,
)
from src.database.models.tp_adjustment import TPAdjustment
from src.database.models.trade import Trade
from src.database.repositories.tp_adjustment_repository import TPAdjustmentRepository
from src.database.repositories.trade_repository import TradeRepository


class ProfitFilter(str, Enum):
    """Filter trades by profit/loss status."""

    ALL = "all"
    PROFITABLE = "profitable"
    LOSSES = "losses"


class SortByField(str, Enum):
    """Sortable fields for trades endpoint."""

    CLOSED_AT = "closedAt"
    ENTRY_PRICE = "entryPrice"
    EXIT_PRICE = "exitPrice"
    QUANTITY = "quantity"
    PNL = "pnl"
    PNL_PERCENT = "pnlPercent"
    DURATION = "duration"


class SortDirection(str, Enum):
    """Sort direction options."""

    ASC = "asc"
    DESC = "desc"


class PeriodFilter(str, Enum):
    """Period options for performance metrics filtering."""

    TODAY = "today"
    SEVEN_DAYS = "7days"
    THIRTY_DAYS = "30days"
    CUSTOM = "custom"


router = APIRouter(prefix="/api/v1/trading")


def _build_adjustment_reason(adjustment: TPAdjustment) -> str:
    """Build a human-readable reason string from TP adjustment data.

    Args:
        adjustment: TPAdjustment model instance

    Returns:
        Formatted reason string describing the adjustment context
    """
    parts = []
    if adjustment.funding_rate is not None:
        parts.append(f"Funding rate: {adjustment.funding_rate:.4f}%")
    if adjustment.funding_accumulated is not None:
        parts.append(f"accumulated: {adjustment.funding_accumulated:.2f}%")
    if adjustment.hours_open is not None:
        parts.append(f"{adjustment.hours_open:.1f}h open")

    return ", ".join(parts) if parts else "Dynamic TP adjustment"


def _convert_tp_adjustment(adjustment: TPAdjustment) -> TpAdjustmentSchema:
    """Convert TPAdjustment model to TpAdjustmentSchema.

    Args:
        adjustment: TPAdjustment model instance

    Returns:
        TpAdjustmentSchema with simplified fields
    """
    return TpAdjustmentSchema(
        timestamp=adjustment.adjusted_at,
        old_tp=adjustment.old_tp_percent,
        new_tp=adjustment.new_tp_percent,
        reason=_build_adjustment_reason(adjustment),
    )


def _calculate_fees(trade: Trade) -> TradeFeesSchema:
    """Calculate fee breakdown with net P&L.

    Args:
        trade: Trade model instance

    Returns:
        TradeFeesSchema with trading_fee, funding_fee, and net_pnl
    """
    pnl = trade.pnl if trade.pnl is not None else Decimal("0")
    net_pnl = pnl - trade.trading_fee - trade.funding_fee

    return TradeFeesSchema(
        trading_fee=trade.trading_fee,
        funding_fee=trade.funding_fee,
        net_pnl=net_pnl,
    )


async def _enrich_trade(
    trade: Trade,
    tp_adjustment_repo: TPAdjustmentRepository,
) -> TradeSchema:
    """Enrich a trade with TP adjustments, duration, and fees.

    Args:
        trade: Trade model instance
        tp_adjustment_repo: Repository to fetch TP adjustments

    Returns:
        TradeSchema with all fields populated including new BE-TRADE-003 fields
    """
    # Fetch TP adjustments for this trade
    adjustments = await tp_adjustment_repo.get_by_trade(trade.id)
    tp_adjustment_schemas = [_convert_tp_adjustment(adj) for adj in adjustments]

    # Calculate duration and fees
    duration = _calculate_duration_seconds(trade)
    fees = _calculate_fees(trade)

    return TradeSchema(
        id=trade.id,
        account_id=trade.account_id,
        exchange_order_id=trade.exchange_order_id,
        exchange_tp_order_id=trade.exchange_tp_order_id,
        symbol=trade.symbol,
        side=trade.side,
        leverage=trade.leverage,
        entry_price=trade.entry_price,
        exit_price=trade.exit_price,
        quantity=trade.quantity,
        tp_price=trade.tp_price,
        tp_percent=trade.tp_percent,
        pnl=trade.pnl,
        pnl_percent=trade.pnl_percent,
        trading_fee=trade.trading_fee,
        funding_fee=trade.funding_fee,
        status=trade.status,
        grid_level=trade.grid_level,
        opened_at=trade.opened_at,
        filled_at=trade.filled_at,
        closed_at=trade.closed_at,
        created_at=trade.created_at,
        updated_at=trade.updated_at,
        duration=duration,
        fees=fees,
        tp_adjustments=tp_adjustment_schemas,
    )


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


def _get_sort_key(trade: Trade, sort_by: SortByField) -> tuple[bool, Decimal | int | datetime | None]:
    """Get the sort key for a trade based on the sort field.

    Returns a tuple of (is_none, value) where is_none is True if the value is None.
    This ensures None values are sorted consistently (at the end for ASC, start for DESC).

    Args:
        trade: Trade instance.
        sort_by: Field to sort by.

    Returns:
        Tuple of (is_none, value) for stable sorting with None handling.
    """
    value: Decimal | int | datetime | None = None

    if sort_by == SortByField.CLOSED_AT:
        value = trade.closed_at
    elif sort_by == SortByField.ENTRY_PRICE:
        value = trade.entry_price
    elif sort_by == SortByField.EXIT_PRICE:
        value = trade.exit_price
    elif sort_by == SortByField.QUANTITY:
        value = trade.quantity
    elif sort_by == SortByField.PNL:
        value = trade.pnl
    elif sort_by == SortByField.PNL_PERCENT:
        value = trade.pnl_percent
    elif sort_by == SortByField.DURATION:
        value = _calculate_duration_seconds(trade)

    # Return tuple for stable sorting: (is_none, value)
    # This ensures None values are always sorted to the end regardless of direction
    return (value is None, value if value is not None else Decimal(0))


def _apply_in_memory_sorting(
    trades: list[Trade],
    sort_by: SortByField,
    sort_direction: SortDirection,
) -> list[Trade]:
    """Sort trades in memory.

    Used when sorting by computed fields (duration) or when in-memory filters
    are applied and we need to re-sort the results.

    Args:
        trades: List of trades to sort.
        sort_by: Field to sort by.
        sort_direction: Sort direction (asc or desc).

    Returns:
        Sorted list of trades.
    """
    reverse = sort_direction == SortDirection.DESC
    return sorted(trades, key=lambda t: _get_sort_key(t, sort_by), reverse=reverse)


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
    tp_adjustment_repo: Annotated[TPAdjustmentRepository, Depends(get_tp_adjustment_repository)],
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
    sort_by: Annotated[
        SortByField,
        Query(
            description="Field to sort by (closedAt, entryPrice, exitPrice, "
            "quantity, pnl, pnlPercent, duration)"
        ),
    ] = SortByField.CLOSED_AT,
    sort_direction: Annotated[
        SortDirection, Query(description="Sort direction (asc, desc)")
    ] = SortDirection.DESC,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Maximum number of trades to return")
    ] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of trades to skip")] = 0,
):
    """Get trades for the current account with advanced filtering, sorting, and pagination.

    Supports 5 filter types:
    - profit_filter: Filter by profit/loss status (all, profitable, losses)
    - price range: Filter by min/max entry price
    - duration range: Filter by min/max trade duration in seconds
    - quantity range: Filter by min/max quantity
    - search: Search by exchange_order_id or exchange_tp_order_id

    Supports sorting by 7 columns:
    - closedAt (default): Sort by close timestamp
    - entryPrice: Sort by entry price
    - exitPrice: Sort by exit price
    - quantity: Sort by trade quantity
    - pnl: Sort by profit/loss amount
    - pnlPercent: Sort by profit/loss percentage
    - duration: Sort by trade duration (computed field)

    All filters combine with AND logic.

    Args:
        account_id: Account UUID (injected via dependency)
        trade_repo: Injected trade repository
        tp_adjustment_repo: Injected TP adjustment repository
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
        sort_by: Field to sort by (default: closedAt)
        sort_direction: Sort direction (default: desc)
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

        # Check if sorting needs to be done in-memory
        # Duration is a computed field that cannot be sorted in SQL
        needs_in_memory_sorting = (
            sort_by == SortByField.DURATION or has_in_memory_filters
        )

        # When in-memory processing is needed, fetch more records
        # This is a trade-off: we fetch more from DB to process in memory
        fetch_limit = limit * 10 if needs_in_memory_sorting else limit
        fetch_offset = 0 if needs_in_memory_sorting else offset

        # Fetch trades with SQL filters and optional SQL sorting
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
            sort_by=None if needs_in_memory_sorting else sort_by,
            sort_direction=sort_direction,
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

        # Apply in-memory sorting when needed
        if needs_in_memory_sorting:
            trades = _apply_in_memory_sorting(trades, sort_by, sort_direction)
            total = len(trades)
            trades = trades[offset : offset + limit]
        else:
            total = sql_total

        # Enrich trades with TP adjustments, duration, and fees
        trade_schemas = [await _enrich_trade(trade, tp_adjustment_repo) for trade in trades]

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
