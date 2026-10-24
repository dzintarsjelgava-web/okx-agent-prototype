"""OKX trading prototype package."""

from .backtester import run_backtest_from_bars, run_backtest_from_candles, run_synthetic_backtest
from .okx_client import OKXClient
from .paper_trading import PaperOrderManager
from .strategy import EmaCrossoverStrategy

__all__ = [
    "EmaCrossoverStrategy",
    "OKXClient",
    "PaperOrderManager",
    "run_backtest_from_bars",
    "run_backtest_from_candles",
    "run_synthetic_backtest",
]
