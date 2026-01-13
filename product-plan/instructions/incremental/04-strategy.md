# Milestone 4: Strategy

> **Provide alongside:** `product-overview.md`
> **Prerequisites:** Milestone 1 (Foundation) complete, Milestone 2 (Dashboard) complete, Milestone 3 (Trade History) complete

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
