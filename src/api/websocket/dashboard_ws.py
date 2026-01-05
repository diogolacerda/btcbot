"""WebSocket endpoint for real-time dashboard updates.

This module provides the WebSocket endpoint for the dashboard to receive
real-time updates from the bot. It handles:
- JWT authentication via query parameter
- Connection lifecycle management
- Message handling (ping/pong)
- Event broadcasting integration
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from src.api.dependencies import ALGORITHM, SECRET_KEY
from src.api.websocket.connection_manager import ConnectionManager, get_connection_manager
from src.api.websocket.events import BotStatusEvent, WebSocketEvent, WebSocketEventType
from src.database.engine import get_session_maker
from src.database.models.user import User

if TYPE_CHECKING:
    from src.grid.grid_manager import GridManager

logger = logging.getLogger(__name__)

router = APIRouter()


async def authenticate_websocket(token: str) -> str | None:
    """Authenticate WebSocket connection using JWT token.

    Args:
        token: JWT token from query parameter.

    Returns:
        User email if authentication successful, None otherwise.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")

        if email is None:
            logger.warning("WebSocket auth failed: no email in token")
            return None

        # Verify user exists and is active
        session_maker = get_session_maker()
        async with session_maker() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user is None:
                logger.warning(f"WebSocket auth failed: user not found - {email}")
                return None

            if not user.is_active:
                logger.warning(f"WebSocket auth failed: user inactive - {email}")
                return None

        return email

    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket auth failed: token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"WebSocket auth failed: invalid token - {e}")
        return None
    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        return None


@router.websocket("/ws/dashboard")
async def dashboard_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
) -> None:
    """WebSocket endpoint for dashboard real-time updates.

    Clients must provide a valid JWT token via query parameter.
    Example: ws://localhost:8000/ws/dashboard?token=<jwt_token>

    Events sent to clients:
    - bot_status: Bot state changes
    - position_update: Position changes
    - order_update: Order status changes
    - price_update: Current BTC price
    - activity_event: Activity log events
    - heartbeat: Connection health check (every 30s)

    Supported client messages:
    - {"type": "ping"}: Returns pong response
    - {"type": "subscribe", "events": ["bot_status", ...]}: Subscribe to specific events

    Args:
        websocket: WebSocket connection.
        token: JWT authentication token from query parameter.
    """
    # Authenticate before accepting connection
    user_email = await authenticate_websocket(token)

    if user_email is None:
        # Close connection with authentication error
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    manager = get_connection_manager()

    try:
        # Accept connection
        await manager.connect(websocket, user_email)

        # Send initial connection success message
        await manager.send_personal(
            websocket,
            WebSocketEvent(
                type=WebSocketEventType.CONNECTION_ESTABLISHED,
                data={
                    "message": "Connected to BTC Grid Bot WebSocket",
                    "user": user_email,
                },
                timestamp=datetime.now(),
            ),
        )

        # Listen for client messages
        while True:
            try:
                data = await websocket.receive_json()
                await handle_client_message(websocket, data, manager)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket receive error: {e}")
                await manager.send_personal(
                    websocket,
                    WebSocketEvent.error("receive_error", str(e)),
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user_email}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


async def handle_client_message(
    websocket: WebSocket,
    data: dict,
    manager: ConnectionManager,
) -> None:
    """Handle incoming messages from WebSocket clients.

    Args:
        websocket: WebSocket connection.
        data: Parsed JSON message from client.
        manager: ConnectionManager instance.
    """
    message_type = data.get("type")

    if message_type == "ping":
        # Respond to ping with pong
        manager.update_heartbeat(websocket)
        await manager.send_personal(
            websocket,
            WebSocketEvent(
                type=WebSocketEventType.PONG,
                data={"timestamp": datetime.now().isoformat()},
                timestamp=datetime.now(),
            ),
        )

    elif message_type == "subscribe":
        # Handle subscription to specific event types
        events = data.get("events", [])
        logger.info(f"Client subscribed to events: {events}")
        await manager.send_personal(
            websocket,
            WebSocketEvent(
                type=WebSocketEventType.SUBSCRIPTION_CONFIRMED,
                data={"events": events},
                timestamp=datetime.now(),
            ),
        )

    elif message_type == "request_status":
        # Client requesting current bot status
        # This would trigger a status broadcast
        from src.api.dependencies import get_grid_manager

        try:
            grid_manager = get_grid_manager()
            # Get current status and send to client
            await send_current_status(websocket, manager, grid_manager)
        except Exception as e:
            await manager.send_personal(
                websocket,
                WebSocketEvent.error("status_unavailable", str(e)),
            )

    else:
        logger.warning(f"Unknown WebSocket message type: {message_type}")


async def send_current_status(
    websocket: WebSocket,
    manager: ConnectionManager,
    grid_manager: GridManager,
) -> None:
    """Send current bot status to a specific client.

    Args:
        websocket: Target WebSocket connection.
        manager: ConnectionManager instance.
        grid_manager: GridManager instance.
    """
    try:
        # Build status from GridManager
        # GridManager uses 'tracker' attribute for OrderTracker
        tracker = getattr(grid_manager, "tracker", None)
        strategy = getattr(grid_manager, "strategy", None)

        # Get state from strategy's _prev_state (last calculated state)
        state_name = "UNKNOWN"
        if strategy and hasattr(strategy, "_prev_state") and strategy._prev_state:
            state_name = strategy._prev_state.name

        status_event = BotStatusEvent(
            state=state_name,
            is_running=getattr(grid_manager, "is_running", True),
            macd_trend=None,  # MACD trend requires klines to calculate
            grid_active=getattr(grid_manager, "grid_active", False),
            pending_orders_count=len(tracker.pending_orders) if tracker else 0,
            filled_orders_count=len(tracker.filled_orders) if tracker else 0,
        )

        await manager.send_personal(websocket, WebSocketEvent.bot_status(status_event))
    except Exception as e:
        logger.error(f"Error sending current status: {e}")
        await manager.send_personal(
            websocket,
            WebSocketEvent.error("status_error", str(e)),
        )
