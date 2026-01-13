# Test Instructions: Dashboard

These test-writing instructions are **framework-agnostic**. Adapt them to your testing setup (Jest, Vitest, Playwright, Cypress, React Testing Library, RSpec, Minitest, PHPUnit, etc.).

## Overview

The Dashboard provides real-time visibility into bot status, market conditions, performance metrics, active trading positions/orders, and recent activity. Tests should verify that users can monitor the bot effectively, execute control actions with proper confirmation, and view detailed information about their trading activity.

---

## User Flow Tests

### Flow 1: View Dashboard Overview and Monitor Bot Status

**Scenario:** User opens the dashboard to check on their bot's current status and recent performance

#### Success Path

**Setup:**
- User is authenticated
- Bot has status data with `status: 'ACTIVE'`
- Market data shows current BTC price: `96500.50`, funding rate: `0.01%`
- Performance metrics show today's P&L: `$125.50` (positive)
- At least one open position and several active orders exist
- Recent activity includes multiple events

**Steps:**
1. User navigates to `/dashboard` route
2. User sees the dashboard load with all sections
3. User observes bot status card showing "ACTIVE" with green badge
4. User sees market overview with current BTC price and 24h change
5. User sees performance metrics card with today's P&L highlighted in green
6. User sees positions table with at least one row showing unrealized P&L
7. User sees orders table with active grid orders
8. User sees recent activity feed with timestamped events

**Expected Results:**
- [ ] Bot Status Card displays status badge "ACTIVE" with green/emerald color
- [ ] Bot Status Card shows cycle activation timestamp and "last updated" time
- [ ] Market Overview Card displays BTC price "$96,500.50" with 24h change indicator (green if positive, red if negative)
- [ ] Market Overview Card shows funding rate "0.01%" and MACD signal indicator
- [ ] Performance Metrics Card shows "Today" section with realized P&L "$125.50" in green
- [ ] Performance Metrics Card shows "Total" section with cumulative stats
- [ ] Positions Table renders with columns: Entry Price, Current Price, Quantity, Side, Unrealized P&L
- [ ] At least one position row is visible with calculated unrealized P&L displayed
- [ ] Orders Table renders with columns: Price, Side, Quantity, Status
- [ ] Active orders are displayed with appropriate side badges (BUY in green, SELL in red)
- [ ] Activity Feed shows recent events in chronological order (newest first)
- [ ] Each activity event has an icon, description, and timestamp
- [ ] Period selector shows default selection (e.g., "Today")

#### Failure Path: Bot Status Data Not Available

**Setup:**
- API call to fetch bot status fails with 500 error
- Other dashboard data loads successfully

**Steps:**
1. User navigates to `/dashboard`
2. Bot status API returns error

**Expected Results:**
- [ ] Bot Status Card shows error state: "Unable to load bot status"
- [ ] Error message is displayed with retry option or helpful text
- [ ] Other dashboard sections (market, performance, positions) still load successfully
- [ ] User can attempt to refresh or reload to retry

#### Failure Path: No Network Connection

**Setup:**
- Network is disconnected
- All API calls fail

**Steps:**
1. User navigates to `/dashboard`
2. All API calls fail due to network error

**Expected Results:**
- [ ] Dashboard shows loading skeleton initially
- [ ] Error message appears: "Unable to connect. Please check your connection."
- [ ] User sees a "Retry" button or refresh option
- [ ] UI degrades gracefully without crashing

---

### Flow 2: Change Time Period Filter

**Scenario:** User wants to view performance metrics for the last 7 days instead of today

#### Success Path

**Setup:**
- Dashboard is loaded with period set to "Today"
- API supports filtering by time period

**Steps:**
1. User sees period selector dropdown at top showing "Today"
2. User clicks the period selector dropdown
3. User sees options: "Today", "7 Days", "30 Days", "Custom"
4. User clicks "7 Days"
5. Dashboard data refreshes

**Expected Results:**
- [ ] Period selector dropdown opens showing all period options
- [ ] "7 Days" option is visible and clickable
- [ ] After selection, dropdown shows "7 Days" as selected
- [ ] `onPeriodChange` callback is called with `period: '7days'`
- [ ] Performance Metrics Card updates to show P&L for the last 7 days
- [ ] Recent Activity Feed updates to show events from the last 7 days
- [ ] Loading state appears briefly during data fetch
- [ ] Updated data renders successfully

#### Failure Path: Custom Date Range Selection

**Setup:**
- User wants to select a custom date range

**Steps:**
1. User clicks period selector
2. User selects "Custom"
3. Date picker modal/popover appears
4. User selects start date and end date
5. User confirms selection

**Expected Results:**
- [ ] Custom option triggers date picker UI
- [ ] Date picker allows selection of start and end dates
- [ ] Selected custom range is validated (end date must be after start date)
- [ ] After confirmation, period selector shows custom range label (e.g., "Dec 1 - Dec 7")
- [ ] `onPeriodChange` is called with `period: 'custom'` and date range object
- [ ] Dashboard data updates for the custom period

---

### Flow 3: Execute Bot Control Action (Pause Bot)

**Scenario:** User wants to pause an actively running bot

#### Success Path

**Setup:**
- Bot status is "ACTIVE"
- User has permission to control the bot

**Steps:**
1. User sees Bot Status Card with status "ACTIVE"
2. User sees control buttons including "Pause" button
3. User clicks "Pause" button
4. Confirmation dialog appears
5. Dialog shows message: "Are you sure you want to pause the bot? This will stop new orders but keep existing positions."
6. User clicks "Confirm" in the dialog
7. Bot pauses successfully

**Expected Results:**
- [ ] Confirmation dialog opens with heading "Pause Bot"
- [ ] Dialog message clearly explains: "This will stop new orders but keep existing positions."
- [ ] Dialog has "Cancel" and "Confirm" buttons
- [ ] Clicking "Confirm" closes the dialog
- [ ] `onPause` callback is invoked
- [ ] Loading state appears on the Pause button or status card during the action
- [ ] After successful pause, bot status updates to "PAUSED" with yellow/amber badge
- [ ] Success notification appears: "Bot paused successfully"
- [ ] Control buttons update to show "Resume" instead of "Pause"

#### Failure Path: User Cancels Pause Action

**Setup:**
- Bot status is "ACTIVE"

**Steps:**
1. User clicks "Pause" button
2. Confirmation dialog appears
3. User clicks "Cancel" in the dialog

**Expected Results:**
- [ ] Dialog closes immediately
- [ ] `onPause` callback is NOT called
- [ ] Bot status remains "ACTIVE"
- [ ] No changes to bot state or UI

#### Failure Path: Pause Action Fails

**Setup:**
- Bot status is "ACTIVE"
- Backend API fails when attempting to pause

**Steps:**
1. User clicks "Pause" and confirms
2. Backend returns error response

**Expected Results:**
- [ ] Error notification appears: "Failed to pause bot. Please try again."
- [ ] Bot status remains "ACTIVE"
- [ ] Pause button returns to enabled state (not stuck in loading)
- [ ] User can retry the action

---

### Flow 4: View Position Details

**Scenario:** User wants to see detailed information about an open position

#### Success Path

**Setup:**
- At least one position exists with:
  - Entry price: `95000`
  - Current price: `96500`
  - Quantity: `0.1`
  - Side: `LONG`
  - Unrealized P&L: `$150`
  - Take profit price: `97000`
  - Liquidation price: `90000`

**Steps:**
1. User sees Positions Table with at least one position row
2. User sees position showing unrealized P&L in green: "+$150 (+1.58%)"
3. User clicks on the position row or "View Details" button
4. Position Details Modal opens

**Expected Results:**
- [ ] Modal opens centered on screen
- [ ] Modal heading shows "Position Details"
- [ ] Modal displays position ID or symbol (e.g., "BTC/USDT")
- [ ] Entry price is displayed: "$95,000.00"
- [ ] Current price is displayed: "$96,500.00"
- [ ] Quantity is displayed: "0.1 BTC"
- [ ] Side badge shows "LONG" with appropriate color (green)
- [ ] Unrealized P&L is prominently displayed: "+$150.00 (+1.58%)" in green
- [ ] Take profit price is shown: "$97,000.00"
- [ ] Liquidation price is shown: "$90,000.00" with warning color if close
- [ ] Opened timestamp is displayed (e.g., "Dec 3, 2025 10:30 AM")
- [ ] Modal has close button (X icon) and/or "Close" button
- [ ] Clicking close button or X closes the modal
- [ ] `onViewPosition` callback was called with the position ID

#### Failure Path: Position Data Incomplete

**Setup:**
- Position exists but some data fields are missing (e.g., no liquidation price)

**Steps:**
1. User clicks position to view details

**Expected Results:**
- [ ] Modal opens successfully
- [ ] Available data is displayed correctly
- [ ] Missing fields show "N/A" or appropriate placeholder (not blank or undefined)
- [ ] UI doesn't break or show errors

---

### Flow 5: Start a Stopped Bot

**Scenario:** User wants to start a bot that is currently stopped

#### Success Path

**Setup:**
- Bot status is "STOPPED"
- Strategy configuration is valid

**Steps:**
1. User sees Bot Status Card with status "STOPPED" (red badge)
2. User sees "Start" button in the control buttons
3. User clicks "Start" button
4. Confirmation dialog appears
5. Dialog explains: "Starting the bot will begin placing orders based on your strategy settings. Make sure your strategy is configured correctly."
6. User clicks "Confirm"

**Expected Results:**
- [ ] Confirmation dialog opens with heading "Start Bot"
- [ ] Dialog warns user to verify strategy configuration
- [ ] User can cancel or confirm
- [ ] Clicking "Confirm" calls `onStart` callback
- [ ] Loading state appears during the action
- [ ] After success, bot status updates to "WAIT" (waiting for MACD activation) or "ACTIVE"
- [ ] Success notification: "Bot started successfully"
- [ ] Control buttons update to show "Pause" and "Stop" options

#### Failure Path: Start Requires MACD Activation

**Setup:**
- Bot is configured to wait for MACD signal before activating

**Steps:**
1. User starts the bot
2. Backend confirms bot is started but waiting for MACD activation

**Expected Results:**
- [ ] Bot status updates to "WAIT" with gray/amber badge
- [ ] Status description explains: "Waiting for MACD bullish signal to activate"
- [ ] User understands bot is running but not yet placing orders
- [ ] No positions or orders are created yet

---

## Empty State Tests

Empty states are critical for first-time users and when data is unavailable. Test these thoroughly:

### No Open Positions

**Scenario:** User has no open positions (bot not yet active or all positions closed)

**Setup:**
- Positions array is empty: `[]`
- Orders and other data exist

**Expected Results:**
- [ ] Positions Table section shows empty state message
- [ ] Message says "No open positions" or similar
- [ ] Helpful subtext: "Positions will appear here when the bot places trades"
- [ ] No broken table layout (not showing table headers with no rows, or showing empty headers)
- [ ] Rest of dashboard (bot status, market, activity) renders normally

### No Active Orders

**Scenario:** User has no active grid orders

**Setup:**
- Orders array is empty: `[]`

**Expected Results:**
- [ ] Orders Table shows empty state: "No active orders"
- [ ] Subtext explains: "Grid orders will appear when the bot is active"
- [ ] Empty state is helpful, not blank

### No Recent Activity

**Scenario:** Bot just started, no trading events yet

**Setup:**
- Activity events array is empty: `[]`

**Expected Results:**
- [ ] Activity Feed shows empty state: "No recent activity"
- [ ] Subtext: "Trading events will appear here as the bot operates"
- [ ] No timeline/list with zero items (should show helpful empty message)

### First-Time User (All Data Empty)

**Scenario:** Brand new user, bot never started, no historical data

**Setup:**
- Bot status: `STOPPED`
- No positions, no orders, no activity
- Performance metrics all zero

**Expected Results:**
- [ ] Bot Status Card shows "STOPPED" with helpful description
- [ ] Market Overview still displays current BTC price and market data
- [ ] Performance Metrics show $0 values (not blank or missing)
- [ ] Positions Table shows empty state
- [ ] Orders Table shows empty state
- [ ] Activity Feed shows empty state
- [ ] User sees clear path to action: "Start" button is prominent
- [ ] No confusing blank sections or errors

---

## Component Interaction Tests

### BotStatusCard Component

**Renders correctly:**
- [ ] Displays bot status badge with correct color based on status (green for ACTIVE, yellow for PAUSED, red for STOPPED, gray for WAIT)
- [ ] Shows status description text explaining current state
- [ ] Displays cycle activation timestamp if bot is active
- [ ] Shows "last updated" timestamp

**User interactions:**
- [ ] Clicking "Pause" button opens confirmation dialog
- [ ] Clicking "Stop" button opens confirmation dialog
- [ ] Clicking "Resume" button (when paused) opens confirmation dialog
- [ ] Clicking "Start" button (when stopped) opens confirmation dialog
- [ ] Buttons are disabled during loading state
- [ ] Only appropriate buttons show based on current status (e.g., no "Pause" when already paused)

### PeriodSelector Component

**Renders correctly:**
- [ ] Shows currently selected period as button/dropdown text
- [ ] Displays dropdown icon indicating it's interactive

**User interactions:**
- [ ] Clicking opens dropdown menu with all period options
- [ ] Options include: "Today", "7 Days", "30 Days", "Custom"
- [ ] Selecting an option closes dropdown
- [ ] Selected option updates the display
- [ ] Calls `onPeriodChange` with correct period value
- [ ] If "Custom" selected, triggers date picker

### PositionsTable Component

**Renders correctly:**
- [ ] Table headers: Entry Price, Current Price, Quantity, Side, Unrealized P&L
- [ ] Each row displays formatted currency values (e.g., "$95,000.00")
- [ ] Side badge shows "LONG" or "SHORT" with color coding
- [ ] Unrealized P&L shows with + or - and percentage, color-coded (green for profit, red for loss)

**User interactions:**
- [ ] Clicking a position row or "View Details" calls `onViewPosition` with position ID
- [ ] Hovering row shows interactive state (cursor pointer, background highlight)

### ConfirmDialog Component

**Renders correctly:**
- [ ] Modal displays with heading, message, and action buttons
- [ ] Message text is clear and explains consequences of action
- [ ] Has "Cancel" and "Confirm" buttons

**User interactions:**
- [ ] Clicking "Cancel" closes dialog without action
- [ ] Clicking "Confirm" triggers the associated callback and closes dialog
- [ ] Clicking outside modal or pressing Escape key closes dialog (cancel behavior)
- [ ] Keyboard navigation works (Tab, Enter, Escape)

### PositionDetailsModal Component

**Renders correctly:**
- [ ] Displays all position details: entry, current, quantity, side, P&L, TP, liquidation
- [ ] Numeric values are formatted with currency or percentage symbols
- [ ] Timestamp is human-readable
- [ ] Modal has close button (X icon in corner)

**User interactions:**
- [ ] Clicking X or "Close" button closes modal
- [ ] Clicking backdrop/overlay closes modal
- [ ] Pressing Escape key closes modal

**Loading and error states:**
- [ ] If position details are loading, show skeleton or spinner
- [ ] If position not found, show error: "Position not found"

---

## Edge Cases

- [ ] **Very long status description:** If status description text is long, it wraps properly without breaking layout
- [ ] **Extremely high/low P&L values:** Large numbers (e.g., +$100,000 or -$50,000) display correctly with proper formatting and color
- [ ] **Multiple positions and orders:** Dashboard handles 10+ open positions and 20+ active orders without performance issues
- [ ] **Rapid status changes:** If bot status changes quickly (e.g., active → paused → active), UI updates correctly without race conditions
- [ ] **BTC price updates in real-time:** If market data updates while user is viewing, position unrealized P&L recalculates correctly
- [ ] **Navigating away and back:** After leaving dashboard and returning, data refreshes and displays correctly
- [ ] **Transition from empty to populated:** After starting bot and first position opens, positions table transitions from empty state to showing data
- [ ] **Transition from populated to empty:** After closing last position, positions table shows empty state (not blank screen)
- [ ] **Concurrent actions:** User cannot trigger multiple control actions simultaneously (e.g., can't click Pause while Stop is processing)

---

## Accessibility Checks

- [ ] All interactive buttons are keyboard accessible (Tab to focus, Enter to activate)
- [ ] Period selector dropdown is navigable with arrow keys
- [ ] Confirmation dialogs trap focus (can't tab outside modal)
- [ ] Close buttons have accessible labels (aria-label="Close")
- [ ] Status badges have sufficient color contrast and don't rely solely on color (include text/icons)
- [ ] Screen readers announce status changes (e.g., "Bot paused successfully")
- [ ] Tables have proper semantic markup (thead, tbody, th, td)
- [ ] Error messages are announced to screen readers

---

## Sample Test Data

Use the data from `sample-data.json` or create variations:

```typescript
// Example test data - Active bot with positions
const mockBotStatus = {
  status: 'ACTIVE' as BotStatus,
  stateDescription: 'Bot is actively trading with MACD bullish signal',
  cycleActivatedAt: '2025-01-03T14:30:00Z',
  lastUpdate: '2025-01-03T18:45:00Z'
};

const mockMarketData = {
  btcPrice: 96500.50,
  priceChange24h: 2.34,
  fundingRate: 0.01,
  fundingInterval: '8h',
  macdSignal: 'bullish' as MacdSignal,
  gridRangeLow: 95000,
  gridRangeHigh: 98000
};

const mockPosition = {
  id: 'pos-1',
  entryPrice: 95000,
  currentPrice: 96500,
  quantity: 0.1,
  side: 'LONG' as PositionSide,
  unrealizedPnl: 150,
  pnlPercent: 1.58,
  takeProfitPrice: 97000,
  liquidationPrice: 90000,
  openedAt: '2025-01-03T16:00:00Z'
};

const mockPositions = [mockPosition];

// Example test data - Empty states
const mockEmptyPositions = [];
const mockEmptyOrders = [];
const mockEmptyActivity = [];

// Example test data - Stopped bot (first-time user)
const mockStoppedBotStatus = {
  status: 'STOPPED' as BotStatus,
  stateDescription: 'Bot is not running. Click Start to begin trading.',
  cycleActivatedAt: '',
  lastUpdate: '2025-01-03T18:00:00Z'
};

const mockZeroPerformance = {
  today: {
    realizedPnl: 0,
    pnlPercent: 0,
    tradesClosed: 0
  },
  total: {
    totalPnl: 0,
    totalTrades: 0,
    avgProfitPerTrade: 0
  }
};

// Example test data - Error scenarios
const mockApiError = {
  status: 500,
  message: 'Internal server error'
};

const mockNetworkError = {
  message: 'Network request failed'
};
```

---

## Notes for Test Implementation

- Mock API calls to test both success and failure scenarios
- Test each callback prop is called with correct arguments (e.g., `onPause()`, `onViewPosition(positionId)`)
- Verify confirmation dialogs prevent accidental actions
- Test that loading states appear during async operations (bot controls, data fetching)
- Ensure error boundaries catch and display errors gracefully
- **Always test empty states** - Pass empty arrays for positions, orders, and activity to verify helpful empty state UI appears (not blank screens)
- Test transitions: empty → first item added, last item removed → empty state returns
- Verify real-time updates work correctly (status changes, price updates)
- Test period selector actually filters data correctly when calling backend
