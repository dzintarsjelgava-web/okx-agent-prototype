from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from app.backtester import OKXClient, run_backtest_from_candles, run_synthetic_backtest


def run_synthetic(args: argparse.Namespace) -> Dict[str, Any]:
    summary = run_synthetic_backtest(
        symbol=args.symbol,
        periods=args.periods,
        short_window=args.short_window,
        long_window=args.long_window,
        initial_cash=args.initial_cash,
        seed=args.seed,
    )
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    with (output_dir / "portfolio_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(f"Symbol: {summary['symbol']}")
    print(f"Final portfolio value: ${summary['portfolio_value']:.2f}")
    print(f"Trades executed: {summary['trade_count']}")
    print(f"Results saved to {output_dir / 'portfolio_summary.json'}")
    return summary


def run_live(args: argparse.Namespace) -> Dict[str, Any]:
    client = OKXClient(base_url=args.base_url)
    candles = client.fetch_candles(symbol=args.symbol, interval=args.interval, limit=args.limit)
    summary = run_backtest_from_candles(
        candles,
        short_window=args.short_window,
        long_window=args.long_window,
        initial_cash=args.initial_cash,
    )
    summary["symbol"] = args.symbol
    summary["interval"] = args.interval
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    with (output_dir / "live_backtest.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(f"Live OKX backtest for {args.symbol} ({args.interval})")
    print(f"Final portfolio value: ${summary['portfolio_value']:.2f}")
    print(f"Trades executed: {summary['trade_count']}")
    print(f"Results saved to {output_dir / 'live_backtest.json'}")
    return summary


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prototype OKX research automation trading agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    synth = subparsers.add_parser("run", help="Run a synthetic strategy simulation")
    synth.add_argument("--symbol", default="BTC-USDT")
    synth.add_argument("--periods", type=int, default=200)
    synth.add_argument("--short-window", type=int, default=9)
    synth.add_argument("--long-window", type=int, default=21)
    synth.add_argument("--initial-cash", type=float, default=10_000.0)
    synth.add_argument("--seed", type=int, default=42)
    synth.set_defaults(func=run_synthetic)

    live = subparsers.add_parser("live", help="Backtest against live OKX market candles")
    live.add_argument("--symbol", default="BTC-USDT")
    live.add_argument("--interval", default="1m")
    live.add_argument("--limit", type=int, default=100)
    live.add_argument("--short-window", type=int, default=9)
    live.add_argument("--long-window", type=int, default=21)
    live.add_argument("--initial-cash", type=float, default=10_000.0)
    live.add_argument("--base-url", default="https://www.okx.com")
    live.set_defaults(func=run_live)

    serve = subparsers.add_parser("serve", help="Run the FastAPI app")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)
    serve.set_defaults(func=lambda args: None)

    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "serve":
        import uvicorn

        uvicorn.run("app.api:app", host=args.host, port=args.port, reload=False)
        return

    args.func(args)


if __name__ == "__main__":
    main()
