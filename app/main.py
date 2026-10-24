from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from app.market_data import generate_market_data
from app.strategy import EmaCrossoverStrategy
from app.paper_trading import PaperOrderManager


def run_simulation(
    symbol: str = "BTC-USD",
    periods: int = 200,
    short_window: int = 9,
    long_window: int = 21,
    initial_cash: float = 10_000.0,
    seed: int = 42,
) -> Dict[str, Any]:
    snapshot = generate_market_data(symbol=symbol, periods=periods, seed=seed)
    prices = [bar.close for bar in snapshot.bars]
    timestamps = [bar.timestamp.isoformat() for bar in snapshot.bars]

    strategy = EmaCrossoverStrategy(short_window=short_window, long_window=long_window)
    signals = strategy.generate(prices=prices, timestamps=timestamps)
    decision_rows = [
        {
            "timestamp": signal.timestamp,
            "price": signal.price,
            "short_ema": signal.short_ema,
            "long_ema": signal.long_ema,
            "signal": signal.signal,
        }
        for signal in signals
    ]

    manager = PaperOrderManager(initial_cash=initial_cash)
    for signal in decision_rows:
        current_action = signal["signal"]
        current_price = float(signal["price"])
        current_time = signal["timestamp"]

        if current_action == "buy" and manager.position == 0:
            manager.buy(price=current_price, timestamp=current_time)
        elif current_action == "sell" and manager.position > 0:
            manager.sell(price=current_price, timestamp=current_time)

        manager.equity_history.append({
            "timestamp": current_time,
            "equity": manager.portfolio_value(current_price),
        })

    final_price = prices[-1]
    summary = {
        "symbol": symbol,
        "periods": periods,
        "initial_cash": initial_cash,
        "final_cash": manager.cash,
        "final_position": manager.position,
        "portfolio_value": manager.portfolio_value(final_price),
        "trade_count": len(manager.trades),
        "signals": decision_rows,
        "trades": [trade.__dict__ for trade in manager.trades],
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Prototype OKX research automation trading agent")
    parser.add_argument("--symbol", default="BTC-USD")
    parser.add_argument("--periods", type=int, default=200)
    parser.add_argument("--short-window", type=int, default=9)
    parser.add_argument("--long-window", type=int, default=21)
    parser.add_argument("--initial-cash", type=float, default=10_000.0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    summary = run_simulation(
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


if __name__ == "__main__":
    main()
