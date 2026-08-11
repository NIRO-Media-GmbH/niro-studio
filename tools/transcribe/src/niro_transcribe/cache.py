from __future__ import annotations

import hashlib
import json
from pathlib import Path


def file_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class TranscriptCache:
    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)

    def _path(self, file_hash: str, engine: str) -> Path:
        return self.cache_dir / f"{file_hash}.{engine}.json"

    def load(self, file_hash: str, engine: str) -> dict | None:
        p = self._path(file_hash, engine)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def save(self, file_hash: str, engine: str, data: dict) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._path(file_hash, engine).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
