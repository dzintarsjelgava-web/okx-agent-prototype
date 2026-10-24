from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Signal:
    timestamp: str
    price: float
    short_ema: float
    long_ema: float
    signal: str


class EmaCrossoverStrategy:
    def __init__(self, short_window: int = 9, long_window: int = 21):
        if short_window <= 0 or long_window <= 0:
            raise ValueError("EMA windows must be positive integers")
        if short_window >= long_window:
            raise ValueError("short_window must be lower than long_window")
        self.short_window = short_window
        self.long_window = long_window

    @staticmethod
    def _ema(prices: List[float], period: int) -> List[float]:
        if not prices:
            return []
        multiplier = 2 / (period + 1)
        result: List[float] = []
        previous = prices[0]
        for price in prices:
            previous = (price - previous) * multiplier + previous
            result.append(previous)
        return result

    def generate(self, prices: List[float], timestamps: Optional[List[str]] = None) -> List[Signal]:
        if not prices:
            return []
        timestamps = timestamps or [str(index) for index in range(len(prices))]
        short_ema = self._ema(prices, self.short_window)
        long_ema = self._ema(prices, self.long_window)

        signals: List[Signal] = []
        for index in range(len(prices)):
            if index == 0:
                signals.append(
                    Signal(timestamp=timestamps[index], price=prices[index], short_ema=short_ema[index], long_ema=long_ema[index], signal="hold")
                )
                continue

            current_short = short_ema[index]
            current_long = long_ema[index]
            previous_short = short_ema[index - 1]
            previous_long = long_ema[index - 1]

            if previous_short <= previous_long and current_short > current_long:
                action = "buy"
            elif previous_short >= previous_long and current_short < current_long:
                action = "sell"
            else:
                action = "hold"

            signals.append(
                Signal(
                    timestamp=timestamps[index],
                    price=prices[index],
                    short_ema=current_short,
                    long_ema=current_long,
                    signal=action,
                )
            )

        return signals
