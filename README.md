# okx-agent-prototype

A lightweight Python prototype for an OKX research automation trading workflow. This MVP includes:

- a synthetic market ingestor that produces OHLCV bars
- an EMA crossover research strategy
- a paper trading manager that simulates order execution
- Docker support for local runs

## Quick start

```bash
python -m app.main --symbol BTC-USD --periods 200 --short-window 9 --long-window 21 --initial-cash 10000 --seed 42
```

## What it does

1. Generates synthetic market data for a symbol.
2. Applies an EMA crossover strategy to produce buy/sell/hold signals.
3. Simulates a paper portfolio using the strategy.
4. Writes the result to `output/portfolio_summary.json`.

## Example output

```text
Symbol: BTC-USD
Final portfolio value: $12345.67
Trades executed: 5
Results saved to output/portfolio_summary.json
```

## Docker

```bash
docker compose up --build
```

## Notes

This is intentionally a prototype and does not connect to the live OKX API yet. It provides a clean starting point for deeper research automation and execution logic.
