from __future__ import annotations

from fastapi import FastAPI, Query

from app.backtester import OKXClient, run_backtest_from_candles

app = FastAPI(title="OKX research automation prototype")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "okx-agent-prototype"}


@app.get("/backtest")
def backtest(
    symbol: str = Query(default="BTC-USDT", description="OKX instrument ID, e.g. BTC-USDT"),
    interval: str = Query(default="1m", description="Candlestick interval"),
    limit: int = Query(default=100, ge=10, le=300),
    short_window: int = Query(default=9, ge=2, le=30),
    long_window: int = Query(default=21, ge=3, le=60),
    initial_cash: float = Query(default=10000.0, ge=100.0),
    risk_per_trade: float = Query(default=0.02, ge=0.0, le=0.25),
    max_position_pct: float = Query(default=0.25, ge=0.0, le=1.0),
    rsi_period: int = Query(default=14, ge=2, le=50),
) -> dict:
    client = OKXClient()
    candles = client.fetch_candles(symbol=symbol, interval=interval, limit=limit)
    report = run_backtest_from_candles(
        candles,
        short_window=short_window,
        long_window=long_window,
        initial_cash=initial_cash,
        risk_per_trade=risk_per_trade,
        max_position_pct=max_position_pct,
        rsi_period=rsi_period,
    )
    report["symbol"] = symbol
    report["interval"] = interval
    return report
