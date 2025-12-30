# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BTC Grid Bot is an automated trading bot implementing a grid trading strategy for BTC-USDT on BingX exchange. It uses MACD indicators to dynamically activate/deactivate the grid strategy and supports both demo (virtual tokens) and live trading modes.

## Development Commands

```bash
# Linting and formatting
ruff check .
ruff format .

# Type checking
mypy .

# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=xml

# Run a single test file
pytest tests/test_grid_calculator.py

# Run a specific test
pytest tests/test_grid_calculator.py::test_function_name -v

# Docker build
docker build -t btcbot .

# Run locally
python main.py
```

## Task Management Rules

**IMPORTANT:** The markdown files in `tasks/` folder (`tasks_backend.md`, `tasks_database.md`, `tasks_devops.md`, etc.) are **historical reference only** and should **NEVER be updated**. All task management must be done exclusively through **GitHub Projects**.

- **DO NOT** update status in markdown task files
- **DO NOT** add new tasks to markdown task files
- **ALWAYS** use GitHub Projects API to update task status
- **ALWAYS** use GitHub Projects API to create new tasks

## Task Execution Workflow

GitHub Projects is the **source of truth** for task status. Follow this workflow for every task:

### 1. Starting a Task

```bash
# 1. Read task description from GitHub Projects
gh api graphql -f query='
query {
  node(id: "PVT_kwHOABvENc4BLYiG") {
    ... on ProjectV2 {
      items(first: 100) {
        nodes {
          content {
            ... on DraftIssue {
              title
              body
            }
          }
        }
      }
    }
  }
}' | grep -A 100 "TASK-ID"

# 2. Update status to "In Progress"
gh project item-edit --project-id PVT_kwHOABvENc4BLYiG --id <ITEM_ID> \
  --field-id PVTSSF_lAHOABvENc4BLYiGzg6-Uo8 --single-select-option-id 1609e48b

# 3. Create feature branch
git checkout main
git pull origin main
git checkout -b feature/TASK-ID-description
```

### 2. Development & PR

```bash
# Run checks before pushing
pytest && ruff check . && mypy .

# Push and create PR
git push -u origin feature/TASK-ID-description
gh pr create --title "[TASK-ID] Feature: Description" --body "..."

# After CI passes, merge the PR
gh pr merge --merge
```

### 3. After PR Merge

```bash
# Update status to "Acceptance Testing"
gh project item-edit --project-id PVT_kwHOABvENc4BLYiG --id <ITEM_ID> \
  --field-id PVTSSF_lAHOABvENc4BLYiGzg6-Uo8 --single-select-option-id d9f2871e
```

CD Stage automatically deploys to Stage environment (port 3001) after merge.

### Status IDs Reference

| Status | ID |
|--------|-----|
| Todo | `69ea4564` |
| In Progress | `1609e48b` |
| Acceptance Testing | `d9f2871e` |
| Done | `fab1b20b` |

## Architecture

```
main.py (Entry Point)
    │
    ├─ BingXClient (src/client/)
    │   ├─ bingx_client.py    # REST API with auth, caching (60s TTL)
    │   └─ websocket_client.py # Real-time order fill notifications
    │
    ├─ GridManager (src/grid/)
    │   ├─ grid_manager.py     # Main orchestrator (~2600 lines)
    │   ├─ grid_calculator.py  # Grid level price calculations
    │   ├─ order_tracker.py    # Position/trade/P&L state management
    │   └─ dynamic_tp_manager.py # TP adjustment based on funding rate
    │
    ├─ MACDStrategy (src/strategy/)
    │   └─ macd_strategy.py    # MACD indicator logic, state machine
    │
    ├─ Filters (src/filters/)
    │   ├─ macd_filter.py      # MACD-based trading filter
    │   └─ registry.py         # Filter registry pattern
    │
    ├─ Dashboard (src/ui/)
    │   ├─ dashboard.py        # Rich terminal UI
    │   └─ keyboard_handler.py # A/D/Q keyboard controls
    │
    └─ HealthServer (src/health/)
        └─ health_server.py    # HTTP :8080 for Docker healthcheck
```

**Grid State Machine:** `WAIT → ACTIVATE → ACTIVE ↔ PAUSE → INACTIVE`

**Main Loop (5s interval):**
1. Fetch klines from BingX API (cached)
2. Calculate MACD indicators
3. Evaluate strategy state machine
4. Check filters (MACDFilter)
5. Create/manage LIMIT orders at grid levels
6. Process fills via WebSocket callbacks
7. Calculate P&L, render dashboard

## Key Concepts

**Trading Modes:**
- `demo` - Uses VST virtual tokens (BingX demo account)
- `live` - Uses real USDT (production)

**Order Limit Calculation:**
- `available_slots = MAX_TOTAL_ORDERS - filled_orders_awaiting_tp - pending_limit_orders`
- BingX consolidates multiple fills into one position but keeps separate TPs
- Count TP orders (not positions) to determine filled order count

**Grid Anchoring:**
- `GRID_ANCHOR_MODE=none|hundred` - Align grid to clean price multiples
- Example: Anchor to $100 multiples for cleaner levels

**Dynamic TP (BE-007):**
- Adjusts take-profit based on funding rate
- Positive funding → larger TP (longs are paying)
- Negative funding → smaller TP (shorts are paying)

## Configuration

All config via environment variables (see `.env.example`):
- `config.py` loads into dataclasses: `BingXConfig`, `TradingConfig`, `GridConfig`, `MACDConfig`, `DynamicTPConfig`, `ReactivationConfig`
- Three env templates: `.env.example`, `.env.stage.example`, `.env.prod.example`

## Environments

| Environment | Port | Config Source | Trading Mode |
|-------------|------|---------------|--------------|
| Local | - | `.env` file | demo |
| Stage | 3001 | **Portainer env vars** | demo |
| Prod | 3000 | **Portainer env vars** | live |

**IMPORTANT**: Stage and Prod environments do NOT use `.env` files. Environment variables are configured directly in Portainer. The `.env.stage.example` and `.env.prod.example` files are just templates for reference.

Current Stage config (Portainer):
- `TAKE_PROFIT_PERCENT=0.5`
- `TRADING_MODE=demo`

## Homeserver Access

| Item | Valor |
|------|-------|
| **IP Local** | `192.168.68.99` |
| **SSH** | `ssh diogo@192.168.68.99` |
| **Portainer** | `http://192.168.68.99:9000` |
| **Stage URL** | `http://192.168.68.99:3001` |
| **Prod URL** | `http://192.168.68.99:3000` |

### Common Commands

```bash
# SSH into homeserver
ssh diogo@192.168.68.99

# View Stage logs
ssh diogo@192.168.68.99 "docker logs btcbot-stage --tail 100"

# View Prod logs
ssh diogo@192.168.68.99 "docker logs btcbot-prod --tail 100"

# Restart Stage container
ssh diogo@192.168.68.99 "docker restart btcbot-stage"

# Check container status
ssh diogo@192.168.68.99 "docker ps --filter 'name=btcbot'"
```

See `docs/HOMESERVER_SETUP.md` for complete setup instructions.

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`):
1. **lint** - ruff check + format
2. **typecheck** - mypy
3. **test** - pytest with Codecov
4. **docker** - build image (no push on feature branches)
5. **ci-success** - gate for all jobs

Pre-commit hooks: ruff, mypy, detect-secrets, trailing-whitespace

## Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<TASK_ID>-<description>` | `feature/BE-001-trade-repository` |
| Bugfix | `bugfix/<ISSUE_NUM>-<description>` | `bugfix/123-fix-pnl-calculation` |
| Hotfix | `hotfix/<TASK_ID>-<description>` | `hotfix/BE-001-fix-validation` |

## Commit Convention

```
<type>(<scope>): <description>

Types: feat, fix, refactor, test, docs, chore
```

See `docs/GITFLOW.md` for complete workflow details.

## Git Worktrees (Parallel Development)

Git worktrees allow multiple agents to work on different tasks simultaneously, each in an independent working directory with its own branch.

### Directory Structure

```
/Users/diogolacerda/Sites/
├── btcbot/                          # Main repo (main branch)
│   └── .git/                        # Shared git database
│
└── btcbot-worktrees/                # Parallel worktrees
    ├── feature-BE-XXX/              # Agent 1 worktree
    ├── feature-DB-YYY/              # Agent 2 worktree
    └── bugfix-ZZZ/                  # Agent 3 worktree
```

### Creating a Worktree

```bash
# From main repo
cd /Users/diogolacerda/Sites/btcbot

# Create worktree with new branch
git worktree add ../btcbot-worktrees/feature-TASK-ID -b feature/TASK-ID-desc main

# Or for existing branch
git worktree add ../btcbot-worktrees/feature-TASK-ID feature/TASK-ID-desc
```

### Setup Environment in Worktree

```bash
cd /Users/diogolacerda/Sites/btcbot-worktrees/feature-TASK-ID

# Create venv
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy .env
cp /Users/diogolacerda/Sites/btcbot/.env .env
```

### Managing Worktrees

```bash
# List active worktrees
git worktree list

# Remove worktree after task completion
git worktree remove ../btcbot-worktrees/feature-TASK-ID

# Force remove (if uncommitted changes)
git worktree remove --force ../btcbot-worktrees/feature-TASK-ID
```

### Workflow per Agent

1. **Check available worktrees**: `git worktree list`
2. **Update main**: `git checkout main && git pull origin main`
3. **Create worktree**: `git worktree add ../btcbot-worktrees/TASK-ID -b feature/TASK-ID main`
4. **Setup environment**: venv, deps, pre-commit, .env
5. **Develop**: edit, test (`pytest`), commit, push
6. **Create PR** and wait for merge
7. **Cleanup**: `git worktree remove ../btcbot-worktrees/TASK-ID`

### Important Notes

- **Database**: All worktrees share the same PostgreSQL (port 5432)
- **Health server**: Only one bot can run locally at a time (port 8080)
- **Migrations**: Run `alembic upgrade head` when switching worktrees
- **Merge order**: Merge PRs sequentially; rebase other branches after merge:
  ```bash
  git fetch origin main && git rebase origin/main
  ```
- **Limitations**: A branch can only be checked out in one worktree at a time
