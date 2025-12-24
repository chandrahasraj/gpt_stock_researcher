from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


class RunIndex:
    def __init__(self, path: str = "runs/run_index.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({}, indent=2))

    def _load(self) -> Dict[str, Any]:
        return json.loads(self.path.read_text())

    def _write(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2))

    def put(self, ticker: str, as_of_date: str, run_id: str, payload: Dict[str, Any]) -> None:
        data = self._load()
        ticker_entry = data.setdefault(ticker, {})
        ticker_entry[f"{as_of_date}#{run_id}"] = payload
        self._write(data)

    def latest_approved(self, ticker: str) -> Optional[Dict[str, Any]]:
        data = self._load().get(ticker, {})
        approved = [value for value in data.values() if value.get("status") == "approved"]
        if not approved:
            return None
        return sorted(approved, key=lambda entry: entry.get("created_at", ""))[-1]
