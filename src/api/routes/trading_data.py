"""Trading data API endpoints for positions, trades, and statistics."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_trade_repository
from src.api.schemas.trading_data import (
    PositionSchema,
    PositionsListResponse,
    TradeSchema,
    TradesListResponse,
    TradeStatsSchema,
)
from src.database.repositories.trade_repository import TradeRepository

router = APIRouter(prefix="/trading")


@router.get("/positions/{account_id}", response_model=PositionsListResponse)
async def get_positions(
    account_id: UUID,
    trade_repo: Annotated[TradeRepository, Depends(get_trade_repository)],
):
    """Get all open positions for an account.

    Args:
        account_id: Account UUID to get positions for
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


@router.get("/trades/{account_id}", response_model=TradesListResponse)
async def get_trades(
    account_id: UUID,
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
    """Get trades for an account with optional filtering and pagination.

    Args:
        account_id: Account UUID to get trades for
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


@router.get("/stats/{account_id}", response_model=TradeStatsSchema)
async def get_trade_stats(
    account_id: UUID,
    trade_repo: Annotated[TradeRepository, Depends(get_trade_repository)],
    start_date: Annotated[
        datetime | None, Query(description="Calculate stats from this date")
    ] = None,
    end_date: Annotated[
        datetime | None, Query(description="Calculate stats until this date")
    ] = None,
):
    """Get trading statistics for an account.

    Calculates comprehensive statistics including win rate, total P&L,
    fees, and average trade performance.

    Args:
        account_id: Account UUID to get stats for
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
