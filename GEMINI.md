# Project Overview

This is a Python-based grid trading bot for the BingX exchange, specifically targeting the BTC-USDT perpetual futures market. It implements a grid trading strategy that is dynamically activated and deactivated based on the MACD indicator. It supports both `demo` (virtual tokens) and `live` (real USDT) trading modes.

## Key Concepts

-   **Trading Modes**:
    -   `demo`: Uses VST virtual tokens via a BingX demo account.
    -   `live`: Uses real USDT for production trading.
-   **Grid State Machine**: The core logic follows a state machine: `WAIT → ACTIVATE → ACTIVE ↔ PAUSE → INACTIVE`.
-   **Main Loop**: Runs every 5 seconds to fetch market data, calculate indicators, evaluate the strategy, and manage grid orders.
-   **Order Limit Calculation**: The number of available grid slots is dynamically calculated: `available_slots = MAX_TOTAL_ORDERS - filled_orders_awaiting_tp - pending_limit_orders`. It counts take-profit orders to accurately determine the number of filled positions, as BingX consolidates multiple fills into a single position but maintains separate TPs.
-   **Grid Anchoring**: `GRID_ANCHOR_MODE=none|hundred` aligns the grid to clean price multiples (e.g., every $100) for cleaner levels.
-   **Dynamic TP (BE-007)**: Adjusts the take-profit percentage based on the funding rate. A positive rate increases the TP, while a negative rate decreases it.

## Architecture

```
main.py (Entry Point)
    │
    ├─ BingXClient (src/client/)
    │   ├─ bingx_client.py    # REST API with auth, caching (60s TTL)
    │   └─ websocket_client.py # Real-time order fill notifications
    │
    ├─ GridManager (src/grid/)
    │   ├─ grid_manager.py     # Main orchestrator of the grid logic
    │   ├─ grid_calculator.py  # Grid level price calculations
    │   ├─ order_tracker.py    # Position/trade/P&L state management
    │   └─ dynamic_tp_manager.py # TP adjustment based on funding rate
    │
    ├─ MACDStrategy (src/strategy/)
    │   └─ macd_strategy.py    # MACD indicator logic and state machine
    │
    ├─ Filters (src/filters/)
    │   ├─ macd_filter.py      # MACD-based trading filter
    │   └─ registry.py         # Filter registry pattern
    │
    ├─ Database (src/database/)
    │   ├─ models/             # SQLAlchemy ORM models
    │   └─ repositories/       # Data access layer
    │
    ├─ UI (src/ui/)
    │   └─ alerts.py           # Audio alerts for trading events
    │
    └─ HealthServer (src/health/)
        └─ health_server.py    # HTTP server on port 8080 for Docker healthchecks
```

-   **Key Technologies**:
    -   Python 3.12
    -   `httpx` for async HTTP requests
    -   `SQLAlchemy` for the ORM and `Alembic` for migrations
    -   `pandas` for MACD calculations
    -   `ruff`, `mypy`, `pytest` for code quality and testing

# Environments & Configuration

All configuration is loaded via environment variables into dataclasses defined in `config.py`.

| Environment | Port | Config Source | Trading Mode |
|-------------|------|---------------|--------------|
| Local | - | `.env` file | `demo` |
| Stage | 3001 | **Portainer env vars** | `demo` |
| Prod | 3000 | **Portainer env vars** | `live` |

**IMPORTANT**: Stage and Prod environments do NOT use `.env` files. Environment variables are configured directly in Portainer. The `.env.stage.example` and `.env.prod.example` files are for reference only.

## Homeserver Access

| Item | Value |
|--------------|--------------------------------|
| **IP Local** | `192.168.68.99` |
| **SSH** | `ssh diogo@192.168.68.99` |
| **Portainer** | `http://192.168.68.99:9000` |
| **Stage URL** | `http://192.168.68.99:3001` |
| **Prod URL** | `http://192.168.68.99:3000` |

### Common Remote Commands

```bash
# View Stage logs
ssh diogo@192.168.68.99 "docker logs btcbot-stage --tail 100"

# View Prod logs
ssh diogo@192.168.68.99 "docker logs btcbot-prod --tail 100"

# Restart Stage container
ssh diogo@192.168.68.99 "docker restart btcbot-stage"
```

# Building and Running

1.  **Clone the repo**.
2.  **Create a virtual environment**: `python3.12 -m venv venv && source venv/bin/activate`
3.  **Install dependencies**: `pip install -r requirements.txt -r requirements-dev.txt`
4.  **Install pre-commit hooks**: `pre-commit install`
5.  **Configure locally**: `cp .env.example .env` and edit the file.
6.  **Run locally**: `python main.py`
7.  **Run with Docker**: `docker build -t btcbot .` and `docker run --env-file .env btcbot`

# Development Workflow

## Task Management

**IMPORTANT**: The markdown files in `tasks/` are **historical reference only** and must **NEVER be updated**. Task management is done exclusively through **GitHub Projects**.

## Git & Commits

-   **Branch Naming**:
    -   Feature: `feature/<TASK_ID>-<description>`
    -   Bugfix: `bugfix/<ISSUE_NUM>-<description>`
    -   Hotfix: `hotfix/<TASK_ID>-<description>`
-   **Commit Convention**: `<type>(<scope>): <description>` (e.g., `feat(grid): add dynamic order limit`).

See `docs/GITFLOW.md` for the complete workflow.

## Git Worktrees for Parallel Development

This project uses Git worktrees to allow multiple agents to work on different tasks in parallel.

1.  **Create Worktree**: From the main repo (`btcbot/`), run:
    ```bash
    git worktree add ../btcbot-worktrees/feature-TASK-ID -b feature/TASK-ID-desc main
    ```
2.  **Setup Environment**: `cd` into the new worktree directory and run the installation steps (venv, pip, pre-commit, cp .env).
3.  **Develop**: Code, test, and commit your changes on the worktree's branch.
4.  **Cleanup**: After the PR is merged, remove the worktree: `git worktree remove ../btcbot-worktrees/feature-TASK-ID`

**Note**: All worktrees share the same PostgreSQL database. Only one bot instance can run locally at a time due to port conflicts (8080).

## Code Quality & Testing

-   **Lint & Format**: `ruff check .` and `ruff format .`
-   **Type Check**: `mypy .`
-   **Run all tests**: `pytest`
-   **Run tests with coverage**: `pytest --cov=src --cov-report=xml`

The project has a full CI/CD pipeline in `.github/workflows/ci.yml` that runs these checks.
