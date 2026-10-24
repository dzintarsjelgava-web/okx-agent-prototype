from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Signal:
    timestamp: str
    price: float
    short_ema: float
    long_ema: float
    signal: str
    strength: float = 0.0
    rsi: float = 50.0
    trend_filter: str = "neutral"


class EmaCrossoverStrategy:
    def __init__(self, short_window: int = 9, long_window: int = 21, rsi_period: int = 14):
        if short_window <= 0 or long_window <= 0:
            raise ValueError("EMA windows must be positive integers")
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")
        if rsi_period <= 1:
            raise ValueError("RSI period must be greater than 1")

        self.short_window = short_window
        self.long_window = long_window
        self.rsi_period = rsi_period

    @staticmethod
    def _ema(values: List[float], period: int) -> List[float]:
        if not values:
            return []
        multiplier = 2 / (period + 1)
        out: List[float] = []
        current = values[0]
        for value in values:
            current = (value - current) * multiplier + current
            out.append(current)
        return out

    @staticmethod
    def _rsi(values: List[float], period: int = 14) -> List[float]:
        if len(values) < period + 1:
            return [50.0 for _ in values]

        gains: List[float] = []
        losses: List[float] = []
        for idx in range(1, len(values)):
            delta = values[idx] - values[idx - 1]
            gains.append(max(delta, 0.0))
            losses.append(max(-delta, 0.0))

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        rsi = [50.0 for _ in values]

        for idx in range(period, len(values)):
            if avg_loss == 0:
                current_rsi = 100.0
            else:
                relative_strength = avg_gain / avg_loss
                current_rsi = 100.0 - (100.0 / (1.0 + relative_strength))

            rsi[idx] = current_rsi
            if idx + 1 < len(values):
                avg_gain = ((avg_gain * (period - 1)) + gains[idx]) / period
                avg_loss = ((avg_loss * (period - 1)) + losses[idx]) / period

        return rsi

    def generate(self, prices: List[float], timestamps: Optional[List[str]] = None) -> List[Signal]:
        if not prices:
            return []

        timestamps = timestamps or [str(idx) for idx in range(len(prices))]
        short_ema = self._ema(prices, self.short_window)
        long_ema = self._ema(prices, self.long_window)
        rsi_values = self._rsi(prices, self.rsi_period)

        signals: List[Signal] = []
        for index in range(len(prices)):
            if index == 0:
                signals.append(
                    Signal(
                        timestamp=timestamps[index],
                        price=prices[index],
                        short_ema=short_ema[index],
                        long_ema=long_ema[index],
                        signal="hold",
                        rsi=rsi_values[index],
                        trend_filter="neutral",
                    )
                )
                continue

            current_short = short_ema[index]
            current_long = long_ema[index]
            prev_short = short_ema[index - 1]
            prev_long = long_ema[index - 1]
            current_rsi = rsi_values[index]

            if current_short > current_long:
                trend_filter = "uptrend"
            elif current_short < current_long:
                trend_filter = "downtrend"
            else:
                trend_filter = "neutral"

            if prev_short <= prev_long and current_short > current_long and current_rsi >= 50.0 and trend_filter == "uptrend":
                action = "buy"
            elif prev_short >= prev_long and current_short < current_long and current_rsi <= 50.0 and trend_filter == "downtrend":
                action = "sell"
            else:
                action = "hold"

            strength = abs(current_short - current_long) / max(abs(current_long), 1e-9)
            strength = min(1.0, max(0.0, strength * 10.0))
            if action == "hold":
                strength *= 0.5

            signals.append(
                Signal(
                    timestamp=timestamps[index],
                    price=prices[index],
                    short_ema=current_short,
                    long_ema=current_long,
                    signal=action,
                    strength=strength,
                    rsi=current_rsi,
                    trend_filter=trend_filter,
                )
            )

        return signals
