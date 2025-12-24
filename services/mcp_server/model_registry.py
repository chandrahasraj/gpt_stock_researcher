from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


class ModelRegistry:
    def __init__(self, config_path: str) -> None:
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Model registry not found: {self.config_path}")
        self._models = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        data = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        return data.get("models", [])

    def list_models(self) -> List[Dict[str, Any]]:
        return self._models

    def get(self, model_id: str) -> Dict[str, Any]:
        for model in self._models:
            if model.get("model_id") == model_id:
                return model
        raise KeyError(f"Unknown model_id: {model_id}")
