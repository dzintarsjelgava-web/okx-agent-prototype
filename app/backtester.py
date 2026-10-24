from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Dict, List, Optional

from app.market_data import MarketBar, generate_market_data
from app.paper_trading import PaperOrderManager
from app.strategy import EmaCrossoverStrategy


def _normalize_bars(candles: Iterable[Dict[str, Any]]) -> List[MarketBar]:
    bars: List[MarketBar] = []
    for candle in candles:
        if isinstance(candle, MarketBar):
            bars.append(candle)
            continue

        bars.append(
            MarketBar(
                timestamp=candle.get("timestamp") or candle.get("time") or candle.get("datetime"),
                open=float(candle.get("open", candle.get("o", 0.0))),
                high=float(candle.get("high", candle.get("h", 0.0))),
                low=float(candle.get("low", candle.get("l", 0.0))),
                close=float(candle.get("close", candle.get("c", 0.0))),
                volume=float(candle.get("volume", candle.get("v", 0.0))),
            )
        )
    return bars


def run_backtest_from_bars(
    bars: Iterable[Dict[str, Any]] | List[MarketBar],
    short_window: int = 9,
    long_window: int = 21,
    initial_cash: float = 10_000.0,
) -> Dict[str, Any]:
    normalized_bars = _normalize_bars(bars)
    if not normalized_bars:
        raise ValueError("No market bar data was provided for backtesting.")

    prices = [bar.close for bar in normalized_bars]
    timestamps = [bar.timestamp.isoformat() if hasattr(bar.timestamp, "isoformat") else str(bar.timestamp) for bar in normalized_bars]

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
        action = signal["signal"]
        price = float(signal["price"])
        timestamp = signal["timestamp"]

        if action == "buy" and manager.position == 0:
            manager.buy(price=price, timestamp=timestamp)
        elif action == "sell" and manager.position > 0:
            manager.sell(price=price, timestamp=timestamp)

        manager.equity_history.append({"timestamp": timestamp, "equity": manager.portfolio_value(price)})

    final_price = prices[-1]
    return {
        "source": "bars",
        "bars_processed": len(normalized_bars),
        "initial_cash": initial_cash,
        "final_cash": manager.cash,
        "final_position": manager.position,
        "portfolio_value": manager.portfolio_value(final_price),
        "trade_count": len(manager.trades),
        "signals": decision_rows,
        "trades": [trade.__dict__ for trade in manager.trades],
    }


def run_backtest_from_candles(
    candles: Iterable[Dict[str, Any]],
    short_window: int = 9,
    long_window: int = 21,
    initial_cash: float = 10_000.0,
) -> Dict[str, Any]:
    return run_backtest_from_bars(candles, short_window=short_window, long_window=long_window, initial_cash=initial_cash)


def run_synthetic_backtest(
    symbol: str = "BTC-USDT",
    periods: int = 200,
    short_window: int = 9,
    long_window: int = 21,
    initial_cash: float = 10_000.0,
    seed: int = 42,
) -> Dict[str, Any]:
    snapshot = generate_market_data(symbol=symbol, periods=periods, seed=seed)
    report = run_backtest_from_bars(snapshot.bars, short_window=short_window, long_window=long_window, initial_cash=initial_cash)
    report["symbol"] = symbol
    report["source"] = "synthetic"
    return report
