"""Testdaten für die Sammler-Tests: Wegwerf-Repo mit Remote und Worktree; später Chargen, Sitzungen, Gedächtnis.
Alle Zeiten in Ortszeit; „heute“ ist ein festes Datum, das die Tests vorgeben."""
from __future__ import annotations

import os
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path


def lokal(tag: date, stunde: int, minute: int = 0) -> datetime:
    return datetime(tag.year, tag.month, tag.day, stunde, minute).astimezone()


def git(ordner: Path, *args: str, env: dict | None = None) -> str:
    umgebung = {**os.environ, **(env or {})}
    aus = subprocess.run(["git", "-C", str(ordner), *args], capture_output=True, text=True, env=umgebung)
    if aus.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {aus.stderr}")
    return aus.stdout


def commit(ordner: Path, botschaft: str, wann: datetime) -> None:
    env = {"GIT_AUTHOR_DATE": wann.isoformat(), "GIT_COMMITTER_DATE": wann.isoformat()}
    git(ordner, "add", "-A")
    git(ordner, "commit", "-q", "-m", botschaft, env=env)


def repo_anlegen(basis: Path, heute: date) -> dict:
    """Repo mit origin: A0 (gestern, gepusht), A (heute, gepusht), B auf claude/x (heute, ungepusht); Worktree wt auf
    claude/x mit geänderter tools/b.txt; ein Stash; im Hauptordner unversioniert: tools/a.txt geändert, tools/motion/
    (2 neu), NOTIZ.md (neu), tools/bin.dat (neu, binär)."""
    gestern = heute - timedelta(days=1)
    repo = basis / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@test")
    git(repo, "config", "user.name", "test")
    git(repo, "config", "commit.gpgsign", "false")
    (repo / ".gitignore").write_text("/projects/\n/berichte/\n")
    (repo / "tools").mkdir()
    (repo / "tools" / "a.txt").write_text("a\n")
    commit(repo, "A0 gestern", lokal(gestern, 9))
    origin = basis / "origin.git"
    git(basis, "init", "-q", "--bare", str(origin))
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "-u", "origin", "main")
    (repo / "tools" / "a.txt").write_text("a2\n")
    commit(repo, "A heute", lokal(heute, 10))
    git(repo, "push", "-q")
    git(repo, "checkout", "-q", "-b", "claude/x")
    (repo / "tools" / "b.txt").write_text("b\n")
    commit(repo, "B ungepusht", lokal(heute, 11, 30))
    git(repo, "checkout", "-q", "main")
    wt = basis / "wt"
    git(repo, "worktree", "add", "-q", str(wt), "claude/x")
    (wt / "tools" / "b.txt").write_text("b geändert\n")
    (repo / "tools" / "a.txt").write_text("stash\n")
    git(repo, "stash", "-q")
    (repo / "tools" / "a.txt").write_text("a3 lokal\n")
    (repo / "tools" / "motion" / "src").mkdir(parents=True)
    (repo / "tools" / "motion" / "neu.ts").write_text("Inhalt der neuen Datei\n")
    (repo / "tools" / "motion" / "src" / "x.ts").write_text("x\n")
    (repo / "NOTIZ.md").write_text("notiz\n")
    (repo / "tools" / "bin.dat").write_bytes(b"\x00\x01\x02")
    return {"repo": repo, "wt": wt, "origin": origin}


def chargen_anlegen(repo: Path, heute: date) -> None:
    """Chargen in beiden Tiefen: Kunde/Projekt/2026-09 Charge (Protokoll mit drei Überschriftenformen, Ergebnisse mit
    a.mp4 heute, b.mp4 gestern, .DS_Store heute), Kunde/2026-08 Kurz (Sammel-Überschrift + Klammerform) und fünf
    Chargen K0–K4 nur mit der Sammel-Überschrift „Medien aufs NAS verschoben“ (zusammen sechs)."""
    gestern = heute - timedelta(days=1)
    iso, deutsch = heute.isoformat(), heute.strftime("%d.%m.%Y")
    c1 = repo / "projects" / "Kunde" / "Projekt" / "2026-09 Charge"
    (c1 / "Ergebnisse" / "Export").mkdir(parents=True)
    (c1 / "Protokoll.md").write_text(
        f"# Protokoll\n\n## {iso} 11:07 — AutoCut: Kantenprüfung\n\nText\n\n## Session {deutsch} — Feinschnitt\n\n"
        f"## {gestern.isoformat()} — Gestern\n\nText\n")
    for name, wann in (("Export/a.mp4", lokal(heute, 12)), ("Export/b.mp4", lokal(gestern, 12)), (".DS_Store", lokal(heute, 12))):
        datei = c1 / "Ergebnisse" / name
        datei.write_bytes(b"x")
        os.utime(datei, (wann.timestamp(), wann.timestamp()))
    c2 = repo / "projects" / "Kunde" / "2026-08 Kurz"
    c2.mkdir(parents=True)
    (c2 / "Protokoll.md").write_text(f"# P\n\n## {iso} — Medien aufs NAS verschoben\n\n## Overlay-Export Video 1 ({iso})\n")
    for i in range(5):
        c = repo / "projects" / f"K{i}" / "P" / "2026-01 C"
        c.mkdir(parents=True)
        (c / "Protokoll.md").write_text(f"# P\n\n## {iso} — Medien aufs NAS verschoben\n")
