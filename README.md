# okx-agent-prototype

A Python prototype for OKX research and paper-trading workflows. This version adds a cleaner project structure and a live market-data backtesting path alongside the synthetic EMA strategy prototype.

## Features

- synthetic OHLCV market data generation
- EMA crossover strategy engine
- paper order manager for simulating execution
- live OKX candle fetcher via public market API
- simple FastAPI health and backtest endpoints
- Docker support for local execution

## Quick start

### Synthetic backtest

```bash
python -m app.main run --symbol BTC-USDT --periods 200 --short-window 9 --long-window 21 --initial-cash 10000 --seed 42
```

### Live OKX backtest

```bash
python -m app.main live --symbol BTC-USDT --interval 1m --limit 100 --short-window 9 --long-window 21 --initial-cash 10000
```

### Start the API

```bash
python -m app.main serve --host 0.0.0.0 --port 8000
```

Then open:

- http://localhost:8000/health
- http://localhost:8000/backtest?symbol=BTC-USDT&interval=1m&limit=100

## Docker

```bash
docker compose up --build
```

## Notes

This project is intentionally designed as a prototype. It does not yet trade live with an exchange account and should be treated as a research and simulation tool.
