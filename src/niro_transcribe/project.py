from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Project:
    root: Path
    audio_dir: Path
    cache_dir: Path
    output_dir: Path
    skript_pdf: Path
    briefs_yaml: Path

    @classmethod
    def open(cls, root: str | Path) -> "Project":
        root = Path(root)
        proj = cls(
            root=root,
            audio_dir=root / "Material" / "Audio",
            cache_dir=root / "_intern" / "cache",
            output_dir=root / "Ergebnisse" / "O-Ton-Pläne",
            skript_pdf=root / "Material" / "Konzept" / "skript.pdf",
            briefs_yaml=root / "_intern" / "briefs.yaml",
        )
        for d in (proj.audio_dir, proj.cache_dir, proj.output_dir):
            d.mkdir(parents=True, exist_ok=True)
        return proj

    def audio_files(self) -> list[Path]:
        return sorted(
            (p for p in self.audio_dir.iterdir()
             if p.is_file() and p.suffix.lower() == ".wav"),
            key=lambda p: p.name.lower(),
        )
