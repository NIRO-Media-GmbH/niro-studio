from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Move:
    src: str
    dst: str


@dataclass
class MovePlan:
    moves: list[Move]

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps({"moves": [asdict(m) for m in self.moves]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "MovePlan":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(moves=[Move(**m) for m in data["moves"]])

    def validate(self, discovered_srcs: list[str]) -> list[str]:
        problems: list[str] = []
        discovered = set(discovered_srcs)
        srcs = [m.src for m in self.moves]
        seen: set[str] = set()
        for s in srcs:
            if s in seen:
                problems.append(f"Quelle mehrfach im Manifest: {s}")
            seen.add(s)
            if s not in discovered:
                problems.append(f"Quelle unbekannt (nicht im Footage gefunden): {s}")
        for d in sorted(discovered - seen):
            problems.append(f"Quelle fehlt im Manifest (würde verloren gehen): {d}")
        dsts: set[str] = set()
        for m in self.moves:
            if m.dst in dsts:
                problems.append(f"Ziel kollidiert (zwei Clips auf denselben Pfad): {m.dst}")
            dsts.add(m.dst)
        for m in self.moves:
            if Path(m.dst).name != Path(m.src).name:
                problems.append(f"Dateiname geändert (Originalname muss erhalten bleiben): {m.src} -> {m.dst}")
        return problems
