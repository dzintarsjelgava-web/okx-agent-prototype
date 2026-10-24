# okx-agent-prototype

A more polished Python trading research app for OKX-style market data and strategy simulation. It is designed as a serious prototype and research tool, not a guaranteed profit engine.

## Features

- synthetic OHLCV data generation
- EMA crossover + RSI trend filtering
- risk-aware paper-trading execution
- backtest metrics including total return, drawdown, and Sharpe-style estimate
- live OKX candle fetching via public market API
- FastAPI endpoints for health checks, research runs, data export, and a lightweight dashboard

## Dashboard

Open the built-in dashboard in a browser:

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000
```

Then visit:

- http://localhost:8000/dashboard
- http://localhost:8000/health
- http://localhost:8000/research?symbol=BTC-USDT&periods=200&short_window=9&long_window=21&initial_cash=10000
- http://localhost:8000/export?format=csv&symbol=BTC-USDT&periods=200

## Quick start

### Synthetic backtest

```bash
python -m app.main run --symbol BTC-USDT --periods 200 --short-window 9 --long-window 21 --initial-cash 10000 --risk-per-trade 0.02 --max-position-pct 0.25 --rsi-period 14
```

### Live OKX backtest

```bash
python -m app.main live --symbol BTC-USDT --interval 1m --limit 100 --short-window 9 --long-window 21 --initial-cash 10000 --risk-per-trade 0.02 --max-position-pct 0.25 --rsi-period 14
```

## Important note

No trading strategy, including this one, can guarantee profit. This app is intended for research, simulation, and learning. Use paper trading only unless you fully understand the risk and exchange API requirements.

## Docker

```bash
docker compose up --build
```
