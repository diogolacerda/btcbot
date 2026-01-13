# Strategy

## Overview

The Strategy section provides comprehensive control over bot trading configuration including risk parameters, grid settings, MACD filters, and execution controls. Users can view current strategy status, adjust position sizing and leverage, configure grid spacing and take profit targets, enable MACD-based activation filters, and start/stop/pause strategy execution with real-time risk calculations and validation.

## User Flows

- View current strategy configuration and execution status (active/paused/stopped/waiting)
- View cycle performance metrics (time since start, P&L, trades, win rate)
- Start strategy with MACD activation requirement
- Pause strategy (keeps positions, cancels new orders)
- Stop strategy with confirmation (cancels pending orders, keeps positions until TP)
- Resume paused strategy
- Adjust risk parameters (position size, max total orders, leverage, margin mode)
- View live risk calculations (total capital at risk, max loss per trade, liquidation risk)
- Configure grid settings (spacing type, spacing value, grid range, take profit percentage)
- Preview grid levels based on current BTC price and settings
- Enable/disable MACD filter with parameter configuration (fast/slow/signal periods, timeframe)
- Configure advanced settings (dynamic TP based on funding rate, auto-reactivation mode)
- Save changes with validation warnings (minimum values, risk alerts, fee warnings)
- View explanatory tooltips and recommended settings

## Design Decisions

**Real-Time Risk Feedback:**
- Risk summary card updates instantly as user adjusts leverage or position size
- Liquidation risk indicator uses color coding (green/yellow/red zones)
- Live calculations show total capital at risk and max loss per trade

**Grid Preview:**
- Shows actual price levels based on current BTC price
- Updates as user changes spacing or grid range
- Helps users visualize order placement strategy

**Validation and Warnings:**
- In-context warnings for risky settings (high leverage, tight spacing, low TP)
- Helpful tooltips explain each setting with recommended values
- Prevents saving invalid configurations

**Confirmation Dialogs:**
- Critical actions (stop, start) require confirmation
- Dialogs explain consequences and requirements (e.g., MACD wait state)

**Organized Layout:**
- Clear visual hierarchy: Status → Risk → Grid → Filters → Advanced
- Collapsible advanced settings keep main form focused
- Grouped related settings (all grid settings together, all MACD settings together)

**Status-Based Controls:**
- Control buttons adapt to current state (Start when stopped, Pause/Stop when active, Resume when paused)
- Status badge clearly indicates current execution state

## Data Used

**Entities:**
- `Strategy` - Complete strategy configuration including status, cycle info, risk parameters, grid settings, MACD filter, advanced settings
- `CurrentMarket` - Live BTC price and funding rate for calculations
- `RiskSummary` - Calculated risk metrics based on current settings
- `GridLevel` - Preview of grid price levels

**From global model:**
- Uses BTC/USDT market data
- Links to bot status and trading positions

## Visual Reference

See `screenshot.png` for the target UI design.

## Components Provided

- `Strategy` - Main container component orchestrating all strategy sections
- `StrategyStatusCard` - Status display with cycle metrics and control buttons
- `RiskParametersSection` - Position size, max orders, leverage slider, margin mode with live risk summary
- `GridSettingsSection` - Grid spacing, range, take profit configuration with grid preview
- `MACDFilterSection` - MACD toggle, parameter inputs, timeframe selector with explanations
- `AdvancedSettingsSection` - Dynamic TP configuration and auto-reactivation mode (collapsible)

## Callback Props

| Callback | Description |
|----------|-------------|
| `onStart` | Called when user confirms starting the strategy (may enter WAIT state for MACD) |
| `onPause` | Called when user confirms pausing the strategy (stops new orders, keeps positions) |
| `onStop` | Called when user confirms stopping the strategy (cancels orders, keeps positions until TP) |
| `onResume` | Called when user confirms resuming a paused strategy |
| `onUpdateRiskParameters` | Called when user changes risk parameters (position size, max orders, leverage, margin mode) |
| `onUpdateGridSettings` | Called when user changes grid settings (spacing type/value, grid range, take profit, anchor) |
| `onUpdateMACDFilter` | Called when user enables/disables MACD filter or changes MACD parameters |
| `onUpdateAdvancedSettings` | Called when user changes advanced settings (dynamic TP config, auto-reactivation mode) |
| `onSave` | Called when user clicks save button to persist all strategy changes |
