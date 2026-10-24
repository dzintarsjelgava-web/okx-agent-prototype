from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Dict, List

from app.market_data import MarketBar, generate_market_data
from app.paper_trading import PaperOrderManager
from app.storage import save_run
from app.strategy import STRATEGIES, get_strategy


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
        return {"total_return": 0.0, "max_drawdown": 0.0, "sharpe_ratio": 0.0}

    total_return = (equity_curve[-1] / max(initial_cash, 1e-9)) - 1.0

    peak = equity_curve[0]
    max_drawdown = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        if peak > 0:
            drawdown = (peak - value) / peak
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
    }


def run_backtest_for_strategy(
    strategy_name: str,
    bars: Iterable[Dict[str, Any]] | List[MarketBar],
    short_window: int = 9,
    long_window: int = 21,
    initial_cash: float = 10_000.0,
    risk_per_trade: float = 0.02,
    max_position_pct: float = 0.25,
    rsi_period: int = 14,
    lookback: int = 20,
    threshold: float = 0.02,
    persist: bool = True,
    symbol: str = "BTC-USDT",
    source: str = "bars",
) -> Dict[str, Any]:
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unsupported strategy '{strategy_name}'. Available: {list(STRATEGIES.keys())}")

    normalized_bars = _normalize_bars(bars)
    if not normalized_bars:
        raise ValueError("No market bar data was provided for backtesting.")

    strategy_class = get_strategy(strategy_name)
    strategy = strategy_class(short_window=short_window, long_window=long_window, rsi_period=rsi_period) if strategy_name == "ema_rsi" else strategy_class(short_window=short_window, long_window=long_window) if strategy_name == "sma_cross" else strategy_class(lookback=lookback, threshold=threshold)

    prices = [bar.close for bar in normalized_bars]
    timestamps = [str(bar.timestamp) for bar in normalized_bars]
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
    report = {
        "strategy": strategy_name,
        "source": source,
        "symbol": symbol,
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

    if persist:
        save_run(strategy=strategy_name, symbol=symbol, source=source, summary=report)

    return report


def run_backtest_from_bars(
    bars: Iterable[Dict[str, Any]] | List[MarketBar],
    short_window: int = 9,
    long_window: int = 21,
    initial_cash: float = 10_000.0,
    risk_per_trade: float = 0.02,
    max_position_pct: float = 0.25,
    rsi_period: int = 14,
) -> Dict[str, Any]:
    return run_backtest_for_strategy(
        strategy_name="ema_rsi",
        bars=bars,
        short_window=short_window,
        long_window=long_window,
        initial_cash=initial_cash,
        risk_per_trade=risk_per_trade,
        max_position_pct=max_position_pct,
        rsi_period=rsi_period,
        persist=False,
    )


def run_backtest_from_candles(
    candles: Iterable[Dict[str, Any]],
    short_window: int = 9,
    long_window: int = 21,
    initial_cash: float = 10_000.0,
    risk_per_trade: float = 0.02,
    max_position_pct: float = 0.25,
    rsi_period: int = 14,
    strategy_name: str = "ema_rsi",
) -> Dict[str, Any]:
    return run_backtest_for_strategy(
        strategy_name=strategy_name,
        bars=candles,
        short_window=short_window,
        long_window=long_window,
        initial_cash=initial_cash,
        risk_per_trade=risk_per_trade,
        max_position_pct=max_position_pct,
        rsi_period=rsi_period,
        persist=False,
        source="live_candles",
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
    strategy_name: str = "ema_rsi",
) -> Dict[str, Any]:
    snapshot = generate_market_data(symbol=symbol, periods=periods, seed=seed)
    report = run_backtest_for_strategy(
        strategy_name=strategy_name,
        bars=snapshot.bars,
        short_window=short_window,
        long_window=long_window,
        initial_cash=initial_cash,
        risk_per_trade=risk_per_trade,
        max_position_pct=max_position_pct,
        rsi_period=rsi_period,
        persist=True,
        symbol=symbol,
        source="synthetic",
    )
    return report


def compare_strategies(
    symbol: str = "BTC-USDT",
    periods: int = 200,
    initial_cash: float = 10_000.0,
    strategies: List[str] | None = None,
    seed: int = 42,
    risk_per_trade: float = 0.02,
    max_position_pct: float = 0.25,
    short_window: int = 9,
    long_window: int = 21,
    rsi_period: int = 14,
) -> Dict[str, Any]:
    selected = strategies or ["ema_rsi", "sma_cross", "momentum"]
    snapshot = generate_market_data(symbol=symbol, periods=periods, seed=seed)
    results = []
    for strategy_name in selected:
        strategy_report = run_backtest_for_strategy(
            strategy_name=strategy_name,
            bars=snapshot.bars,
            short_window=short_window,
            long_window=long_window,
            initial_cash=initial_cash,
            risk_per_trade=risk_per_trade,
            max_position_pct=max_position_pct,
            rsi_period=rsi_period,
            persist=True,
            symbol=symbol,
            source="compare",
        )
        results.append(strategy_report)

    best = max(results, key=lambda item: item["metrics"]["total_return"]) if results else None
    return {
        "symbol": symbol,
        "results": results,
        "best_strategy": best["strategy"] if best else None,
        "best_total_return": best["metrics"]["total_return"] if best else 0.0,
    }


__all__ = [
    "compare_strategies",
    "run_backtest_for_strategy",
    "run_backtest_from_bars",
    "run_backtest_from_candles",
    "run_synthetic_backtest",
]
