# Test Instructions: Trade History

These test-writing instructions are **framework-agnostic**. Adapt them to your testing setup (Jest, Vitest, Playwright, Cypress, React Testing Library, RSpec, Minitest, PHPUnit, etc.).

## Overview

The Trade History section provides comprehensive analytics and detailed filtering for all closed trades. Users can view performance metrics, analyze cumulative P&L trends, filter and sort trades, search by order ID, and drill into individual trade details. Tests should verify that users can effectively analyze their trading performance and find specific trades quickly.

---

## User Flow Tests

### Flow 1: View Trade History Overview with Performance Analytics

**Scenario:** User opens trade history to review their overall trading performance

#### Success Path

**Setup:**
- User is authenticated
- User has trade history with at least 10 closed trades
- Overall metrics: Total P&L = `$1,250.50`, Total Trades = `45`, Winning = `30`, Losing = `15`, Win Rate = `66.7%`
- Best trade: `$250`, Worst trade: `-$85`
- Cumulative P&L data available for chart

**Steps:**
1. User navigates to `/trade-history` route
2. Page loads with performance analytics at top
3. User sees cumulative P&L chart
4. User sees trades table with paginated results
5. User observes period selector showing default selection

**Expected Results:**
- [ ] Performance Cards section renders with 6 cards:
  - Total P&L card shows "$1,250.50" with ROI percentage in green
  - Total Trades card shows "45"
  - Win Rate card shows "66.7%" with visual indicator (e.g., "30 wins / 15 losses")
  - Average Profit card shows average profit per trade
  - Best Trade card shows "$250.00" with date
  - Worst Trade card shows "-$85.00" with date in red
- [ ] All positive metrics (P&L, best trade) are displayed in green
- [ ] Negative metrics (worst trade) are displayed in red
- [ ] Cumulative P&L Chart renders as a line chart showing profit trajectory
- [ ] Chart has time range controls (e.g., 7D, 30D, All)
- [ ] Trades Table renders with column headers: Date/Time, Entry Price, Exit Price, Quantity, P&L ($), P&L (%), Duration, Status, View Details
- [ ] At least 10 trade rows are visible (or up to page limit, e.g., 50)
- [ ] Pagination shows "Showing 1-45 of 45 trades" (or similar based on data)
- [ ] Period selector shows default selection (e.g., "30 Days")

#### Failure Path: No Trade History Available

**Setup:**
- User has never closed any trades (new user or bot hasn't completed trades yet)

**Steps:**
1. User navigates to `/trade-history`

**Expected Results:**
- [ ] Performance Cards show zeros: "$0.00" for P&L, "0" for total trades, "N/A" or "0%" for win rate
- [ ] Best/Worst trade cards show "N/A" or "-" (no data available)
- [ ] Cumulative P&L Chart shows empty state or message: "No data to display"
- [ ] Trades Table shows empty state message: "No trades yet"
- [ ] Empty state includes helpful text: "Closed trades will appear here after your bot completes positions"
- [ ] No broken layouts or errors

#### Failure Path: API Error Loading Trades

**Setup:**
- Backend API fails with 500 error when fetching trades

**Steps:**
1. User navigates to `/trade-history`
2. API returns error

**Expected Results:**
- [ ] Error message appears: "Unable to load trade history. Please try again."
- [ ] User sees a "Retry" button or refresh option
- [ ] Performance cards may show loading skeletons or error states
- [ ] UI doesn't crash

---

### Flow 2: Filter Trades by Status (Closed vs Open)

**Scenario:** User wants to view only closed trades (not open positions)

#### Success Path

**Setup:**
- Trade history includes both closed trades and open positions
- Closed trades: 40, Open trades: 5
- Default filter shows "All"

**Steps:**
1. User is on trade history page
2. User sees filter panel or filter dropdown
3. User clicks "Status" filter
4. User sees options: "All", "Closed", "Open"
5. User selects "Closed"
6. Trades table refreshes

**Expected Results:**
- [ ] Status filter updates to show "Closed" as selected
- [ ] Active filter badge appears showing "Status: Closed" with X button
- [ ] `onFiltersChange` callback is called with `{ status: 'closed' }`
- [ ] Trades table refreshes showing only closed trades
- [ ] Performance metrics update to reflect only closed trades
- [ ] Pagination updates: "Showing 1-40 of 40 trades"
- [ ] No open positions appear in the table

#### Failure Path: Filter Returns No Results

**Setup:**
- User applies filter that matches no trades (e.g., filters for "Open" but all trades are closed)

**Steps:**
1. User selects "Open" in status filter
2. No trades match this criteria

**Expected Results:**
- [ ] Trades table shows empty state: "No results found"
- [ ] Helpful message: "Try adjusting your filters"
- [ ] "Clear filters" link or button is visible
- [ ] Performance cards show zeros (since no trades match)
- [ ] Filter badge shows "Status: Open" (filter is active even though no results)

---

### Flow 3: Search for a Specific Trade by Order ID

**Scenario:** User wants to find a specific trade using its order ID

#### Success Path

**Setup:**
- Trade with order ID `12345678` exists in the history

**Steps:**
1. User sees search input field (placeholder: "Search by Order ID")
2. User types "12345678" into the search field
3. User presses Enter or clicks search button

**Expected Results:**
- [ ] Search input shows "12345678"
- [ ] Active filter badge appears: "Search: 12345678" with X button
- [ ] `onSearch` callback is called with query `"12345678"`
- [ ] Trades table updates to show only matching trade(s)
- [ ] If only one trade matches, table shows single row
- [ ] Performance metrics update based on search results (may be just one trade)
- [ ] Pagination shows "Showing 1-1 of 1 trade"

#### Failure Path: Search Query Matches No Trades

**Setup:**
- User searches for order ID that doesn't exist: "99999999"

**Steps:**
1. User enters "99999999" in search field
2. No trades match

**Expected Results:**
- [ ] Trades table shows empty state: "No results found"
- [ ] Suggestion: "Try a different order ID or clear your search"
- [ ] Search filter badge shows "Search: 99999999"
- [ ] "Clear filters" or X button on badge allows removing search
- [ ] Performance cards show zeros

---

### Flow 4: Sort Trades Table by Column

**Scenario:** User wants to sort trades by P&L to see most profitable trades first

#### Success Path

**Setup:**
- Trades table is displayed with multiple trades
- Default sort: Date/Time descending (newest first)

**Steps:**
1. User sees trades table with sortable column headers
2. User clicks "P&L ($)" column header
3. Table re-sorts to show highest P&L trades first

**Expected Results:**
- [ ] "P&L ($)" column header shows sort indicator (down arrow for descending)
- [ ] `onSortChange` callback is called with `{ column: 'pnl', direction: 'desc' }`
- [ ] Trades table re-renders with trades sorted by P&L descending
- [ ] Highest profit trade appears at top
- [ ] Clicking same column header again toggles sort direction to ascending
- [ ] Arrow icon toggles from down to up
- [ ] Lowest P&L (biggest loss) now appears at top

#### Success Path: Sort by Entry Price

**Steps:**
1. User clicks "Entry Price" column header
2. Table sorts by entry price ascending

**Expected Results:**
- [ ] Trades sort by entry price, lowest first
- [ ] Sort indicator appears on "Entry Price" column (up arrow)
- [ ] `onSortChange` called with `{ column: 'entryPrice', direction: 'asc' }`

---

### Flow 5: View Detailed Information for a Trade

**Scenario:** User wants to see full details of a specific trade including fees and TP adjustment history

#### Success Path

**Setup:**
- Trade exists with:
  - Order ID: `12345678`, TP Order ID: `87654321`
  - Symbol: `BTC/USDT`, Side: `LONG`, Leverage: `10x`
  - Entry: `$95,000`, Exit: `$96,500`, Quantity: `0.1`
  - P&L: `$150` (+1.58%), Duration: `2h 15m`
  - Fees: Trading fee `$12`, Funding fee `$3`, Net P&L `$135`
  - TP adjustments: 2 adjustments during trade
  - Timeline: Opened at `2025-01-03 10:00`, Filled at `10:05`, Closed at `12:15`

**Steps:**
1. User sees trades table with this trade row
2. User clicks the trade row or "View Details" button
3. Trade Details Modal opens

**Expected Results:**
- [ ] Modal opens centered on screen with heading "Trade Details"
- [ ] **Overview Section** displays:
  - Order ID: "12345678"
  - TP Order ID: "87654321"
  - Symbol: "BTC/USDT"
  - Side: "LONG" badge (green)
  - Leverage: "10x"
- [ ] **Prices & P&L Section** displays:
  - Entry Price: "$95,000.00"
  - Exit Price: "$96,500.00"
  - Quantity: "0.1 BTC"
  - P&L: "+$150.00 (+1.58%)" in green
  - Net P&L (after fees): "+$135.00" in green
- [ ] **Timeline Section** displays:
  - Opened: "Jan 3, 2025 10:00 AM"
  - Filled: "Jan 3, 2025 10:05 AM" (5 minutes later)
  - Closed: "Jan 3, 2025 12:15 PM" (2h 15m total)
  - Duration: "2h 15m"
- [ ] **TP Details Section** displays:
  - TP adjustment history with 2 entries showing old TP, new TP, timestamp, and reason
- [ ] **Fees Breakdown Section** displays:
  - Trading Fee: "$12.00"
  - Funding Fee: "$3.00"
  - Total Fees: "$15.00"
  - Net P&L: "$135.00"
- [ ] Modal has close button (X icon in corner) and/or "Close" button
- [ ] Clicking close or X dismisses modal

#### Failure Path: Trade Details Not Found

**Setup:**
- User clicks a trade but backend can't find details (e.g., ID mismatch or deleted)

**Steps:**
1. User clicks trade row
2. API returns 404 Not Found

**Expected Results:**
- [ ] Modal opens but shows error message: "Trade details not found"
- [ ] User can close modal
- [ ] No crash or broken UI

---

### Flow 6: Apply Multiple Filters and Clear All

**Scenario:** User applies several filters to narrow down trades, then clears all filters at once

#### Success Path

**Setup:**
- User has many trades across different price ranges and durations

**Steps:**
1. User applies Status filter: "Closed"
2. User applies Profit/Loss filter: "Profitable only"
3. User applies Entry Price Range: "$90,000 - $95,000"
4. Active filter badges appear for each filter
5. Trades table shows only trades matching all criteria
6. User clicks "Clear all filters" link

**Expected Results:**
- [ ] After each filter applied, new filter badge appears showing active filter
- [ ] Three badges visible: "Status: Closed", "Profit: Profitable", "Entry: $90k-$95k"
- [ ] Each badge has X button to remove individually
- [ ] Trades table updates after each filter to show matching trades
- [ ] Performance metrics update to reflect filtered data
- [ ] "Clear all filters" link is visible when filters are active
- [ ] Clicking "Clear all filters" calls `onClearFilters` callback
- [ ] All filter badges disappear
- [ ] Trades table refreshes to show all trades (unfiltered)
- [ ] Performance metrics update to show all trades again

#### Success Path: Remove Individual Filter

**Steps:**
1. User has 3 active filters (from above)
2. User clicks X on "Profit: Profitable" badge

**Expected Results:**
- [ ] "Profit: Profitable" badge disappears
- [ ] Other two badges remain: "Status: Closed", "Entry: $90k-$95k"
- [ ] `onRemoveFilter` callback is called with filter key `'profitFilter'`
- [ ] Trades table updates to include both profitable and losing trades (but still within closed status and entry price range)

---

### Flow 7: Paginate Through Large Trade History

**Scenario:** User has 150 closed trades and needs to navigate through pages

#### Success Path

**Setup:**
- Total trades: 150
- Trades per page: 50
- Current page: 1

**Steps:**
1. User sees trades table showing first 50 trades
2. User sees pagination control showing "Showing 1-50 of 150 trades"
3. User clicks "Next" or page number "2"
4. Page 2 loads

**Expected Results:**
- [ ] Pagination shows "Showing 1-50 of 150 trades" initially
- [ ] "Next" button or page "2" button is visible and enabled
- [ ] Clicking next/page 2 calls `onPageChange(2)`
- [ ] Trades table updates to show trades 51-100
- [ ] Pagination updates to "Showing 51-100 of 150 trades"
- [ ] "Previous" button becomes enabled
- [ ] User can navigate to page 3 to see trades 101-150

#### Edge Case: Last Page with Partial Results

**Setup:**
- Page 3 has only 50 trades (trades 101-150)

**Steps:**
1. User navigates to page 3

**Expected Results:**
- [ ] Pagination shows "Showing 101-150 of 150 trades"
- [ ] Table displays 50 rows
- [ ] "Next" button is disabled (no page 4)
- [ ] "Previous" button is enabled

---

## Empty State Tests

Empty states are critical for first-time users and when filters return no results. Test these thoroughly:

### No Trades Yet (First-Time User)

**Scenario:** User has never closed any trades

**Setup:**
- Trades array is empty: `[]`
- Performance metrics all zero

**Expected Results:**
- [ ] Performance Cards show zeros: Total P&L "$0.00", Total Trades "0", Win Rate "N/A" or "0%"
- [ ] Best/Worst trade cards show "N/A" or "-"
- [ ] Cumulative P&L Chart shows empty state: "No data to display" or blank chart with message
- [ ] Trades Table shows empty state message: "No trades yet"
- [ ] Helpful subtext: "Closed trades will appear here after your bot completes positions"
- [ ] No broken table layouts or blank screens

### No Trades Match Filters

**Scenario:** User applies filters that result in zero matching trades

**Setup:**
- User has 50 trades total
- User filters for "Entry Price > $100,000" but all trades have entry < $100k

**Steps:**
1. User applies entry price filter that matches nothing

**Expected Results:**
- [ ] Trades Table shows empty state: "No results found"
- [ ] Helpful message: "Try adjusting your filters"
- [ ] "Clear filters" link is prominently displayed
- [ ] Filter badges still show active filters
- [ ] Performance cards show zeros (no trades match)

### Search Returns No Results

**Scenario:** User searches for order ID that doesn't exist

**Setup:**
- User searches for "99999999" which doesn't exist

**Expected Results:**
- [ ] Empty state: "No results found"
- [ ] Suggestion: "Try a different order ID or clear your search"
- [ ] Search badge shows "Search: 99999999" with X to remove

---

## Component Interaction Tests

### PerformanceCards Component

**Renders correctly:**
- [ ] Displays 6 cards: Total P&L, Total Trades, Win Rate, Avg Profit, Best Trade, Worst Trade
- [ ] Total P&L shows dollar amount with + or - and ROI percentage
- [ ] Win Rate shows percentage with count (e.g., "30 wins / 15 losses")
- [ ] Best Trade shows amount in green with date
- [ ] Worst Trade shows amount in red with date
- [ ] All cards update when filters change

### PnlChart Component

**Renders correctly:**
- [ ] Line chart displays with X-axis (time) and Y-axis (cumulative P&L)
- [ ] Positive P&L sections of line are green, negative are red
- [ ] Time range selector is visible (e.g., 7D, 30D, All buttons)

**User interactions:**
- [ ] Clicking time range button updates chart data range
- [ ] Hovering over chart shows tooltip with date and P&L value

### Filters Component

**Renders correctly:**
- [ ] Status filter dropdown/buttons (All, Closed, Open)
- [ ] Profit/Loss filter (All, Profitable, Losses)
- [ ] Advanced filters: Entry Price Range, Duration Range, Quantity Range inputs
- [ ] Search input field with placeholder "Search by Order ID"

**User interactions:**
- [ ] Selecting status option calls `onFiltersChange` with updated status
- [ ] Entering price range and submitting calls `onFiltersChange` with price range object
- [ ] Typing in search and pressing Enter calls `onSearch` with query string

### FilterBadges Component

**Renders correctly:**
- [ ] Shows one badge for each active filter
- [ ] Badge text describes the filter (e.g., "Status: Closed", "Search: 12345")
- [ ] Each badge has X button

**User interactions:**
- [ ] Clicking X on a badge calls `onRemoveFilter` with that filter's key
- [ ] "Clear all filters" link is visible when any filters are active
- [ ] Clicking "Clear all filters" calls `onClearFilters`

### TradesTable Component

**Renders correctly:**
- [ ] Table headers: Date/Time, Entry Price, Exit Price, Quantity, P&L ($), P&L (%), Duration, Status, View Details
- [ ] Sortable columns have sort indicator icons
- [ ] Each row displays formatted data (currency with $, percentages with %, timestamps)
- [ ] P&L values are color-coded (green for profit, red for loss)
- [ ] Status badge shows "CLOSED" or "OPEN" with appropriate color

**User interactions:**
- [ ] Clicking column header calls `onSortChange` with column and direction
- [ ] Clicking column header again toggles sort direction
- [ ] Clicking trade row or "View Details" calls `onViewTradeDetails` with trade ID
- [ ] Hovering row shows interactive state (cursor pointer, background highlight)

### TradeDetailsModal Component

**Renders correctly:**
- [ ] Modal displays with all sections: Overview, Prices & P&L, Timeline, TP Details, Fees Breakdown
- [ ] All data formatted correctly (currency, dates, percentages)
- [ ] TP adjustment history shows multiple adjustments with timestamps and reasons
- [ ] Modal has close button (X icon)

**User interactions:**
- [ ] Clicking X or "Close" button closes modal
- [ ] Clicking backdrop/overlay closes modal
- [ ] Pressing Escape key closes modal

**Loading and error states:**
- [ ] If trade details loading, shows skeleton or spinner
- [ ] If trade not found, shows error: "Trade details not found"

---

## Edge Cases

- [ ] **Very large P&L values:** Trades with +$10,000 or -$5,000 P&L display correctly with proper formatting
- [ ] **Very short duration:** Trade duration of 1 minute displays as "1m" not "0h"
- [ ] **Very long duration:** Trade open for 3 days shows "3d 2h" or similar
- [ ] **Zero P&L trade:** Trade that breaks even shows "$0.00 (0%)" in neutral color (not green or red)
- [ ] **Many TP adjustments:** Trade with 10+ TP adjustments displays scrollable list in modal
- [ ] **Hundreds of trades:** Performance with 500+ trades in table doesn't cause lag (pagination helps)
- [ ] **Rapid filter changes:** Applying multiple filters quickly doesn't cause race conditions or stale data
- [ ] **Sort persists across filters:** If user sorts by P&L, then filters, sort remains applied to filtered results
- [ ] **Navigating away and back:** After leaving and returning to trade history, filters and sort state are either preserved or reset appropriately
- [ ] **Transition from empty to populated:** After bot closes first trade, trade history transitions from empty state to showing data

---

## Accessibility Checks

- [ ] All interactive elements (filter buttons, sort headers, badges) are keyboard accessible
- [ ] Filter dropdown is navigable with arrow keys
- [ ] Clicking table header with Enter key sorts the column
- [ ] Trade Details Modal traps focus (can't tab outside modal)
- [ ] Close buttons have aria-labels
- [ ] Tables have proper semantic markup (thead, tbody, th, td)
- [ ] Sort indicators have accessible text (e.g., "sorted descending")
- [ ] Empty states have accessible messaging
- [ ] Chart has accessible description or data table alternative

---

## Sample Test Data

Use the data from `sample-data.json` or create variations:

```typescript
// Example test data - Trade list
const mockTrades: Trade[] = [
  {
    id: 'trade-1',
    orderId: '12345678',
    tpOrderId: '87654321',
    symbol: 'BTC/USDT',
    side: 'LONG',
    leverage: 10,
    entryPrice: 95000,
    exitPrice: 96500,
    quantity: 0.1,
    pnl: 150,
    pnlPercent: 1.58,
    status: 'CLOSED',
    openedAt: '2025-01-03T10:00:00Z',
    filledAt: '2025-01-03T10:05:00Z',
    closedAt: '2025-01-03T12:15:00Z',
    duration: 8100, // seconds (2h 15m)
    fees: {
      tradingFee: 12,
      fundingFee: 3,
      netPnl: 135
    },
    tpAdjustments: [
      {
        timestamp: '2025-01-03T11:00:00Z',
        oldTp: 96000,
        newTp: 96500,
        reason: 'Funding rate increased to 0.02%'
      }
    ]
  },
  // ... more trades
];

// Example test data - Performance metrics
const mockPerformance: PerformanceMetrics = {
  totalPnl: 1250.50,
  roi: 12.5,
  totalTrades: 45,
  winningTrades: 30,
  losingTrades: 15,
  winRate: 66.7,
  avgProfit: 27.79,
  bestTrade: {
    id: 'trade-best',
    pnl: 250,
    date: '2025-01-02T14:30:00Z'
  },
  worstTrade: {
    id: 'trade-worst',
    pnl: -85,
    date: '2025-01-01T09:15:00Z'
  }
};

// Example test data - Cumulative P&L
const mockCumulativePnl: CumulativePnlDataPoint[] = [
  { date: '2025-01-01', cumulativePnl: 50 },
  { date: '2025-01-02', cumulativePnl: 300 },
  { date: '2025-01-03', cumulativePnl: 1250.50 }
];

// Example test data - Empty states
const mockEmptyTrades = [];
const mockZeroPerformance: PerformanceMetrics = {
  totalPnl: 0,
  roi: 0,
  totalTrades: 0,
  winningTrades: 0,
  losingTrades: 0,
  winRate: 0,
  avgProfit: 0,
  bestTrade: { id: '', pnl: 0, date: '' },
  worstTrade: { id: '', pnl: 0, date: '' }
};

// Example test data - Filters
const mockFilters: TradeFilters = {
  period: '30days',
  status: 'closed',
  profitFilter: 'profitable',
  entryPriceRange: { min: 90000, max: 95000 }
};

// Example test data - Sort config
const mockSortConfig: SortConfig = {
  column: 'pnl',
  direction: 'desc'
};
```

---

## Notes for Test Implementation

- Mock API calls to test both success and failure scenarios (trades loaded, API errors, network failures)
- Test each callback prop is called with correct arguments
- Verify filters actually filter data (test filter logic or mock filtered API responses)
- Verify sort actually changes order (test sort logic or mock sorted API responses)
- Test pagination shows correct ranges and navigates properly
- Ensure loading states appear during async operations
- **Always test empty states** - Pass empty arrays for trades, zero metrics, to verify helpful empty state UI appears (not blank screens)
- Test transitions: empty → first trade, last trade removed → empty state
- Test modal interactions: open, close, keyboard navigation
- Verify chart renders correctly with varying data (all positive, all negative, mixed)
