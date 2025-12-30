"""Helper functions for database operations."""

import hashlib
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import BingXConfig, TradingConfig
from src.database.models.account import Account
from src.database.models.user import User
from src.utils.logger import main_logger


async def get_or_create_account(
    session: AsyncSession,
    bingx_config: BingXConfig,
    trading_config: TradingConfig,
    user_email: str = "default@btcbot.local",
) -> UUID:
    """
    Get or create an account for the current configuration.

    This helper creates a consistent account_id based on:
    - User email (default user for single-bot deployment)
    - Exchange name (bingx)
    - Trading mode (demo/live)
    - API key hash (for uniqueness)

    Args:
        session: Database session
        bingx_config: BingX configuration
        trading_config: Trading configuration
        user_email: User email (default for single-bot)

    Returns:
        Account UUID
    """
    try:
        # Get or create default user
        stmt = select(User).where(User.email == user_email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=user_email,
                name="Default Bot User",
                password_hash="not_used_for_bot",  # pragma: allowlist secret
            )
            session.add(user)
            await session.flush()
            main_logger.info(f"Created default user: {user_email}")

        # Hash API key for identification
        api_key_hash = hashlib.sha256(bingx_config.api_key.encode()).hexdigest()

        # Get or create account
        exchange = "bingx"
        is_demo = trading_config.is_demo
        account_name = f"BingX {'Demo' if is_demo else 'Live'} Account"

        account_stmt = select(Account).where(
            Account.user_id == user.id,
            Account.exchange == exchange,
            Account.name == account_name,
            Account.is_demo == is_demo,
        )
        account_result = await session.execute(account_stmt)
        account = account_result.scalar_one_or_none()

        if not account:
            account = Account(
                user_id=user.id,
                exchange=exchange,
                name=account_name,
                is_demo=is_demo,
                api_key_hash=api_key_hash,
            )
            session.add(account)
            await session.flush()
            main_logger.info(f"Created account: {account_name} (id={account.id})")
        else:
            # Update API key hash if changed
            if account.api_key_hash != api_key_hash:
                account.api_key_hash = api_key_hash
                main_logger.info("Updated account API key hash")

        await session.commit()
        return cast(UUID, account.id)

    except Exception as e:
        await session.rollback()
        main_logger.error(f"Error getting/creating account: {e}")
        raise
