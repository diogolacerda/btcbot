# AGENTS.md

This file provides guidelines for agentic coding agents working on this repository.

## Build/Lint/Test Commands

```bash
# Backend (Python)
ruff check .          # Linting
ruff format .          # Formatting
mypy .                 # Type checking
pytest                 # Run all tests
pytest tests/test_grid_calculator.py           # Single test file
pytest tests/test_grid_calculator.py::test_function_name  # Single test
pytest --cov=src --cov-report=xml              # With coverage

# Frontend (TypeScript/React)
cd frontend
npm run lint            # ESLint
npx tsc --noEmit        # TypeScript check
npm run build           # Production build
npm run dev             # Dev server

# Docker
docker build -t btcbot .
```

## Code Style Guidelines

### Python

**Imports:**
- `from __future__ import annotations` at top of all files
- Group: stdlib → third-party → local (src/) → TYPE_CHECKING
- `from typing import TYPE_CHECKING` for circular imports
- Example:
  ```python
  from __future__ import annotations
  import asyncio
  from collections.abc import Callable
  from decimal import Decimal
  from uuid import UUID

  from fastapi import Depends
  from sqlalchemy.ext.asyncio import AsyncSession

  from src.database.models.user import User

  if TYPE_CHECKING:
      from src.database.repositories.account_repository import AccountRepository
  ```

**Type Hints:**
- Use `T | None` instead of `Optional[T]`
- Use `list[T]` instead of `List[T]`
- Use `dict[K, V]` instead of `Dict[K, V]`
- Use `TypeVar` for generic types: `T = TypeVar("T", bound=Base)`
- Return type annotation on all functions
- Annotate class attributes in dataclasses and models

**Naming Conventions:**
- Classes: `PascalCase` (e.g., `GridCalculator`, `GridStatus`)
- Functions/Methods: `snake_case` (e.g., `calculate_levels`, `get_by_id`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_TOTAL_ORDERS`)
- Private members: `_leading_underscore` (e.g., `_cache`, `_invalidate_cache`)
- Test classes: `TestPascalCase` (e.g., `TestAnchorPrice`)
- Test functions: `test_snake_case` (e.g., `test_anchor_to_hundreds`)

**Formatting:**
- Line length: 100 characters (enforced by ruff)
- Ruff formatter auto-applies on commit via pre-commit hooks
- Use dataclasses for simple data containers
- Use `@dataclass` decorator with explicit field defaults

**Error Handling:**
- Always use try/except for external API calls and DB operations
- Log errors with context: `logger.error(f"Error fetching {resource}: {e}")`
- Re-raise after logging: `raise`
- Use specific exceptions when possible (e.g., `HTTPException` with status codes)
- Example:
  ```python
  try:
      result = await client.get_data()
      return result
  except Exception as e:
      logger.error(f"API request failed: {e}")
      raise HTTPException(status_code=500, detail="API error")
  ```

**Documentation:**
- Docstrings in Google style with Args/Returns/Raises sections
- Example:
  ```python
  async def get_by_id(self, id: UUID) -> T | None:
      """Get a record by its ID.

      Args:
          id: The UUID of the record to retrieve.

      Returns:
          The record if found, None otherwise.

      Raises:
          DatabaseError: If database query fails.
      """
  ```

**Database (SQLAlchemy):**
- Async sessions: `AsyncSession` from `sqlalchemy.ext.asyncio`
- Models inherit from `Base` with UUID primary keys
- Use `Mapped[Type]` with `mapped_column()`
- Decimal for all financial values: `Numeric(20, 8)`
- Repository pattern: inherit from `BaseRepository[T]`
- Relationships: use `relationship()` with string forward refs
- Cascade deletes for related records

**API (FastAPI):**
- Use `APIRouter` with prefix and tags
- `Annotated` for dependencies: `Annotated[User, Depends(get_current_active_user)]`
- Response models: Pydantic schemas in `src/api/schemas/`
- HTTP exceptions with status codes from `fastapi.HTTPException`

**Testing (pytest):**
- `@pytest.fixture` for test data setup
- Class-based organization for related tests
- Async tests: use `async def` and `pytest-asyncio` (auto mode)
- Arrange-Act-Assert pattern
- Print statements for debugging in integration tests
- Example:
  ```python
  class TestAnchorPrice:
      def test_anchor_to_hundreds(self):
          assert anchor_price(88050, 100) == 88000.0
  ```

**Logging:**
- Module-level loggers: `logger = logging.getLogger(__name__)`
- Pre-defined loggers in `src/utils/logger.py`: `main_logger`, `orders_logger`, `error_logger`
- Use appropriate levels: DEBUG for details, INFO for normal ops, ERROR for problems

**Decimal Usage:**
- Use `Decimal("1.5")` not `Decimal(1.5)` for financial values
- Convert to float for API responses only: `float(dec_value)`
- Keep Decimal internally for precision

### Frontend (TypeScript/React)

**Imports:**
- Group: React → UI components → utils → types
- Absolute imports for src/ components: `@/components/Button`
- Relative for co-located files

**Components:**
- Functional components with hooks
- Props interfaces defined inline or in types.ts
- Tailwind CSS for styling
- Example:
  ```tsx
  interface ButtonProps {
    onClick: () => void;
    label: string;
    disabled?: boolean;
  }

  export const Button = ({ onClick, label, disabled }: ButtonProps) => {
    return (
      <button
        onClick={onClick}
        disabled={disabled}
        className="px-4 py-2 bg-blue-500 rounded"
      >
        {label}
      </button>
    );
  };
  ```

## Pre-Commit Hooks

Hooks run automatically on commit and block non-compliant code:
- Ruff linting (with auto-fix)
- Ruff formatting
- MyPy type checking
- Detect-secrets (scans for leaked credentials)
- Trailing whitespace removal
- No debug statements (print/pdb)

## GitHub Actions Self-Hosted Runners

The repository uses 9 self-hosted runners on homeserver (192.168.68.99) for CI/CD workflows.

**Performance:**
- CI: 65s (73% faster than GitHub cloud runners)
- CD Stage: 77-120s (63% faster)
- Cost: $0/month (vs ~$100 on cloud)

**Quick Commands:**

```bash
# Check runner status
ssh diogo@192.168.68.99 "sudo systemctl list-units 'actions.runner*' --no-pager | grep 'active running'"

# View logs of specific runner
ssh diogo@192.168.68.99 "sudo journalctl -u actions.runner.diogolacerda-btcbot.homeserver-runner -f"

# Restart all runners
ssh diogo@192.168.68.99 "sudo systemctl restart 'actions.runner*'"

# Check system resources
ssh diogo@192.168.68.99 "free -h && df -h && uptime"

# View recent workflow runs
gh run list --limit 10

# Watch workflow run in real-time
gh run watch
```

**Documentation:** See [docs/SELFHOSTED_RUNNER.md](docs/SELFHOSTED_RUNNER.md) for complete configuration, troubleshooting, and management guide.

## Development Protocol

**ONLY follow this protocol when explicitly asked to implement a card/task.**

You are working on the btcbot repository. Follow this workflow strictly:

### 1. Task Management (GitHub Projects)

GitHub Projects is the source of truth. NEVER edit files in tasks/ - they are historical reference only.

Status IDs:
| Status             | ID       |
|--------------------|----------|
| Todo               | 69ea4564 |
| In Progress        | 1609e48b |
| Acceptance Testing | d9f2871e |
| Done               | fab1b20b |

Update status:
```bash
gh project item-edit --project-id PVT_kwHOABvENc4BLYiG --id <ITEM_ID> \
  --field-id PVTSSF_lAHOABvENc4BLYiGzg6-Uo8 --single-select-option-id <STATUS_ID>
```

### Creating and Updating Project Cards

**Create a GitHub Issue:**
```bash
gh issue create --title "TASK-ID: Brief description" --body "<detailed task description>"
```

**Add Issue to Project:**
```bash
# Get issue node_id
gh api repos/diogolacerda/btcbot/issues/<ISSUE_NUMBER> --jq '.node_id'

# Add to project via GraphQL
gh api graphql -f query='
mutation {
  addProjectV2ItemById(input: {projectId: "PVT_kwHOABvENc4BLYiG", contentId: "<NODE_ID>"}) {
    item {
      id
      content {
        ... on Issue {
          number
          title
        }
      }
    }
  }
}'
```

**Find Project Item ID:**
```bash
# List items to find your issue
gh api graphql -f query='
{
  user(login: "diogolacerda") {
    projectV2(number: 2) {
      items(first: 100) {
        nodes {
          id
          content {
            ... on Issue {
              number
              title
            }
          }
        }
      }
    }
  }
}' | jq '.data.user.projectV2.items.nodes[] | select(.content.number == <ISSUE_NUMBER>) | .id'
```

**Update Project Item Fields:**
```bash
# Update Status
gh project item-edit --project-id PVT_kwHOABvENc4BLYiG --id <ITEM_ID> \
  --field-id PVTSSF_lAHOABvENc4BLYiGzg6-Uo8 --single-select-option-id <STATUS_ID>

# Update Area (Backend/Frontend/DevOps/Database/Docs)
gh project item-edit --project-id PVT_kwHOABvENc4BLYiG --id <ITEM_ID> \
  --field-id PVTSSF_lAHOABvENc4BLYiGzg6-UrM --single-select-option-id <AREA_ID>

# Update Priority (Critical/High/Medium/Low)
gh project item-edit --project-id PVT_kwHOABvENc4BLYiG --id <ITEM_ID> \
  --field-id PVTSSF_lAHOABvENc4BLYiGzg6-Usk --single-select-option-id <PRIORITY_ID>
```

**Field IDs Reference:**

Status:
| Status             | ID       |
|--------------------|----------|
| Todo               | 69ea4564 |
| In Progress        | 1609e48b |
| Acceptance Testing | d9f2871e |
| Done               | fab1b20b |

Area:
| Area      | ID       |
|-----------|----------|
| Backend   | df9776cc |
| Frontend  | d0242095 |
| DevOps    | 2b6db103 |
| Database  | bb875bc3 |
| Docs      | 93b52a0b |

Priority:
| Priority | ID       |
|----------|----------|
| 🔴 Critical | 9591fa8c |
| 🟠 High | 744ef8f1 |
| 🟡 Medium | ec1ebddb |
| 🟢 Low | a08f8e50 |

### 2. Git Worktrees (Parallel Development)

Each task must have its own worktree in /Users/diogolacerda/Sites/btcbot-worktrees/.

Create worktree:
```bash
cd /Users/diogolacerda/Sites/btcbot
git checkout main && git pull origin main
git worktree add ../btcbot-worktrees/feature-TASK-ID -b feature/TASK-ID-desc main
```

Setup environment:
```bash
cd /Users/diogolacerda/Sites/btcbot-worktrees/feature-TASK-ID
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp /Users/diogolacerda/Sites/btcbot/.env .env
```

IMPORTANT: DO NOT run pre-commit install in worktrees - hooks already work automatically via shared dynamic script.

### 3. Branch Naming

| Type    | Pattern                 | Example                         |
|---------|-------------------------|---------------------------------|
| Feature | feature/<TASK_ID>-<desc> | feature/BE-001-trade-repository |
| Bugfix  | bugfix/<ISSUE>-<desc>    | bugfix/123-fix-pnl              |
| Hotfix  | hotfix/<TASK_ID>-<desc>  | hotfix/BE-001-fix-validation    |

### 4. Commits and PRs

ALWAYS use the /commit-push-pr skill instead of manual commands. It:
- Analyzes git status and git diff
- Generates commit message following convention
- Makes commit, push and creates PR automatically

Commit convention:
```
<type>(<scope>): <description>
```

Types: feat, fix, refactor, test, docs, chore

### 5. Complete Task Workflow

1. Fetch task from GitHub Projects
2. Update status to "In Progress" (1609e48b)
3. Create worktree with new branch based on main
4. Setup environment (venv, deps, .env)
5. Develop and test (pytest)
6. Create PR using /commit-push-pr
7. Wait for CI to pass
8. Merge with gh pr merge --merge
9. Update status to "Acceptance Testing" (d9f2871e)
10. Clean up worktree with git worktree remove

### 6. After Other Branches Are Merged

If another branch was merged before yours:
```bash
git fetch origin main && git rebase origin/main
```

### 7. Important Notes

- Database: All worktrees share the same PostgreSQL (port 5432)
- Health server: Only one bot can run locally (port 8080)
- Migrations: Run alembic upgrade head when switching worktrees
- Pre-commit: Hooks are shared - NEVER run pre-commit install in worktrees

## Manual Testing Protocol

When asked to test a task, act as a human tester accessing the stage environment:

**Testing Process:**
- Navigate to the stage frontend: http://192.168.68.99:3003
- Backend API: http://192.168.68.99:3002
- **IMPORTANT: Read the task description carefully and test ONLY what is specified**
- Test functionality as a human user would (interacting with UI, forms, buttons)
- **DO NOT** run unit tests - that is the developer's responsibility
- Provide a test report at the end indicating PASS/FAIL status
- Only examine code to find bugs if the test fails
- When investigating bugs, ensure main branch is up-to-date: `git fetch origin && git status`

**Test Report Format:**
```
## Test Report: [Feature Name]

**Status:** ✅ PASS / ❌ FAIL

**Tested:**
- [ ] Test case 1 description
- [ ] Test case 2 description
- [ ] Test case 3 description

**Result:** [Brief summary of findings]
```

**Common Testing Issues & Solutions:**

**Issue: Browser already in use error**
```
Error: Browser is already in use for /path/to/browser
```
Solution: Close existing browser processes before starting new tests
```bash
pkill -f "chrome"
```

**Issue: Cannot find task implementation files**
- First check if files exist using `glob` or `read` tools
- Verify main branch is up-to-date: `git fetch origin && git status`
- The task may not be implemented yet despite being marked as "in progress"

**Issue: Login fails with 401 Unauthorized**
- Check if frontend is connected to correct backend (port 3002)
- Verify user exists in database
- Use test credentials from Testing Notes section

**Issue: Frontend shows "Coming Soon" placeholder**
- The feature may not be fully implemented yet
- Check if API endpoints exist and return data
- Verify frontend components exist for the feature

**Issue: Incorrect test report due to stale code**
- Always run `git fetch origin` before testing
- Verify the main branch is current with `git status`
- Check implementation files exist before concluding a feature is missing
- Use `glob` tool to verify files like `frontend/src/hooks/useTradeHistory.ts`

## Finding Tasks in GitHub Projects

To find and view tasks tracked in GitHub Projects:

```bash
# List all GitHub Projects
gh project list

# List items in a specific project (replace <project-number> with actual number)
gh project item-list <project-number> --limit 50 --owner @me --format json

# Find a specific task by ID or name
gh project item-list <project-number> --limit 50 --owner @me --format json | jq '.items[] | select(.title | contains("TASK-ID"))'

# Get detailed content of a specific task
gh project item-list <project-number> --limit 50 --owner @me --format json | jq '.items[] | select(.title | contains("TASK-ID")) | .content.body'

# Filter by status column (example: items in "Acceptance Testing")
# Note: Requires additional jq filtering on status field
```

**Example: Finding BE-TRADE-004**
```bash
# List projects to find project number
gh project list

# Search for BE-TRADE-004 in project 2
gh project item-list 2 --limit 50 --owner @me --format json | jq '.items[] | select(.title | contains("BE-TRADE-004"))'

# Get full task details
gh project item-list 2 --limit 50 --owner @me --format json | jq '.items[] | select(.title | contains("BE-TRADE-004")) | .content.body' > /tmp/task-details.json
```

## Testing Notes

**Stage Environment Login Credentials:**
- Email: `diogo@example.com`
- Password: `diogo1051`  # pragma: allowlist secret

**Browser Testing:**
- Always close Playwright browser after testing: `playwright_browser_close`
- Check for console errors: `playwright_browser_console_messages` with level `error`
- Wait for dynamic content: `playwright_browser_wait_for` with appropriate time

**Before Testing:**
- Ensure main branch is up-to-date: `git fetch origin && git status`
- Verify task implementation by checking for required files first
- If testing fails unexpectedly, verify if code exists before reporting failure
- Example: If testing FE-TRADE-001, check if `frontend/src/hooks/useTradeHistory.ts` exists

## Important Notes

- **NO comments** in code unless explicitly requested
- Type checking is enforced in CI but partial typing is acceptable
- Database migrations via Alembic
- All async operations must be awaited
- Use `datetime.now(UTC)` for timezone-aware timestamps
- Frontend builds via Vite + React + TypeScript
- **All project tasks are tracked in GitHub Projects** - refer to the GitHub Projects board for task status, assignments, and sprint planning
