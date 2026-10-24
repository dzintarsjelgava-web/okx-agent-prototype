from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List


@dataclass
class MarketBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class MarketSnapshot:
    symbol: str
    bars: List[MarketBar] = field(default_factory=list)

    def prices(self) -> List[float]:
        return [bar.close for bar in self.bars]


def generate_market_data(
    symbol: str = "BTC-USD",
    periods: int = 250,
    start_price: float = 100.0,
    drift: float = 0.08,
    volatility: float = 2.5,
    seed: int = 42,
) -> MarketSnapshot:
    """Create a simple synthetic OHLCV stream for strategy testing."""
    import random

    random.seed(seed)
    current = start_price
    bars: List[MarketBar] = []
    start_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(days=periods)

    for idx in range(periods):
        timestamp = start_time + timedelta(minutes=idx)
        move = random.uniform(-volatility, volatility) + drift
        open_price = current
        close_price = max(1.0, open_price * (1 + (move / 100)))
        high = max(open_price, close_price) * (1 + random.uniform(0.0, volatility / 100))
        low = min(open_price, close_price) * (1 - random.uniform(0.0, volatility / 100))
        volume = random.uniform(800, 2200)
        bars.append(
            MarketBar(
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=volume,
            )
        )
        current = close_price

    return MarketSnapshot(symbol=symbol, bars=bars)
