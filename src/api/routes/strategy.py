"""Strategy endpoints for managing trading strategies and MACD filter configuration."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_account_id, get_current_active_user
from src.api.schemas.strategy import MACDFilterConfigResponse, MACDFilterConfigUpdate
from src.database.engine import get_session
from src.database.models.user import User
from src.database.repositories.macd_filter_config_repository import MACDFilterConfigRepository
from src.database.repositories.strategy_repository import StrategyRepository

logger = logging.getLogger(__name__)

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

        logger.info(f"MACD filter config updated for strategy {strategy_id}: {list(kwargs.keys())}")

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
