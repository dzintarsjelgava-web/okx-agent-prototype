from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Tuple

DB_PATH = os.path.join(os.getcwd(), "data", "research_runs.db")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy TEXT NOT NULL,
            symbol TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            summary_json TEXT NOT NULL
        )
        """
    )
    return connection


def save_run(strategy: str, symbol: str, source: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    connection = _connect()
    payload = json.dumps(summary, default=str)
    cursor = connection.execute(
        "INSERT INTO runs (strategy, symbol, source, summary_json) VALUES (?, ?, ?, ?)",
        (strategy, symbol, source, payload),
    )
    connection.commit()
    connection.close()
    return {"id": cursor.lastrowid, "strategy": strategy, "symbol": symbol, "source": source}


def list_runs(limit: int = 20) -> List[Dict[str, Any]]:
    connection = _connect()
    rows = connection.execute(
        "SELECT id, strategy, symbol, source, created_at, summary_json FROM runs ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    connection.close()
    results: List[Dict[str, Any]] = []
    for row in rows:
        run_id, strategy, symbol, source, created_at, payload = row
        summary = json.loads(payload)
        results.append({
            "id": run_id,
            "strategy": strategy,
            "symbol": symbol,
            "source": source,
            "created_at": created_at,
            "summary": summary,
        })
    return results


__all__ = ["save_run", "list_runs", "DB_PATH"]
