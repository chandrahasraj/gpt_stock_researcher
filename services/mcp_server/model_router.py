from __future__ import annotations

from typing import Any, Dict, List


class ModelRouter:
    def __init__(self) -> None:
        self._trace = []

    def generate(
        self,
        model_id: str,
        messages: List[Dict[str, Any]],
        tools_enabled: bool,
        tool_schema: Dict[str, Any],
        context_refs: List[str],
        run_id: str,
        temperature: float,
    ) -> Dict[str, Any]:
        self._trace.append({
            "model_id": model_id,
            "messages": messages,
            "tools_enabled": tools_enabled,
            "context_refs": context_refs,
            "run_id": run_id,
            "temperature": temperature,
        })
        return {
            "text": "Model routing placeholder response.",
            "tool_calls": [],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            "model_version": model_id,
            "trace_id": run_id,
        }
