# Data Model

## Entities

### User
User of the Btcbot application who manages trading accounts and monitors bot performance.

### Account
Exchange account connection with BingX credentials and settings. Each account runs one active trading strategy.

### Strategy
Trading strategy configuration defining how the bot trades, including risk parameters (position size, max positions, grid spacing), filters (MACD), and execution state (running/paused/stopped).

### Trade
A completed trading transaction with entry price, exit price, profit/loss, and timestamp. Represents the historical record of bot performance.

### Order
An active buy or sell order currently placed on the exchange as part of the grid strategy. Real-time data synchronized from the exchange.

### Position
A currently open position on the exchange being managed by the bot. Real-time data showing active exposure and unrealized P&L.

## Relationships

- User has many Accounts
- Account has one Strategy (active)
- Account has many Trades
- Account has many Orders (real-time)
- Account has many Positions (real-time)
- Strategy belongs to Account
- Trade belongs to Account
- Order belongs to Account (real-time, not Strategy)
- Position belongs to Account (real-time, not Strategy)
