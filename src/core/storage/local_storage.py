from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


class LocalStorage:
    def __init__(self, base_dir: str = "runs") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def ensure_dir(self, path: str) -> Path:
        full_path = self.base_dir / path
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    def write_json(self, path: str, payload: Dict[str, Any]) -> str:
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(json.dumps(payload, indent=2, default=str))
        return str(full_path)

    def write_text(self, path: str, content: str) -> str:
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return str(full_path)

    def read_json(self, path: str) -> Dict[str, Any]:
        full_path = self.base_dir / path
        return json.loads(full_path.read_text())

    def exists(self, path: str) -> bool:
        return (self.base_dir / path).exists()

    def path(self, path: str) -> str:
        return str(self.base_dir / path)

    def list_runs(self) -> list[str]:
        return [p.name for p in self.base_dir.iterdir() if p.is_dir()]
