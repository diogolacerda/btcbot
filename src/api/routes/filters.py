"""Filters endpoints for managing trading filters."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_active_user, get_filter_registry
from src.api.schemas.filters import (
    BulkFilterResponse,
    FiltersResponse,
    FilterStatus,
    MACDTriggerRequest,
    MACDTriggerResponse,
    ToggleFilterRequest,
    ToggleFilterResponse,
)
from src.database.models.user import User
from src.filters.macd_filter import MACDFilter
from src.filters.registry import FilterRegistry
from src.utils.logger import main_logger

router = APIRouter(prefix="/api/v1/filters", tags=["Filters"])


@router.get("", response_model=FiltersResponse)
async def get_filters(
    current_user: Annotated[User, Depends(get_current_active_user)],
    registry: FilterRegistry = Depends(get_filter_registry),
):
    """Get status of all registered filters.

    Returns:
        FiltersResponse: Current state of all filters with summary information
    """
    try:
        states = registry.get_all_states()

        # Transform internal format to API schema format
        filters_dict = {}
        for name, filter_data in states["filters"].items():
            filters_dict[name] = FilterStatus(
                enabled=filter_data["enabled"],
                description=filter_data["description"],
                details=filter_data["details"],
            )

        return FiltersResponse(
            filters=filters_dict,
            all_enabled=states["all_enabled"],
            any_enabled=states["any_enabled"],
            total_count=states["total_count"],
            enabled_count=states["enabled_count"],
        )

    except Exception as e:
        main_logger.error(f"Error getting filter states: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/{filter_name}/toggle", response_model=ToggleFilterResponse)
async def toggle_filter(
    filter_name: str,
    request: ToggleFilterRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    registry: FilterRegistry = Depends(get_filter_registry),
):
    """Toggle a specific filter on or off.

    Args:
        filter_name: Name of the filter to toggle
        request: Request containing enabled state

    Returns:
        ToggleFilterResponse: Updated filter state

    Raises:
        HTTPException: If filter not found or toggle fails
    """
    try:
        # Check if filter exists
        filter_instance = registry.get_filter(filter_name)
        if not filter_instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Filter '{filter_name}' not found",
            )

        # Toggle filter
        if request.enabled:
            success = registry.enable_filter(filter_name)
        else:
            success = registry.disable_filter(filter_name)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update filter '{filter_name}'",
            )

        # Get updated state
        filter_instance = registry.get_filter(filter_name)
        state = filter_instance.get_state() if filter_instance else None

        action = "enabled" if request.enabled else "disabled"
        return ToggleFilterResponse(
            filter=filter_name,
            enabled=request.enabled,
            message=f"Filter {filter_name} {action}",
            details=(state.details or {}) if state else {},
        )

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Error toggling filter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/disable-all", response_model=BulkFilterResponse)
async def disable_all_filters(
    current_user: Annotated[User, Depends(get_current_active_user)],
    registry: FilterRegistry = Depends(get_filter_registry),
):
    """Disable all registered filters.

    This allows trading without any filter restrictions.

    Returns:
        BulkFilterResponse: Success message with list of affected filters
    """
    try:
        registry.disable_all()

        return BulkFilterResponse(
            message="All filters disabled",
            filters=registry.list_filters(),
        )

    except Exception as e:
        main_logger.error(f"Error disabling all filters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/enable-all", response_model=BulkFilterResponse)
async def enable_all_filters(
    current_user: Annotated[User, Depends(get_current_active_user)],
    registry: FilterRegistry = Depends(get_filter_registry),
):
    """Enable all registered filters.

    Restores all filters to their default enabled state.

    Returns:
        BulkFilterResponse: Success message with list of affected filters
    """
    try:
        registry.enable_all()

        return BulkFilterResponse(
            message="All filters enabled",
            filters=registry.list_filters(),
        )

    except Exception as e:
        main_logger.error(f"Error enabling all filters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/macd/activate", response_model=MACDTriggerResponse)
async def activate_macd(
    current_user: Annotated[User, Depends(get_current_active_user)],
    registry: FilterRegistry = Depends(get_filter_registry),
):
    """Manually activate the MACD cycle and trigger.

    Activates the MACD strategy and persists state to database.

    Returns:
        MACDTriggerResponse: Activation status and current MACD state

    Raises:
        HTTPException: If MACD filter not found or activation fails
    """
    try:
        # Get MACD filter
        macd_filter = registry.get_filter("macd")
        if not macd_filter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MACD filter not found",
            )

        # Check if filter is MACDFilter
        if not isinstance(macd_filter, MACDFilter):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MACD filter does not support manual activation",
            )

        # Activate cycle and trigger via manual_activate()
        success = macd_filter.manual_activate()

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to activate MACD (might be in INACTIVE state - market falling)",
            )

        # Get updated state
        state = macd_filter.get_state()

        return MACDTriggerResponse(
            message="MACD cycle and trigger activated successfully",
            activated=True,
            persisted=True,
            details=state.details or {},
        )

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Error activating MACD: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/macd/deactivate", response_model=MACDTriggerResponse)
async def deactivate_macd(
    current_user: Annotated[User, Depends(get_current_active_user)],
    registry: FilterRegistry = Depends(get_filter_registry),
):
    """Manually deactivate the MACD cycle and trigger.

    Deactivates the MACD strategy and persists state to database.

    Returns:
        MACDTriggerResponse: Deactivation status and current MACD state

    Raises:
        HTTPException: If MACD filter not found or deactivation fails
    """
    try:
        # Get MACD filter
        macd_filter = registry.get_filter("macd")
        if not macd_filter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MACD filter not found",
            )

        # Check if filter is MACDFilter
        if not isinstance(macd_filter, MACDFilter):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MACD filter does not support manual deactivation",
            )

        # Deactivate cycle and trigger via manual_deactivate()
        macd_filter.manual_deactivate()

        # Get updated state
        state = macd_filter.get_state()

        return MACDTriggerResponse(
            message="MACD cycle and trigger deactivated successfully",
            activated=False,
            persisted=True,
            details=state.details or {},
        )

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Error deactivating MACD: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/macd/trigger", response_model=MACDTriggerResponse)
async def macd_trigger(
    request: MACDTriggerRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    registry: FilterRegistry = Depends(get_filter_registry),
):
    """Control MACD trigger state.

    Unified endpoint to activate or deactivate the MACD cycle and trigger.

    Args:
        request: Request containing activation state

    Returns:
        MACDTriggerResponse: Updated trigger status and current MACD state

    Raises:
        HTTPException: If MACD filter not found or trigger control fails
    """
    try:
        # Get MACD filter
        macd_filter = registry.get_filter("macd")
        if not macd_filter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MACD filter not found",
            )

        # Check if filter is MACDFilter
        if not isinstance(macd_filter, MACDFilter):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MACD filter does not support trigger control",
            )

        # Activate or deactivate cycle and trigger
        if request.activated:
            success = macd_filter.manual_activate()
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to activate MACD (might be in INACTIVE state - market falling)",
                )
        else:
            macd_filter.manual_deactivate()

        # Get updated state
        state = macd_filter.get_state()

        action = "activated" if request.activated else "deactivated"
        return MACDTriggerResponse(
            message=f"MACD cycle and trigger {action} successfully",
            activated=request.activated,
            persisted=True,
            details=state.details or {},
        )

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Error controlling MACD trigger: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
