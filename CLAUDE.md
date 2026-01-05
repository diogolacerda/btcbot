# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BTC Grid Bot is an automated trading bot implementing a grid trading strategy for BTC-USDT on BingX exchange. It uses MACD indicators to dynamically activate/deactivate the grid strategy and supports both demo (virtual tokens) and live trading modes.

**Tech Stack:**
- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), Alembic, WebSockets
- **Frontend:** React 19, TypeScript, Vite, TailwindCSS, React Query
- **Database:** PostgreSQL (asyncpg)
- **Infrastructure:** Docker, GitHub Actions CI/CD, Watchtower (auto-deploy)

## Development Commands

### Backend

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

# Database migrations
alembic upgrade head       # Apply all migrations
alembic revision -m "description"  # Create new migration

# Docker build
docker build -t btcbot .

# Run locally (starts bot + API server on port 8081)
python main.py
```

### Frontend

```bash
cd frontend

# Development server (port 5173)
npm run dev

# Type check and build
npm run build

# Linting
npm run lint

# Production preview
npm run preview
```

### Docker Compose

```bash
# Local development (bot + postgres)
docker-compose up -d

# Stage environment
docker-compose -f docker-compose.stage.yml up -d

# Production environment
docker-compose -f docker-compose.prod.yml up -d
```

## Architecture

```
main.py (Entry Point - Bot + API Server)
    │
    ├─ FastAPI (src/api/) - Port 8081
    │   ├─ main.py           # App setup, CORS, router registration
    │   ├─ dependencies.py   # DI: get_session, get_current_user
    │   ├─ routes/
    │   │   ├─ auth.py       # POST /auth/login, /auth/register
    │   │   ├─ health.py     # GET /health
    │   │   ├─ configs.py    # CRUD /configs/trading, /configs/grid
    │   │   ├─ filters.py    # GET/POST /filters
    │   │   └─ trading_data.py  # GET /trading-data/overview
    │   └─ schemas/          # Pydantic models for API
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
    │   ├─ base.py           # Filter abstract base class
    │   ├─ macd_filter.py    # MACD-based trading filter
    │   └─ registry.py       # Filter registry singleton
    │
    ├─ Database (src/database/)
    │   ├─ engine.py         # Async SQLAlchemy engine
    │   ├─ base.py           # Declarative base
    │   ├─ models/           # ORM models
    │   │   ├─ account.py    # BingX account (api_key hash)
    │   │   ├─ user.py       # Auth user (email, password)
    │   │   ├─ trade.py      # Trade history
    │   │   ├─ bot_state.py  # Grid state persistence
    │   │   ├─ trading_config.py  # Trading params
    │   │   ├─ grid_config.py     # Grid params
    │   │   └─ tp_adjustment.py   # TP history log
    │   └─ repositories/     # Data access layer
    │
    ├─ Services (src/services/)
    │   ├─ auth_service.py   # JWT tokens, password hashing
    │   └─ account_service.py # Account management
    │
    ├─ UI (src/ui/)
    │   └─ alerts.py         # Audio alerts for events
    │
    └─ HealthServer (src/health/)
        └─ health_server.py  # HTTP :8080 for Docker healthcheck

frontend/ (React Web UI)
    ├─ src/
    │   ├─ pages/           # DashboardPage, SettingsPage, etc.
    │   ├─ components/      # Reusable UI components
    │   ├─ contexts/        # AuthContext (JWT storage)
    │   ├─ services/        # API client (axios)
    │   ├─ hooks/           # useDarkMode, etc.
    │   ├─ lib/             # axios config, react-query
    │   └─ types/           # TypeScript interfaces
    └─ Dockerfile           # Multi-stage build with nginx
```

**Grid State Machine:** `WAIT → ACTIVATE → ACTIVE ↔ PAUSE → INACTIVE`

**Main Loop (5s interval):**
1. Fetch klines from BingX API (cached)
2. Calculate MACD indicators
3. Evaluate strategy state machine
4. Check filters (MACDFilter)
5. Create/manage LIMIT orders at grid levels
6. Process fills via WebSocket callbacks
7. Calculate P&L and log status

## Database Models

| Model | Table | Description |
|-------|-------|-------------|
| `Account` | `accounts` | BingX API credentials (hashed), trading mode |
| `User` | `users` | Auth users (email, bcrypt password) |
| `Trade` | `trades` | Trade history with P&L |
| `BotState` | `bot_states` | Grid state for crash recovery |
| `TradingConfig` | `trading_configs` | Symbol, leverage, order size |
| `GridConfig` | `grid_configs` | Spacing, range, TP percent |
| `TPAdjustment` | `tp_adjustments` | Dynamic TP change log |

**Migrations:** Located in `migrations/versions/`. Run with `alembic upgrade head`.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Create user account |
| POST | `/auth/login` | No | Get JWT token |
| GET | `/health` | No | Healthcheck |
| GET | `/configs/trading` | JWT | Get trading config |
| PUT | `/configs/trading` | JWT | Update trading config |
| GET | `/configs/grid` | JWT | Get grid config |
| PUT | `/configs/grid` | JWT | Update grid config |
| GET | `/filters` | JWT | List all filters |
| POST | `/filters/{name}` | JWT | Enable/disable filter |
| GET | `/trading-data/overview` | JWT | Current positions, P&L |

**Swagger UI:** http://localhost:8081/docs

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

**Filter System:**
- Pluggable filters control order creation
- Filters enabled by default, volatile state (resets on restart)
- When all filters disabled: orders based on price + MAX_ORDERS only
- When any filter active: all active filters must approve
- See `src/filters/README.md` for details

## Configuration

All config via environment variables (see `.env.example`):
- `config.py` loads into dataclasses: `BingXConfig`, `TradingConfig`, `GridConfig`, `MACDConfig`, `DynamicTPConfig`, `BotStateConfig`
- Three env templates: `.env.example`, `.env.stage.example`, `.env.prod.example`

**Key Environment Variables:**
| Variable | Description | Default |
|----------|-------------|---------|
| `TRADING_MODE` | demo/live | demo |
| `SYMBOL` | Trading pair | BTC-USDT |
| `LEVERAGE` | Position leverage | 10 |
| `ORDER_SIZE_USDT` | Order size | 100 |
| `GRID_SPACING_TYPE` | fixed/percent | fixed |
| `GRID_SPACING_VALUE` | Spacing amount | 100 |
| `TAKE_PROFIT_PERCENT` | TP percentage | 1.0 |
| `MAX_TOTAL_ORDERS` | Max concurrent orders | 10 |
| `DATABASE_URL` | PostgreSQL connection | - |
| `JWT_SECRET_KEY` | API auth secret | - |
| `CORS_ORIGINS` | Allowed CORS origins | localhost:3000 |

## Environments

| Environment | Bot Port | API Port | Frontend Port | Config Source |
|-------------|----------|----------|---------------|---------------|
| Local | 8080 | 8081 | 5173 | `.env` file |
| Stage | 3001 | 3001 | 4001 | Portainer env vars |
| Prod | 3000 | 3000 | 4000 | Portainer env vars |

**IMPORTANT**: Stage and Prod environments do NOT use `.env` files. Environment variables are configured directly in Portainer. The `.env.stage.example` and `.env.prod.example` files are just templates for reference.

## CI/CD Pipeline

### Backend Workflows (`.github/workflows/`)

| Workflow | Trigger | Jobs |
|----------|---------|------|
| `ci.yml` | Push to feature branches | lint, typecheck, test, docker build |
| `cd-stage.yml` | Push to main | Build + push `:stage` tag |

**CI Jobs:**
1. **lint** - `ruff check .` + `ruff format --check .`
2. **typecheck** - `mypy . --ignore-missing-imports`
3. **test** - `pytest --cov=src` with Codecov upload
4. **build** - Docker build (no push on feature branches)
5. **ci-success** - Gate job requiring all above to pass

### Frontend Workflows

| Workflow | Trigger | Action |
|----------|---------|--------|
| `ci-frontend.yml` | Push to feature branches | lint, typecheck, build |
| `cd-stage-frontend.yml` | Push to main | Build + push frontend `:stage` |
| `cd-prod-frontend.yml` | Manual/tag | Build + push frontend `:prod` |

### Auto-Deploy (Watchtower)

Watchtower on homeserver monitors `:stage` and `:prod` tags and auto-restarts containers when new images are pushed.

**Pre-commit hooks:** ruff, mypy, detect-secrets, trailing-whitespace

## Test Structure

```
tests/
├─ api/                    # API endpoint tests
├─ database/               # Repository & model tests
│   ├─ conftest.py         # SQLite async fixtures
│   ├─ test_*_repository.py
│   └─ test_*_model.py
├─ services/               # Service layer tests
├─ test_filters*.py        # Filter system tests
├─ test_bingx_client.py    # BingX API client tests
├─ test_grid_*.py          # Grid calculation tests
├─ test_macd_strategy.py   # Strategy tests
└─ test_bug_*.py           # Regression tests for bug fixes
```

**Run specific test categories:**
```bash
pytest tests/database/ -v       # Database tests only
pytest tests/api/ -v            # API tests only
pytest tests/test_filters*.py   # Filter tests
```

## Homeserver Access

| Item | Value |
|------|-------|
| **IP Local** | `192.168.68.99` |
| **SSH** | `ssh diogo@192.168.68.99` |
| **Portainer** | `http://192.168.68.99:9000` |
| **Stage Bot** | `http://192.168.68.99:3001` |
| **Stage Frontend** | `http://192.168.68.99:4001` |
| **Prod Bot** | `http://192.168.68.99:3000` |
| **Prod Frontend** | `http://192.168.68.99:4000` |

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

# Database backup
./scripts/backup_db.sh

# Database restore
./scripts/restore_db.sh
```

See `docs/HOMESERVER_SETUP.md` for complete setup instructions.

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

CD Stage automatically deploys to Stage environment after merge.

### Status IDs Reference

| Status | ID |
|--------|-----|
| Todo | `69ea4564` |
| In Progress | `1609e48b` |
| Acceptance Testing | `d9f2871e` |
| Done | `fab1b20b` |

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
Scopes: api, grid, client, db, filters, ui, ci
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

## Code Quality

**Ruff Configuration** (from `pyproject.toml`):
- Line length: 100
- Target: Python 3.12
- Rules: E, W, F, I (isort), B (bugbear), C4 (comprehensions), UP (pyupgrade)

**Type Checking:**
- mypy with `--ignore-missing-imports`
- Type stubs: `types-requests`, `pandas-stubs`

**Testing:**
- pytest with `asyncio_mode = "auto"`
- Coverage target: `src/` directory
- SQLite in-memory for async database tests

## Security Notes

- API keys stored as SHA-256 hashes in database
- JWT tokens for API authentication (configurable expiry)
- Passwords hashed with bcrypt
- Pre-commit hook: `detect-secrets` for accidental credential commits
- Never commit `.env` files (in `.gitignore`)
