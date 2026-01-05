"""Orders API endpoints for active grid orders."""

import logging
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies import get_order_tracker
from src.api.schemas.orders import OrderSchema, OrdersListResponse, OrderStatusEnum
from src.grid.order_tracker import OrderStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


def _convert_order_status(status: OrderStatus) -> OrderStatusEnum:
    """Convert internal OrderStatus to API OrderStatusEnum."""
    mapping = {
        OrderStatus.PENDING: OrderStatusEnum.PENDING,
        OrderStatus.FILLED: OrderStatusEnum.FILLED,
        OrderStatus.TP_HIT: OrderStatusEnum.TP_HIT,
        OrderStatus.CANCELLED: OrderStatusEnum.CANCELLED,
    }
    return mapping.get(status, OrderStatusEnum.PENDING)


@router.get("", response_model=OrdersListResponse)
async def get_orders(
    status: Annotated[
        str | None,
        Query(description="Filter by status (PENDING, FILLED, TP_HIT, CANCELLED)"),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Maximum number of orders to return")
    ] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of orders to skip")] = 0,
) -> OrdersListResponse:
    """Get active grid orders with optional filtering and pagination.

    Returns orders tracked by the GridManager's OrderTracker, including:
    - PENDING: Limit orders waiting to be filled
    - FILLED: Orders that have been filled and have open positions with TP orders

    Args:
        status: Optional status filter (PENDING, FILLED, TP_HIT, CANCELLED)
        limit: Maximum number of orders to return (1-1000)
        offset: Number of orders to skip for pagination

    Returns:
        OrdersListResponse: List of orders with pagination info and counts

    Raises:
        HTTPException: If OrderTracker is not available or invalid parameters
    """
    order_tracker = get_order_tracker()

    if order_tracker is None:
        raise HTTPException(
            status_code=503,
            detail="OrderTracker not available. Bot may not be fully initialized.",
        )

    try:
        # Validate status filter if provided
        valid_statuses = ["PENDING", "FILLED", "TP_HIT", "CANCELLED"]
        if status and status.upper() not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

        # Get all orders from tracker
        all_orders = list(order_tracker._orders.values())

        # Filter by status if provided
        if status:
            status_upper = status.upper()
            status_enum_map = {
                "PENDING": OrderStatus.PENDING,
                "FILLED": OrderStatus.FILLED,
                "TP_HIT": OrderStatus.TP_HIT,
                "CANCELLED": OrderStatus.CANCELLED,
            }
            target_status = status_enum_map.get(status_upper)
            if target_status:
                all_orders = [o for o in all_orders if o.status == target_status]

        # Sort by created_at descending (newest first)
        all_orders.sort(key=lambda o: o.created_at, reverse=True)

        # Get counts before pagination
        total = len(all_orders)
        pending_count = sum(
            1 for o in order_tracker._orders.values() if o.status == OrderStatus.PENDING
        )
        filled_count = sum(
            1 for o in order_tracker._orders.values() if o.status == OrderStatus.FILLED
        )

        # Apply pagination
        paginated_orders = all_orders[offset : offset + limit]

        # Convert to schemas
        order_schemas = [
            OrderSchema(
                order_id=order.order_id,
                price=Decimal(str(order.entry_price)),
                tp_price=Decimal(str(order.tp_price)),
                quantity=Decimal(str(order.quantity)),
                side="LONG",  # Currently bot only supports LONG
                status=_convert_order_status(order.status),
                created_at=order.created_at,
                filled_at=order.filled_at,
                closed_at=order.closed_at,
                exchange_tp_order_id=order.exchange_tp_order_id,
            )
            for order in paginated_orders
        ]

        return OrdersListResponse(
            orders=order_schemas,
            total=total,
            limit=limit,
            offset=offset,
            pending_count=pending_count,
            filled_count=filled_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}") from e
