from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

VIDEO_SUFFIXES = {".mp4", ".mov"}


@dataclass(frozen=True)
class Clip:
    path: Path
    camera: str
    sidecar: Path | None


def find_sidecar(video: Path) -> Path | None:
    """XML-Sidecar zu einem Clip finden. Erkennt exakten Stem und Sony-Muster
    <stem>M## (z. B. FX3_9709.MP4 -> FX3_9709M01.XML)."""
    if not video.parent.exists():
        return None
    for cand in video.parent.iterdir():
        if cand.suffix.lower() != ".xml":
            continue
        if cand.stem == video.stem or re.fullmatch(re.escape(video.stem) + r"M\d{2}", cand.stem):
            return cand
    return None


def discover_clips(footage_root: str | Path) -> list[Clip]:
    root = Path(footage_root)
    clips: list[Clip] = []
    for video in root.rglob("*"):
        if not video.is_file() or video.suffix.lower() not in VIDEO_SUFFIXES:
            continue
        rel = video.relative_to(root)
        camera = rel.parts[0] if len(rel.parts) > 1 else ""
        clips.append(Clip(path=video, camera=camera, sidecar=find_sidecar(video)))
    clips.sort(key=lambda c: (c.camera, c.path.name))
    return clips
