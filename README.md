from __future__ import annotations

import csv
import io

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response

from app.backtester import compare_strategies, run_backtest_from_candles, run_synthetic_backtest
from app.storage import list_runs

app = FastAPI(title="OKX research automation prototype")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "okx-agent-prototype"}


@app.get("/strategies")
def strategies() -> dict:
    return {
        "strategies": [
            {
                "name": "ema_rsi",
                "description": "EMA crossover with RSI confirmation.",
            },
            {
                "name": "sma_cross",
                "description": "Simple moving average cross strategy.",
            },
            {
                "name": "momentum",
                "description": "Rate-of-change momentum strategy.",
            },
        ]
    }


@app.get("/research")
def research(
    symbol: str = Query(default="BTC-USDT"),
    periods: int = Query(default=200, ge=50, le=1000),
    short_window: int = Query(default=9, ge=2, le=30),
    long_window: int = Query(default=21, ge=3, le=60),
    initial_cash: float = Query(default=10000.0, ge=100.0),
    seed: int = Query(default=42, ge=0),
    risk_per_trade: float = Query(default=0.02, ge=0.0, le=0.25),
    max_position_pct: float = Query(default=0.25, ge=0.0, le=1.0),
    rsi_period: int = Query(default=14, ge=2, le=50),
    strategy: str = Query(default="ema_rsi", pattern="^(ema_rsi|sma_cross|momentum)$"),
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
        strategy_name=strategy,
    )
    report["symbol"] = symbol
    report["source"] = "synthetic"
    return report


@app.get("/backtest")
def backtest(
    symbol: str = Query(default="BTC-USDT"),
    interval: str = Query(default="1m"),
    limit: int = Query(default=100, ge=10, le=300),
    short_window: int = Query(default=9, ge=2, le=30),
    long_window: int = Query(default=21, ge=3, le=60),
    initial_cash: float = Query(default=10000.0, ge=100.0),
    risk_per_trade: float = Query(default=0.02, ge=0.0, le=0.25),
    max_position_pct: float = Query(default=0.25, ge=0.0, le=1.0),
    rsi_period: int = Query(default=14, ge=2, le=50),
    strategy: str = Query(default="ema_rsi", pattern="^(ema_rsi|sma_cross|momentum)$"),
) -> dict:
    from app.okx_client import OKXClient

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
        strategy_name=strategy,
    )
    report["symbol"] = symbol
    report["interval"] = interval
    return report


@app.get("/compare")
def compare(
    symbol: str = Query(default="BTC-USDT"),
    periods: int = Query(default=200, ge=50, le=1000),
    initial_cash: float = Query(default=10000.0, ge=100.0),
    strategies: str = Query(default="ema_rsi,sma_cross,momentum"),
    risk_per_trade: float = Query(default=0.02, ge=0.0, le=0.25),
    max_position_pct: float = Query(default=0.25, ge=0.0, le=1.0),
    short_window: int = Query(default=9, ge=2, le=30),
    long_window: int = Query(default=21, ge=3, le=60),
    rsi_period: int = Query(default=14, ge=2, le=50),
    seed: int = Query(default=42, ge=0),
) -> dict:
    selected = [item.strip() for item in strategies.split(",") if item.strip()]
    return compare_strategies(
        symbol=symbol,
        periods=periods,
        initial_cash=initial_cash,
        strategies=selected,
        seed=seed,
        risk_per_trade=risk_per_trade,
        max_position_pct=max_position_pct,
        short_window=short_window,
        long_window=long_window,
        rsi_period=rsi_period,
    )


@app.get("/runs")
def runs(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return {"runs": list_runs(limit=limit)}


@app.get("/dashboard")
def dashboard() -> HTMLResponse:
    html = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>OKX Strategy Dashboard</title>
        <style>
          body { font-family: Arial, sans-serif; background: #0b1020; color: #e5e7eb; margin: 0; }
          .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
          .card { background: rgba(17,24,39,0.9); border: 1px solid rgba(148,163,184,0.22); border-radius: 12px; padding: 18px; margin-bottom: 18px; }
          .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
          .metric { background: rgba(15,23,42,0.8); padding: 14px; border-radius: 10px; }
          .label { color: #94a3b8; font-size: 12px; margin-bottom: 8px; }
          .value { font-size: 1.7rem; font-weight: bold; }
          table { width: 100%; border-collapse: collapse; }
          th, td { text-align: left; padding: 10px; border-bottom: 1px solid rgba(148,163,184,0.18); }
          th { color: #a5b4cf; }
          button, input { border-radius: 8px; padding: 10px 12px; border: 1px solid rgba(148,163,184,0.25); }
          button { background: linear-gradient(135deg, #22c55e, #38bdf8); border: none; color: #04151d; font-weight: bold; cursor: pointer; }
          input { background: rgba(15,23,42,0.9); color: #e5e7eb; width: 100%; }
          .good { color: #4ade80; }
          .warn { color: #f87171; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="card">
            <h2>Strategy comparison dashboard</h2>
            <div class="grid">
              <div><div class="label">Symbol</div><input id="symbol" value="BTC-USDT" /></div>
              <div><div class="label">Periods</div><input id="periods" value="200" /></div>
              <div><div class="label">Initial cash</div><input id="initialCash" value="10000" /></div>
              <div><div class="label">Strategies</div><input id="strategies" value="ema_rsi,sma_cross,momentum" /></div>
              <div><div class="label">&nbsp;</div><button id="runBtn">Run comparison</button></div>
            </div>
          </div>

          <div class="grid" id="summaryGrid"></div>

          <div class="card">
            <h3>Comparison results</h3>
            <table>
              <thead>
                <tr><th>Strategy</th><th>Total return</th><th>Max drawdown</th><th>Sharpe</th><th>Portfolio value</th><th>Trades</th></tr>
              </thead>
              <tbody id="resultsBody"></tbody>
            </table>
          </div>

          <div class="card">
            <h3>Recent saved runs</h3>
            <table>
              <thead>
                <tr><th>ID</th><th>Strategy</th><th>Symbol</th><th>Source</th><th>Created</th></tr>
              </thead>
              <tbody id="runsBody"></tbody>
            </table>
          </div>
        </div>

        <script>
          const summaryGrid = document.getElementById('summaryGrid');
          const resultsBody = document.getElementById('resultsBody');
          const runsBody = document.getElementById('runsBody');

          async function loadRuns() {
            const response = await fetch('/runs?limit=10');
            const data = await response.json();
            runsBody.innerHTML = (data.runs || []).map((run) => `
              <tr>
                <td>${run.id}</td>
                <td>${run.strategy}</td>
                <td>${run.symbol}</td>
                <td>${run.source}</td>
                <td>${run.created_at}</td>
              </tr>
            `).join('');
          }

          async function runComparison() {
            const params = new URLSearchParams({
              symbol: document.getElementById('symbol').value,
              periods: document.getElementById('periods').value,
              initial_cash: document.getElementById('initialCash').value,
              strategies: document.getElementById('strategies').value,
              seed: '42',
              short_window: '9',
              long_window: '21',
              rsi_period: '14',
              risk_per_trade: '0.02',
              max_position_pct: '0.25'
            });

            const response = await fetch('/compare?' + params.toString());
            const data = await response.json();
            const best = data.best_strategy || 'n/a';
            summaryGrid.innerHTML = `
              <div class="metric"><div class="label">Best strategy</div><div class="value">${best}</div></div>
              <div class="metric"><div class="label">Best return</div><div class="value">${((data.best_total_return || 0) * 100).toFixed(2)}%</div></div>
              <div class="metric"><div class="label">Results count</div><div class="value">${(data.results || []).length}</div></div>
            `;

            resultsBody.innerHTML = (data.results || []).map((entry) => `
              <tr>
                <td>${entry.strategy}</td>
                <td>${((entry.metrics?.total_return || 0) * 100).toFixed(2)}%</td>
                <td>${((entry.metrics?.max_drawdown || 0) * 100).toFixed(2)}%</td>
                <td>${(entry.metrics?.sharpe_ratio || 0).toFixed(2)}</td>
                <td>${Number(entry.portfolio_value || 0).toFixed(2)}</td>
                <td>${entry.trade_count || 0}</td>
              </tr>
            `).join('');

            await loadRuns();
          }

          document.getElementById('runBtn').addEventListener('click', runComparison);
          runComparison();
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
    strategy: str = Query(default="ema_rsi", pattern="^(ema_rsi|sma_cross|momentum)$"),
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
        strategy_name=strategy,
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
