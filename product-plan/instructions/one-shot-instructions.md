# Btcbot — Complete Implementation Instructions

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
- **DO NOT** redesign or restyle the provided components — use them as-is
- **DO** wire up the callback props to your routing and API calls
- **DO** replace sample data with real data from your backend
- **DO** implement proper error handling and loading states
- **DO** implement empty states when no records exist (first-time users, after deletions)
- **DO** use test-driven development — write tests first using `tests.md` instructions
- The components are props-based and ready to integrate — focus on the backend and data layer

---

# Btcbot — Product Overview

## Summary

An automated Bitcoin grid trading bot with intelligent MACD-based activation that runs 24/7 on BingX perpetual futures. A "set it and forget it" system that eliminates emotional trading and constant chart monitoring - now with a professional control panel so you can actually see what your bot is doing.

## Planned Sections

1. **Dashboard** — Real-time monitoring of bot status, active orders, open positions, and P&L.

2. **Trade History** — Comprehensive view of all closed trades with entry/exit prices, profit tracking, and performance analytics.

3. **Strategy** — Configure and manage trading strategies (risk parameters, filters like MACD, grid settings) with start/stop/pause controls.

4. **Settings** — General Btcbot configuration (exchange connection, notifications, display preferences, and system settings).

## Data Model

**Core Entities:**
- **User** — User of the Btcbot application who manages trading accounts and monitors bot performance
- **Account** — Exchange account connection with BingX credentials and settings
- **Strategy** — Trading strategy configuration with risk parameters, filters, and execution state
- **Trade** — Completed trading transaction with entry/exit prices and P&L
- **Order** — Active buy/sell order currently placed on the exchange
- **Position** — Currently open position being managed by the bot

## Design System

**Colors:**
- Primary: emerald
- Secondary: amber
- Neutral: slate

**Typography:**
- Heading: Inter
- Body: Inter
- Mono: JetBrains Mono

## Implementation Sequence

Build this product in milestones:

1. **Foundation** — Set up design tokens, data model types, and application shell
2. **Dashboard** — Real-time monitoring interface
3. **Trade History** — Historical trade analytics
4. **Strategy** — Strategy configuration controls
5. **Settings** — System and account management

Each milestone has a dedicated instruction document in `product-plan/instructions/`.

---

# Milestone 1: Foundation

## Goal

Set up the foundational elements: design tokens, data model types, routing structure, and application shell.

## What to Implement

### 1. Design Tokens

Configure your styling system with these tokens:

- See `product-plan/design-system/tokens.css` for CSS custom properties
- See `product-plan/design-system/tailwind-colors.md` for Tailwind configuration
- See `product-plan/design-system/fonts.md` for Google Fonts setup

**Key Colors:**
- Primary: `emerald` (buttons, links, active states)
- Secondary: `amber` (tags, highlights)
- Neutral: `slate` (backgrounds, text, borders)

**Typography:**
- Heading & Body: Inter
- Code/Mono: JetBrains Mono

Import Google Fonts in your HTML `<head>`:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

### 2. Data Model Types

Create TypeScript interfaces for your core entities:

- See `product-plan/data-model/types.ts` for interface definitions
- See `product-plan/data-model/README.md` for entity relationships

**Core Entities:**
- **User** — Application user
- **Account** — BingX exchange account connection
- **Strategy** — Trading strategy configuration
- **Trade** — Completed trade record
- **Order** — Active exchange order
- **Position** — Open exchange position

Copy the types from `product-plan/data-model/types.ts` to your project and extend as needed for your backend.

### 3. Routing Structure

Create placeholder routes for each section:

- `/` or `/dashboard` — Dashboard (default/home)
- `/trade-history` — Trade History
- `/strategy` — Strategy Configuration
- `/settings` — Settings

For now, these can render simple placeholder pages. You'll replace them with real section implementations in later milestones.

### 4. Application Shell

Copy the shell components from `product-plan/shell/components/` to your project:

- `AppShell.tsx` — Main layout wrapper
- `MainNav.tsx` — Navigation component
- `UserMenu.tsx` — User menu with avatar

**Wire Up Navigation:**

Connect navigation to your routing:

```typescript
const navigationItems = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Trade History', href: '/trade-history', icon: History },
  { label: 'Strategy', href: '/strategy', icon: Target },
  { label: 'Settings', href: '/settings', icon: Settings },
]

// Mark current route as active
navigationItems.forEach(item => {
  item.isActive = currentPath === item.href
})
```

**User Menu:**

The user menu expects:
- User name (required)
- Avatar URL (optional — shows initials if not provided)
- Logout callback

Example integration:
```typescript
const user = {
  name: currentUser.name,
  avatarUrl: currentUser.avatarUrl, // optional
}

function handleLogout() {
  // Clear session, redirect to login
}

<AppShell
  navigationItems={navigationItems}
  user={user}
  onNavigate={(href) => router.push(href)}
  onLogout={handleLogout}
>
  {children}
</AppShell>
```

## Files to Reference

- `product-plan/design-system/` — Design tokens
- `product-plan/data-model/` — Type definitions
- `product-plan/shell/README.md` — Shell design intent
- `product-plan/shell/components/` — Shell React components

## Done When

- [ ] Design tokens are configured (Tailwind colors, fonts loaded)
- [ ] Data model types are defined in your project
- [ ] Routes exist for all sections (can be placeholder pages)
- [ ] Shell renders with navigation
- [ ] Navigation links to correct routes
- [ ] User menu shows user info
- [ ] Logout works
- [ ] Responsive on mobile (sidebar collapses to hamburger menu)
- [ ] Light and dark mode both work

---

# Milestone 2: Dashboard

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

---

# Milestone 3: Trade History

## Goal

Implement the Trade History feature - comprehensive analytics and filtering for all closed trades.

## Overview

The Trade History section provides comprehensive visibility into trading performance with detailed analytics, filtering capabilities, and a sortable table of all closed trades. Users can analyze performance metrics, filter trades by various criteria, view cumulative P&L trends, and drill into individual trade details to understand their trading patterns and profitability. This section is essential for users to review and learn from their trading history.

**Key Functionality:**
- View aggregate performance metrics (total P&L with ROI, win rate, average profit, best/worst trades)
- Analyze cumulative P&L chart showing profit trajectory over time
- Filter trades by time period, status, profit/loss, entry price range, duration, and quantity
- Search for specific trades by order ID or TP order ID
- Sort trades table by any column (date, prices, P&L, duration)
- View detailed trade information in modal (timeline, fees breakdown, TP adjustment history)
- Paginate through large trade histories (50 trades per page)
- Manage active filters with visual badges and quick clear options

## Recommended Approach: Test-Driven Development

Before implementing this section, **write tests first** based on the test specifications provided.

See `product-plan/sections/trade-history/tests.md` for detailed test-writing instructions including:
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

Copy the section components from `product-plan/sections/trade-history/components/`:

- `TradeHistory.tsx` - Main container component orchestrating all trade history sections
- `PeriodSelector.tsx` - Time range filter (today/7days/30days/custom with date picker)
- `PerformanceCards.tsx` - Analytics cards showing total P&L, win rate, averages, best/worst trades
- `PnlChart.tsx` - Cumulative P&L line chart with time range controls
- `Filters.tsx` - Filter panel with status, profit/loss, advanced filters, and search
- `FilterBadges.tsx` - Active filter tags with remove buttons and clear all option
- `TradesTable.tsx` - Sortable table of trades with pagination
- `TradeDetailsModal.tsx` - Full trade details including timeline, fees, TP adjustment history

### Data Layer

The components expect these data shapes (see `types.ts`):

**Trade:**
- Core data: order ID, TP order ID, symbol, side (LONG/SHORT), leverage
- Prices: entry price, exit price, quantity
- P&L: profit/loss in dollars and percentage
- Status: CLOSED or OPEN
- Timestamps: opened, filled, closed, duration in seconds
- Fees: trading fee, funding fee, net P&L after fees
- TP adjustments: array of TP changes with timestamp, old/new values, and reason

**PerformanceMetrics:**
- Aggregate stats: total P&L, ROI percentage, total trades count
- Win/loss breakdown: winning trades count, losing trades count, win rate percentage
- Averages: average profit per trade
- Highlights: best trade (ID, P&L, date) and worst trade (ID, P&L, date)

**CumulativePnlDataPoint:**
- Time-series data for chart: date and cumulative P&L at that date

**TradeFilters:**
- Period filter: today/7days/30days/custom with optional date range
- Status filter: all/closed/open
- Profit filter: all/profitable/losses
- Advanced filters: entry price range, duration range, quantity range
- Search query: order ID or TP order ID

**SortConfig:**
- Column: which column to sort by (closedAt, entryPrice, exitPrice, quantity, pnl, pnlPercent, duration)
- Direction: asc or desc

You'll need to:
- Create API endpoint to fetch all trades with filtering, sorting, and pagination support
- Implement backend logic to calculate performance metrics based on filtered trades
- Generate cumulative P&L time-series data for chart
- Store trade data including full timeline (opened, filled, closed timestamps)
- Track TP adjustments for each trade with reasons
- Calculate and store fees (trading fees, funding fees)
- Support search by order ID or TP order ID
- Implement efficient pagination for large trade histories

### Callbacks

Wire up these user actions:

| Callback | Description | Implementation Notes |
|----------|-------------|---------------------|
| `onPeriodChange` | Called when user changes time period (today/7days/30days/custom with optional date range) | Refetch trades and performance metrics filtered by the selected time period. For custom period, date range object includes startDate and endDate. |
| `onFiltersChange` | Called when user updates any filter criteria (status, profit/loss, price ranges, search) | Apply filters on backend and refetch trades. Update performance metrics to reflect filtered data. Filters object contains all active filter values. |
| `onSortChange` | Called when user clicks a column header to sort (passes column name and direction) | Re-sort trades data by specified column and direction. Can be done client-side if all trades are loaded, or server-side for better performance with large datasets. |
| `onViewTradeDetails` | Called when user clicks a trade row to view full details (passes trade ID) | Fetch complete trade details including full timeline, all TP adjustments, and fees breakdown. Open TradeDetailsModal with the data. |
| `onSearch` | Called when user searches by order ID or TP order ID | Query trades by order ID field. Return matching trade(s). Update table and performance metrics. |
| `onClearFilters` | Called when user clicks "Clear all filters" link | Reset all filter values to defaults. Refetch trades without filters. Update UI to show all trades. |
| `onRemoveFilter` | Called when user clicks X on a filter badge to remove specific filter (passes filter key) | Remove only the specified filter while keeping others active. Refetch trades with updated filters. |
| `onPageChange` | Called when user navigates to a different page in pagination | Fetch next/previous page of trades (e.g., trades 51-100). Update pagination display. |

### Empty States

Implement empty state UI for when no records exist yet:

- **No trades yet (first-time user):** Show message "No trades yet" with subtext "Closed trades will appear here after your bot completes positions". Performance cards show zeros or "N/A". Chart shows empty state.
- **No trades match filters:** Show message "No results found" with subtext "Try adjusting your filters". Display "Clear filters" link prominently. Filter badges remain visible to show what's active.
- **Search returns no results:** Show "No results found" with suggestion "Try a different order ID or clear your search". Search badge shows query with X to remove.

The provided components include empty state designs - make sure to render them when data is empty rather than showing blank screens.

## Files to Reference

- `product-plan/sections/trade-history/README.md` - Feature overview and design intent
- `product-plan/sections/trade-history/tests.md` - Test-writing instructions (use for TDD)
- `product-plan/sections/trade-history/components/` - React components
- `product-plan/sections/trade-history/types.ts` - TypeScript interfaces
- `product-plan/sections/trade-history/sample-data.json` - Test data
- `product-plan/sections/trade-history/screenshot.png` - Visual reference

## Expected User Flows

When fully implemented, users should be able to complete these flows:

### Flow 1: View Overall Trading Performance

1. User navigates to `/trade-history`
2. User sees performance analytics cards at top showing total P&L, win rate, average profit, best/worst trades
3. User sees cumulative P&L chart visualizing profit trajectory
4. User sees trades table with recent trades listed
5. User observes pagination showing total trade count
6. **Outcome:** User gets comprehensive overview of their trading performance with key metrics at a glance

### Flow 2: Filter Trades by Profitability

1. User sees filter panel with Profit/Loss filter
2. User clicks "Profitable only" option
3. Filter badge appears: "Profit: Profitable"
4. Trades table refreshes showing only winning trades
5. Performance metrics update to reflect only profitable trades
6. **Outcome:** User can focus analysis on successful trades to understand what worked

### Flow 3: Search for a Specific Trade by Order ID

1. User enters order ID "12345678" into search field
2. User presses Enter
3. Search badge appears: "Search: 12345678"
4. Trades table shows only the matching trade
5. Performance metrics update for that single trade
6. **Outcome:** User quickly finds the specific trade they were looking for

### Flow 4: Sort Trades by P&L to Find Best Performers

1. User sees trades table with default date sorting
2. User clicks "P&L ($)" column header
3. Sort indicator appears (down arrow) on P&L column
4. Trades re-sort with highest P&L trades at top
5. User can see their most profitable trades first
6. **Outcome:** User identifies their best-performing trades for analysis

### Flow 5: View Detailed Trade Information

1. User sees a profitable trade in the table: "+$150 (+1.58%)"
2. User clicks the trade row
3. Trade Details Modal opens showing:
   - Order IDs, symbol, side, leverage
   - Entry/exit prices, quantity, P&L
   - Timeline: opened, filled, closed timestamps with duration
   - TP adjustment history (if any adjustments were made)
   - Fees breakdown: trading fee, funding fee, net P&L
4. User reviews all details
5. User clicks "Close" to dismiss modal
6. **Outcome:** User understands complete trade lifecycle including fees and TP adjustments

### Flow 6: Clear All Active Filters

1. User has applied multiple filters: Status = "Closed", Profit = "Profitable", Entry Price = "$90k-$95k"
2. Three filter badges are visible
3. User clicks "Clear all filters" link
4. All badges disappear
5. Trades table refreshes to show all trades (unfiltered)
6. Performance metrics update to show all-time stats
7. **Outcome:** User quickly resets to full view after focused analysis

## Done When

- [ ] Tests written for key user flows (success and failure paths)
- [ ] All tests pass
- [ ] Trade History component renders with real trade data
- [ ] Performance Cards display accurate aggregate metrics (P&L, ROI, win rate, averages, best/worst)
- [ ] Cumulative P&L Chart visualizes profit trajectory over time
- [ ] Period selector filters trades and metrics by time period (today/7days/30days/custom)
- [ ] Status filter (all/closed/open) works correctly
- [ ] Profit/Loss filter (all/profitable/losses) works correctly
- [ ] Advanced filters (entry price, duration, quantity ranges) work correctly
- [ ] Search by order ID finds and displays matching trade(s)
- [ ] Filter badges show active filters with remove buttons
- [ ] "Clear all filters" clears all active filters at once
- [ ] Removing individual filter badge updates results correctly
- [ ] Trades table columns are sortable (clicking header sorts, clicking again toggles direction)
- [ ] Clicking trade row opens Trade Details Modal with complete information
- [ ] Trade Details Modal shows timeline, fees breakdown, and TP adjustment history
- [ ] Pagination works for large trade histories (50 per page)
- [ ] Empty states display properly when no trades exist or no trades match filters
- [ ] First-time user sees helpful empty state with zeros/N/A in metrics
- [ ] Filtered empty state suggests adjusting filters with clear option
- [ ] Color coding works (green for profits, red for losses)
- [ ] All user actions work end-to-end
- [ ] Matches the visual design
- [ ] Responsive on mobile, tablet, and desktop

---

# Milestone 4: Strategy

## Goal

Implement the Strategy feature - comprehensive control over bot trading configuration and execution.

## Overview

The Strategy section provides comprehensive control over bot trading configuration including risk parameters, grid settings, MACD filters, and execution controls. Users can view current strategy status, adjust position sizing and leverage, configure grid spacing and take profit targets, enable MACD-based activation filters, and start/stop/pause strategy execution with real-time risk calculations and validation. This is a critical section where users configure how their bot will trade.

**Key Functionality:**
- View current strategy status and cycle performance (P&L, trades, win rate since activation)
- Execute strategy controls (start/pause/stop/resume) with confirmation dialogs
- Configure risk parameters (position size, max total orders, leverage 1-125x, margin mode)
- View real-time risk calculations (total capital at risk, liquidation risk, max loss per trade)
- Configure grid settings (spacing type fixed/percentage, spacing value, grid range, take profit)
- Preview grid price levels based on current BTC price and settings
- Enable/disable MACD filter with configurable parameters (fast/slow/signal periods, timeframe)
- Configure advanced settings (dynamic TP based on funding rate, auto-reactivation mode)
- Validate configuration with in-context warnings and helpful tooltips

## Recommended Approach: Test-Driven Development

Before implementing this section, **write tests first** based on the test specifications provided.

See `product-plan/sections/strategy/tests.md` for detailed test-writing instructions including:
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

Copy the section components from `product-plan/sections/strategy/components/`:

- `Strategy.tsx` - Main container component orchestrating all strategy sections
- `StrategyStatusCard.tsx` - Status display with cycle metrics and control buttons (start/pause/stop/resume)
- `RiskParametersSection.tsx` - Position size, max orders, leverage slider (1-125x), margin mode with live risk summary card
- `GridSettingsSection.tsx` - Grid spacing configuration, range, take profit with grid preview showing actual price levels
- `MACDFilterSection.tsx` - MACD enable/disable toggle, parameter inputs (fast/slow/signal periods), timeframe selector with explanations
- `AdvancedSettingsSection.tsx` - Dynamic TP configuration and auto-reactivation mode (collapsible for advanced users)

### Data Layer

The components expect these data shapes (see `types.ts`):

**Strategy:**
- Status and context: current execution state (active/paused/stopped/wait) with explanation
- Cycle metrics: started timestamp, P&L since activation, trades count, win rate
- Risk parameters: position size (USDT), max total orders, leverage (1-125x), margin mode (crossed/isolated)
- Grid settings: spacing type (fixed/percentage), spacing value, grid range (±%), take profit (%), grid anchor
- MACD filter: enabled flag, fast/slow/signal periods, timeframe (15m/1h/4h/1d)
- Advanced settings: dynamic TP config (enabled, base/min/max TP, safety margin, check interval), auto-reactivation mode
- Last updated timestamp

**CurrentMarket:**
- Current BTC price (for grid preview and risk calculations)
- Current funding rate (for dynamic TP calculations)
- Last update timestamp

**RiskSummary:**
- Total capital at risk (position size × max orders)
- Capital per position (same as position size)
- Liquidation risk level (low/medium/high based on leverage)
- Max loss per trade in dollars and percentage

**GridLevel:**
- Level number (negative for buy levels, positive for sell levels, 0 for current price)
- Price at this level
- Type (buy/sell/current)
- Distance from current price (percentage)

You'll need to:
- Create API endpoints to fetch and update strategy configuration
- Implement backend logic to calculate risk summary based on current settings
- Generate grid preview levels based on spacing type, value, range, and current BTC price
- Store strategy configuration persistently
- Implement bot control actions (start/pause/stop/resume) with state management
- Validate configuration before allowing strategy start (minimum values, logical constraints)
- Track cycle metrics (P&L, trades, win rate since activation)
- Fetch real-time BTC price and funding rate for calculations
- Implement dynamic TP adjustment logic if feature is enabled
- Manage MACD signal calculations for activation filtering

### Callbacks

Wire up these user actions:

| Callback | Description | Implementation Notes |
|----------|-------------|---------------------|
| `onStart` | Called when user confirms starting the strategy | Validate configuration first. If MACD filter enabled, bot enters WAIT state until bullish signal. Otherwise goes to ACTIVE. Initialize cycle metrics. |
| `onPause` | Called when user confirms pausing the strategy | Stop placing new orders, but keep existing positions open. Active orders remain. Update status to PAUSED. |
| `onStop` | Called when user confirms stopping the strategy | Cancel all pending orders, keep positions until take-profit triggers. Update status to STOPPED. Reset cycle metrics. |
| `onResume` | Called when user confirms resuming a paused strategy | Return to previous state (ACTIVE or WAIT). Resume placing orders based on grid settings. |
| `onUpdateRiskParameters` | Called when user changes risk parameters (position size, max orders, leverage, margin mode) | Validate inputs (position size >= $5, leverage 1-125, etc.). Recalculate risk summary. Update UI in real-time. Don't persist until user clicks Save. |
| `onUpdateGridSettings` | Called when user changes grid settings (spacing type/value, grid range, take profit, anchor) | Validate inputs (spacing > 0, TP > 0, grid range reasonable). Regenerate grid preview. Warn if TP too low relative to fees. |
| `onUpdateMACDFilter` | Called when user enables/disables MACD filter or changes MACD parameters | Validate MACD parameters (fast < slow, all > 0). Warn if disabling filter (continuous trading risk). |
| `onUpdateAdvancedSettings` | Called when user changes advanced settings (dynamic TP config, auto-reactivation mode) | Validate dynamic TP ranges (min <= base <= max). Update settings. |
| `onSave` | Called when user clicks save button to persist all strategy changes | Validate entire configuration. Persist to database. Show success/error notification. Clear unsaved changes indicator. |

### Empty States

Implement empty state UI for when no records exist yet:

- **No strategy configured (first-time user):** Show default/recommended values in form fields:
  - Position size: $50 (or conservative starting value)
  - Leverage: 5x (safer for beginners)
  - Grid spacing: 1% or $500
  - Take profit: 1.5%
  - MACD enabled by default
  - Helpful onboarding message: "Configure your strategy settings and click Start to begin trading"
  - Once minimum valid configuration exists, "Start" button becomes enabled

The provided components include helpful states for first-time configuration.

## Files to Reference

- `product-plan/sections/strategy/README.md` - Feature overview and design intent
- `product-plan/sections/strategy/tests.md` - Test-writing instructions (use for TDD)
- `product-plan/sections/strategy/components/` - React components
- `product-plan/sections/strategy/types.ts` - TypeScript interfaces
- `product-plan/sections/strategy/sample-data.json` - Test data
- `product-plan/sections/strategy/screenshot.png` - Visual reference

## Expected User Flows

When fully implemented, users should be able to complete these flows:

### Flow 1: View Current Strategy Configuration and Status

1. User navigates to `/strategy`
2. User sees Strategy Status Card showing current status (active/paused/stopped/wait) with cycle metrics
3. User sees Risk Parameters section with current position size, leverage, margin mode
4. User sees Risk Summary card showing total capital at risk and liquidation risk indicator
5. User sees Grid Settings with current spacing, range, and TP configuration
6. User sees Grid Preview showing actual price levels around current BTC price
7. User sees MACD Filter status and parameters
8. **Outcome:** User has complete visibility into how their bot is configured and performing

### Flow 2: Adjust Position Size and View Real-Time Risk Calculations

1. User sees current position size: $100, leverage: 10x
2. User changes position size to $200
3. Risk Summary card updates immediately: Total capital increases to $4,000 (200 × 20 orders)
4. User adjusts leverage slider to 25x
5. Liquidation Risk indicator changes to red with warning: "High leverage increases liquidation risk"
6. Max Loss Per Trade value updates
7. **Outcome:** User understands risk implications of their configuration changes in real-time

### Flow 3: Configure Grid Settings and Preview Price Levels

1. User changes Spacing Type from "Fixed $" to "Percentage %"
2. User enters 0.5% spacing value
3. User sets Grid Range to ±3%
4. Grid Preview updates showing buy and sell levels around current BTC price
5. User sees approximately 12 levels (6 buy orders below price, 6 sell orders above)
6. User sets Take Profit to 1.5%
7. User clicks "Save" to persist changes
8. **Outcome:** User has configured optimal grid spacing for current market conditions with visual confirmation

### Flow 4: Enable MACD Filter for Safer Activation

1. User sees MACD Filter section with toggle OFF
2. User reads explanation: "When disabled, bot trades continuously without MACD signal confirmation"
3. User toggles MACD ON
4. MACD parameter inputs appear: Fast 12, Slow 26, Signal 9
5. User selects Timeframe: 1h
6. Warning appears: "Bot will only activate when MACD shows bullish signal"
7. User clicks "Save"
8. **Outcome:** Strategy is configured to wait for bullish MACD signal before activating, reducing risk

### Flow 5: Start Strategy with MACD Wait State

1. User has configured strategy with MACD filter enabled
2. User sees "Start" button in Strategy Status Card
3. User clicks "Start"
4. Confirmation dialog appears: "Bot will wait for MACD bullish signal before activating. Are you sure?"
5. User confirms
6. Strategy status updates to "WAIT" with gray badge
7. Status context: "Waiting for MACD bullish signal to activate"
8. Control buttons update to show "Pause" and "Stop" options
9. **Outcome:** Bot is running but waiting for safe entry signal, not placing orders yet

### Flow 6: Pause Active Strategy to Prevent New Orders

1. User sees strategy status "ACTIVE" with ongoing trades
2. User clicks "Pause" button
3. Confirmation dialog: "Pausing will stop new orders but keep existing positions open"
4. User confirms
5. Status updates to "PAUSED" with yellow badge
6. New orders stop, existing positions remain until take-profit
7. **Outcome:** User has temporarily halted new trading activity while preserving current positions

## Done When

- [ ] Tests written for key user flows (success and failure paths)
- [ ] All tests pass
- [ ] Strategy component renders with real configuration data
- [ ] Strategy Status Card displays current status, cycle metrics, and appropriate control buttons
- [ ] Risk Parameters section allows adjusting position size, max orders, leverage (1-125x), and margin mode
- [ ] Risk Summary card calculates and displays in real-time: total capital, liquidation risk, max loss
- [ ] Risk Summary updates immediately as user adjusts risk parameters (no delay)
- [ ] Liquidation risk indicator changes color based on leverage (green <10x, yellow 10-25x, red >25x)
- [ ] Grid Settings section allows configuring spacing type (fixed/percentage), value, range, and TP
- [ ] Grid Preview displays actual price levels based on current BTC price and settings
- [ ] Grid Preview updates in real-time as user changes spacing or range
- [ ] MACD Filter toggle enables/disables MACD activation requirement
- [ ] MACD parameters (fast/slow/signal periods, timeframe) are configurable
- [ ] Advanced Settings section (collapsible) includes Dynamic TP and Auto-Reactivation options
- [ ] Start action validates configuration and enters WAIT or ACTIVE state appropriately
- [ ] Pause action stops new orders, keeps positions, shows confirmation dialog
- [ ] Stop action cancels orders, keeps positions until TP, shows confirmation dialog
- [ ] Resume action returns paused strategy to active state
- [ ] Save action persists all configuration changes to backend
- [ ] Validation warnings appear for invalid inputs (too small position size, invalid MACD params, etc.)
- [ ] In-context warnings for risky settings (high leverage, low TP below fees)
- [ ] Tooltips provide helpful explanations for all settings
- [ ] First-time user sees default/recommended values with clear path to start trading
- [ ] All user actions work end-to-end
- [ ] Matches the visual design
- [ ] Responsive on mobile, tablet, and desktop

---

# Milestone 5: Settings

## Goal

Implement the Settings feature - system-level configuration including exchange account management, bot state configuration, and system information.

## Overview

The Settings section provides system-level configuration management including BingX account connections, bot state configuration, and system information. Users can manage multiple exchange accounts (demo/live), configure bot behavior settings that are currently environment variables, and view version and uptime information across three organized tabs. This section enables users to safely manage their trading infrastructure.

**Key Functionality:**
- View all connected BingX accounts with status, mode (demo/live), and connection indicators
- Add new BingX accounts via modal with API key/secret and mode selection
- Test connection to validate API credentials with BingX exchange
- Edit existing account credentials securely (API key/secret masked)
- Set active account to switch which account the bot uses for trading
- Remove accounts with confirmation dialogs
- View and update bot state configuration (restore max age, load history on start toggle, history limit)
- View system version information (Btcbot, backend, database versions)
- View uptime metrics (bot running time, last restart timestamp)

## Recommended Approach: Test-Driven Development

Before implementing this section, **write tests first** based on the test specifications provided.

See `product-plan/sections/settings/tests.md` for detailed test-writing instructions including:
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

Copy the section components from `product-plan/sections/settings/components/`:

- `Settings.tsx` - Main container with tab navigation (Accounts/System/About)
- `AccountCard.tsx` - Individual account display with mode badge, connection status, masked credentials, action buttons
- `AddAccountModal.tsx` - Form to add new BingX account (API key/secret, demo/live mode)
- `EditAccountModal.tsx` - Form to edit existing account credentials
- `ConfirmDialog.tsx` - Reusable confirmation for account removal and active account changes

### Data Layer

The components expect these data shapes (see `types.ts`):

**Account:**
- ID, exchange name ("BingX" for MVP)
- Mode: demo or live
- API key and masked API secret (for security, only last 4 chars of secret visible)
- Connection status: connected/disconnected/testing
- Active flag: indicates which account bot is currently using
- Created and last tested timestamps

**SystemConfig:**
- Restore max age (hours): how old state can be when restoring from database
- Load history on start (boolean): whether to load trade history when bot starts
- History limit (number): maximum trades to load

**SystemInfo:**
- Versions: Btcbot version, backend (Python) version, database (PostgreSQL) version
- Uptime: bot running time (human-readable), last restart timestamp

You'll need to:
- Create API endpoints to manage accounts (list, add, edit, test connection, set active, remove)
- Store account credentials securely (encrypt API secrets in database)
- Implement connection testing by calling BingX API to validate credentials
- Ensure only one account can be active at a time
- Prevent removing the active account (require user to set another as active first)
- Create API endpoints to get and update system configuration
- Store system config persistently (database or configuration file)
- Create endpoint to fetch system info (versions from build/env, uptime from runtime)
- Implement security checks: only account owner can manage their accounts

### Callbacks

Wire up these user actions:

| Callback | Description | Implementation Notes |
|----------|-------------|---------------------|
| `onAddAccount` | Called when user submits new account form (passes account data without ID or timestamps) | Validate API key/secret format. Store credentials securely (encrypt secret). Test connection optionally. Add account to database. Return new account with ID. |
| `onTestConnection` | Called when user clicks "Test Connection" to validate API credentials (passes account ID) | Fetch account credentials from database (decrypt secret). Make test API call to BingX (e.g., fetch account balance or info). Update connection status based on result. Return success/failure. |
| `onEditAccount` | Called when user saves edited account credentials (passes account ID and updated fields) | Validate new credentials. Update account in database (re-encrypt secret if changed). Optionally re-test connection. Return success/failure. |
| `onSetActiveAccount` | Called when user clicks "Set Active" to switch trading to this account (passes account ID) | Check if bot is currently running (if yes, warn or block). Set all accounts' isActive to false. Set specified account's isActive to true. Update bot to use new account credentials. Return success. |
| `onRemoveAccount` | Called when user confirms account deletion (passes account ID) | Check if account is active (if yes, block removal with error message). Delete account from database. Return success. |
| `onUpdateSystemConfig` | Called when user changes bot state configuration (passes complete config object) | Validate config values (restore max age > 0, history limit > 0). Update configuration in database or config file. Apply changes to bot runtime if applicable. Return success/failure. |

### Empty States

Implement empty state UI for when no records exist yet:

- **No accounts configured (first-time user):** Show message "No accounts configured" with subtext "Add a BingX account to start trading". "Add Account" button is prominent. No account cards displayed.

The provided components include empty state designs for accounts tab.

## Files to Reference

- `product-plan/sections/settings/README.md` - Feature overview and design intent
- `product-plan/sections/settings/tests.md` - Test-writing instructions (use for TDD)
- `product-plan/sections/settings/components/` - React components
- `product-plan/sections/settings/types.ts` - TypeScript interfaces
- `product-plan/sections/settings/sample-data.json` - Test data
- `product-plan/sections/settings/screenshot.png` - Visual reference

## Expected User Flows

When fully implemented, users should be able to complete these flows:

### Flow 1: Add New BingX Account for Trading

1. User navigates to `/settings` (opens on Accounts tab by default)
2. User clicks "Add Account" button
3. Add Account Modal opens with form fields
4. User enters BingX API Key and API Secret (secret field is masked)
5. User selects Mode: "Demo" or "Live" via radio buttons
6. User clicks "Add" button
7. Backend validates credentials and stores account securely
8. Modal closes, success notification appears
9. New account card appears in the accounts list showing masked credentials
10. **Outcome:** User has successfully configured a trading account for the bot to use

### Flow 2: Test Connection to Verify Credentials

1. User sees account card for their BingX account
2. User clicks "Test Connection" button
3. Button shows loading state: "Testing..."
4. Backend makes test API call to BingX to verify credentials
5. Connection succeeds, success notification appears: "✅ Connection successful"
6. Account card updates connection status to "Connected" with timestamp
7. **Outcome:** User has verified their API credentials are valid and working

### Flow 3: Edit Account Credentials

1. User clicks "Edit" button on an account card
2. Edit Account Modal opens pre-filled with current API key and masked secret
3. User updates API Key to new value
4. User enters new API Secret (field shows masked input)
5. User clicks "Save"
6. Backend validates and updates credentials in database
7. Modal closes, success notification: "Account updated successfully"
8. Account card reflects updated information
9. **Outcome:** User has safely updated their exchange API credentials

### Flow 4: Switch Active Account for Trading

1. User has 2 accounts configured: Account 1 (Demo, currently active), Account 2 (Live, inactive)
2. User wants to switch bot to trade on Account 2
3. User clicks "Set Active" button on Account 2 card
4. Confirmation dialog appears: "Switching active account will change which account the bot uses for trading. Are you sure?"
5. User clicks "Confirm"
6. Backend sets Account 2 as active, Account 1 as inactive
7. Account 2 card now shows "ACTIVE" badge
8. Account 1 "ACTIVE" badge is removed, "Set Active" button appears
9. Success notification: "Active account changed"
10. **Outcome:** Bot will now trade using Account 2 credentials

### Flow 5: Remove Unused Account

1. User has Account 3 that is no longer needed (not active)
2. User clicks "Remove" button on Account 3 card
3. Confirmation dialog appears: "Are you sure you want to remove this account? This action cannot be undone."
4. User clicks "Confirm"
5. Backend deletes account from database
6. Account 3 card disappears from list
7. Success notification: "Account removed"
8. **Outcome:** Unused account has been safely deleted

### Flow 6: Update Bot State Configuration

1. User clicks "System" tab in settings
2. User sees Bot State Config section with current settings
3. User changes "Restore Max Age" from 24 to 48 hours
4. User toggles "Load History on Start" to OFF
5. User changes "History Limit" from 100 to 200 trades
6. User clicks "Save" (or changes auto-save)
7. Backend validates and updates configuration
8. Success notification: "Configuration updated"
9. **Outcome:** Bot behavior settings have been updated

### Flow 7: View System Version and Uptime Information

1. User clicks "About" tab in settings
2. User sees Version Info section displaying:
   - Btcbot version: v1.2.3
   - Backend: Python 3.11
   - Database: PostgreSQL 15.2
3. User sees Uptime section displaying:
   - Bot running time: 3 days 5 hours
   - Last restart: Jan 1, 2025 10:00 AM
4. **Outcome:** User can check version for troubleshooting and monitor bot uptime

## Done When

- [ ] Tests written for key user flows (success and failure paths)
- [ ] All tests pass
- [ ] Settings page renders with tab navigation (Accounts, System, About)
- [ ] Accounts tab displays all configured accounts as cards
- [ ] Each account card shows: exchange name, mode badge (Demo/Live), connection status, masked API key, created date, active badge (if active), action buttons
- [ ] "Add Account" button opens Add Account Modal
- [ ] Add Account Modal allows entering API key, API secret (masked), selecting mode, and saving
- [ ] New accounts are validated and stored securely (API secret encrypted)
- [ ] "Test Connection" validates API credentials with BingX and updates status
- [ ] "Edit" opens Edit Account Modal pre-filled with current data
- [ ] Editing account updates credentials securely
- [ ] "Set Active" switches active account with confirmation dialog
- [ ] Only one account can be active at a time
- [ ] Active account is clearly indicated with badge
- [ ] "Remove" deletes account after confirmation
- [ ] Cannot remove active account (must set another as active first)
- [ ] System tab displays Bot State Config with editable fields (restore max age, load history toggle, history limit)
- [ ] System config changes are validated and saved
- [ ] About tab displays read-only system info: versions (Btcbot, backend, database) and uptime (running time, last restart)
- [ ] Empty state shows when no accounts configured: helpful message and prominent "Add Account" button
- [ ] All confirmation dialogs work correctly (account removal, set active)
- [ ] API secrets are masked in UI (show only last 4 characters of API key, hide secret entirely)
- [ ] Success/error notifications appear for all actions
- [ ] Loading states appear during async operations (test connection, add/edit/remove account)
- [ ] All user actions work end-to-end
- [ ] Matches the visual design
- [ ] Responsive on mobile, tablet, and desktop
