from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path

from ..cache import file_hash
from .discover import find_sidecar
from .move_plan import Move, MovePlan


@dataclass
class MoveResult:
    src: str
    dst: str
    method: str
    size: int
    sidecar_src: str | None
    sidecar_dst: str | None


def _existing_ancestor(p: Path) -> Path:
    p = p.parent
    while not p.exists():
        p = p.parent
    return p


def _same_filesystem(src: Path, dst: Path) -> bool:
    return os.stat(src).st_dev == os.stat(_existing_ancestor(dst)).st_dev


def _move_one(src: Path, dst: Path, *, force_copy: bool) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(f"Ziel existiert bereits, wird nicht überschrieben: {dst}")
    if not force_copy and _same_filesystem(src, dst):
        os.rename(src, dst)
        return "rename"
    before = file_hash(src)
    shutil.copy2(src, dst)
    if file_hash(dst) != before:
        dst.unlink(missing_ok=True)
        raise RuntimeError(f"Prüfsumme nach Kopie abweichend: {src} -> {dst}")
    src.unlink()
    return "copy"


def execute_move(move: Move, *, dry_run: bool = False, force_copy: bool = False) -> MoveResult:
    src = Path(move.src)
    dst = Path(move.dst)
    if not src.exists():
        raise FileNotFoundError(f"Quelle fehlt: {src}")
    sc_src = find_sidecar(src)
    sc_dst = (dst.parent / sc_src.name) if sc_src else None
    size = src.stat().st_size
    if dry_run:
        method = "rename" if (not force_copy and _same_filesystem(src, dst)) else "copy"
        return MoveResult(str(src), str(dst), method, size,
                          str(sc_src) if sc_src else None, str(sc_dst) if sc_dst else None)
    if dst.exists():
        raise FileExistsError(f"Ziel existiert bereits, wird nicht überschrieben: {dst}")
    if sc_dst is not None and sc_dst.exists():
        raise FileExistsError(f"Sidecar-Ziel existiert bereits, wird nicht überschrieben: {sc_dst}")
    method = _move_one(src, dst, force_copy=force_copy)
    if sc_src and sc_dst:
        try:
            _move_one(sc_src, sc_dst, force_copy=force_copy)
        except Exception:
            _move_one(dst, src, force_copy=force_copy)  # Clip zurückrollen
            raise
    return MoveResult(str(src), str(dst), method, size,
                      str(sc_src) if sc_src else None, str(sc_dst) if sc_dst else None)


def execute_plan(plan: MovePlan, log_path: str | Path, *, discovered_srcs: list[str],
                 dry_run: bool = False) -> list[MoveResult]:
    problems = plan.validate(discovered_srcs)
    if problems:
        raise ValueError(
            "Manifest unvollständig/inkonsistent — es wird NICHTS verschoben:\n" + "\n".join(problems)
        )
    log = Path(log_path)
    log.parent.mkdir(parents=True, exist_ok=True)
    results: list[MoveResult] = []
    try:
        with open(log, "a", encoding="utf-8") as fh:
            for move in plan.moves:
                res = execute_move(move, dry_run=dry_run)
                results.append(res)
                if not dry_run:
                    fh.write(json.dumps(asdict(res), ensure_ascii=False) + "\n")
                    fh.flush()
    except Exception as e:
        raise RuntimeError(
            f"Verschieben bei einem Fehler abgebrochen. Bereits erfolgte Moves stehen im Log; "
            f"mit undo('{log}') rückgängig machen. Ursache: {e}"
        ) from e
    return results


def undo(log_path: str | Path) -> None:
    lines = Path(log_path).read_text(encoding="utf-8").strip().splitlines()
    for line in reversed(lines):
        r = json.loads(line)
        _move_one(Path(r["dst"]), Path(r["src"]), force_copy=False)
        if r.get("sidecar_dst") and r.get("sidecar_src"):
            _move_one(Path(r["sidecar_dst"]), Path(r["sidecar_src"]), force_copy=False)
