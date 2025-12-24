from __future__ import annotations

from typing import Any, Dict

from src.core.storage.local_storage import LocalStorage


class TrainingArtifactWriter:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def write(self, base_path: str, payloads: Dict[str, Any]) -> Dict[str, str]:
        written: Dict[str, str] = {}
        for name, payload in payloads.items():
            if isinstance(payload, str):
                written[name] = self.storage.write_text(f"{base_path}/{name}.txt", payload)
            else:
                written[name] = self.storage.write_json(f"{base_path}/{name}.json", payload)
        return written
