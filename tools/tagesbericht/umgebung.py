"""Umgebung des Sammlers: Repo, NAS, Mac-Name, Tag, Sitzungs- und Gedächtnis-Ordner.
Spec: docs/superpowers/specs/2026-09-17-tagesbericht-design.md, Abschnitte 1–2."""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

NAS_STANDARD = "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio"


def schluessel_fuer(repo: Path) -> str:
    """Claude-Code-Ordnername eines Repos: jedes Zeichen außer A–Z/a–z/0–9 wird „-“."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(repo))


def _befehl(args: list[str], cwd: Path | None = None) -> str:
    try:
        aus = subprocess.run(args, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return aus.stdout if aus.returncode == 0 else ""


def repo_finden() -> Path:
    """Hauptordner des Repos (erste Zeile von `git worktree list`), sonst der Ordner über tools/."""
    env = os.environ.get("NIRO_STUDIO_REPO")
    if env:
        return Path(env)
    hier = Path(__file__).resolve().parent
    for zeile in _befehl(["git", "worktree", "list", "--porcelain"], cwd=hier).splitlines():
        if zeile.startswith("worktree "):
            return Path(zeile[len("worktree "):])
    return hier.parents[1]


def mac_name(repo: Path) -> str:
    """NIRO_STUDIO_MAC → git config niro.mac → Computername → „Mac“; „/“ und „:“ werden „-“."""
    name = os.environ.get("NIRO_STUDIO_MAC") or ""
    if not name:
        name = _befehl(["git", "-C", str(repo), "config", "--get", "niro.mac"]).strip()
    if not name:
        name = _befehl(["scutil", "--get", "ComputerName"]).strip()
    return name.replace("/", "-").replace(":", "-").strip() or "Mac"


def heute_bestimmen() -> date:
    env = os.environ.get("NIRO_STUDIO_HEUTE")
    return date.fromisoformat(env) if env else date.today()


def tag_parsen(wert: str | None, heute: date) -> date:
    if not wert or wert == "heute":
        return heute
    if wert == "gestern":
        return heute - timedelta(days=1)
    return date.fromisoformat(wert)


def tagesgrenzen(tag: date) -> tuple[datetime, datetime]:
    """Beginn und Ende (exklusiv) des Tages in Ortszeit, zeitzonenbewusst."""
    anfang = datetime(tag.year, tag.month, tag.day).astimezone()
    naechster = tag + timedelta(days=1)
    ende = datetime(naechster.year, naechster.month, naechster.day).astimezone()
    return anfang, ende


@dataclass
class Umgebung:
    repo: Path
    nas: Path
    mac: str
    heute: date
    projects_dir: Path
    gedaechtnis: Path

    @property
    def schluessel(self) -> str:
        return schluessel_fuer(self.repo)

    @property
    def berichte(self) -> Path:
        return self.repo / "berichte"

    def nas_da(self) -> bool:
        """Wie studio_abgleich.sh: der Ordner über „NIRO Studio“ (08_Claude Tools) muss da sein."""
        return self.nas.parent.is_dir()

    def sitzungsordner(self) -> list[Path]:
        """Alle Claude-Code-Ordner dieses Repos: Hauptordner, Worktrees, Unterordner (Präfix = Schlüssel)."""
        if not self.projects_dir.is_dir():
            return []
        return sorted(p for p in self.projects_dir.iterdir() if p.is_dir() and p.name.startswith(self.schluessel))


def umgebung_laden() -> Umgebung:
    repo = repo_finden()
    projects_dir = Path(os.environ.get("NIRO_CLAUDE_PROJECTS_DIR") or (Path.home() / ".claude" / "projects"))
    gedaechtnis = Path(os.environ.get("NIRO_CLAUDE_MEMORY_DIR") or (projects_dir / schluessel_fuer(repo) / "memory"))
    return Umgebung(
        repo=repo,
        nas=Path(os.environ.get("NIRO_STUDIO_NAS") or NAS_STANDARD),
        mac=mac_name(repo),
        heute=heute_bestimmen(),
        projects_dir=projects_dir,
        gedaechtnis=gedaechtnis,
    )
