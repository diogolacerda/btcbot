# Test Instructions: Strategy

These test-writing instructions are **framework-agnostic**. Adapt them to your testing setup (Jest, Vitest, Playwright, Cypress, React Testing Library, RSpec, Minitest, PHPUnit, etc.).

## Overview

The Strategy section provides comprehensive control over bot trading configuration including risk parameters, grid settings, MACD filters, and execution controls. Tests should verify that users can safely configure their trading strategy, see real-time risk calculations, preview grid levels, and execute strategy controls with proper validation and confirmation.

---

## User Flow Tests

### Flow 1: View Current Strategy Configuration and Status

**Scenario:** User opens strategy page to review current configuration and bot status

#### Success Path

**Setup:**
- User is authenticated
- Strategy exists with:
  - Status: `active`
  - Cycle started: `2025-01-03 10:00 AM`, P&L since start: `$450`, Trades: `15`, Win rate: `73%`
  - Position size: `$100`, Max orders: `20`, Leverage: `10x`, Margin: `crossed`
  - Grid: Fixed `$500` spacing, `±5%` range, `1.5%` TP
  - MACD enabled: 12/26/9 on 1h timeframe
  - Current BTC price: `$96,500`

**Steps:**
1. User navigates to `/strategy` route
2. Page loads with all sections

**Expected Results:**
- [ ] Strategy Status Card displays:
  - Status badge "ACTIVE" in green/emerald
  - Status context: "Bot is actively trading with MACD bullish signal"
  - Cycle info: "Started Jan 3, 2025 10:00 AM"
  - Cycle metrics: "P&L: +$450", "Trades: 15", "Win Rate: 73%"
  - Last updated timestamp
  - Control buttons: "Pause" and "Stop" visible (not "Start" or "Resume")
- [ ] Risk Parameters Section shows:
  - Position Size: "$100"
  - Max Total Orders: "20"
  - Total capital display: "$2,000" (100 × 20)
  - Leverage slider at "10x"
  - Margin Mode: "Crossed" selected
- [ ] Risk Summary Card shows:
  - Total Capital at Risk: "$2,000"
  - Capital Per Position: "$100"
  - Liquidation Risk indicator (green/yellow/red based on leverage)
  - Max Loss Per Trade: calculated value
- [ ] Grid Settings Section shows:
  - Spacing Type: "Fixed $" selected
  - Spacing Value: "$500"
  - Grid Range: "±5%"
  - Take Profit: "1.5%"
- [ ] Grid Preview displays price levels around current BTC price ($96,500)
- [ ] MACD Filter Section shows:
  - MACD enabled toggle is ON
  - Fast Period: "12", Slow Period: "26", Signal Period: "9"
  - Timeframe: "1h" selected
- [ ] Advanced Settings section is collapsed by default

#### Failure Path: Strategy Data Not Available

**Setup:**
- API fails to load strategy configuration

**Steps:**
1. User navigates to `/strategy`
2. API returns error

**Expected Results:**
- [ ] Error message: "Unable to load strategy configuration"
- [ ] User sees retry button
- [ ] Form sections show loading skeletons or error states
- [ ] No crash

---

### Flow 2: Adjust Risk Parameters and View Live Risk Calculations

**Scenario:** User wants to increase position size and see how it affects risk

#### Success Path

**Setup:**
- Current position size: `$100`
- Current leverage: `10x`
- Current max orders: `20`

**Steps:**
1. User sees Risk Parameters section
2. User changes Position Size from `$100` to `$200`
3. Risk Summary updates in real-time
4. User adjusts Leverage slider from `10x` to `25x`
5. Risk Summary updates again

**Expected Results:**
- [ ] Position Size input shows "$200" after change
- [ ] Total capital calculation updates: "$4,000" (200 × 20)
- [ ] `onUpdateRiskParameters` callback is called with updated `positionSize: 200`
- [ ] Risk Summary Card updates immediately:
  - Total Capital at Risk: "$4,000"
  - Capital Per Position: "$200"
  - Max Loss Per Trade increases
- [ ] After leverage change to 25x:
  - Leverage slider shows "25x"
  - Liquidation Risk indicator changes color (likely to red for high leverage)
  - Warning appears: "High leverage increases liquidation risk"
- [ ] `onUpdateRiskParameters` called with `leverage: 25`

#### Validation Path: Position Size Too Small

**Setup:**
- User tries to set position size below minimum

**Steps:**
1. User enters "$3" in Position Size field (below minimum of $5)
2. User tabs away or attempts to save

**Expected Results:**
- [ ] Validation error appears below field: "Position size must be at least $5"
- [ ] Field border turns red
- [ ] Save button is disabled or shows warning
- [ ] `onUpdateRiskParameters` is not called with invalid value

---

### Flow 3: Configure Grid Settings and Preview Grid Levels

**Scenario:** User wants to adjust grid spacing and see preview of price levels

#### Success Path

**Setup:**
- Current BTC price: `$96,500`
- Current grid: Fixed `$500` spacing, `±5%` range

**Steps:**
1. User sees Grid Settings section
2. User changes Spacing Type from "Fixed $" to "Percentage %"
3. User enters `0.5` in Spacing Value (0.5%)
4. User changes Grid Range from `±5%` to `±3%`
5. Grid Preview updates

**Expected Results:**
- [ ] Spacing Type updates to "Percentage %" selected
- [ ] Spacing Value input shows "0.5" with "%" suffix
- [ ] `onUpdateGridSettings` called with `{ spacingType: 'percentage', spacingValue: 0.5 }`
- [ ] Grid Range input shows "±3%"
- [ ] Grid Preview updates to show price levels calculated with:
  - 0.5% spacing between levels
  - Range of ±3% from current price ($96,500)
- [ ] Preview shows levels like:
  - Buy levels below current price (e.g., $96,017, $95,536...)
  - Sell levels above current price (e.g., $96,983, $97,467...)
  - Current price level highlighted or marked
- [ ] Preview shows approximately 12 levels (6 buy, 6 sell) within ±3% range

#### Validation Path: Take Profit Too Low (Below Fees)

**Setup:**
- User sets Take Profit to very low value

**Steps:**
1. User enters `0.05` (0.05%) in Take Profit field
2. Field loses focus

**Expected Results:**
- [ ] Warning appears: "Take profit may be too low to cover trading fees"
- [ ] Warning is in amber/yellow color
- [ ] Field shows warning border
- [ ] User can still save but is warned about risk
- [ ] Tooltip suggests minimum TP based on estimated fees (e.g., "Recommended: at least 0.1%")

---

### Flow 4: Enable MACD Filter with Parameters

**Scenario:** User wants to enable MACD filter so bot only activates on bullish signals

#### Success Path

**Setup:**
- MACD filter is currently disabled

**Steps:**
1. User sees MACD Filter section with toggle OFF
2. User sees explanation: "When disabled, bot trades continuously without MACD signal confirmation"
3. User clicks toggle to enable MACD
4. MACD parameter inputs become visible/editable
5. User sets Fast: `12`, Slow: `26`, Signal: `9`
6. User selects Timeframe: `1h`

**Expected Results:**
- [ ] Toggle switches to ON state (green/emerald)
- [ ] Explanation updates: "Bot will only activate when MACD shows bullish signal"
- [ ] MACD parameter inputs are enabled:
  - Fast Period input shows "12"
  - Slow Period input shows "26"
  - Signal Period input shows "9"
- [ ] Timeframe dropdown shows "1h" selected
- [ ] `onUpdateMACDFilter` callback is called with `{ enabled: true, fastPeriod: 12, slowPeriod: 26, signalPeriod: 9, timeframe: '1h' }`
- [ ] Common values are shown as suggestions or presets (e.g., "Default: 12/26/9")

#### Success Path: Disable MACD Filter

**Steps:**
1. User has MACD enabled
2. User clicks toggle to disable
3. Warning appears

**Expected Results:**
- [ ] Confirmation or warning: "Disabling MACD filter will allow bot to trade continuously without signal confirmation. Are you sure?"
- [ ] If user confirms, toggle switches to OFF
- [ ] MACD parameter inputs become disabled or hidden
- [ ] `onUpdateMACDFilter` called with `{ enabled: false, ... }`

---

### Flow 5: Start Strategy with MACD Activation Requirement

**Scenario:** User wants to start a stopped strategy that has MACD filter enabled

#### Success Path

**Setup:**
- Strategy status: `stopped`
- MACD filter is enabled
- Strategy configuration is valid

**Steps:**
1. User sees Strategy Status Card showing "STOPPED" with red badge
2. User sees "Start" button
3. User clicks "Start" button
4. Confirmation dialog appears
5. Dialog explains: "Starting the bot will begin placing orders based on your strategy. Bot will wait for MACD bullish signal before activating."
6. User clicks "Confirm"

**Expected Results:**
- [ ] Confirmation dialog opens with heading "Start Strategy"
- [ ] Dialog clearly explains MACD wait state: "Bot will enter WAIT state until MACD shows bullish signal"
- [ ] User can cancel or confirm
- [ ] Clicking "Confirm" calls `onStart` callback
- [ ] Loading state appears during action
- [ ] After success, strategy status updates to "WAIT" (waiting for MACD activation)
- [ ] Status context: "Waiting for MACD bullish signal to activate"
- [ ] Success notification: "Strategy started. Waiting for MACD signal."
- [ ] Control buttons update to show "Pause" and "Stop" (not "Start")

#### Failure Path: Start with Invalid Configuration

**Setup:**
- Strategy has invalid settings (e.g., position size = 0, grid spacing = 0)

**Steps:**
1. User clicks "Start"
2. Validation runs

**Expected Results:**
- [ ] Error message appears: "Please fix configuration errors before starting"
- [ ] Invalid fields are highlighted with error messages
- [ ] `onStart` is not called until validation passes

---

### Flow 6: Pause Active Strategy

**Scenario:** User wants to pause an actively trading bot

#### Success Path

**Setup:**
- Strategy status: `active`
- Bot has open positions and active orders

**Steps:**
1. User sees "Pause" button in Strategy Status Card
2. User clicks "Pause"
3. Confirmation dialog appears
4. Dialog explains: "Pausing will stop new orders but keep existing positions open. Active orders will remain."
5. User clicks "Confirm"

**Expected Results:**
- [ ] Confirmation dialog opens with heading "Pause Strategy"
- [ ] Dialog explains consequences clearly
- [ ] Clicking "Confirm" calls `onPause` callback
- [ ] Loading state during action
- [ ] After success, status updates to "PAUSED" with yellow/amber badge
- [ ] Status context: "Strategy paused. No new orders will be placed."
- [ ] Control buttons update to show "Resume" and "Stop" (not "Pause")
- [ ] Success notification: "Strategy paused"

---

### Flow 7: Configure Advanced Settings (Dynamic TP)

**Scenario:** User wants to enable dynamic take profit based on funding rate

#### Success Path

**Setup:**
- Advanced Settings section is collapsed
- Dynamic TP is disabled

**Steps:**
1. User clicks "Advanced Settings" to expand section
2. Section expands showing Dynamic TP and Auto-Reactivation options
3. User toggles Dynamic TP to ON
4. Dynamic TP configuration inputs appear
5. User sets Base TP: `1.5%`, Min TP: `0.8%`, Max TP: `3.0%`, Safety Margin: `0.2%`, Check Interval: `60` seconds
6. Current funding rate preview shows: "Current funding: 0.01%"

**Expected Results:**
- [ ] Advanced Settings section expands smoothly
- [ ] Dynamic TP toggle switches to ON
- [ ] Configuration inputs become visible and editable:
  - Base TP: "1.5%"
  - Min TP: "0.8%"
  - Max TP: "3.0%"
  - Safety Margin: "0.2%"
  - Check Interval: "60" seconds
- [ ] Current funding rate preview displays live value
- [ ] Tooltips explain each setting (e.g., "TP will adjust based on funding rate to maximize profit")
- [ ] `onUpdateAdvancedSettings` called with `{ dynamicTP: { enabled: true, baseTP: 1.5, minTP: 0.8, maxTP: 3.0, ... } }`

---

### Flow 8: Save All Strategy Changes

**Scenario:** User has made multiple changes and wants to save configuration

#### Success Path

**Setup:**
- User has modified:
  - Position size to $200
  - Leverage to 15x
  - Grid spacing to 0.5%
  - TP to 1.8%
- All changes are valid

**Steps:**
1. User sees "Save" or "Save Changes" button
2. Button may be highlighted or show "unsaved changes" indicator
3. User clicks "Save"

**Expected Results:**
- [ ] `onSave` callback is called
- [ ] Loading state appears on save button: "Saving..."
- [ ] Button is disabled during save
- [ ] After success, success notification: "Strategy configuration saved"
- [ ] "Unsaved changes" indicator clears
- [ ] Save button returns to default state or shows "Saved" checkmark briefly

#### Failure Path: Save Fails

**Setup:**
- Backend API fails when saving

**Steps:**
1. User clicks "Save"
2. API returns error

**Expected Results:**
- [ ] Error notification: "Failed to save strategy. Please try again."
- [ ] Changes remain in form (not lost)
- [ ] Save button returns to enabled state
- [ ] User can retry saving

---

## Empty State Tests

### First-Time User (No Strategy Configured)

**Scenario:** User has never configured a strategy

**Setup:**
- No existing strategy configuration

**Expected Results:**
- [ ] Strategy Status shows "STOPPED" or "NOT CONFIGURED"
- [ ] Form fields show default/recommended values:
  - Position Size: $50 (or suggested starting value)
  - Leverage: 5x (conservative default)
  - Grid Spacing: 1% (reasonable default)
  - TP: 1.5%
- [ ] MACD enabled by default (safer for beginners)
- [ ] Helpful onboarding message: "Configure your strategy settings and click Start to begin trading"
- [ ] "Start" button is enabled once minimum valid configuration exists

---

## Component Interaction Tests

### StrategyStatusCard Component

**Renders correctly:**
- [ ] Displays status badge with correct color (green=active, yellow=paused, red=stopped, gray=wait)
- [ ] Shows status context explaining current state
- [ ] Displays cycle metrics (started time, P&L, trades, win rate) when active
- [ ] Shows last updated timestamp

**User interactions:**
- [ ] Clicking "Start" opens confirmation dialog then calls `onStart`
- [ ] Clicking "Pause" opens confirmation then calls `onPause`
- [ ] Clicking "Stop" opens confirmation then calls `onStop`
- [ ] Clicking "Resume" calls `onResume`
- [ ] Only appropriate buttons show based on status (can't pause when already paused)
- [ ] Buttons disabled during loading

### RiskParametersSection Component

**Renders correctly:**
- [ ] Position Size input with $ prefix
- [ ] Max Total Orders input
- [ ] Total capital calculation displayed: "Total: $X,XXX"
- [ ] Leverage slider with value indicator (1x - 125x)
- [ ] Leverage risk indicator changes color at thresholds (green <10x, yellow 10-25x, red >25x)
- [ ] Margin Mode radio buttons (Crossed / Isolated) with tooltips

**User interactions:**
- [ ] Changing position size updates total capital calculation immediately
- [ ] Changing position size calls `onUpdateRiskParameters` with new value
- [ ] Dragging leverage slider updates value and risk indicator
- [ ] Changing leverage calls `onUpdateRiskParameters`
- [ ] Selecting margin mode calls `onUpdateRiskParameters`
- [ ] Validation messages appear for invalid inputs (too low position size)

### RiskSummary Card

**Renders correctly:**
- [ ] Total Capital at Risk displays with currency formatting
- [ ] Capital Per Position shows position size value
- [ ] Liquidation Risk indicator with color (green/yellow/red)
- [ ] Max Loss Per Trade calculated and displayed

**Real-time updates:**
- [ ] Updates immediately when position size changes
- [ ] Updates immediately when leverage changes
- [ ] Updates immediately when max orders changes
- [ ] Liquidation risk color changes based on leverage level

### GridSettingsSection Component

**Renders correctly:**
- [ ] Spacing Type radio buttons (Fixed $ / Percentage %)
- [ ] Spacing Value input with appropriate suffix ($ or %)
- [ ] Grid Range input with ± symbol and %
- [ ] Take Profit input with %
- [ ] Grid Anchor dropdown (if applicable)

**User interactions:**
- [ ] Changing spacing type updates input suffix
- [ ] Entering spacing value calls `onUpdateGridSettings`
- [ ] Changing grid range updates grid preview
- [ ] Changing TP shows warning if too low
- [ ] Grid preview updates in real-time

### Grid Preview

**Renders correctly:**
- [ ] Shows list of price levels (buy and sell orders)
- [ ] Current price level is highlighted or marked
- [ ] Buy levels shown in green, sell levels in red
- [ ] Displays distance from current price for each level

**Real-time updates:**
- [ ] Updates when spacing type/value changes
- [ ] Updates when grid range changes
- [ ] Updates when current BTC price changes (if live)

### MACDFilterSection Component

**Renders correctly:**
- [ ] Toggle switch for enable/disable
- [ ] Explanation text changes based on toggle state
- [ ] MACD parameter inputs (Fast, Slow, Signal periods)
- [ ] Timeframe dropdown (15m, 1h, 4h, 1d)
- [ ] Common values shown as hints

**User interactions:**
- [ ] Toggling MACD calls `onUpdateMACDFilter` with enabled state
- [ ] Changing parameters calls `onUpdateMACDFilter` with new values
- [ ] Disabling shows warning about continuous trading
- [ ] Parameter inputs disabled when toggle is OFF

### AdvancedSettingsSection Component

**Renders correctly:**
- [ ] Section is collapsed by default
- [ ] Expand/collapse button or icon
- [ ] When expanded, shows Dynamic TP and Auto-Reactivation options

**User interactions:**
- [ ] Clicking expand button opens section smoothly
- [ ] Dynamic TP toggle enables/disables configuration inputs
- [ ] Auto-Reactivation mode radio buttons work correctly
- [ ] Changing settings calls `onUpdateAdvancedSettings`

---

## Edge Cases

- [ ] **Very high leverage (100x+):** UI shows strong warning, liquidation risk indicator is red, max loss calculation reflects extreme risk
- [ ] **Very small position size (<$10):** Warning appears, risk calculations adjust correctly
- [ ] **Very tight grid spacing (<0.1%):** Warning about too many orders, fee impact warning
- [ ] **Very wide grid range (>20%):** Fewer orders placed, preview shows sparse levels
- [ ] **BTC price changes during configuration:** Grid preview updates, risk calculations adjust if leverage changes due to price movement
- [ ] **Concurrent edits to multiple sections:** All callbacks fire correctly, state updates don't conflict
- [ ] **Rapid slider changes:** Debounced or throttled updates prevent excessive callback calls
- [ ] **Invalid MACD parameters (e.g., fast > slow):** Validation error: "Fast period must be less than slow period"
- [ ] **Saving during network loss:** Error handling, changes preserved in form for retry

---

## Accessibility Checks

- [ ] All form inputs have associated labels
- [ ] Leverage slider is keyboard accessible (arrow keys to adjust)
- [ ] Radio buttons navigable with arrow keys
- [ ] Toggle switches keyboard accessible (Space to toggle)
- [ ] Error messages announced to screen readers
- [ ] Tooltips accessible on focus (not just hover)
- [ ] Confirmation dialogs trap focus
- [ ] Status changes announced to screen readers

---

## Sample Test Data

```typescript
// Example test data - Active strategy
const mockStrategy: Strategy = {
  id: 'strategy-1',
  name: 'BTC Grid Strategy',
  status: 'active',
  statusContext: 'Bot is actively trading with MACD bullish signal',
  cycle: {
    startedAt: '2025-01-03T10:00:00Z',
    pnlSinceStart: 450,
    tradesSinceStart: 15,
    winRateSinceStart: 73
  },
  lastUpdated: '2025-01-03T18:00:00Z',
  riskParameters: {
    positionSize: 100,
    maxTotalOrders: 20,
    leverage: 10,
    marginMode: 'crossed'
  },
  gridSettings: {
    spacingType: 'fixed',
    spacingValue: 500,
    gridRange: 5,
    takeProfit: 1.5,
    gridAnchor: 'none'
  },
  macdFilter: {
    enabled: true,
    fastPeriod: 12,
    slowPeriod: 26,
    signalPeriod: 9,
    timeframe: '1h'
  },
  advancedSettings: {
    dynamicTP: {
      enabled: false,
      baseTP: 1.5,
      minTP: 0.8,
      maxTP: 3.0,
      safetyMargin: 0.2,
      checkInterval: 60
    },
    autoReactivationMode: 'immediate'
  }
};

const mockCurrentMarket: CurrentMarket = {
  btcPrice: 96500,
  fundingRate: 0.01,
  lastUpdate: '2025-01-03T18:00:00Z'
};

const mockRiskSummary: RiskSummary = {
  totalCapital: 2000,
  capitalPerPosition: 100,
  liquidationRisk: 'medium',
  maxLossPerTrade: 100,
  maxLossPerTradePercent: 5
};

const mockGridPreview: GridLevel[] = [
  { level: -3, price: 95000, type: 'buy', distanceFromCurrent: -1.55 },
  { level: -2, price: 95500, type: 'buy', distanceFromCurrent: -1.04 },
  { level: -1, price: 96000, type: 'buy', distanceFromCurrent: -0.52 },
  { level: 0, price: 96500, type: 'current', distanceFromCurrent: 0 },
  { level: 1, price: 97000, type: 'sell', distanceFromCurrent: 0.52 },
  { level: 2, price: 97500, type: 'sell', distanceFromCurrent: 1.04 },
  { level: 3, price: 98000, type: 'sell', distanceFromCurrent: 1.55 }
];

// Example test data - Stopped strategy (first-time user)
const mockStoppedStrategy: Strategy = {
  ...mockStrategy,
  status: 'stopped',
  statusContext: 'Strategy not running. Configure settings and click Start.',
  cycle: {
    startedAt: '',
    pnlSinceStart: 0,
    tradesSinceStart: 0,
    winRateSinceStart: 0
  }
};
```

---

## Notes for Test Implementation

- Mock API calls for strategy load, save, and control actions
- Test each callback prop is called with correct arguments
- Verify real-time calculations update correctly (risk summary, grid preview)
- Test validation logic for all input fields
- Test confirmation dialogs prevent accidental critical actions
- Ensure loading states appear during async operations
- Test that changes are preserved in form if save fails (for retry)
- Verify tooltips provide helpful context for all settings
- Test keyboard navigation and accessibility thoroughly
- Test that invalid configurations cannot be saved or started
