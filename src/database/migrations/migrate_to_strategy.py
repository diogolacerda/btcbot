"""Data migration script: TradingConfig + GridConfig -> Strategy.

Migrates existing TradingConfig and GridConfig data to the new unified Strategy model.
Each account's configs are combined into a single Strategy with an associated MACDFilterConfig.

Usage:
    # Dry run (default) - shows what would be migrated
    python -m src.database.migrations.migrate_to_strategy

    # Execute migration
    python -m src.database.migrations.migrate_to_strategy --execute

    # Verbose output
    python -m src.database.migrations.migrate_to_strategy --execute --verbose
"""

import argparse
import logging
import sys
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.database.engine import get_engine, get_session_maker
from src.database.models.account import Account
from src.database.models.grid_config import GridConfig
from src.database.models.macd_filter_config import MACDFilterConfig
from src.database.models.strategy import Strategy
from src.database.models.trading_config import TradingConfig

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of a single account migration."""

    account_id: UUID
    account_name: str
    status: str  # 'migrated', 'skipped', 'error'
    strategy_id: UUID | None = None
    error_message: str | None = None


@dataclass
class MigrationSummary:
    """Summary of the migration run."""

    total_accounts: int
    migrated: int
    skipped: int
    errors: int
    results: list[MigrationResult]


def map_margin_mode(old_value: str) -> str:
    """Map margin mode from old format to new format.

    Args:
        old_value: Old margin mode (e.g., 'CROSSED', 'ISOLATED')

    Returns:
        New format margin mode (lowercase)
    """
    return old_value.lower()


def create_strategy_from_configs(
    account: Account,
    trading_config: TradingConfig,
    grid_config: GridConfig,
) -> Strategy:
    """Create a Strategy instance from TradingConfig and GridConfig.

    Args:
        account: The account to create the strategy for
        trading_config: The existing trading configuration
        grid_config: The existing grid configuration

    Returns:
        New Strategy instance (not yet added to session)
    """
    return Strategy(
        account_id=account.id,
        name=f"Migrated Strategy - {account.name}",
        is_active=True,  # Assume active if configs exist
        symbol=trading_config.symbol,
        # Risk parameters from TradingConfig
        leverage=trading_config.leverage,
        order_size_usdt=trading_config.order_size_usdt,
        margin_mode=map_margin_mode(trading_config.margin_mode),
        # Take profit parameters from TradingConfig
        take_profit_percent=trading_config.take_profit_percent,
        tp_dynamic_enabled=trading_config.tp_dynamic_enabled,
        tp_dynamic_base=trading_config.tp_base_percent,
        tp_dynamic_min=trading_config.tp_min_percent,
        tp_dynamic_max=trading_config.tp_max_percent,
        tp_dynamic_safety_margin=trading_config.tp_safety_margin,
        tp_dynamic_check_interval=trading_config.tp_check_interval_min,
        # Grid parameters from GridConfig
        spacing_type=grid_config.spacing_type,
        spacing_value=grid_config.spacing_value,
        range_percent=grid_config.range_percent,
        max_total_orders=grid_config.max_total_orders,
    )


def create_default_macd_config(strategy: Strategy) -> MACDFilterConfig:
    """Create a default MACDFilterConfig for a strategy.

    Args:
        strategy: The strategy to attach the config to

    Returns:
        New MACDFilterConfig instance
    """
    return MACDFilterConfig(
        strategy_id=strategy.id,
        enabled=True,
        fast_period=12,
        slow_period=26,
        signal_period=9,
        timeframe="1h",
    )


def has_existing_strategy(session: Session, account_id: UUID) -> bool:
    """Check if account already has a Strategy.

    Args:
        session: Database session
        account_id: Account UUID to check

    Returns:
        True if strategy exists, False otherwise
    """
    stmt = select(Strategy).where(Strategy.account_id == account_id).limit(1)
    result = session.scalar(stmt)
    return result is not None


def migrate_account(
    session: Session,
    account: Account,
    trading_config: TradingConfig | None,
    grid_config: GridConfig | None,
    dry_run: bool = True,
) -> MigrationResult:
    """Migrate a single account's configs to Strategy.

    Args:
        session: Database session
        account: Account to migrate
        trading_config: Account's trading config (may be None)
        grid_config: Account's grid config (may be None)
        dry_run: If True, don't actually create records

    Returns:
        MigrationResult with status and details
    """
    # Check if already migrated (idempotent)
    if has_existing_strategy(session, account.id):
        return MigrationResult(
            account_id=account.id,
            account_name=account.name,
            status="skipped",
            error_message="Strategy already exists for this account",
        )

    # Need both configs to migrate
    if trading_config is None or grid_config is None:
        missing = []
        if trading_config is None:
            missing.append("TradingConfig")
        if grid_config is None:
            missing.append("GridConfig")
        return MigrationResult(
            account_id=account.id,
            account_name=account.name,
            status="skipped",
            error_message=f"Missing: {', '.join(missing)}",
        )

    if dry_run:
        # In dry run, just report what would be done
        return MigrationResult(
            account_id=account.id,
            account_name=account.name,
            status="migrated",
            strategy_id=None,  # No actual ID in dry run
        )

    # Create Strategy
    strategy = create_strategy_from_configs(account, trading_config, grid_config)
    session.add(strategy)
    session.flush()  # Get the strategy ID

    # Create default MACDFilterConfig
    macd_config = create_default_macd_config(strategy)
    session.add(macd_config)

    return MigrationResult(
        account_id=account.id,
        account_name=account.name,
        status="migrated",
        strategy_id=strategy.id,
    )


def run_migration(dry_run: bool = True, verbose: bool = False) -> MigrationSummary:
    """Run the migration for all accounts.

    Args:
        dry_run: If True, don't commit changes
        verbose: If True, print detailed progress

    Returns:
        MigrationSummary with results
    """
    engine = get_engine()
    session_maker = get_session_maker(engine)
    results: list[MigrationResult] = []
    migrated = 0
    skipped = 0
    errors = 0

    with session_maker() as session:
        # Load all accounts with their configs (eager load relationships)
        stmt = select(Account).options(
            selectinload(Account.trading_config),
            selectinload(Account.grid_config),
        )
        result = session.execute(stmt)
        accounts = list(result.scalars())
        total_accounts = len(accounts)

        if verbose:
            logger.info(f"Found {total_accounts} accounts to process")

        for account in accounts:
            try:
                # Get related configs (already loaded)
                trading_config = account.trading_config
                grid_config = account.grid_config

                migration_result = migrate_account(
                    session=session,
                    account=account,
                    trading_config=trading_config,
                    grid_config=grid_config,
                    dry_run=dry_run,
                )

                results.append(migration_result)

                if migration_result.status == "migrated":
                    migrated += 1
                    if verbose:
                        logger.info(f"[MIGRATED] {account.name} (id={account.id})")
                elif migration_result.status == "skipped":
                    skipped += 1
                    if verbose:
                        logger.info(f"[SKIPPED] {account.name}: {migration_result.error_message}")

            except Exception as e:
                errors += 1
                results.append(
                    MigrationResult(
                        account_id=account.id,
                        account_name=account.name,
                        status="error",
                        error_message=str(e),
                    )
                )
                logger.error(f"[ERROR] {account.name}: {e}")

        # Commit if not dry run
        if not dry_run:
            session.commit()
            logger.info("Migration committed successfully")
        else:
            session.rollback()
            logger.info("Dry run - no changes committed")

    engine.dispose()

    return MigrationSummary(
        total_accounts=total_accounts,
        migrated=migrated,
        skipped=skipped,
        errors=errors,
        results=results,
    )


def print_summary(summary: MigrationSummary, dry_run: bool) -> None:
    """Print migration summary to console.

    Args:
        summary: Migration summary to print
        dry_run: Whether this was a dry run
    """
    mode = "DRY RUN" if dry_run else "EXECUTED"
    print(f"\n{'=' * 60}")
    print(f"Migration Summary ({mode})")
    print("=" * 60)
    print(f"Total accounts:  {summary.total_accounts}")
    print(f"Migrated:        {summary.migrated}")
    print(f"Skipped:         {summary.skipped}")
    print(f"Errors:          {summary.errors}")
    print("=" * 60)

    if summary.errors > 0:
        print("\nErrors:")
        for result in summary.results:
            if result.status == "error":
                print(f"  - {result.account_name}: {result.error_message}")


def main() -> int:
    """Main entry point for the migration script.

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    parser = argparse.ArgumentParser(
        description="Migrate TradingConfig + GridConfig to Strategy model"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute migration (default is dry run)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()
    dry_run = not args.execute

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    if dry_run:
        logger.info("Starting migration in DRY RUN mode (use --execute to apply)")
    else:
        logger.info("Starting migration in EXECUTE mode")

    summary = run_migration(dry_run=dry_run, verbose=args.verbose)
    print_summary(summary, dry_run)

    return 0 if summary.errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
