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
