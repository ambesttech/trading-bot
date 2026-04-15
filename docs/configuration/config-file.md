# Configuration File Reference

The bot is configured via a JSON file (typically `config/config.json`). This page documents every available parameter.

## Complete Example

```json
{
  "exchange": {
    "name": "binance",
    "trading_fee": 0.001,
    "trading_mode": "backtest"
  },
  "pair": {
    "base_currency": "SOL",
    "quote_currency": "USDT"
  },
  "trading_settings": {
    "timeframe": "1m",
    "period": {
      "start_date": "2024-08-01T00:00:00Z",
      "end_date": "2024-10-20T00:00:00Z"
    },
    "initial_balance": 10000,
    "historical_data_file": "data/SOL_USDT/2024/1m.csv"
  },
  "grid_strategy": {
    "type": "simple_grid",
    "spacing": "geometric",
    "num_grids": 8,
    "range": {
      "top": 250,
      "bottom": 200
    },
    "buy_ratio": 1.0,
    "sell_ratio": 0.5
  },
  "risk_management": {
    "take_profit": {
      "enabled": false,
      "threshold": 280
    },
    "stop_loss": {
      "enabled": false,
      "threshold": 180
    },
    "position_sizing": {
      "max_portfolio_fraction": 1.0,
      "min_quote_notional_per_grid": 10
    },
    "safety": {
      "enforce_tp_sl_vs_grid_range": false
    }
  },
  "execution": {
    "max_retries": 3,
    "retry_delay": 1.0,
    "max_slippage": 0.01,
    "backtest_slippage": 0.001,
    "order_polling_interval": 15.0,
    "websocket_max_retries": 5,
    "websocket_retry_base_delay": 5,
    "health_check_interval": 60,
    "circuit_breaker_failure_threshold": 5,
    "circuit_breaker_recovery_timeout": 60.0,
    "circuit_breaker_half_open_max_calls": 1,
    "reconciliation_interval": 300.0,
    "reconciliation_balance_tolerance": 0.01
  },
  "logging": {
    "log_level": "INFO",
    "log_to_file": true
  },
  "persistence": {
    "enabled": true,
    "db_path": "data/SOL_USDT/state.db"
  }
}
```

## Parameter Reference

### `exchange`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Exchange name (e.g., `binance`, `kraken`). Must be supported by CCXT. |
| `trading_fee` | float | Yes | Trading fee in decimal format (e.g., `0.001` for 0.1%). |
| `trading_mode` | string | Yes | One of `backtest`, `paper_trading`, or `live`. |

### `pair`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `base_currency` | string | Yes | Base currency symbol (e.g., `SOL`, `ETH`, `BTC`). |
| `quote_currency` | string | Yes | Quote currency symbol (e.g., `USDT`, `USDC`). |

### `trading_settings`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `timeframe` | string | Yes | OHLCV timeframe (e.g., `1m`, `5m`, `1h`, `1d`). |
| `period.start_date` | string | Yes | Start date in ISO 8601 format. |
| `period.end_date` | string | Yes | End date in ISO 8601 format. |
| `initial_balance` | float | Yes | Starting balance in quote currency. |
| `historical_data_file` | string | No | Path to local CSV file for offline backtesting. If omitted, data is fetched via CCXT. |

### `grid_strategy`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | Yes | `simple_grid` (independent levels) or `hedged_grid` (paired levels). |
| `spacing` | string | Yes | `arithmetic` (equal intervals) or `geometric` (proportional intervals). |
| `num_grids` | int | Yes | Total number of grid levels. |
| `range.top` | float | Yes | Upper price limit of the grid. |
| `range.bottom` | float | Yes | Lower price limit of the grid. |
| `buy_ratio` | float | No | Fraction of the base quantity to use for buy orders. Must be in `(0, 1.0]`. Default: `1.0`. |
| `sell_ratio` | float | No | Fraction of the base quantity to use for sell orders. Must be in `(0, 1.0]`. Default: `1.0`. |

### `risk_management`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `take_profit.enabled` | bool | Yes | Whether take-profit is active. |
| `take_profit.threshold` | float | Yes | Spot price at or above which take-profit triggers (market sell, then bot stops). Compare to your pair’s quote price. |
| `stop_loss.enabled` | bool | Yes | Whether stop-loss is active. |
| `stop_loss.threshold` | float | Yes | Spot price at or below which stop-loss triggers (market sell, then bot stops). |

**Ordering when both are enabled:** `stop_loss.threshold` must be strictly less than `take_profit.threshold`.

#### `position_sizing` *(optional)*

Caps how much of total portfolio value (in quote terms) is used to size grid limit orders and the initial inventory target. Omit this object for full-portfolio sizing (`max_portfolio_fraction` defaults to `1.0`).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_portfolio_fraction` | float | `1.0` | Fraction in `(0, 1]` of marked-to-market portfolio value used for per-grid order sizing and the 50% initial-base target. `0.5` uses half the portfolio for those calculations. |
| `min_quote_notional_per_grid` | float | — | If set, must be positive. Startup validation requires `initial_balance * max_portfolio_fraction / num_grids` ≥ this value so each grid line has enough quote notional; fails fast if the grid is too tight for the balance. |

#### `safety` *(optional)*

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enforce_tp_sl_vs_grid_range` | bool | `false` | When `true` and the corresponding exit is enabled: take-profit threshold must be **greater** than `grid_strategy.range.top`, and stop-loss threshold must be **less** than `grid_strategy.range.bottom` (long grid: exit above the grid for TP, below for SL). |

### `execution` *(optional)*

All fields are optional with sensible defaults. These fine-tune order execution behavior.

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `max_retries` | int | `3` | 1–20 | Maximum retry attempts for failed orders (live/paper). |
| `retry_delay` | float | `1.0` | 0.1–60.0 | Delay in seconds between retries. |
| `max_slippage` | float | `0.01` | 0.0001–0.1 | Maximum acceptable slippage for live/paper execution (e.g., `0.01` = 1%). |
| `backtest_slippage` | float | `0.0` | 0.0–0.1 | Fixed slippage applied to simulated fills (e.g., `0.001` = 0.1%). Buys fill higher, sells fill lower. |
| `order_polling_interval` | float | `15.0` | 1.0–300.0 | Seconds between open order status polls (live/paper). |
| `websocket_max_retries` | int | `5` | 1–50 | Maximum WebSocket reconnection attempts. |
| `websocket_retry_base_delay` | int | `5` | 1–120 | Base delay (seconds) for WebSocket reconnection backoff. |
| `health_check_interval` | int | `60` | 10–3600 | Seconds between health check pings. |
| `circuit_breaker_failure_threshold` | int | `5` | 1–50 | Consecutive API failures before circuit breaker opens. |
| `circuit_breaker_recovery_timeout` | float | `60.0` | 1.0–600.0 | Seconds to wait before recovery attempt after circuit breaker opens. |
| `circuit_breaker_half_open_max_calls` | int | `1` | 1–10 | Maximum test calls allowed in half-open state. |
| `reconciliation_interval` | float | `300.0` | 60.0–3600.0 | Seconds between reconciliation cycles that audit local state vs exchange (live mode only). |
| `reconciliation_balance_tolerance` | float | `0.01` | 0.0–100.0 | Minimum absolute difference to report a balance drift. Avoids alerts for rounding noise. |

### `logging`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `log_level` | string | Yes | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `log_to_file` | bool | Yes | Enable logging to a file in the `logs/` directory. |

### `persistence` *(optional, live mode only)*

SQLite state persistence for crash recovery. Only active in `live` trading mode — ignored in `backtest` and `paper_trading`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | `true` | Whether to persist bot state to SQLite. |
| `db_path` | string | `data/{BASE}_{QUOTE}/state_{hash}.db` | Path to the SQLite database file. The default path includes a short config hash so different grid configurations for the same pair use separate databases. |
