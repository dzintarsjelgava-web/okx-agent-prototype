from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx


class OKXClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
    ):
        self.base_url = (base_url or os.getenv("OKX_BASE_URL") or "https://www.okx.com").rstrip("/")
        self.api_key = api_key or os.getenv("OKX_API_KEY")
        self.api_secret = api_secret or os.getenv("OKX_API_SECRET")

    def fetch_candles(
        self,
        symbol: str = "BTC-USDT",
        interval: str = "1m",
        limit: int = 100,
        *,
        inst_type: str = "SPOT",
    ) -> List[Dict[str, Any]]:
        params = {
            "instId": symbol,
            "bar": interval,
            "limit": str(limit),
        }
        if inst_type:
            params["instType"] = inst_type

        response = httpx.get(f"{self.base_url}/api/v5/market/candles", params=params, timeout=20.0)
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != "0":
            raise ValueError(f"OKX API returned an error: {payload}")

        candles = payload.get("data", [])
        normalized: List[Dict[str, Any]] = []
        for item in candles:
            try:
                normalized.append(
                    {
                        "timestamp": item[0],
                        "open": float(item[1]),
                        "high": float(item[2]),
                        "low": float(item[3]),
                        "close": float(item[4]),
                        "volume": float(item[5]),
                    }
                )
            except (IndexError, TypeError, ValueError):
                continue
        return normalized
