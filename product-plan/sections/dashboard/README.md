# Dashboard

## Overview

The Dashboard provides real-time visibility into bot health, trading activity, and performance. Users can monitor bot status, check P&L metrics, view active positions/orders, and track recent trading events - all within a selected time period (today, 7 days, 30 days, or custom range).

## User Flows

- Select time period (today/7 days/30 days/custom) to filter all dashboard data
- View current bot status and understand why it's in current state (active/paused/stopped/wait)
- Execute bot controls (pause/stop/resume/start) with confirmation dialogs
- Monitor real-time market conditions (BTC price, funding rate, MACD signal, grid range)
- Check performance metrics (realized P&L, trades closed) for selected period
- Review active positions with unrealized P&L
- Monitor active grid orders
- Click position to view detailed modal (TP price, liquidation, etc.)
- Track recent trading activity and events (order fills, trades closed, strategy changes)

## Design Decisions

**Color-Coded Status System:**
- Green (emerald) for ACTIVE status and profitable positions
- Yellow (amber) for PAUSED status and warnings
- Red for STOPPED status and losses
- Gray for WAIT status

**Real-Time Updates:**
- All cards display "last updated" timestamps
- Market data shows 24h price change with directional indicators
- Position unrealized P&L updates based on current price

**Confirmation Dialogs:**
- Critical actions (pause/stop/resume/start) require user confirmation
- Dialogs explain the consequences of each action

**Responsive Layout:**
- Cards stack vertically on mobile
- Tables adapt with horizontal scrolling where needed
- Period selector remains accessible at all viewport sizes

## Data Used

**Entities:**
- `BotStatusData` - Current bot state, cycle information, last update time
- `MarketData` - BTC price, funding rate, MACD signal, grid range
- `PerformanceMetrics` - Today's and total P&L, trade counts, averages
- `Position` - Open positions with entry/current prices, unrealized P&L, TP/liquidation prices
- `Order` - Active grid orders with price, side, quantity, status
- `ActivityEvent` - Recent trading events with type, description, timestamp

**From global model:**
- Uses BTC/USDT trading pair data
- Links to order and trade entities

## Visual Reference

See `screenshot.png` for the target UI design.

## Components Provided

- `Dashboard` - Main container component that orchestrates all dashboard sections
- `PeriodSelector` - Dropdown to filter data by time period
- `BotStatusCard` - Displays bot status with controls and cycle information
- `MarketOverviewCard` - Shows current BTC price, funding rate, MACD signal, grid range
- `PerformanceMetricsCard` - Performance stats in Today/Total layout
- `PositionsTable` - Table of open positions with unrealized P&L
- `OrdersTable` - Table of active grid orders
- `ActivityFeed` - Timeline of recent trading events
- `ConfirmDialog` - Reusable confirmation modal for bot actions
- `PositionDetailsModal` - Detailed view of a position when clicked

## Callback Props

| Callback | Description |
|----------|-------------|
| `onPeriodChange` | Called when user changes the time period filter (today/7days/30days/custom) |
| `onPause` | Called when user confirms pausing the bot |
| `onStop` | Called when user confirms stopping the bot |
| `onResume` | Called when user confirms resuming a paused bot |
| `onStart` | Called when user confirms starting a stopped bot |
| `onViewPosition` | Called when user clicks a position to view details (passes position ID) |
| `onCancelOrder` | Called when user wants to cancel an active order (passes order ID) |
