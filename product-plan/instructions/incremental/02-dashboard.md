# Milestone 2: Dashboard

> **Provide alongside:** `product-overview.md`
> **Prerequisites:** Milestone 1 (Foundation) complete

---

## About These Instructions

**What you're receiving:**
- Finished UI designs (React components with full styling)
- Data model definitions (TypeScript types and sample data)
- UI/UX specifications (user flows, requirements, screenshots)
- Design system tokens (colors, typography, spacing)
- Test-writing instructions for each section (for TDD approach)

**What you need to build:**
- Backend API endpoints and database schema
- Authentication and authorization
- Data fetching and state management
- Business logic and validation
- Integration of the provided UI components with real data

**Important guidelines:**
- **DO NOT** redesign or restyle the provided components - use them as-is
- **DO** wire up the callback props to your routing and API calls
- **DO** replace sample data with real data from your backend
- **DO** implement proper error handling and loading states
- **DO** implement empty states when no records exist (first-time users, after deletions)
- **DO** use test-driven development - write tests first using `tests.md` instructions
- The components are props-based and ready to integrate - focus on the backend and data layer

---

## Goal

Implement the Dashboard feature - the primary monitoring interface for bot health, trading activity, and performance.

## Overview

The Dashboard provides real-time visibility into bot health, trading activity, and performance. Users can monitor bot status, check P&L metrics, view active positions/orders, and track recent trading events - all within a selected time period. This is the main screen users will check frequently to understand how their trading bot is performing.

**Key Functionality:**
- View real-time bot status with color-coded indicators (active/paused/stopped/wait)
- Execute bot control actions (pause/stop/resume/start) with confirmation dialogs
- Monitor current market conditions (BTC price, funding rate, MACD signal, grid range)
- Track performance metrics (realized P&L, trades closed) filtered by time period
- Review open positions with live unrealized P&L calculations
- Monitor active grid orders waiting to be filled
- View recent trading activity timeline showing order fills, trades closed, and strategy events

## Recommended Approach: Test-Driven Development

Before implementing this section, **write tests first** based on the test specifications provided.

See `product-plan/sections/dashboard/tests.md` for detailed test-writing instructions including:
- Key user flows to test (success and failure paths)
- Specific UI elements, button labels, and interactions to verify
- Expected behaviors and assertions

The test instructions are framework-agnostic - adapt them to your testing setup (Jest, Vitest, Playwright, Cypress, RSpec, Minitest, PHPUnit, etc.).

**TDD Workflow:**
1. Read `tests.md` and write failing tests for the key user flows
2. Implement the feature to make tests pass
3. Refactor while keeping tests green

## What to Implement

### Components

Copy the section components from `product-plan/sections/dashboard/components/`:

- `Dashboard.tsx` - Main container component that orchestrates all dashboard sections
- `PeriodSelector.tsx` - Dropdown to filter data by time period (today/7days/30days/custom)
- `BotStatusCard.tsx` - Bot status display with control buttons and cycle information
- `MarketOverviewCard.tsx` - Real-time market data (BTC price, funding, MACD, grid range)
- `PerformanceMetricsCard.tsx` - Performance statistics in Today/Total layout
- `PositionsTable.tsx` - Table of open positions with unrealized P&L
- `OrdersTable.tsx` - Table of active grid orders
- `ActivityFeed.tsx` - Timeline of recent trading events
- `ConfirmDialog.tsx` - Reusable confirmation modal for bot actions
- `PositionDetailsModal.tsx` - Detailed view when user clicks a position

### Data Layer

The components expect these data shapes (see `types.ts`):

**BotStatusData:**
- Current bot status (ACTIVE/PAUSED/STOPPED/WAIT)
- State description explaining why bot is in current state
- Cycle activation timestamp
- Last update timestamp

**MarketData:**
- Current BTC price and 24h change percentage
- Funding rate and interval
- MACD signal (bullish/bearish)
- Current grid range (low/high prices)

**PerformanceMetrics:**
- Today's metrics: realized P&L, P&L percentage, trades closed
- Total metrics: total P&L, total trades, average profit per trade

**Position:**
- Entry price, current price, quantity, side (LONG/SHORT)
- Unrealized P&L (dollar and percentage)
- Take profit price, liquidation price
- Opened timestamp

**Order:**
- Price, side (BUY/SELL), quantity, status
- Order ID and created timestamp

**ActivityEvent:**
- Event type (ORDER_FILLED, TRADE_CLOSED, STRATEGY_PAUSED, TP_ADJUSTED, CYCLE_ACTIVATED)
- Description text
- Timestamp

You'll need to:
- Create API endpoints to fetch bot status, market data, performance metrics, positions, orders, and activity events
- Implement backend logic to calculate unrealized P&L for open positions
- Create endpoints to execute bot control actions (pause/stop/resume/start)
- Support filtering performance metrics and activity by time period
- Fetch real-time market data (BTC price, funding rate, MACD calculations)
- Store and retrieve bot state, cycle information, and trading history

### Callbacks

Wire up these user actions:

| Callback | Description | Implementation Notes |
|----------|-------------|---------------------|
| `onPeriodChange` | Called when user selects a time period (today/7days/30days/custom) | Refetch performance metrics and activity events filtered by the selected period. Custom period includes start/end date objects. |
| `onPause` | Called when user confirms pausing the bot | Send pause command to bot backend. Bot should stop placing new orders but keep existing positions open. Update bot status to PAUSED. |
| `onStop` | Called when user confirms stopping the bot | Send stop command. Bot should cancel all pending orders but keep positions until take-profit triggers. Update status to STOPPED. |
| `onResume` | Called when user confirms resuming a paused bot | Send resume command. Bot should return to ACTIVE or WAIT state and resume normal operation. |
| `onStart` | Called when user confirms starting a stopped bot | Send start command. Bot may enter WAIT state if MACD activation is required, or go directly to ACTIVE. |
| `onViewPosition` | Called when user clicks a position to view details (passes position ID) | Fetch full position details and open the PositionDetailsModal. May need additional data not in table row. |
| `onCancelOrder` | Called when user wants to cancel an active order (passes order ID) | Send cancel order command to exchange API. Remove order from active orders list on success. |

### Empty States

Implement empty state UI for when no records exist yet:

- **No open positions:** Show message "No open positions" with subtext "Positions will appear here when the bot places trades"
- **No active orders:** Show message "No active orders" with subtext "Grid orders will appear when the bot is active"
- **No recent activity:** Show message "No recent activity" with subtext "Trading events will appear here as the bot operates"
- **First-time user (bot stopped, no history):** All metrics show $0, empty states for positions/orders/activity, but Market Overview still shows current market data. "Start" button is prominent.

The provided components include empty state designs - make sure to render them when data is empty rather than showing blank screens.

## Files to Reference

- `product-plan/sections/dashboard/README.md` - Feature overview and design intent
- `product-plan/sections/dashboard/tests.md` - Test-writing instructions (use for TDD)
- `product-plan/sections/dashboard/components/` - React components
- `product-plan/sections/dashboard/types.ts` - TypeScript interfaces
- `product-plan/sections/dashboard/sample-data.json` - Test data
- `product-plan/sections/dashboard/screenshot.png` - Visual reference

## Expected User Flows

When fully implemented, users should be able to complete these flows:

### Flow 1: Monitor Bot Status and View Dashboard Overview

1. User navigates to `/dashboard`
2. User sees bot status card displaying current status (ACTIVE/PAUSED/STOPPED/WAIT) with color-coded badge
3. User sees market overview showing current BTC price, funding rate, MACD signal
4. User sees performance metrics for selected time period (default: Today)
5. User sees open positions table with live unrealized P&L
6. User sees active orders table with current grid orders
7. User sees recent activity feed with timestamped events
8. **Outcome:** User has full visibility into bot health and current trading state

### Flow 2: Change Time Period to View Historical Performance

1. User sees period selector at top of dashboard showing "Today"
2. User clicks period selector dropdown
3. User selects "7 Days" from the options
4. Dashboard refreshes with data for the last 7 days
5. **Outcome:** Performance metrics and activity feed update to show last 7 days of data, user can analyze performance over different time ranges

### Flow 3: Pause an Active Bot

1. User sees bot status card showing "ACTIVE" with green badge
2. User clicks "Pause" button in the bot controls
3. Confirmation dialog appears: "Are you sure you want to pause the bot? This will stop new orders but keep existing positions."
4. User clicks "Confirm" in the dialog
5. Bot status updates to "PAUSED" with yellow badge
6. Success notification appears: "Bot paused successfully"
7. **Outcome:** Bot stops placing new orders, existing positions remain open, control buttons now show "Resume" option

### Flow 4: View Detailed Information for an Open Position

1. User sees positions table with open positions
2. User clicks on a position row showing unrealized P&L
3. Position details modal opens showing:
   - Entry price, current price, quantity
   - Unrealized P&L with percentage
   - Take profit price and liquidation price
   - Opened timestamp
4. User reviews the details
5. User clicks "Close" or X to dismiss modal
6. **Outcome:** User understands full details of their position including risk levels (liquidation price proximity)

### Flow 5: Start a Stopped Bot

1. User sees bot status card showing "STOPPED" with red badge
2. User clicks "Start" button
3. Confirmation dialog appears: "Starting the bot will begin placing orders based on your strategy settings. Make sure your strategy is configured correctly."
4. User clicks "Confirm"
5. Bot status updates to "WAIT" (if MACD activation required) or "ACTIVE"
6. Status description explains: "Waiting for MACD bullish signal to activate" (if in WAIT state)
7. **Outcome:** Bot starts running, will begin trading when conditions are met

## Done When

- [ ] Tests written for key user flows (success and failure paths)
- [ ] All tests pass
- [ ] Dashboard component renders with real bot status data
- [ ] Period selector filters performance metrics and activity by time period
- [ ] Bot control actions (pause/stop/resume/start) work with confirmation dialogs
- [ ] Market overview displays real-time BTC price, funding rate, MACD signal, grid range
- [ ] Performance metrics calculate and display correctly (today's P&L, total P&L, averages)
- [ ] Positions table shows open positions with live unrealized P&L calculations
- [ ] Orders table displays active grid orders
- [ ] Activity feed shows recent trading events in chronological order
- [ ] Clicking a position opens position details modal with full information
- [ ] Empty states display properly when no positions, orders, or activity exist
- [ ] First-time user sees helpful empty states and clear "Start" button
- [ ] Color coding works correctly (green for profits/active, red for losses/stopped, yellow for paused)
- [ ] All user actions work end-to-end
- [ ] Matches the visual design
- [ ] Responsive on mobile, tablet, and desktop
