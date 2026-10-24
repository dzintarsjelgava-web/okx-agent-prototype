from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Trade:
    timestamp: str
    side: str
    price: float
    quantity: float
    notes: str = ""


class PaperOrderManager:
    def __init__(
        self,
        initial_cash: float = 10_000.0,
        risk_per_trade: float = 0.02,
        max_position_pct: float = 0.25,
    ):
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.position = 0.0
        self.average_cost: Optional[float] = None
        self.risk_per_trade = max(0.0, min(1.0, float(risk_per_trade)))
        self.max_position_pct = max(0.0, min(1.0, float(max_position_pct)))
        self.trades: List[Trade] = []
        self.equity_history: List[Dict[str, float]] = []
        self.realized_pnl = 0.0

    def _current_position_value(self, price: float) -> float:
        return self.position * price

    def buy(self, price: float, timestamp: str, quantity: Optional[float] = None) -> Dict[str, float]:
        if price <= 0:
            raise ValueError("Trade price must be greater than zero")
        if quantity is None:
            quantity = (self.cash * self.max_position_pct) / price
        if self.cash < price * quantity:
            raise ValueError("Insufficient cash to buy")

        self.cash -= price * quantity
        if self.average_cost is None:
            self.average_cost = price
            self.position = quantity
        else:
            total_cost = self.average_cost * self.position + price * quantity
            total_quantity = self.position + quantity
            self.average_cost = total_cost / total_quantity
            self.position = total_quantity

        self.trades.append(
            Trade(timestamp=timestamp, side="buy", price=price, quantity=quantity, notes="opened long position")
        )
        return {"cash": self.cash, "position": self.position, "average_cost": self.average_cost}

    def sell(self, price: float, timestamp: str, quantity: Optional[float] = None) -> Dict[str, float]:
        if price <= 0:
            raise ValueError("Trade price must be greater than zero")
        if quantity is None:
            quantity = self.position
        if quantity > self.position:
            raise ValueError("Cannot sell more than current position")

        execution_value = price * quantity
        self.cash += execution_value
        self.realized_pnl += (price - (self.average_cost or price)) * quantity
        self.position -= quantity
        if self.position == 0:
            self.average_cost = None

        self.trades.append(
            Trade(timestamp=timestamp, side="sell", price=price, quantity=quantity, notes="closed long position")
        )
        return {"cash": self.cash, "position": self.position, "average_cost": self.average_cost}

    def portfolio_value(self, price: float) -> float:
        return self.cash + self._current_position_value(price)

    def summary(self, current_price: float) -> Dict[str, float]:
        return {
            "cash": self.cash,
            "position": self.position,
            "average_cost": self.average_cost,
            "portfolio_value": self.portfolio_value(current_price),
            "trade_count": len(self.trades),
            "realized_pnl": self.realized_pnl,
        }

    def simulate(self, signals: List[Dict[str, float]], price_key: str = "price") -> Dict[str, float]:
        for signal in signals:
            action = str(signal.get("signal", "hold"))
            price = float(signal[price_key])
            timestamp = str(signal.get("timestamp", "unknown"))

            if action == "buy" and self.position == 0:
                self.buy(price=price, timestamp=timestamp)
            elif action == "sell" and self.position > 0:
                self.sell(price=price, timestamp=timestamp)

            self.equity_history.append({"timestamp": timestamp, "equity": self.portfolio_value(price)})

        final_equity = self.portfolio_value(float(signals[-1][price_key])) if signals else self.cash
        return {
            "starting_cash": self.initial_cash,
            "final_cash": self.cash,
            "final_position": self.position,
            "final_equity": final_equity,
            "trade_count": len(self.trades),
            "trades": [trade.__dict__ for trade in self.trades],
        }
