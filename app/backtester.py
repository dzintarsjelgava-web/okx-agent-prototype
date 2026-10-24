from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Dict, List

from app.market_data import MarketBar, generate_market_data
from app.paper_trading import PaperOrderManager
from app.strategy import EmaCrossoverStrategy


def _normalize_bars(candles: Iterable[Dict[str, Any]]) -> List[MarketBar]:
    bars: List[MarketBar] = []
    for candle in candles:
        if isinstance(candle, MarketBar):
            bars.append(candle)
            continue

        timestamp = candle.get("timestamp") or candle.get("time") or candle.get("datetime")
        bars.append(
            MarketBar(
                timestamp=timestamp,
                open=float(candle.get("open", candle.get("o", 0.0))),
                high=float(candle.get("high", candle.get("h", 0.0))),
                low=float(candle.get("low", candle.get("l", 0.0))),
                close=float(candle.get("close", candle.get("c", 0.0))),
                volume=float(candle.get("volume", candle.get("v", 0.0))),
            )
        )
    return bars


def _calculate_metrics(equity_curve: List[float], initial_cash: float) -> Dict[str, float]:
    if not equity_curve:
        return {
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
        }

    total_return = (equity_curve[-1] / max(initial_cash, 1e-9)) - 1.0

    peak = equity_curve[0]
    max_drawdown = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = ((peak - value) / peak) if peak > 0 else 0.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    returns = []
    for idx in range(1, len(equity_curve)):
        if equity_curve[idx - 1] > 0:
            pct = (equity_curve[idx] - equity_curve[idx - 1]) / equity_curve[idx - 1]
            returns.append(pct)

    if len(returns) > 1:
        avg_return = sum(returns) / len(returns)
        variance = sum((item - avg_return) ** 2 for item in returns) / len(returns)
        vol = variance ** 0.5
        sharpe_ratio = (avg_return / vol) * (252 ** 0.5) if vol > 0 else 0.0
    else:
        sharpe_ratio = 0.0

    return {
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "win_rate": 0.0,
    }


def run_backtest_from_bars(
    bars: Iterable[Dict[str, Any]] | List[MarketBar],
    short_window: int = 9,
    long_window: int = 21,
    initial_cash: float = 10_000.0,
    risk_per_trade: float = 0.02,
    max_position_pct: float = 0.25,
    rsi_period: int = 14,
) -> Dict[str, Any]:
    normalized_bars = _normalize_bars(bars)
    if not normalized_bars:
        raise ValueError("No market bar data was provided for backtesting.")

    prices = [bar.close for bar in normalized_bars]
    timestamps = [str(bar.timestamp) for bar in normalized_bars]

    strategy = EmaCrossoverStrategy(short_window=short_window, long_window=long_window, rsi_period=rsi_period)
    signals = strategy.generate(prices=prices, timestamps=timestamps)

    decision_rows = [
        {
            "timestamp": signal.timestamp,
            "price": signal.price,
            "short_ema": signal.short_ema,
            "long_ema": signal.long_ema,
            "signal": signal.signal,
            "strength": signal.strength,
            "rsi": signal.rsi,
            "trend_filter": signal.trend_filter,
        }
        for signal in signals
    ]

    manager = PaperOrderManager(
        initial_cash=initial_cash,
        risk_per_trade=risk_per_trade,
        max_position_pct=max_position_pct,
    )
    equity_curve: List[float] = []
    for signal in decision_rows:
        action = signal["signal"]
        price = float(signal["price"])
        timestamp = signal["timestamp"]

        if action == "buy" and manager.position == 0:
            manager.buy(price=price, timestamp=timestamp)
        elif action == "sell" and manager.position > 0:
            manager.sell(price=price, timestamp=timestamp)

        equity = manager.portfolio_value(price)
        equity_curve.append(equity)
        manager.equity_history.append({"timestamp": timestamp, "equity": equity})

    metrics = _calculate_metrics(equity_curve, initial_cash)
    final_price = prices[-1]
    return {
        "source": "bars",
        "bars_processed": len(normalized_bars),
        "initial_cash": initial_cash,
        "final_cash": manager.cash,
        "final_position": manager.position,
        "portfolio_value": manager.portfolio_value(final_price),
        "trade_count": len(manager.trades),
        "realized_pnl": manager.realized_pnl,
        "metrics": metrics,
        "signals": decision_rows,
        "trades": [trade.__dict__ for trade in manager.trades],
    }


def run_backtest_from_candles(
    candles: Iterable[Dict[str, Any]],
    short_window: int = 9,
    long_window: int = 21,
    initial_cash: float = 10_000.0,
    risk_per_trade: float = 0.02,
    max_position_pct: float = 0.25,
    rsi_period: int = 14,
) -> Dict[str, Any]:
    return run_backtest_from_bars(
        candles,
        short_window=short_window,
        long_window=long_window,
        initial_cash=initial_cash,
        risk_per_trade=risk_per_trade,
        max_position_pct=max_position_pct,
        rsi_period=rsi_period,
    )


def run_synthetic_backtest(
    symbol: str = "BTC-USDT",
    periods: int = 200,
    short_window: int = 9,
    long_window: int = 21,
    initial_cash: float = 10_000.0,
    seed: int = 42,
    risk_per_trade: float = 0.02,
    max_position_pct: float = 0.25,
    rsi_period: int = 14,
) -> Dict[str, Any]:
    snapshot = generate_market_data(symbol=symbol, periods=periods, seed=seed)
    report = run_backtest_from_bars(
        snapshot.bars,
        short_window=short_window,
        long_window=long_window,
        initial_cash=initial_cash,
        risk_per_trade=risk_per_trade,
        max_position_pct=max_position_pct,
        rsi_period=rsi_period,
    )
    report["symbol"] = symbol
    report["source"] = "synthetic"
    return report
