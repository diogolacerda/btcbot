"""Configuration endpoints for trading and grid settings."""

import logging
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_active_user
from src.api.schemas.config import (
    GridConfigResponse,
    GridConfigUpdate,
    TradingConfigResponse,
    TradingConfigUpdate,
)
from src.database.engine import get_session
from src.database.models.user import User
from src.database.repositories.grid_config_repository import GridConfigRepository
from src.database.repositories.trading_config_repository import TradingConfigRepository

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/configs", tags=["configs"])


# Dependency functions
async def get_trading_config_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TradingConfigRepository:
    """Get trading config repository instance.

    Args:
        session: Database session.

    Returns:
        TradingConfigRepository instance.
    """
    return TradingConfigRepository(session)


async def get_grid_config_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GridConfigRepository:
    """Get grid config repository instance.

    Args:
        session: Database session.

    Returns:
        GridConfigRepository instance.
    """
    return GridConfigRepository(session)


async def get_account_id() -> UUID:
    """Get current account ID.

    TODO: Replace with actual authentication/multi-account logic.
    For now, uses a global account ID set at startup.

    Returns:
        Account UUID.

    Raises:
        HTTPException: If account ID is not set.
    """
    # Single-account mode (backward compatibility)
    # Account ID is set globally during startup in main.py
    # TODO: Extract from JWT token or user session for multi-account support
    from src.api.dependencies import get_global_account_id

    account_id = get_global_account_id()
    if account_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account ID not configured. Ensure bot is fully initialized.",
        )
    return account_id


# Trading Config Endpoints


@router.get("/trading", response_model=TradingConfigResponse)
async def get_trading_config(
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[TradingConfigRepository, Depends(get_trading_config_repo)],
) -> TradingConfigResponse:
    """Get current trading configuration.

    Args:
        account_id: Current account UUID.
        repo: Trading config repository.

    Returns:
        TradingConfigResponse with current configuration.

    Raises:
        HTTPException: If config not found (404) or database error (500).
    """
    logger.debug(f"GET /api/v1/configs/trading for account {account_id}")

    try:
        config = await repo.get_by_account(account_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No trading configuration found for this account",
            )

        return TradingConfigResponse(
            id=str(config.id),
            account_id=str(config.account_id),
            symbol=config.symbol,
            leverage=config.leverage,
            order_size_usdt=config.order_size_usdt,
            margin_mode=config.margin_mode,
            take_profit_percent=config.take_profit_percent,
            tp_dynamic_enabled=config.tp_dynamic_enabled,
            tp_base_percent=config.tp_base_percent,
            tp_min_percent=config.tp_min_percent,
            tp_max_percent=config.tp_max_percent,
            tp_safety_margin=config.tp_safety_margin,
            tp_check_interval_min=config.tp_check_interval_min,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trading config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.patch("/trading", response_model=TradingConfigResponse)
async def update_trading_config(
    update_data: TradingConfigUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[TradingConfigRepository, Depends(get_trading_config_repo)],
) -> TradingConfigResponse:
    """Update trading configuration (partial update).

    Only provided fields will be updated. Validates TP constraint: min <= base <= max.

    Args:
        update_data: Fields to update.
        account_id: Current account UUID.
        repo: Trading config repository.

    Returns:
        TradingConfigResponse with updated configuration.

    Raises:
        HTTPException: If validation fails (400) or database error (500).
    """
    logger.debug(f"PATCH /api/v1/configs/trading for account {account_id}")

    try:
        # Build kwargs with only provided fields
        kwargs: dict[str, str | int | Decimal | bool] = {}

        if update_data.symbol is not None:
            kwargs["symbol"] = update_data.symbol
        if update_data.leverage is not None:
            kwargs["leverage"] = update_data.leverage
        if update_data.order_size_usdt is not None:
            kwargs["order_size_usdt"] = update_data.order_size_usdt
        if update_data.margin_mode is not None:
            kwargs["margin_mode"] = update_data.margin_mode
        if update_data.take_profit_percent is not None:
            kwargs["take_profit_percent"] = update_data.take_profit_percent
        if update_data.tp_dynamic_enabled is not None:
            kwargs["tp_dynamic_enabled"] = update_data.tp_dynamic_enabled
        if update_data.tp_base_percent is not None:
            kwargs["tp_base_percent"] = update_data.tp_base_percent
        if update_data.tp_min_percent is not None:
            kwargs["tp_min_percent"] = update_data.tp_min_percent
        if update_data.tp_max_percent is not None:
            kwargs["tp_max_percent"] = update_data.tp_max_percent
        if update_data.tp_safety_margin is not None:
            kwargs["tp_safety_margin"] = update_data.tp_safety_margin
        if update_data.tp_check_interval_min is not None:
            kwargs["tp_check_interval_min"] = update_data.tp_check_interval_min

        if not kwargs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update",
            )

        # Validate TP constraints if any TP percent fields are being updated
        tp_min_val: Decimal | None = kwargs.get("tp_min_percent")  # type: ignore[assignment]
        tp_base_val: Decimal | None = kwargs.get("tp_base_percent")  # type: ignore[assignment]
        tp_max_val: Decimal | None = kwargs.get("tp_max_percent")  # type: ignore[assignment]

        if tp_min_val is not None or tp_base_val is not None or tp_max_val is not None:
            # Get current config to fill in missing values
            current_config = await repo.get_by_account(account_id)
            if current_config:
                final_min: Decimal = (
                    tp_min_val if tp_min_val is not None else current_config.tp_min_percent
                )
                final_base: Decimal = (
                    tp_base_val if tp_base_val is not None else current_config.tp_base_percent
                )
                final_max: Decimal = (
                    tp_max_val if tp_max_val is not None else current_config.tp_max_percent
                )

                # Validate: min <= base <= max
                if not (final_min <= final_base <= final_max):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="TP percentages must satisfy: min <= base <= max",
                    )

        # Update config
        config = await repo.create_or_update(
            account_id,
            **kwargs,  # type: ignore[arg-type]
        )

        logger.info(f"Trading config updated (partial): {list(kwargs.keys())}")

        return TradingConfigResponse(
            id=str(config.id),
            account_id=str(config.account_id),
            symbol=config.symbol,
            leverage=config.leverage,
            order_size_usdt=config.order_size_usdt,
            margin_mode=config.margin_mode,
            take_profit_percent=config.take_profit_percent,
            tp_dynamic_enabled=config.tp_dynamic_enabled,
            tp_base_percent=config.tp_base_percent,
            tp_min_percent=config.tp_min_percent,
            tp_max_percent=config.tp_max_percent,
            tp_safety_margin=config.tp_safety_margin,
            tp_check_interval_min=config.tp_check_interval_min,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating trading config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


# Grid Config Endpoints


@router.get("/grid", response_model=GridConfigResponse)
async def get_grid_config(
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[GridConfigRepository, Depends(get_grid_config_repo)],
) -> GridConfigResponse:
    """Get current grid configuration.

    Args:
        account_id: Current account UUID.
        repo: Grid config repository.

    Returns:
        GridConfigResponse with current configuration.

    Raises:
        HTTPException: If database error (500).
    """
    logger.debug(f"GET /api/v1/configs/grid for account {account_id}")

    try:
        # get_or_create will create with defaults if not exists
        config = await repo.get_or_create(account_id)

        return GridConfigResponse(
            id=str(config.id),
            account_id=str(config.account_id),
            spacing_type=config.spacing_type,
            spacing_value=config.spacing_value,
            range_percent=config.range_percent,
            max_total_orders=config.max_total_orders,
            anchor_mode=config.anchor_mode,
            anchor_value=config.anchor_value,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    except Exception as e:
        logger.error(f"Error getting grid config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.patch("/grid", response_model=GridConfigResponse)
async def update_grid_config(
    update_data: GridConfigUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    account_id: Annotated[UUID, Depends(get_account_id)],
    repo: Annotated[GridConfigRepository, Depends(get_grid_config_repo)],
) -> GridConfigResponse:
    """Update grid configuration (partial update).

    Only provided fields will be updated.

    Args:
        update_data: Fields to update.
        account_id: Current account UUID.
        repo: Grid config repository.

    Returns:
        GridConfigResponse with updated configuration.

    Raises:
        HTTPException: If validation fails (400) or database error (500).
    """
    logger.debug(f"PATCH /api/v1/configs/grid for account {account_id}")

    try:
        # Build kwargs with only provided fields
        kwargs: dict[str, str | int | Decimal] = {}

        if update_data.spacing_type is not None:
            kwargs["spacing_type"] = update_data.spacing_type
        if update_data.spacing_value is not None:
            kwargs["spacing_value"] = update_data.spacing_value
        if update_data.range_percent is not None:
            kwargs["range_percent"] = update_data.range_percent
        if update_data.max_total_orders is not None:
            kwargs["max_total_orders"] = update_data.max_total_orders
        if update_data.anchor_mode is not None:
            kwargs["anchor_mode"] = update_data.anchor_mode
        if update_data.anchor_value is not None:
            kwargs["anchor_value"] = update_data.anchor_value

        if not kwargs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update",
            )

        # Update config
        config = await repo.save_config(
            account_id,
            **kwargs,  # type: ignore[arg-type]
        )

        logger.info(f"Grid config updated (partial): {list(kwargs.keys())}")

        return GridConfigResponse(
            id=str(config.id),
            account_id=str(config.account_id),
            spacing_type=config.spacing_type,
            spacing_value=config.spacing_value,
            range_percent=config.range_percent,
            max_total_orders=config.max_total_orders,
            anchor_mode=config.anchor_mode,
            anchor_value=config.anchor_value,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating grid config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
