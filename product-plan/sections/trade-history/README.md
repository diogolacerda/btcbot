# Trade History

## Overview

The Trade History section provides comprehensive visibility into trading performance with detailed analytics, filtering capabilities, and a sortable table of all closed trades. Users can analyze performance metrics, filter trades by various criteria, view cumulative P&L trends, and drill into individual trade details to understand their trading patterns and profitability.

## User Flows

- Select time period (today/7 days/30 days/custom) to filter all data
- View performance analytics cards (Total P&L, Win Rate, Best/Worst trades, etc.) that update based on selected filters
- Analyze cumulative P&L chart showing profit trajectory over time
- Filter trades by status (closed/open), profit/loss, entry price range, duration, quantity
- Search trades by order ID or TP order ID
- Sort trades table by any column (date, entry price, exit price, P&L, duration)
- Click trade row to open modal with full details
- View trade details including prices, P&L breakdown, timeline, TP adjustment history, and fees
- Remove individual filters via badges or clear all filters at once
- Navigate through paginated results (50 trades per page)

## Design Decisions

**Advanced Filtering System:**
- Multiple filter types: time range, status, profit/loss, price ranges, duration, quantity
- Active filter badges show at-a-glance what filters are applied
- Quick clear options for individual filters or all filters at once
- Search by order ID for quick lookup

**Sortable Table:**
- All numeric columns are sortable (price, P&L, duration)
- Visual sort indicators (up/down arrows) show current sort state
- Default sort: most recent trades first

**Performance Analytics:**
- Aggregate metrics update based on active filters
- Win rate calculation with visual indicator
- Best/worst trade highlights for quick insight
- ROI percentage alongside absolute P&L

**Cumulative P&L Chart:**
- Line chart shows profit trajectory over time
- Helps visualize consistency and drawdowns
- Time range selector for chart zoom

**Responsive Pagination:**
- Shows "X-Y of Z trades" for context
- Load more or page navigation options

## Data Used

**Entities:**
- `Trade` - Individual trade records with entry/exit prices, P&L, fees, TP adjustments
- `PerformanceMetrics` - Aggregate statistics (total P&L, ROI, win rate, averages, best/worst trades)
- `CumulativePnlDataPoint` - Time-series data for P&L chart
- `TradeFilters` - Filter criteria for querying trades
- `SortConfig` - Current sort column and direction

**From global model:**
- Uses BTC/USDT trading pair
- Links to order and position entities
- References strategy configuration (leverage, TP adjustments)

## Visual Reference

See `screenshot.png` for the target UI design.

## Components Provided

- `TradeHistory` - Main container component orchestrating all trade history sections
- `PeriodSelector` - Time range filter (today/7days/30days/custom with date picker)
- `PerformanceCards` - Analytics cards showing total P&L, win rate, averages, best/worst trades
- `PnlChart` - Cumulative P&L line chart with time range controls
- `Filters` - Filter panel with status, profit/loss, advanced filters, and search
- `FilterBadges` - Active filter tags with remove buttons and clear all option
- `TradesTable` - Sortable table of trades with pagination
- `TradeDetailsModal` - Full trade details including timeline, fees, TP adjustment history

## Callback Props

| Callback | Description |
|----------|-------------|
| `onPeriodChange` | Called when user changes time period (today/7days/30days/custom with optional date range) |
| `onFiltersChange` | Called when user updates any filter criteria (status, profit/loss, price ranges, search) |
| `onSortChange` | Called when user clicks a column header to sort (passes column name and direction) |
| `onViewTradeDetails` | Called when user clicks a trade row to view full details (passes trade ID) |
| `onSearch` | Called when user searches by order ID or TP order ID |
| `onClearFilters` | Called when user clicks "Clear all filters" link |
| `onRemoveFilter` | Called when user clicks X on a filter badge to remove specific filter |
| `onPageChange` | Called when user navigates to a different page in pagination |
