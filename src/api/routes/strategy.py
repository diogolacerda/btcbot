"""Strategy API endpoints for CRUD operations and filter configuration."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_account_id, get_current_active_user
from src.api.schemas.strategy import (
    EMAFilterConfigResponse,
    EMAFilterConfigUpdate,
    MACDFilterConfigResponse,
    MACDFilterConfigUpdate,
    StrategyActivateResponse,
    StrategyCreate,
    StrategyResponse,
    StrategyUpdate,
)
from src.database.engine import get_session
from src.database.models.user import User
from src.database.repositories.ema_filter_config_repository import EMAFilterConfigRepository
from src.database.repositories.macd_filter_config_repository import MACDFilterConfigRepository
from src.database.repositories.strategy_repository import StrategyRepository
from src.utils.logger import api_logger as logger

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])


async def get_strategy_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StrategyRepository:
    """Get strategy repository instance.

    Args:
        session: Database session.

    Returns:
        StrategyRepository instance.
    """
    return StrategyRepository(session)


async def get_macd_filter_config_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MACDFilterConfigRepository:
    """Get MACD filter config repository instance.

    Args:
        session: Database session.

    Returns:
        MACDFilterConfigRepository instance.
    """
    return MACDFilterConfigRepository(session)


async def get_ema_filter_config_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EMAFilterConfigRepository:
    """Get EMA filter config repository instance.

    Args:
        session: Database session.

    Returns:
        EMAFilterConfigRepository instance.
    """
    return EMAFilterConfigRepository(session)


def _strategy_to_response(strategy) -> StrategyResponse:
    """Convert Strategy model to StrategyResponse schema.

    Args:
        strategy: Strategy model instance.

    Returns:
        StrategyResponse schema.
    """
    return StrategyResponse(
        id=str(strategy.id),
        account_id=str(strategy.account_id),
        name=strategy.name,
        is_active=strategy.is_active,
        symbol=strategy.symbol,
        leverage=strategy.leverage,
        order_size_usdt=strategy.order_size_usdt,
        margin_mode=strategy.margin_mode,
        take_profit_percent=strategy.take_profit_percent,
        tp_dynamic_enabled=strategy.tp_dynamic_enabled,
        tp_dynamic_base=strategy.tp_dynamic_base,
        tp_dynamic_min=strategy.tp_dynamic_min,
        tp_dynamic_max=strategy.tp_dynamic_max,
        tp_dynamic_safety_margin=strategy.tp_dynamic_safety_margin,
        tp_dynamic_check_interval=strategy.tp_dynamic_check_interval,
        spacing_type=strategy.spacing_type,
        spacing_value=strategy.spacing_value,
        range_percent=strategy.range_percent,
        max_total_orders=strategy.max_total_orders,
        created_at=strategy.created_at,
        updated_at=strategy.updated_at,
    )


@router.get("", response_model=list[StrategyResponse])
async def list_strategies(
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
) -> list[StrategyResponse]:
    """List all strategies for the current account.

    Args:
        current_user: Authenticated user.
        account_id: Current account UUID.
        repo: Strategy repository.

    Returns:
        List of StrategyResponse for the account.

    Raises:
        HTTPException: If database error occurs (500).
    """
    logger.debug(f"GET /api/v1/strategies for account {account_id}")

    try:
        strategies = await repo.get_by_account(account_id)
        return [_strategy_to_response(s) for s in strategies]
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/active", response_model=StrategyResponse | None)
async def get_active_strategy(
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
) -> StrategyResponse | None:
    """Get the active strategy for the current account.

    Args:
        current_user: Authenticated user.
        account_id: Current account UUID.
        repo: Strategy repository.

    Returns:
        StrategyResponse if active strategy exists, None otherwise.

    Raises:
        HTTPException: If database error occurs (500).
    """
    logger.debug(f"GET /api/v1/strategies/active for account {account_id}")

    try:
        strategy = await repo.get_active_by_account(account_id)
        if not strategy:
            return None
        return _strategy_to_response(strategy)
    except Exception as e:
        logger.error(f"Error getting active strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
) -> StrategyResponse:
    """Get a specific strategy by ID.

    Args:
        strategy_id: UUID of the strategy to retrieve.
        current_user: Authenticated user.
        account_id: Current account UUID.
        repo: Strategy repository.

    Returns:
        StrategyResponse with strategy details.

    Raises:
        HTTPException: If strategy not found (404) or not owned by account (403).
    """
    logger.debug(f"GET /api/v1/strategies/{strategy_id}")

    try:
        strategy = await repo.get_by_id(strategy_id)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}",
            )

        # Verify ownership
        if strategy.account_id != account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Strategy does not belong to this account",
            )

        return _strategy_to_response(strategy)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    data: StrategyCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
) -> StrategyResponse:
    """Create a new strategy for the current account.

    Args:
        data: Strategy creation data.
        current_user: Authenticated user.
        account_id: Current account UUID.
        repo: Strategy repository.

    Returns:
        StrategyResponse with created strategy details.

    Raises:
        HTTPException: If validation fails (400) or database error (500).
    """
    logger.debug(f"POST /api/v1/strategies for account {account_id}")

    try:
        # Validate TP constraints: min <= base <= max
        if not (data.tp_dynamic_min <= data.tp_dynamic_base <= data.tp_dynamic_max):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dynamic TP percentages must satisfy: min <= base <= max",
            )

        # Build strategy data
        strategy_data = {
            "account_id": account_id,
            "name": data.name,
            "is_active": data.is_active,
            "symbol": data.symbol,
            "leverage": data.leverage,
            "order_size_usdt": data.order_size_usdt,
            "margin_mode": data.margin_mode,
            "take_profit_percent": data.take_profit_percent,
            "tp_dynamic_enabled": data.tp_dynamic_enabled,
            "tp_dynamic_base": data.tp_dynamic_base,
            "tp_dynamic_min": data.tp_dynamic_min,
            "tp_dynamic_max": data.tp_dynamic_max,
            "tp_dynamic_safety_margin": data.tp_dynamic_safety_margin,
            "tp_dynamic_check_interval": data.tp_dynamic_check_interval,
            "spacing_type": data.spacing_type,
            "spacing_value": data.spacing_value,
            "range_percent": data.range_percent,
            "max_total_orders": data.max_total_orders,
        }

        # If creating as active, deactivate others first
        if data.is_active:
            await repo.deactivate_all(account_id)

        strategy = await repo.create_strategy(strategy_data)
        logger.info(f"Strategy created: {strategy.id} ({strategy.name})")

        return _strategy_to_response(strategy)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.patch("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: UUID,
    data: StrategyUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
) -> StrategyResponse:
    """Update a strategy (partial update).

    Only provided fields will be updated.

    Args:
        strategy_id: UUID of the strategy to update.
        data: Fields to update.
        current_user: Authenticated user.
        account_id: Current account UUID.
        repo: Strategy repository.

    Returns:
        StrategyResponse with updated strategy details.

    Raises:
        HTTPException: If strategy not found (404), validation fails (400),
            or not owned by account (403).
    """
    logger.debug(f"PATCH /api/v1/strategies/{strategy_id}")

    try:
        # Verify strategy exists and belongs to account
        strategy = await repo.get_by_id(strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}",
            )

        if strategy.account_id != account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Strategy does not belong to this account",
            )

        # Build update dict with only provided fields
        updates: dict = {}
        for field in [
            "name",
            "is_active",
            "symbol",
            "leverage",
            "order_size_usdt",
            "margin_mode",
            "take_profit_percent",
            "tp_dynamic_enabled",
            "tp_dynamic_base",
            "tp_dynamic_min",
            "tp_dynamic_max",
            "tp_dynamic_safety_margin",
            "tp_dynamic_check_interval",
            "spacing_type",
            "spacing_value",
            "range_percent",
            "max_total_orders",
        ]:
            value = getattr(data, field)
            if value is not None:
                updates[field] = value

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update",
            )

        # Validate TP constraints if any TP fields are being updated
        tp_min = updates.get("tp_dynamic_min", strategy.tp_dynamic_min)
        tp_base = updates.get("tp_dynamic_base", strategy.tp_dynamic_base)
        tp_max = updates.get("tp_dynamic_max", strategy.tp_dynamic_max)

        if not (tp_min <= tp_base <= tp_max):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dynamic TP percentages must satisfy: min <= base <= max",
            )

        # Handle activation (deactivate others first)
        if updates.get("is_active") is True and not strategy.is_active:
            await repo.deactivate_all(account_id)

        updated_strategy = await repo.update_strategy(strategy_id, updates)
        logger.info(f"Strategy updated: {strategy_id} - fields: {list(updates.keys())}")

        return _strategy_to_response(updated_strategy)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error updating strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
) -> None:
    """Delete a strategy.

    Args:
        strategy_id: UUID of the strategy to delete.
        current_user: Authenticated user.
        account_id: Current account UUID.
        repo: Strategy repository.

    Raises:
        HTTPException: If strategy not found (404) or not owned by account (403).
    """
    logger.debug(f"DELETE /api/v1/strategies/{strategy_id}")

    try:
        # Verify strategy exists and belongs to account
        strategy = await repo.get_by_id(strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}",
            )

        if strategy.account_id != account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Strategy does not belong to this account",
            )

        await repo.delete(strategy_id)
        logger.info(f"Strategy deleted: {strategy_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/{strategy_id}/activate", response_model=StrategyActivateResponse)
async def activate_strategy(
    strategy_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
) -> StrategyActivateResponse:
    """Activate a strategy (deactivates all others for the account).

    Only one strategy can be active per account at a time.

    Args:
        strategy_id: UUID of the strategy to activate.
        current_user: Authenticated user.
        account_id: Current account UUID.
        repo: Strategy repository.

    Returns:
        StrategyActivateResponse with activation confirmation.

    Raises:
        HTTPException: If strategy not found (404) or not owned by account (403).
    """
    logger.debug(f"POST /api/v1/strategies/{strategy_id}/activate")

    try:
        # Verify strategy exists and belongs to account
        strategy = await repo.get_by_id(strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}",
            )

        if strategy.account_id != account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Strategy does not belong to this account",
            )

        activated = await repo.activate_strategy(strategy_id)
        logger.info(f"Strategy activated: {strategy_id} ({activated.name})")

        return StrategyActivateResponse(
            message=f"Strategy '{activated.name}' is now active",
            strategy=_strategy_to_response(activated),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error activating strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


# MACD Filter Config Endpoints


@router.get("/{strategy_id}/macd-filter", response_model=MACDFilterConfigResponse)
async def get_macd_filter_config(
    strategy_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    strategy_repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
    macd_repo: Annotated[MACDFilterConfigRepository, Depends(get_macd_filter_config_repo)],
) -> MACDFilterConfigResponse:
    """Get MACD filter configuration for a specific strategy.

    Args:
        strategy_id: UUID of strategy.
        account_id: Current account UUID.
        strategy_repo: Strategy repository.
        macd_repo: MACD filter config repository.

    Returns:
        MACDFilterConfigResponse with current configuration.

    Raises:
        HTTPException: If strategy not found (404), doesn't belong to account (403),
            or database error (500).
    """
    logger.debug(f"GET /api/v1/strategies/{strategy_id}/macd-filter for account {account_id}")

    try:
        strategy = await strategy_repo.get_by_id(strategy_id)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )

        if strategy.account_id != account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Strategy does not belong to this account",
            )

        config = await macd_repo.get_by_strategy(strategy_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MACD filter configuration not found for this strategy",
            )

        return MACDFilterConfigResponse(
            id=str(config.id),
            strategy_id=str(config.strategy_id),
            enabled=config.enabled,
            fast_period=config.fast_period,
            slow_period=config.slow_period,
            signal_period=config.signal_period,
            timeframe=config.timeframe,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MACD filter config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.patch("/{strategy_id}/macd-filter", response_model=MACDFilterConfigResponse)
async def update_macd_filter_config(
    strategy_id: UUID,
    update_data: MACDFilterConfigUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    strategy_repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
    macd_repo: Annotated[MACDFilterConfigRepository, Depends(get_macd_filter_config_repo)],
) -> MACDFilterConfigResponse:
    """Update MACD filter configuration for a specific strategy (partial update).

    Only provided fields will be updated. Validates that fast < slow if both provided.

    Args:
        strategy_id: UUID of strategy.
        update_data: Fields to update.
        account_id: Current account UUID.
        strategy_repo: Strategy repository.
        macd_repo: MACD filter config repository.

    Returns:
        MACDFilterConfigResponse with updated configuration.

    Raises:
        HTTPException: If strategy not found (404), doesn't belong to account (403),
            validation fails (400), or database error (500).
    """
    logger.debug(f"PATCH /api/v1/strategies/{strategy_id}/macd-filter for account {account_id}")

    try:
        strategy = await strategy_repo.get_by_id(strategy_id)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )

        if strategy.account_id != account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Strategy does not belong to this account",
            )

        kwargs: dict[str, bool | int | str] = {}

        if update_data.enabled is not None:
            kwargs["enabled"] = update_data.enabled
        if update_data.fast_period is not None:
            kwargs["fast_period"] = update_data.fast_period
        if update_data.slow_period is not None:
            kwargs["slow_period"] = update_data.slow_period
        if update_data.signal_period is not None:
            kwargs["signal_period"] = update_data.signal_period
        if update_data.timeframe is not None:
            kwargs["timeframe"] = update_data.timeframe

        if not kwargs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update",
            )

        config = await macd_repo.create_or_update(
            strategy_id,
            enabled=update_data.enabled,
            fast_period=update_data.fast_period,
            slow_period=update_data.slow_period,
            signal_period=update_data.signal_period,
            timeframe=update_data.timeframe,
        )

        return MACDFilterConfigResponse(
            id=str(config.id),
            strategy_id=str(config.strategy_id),
            enabled=config.enabled,
            fast_period=config.fast_period,
            slow_period=config.slow_period,
            signal_period=config.signal_period,
            timeframe=config.timeframe,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating MACD filter config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


# EMA Filter Config Endpoints


@router.get("/{strategy_id}/ema-filter", response_model=EMAFilterConfigResponse)
async def get_ema_filter_config(
    strategy_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    strategy_repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
    ema_repo: Annotated[EMAFilterConfigRepository, Depends(get_ema_filter_config_repo)],
) -> EMAFilterConfigResponse:
    """Get EMA filter configuration for a specific strategy.

    The EMA filter is part of the Impulse System (Alexander Elder).
    It uses EMA direction to determine if trading should be allowed.

    Args:
        strategy_id: UUID of strategy.
        current_user: Authenticated user.
        account_id: Current account UUID.
        strategy_repo: Strategy repository.
        ema_repo: EMA filter config repository.

    Returns:
        EMAFilterConfigResponse with current configuration.

    Raises:
        HTTPException: If strategy not found (404), doesn't belong to account (403),
            or database error (500).
    """
    logger.debug(f"GET /api/v1/strategies/{strategy_id}/ema-filter for account {account_id}")

    try:
        strategy = await strategy_repo.get_by_id(strategy_id)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )

        if strategy.account_id != account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Strategy does not belong to this account",
            )

        config = await ema_repo.get_by_strategy(strategy_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="EMA filter configuration not found for this strategy",
            )

        return EMAFilterConfigResponse(
            id=str(config.id),
            strategy_id=str(config.strategy_id),
            enabled=config.enabled,
            period=config.period,
            timeframe=config.timeframe,
            allow_on_rising=config.allow_on_rising,
            allow_on_falling=config.allow_on_falling,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting EMA filter config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.patch("/{strategy_id}/ema-filter", response_model=EMAFilterConfigResponse)
async def update_ema_filter_config(
    strategy_id: UUID,
    update_data: EMAFilterConfigUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    strategy_repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
    ema_repo: Annotated[EMAFilterConfigRepository, Depends(get_ema_filter_config_repo)],
) -> EMAFilterConfigResponse:
    """Update EMA filter configuration for a specific strategy (partial update).

    Only provided fields will be updated. If no configuration exists, one will be created.

    Args:
        strategy_id: UUID of strategy.
        update_data: Fields to update.
        current_user: Authenticated user.
        account_id: Current account UUID.
        strategy_repo: Strategy repository.
        ema_repo: EMA filter config repository.

    Returns:
        EMAFilterConfigResponse with updated configuration.

    Raises:
        HTTPException: If strategy not found (404), doesn't belong to account (403),
            validation fails (400), or database error (500).
    """
    logger.debug(f"PATCH /api/v1/strategies/{strategy_id}/ema-filter for account {account_id}")

    try:
        strategy = await strategy_repo.get_by_id(strategy_id)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )

        if strategy.account_id != account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Strategy does not belong to this account",
            )

        # Check if at least one field is provided
        has_update = any(
            getattr(update_data, field) is not None
            for field in ["enabled", "period", "timeframe", "allow_on_rising", "allow_on_falling"]
        )

        if not has_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update",
            )

        config = await ema_repo.create_or_update(
            strategy_id,
            enabled=update_data.enabled,
            period=update_data.period,
            timeframe=update_data.timeframe,
            allow_on_rising=update_data.allow_on_rising,
            allow_on_falling=update_data.allow_on_falling,
        )

        return EMAFilterConfigResponse(
            id=str(config.id),
            strategy_id=str(config.strategy_id),
            enabled=config.enabled,
            period=config.period,
            timeframe=config.timeframe,
            allow_on_rising=config.allow_on_rising,
            allow_on_falling=config.allow_on_falling,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating EMA filter config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
