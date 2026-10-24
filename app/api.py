from __future__ import annotations

import csv
import io

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

from app.backtester import OKXClient, run_backtest_from_candles, run_synthetic_backtest

app = FastAPI(title="OKX research automation prototype")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "okx-agent-prototype"}


@app.get("/strategies")
def strategies() -> dict:
    return {
        "strategies": [
            {
                "name": "ema_rsi_crossover",
                "description": "EMA crossover combined with RSI trend filtering and risk-aware sizing.",
                "parameters": {
                    "short_window": 9,
                    "long_window": 21,
                    "rsi_period": 14,
                    "risk_per_trade": 0.02,
                    "max_position_pct": 0.25,
                },
            }
        ]
    }


@app.get("/research")
def research(
    symbol: str = Query(default="BTC-USDT", description="Asset symbol for synthetic backtest"),
    periods: int = Query(default=200, ge=50, le=1000),
    short_window: int = Query(default=9, ge=2, le=30),
    long_window: int = Query(default=21, ge=3, le=60),
    initial_cash: float = Query(default=10000.0, ge=100.0),
    seed: int = Query(default=42, ge=0),
    risk_per_trade: float = Query(default=0.02, ge=0.0, le=0.25),
    max_position_pct: float = Query(default=0.25, ge=0.0, le=1.0),
    rsi_period: int = Query(default=14, ge=2, le=50),
) -> dict:
    report = run_synthetic_backtest(
        symbol=symbol,
        periods=periods,
        short_window=short_window,
        long_window=long_window,
        initial_cash=initial_cash,
        seed=seed,
        risk_per_trade=risk_per_trade,
        max_position_pct=max_position_pct,
        rsi_period=rsi_period,
    )
    report["symbol"] = symbol
    report["source"] = "synthetic"
    return report


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


@app.get("/dashboard")
def dashboard() -> HTMLResponse:
    html = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>OKX Research Dashboard</title>
        <style>
          :root {
            --bg: #0b1020;
            --panel: #111827;
            --panel-2: #1f2937;
            --accent: #22c55e;
            --accent-2: #38bdf8;
            --text: #e5e7eb;
            --muted: #9ca3af;
            --danger: #f87171;
          }
          * { box-sizing: border-box; }
          body {
            margin: 0;
            background: linear-gradient(180deg, #0b1020 0%, #111827 100%);
            color: var(--text);
            font-family: Arial, sans-serif;
          }
          .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 32px 20px 48px;
          }
          .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 12px;
          }
          h1 {
            margin: 0;
            font-size: 2rem;
          }
          .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
          }
          .card {
            background: rgba(17,24,39,0.9);
            border: 1px solid rgba(148,163,184,0.25);
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 8px 18px rgba(0,0,0,0.18);
          }
          .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
          }
          .stat {
            background: rgba(17,24,39,0.85);
            border: 1px solid rgba(148,163,184,0.25);
            border-radius: 12px;
            padding: 16px;
          }
          .label { color: var(--muted); font-size: 0.8rem; margin-bottom: 8px; }
          .value { font-size: 1.8rem; font-weight: bold; }
          .muted { color: var(--muted); }
          table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
          }
          th, td {
            text-align: left;
            padding: 12px 10px;
            border-bottom: 1px solid rgba(148,163,184,0.2);
          }
          th { color: var(--muted); }
          button {
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            border: none;
            color: #031017;
            border-radius: 999px;
            padding: 10px 18px;
            font-weight: bold;
            cursor: pointer;
          }
          input, select {
            width: 100%;
            padding: 10px 12px;
            border-radius: 8px;
            border: 1px solid rgba(148,163,184,0.3);
            background: rgba(15,23,42,0.9);
            color: var(--text);
          }
          .good { color: var(--accent); }
          .warn { color: var(--danger); }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="topbar">
            <h1>OKX Research Dashboard</h1>
            <button id="runBtn">Run synthetic backtest</button>
          </div>

          <div class="controls card">
            <div>
              <div class="label">Symbol</div>
              <input id="symbol" value="BTC-USDT" />
            </div>
            <div>
              <div class="label">Periods</div>
              <input id="periods" type="number" value="200" />
            </div>
            <div>
              <div class="label">Short EMA</div>
              <input id="shortWindow" type="number" value="9" />
            </div>
            <div>
              <div class="label">Long EMA</div>
              <input id="longWindow" type="number" value="21" />
            </div>
            <div>
              <div class="label">Initial cash</div>
              <input id="initialCash" type="number" value="10000" />
            </div>
            <div>
              <div class="label">RSI period</div>
              <input id="rsiPeriod" type="number" value="14" />
            </div>
          </div>

          <div class="stats">
            <div class="stat">
              <div class="label">Portfolio value</div>
              <div id="portfolioValue" class="value">--</div>
            </div>
            <div class="stat">
              <div class="label">Total return</div>
              <div id="totalReturn" class="value">--</div>
            </div>
            <div class="stat">
              <div class="label">Max drawdown</div>
              <div id="maxDrawdown" class="value">--</div>
            </div>
            <div class="stat">
              <div class="label">Trades</div>
              <div id="tradeCount" class="value">--</div>
            </div>
          </div>

          <div class="card">
            <div class="muted">Recent signals</div>
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Signal</th>
                  <th>Price</th>
                  <th>Short EMA</th>
                  <th>Long EMA</th>
                  <th>RSI</th>
                </tr>
              </thead>
              <tbody id="signalTableBody"></tbody>
            </table>
          </div>
        </div>

        <script>
          const els = {
            runBtn: document.getElementById('runBtn'),
            symbol: document.getElementById('symbol'),
            periods: document.getElementById('periods'),
            shortWindow: document.getElementById('shortWindow'),
            longWindow: document.getElementById('longWindow'),
            initialCash: document.getElementById('initialCash'),
            rsiPeriod: document.getElementById('rsiPeriod'),
            portfolioValue: document.getElementById('portfolioValue'),
            totalReturn: document.getElementById('totalReturn'),
            maxDrawdown: document.getElementById('maxDrawdown'),
            tradeCount: document.getElementById('tradeCount'),
            signalTableBody: document.getElementById('signalTableBody')
          };

          async function runBacktest() {
            const params = new URLSearchParams({
              symbol: els.symbol.value,
              periods: els.periods.value,
              short_window: els.shortWindow.value,
              long_window: els.longWindow.value,
              initial_cash: els.initialCash.value,
              rsi_period: els.rsiPeriod.value,
              risk_per_trade: '0.02',
              max_position_pct: '0.25',
              seed: '42'
            });

            const response = await fetch('/research?' + params.toString());
            const report = await response.json();

            els.portfolioValue.textContent = '$' + Number(report.portfolio_value || 0).toFixed(2);
            els.totalReturn.textContent = `${((report.metrics?.total_return || 0) * 100).toFixed(2)}%`;
            els.maxDrawdown.textContent = `${((report.metrics?.max_drawdown || 0) * 100).toFixed(2)}%`;
            els.tradeCount.textContent = String(report.trade_count || 0);

            const signals = (report.signals || []).slice(-10).reverse();
            els.signalTableBody.innerHTML = signals.map((signal) => `
              <tr>
                <td>${signal.timestamp}</td>
                <td class="${signal.signal === 'buy' ? 'good' : signal.signal === 'sell' ? 'warn' : ''}">${signal.signal}</td>
                <td>${Number(signal.price || 0).toFixed(2)}</td>
                <td>${Number(signal.short_ema || 0).toFixed(4)}</td>
                <td>${Number(signal.long_ema || 0).toFixed(4)}</td>
                <td>${Number(signal.rsi || 0).toFixed(2)}</td>
              </tr>
            `).join('');
          }

          els.runBtn.addEventListener('click', runBacktest);
          runBacktest();
        </script>
      </body>
    </html>
    """
    return HTMLResponse(html)


@app.get("/export")
def export_csv(
    format: str = Query(default="json", pattern="^(json|csv)$"),
    symbol: str = Query(default="BTC-USDT"),
    periods: int = Query(default=200, ge=50, le=1000),
    short_window: int = Query(default=9, ge=2, le=30),
    long_window: int = Query(default=21, ge=3, le=60),
    initial_cash: float = Query(default=10000.0, ge=100.0),
    seed: int = Query(default=42, ge=0),
    risk_per_trade: float = Query(default=0.02, ge=0.0, le=0.25),
    max_position_pct: float = Query(default=0.25, ge=0.0, le=1.0),
    rsi_period: int = Query(default=14, ge=2, le=50),
):
    report = run_synthetic_backtest(
        symbol=symbol,
        periods=periods,
        short_window=short_window,
        long_window=long_window,
        initial_cash=initial_cash,
        seed=seed,
        risk_per_trade=risk_per_trade,
        max_position_pct=max_position_pct,
        rsi_period=rsi_period,
    )

    if format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        if report.get("signals"):
            headers = ["timestamp", "signal", "price", "short_ema", "long_ema", "rsi", "trend_filter", "strength"]
            writer.writerow(headers)
            for signal in report["signals"]:
                writer.writerow(
                    [
                        signal.get("timestamp"),
                        signal.get("signal"),
                        signal.get("price"),
                        signal.get("short_ema"),
                        signal.get("long_ema"),
                        signal.get("rsi"),
                        signal.get("trend_filter"),
                        signal.get("strength"),
                    ]
                )
        return Response(content=buffer.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=signals.csv"})

    return JSONResponse(report)
