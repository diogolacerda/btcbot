"""Activity events API endpoints for trading timeline."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import (
    get_activity_event_repository,
    get_global_account_id,
)
from src.api.schemas.activity import (
    ActivityEventSchema,
    ActivityEventsListResponse,
    EventTypeEnum,
    TimePeriodEnum,
)
from src.database.repositories.activity_event_repository import ActivityEventRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/activity", tags=["Activity"])


def _calculate_period_range(period: TimePeriodEnum) -> tuple[datetime, datetime]:
    """Calculate start and end datetime for a predefined period.

    Args:
        period: The time period enum value.

    Returns:
        Tuple of (start_datetime, end_datetime).
    """
    now = datetime.now(UTC)
    end = now

    if period == TimePeriodEnum.TODAY:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == TimePeriodEnum.SEVEN_DAYS:
        start = now - timedelta(days=7)
    elif period == TimePeriodEnum.THIRTY_DAYS:
        start = now - timedelta(days=30)
    else:
        # For custom, return a wide range (will be overridden)
        start = now - timedelta(days=365)

    return start, end


@router.get("", response_model=ActivityEventsListResponse)
async def get_activity_events(
    period: Annotated[
        TimePeriodEnum | None,
        Query(description="Predefined time period filter (today, 7days, 30days, custom)"),
    ] = None,
    start_date: Annotated[
        datetime | None,
        Query(
            description="Custom start date (ISO 8601 format). Required when period=custom.",
            alias="startDate",
        ),
    ] = None,
    end_date: Annotated[
        datetime | None,
        Query(
            description="Custom end date (ISO 8601 format). Required when period=custom.",
            alias="endDate",
        ),
    ] = None,
    event_type: Annotated[
        EventTypeEnum | None,
        Query(description="Filter by event type"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum number of events to return"),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of events to skip"),
    ] = 0,
    repository: ActivityEventRepository = Depends(get_activity_event_repository),
) -> ActivityEventsListResponse:
    """Get activity events with filtering and pagination.

    Returns activity events for the trading timeline dashboard, supporting:
    - Predefined time periods (today, 7days, 30days)
    - Custom date ranges (startDate + endDate)
    - Event type filtering
    - Pagination (limit + offset)

    Events are always ordered by timestamp DESC (newest first).

    Args:
        period: Predefined time period filter.
        start_date: Custom start date (required when period=custom).
        end_date: Custom end date (required when period=custom).
        event_type: Optional event type filter.
        limit: Maximum events to return (1-1000).
        offset: Number of events to skip.
        repository: ActivityEventRepository instance (injected).

    Returns:
        ActivityEventsListResponse: List of events with pagination info.

    Raises:
        HTTPException: If account not configured or invalid parameters.
    """
    account_id = get_global_account_id()

    if account_id is None:
        raise HTTPException(
            status_code=503,
            detail="Account not configured. Bot may not be fully initialized.",
        )

    try:
        # Determine date range
        if period == TimePeriodEnum.CUSTOM:
            if not start_date or not end_date:
                raise HTTPException(
                    status_code=400,
                    detail="start_date and end_date are required when period=custom",
                )
            start = start_date
            end = end_date
        elif period:
            start, end = _calculate_period_range(period)
        else:
            # Default: last 7 days if no period specified
            start, end = _calculate_period_range(TimePeriodEnum.SEVEN_DAYS)

        # Fetch events based on filters
        if event_type:
            # Filter by event type (uses get_events_by_type which doesn't support period)
            # We need to use get_events_by_period and filter locally
            all_events = await repository.get_events_by_period(
                account_id=account_id,
                start=start,
                end=end,
                limit=limit + offset + 100,  # Fetch more to account for filtering
            )
            filtered_events = [e for e in all_events if e.event_type == event_type.value]
            total = len(filtered_events)
            events = filtered_events[offset : offset + limit]
        else:
            # Get all events in period
            events = await repository.get_events_by_period(
                account_id=account_id,
                start=start,
                end=end,
                limit=limit + offset,
            )
            # For total count, we need a separate query
            # The repository doesn't have count_by_period, so we estimate
            # In production, you might want to add a proper count method
            all_in_period = await repository.get_events_by_period(
                account_id=account_id,
                start=start,
                end=end,
                limit=10000,  # Large limit to get approximate total
            )
            total = len(all_in_period)
            events = events[offset:][:limit] if offset > 0 else events[:limit]

        # Convert to schemas
        event_schemas = [
            ActivityEventSchema(
                id=event.id,
                event_type=EventTypeEnum(event.event_type),
                description=event.description,
                event_data=event.event_data,
                timestamp=event.timestamp,
            )
            for event in events
        ]

        return ActivityEventsListResponse(
            events=event_schemas,
            total=total,
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching activity events: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch activity events: {str(e)}",
        ) from e
