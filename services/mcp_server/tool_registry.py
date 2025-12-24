from __future__ import annotations

from typing import Any, Dict, List


class ToolRegistry:
    def __init__(self) -> None:
        self._tools = [
            {
                "name": "init_run_context",
                "description": "Initialize run context and paths",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "as_of_date": {"type": "string"},
                        "mode": {"type": "string"},
                        "model_id": {"type": "string"},
                    },
                    "required": ["ticker", "as_of_date", "mode", "model_id"],
                },
            },
            {
                "name": "fetch_sec_filings",
                "description": "Fetch SEC filings metadata",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "forms": {"type": "array", "items": {"type": "string"}},
                        "limit": {"type": "integer"},
                    },
                    "required": ["ticker", "forms"],
                },
            },
        ]

    def list_tools(self) -> List[Dict[str, Any]]:
        return self._tools
