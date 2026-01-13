# Milestone 3: Trade History

> **Provide alongside:** `product-overview.md`
> **Prerequisites:** Milestone 1 (Foundation) complete, Milestone 2 (Dashboard) complete

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
