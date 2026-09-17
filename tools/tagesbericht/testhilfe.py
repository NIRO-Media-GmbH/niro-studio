"""Testdaten für die Sammler-Tests: Wegwerf-Repo mit Remote und Worktree; später Chargen, Sitzungen, Gedächtnis.
Alle Zeiten in Ortszeit; „heute“ ist ein festes Datum, das die Tests vorgeben."""
from __future__ import annotations

import json
import os
import subprocess
from datetime import date, datetime, timedelta, timezone
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


def _ts(wann: datetime) -> str:
    return wann.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _rec(typ: str, wann: datetime, inhalt, cwd: Path, branch: str, **extra) -> dict:
    d = {"type": typ, "timestamp": _ts(wann), "cwd": str(cwd), "gitBranch": branch, "isSidechain": False,
         "message": {"role": "user" if typ == "user" else "assistant", "content": inhalt}}
    d.update(extra)
    return d


def sitzungen_anlegen(projects_dir: Path, repo: Path, wt: Path, heute: date) -> dict:
    """Zwei Sitzungsordner (Hauptordner und Worktree). s1: Titel „Test-Sitzung“, 16 Aufträge heute (plus Meta,
    System-Reminder, Abbruch — zählen nicht), 2 Tool-Fehler (einer beginnt mit „Exit code 1“), Edit auf eine Charge ohne Protokoll, Write auf tools/neu.py,
    Sidechain-Text, Schlussbericht 10:00, ein Auftrag gestern 22:00, eine kaputte Zeile, ein Subagenten-Verlauf im
    Unterordner. s2 (Worktree): ein Auftrag, danach fünf Tool-Fehler ohne Antwort. alt.jsonl: heute-Datensatz, aber
    Änderungszeit vorgestern."""
    from umgebung import schluessel_fuer
    gestern = heute - timedelta(days=1)
    haupt = projects_dir / schluessel_fuer(repo)
    wt_ordner = projects_dir / (schluessel_fuer(repo) + "--claude-worktrees-wt")
    haupt.mkdir(parents=True)
    wt_ordner.mkdir(parents=True)
    charge_datei = str(repo / "projects" / "Ohne" / "Projekt" / "2026-09 Charge" / "_intern" / "x.py")
    s1 = [
        {"type": "custom-title", "customTitle": "Test-Sitzung"},
        _rec("user", lokal(gestern, 22), "Gestern-Auftrag", repo, "main"),
        _rec("user", lokal(heute, 9, 0), "Auftrag eins", repo, "main"),
        _rec("assistant", lokal(heute, 9, 1), [{"type": "text", "text": "Ich fange an."},
                                               {"type": "tool_use", "name": "Edit", "input": {"file_path": charge_datei}}], repo, "main"),
        _rec("user", lokal(heute, 9, 2), [{"type": "tool_result", "is_error": True, "content": "Fehler: Datei fehlt\nDetails"}], repo, "main"),
        _rec("user", lokal(heute, 9, 3), "meta text", repo, "main", isMeta=True),
        _rec("user", lokal(heute, 9, 4), [{"type": "text", "text": "<system-reminder>Hinweis</system-reminder>"}], repo, "main"),
        _rec("user", lokal(heute, 9, 4), "[Request interrupted by user]", repo, "main"),
        _rec("user", lokal(heute, 9, 4), "<task-notification>fertig</task-notification>", repo, "main"),
        _rec("user", lokal(heute, 9, 4), [{"type": "tool_result", "is_error": True, "content": "Exit code 1\nls: x: No such file or directory"}], repo, "main"),
        _rec("user", lokal(heute, 9, 5), [{"type": "text", "text": "Auftrag zwei"}], repo, "main"),
        _rec("assistant", lokal(heute, 9, 6), [{"type": "text", "text": "Zwischenstand."},
                                               {"type": "tool_use", "name": "Write", "input": {"file_path": str(repo / "tools" / "neu.py")}}], repo, "main"),
    ]
    for n in range(3, 17):
        s1.append(_rec("user", lokal(heute, 9, 6 + n), f"Auftrag {n}", repo, "main"))
    s1.append(_rec("assistant", lokal(heute, 9, 30), [{"type": "text", "text": "Sidechain-Text"}], repo, "main", isSidechain=True))
    s1.append(_rec("assistant", lokal(heute, 10, 0), [{"type": "text", "text": "Schlussbericht: alles erledigt."}], repo, "main"))
    zeilen = [json.dumps(r) for r in s1]
    zeilen.insert(3, "{kaputt")
    (haupt / "s1.jsonl").write_text("\n".join(zeilen) + "\n")
    (haupt / "s1" / "subagents").mkdir(parents=True)
    (haupt / "s1" / "subagents" / "agent-1.jsonl").write_text(json.dumps(_rec("user", lokal(heute, 9, 10), "Subagent", repo, "main")) + "\n")
    s2 = [
        _rec("user", lokal(heute, 11, 0), "Offener Auftrag", wt, "claude/x"),
        _rec("assistant", lokal(heute, 11, 1), [{"type": "text", "text": "Ich prüfe."},
                                                {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}], wt, "claude/x"),
    ]
    for n in range(1, 6):
        s2.append(_rec("user", lokal(heute, 11, 1 + n),
                       [{"type": "tool_result", "is_error": True, "content": [{"type": "text", "text": f"Fehler {n}"}]}], wt, "claude/x"))
    (wt_ordner / "s2.jsonl").write_text("\n".join(json.dumps(r) for r in s2) + "\n")
    alt = haupt / "alt.jsonl"
    alt.write_text(json.dumps(_rec("user", lokal(heute, 12, 0), "Alt", repo, "main")) + "\n")
    vorgestern = lokal(heute - timedelta(days=2), 12).timestamp()
    os.utime(alt, (vorgestern, vorgestern))
    return {"haupt": haupt, "wt": wt_ordner}


def gedaechtnis_anlegen(ordner: Path, heute: date) -> None:
    """MEMORY.md (heute, zählt nicht), notiz-a.md (heute, Beschreibung mit maskierten Anführungszeichen),
    notiz-b.md (gestern)."""
    ordner.mkdir(parents=True)
    dateien = {
        "MEMORY.md": ("- [A](notiz-a.md) — x\n", lokal(heute, 14)),
        "notiz-a.md": ('---\nname: notiz-a\ndescription: "Eine \\"Notiz\\" von heute"\nmetadata:\n  type: project\n---\n\nInhalt\n', lokal(heute, 14)),
        "notiz-b.md": ("---\nname: notiz-b\ndescription: gestern\n---\n", lokal(heute - timedelta(days=1), 14)),
    }
    for name, (text, wann) in dateien.items():
        datei = ordner / name
        datei.write_text(text)
        os.utime(datei, (wann.timestamp(), wann.timestamp()))
