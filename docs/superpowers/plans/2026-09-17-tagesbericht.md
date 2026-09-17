# Tagesbericht beider Studio-Macs — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein Sammler je Mac schreibt den Tagesstand (Git, Chargen, Claude-Sitzungen, Gedächtnis) nach `berichte/<Tag>/<Mac>.md`, der Ordner läuft übers NAS, und die Funktion „Tagesbericht" fasst beide Macs zu `Tagesbericht.md` zusammen — nur als Empfehlung.

**Architecture:** `tools/tagesbericht/` enthält kleine Python-Module je Quelle (`git_stand`, `chargen_stand`, `sitzungen_stand`, `gedaechtnis_stand`), einen Renderer (`bericht`), die Umgebung (`umgebung`) und den CLI-Einstieg `sammler.py`. `tools/studio_abgleich.sh` bekommt `--berichte` und ruft den Sammler vor dem Spiegeln auf; ein versionierter SessionStart-Hook startet ihn bei jedem Sitzungsstart. Der Haupt-Check ist eine Workflow-Datei für Claude, kein Code.

**Tech Stack:** Python 3 ≥ 3.9 nur Standardbibliothek (`python3` aus dem PATH, auf dem MacBook ggf. Xcode-CLT 3.9.6), `unittest`; POSIX `sh` + `rsync` (bestehendes `studio_abgleich.sh`); Claude-Code-Hooks in `.claude/settings.json`.

Spec: `docs/superpowers/specs/2026-09-17-tagesbericht-design.md` (vom User am 17.09.2026 freigegeben).

## Global Constraints

- Python-Code läuft unter 3.9: `from __future__ import annotations` in jedem Modul, keine `match`-Anweisung, kein `datetime.UTC`, keine `X | Y`-Typen zur Laufzeit.
- Alles auf Deutsch: Dateinamen, Bezeichner, Kommentare, Ausgaben, Commit-Botschaften (Stil `feat(tagesbericht): …`).
- Der Sammler endet **immer mit 0** und meldet Fehler nur auf stderr; er schreibt nur unter `<Repo>/berichte/`.
- `berichte/` liegt im Hauptordner des Repos (erste Zeile von `git worktree list`), ist gitignoriert (`/berichte/`) und wird wie `projects/` gespiegelt: beide Richtungen, neuere Datei gewinnt, nie löschen.
- Mac-Name: `NIRO_STUDIO_MAC` → `git config --get niro.mac` → `scutil --get ComputerName` → „Mac"; `/` und `:` werden `-`.
- Umgebungsvariablen für Tests: `NIRO_STUDIO_REPO`, `NIRO_STUDIO_NAS`, `NIRO_STUDIO_MAC`, `NIRO_STUDIO_HEUTE` (`JJJJ-MM-TT`), `NIRO_CLAUDE_PROJECTS_DIR` (Standard `~/.claude/projects`), `NIRO_CLAUDE_MEMORY_DIR` (Standard `<projects-dir>/<Schlüssel>/memory`), `NIRO_SAMMLER_CMD` (Shell-Ersatz für den Sammler), `NIRO_SAMMLER_ABGLEICH_CMD` und `NIRO_SAMMLER_ABGLEICH_TIMEOUT` (Ersatzbefehl/Zeitlimit für den Abgleich).
- Der Arbeitsbaum enthält ungesicherte Änderungen anderer Sessions (Motion, `tools/musik`, `tools/sfx`, `CLAUDE.md`, `tools/resolve/WORKFLOW-Resolve.md`). **Nie `git add -A` oder `git add .`** — immer nur die Dateien der eigenen Aufgabe stagen und vor dem Commit `git -c core.quotepath=false diff --cached --name-only` prüfen.
- Commits enden mit `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. Kein Push vor Aufgabe 10.
- Ortszeit überall: Tagesgrenzen, Uhrzeiten in Berichten, Vergleich von Zeitstempeln (`timestamp` der Sitzungen ist UTC mit `Z`).
- Ausgabeformat des Tagesstands (Überschriften, Reihenfolge) exakt wie Spec 2.7 — der Haupt-Check verlässt sich darauf.

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `tools/tagesbericht/umgebung.py` | Repo, NAS, Mac-Name, „heute", Tag-Argument, Tagesgrenzen, Sitzungs- und Gedächtnis-Ordner |
| `tools/tagesbericht/text.py` | `kuerzen()`, `erste_zeile()` — gemeinsame Textkürzung |
| `tools/tagesbericht/git_stand.py` | Quelle Git (Spec 2.1) und Sicherungs-Patch (2.6) |
| `tools/tagesbericht/chargen_stand.py` | Quelle Chargen (2.2): Protokoll-Einträge, Sammelzeile, neue Ergebnisse |
| `tools/tagesbericht/sitzungen_stand.py` | Quelle Sitzungen (2.3): JSONL-Verläufe → Titel, Aufträge, Schlussbericht, Fehler, Dateien |
| `tools/tagesbericht/gedaechtnis_stand.py` | Quelle Gedächtnis (2.4) |
| `tools/tagesbericht/bericht.py` | `Tagesstand`, Hinweise (2.5), Markdown-Renderer (2.7) |
| `tools/tagesbericht/sammler.py` | CLI: Tage schreiben, Patch, Abgleich mit Zeitlimit, Hook-Hinweis (2, 4) |
| `tools/tagesbericht/testhilfe.py` | Testdaten: Wegwerf-Repo, Chargen, Sitzungsverläufe, Gedächtnis |
| `tools/tagesbericht/<modul>_test.py` | `unittest` je Modul |
| `tools/tagesbericht/sammler_test.py` | Ende-zu-Ende-Tests + Runner (`discover *_test.py`, Exit 0 = bestanden) |
| `tools/tagesbericht/README.md`, `WORKFLOW-Tagesbericht.md` | Doku Sammler; Anleitung Haupt-Check (Spec 5) |
| `tools/studio_abgleich.sh`, `tools/studio_abgleich_test.sh` | `--berichte`, Sammler-Aufruf, `berichte_abgleichen` (Spec 3) |
| `.claude/settings.json` | SessionStart-Hook (Spec 4) |
| `.gitignore`, `SETUP.md`, `CLAUDE.md` | `/berichte/`; Mac-Name + Hook; Trigger-Zeile |

Module importieren sich gegenseitig als Nachbarn (`from umgebung import …`): Python setzt beim Aufruf `python3 tools/tagesbericht/<datei>.py` den Skriptordner an den Anfang von `sys.path`. Kein Paket, kein `__init__.py`.

---

### Task 1: Umgebung, Texthilfen, Test-Runner, `.gitignore`

**Files:**
- Create: `tools/tagesbericht/umgebung.py`
- Create: `tools/tagesbericht/text.py`
- Create: `tools/tagesbericht/umgebung_test.py`
- Create: `tools/tagesbericht/text_test.py`
- Create: `tools/tagesbericht/sammler_test.py` (vorerst nur Runner)
- Modify: `.gitignore`

**Interfaces:**
- Produces: `umgebung.Umgebung` (Felder `repo: Path`, `nas: Path`, `mac: str`, `heute: date`, `projects_dir: Path`, `gedaechtnis: Path`; Properties `schluessel`, `berichte`; Methoden `nas_da() -> bool`, `sitzungsordner() -> list[Path]`), `umgebung.umgebung_laden() -> Umgebung`, `umgebung.schluessel_fuer(Path) -> str`, `umgebung.tag_parsen(str | None, date) -> date`, `umgebung.tagesgrenzen(date) -> tuple[datetime, datetime]` (zeitzonenbewusst, Ortszeit), `umgebung.mac_name(Path) -> str`, `umgebung.NAS_STANDARD`; `text.kuerzen(text: str, laenge: int) -> str` (Whitespace normalisiert, bei Kürzung endet auf „…"), `text.erste_zeile(texte: list[str]) -> str`.

- [ ] **Step 1: Tests für Umgebung und Text schreiben**

`tools/tagesbericht/text_test.py`:

```python
import unittest

from text import erste_zeile, kuerzen


class Kuerzen(unittest.TestCase):
    def test_normalisiert_whitespace(self):
        self.assertEqual(kuerzen("  a \n b\t c ", 100), "a b c")

    def test_kuerzt_mit_auslassung(self):
        self.assertEqual(kuerzen("abcdefghij", 5), "abcd…")
        self.assertEqual(len(kuerzen("x" * 500, 200)), 200)

    def test_laesst_kurzes_stehen(self):
        self.assertEqual(kuerzen("kurz", 4), "kurz")


class ErsteZeile(unittest.TestCase):
    def test_erste_nicht_leere_zeile(self):
        self.assertEqual(erste_zeile(["\n\nFehler: x\nDetails", "mehr"]), "Fehler: x")

    def test_leer(self):
        self.assertEqual(erste_zeile([]), "")
        self.assertEqual(erste_zeile(["", " \n "]), "")


if __name__ == "__main__":
    unittest.main()
```

`tools/tagesbericht/umgebung_test.py`:

```python
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import umgebung
from umgebung import Umgebung, schluessel_fuer, tag_parsen, tagesgrenzen, umgebung_laden


class SchluesselUndTag(unittest.TestCase):
    def test_schluessel(self):
        self.assertEqual(schluessel_fuer(Path("/Users/jansantos/NIRO Studio")), "-Users-jansantos-NIRO-Studio")

    def test_tag_parsen(self):
        heute = date(2026, 9, 17)
        self.assertEqual(tag_parsen(None, heute), heute)
        self.assertEqual(tag_parsen("heute", heute), heute)
        self.assertEqual(tag_parsen("gestern", heute), date(2026, 9, 16))
        self.assertEqual(tag_parsen("2026-09-01", heute), date(2026, 9, 1))

    def test_tagesgrenzen(self):
        anfang, ende = tagesgrenzen(date(2026, 9, 17))
        self.assertIsNotNone(anfang.tzinfo)
        self.assertEqual(anfang.date(), date(2026, 9, 17))
        self.assertEqual((anfang.hour, anfang.minute), (0, 0))
        self.assertEqual(ende - anfang, timedelta(days=1))


class UmgebungAusVariablen(unittest.TestCase):
    def setUp(self):
        self.basis = Path(tempfile.mkdtemp(prefix="umgebung_test_"))
        self.repo = self.basis / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.projects = self.basis / "projects"
        self.schluessel = schluessel_fuer(self.repo)
        for name in (self.schluessel, self.schluessel + "--claude-worktrees-x", "-anderes-repo"):
            (self.projects / name).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.basis, ignore_errors=True)

    def test_laden_aus_variablen(self):
        env = {
            "NIRO_STUDIO_REPO": str(self.repo),
            "NIRO_STUDIO_NAS": str(self.basis / "nas" / "NIRO Studio"),
            "NIRO_STUDIO_MAC": "Test/Mac:1",
            "NIRO_STUDIO_HEUTE": "2026-09-17",
            "NIRO_CLAUDE_PROJECTS_DIR": str(self.projects),
        }
        with mock.patch.dict(os.environ, env):
            os.environ.pop("NIRO_CLAUDE_MEMORY_DIR", None)
            u = umgebung_laden()
        self.assertEqual(u.repo, self.repo)
        self.assertEqual(u.mac, "Test-Mac-1")
        self.assertEqual(u.heute, date(2026, 9, 17))
        self.assertEqual(u.gedaechtnis, self.projects / self.schluessel / "memory")
        self.assertEqual(u.berichte, self.repo / "berichte")
        self.assertFalse(u.nas_da())
        self.assertEqual([p.name for p in u.sitzungsordner()],
                         sorted([self.schluessel, self.schluessel + "--claude-worktrees-x"]))

    def test_mac_aus_git_config(self):
        subprocess.run(["git", "-C", str(self.repo), "config", "niro.mac", "Studio-Mac"], check=True)
        with mock.patch.dict(os.environ, {"NIRO_STUDIO_REPO": str(self.repo)}):
            os.environ.pop("NIRO_STUDIO_MAC", None)
            self.assertEqual(umgebung.mac_name(self.repo), "Studio-Mac")

    def test_nas_da_wenn_elternordner_existiert(self):
        (self.basis / "nas").mkdir()
        u = Umgebung(repo=self.repo, nas=self.basis / "nas" / "NIRO Studio", mac="M", heute=date(2026, 9, 17),
                     projects_dir=self.projects, gedaechtnis=self.basis / "g")
        self.assertTrue(u.nas_da())

    def test_sitzungsordner_ohne_projects_dir(self):
        u = Umgebung(repo=self.repo, nas=self.basis / "nas", mac="M", heute=date(2026, 9, 17),
                     projects_dir=self.basis / "fehlt", gedaechtnis=self.basis / "g")
        self.assertEqual(u.sitzungsordner(), [])


if __name__ == "__main__":
    unittest.main()
```

`tools/tagesbericht/sammler_test.py` (Runner; die Ende-zu-Ende-Tests kommen in Aufgabe 7 dazu):

```python
"""Ende-zu-Ende-Tests des Sammlers und Runner für alle *_test.py in diesem Ordner.
Aufruf: python3 tools/tagesbericht/sammler_test.py   (Exit 0 = alle Tests bestanden)"""
import sys
import unittest
from pathlib import Path

HIER = Path(__file__).resolve().parent


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(HIER), pattern="*_test.py", top_level_dir=str(HIER))
    ergebnis = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if ergebnis.wasSuccessful() else 1)
```

- [ ] **Step 2: Tests laufen lassen — sie müssen fehlschlagen**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py`
Expected: Import-Fehler `ModuleNotFoundError: No module named 'text'` / `'umgebung'` (als Test-Fehler gelistet), Exit 1.

- [ ] **Step 3: `text.py` und `tools/tagesbericht/umgebung.py` schreiben**

`tools/tagesbericht/text.py`:

```python
"""Gemeinsame Textkürzung für Tagesstand und Bericht."""
from __future__ import annotations


def kuerzen(text: str, laenge: int) -> str:
    """Whitespace auf einzelne Leerzeichen normalisieren, bei Überlänge mit „…“ abschneiden."""
    text = " ".join(text.split())
    if len(text) <= laenge:
        return text
    return text[: laenge - 1].rstrip() + "…"


def erste_zeile(texte: list[str]) -> str:
    """Erste nicht leere Zeile aus einer Liste von Texten."""
    for text in texte:
        for zeile in text.splitlines():
            if zeile.strip():
                return zeile.strip()
    return ""
```

`tools/tagesbericht/umgebung.py`:

```python
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
```

- [ ] **Step 4: Tests laufen lassen — grün**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py`
Expected: `OK`, Exit 0 (12 Tests).

- [ ] **Step 5: `.gitignore` ergänzen**

Nach dem Block `/projects/` (Zeile 4) einfügen:

```
# berichte/ (Spec docs/superpowers/specs/2026-09-17-tagesbericht-design.md): Tagesstände beider Macs und Tagesberichte
# laufen über denselben NAS-Spiegel (tools/studio_abgleich.sh --berichte), nicht über GitHub.
/berichte/
```

Prüfen: `mkdir -p berichte/x && touch berichte/x/y.md && git status --short berichte; rm -r berichte` → keine Ausgabe.

- [ ] **Step 6: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add .gitignore tools/tagesbericht/umgebung.py tools/tagesbericht/text.py tools/tagesbericht/umgebung_test.py tools/tagesbericht/text_test.py tools/tagesbericht/sammler_test.py && git -c core.quotepath=false diff --cached --name-only && git commit -q -m "feat(tagesbericht): Umgebung des Sammlers (Repo, NAS, Mac-Name, Tag, Sitzungsordner); berichte/ ignoriert

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Quelle Git und Sicherungs-Patch

**Files:**
- Create: `tools/tagesbericht/git_stand.py`
- Create: `tools/tagesbericht/testhilfe.py` (Grundgerüst + `repo_anlegen`)
- Create: `tools/tagesbericht/git_stand_test.py`

**Interfaces:**
- Consumes: `umgebung.tagesgrenzen`.
- Produces: Dataclasses `Commit(zeit, hash, betreff)`, `Branch(name, vor, hinter, letzter, worktree, commits_heute)`, `Gruppe(pfad, geaendert, neu, geloescht, juengste, beispiele, weitere)`, `Worktree(pfad, branch, ist_haupt, gruppen)`, `GitStand(head_branch, head_hash, auf_main, branches, worktrees, stashes, fehler)` mit Property `commits_gesamt`; Funktionen `git_stand(repo: Path, tag: date) -> GitStand`, `sicherung(repo: Path, mac: str, jetzt: datetime) -> str` (Patch-Text), `worktrees_lesen(repo) -> list[tuple[str, str]]` (Pfad, Branch). Testhilfe: `testhilfe.lokal(tag, stunde, minute=0) -> datetime` (Ortszeit, zeitzonenbewusst), `testhilfe.git(ordner, *args, env=None) -> str`, `testhilfe.commit(ordner, botschaft, wann)`, `testhilfe.repo_anlegen(basis, heute) -> dict` mit Schlüsseln `repo`, `wt`, `origin`.

- [ ] **Step 1: Testhilfe mit dem Wegwerf-Repo schreiben**

`tools/tagesbericht/testhilfe.py`:

```python
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
```

- [ ] **Step 2: Tests für `git_stand` schreiben**

`tools/tagesbericht/git_stand_test.py`:

```python
import os
import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from git_stand import git_stand, sicherung, worktrees_lesen
from testhilfe import lokal, repo_anlegen

HEUTE = date(2026, 9, 17)


class GitStandAusRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.basis = Path(tempfile.mkdtemp(prefix="git_stand_test_"))
        daten = repo_anlegen(cls.basis, HEUTE)
        cls.repo, cls.wt = daten["repo"], daten["wt"]
        cls.stand = git_stand(cls.repo, HEUTE)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.basis, ignore_errors=True)

    def branch(self, name):
        return next(b for b in self.stand.branches if b.name == name)

    def test_kopf(self):
        self.assertEqual(self.stand.head_branch, "main")
        self.assertEqual(len(self.stand.head_hash), 7)
        self.assertEqual(self.stand.fehler, [])

    def test_auf_main_nur_heute(self):
        self.assertEqual([c.betreff for c in self.stand.auf_main], ["A heute"])
        self.assertEqual(self.stand.auf_main[0].zeit, "10:00")
        self.assertEqual(len(self.stand.auf_main[0].hash), 7)

    def test_ungepushter_branch(self):
        x = self.branch("claude/x")
        self.assertEqual((x.vor, x.hinter), (1, 0))
        self.assertEqual(x.letzter, "2026-09-17")
        self.assertEqual(os.path.realpath(x.worktree), os.path.realpath(str(self.wt)))
        self.assertEqual([(c.zeit, c.betreff) for c in x.commits_heute], [("11:30", "B ungepusht")])

    def test_main_ohne_vorsprung(self):
        m = self.branch("main")
        self.assertEqual((m.vor, m.hinter), (0, 0))
        self.assertIsNone(m.worktree)
        self.assertEqual(m.commits_heute, [])

    def test_commits_gesamt(self):
        self.assertEqual(self.stand.commits_gesamt, 2)

    def test_unversioniert_hauptordner(self):
        haupt = next(w for w in self.stand.worktrees if w.ist_haupt)
        self.assertEqual(haupt.branch, "main")
        gruppen = {g.pfad: g for g in haupt.gruppen}
        self.assertEqual(sorted(gruppen), ["NOTIZ.md", "tools/a.txt", "tools/bin.dat", "tools/motion/"])
        self.assertEqual((gruppen["tools/a.txt"].geaendert, gruppen["tools/a.txt"].neu), (1, 0))
        self.assertEqual((gruppen["tools/motion/"].neu, gruppen["tools/motion/"].weitere), (2, 0))
        self.assertEqual(gruppen["tools/motion/"].beispiele, ["tools/motion/neu.ts", "tools/motion/src/x.ts"])
        self.assertRegex(gruppen["tools/motion/"].juengste, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
        self.assertEqual(gruppen["NOTIZ.md"].neu, 1)

    def test_unversioniert_worktree(self):
        wt = next(w for w in self.stand.worktrees if not w.ist_haupt)
        self.assertEqual(wt.branch, "claude/x")
        self.assertEqual([(g.pfad, g.geaendert) for g in wt.gruppen], [("tools/b.txt", 1)])

    def test_stashes(self):
        self.assertEqual(self.stand.stashes, 1)

    def test_gestern(self):
        gestern = git_stand(self.repo, HEUTE - timedelta(days=1))
        self.assertEqual([c.betreff for c in gestern.auf_main], ["A0 gestern"])
        self.assertEqual(next(b for b in gestern.branches if b.name == "claude/x").commits_heute, [])

    def test_worktrees_lesen(self):
        wts = worktrees_lesen(self.repo)
        self.assertEqual([b for _, b in wts], ["main", "claude/x"])

    def test_sicherung(self):
        patch = sicherung(self.repo, "Test-Mac", lokal(HEUTE, 16, 40))
        self.assertTrue(patch.startswith("# Sicherung Test-Mac 2026-09-17 16:40\n"))
        self.assertIn("# Worktree: ", patch)
        self.assertIn("(main)", patch)
        self.assertIn("(claude/x)", patch)
        self.assertIn("diff --git a/tools/a.txt b/tools/a.txt", patch)
        self.assertIn("+a3 lokal", patch)
        self.assertIn("+Inhalt der neuen Datei", patch)
        self.assertIn("+notiz", patch)
        self.assertIn("# nicht gesichert (groß oder binär): tools/bin.dat", patch)
        self.assertIn("+b geändert", patch)
        self.assertLess(patch.index("(main)"), patch.index("(claude/x)"))


class GitStandOhneRemote(unittest.TestCase):
    def setUp(self):
        self.basis = Path(tempfile.mkdtemp(prefix="git_stand_test_"))

    def tearDown(self):
        shutil.rmtree(self.basis, ignore_errors=True)

    def test_repo_ohne_origin(self):
        from testhilfe import commit, git
        repo = self.basis / "solo"
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "t@t")
        git(repo, "config", "user.name", "t")
        git(repo, "config", "commit.gpgsign", "false")
        (repo / "x.txt").write_text("x\n")
        commit(repo, "einziger", lokal(HEUTE, 8))
        stand = git_stand(repo, HEUTE)
        self.assertEqual(stand.auf_main, [])
        m = next(b for b in stand.branches if b.name == "main")
        self.assertIsNone(m.vor)
        self.assertEqual([c.betreff for c in m.commits_heute], ["einziger"])
        self.assertEqual(stand.fehler, [])

    def test_kein_repo(self):
        stand = git_stand(self.basis / "leer", HEUTE)
        self.assertTrue(stand.fehler)
        self.assertEqual(stand.auf_main, [])
        patch = sicherung(self.basis / "leer", "M", lokal(HEUTE, 9))
        self.assertIn("# Fehler", patch)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Tests laufen lassen — fehlschlagen**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/git_stand_test.py`
Expected: `ModuleNotFoundError: No module named 'git_stand'`.

- [ ] **Step 4: `tools/tagesbericht/git_stand.py` schreiben**

```python
"""Quelle Git (Spec 2.1): Commits des Tages auf main und je Branch, Vorsprung zu origin/main, unversionierte
Änderungen je Worktree, Stashes. Dazu die Sicherung der unversionierten Änderungen als Patch (Spec 2.6)."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from umgebung import tagesgrenzen

TRENNER = "\x1f"
BEISPIELE_MAX = 8
PATCH_DATEI_MAX = 1024 * 1024
PATCH_GESAMT_MAX = 5 * 1024 * 1024


class GitFehler(Exception):
    pass


@dataclass
class Commit:
    zeit: str
    hash: str
    betreff: str


@dataclass
class Branch:
    name: str
    vor: int | None
    hinter: int | None
    letzter: str
    worktree: str | None
    commits_heute: list[Commit] = field(default_factory=list)


@dataclass
class Gruppe:
    pfad: str
    geaendert: int = 0
    neu: int = 0
    geloescht: int = 0
    juengste: str = ""
    beispiele: list[str] = field(default_factory=list)
    weitere: int = 0


@dataclass
class Worktree:
    pfad: str
    branch: str
    ist_haupt: bool
    gruppen: list[Gruppe] = field(default_factory=list)


@dataclass
class GitStand:
    head_branch: str = ""
    head_hash: str = ""
    auf_main: list[Commit] = field(default_factory=list)
    branches: list[Branch] = field(default_factory=list)
    worktrees: list[Worktree] = field(default_factory=list)
    stashes: int = 0
    fehler: list[str] = field(default_factory=list)

    @property
    def commits_gesamt(self) -> int:
        return len(self.auf_main) + sum(len(b.commits_heute) for b in self.branches)


def git(ordner: Path, *args: str, ok_rc: tuple[int, ...] = (0,)) -> str:
    try:
        aus = subprocess.run(["git", "-C", str(ordner), *args], capture_output=True, text=True,
                             errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        raise GitFehler(f"git {' '.join(args[:2])}: {e}") from e
    if aus.returncode not in ok_rc:
        raise GitFehler(f"git {' '.join(args[:2])}: rc {aus.returncode} {aus.stderr.strip()[:200]}")
    return aus.stdout


def _gleich(a: str, b: str) -> bool:
    return os.path.realpath(a) == os.path.realpath(b)


def _commits(repo: Path, tag: date, bereich: str) -> list[Commit]:
    anfang, ende = tagesgrenzen(tag)
    aus = git(repo, "log", bereich, f"--since={anfang.isoformat()}", f"--until={ende.isoformat()}",
              f"--format=%h{TRENNER}%ct{TRENNER}%s")
    commits = []
    for zeile in aus.splitlines():
        teile = zeile.split(TRENNER, 2)
        if len(teile) != 3 or not teile[1].isdigit():
            continue
        zeit = datetime.fromtimestamp(int(teile[1])).strftime("%H:%M")
        commits.append(Commit(zeit=zeit, hash=teile[0], betreff=teile[2]))
    return commits


def worktrees_lesen(repo: Path) -> list[tuple[str, str]]:
    """(Pfad, Branch) je Worktree aus `git worktree list --porcelain`; Hauptordner zuerst."""
    ergebnis: list[tuple[str, str]] = []
    pfad, branch = None, "(detached)"
    for zeile in git(repo, "worktree", "list", "--porcelain").splitlines() + [""]:
        if zeile.startswith("worktree "):
            pfad, branch = zeile[len("worktree "):], "(detached)"
        elif zeile.startswith("branch "):
            branch = zeile[len("branch "):]
            if branch.startswith("refs/heads/"):
                branch = branch[len("refs/heads/"):]
        elif zeile == "" and pfad is not None:
            ergebnis.append((pfad, branch))
            pfad = None
    return ergebnis


def gruppen_lesen(ordner: Path) -> list[Gruppe]:
    """`git status --porcelain -uall -z`, gruppiert nach den ersten zwei Pfadteilen (Wurzeldateien einzeln)."""
    eintraege = git(ordner, "status", "--porcelain", "-uall", "-z").split("\0")
    gruppen: dict[str, Gruppe] = {}
    zeiten: dict[str, float] = {}
    i = 0
    while i < len(eintraege):
        eintrag = eintraege[i]
        i += 1
        if len(eintrag) < 4:
            continue
        xy, pfad = eintrag[:2], eintrag[3:]
        if xy[0] in "RC":
            i += 1  # bei Umbenennen/Kopie folgt der alte Pfad als eigener Eintrag
        teile = pfad.split("/")
        schluessel = "/".join(teile[:2]) + ("/" if len(teile) > 2 else "")
        g = gruppen.setdefault(schluessel, Gruppe(pfad=schluessel))
        if xy == "??" or "A" in xy:
            g.neu += 1
        elif "D" in xy:
            g.geloescht += 1
        else:
            g.geaendert += 1
        if len(g.beispiele) < BEISPIELE_MAX:
            g.beispiele.append(pfad)
        else:
            g.weitere += 1
        try:
            zeiten[schluessel] = max(zeiten.get(schluessel, 0.0), os.path.getmtime(ordner / pfad))
        except OSError:
            pass
    for schluessel, g in gruppen.items():
        if schluessel in zeiten:
            g.juengste = datetime.fromtimestamp(zeiten[schluessel]).strftime("%Y-%m-%d %H:%M")
    return sorted(gruppen.values(), key=lambda g: g.pfad)


def git_stand(repo: Path, tag: date) -> GitStand:
    stand = GitStand()
    try:
        stand.head_branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
        stand.head_hash = git(repo, "rev-parse", "--short", "HEAD").strip()
    except GitFehler as e:
        stand.fehler.append(str(e))
        return stand
    origin_da = bool(git(repo, "rev-parse", "--verify", "-q", "origin/main", ok_rc=(0, 1)).strip())
    if origin_da:
        try:
            stand.auf_main = _commits(repo, tag, "origin/main")
        except GitFehler as e:
            stand.fehler.append(str(e))
    worktrees: list[tuple[str, str]] = []
    try:
        worktrees = worktrees_lesen(repo)
    except GitFehler as e:
        stand.fehler.append(str(e))
    wt_je_branch = {b: p for p, b in worktrees if not _gleich(p, str(repo))}
    try:
        for zeile in git(repo, "for-each-ref", "refs/heads", "--format=%(refname:short)\t%(committerdate:unix)").splitlines():
            name, _, unix = zeile.partition("\t")
            if not name:
                continue
            letzter = datetime.fromtimestamp(int(unix)).strftime("%Y-%m-%d") if unix.strip().isdigit() else ""
            vor = hinter = None
            if origin_da:
                zaehler = git(repo, "rev-list", "--left-right", "--count", f"origin/main...{name}").split()
                if len(zaehler) == 2:
                    hinter, vor = int(zaehler[0]), int(zaehler[1])
                commits = _commits(repo, tag, f"origin/main..{name}")
            else:
                commits = _commits(repo, tag, name)
            stand.branches.append(Branch(name=name, vor=vor, hinter=hinter, letzter=letzter,
                                         worktree=wt_je_branch.get(name), commits_heute=commits))
    except GitFehler as e:
        stand.fehler.append(str(e))
    for pfad, branch in worktrees:
        try:
            gruppen = gruppen_lesen(Path(pfad))
        except GitFehler as e:
            stand.fehler.append(f"Worktree {pfad}: {e}")
            continue
        stand.worktrees.append(Worktree(pfad=pfad, branch=branch, ist_haupt=_gleich(pfad, str(repo)), gruppen=gruppen))
    try:
        stand.stashes = len(git(repo, "stash", "list").splitlines())
    except GitFehler as e:
        stand.fehler.append(str(e))
    return stand


def sicherung(repo: Path, mac: str, jetzt: datetime) -> str:
    """Patch aller Worktrees: `git diff HEAD` plus je unversionierter Textdatei (≤ 1 MB, kein NUL in den ersten 8 KB)
    ein `git diff --no-index`. Gesamt höchstens 5 MB, danach nur noch Namen. Hauptordner zuerst."""
    zeilen = [f"# Sicherung {mac} {jetzt.strftime('%Y-%m-%d %H:%M')}"]
    try:
        worktrees = worktrees_lesen(repo)
    except GitFehler as e:
        return "\n".join(zeilen + [f"# Fehler: {e}"]) + "\n"
    worktrees.sort(key=lambda pb: not _gleich(pb[0], str(repo)))
    groesse = 0
    abgebrochen = False
    aenderungen = False
    for pfad, branch in worktrees:
        ordner = Path(pfad)
        teile: list[str] = []
        try:
            diff = git(ordner, "diff", "HEAD", "--", ".")
        except GitFehler:
            diff = ""
        if diff.strip():
            teile.append(diff)
            groesse += len(diff.encode("utf-8", "replace"))
        try:
            neue = [n for n in git(ordner, "ls-files", "--others", "--exclude-standard", "-z").split("\0") if n]
        except GitFehler:
            neue = []
        for name in neue:
            datei = ordner / name
            try:
                gross = datei.stat().st_size > PATCH_DATEI_MAX
                with open(datei, "rb") as fh:
                    binaer = b"\0" in fh.read(8192)
            except OSError:
                continue
            if gross or binaer:
                teile.append(f"# nicht gesichert (groß oder binär): {name}\n")
                continue
            if groesse > PATCH_GESAMT_MAX:
                if not abgebrochen:
                    abgebrochen = True
                    teile.append("# Abbruch: 5 MB erreicht — weitere Dateien nur als Namen\n")
                teile.append(f"# nicht gesichert (Abbruch): {name}\n")
                continue
            try:
                d = git(ordner, "diff", "--no-index", "--", "/dev/null", name, ok_rc=(0, 1))
            except GitFehler as e:
                teile.append(f"# Fehler bei {name}: {e}\n")
                continue
            teile.append(d)
            groesse += len(d.encode("utf-8", "replace"))
        if teile:
            aenderungen = True
            zeilen.append(f"# Worktree: {pfad} ({branch})")
            zeilen.extend(t.rstrip("\n") for t in teile)
    if not aenderungen:
        zeilen.append("# keine unversionierten Änderungen")
    return "\n".join(zeilen) + "\n"
```

- [ ] **Step 5: Tests laufen lassen — grün**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py`
Expected: `OK` (alle bisherigen + 13 neue Tests). Falls `test_sicherung` an `+notiz` scheitert: prüfen, ob `NOTIZ.md` in `git ls-files --others` auftaucht (Pfad relativ zum Worktree, `-C` gesetzt).

- [ ] **Step 6: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/tagesbericht/git_stand.py tools/tagesbericht/testhilfe.py tools/tagesbericht/git_stand_test.py && git -c core.quotepath=false diff --cached --name-only && git commit -q -m "feat(tagesbericht): Quelle Git — Commits, Branches, Unversioniertes je Worktree, Stashes, Sicherungs-Patch

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Quelle Chargen

**Files:**
- Create: `tools/tagesbericht/chargen_stand.py`
- Modify: `tools/tagesbericht/testhilfe.py` (am Ende `chargen_anlegen` anfügen)
- Create: `tools/tagesbericht/chargen_stand_test.py`

**Interfaces:**
- Consumes: `umgebung.tagesgrenzen`, `text.kuerzen`.
- Produces: `Lieferung(charge: str, anzahl: int, beispiele: list[str])`, `ChargenStand(je_charge_alle: dict[str, list[str]], je_charge: dict[str, list[str]], sammel: list[tuple[str, int]], lieferungen: list[Lieferung], fehler: list[str])`, `chargen_stand(repo: Path, tag: date) -> ChargenStand`. Chargen-Schlüssel sind Pfade relativ zum Repo (`projects/Kunde/Projekt/2026-09 Charge`). Testhilfe: `chargen_anlegen(repo: Path, heute: date) -> None`.

- [ ] **Step 1: Testdaten anfügen**

An `tools/tagesbericht/testhilfe.py` anhängen:

```python


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
```

- [ ] **Step 2: Tests schreiben**

`tools/tagesbericht/chargen_stand_test.py`:

```python
import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from chargen_stand import Lieferung, chargen_stand
from testhilfe import chargen_anlegen

HEUTE = date(2026, 9, 17)
C1 = "projects/Kunde/Projekt/2026-09 Charge"
C2 = "projects/Kunde/2026-08 Kurz"


class ChargenStandAusProtokollen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.basis = Path(tempfile.mkdtemp(prefix="chargen_test_"))
        cls.repo = cls.basis / "repo"
        cls.repo.mkdir()
        chargen_anlegen(cls.repo, HEUTE)
        cls.stand = chargen_stand(cls.repo, HEUTE)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.basis, ignore_errors=True)

    def test_eintraege_aller_formen_nur_heute(self):
        self.assertEqual(self.stand.je_charge[C1], ["2026-09-17 11:07 — AutoCut: Kantenprüfung", "Session 17.09.2026 — Feinschnitt"])
        self.assertEqual(self.stand.je_charge[C2], ["Overlay-Export Video 1 (2026-09-17)"])

    def test_sammelzeile(self):
        self.assertEqual(self.stand.sammel, [("2026-09-17 — Medien aufs NAS verschoben", 6)])
        self.assertNotIn("projects/K0/P/2026-01 C", self.stand.je_charge)
        self.assertIn("projects/K0/P/2026-01 C", self.stand.je_charge_alle)
        self.assertEqual(len(self.stand.je_charge_alle), 7)

    def test_lieferungen(self):
        self.assertEqual(self.stand.lieferungen, [Lieferung(charge=C1, anzahl=1, beispiele=["Export/a.mp4"])])

    def test_gestern(self):
        gestern = chargen_stand(self.repo, HEUTE - timedelta(days=1))
        self.assertEqual(gestern.je_charge_alle, {C1: ["2026-09-16 — Gestern"]})
        self.assertEqual(gestern.sammel, [])
        self.assertEqual(gestern.lieferungen, [Lieferung(charge=C1, anzahl=1, beispiele=["Export/b.mp4"])])

    def test_ohne_projects(self):
        leer = chargen_stand(self.basis / "nix", HEUTE)
        self.assertEqual((leer.je_charge_alle, leer.lieferungen, leer.fehler), ({}, [], []))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Tests laufen lassen — fehlschlagen**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/chargen_stand_test.py`
Expected: `ModuleNotFoundError: No module named 'chargen_stand'`.

- [ ] **Step 4: `tools/tagesbericht/chargen_stand.py` schreiben**

```python
"""Quelle Chargen (Spec 2.2): Protokoll-Einträge des Tages je Charge (Sammelzeile ab fünf gleichen Überschriften)
und neue Dateien unter Ergebnisse/."""
from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from text import kuerzen
from umgebung import tagesgrenzen

SAMMEL_AB = 5
UEBERSCHRIFT_MAX = 120
BEISPIELE_MAX = 5


@dataclass
class Lieferung:
    charge: str
    anzahl: int
    beispiele: list[str]


@dataclass
class ChargenStand:
    je_charge_alle: dict[str, list[str]] = field(default_factory=dict)
    je_charge: dict[str, list[str]] = field(default_factory=dict)
    sammel: list[tuple[str, int]] = field(default_factory=list)
    lieferungen: list[Lieferung] = field(default_factory=list)
    fehler: list[str] = field(default_factory=list)


def chargen_ordner(repo: Path) -> list[Path]:
    """Ordner in Tiefe 2 und 3 unter projects/ mit Protokoll.md oder Ergebnisse/."""
    projects = repo / "projects"
    if not projects.is_dir():
        return []
    gefunden = set()
    for muster in ("*/*", "*/*/*"):
        for p in projects.glob(muster):
            if p.is_dir() and ((p / "Protokoll.md").is_file() or (p / "Ergebnisse").is_dir()):
                gefunden.add(p)
    return sorted(gefunden)


def eintraege_des_tages(protokoll: Path, tag: date) -> list[str]:
    """Überschriften `## …`, die das Datum als JJJJ-MM-TT oder TT.MM.JJJJ enthalten, ohne `## `, gekürzt."""
    iso, deutsch = tag.isoformat(), tag.strftime("%d.%m.%Y")
    ergebnis = []
    with open(protokoll, encoding="utf-8", errors="replace") as fh:
        for zeile in fh:
            if zeile.startswith("## ") and (iso in zeile or deutsch in zeile):
                ergebnis.append(kuerzen(zeile[3:], UEBERSCHRIFT_MAX))
    return ergebnis


def chargen_stand(repo: Path, tag: date) -> ChargenStand:
    stand = ChargenStand()
    anfang, ende = tagesgrenzen(tag)
    von, bis = anfang.timestamp(), ende.timestamp()
    for ordner in chargen_ordner(repo):
        charge = ordner.relative_to(repo).as_posix()
        protokoll = ordner / "Protokoll.md"
        if protokoll.is_file():
            try:
                eintraege = eintraege_des_tages(protokoll, tag)
            except OSError as e:
                stand.fehler.append(f"{charge}/Protokoll.md: {e}")
                eintraege = []
            if eintraege:
                stand.je_charge_alle[charge] = eintraege
        ergebnisse = ordner / "Ergebnisse"
        if ergebnisse.is_dir():
            treffer = []
            for wurzel, _ordner, dateien in os.walk(ergebnisse):
                for name in dateien:
                    if name == ".DS_Store":
                        continue
                    pfad = Path(wurzel) / name
                    try:
                        mtime = pfad.stat().st_mtime
                    except OSError:
                        continue
                    if von <= mtime < bis:
                        treffer.append(pfad.relative_to(ergebnisse).as_posix())
            if treffer:
                treffer.sort()
                stand.lieferungen.append(Lieferung(charge=charge, anzahl=len(treffer), beispiele=treffer[:BEISPIELE_MAX]))
    zaehler = Counter(u for eintraege in stand.je_charge_alle.values() for u in set(eintraege))
    stand.sammel = sorted(((u, n) for u, n in zaehler.items() if n >= SAMMEL_AB), key=lambda x: (-x[1], x[0]))
    zusammengefasst = {u for u, _ in stand.sammel}
    for charge, eintraege in stand.je_charge_alle.items():
        rest = [u for u in eintraege if u not in zusammengefasst]
        if rest:
            stand.je_charge[charge] = rest
    return stand
```

- [ ] **Step 5: Tests laufen lassen — grün**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py`
Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/tagesbericht/chargen_stand.py tools/tagesbericht/testhilfe.py tools/tagesbericht/chargen_stand_test.py && git -c core.quotepath=false diff --cached --name-only && git commit -q -m "feat(tagesbericht): Quelle Chargen — Protokoll-Einträge des Tages, Sammelzeile, neue Ergebnisse

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Quelle Sitzungen

**Files:**
- Create: `tools/tagesbericht/sitzungen_stand.py`
- Modify: `tools/tagesbericht/testhilfe.py` (am Ende `sitzungen_anlegen` anfügen; oben `import json` und `from datetime import timezone` ergänzen)
- Create: `tools/tagesbericht/sitzungen_stand_test.py`

**Interfaces:**
- Consumes: `umgebung.tagesgrenzen`, `umgebung.schluessel_fuer` (Testhilfe), `text.kuerzen`, `text.erste_zeile`.
- Produces: `Sitzung(kennung, titel, ordner, branch, von, bis, auftraege, weitere_auftraege, schluss, schluss_offen, fehler_anzahl, fehler, dateien, weitere_dateien, werkzeuge: list[tuple[str, int]], chargen: list[str], beginn: datetime | None)`, `SitzungenStand(sitzungen, fehler)`, `sitzungen_stand(ordner: list[Path], tag: date, repo: Path) -> SitzungenStand`, `sitzung_lesen(datei, tag, repo) -> Sitzung | None`, `relativ(pfad: str, repo: Path) -> str`, `charge_aus_pfad(rel: str) -> str | None`. Testhilfe: `sitzungen_anlegen(projects_dir, repo, wt, heute) -> dict` mit `haupt`, `wt` (die zwei Sitzungsordner).

- [ ] **Step 1: Testdaten anfügen**

Am Kopf von `tools/tagesbericht/testhilfe.py` die Importe ergänzen (`import json` nach `import os`; `from datetime import date, datetime, timedelta, timezone`). Am Ende anhängen:

```python


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
```

- [ ] **Step 2: Tests schreiben**

`tools/tagesbericht/sitzungen_stand_test.py`:

```python
import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from sitzungen_stand import charge_aus_pfad, relativ, sitzungen_stand
from testhilfe import sitzungen_anlegen

HEUTE = date(2026, 9, 17)


class SitzungenAusVerlaeufen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.basis = Path(tempfile.mkdtemp(prefix="sitzungen_test_"))
        cls.repo = cls.basis / "repo"
        cls.wt = cls.basis / "wt"
        cls.repo.mkdir()
        cls.wt.mkdir()
        ordner = sitzungen_anlegen(cls.basis / "claude" / "projects", cls.repo, cls.wt, HEUTE)
        cls.ordner = [ordner["haupt"], ordner["wt"]]
        cls.stand = sitzungen_stand(cls.ordner, HEUTE, cls.repo)
        cls.s1, cls.s2 = cls.stand.sitzungen

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.basis, ignore_errors=True)

    def test_zwei_sitzungen_chronologisch(self):
        self.assertEqual(len(self.stand.sitzungen), 2)
        self.assertEqual((self.s1.von, self.s2.von), ("09:00", "11:00"))
        self.assertEqual(self.stand.fehler, [])

    def test_titel_zeitraum_branch_ordner(self):
        self.assertEqual(self.s1.titel, "Test-Sitzung")
        self.assertEqual((self.s1.von, self.s1.bis), ("09:00", "10:00"))
        self.assertEqual(self.s1.branch, "main")
        self.assertEqual(self.s1.ordner, ".")
        self.assertEqual(self.s1.kennung, "s1")

    def test_auftraege_gefiltert_und_gekuerzt(self):
        self.assertEqual(len(self.s1.auftraege), 12)
        self.assertEqual(self.s1.auftraege[0], "Auftrag eins")
        self.assertEqual(self.s1.auftraege[1], "Auftrag zwei")
        self.assertEqual(self.s1.weitere_auftraege, 4)
        alle = " ".join(self.s1.auftraege)
        for verboten in ("meta text", "system-reminder", "Request interrupted", "task-notification", "Gestern-Auftrag", "Subagent", "Alt"):
            self.assertNotIn(verboten, alle)

    def test_schlussbericht(self):
        self.assertEqual(self.s1.schluss, "Schlussbericht: alles erledigt.")
        self.assertFalse(self.s1.schluss_offen)

    def test_fehler_dateien_werkzeuge_chargen(self):
        self.assertEqual(self.s1.fehler_anzahl, 2)
        self.assertEqual(self.s1.fehler, ["Fehler: Datei fehlt", "ls: x: No such file or directory"])
        self.assertEqual(self.s1.dateien, ["projects/Ohne/Projekt/2026-09 Charge/_intern/x.py", "tools/neu.py"])
        self.assertEqual(self.s1.werkzeuge, [("Edit", 1), ("Write", 1)])
        self.assertEqual(self.s1.chargen, ["projects/Ohne/Projekt/2026-09 Charge"])

    def test_worktree_sitzung_offen_mit_vielen_fehlern(self):
        self.assertEqual(self.s2.titel, "Offener Auftrag")
        self.assertEqual(self.s2.branch, "claude/x")
        self.assertTrue(self.s2.schluss_offen)
        self.assertEqual(self.s2.schluss, "Ich prüfe.")
        self.assertEqual(self.s2.fehler_anzahl, 5)
        self.assertEqual(self.s2.fehler, [f"Fehler {n}" for n in range(1, 6)])
        self.assertEqual(self.s2.werkzeuge, [("Bash", 1)])
        self.assertTrue(self.s2.ordner.startswith("/"))

    def test_gestern(self):
        gestern = sitzungen_stand(self.ordner, HEUTE - timedelta(days=1), self.repo)
        self.assertEqual(len(gestern.sitzungen), 1)
        s = gestern.sitzungen[0]
        self.assertEqual(s.auftraege, ["Gestern-Auftrag"])
        self.assertEqual((s.von, s.bis), ("22:00", "22:00"))
        self.assertTrue(s.schluss_offen)

    def test_fehlender_ordner(self):
        stand = sitzungen_stand([self.basis / "fehlt"], HEUTE, self.repo)
        self.assertEqual(stand.sitzungen, [])
        self.assertEqual(len(stand.fehler), 1)


class Pfade(unittest.TestCase):
    def test_relativ(self):
        repo = Path("/tmp/x/repo")
        self.assertEqual(relativ("/tmp/x/repo/tools/a.py", repo), "tools/a.py")
        self.assertEqual(relativ("/tmp/x/repo", repo), ".")
        self.assertEqual(relativ("/tmp/x/anders/a.py", repo), "/tmp/x/anders/a.py")

    def test_charge_aus_pfad(self):
        self.assertEqual(charge_aus_pfad("projects/K/P/2026-09 C/_intern/x.py"), "projects/K/P/2026-09 C")
        self.assertEqual(charge_aus_pfad("projects/K/2026-08 C/Protokoll.md"), "projects/K/2026-08 C")
        self.assertIsNone(charge_aus_pfad("projects/K/P/Protokoll.md"))
        self.assertIsNone(charge_aus_pfad("tools/a.py"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Tests laufen lassen — fehlschlagen**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sitzungen_stand_test.py`
Expected: `ModuleNotFoundError: No module named 'sitzungen_stand'`.

- [ ] **Step 4: `tools/tagesbericht/sitzungen_stand.py` schreiben**

```python
"""Quelle Sitzungen (Spec 2.3): Claude-Code-Verläufe (JSONL) eines Tages — Titel, Zeitraum, Aufträge, Schlussbericht,
Tool-Fehler, editierte Dateien, Werkzeuge, Chargen-Bezug. Subagenten-Verläufe und Sidechains bleiben draußen."""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from text import erste_zeile, kuerzen
from umgebung import tagesgrenzen

AUFTRAG_MAX = 200
AUFTRAEGE_MAX = 12
SCHLUSS_MAX = 1500
FEHLER_MAX = 5
FEHLER_ZEILE_MAX = 160
DATEIEN_MAX = 20
WERKZEUGE_MAX = 5
TITEL_MAX = 80
CHARGE_MUSTER = re.compile(r"^\d{4}-\d{2}\b")
EDIT_WERKZEUGE = ("Edit", "Write", "NotebookEdit")
KEIN_AUFTRAG = ("<system-reminder>", "<task-notification>", "<command-name>", "<local-command", "[Request interrupted")
EXIT_MUSTER = re.compile(r"^Exit code \d+$")


@dataclass
class Sitzung:
    kennung: str
    titel: str = ""
    ordner: str = ""
    branch: str = ""
    von: str = ""
    bis: str = ""
    auftraege: list[str] = field(default_factory=list)
    weitere_auftraege: int = 0
    schluss: str = ""
    schluss_offen: bool = False
    fehler_anzahl: int = 0
    fehler: list[str] = field(default_factory=list)
    dateien: list[str] = field(default_factory=list)
    weitere_dateien: int = 0
    werkzeuge: list[tuple[str, int]] = field(default_factory=list)
    chargen: list[str] = field(default_factory=list)
    beginn: datetime | None = None


@dataclass
class SitzungenStand:
    sitzungen: list[Sitzung] = field(default_factory=list)
    fehler: list[str] = field(default_factory=list)


def relativ(pfad: str, repo: Path) -> str:
    """Pfad relativ zum Repo (realpath-Vergleich, macOS /var → /private/var); außerhalb unverändert."""
    wurzel = os.path.realpath(str(repo))
    p = os.path.realpath(pfad) if pfad.startswith("/") else pfad
    if p == wurzel:
        return "."
    if p.startswith(wurzel + "/"):
        return p[len(wurzel) + 1:]
    return pfad


def charge_aus_pfad(rel: str) -> str | None:
    """projects/<Kunde>/[<Projekt>/]<JJJJ-MM Charge>/… → Chargen-Pfad, sonst None."""
    teile = rel.split("/")
    if len(teile) < 3 or teile[0] != "projects":
        return None
    for i in range(2, min(len(teile), 4)):
        if CHARGE_MUSTER.match(teile[i]):
            return "/".join(teile[: i + 1])
    return None


def _text_bloecke(inhalt) -> list[str]:
    if isinstance(inhalt, str):
        return [inhalt]
    if isinstance(inhalt, list):
        return [b.get("text", "") for b in inhalt if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)]
    return []


def _fehlerzeile(texte: list[str]) -> str:
    """Erste aussagekräftige Zeile eines Tool-Fehlers: „Exit code N“ allein sagt nichts, dann die nächste Zeile."""
    zeilen = [z.strip() for t in texte for z in t.splitlines() if z.strip()]
    for zeile in zeilen:
        if not EXIT_MUSTER.match(zeile):
            return zeile
    return erste_zeile(texte)


def _zeitpunkt(ts) -> datetime | None:
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def sitzung_lesen(datei: Path, tag: date, repo: Path) -> Sitzung | None:
    """Ein Verlauf; None, wenn er am Tag keine user-/assistant-Datensätze hat."""
    anfang, ende = tagesgrenzen(tag)
    s = Sitzung(kennung=datei.stem[:8])
    titel_custom = titel_summary = ""
    alle_auftraege: list[str] = []
    werkzeuge: Counter = Counter()
    dateien: list[str] = []
    beginn = letzte = None
    letzter_typ = ""
    with open(datei, encoding="utf-8", errors="replace") as fh:
        for zeile in fh:
            try:
                d = json.loads(zeile)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            typ = d.get("type")
            if typ == "custom-title":
                titel_custom = d.get("customTitle") or titel_custom
                continue
            if typ == "summary":
                titel_summary = d.get("summary") or titel_summary
                continue
            if typ not in ("user", "assistant") or d.get("isSidechain"):
                continue
            zeit = _zeitpunkt(d.get("timestamp"))
            if zeit is None or not (anfang <= zeit < ende):
                continue
            beginn = beginn or zeit
            letzte = zeit
            letzter_typ = typ
            s.branch = d.get("gitBranch") or s.branch
            if isinstance(d.get("cwd"), str) and d["cwd"]:
                s.ordner = relativ(d["cwd"], repo)
            nachricht = d.get("message") if isinstance(d.get("message"), dict) else {}
            inhalt = nachricht.get("content")
            if typ == "user":
                if isinstance(inhalt, list):
                    for b in inhalt:
                        if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error"):
                            s.fehler_anzahl += 1
                            if len(s.fehler) < FEHLER_MAX:
                                s.fehler.append(kuerzen(_fehlerzeile(_text_bloecke(b.get("content"))), FEHLER_ZEILE_MAX))
                if d.get("isMeta"):
                    continue
                for text in _text_bloecke(inhalt):
                    text = text.strip()
                    if not text or text.startswith(KEIN_AUFTRAG):
                        continue
                    alle_auftraege.append(text)
            else:
                for b in inhalt if isinstance(inhalt, list) else []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and isinstance(b.get("text"), str) and b["text"].strip():
                        s.schluss = kuerzen(b["text"], SCHLUSS_MAX)
                    elif b.get("type") == "tool_use":
                        name = b.get("name") or "?"
                        werkzeuge[name] += 1
                        eingabe = b.get("input") if isinstance(b.get("input"), dict) else {}
                        pfad = eingabe.get("file_path") if name in EDIT_WERKZEUGE else None
                        if isinstance(pfad, str) and pfad:
                            rel = relativ(pfad, repo)
                            if rel not in dateien:
                                dateien.append(rel)
    if beginn is None or letzte is None:
        return None
    s.beginn = beginn
    s.von, s.bis = beginn.strftime("%H:%M"), letzte.strftime("%H:%M")
    s.auftraege = [kuerzen(a, AUFTRAG_MAX) for a in alle_auftraege[:AUFTRAEGE_MAX]]
    s.weitere_auftraege = max(0, len(alle_auftraege) - AUFTRAEGE_MAX)
    s.schluss_offen = letzter_typ == "user" or not s.schluss
    s.dateien = dateien[:DATEIEN_MAX]
    s.weitere_dateien = max(0, len(dateien) - DATEIEN_MAX)
    s.werkzeuge = werkzeuge.most_common(WERKZEUGE_MAX)
    s.chargen = sorted({c for c in (charge_aus_pfad(p) for p in dateien) if c})
    s.titel = titel_custom or titel_summary or (kuerzen(alle_auftraege[0], TITEL_MAX) if alle_auftraege else "(ohne Titel)")
    return s


def sitzungen_stand(ordner: list[Path], tag: date, repo: Path) -> SitzungenStand:
    """Alle *.jsonl direkt in den Sitzungsordnern (keine Unterordner); Dateien, die seit Tagesbeginn unverändert
    sind, werden nicht geöffnet."""
    stand = SitzungenStand()
    anfang, _ = tagesgrenzen(tag)
    for o in ordner:
        try:
            dateien = sorted(p for p in o.iterdir() if p.is_file() and p.suffix == ".jsonl")
        except OSError as e:
            stand.fehler.append(f"Sitzungsordner {o}: {e}")
            continue
        for datei in dateien:
            try:
                if datei.stat().st_mtime < anfang.timestamp():
                    continue
                s = sitzung_lesen(datei, tag, repo)
            except OSError as e:
                stand.fehler.append(f"{datei.name}: {e}")
                continue
            if s is not None:
                stand.sitzungen.append(s)
    stand.sitzungen.sort(key=lambda s: s.beginn)
    return stand
```

- [ ] **Step 5: Tests laufen lassen — grün**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py`
Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/tagesbericht/sitzungen_stand.py tools/tagesbericht/testhilfe.py tools/tagesbericht/sitzungen_stand_test.py && git -c core.quotepath=false diff --cached --name-only && git commit -q -m "feat(tagesbericht): Quelle Sitzungen — Titel, Aufträge, Schlussbericht, Fehler, Dateien aus den Claude-Verläufen

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Gedächtnis, Hinweise und Markdown-Tagesstand

**Files:**
- Create: `tools/tagesbericht/gedaechtnis_stand.py`
- Create: `tools/tagesbericht/bericht.py`
- Modify: `tools/tagesbericht/testhilfe.py` (am Ende `gedaechtnis_anlegen` anfügen)
- Create: `tools/tagesbericht/gedaechtnis_stand_test.py`
- Create: `tools/tagesbericht/bericht_test.py`

**Interfaces:**
- Consumes: `git_stand.GitStand/Commit/Branch/Gruppe/Worktree`, `chargen_stand.ChargenStand/Lieferung`, `sitzungen_stand.Sitzung/SitzungenStand`, `text.kuerzen`, `umgebung.tagesgrenzen`.
- Produces: `gedaechtnis_stand.Notiz(name, beschreibung)`, `gedaechtnis_stand.gedaechtnis_stand(ordner: Path, tag: date) -> tuple[list[Notiz], list[str]]`; `bericht.Tagesstand(mac, tag, stand: datetime, repo: str, git, chargen, sitzungen, notizen, fehler)`, `bericht.hinweise(t) -> list[str]`, `bericht.rendern(t) -> str`. Testhilfe: `gedaechtnis_anlegen(ordner: Path, heute: date) -> None`.

- [ ] **Step 1: Testdaten und Tests schreiben**

An `tools/tagesbericht/testhilfe.py` anhängen:

```python


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
```

`tools/tagesbericht/gedaechtnis_stand_test.py`:

```python
import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from gedaechtnis_stand import Notiz, gedaechtnis_stand
from testhilfe import gedaechtnis_anlegen

HEUTE = date(2026, 9, 17)


class GedaechtnisNotizen(unittest.TestCase):
    def setUp(self):
        self.basis = Path(tempfile.mkdtemp(prefix="gedaechtnis_test_"))
        self.ordner = self.basis / "memory"
        gedaechtnis_anlegen(self.ordner, HEUTE)

    def tearDown(self):
        shutil.rmtree(self.basis, ignore_errors=True)

    def test_heute_geaenderte_notizen(self):
        notizen, fehler = gedaechtnis_stand(self.ordner, HEUTE)
        self.assertEqual(notizen, [Notiz(name="notiz-a", beschreibung='Eine "Notiz" von heute')])
        self.assertEqual(fehler, [])

    def test_gestern(self):
        notizen, _ = gedaechtnis_stand(self.ordner, HEUTE - timedelta(days=1))
        self.assertEqual(notizen, [Notiz(name="notiz-b", beschreibung="gestern")])

    def test_ordner_fehlt(self):
        notizen, fehler = gedaechtnis_stand(self.basis / "fehlt", HEUTE)
        self.assertEqual(notizen, [])
        self.assertEqual(len(fehler), 1)


if __name__ == "__main__":
    unittest.main()
```

`tools/tagesbericht/bericht_test.py`:

```python
import unittest
from datetime import date, datetime

from bericht import Tagesstand, hinweise, rendern
from chargen_stand import ChargenStand, Lieferung
from gedaechtnis_stand import Notiz
from git_stand import Branch, Commit, GitStand, Gruppe, Worktree
from sitzungen_stand import Sitzung, SitzungenStand

HEUTE = date(2026, 9, 17)
STAND = datetime(2026, 9, 17, 16, 40)


def voller_stand() -> Tagesstand:
    git = GitStand(
        head_branch="main", head_hash="abc1234",
        auf_main=[Commit("10:00", "abc1234", "A heute")],
        branches=[Branch("claude/x", 1, 0, "2026-09-17", "/wt", [Commit("11:30", "b000000", "B ungepusht")]),
                  Branch("main", 0, 0, "2026-09-17", None, [])],
        worktrees=[Worktree("/repo", "main", True, [Gruppe("tools/motion/", 0, 2, 0, "2026-09-17 09:00",
                                                           ["tools/motion/neu.ts", "tools/motion/src/x.ts"], 0)]),
                   Worktree("/wt", "claude/x", False, [])],
        stashes=1)
    chargen = ChargenStand(
        je_charge_alle={"projects/Kunde/Projekt/2026-09 Charge": ["2026-09-17 11:07 — AutoCut: Kantenprüfung"],
                        "projects/K0/P/2026-01 C": ["2026-09-17 — Medien aufs NAS verschoben"]},
        je_charge={"projects/Kunde/Projekt/2026-09 Charge": ["2026-09-17 11:07 — AutoCut: Kantenprüfung"]},
        sammel=[("2026-09-17 — Medien aufs NAS verschoben", 6)],
        lieferungen=[Lieferung("projects/Kunde/Projekt/2026-09 Charge", 7, ["Export/a.mp4", "Export/b.mp4"])])
    s1 = Sitzung(kennung="s1", titel="Test-Sitzung", ordner=".", branch="main", von="09:00", bis="10:00",
                 auftraege=["Auftrag eins", "Auftrag zwei"], weitere_auftraege=14, schluss="Schlussbericht: alles erledigt.",
                 fehler_anzahl=1, fehler=["Fehler: Datei fehlt"], dateien=["projects/Ohne/Projekt/2026-09 Charge/_intern/x.py"],
                 werkzeuge=[("Edit", 1)], chargen=["projects/Ohne/Projekt/2026-09 Charge"])
    s2 = Sitzung(kennung="s2", titel="Offen", ordner="/wt", branch="claude/x", von="11:00", bis="11:06",
                 auftraege=["Offener Auftrag"], schluss="Ich prüfe.", schluss_offen=True, fehler_anzahl=5,
                 fehler=[f"Fehler {n}" for n in range(1, 6)], werkzeuge=[("Bash", 1)])
    return Tagesstand(mac="Test-Mac", tag=HEUTE, stand=STAND, repo="/repo", git=git, chargen=chargen,
                      sitzungen=SitzungenStand(sitzungen=[s1, s2]), notizen=[Notiz("notiz-a", "Eine Notiz")],
                      fehler=["Testfehler"])


def leerer_stand() -> Tagesstand:
    return Tagesstand(mac="Test-Mac", tag=HEUTE, stand=STAND, repo="/repo", git=GitStand(head_branch="main", head_hash="abc1234"),
                      chargen=ChargenStand(), sitzungen=SitzungenStand(), notizen=[])


class Hinweise(unittest.TestCase):
    def test_alle_hinweisarten(self):
        h = hinweise(voller_stand())
        self.assertEqual(h, [
            "Protokoll fehlt: projects/Ohne/Projekt/2026-09 Charge — Sitzung „Test-Sitzung“ (09:00–10:00)",
            "Ohne Schlussbericht: „Offen“ (11:00–11:06)",
            "Viele Tool-Fehler: „Offen“ (5)",
            "Ungepusht: claude/x (+1)",
        ])

    def test_worktree_mit_aenderungen(self):
        t = voller_stand()
        t.git.worktrees[1].gruppen.append(Gruppe("tools/b.txt", 1))
        self.assertIn("Worktree mit Änderungen: /wt (claude/x)", hinweise(t))

    def test_leer(self):
        self.assertEqual(hinweise(leerer_stand()), [])


class Rendern(unittest.TestCase):
    def setUp(self):
        self.md = rendern(voller_stand())

    def test_kopf(self):
        zeilen = self.md.splitlines()
        self.assertEqual(zeilen[0], "# Tagesstand Test-Mac — 2026-09-17")
        self.assertEqual(zeilen[1], "Stand: 2026-09-17 16:40 · Repo /repo · HEAD main abc1234 · Sitzungen 2 · Commits 2")

    def test_git(self):
        self.assertIn("## Git\n### Auf main\n- 10:00 abc1234 A heute\n", self.md)
        self.assertIn("### Ungepusht\n- claude/x (+1 / −0, letzter Commit 2026-09-17, Worktree /wt)\n  - 11:30 b000000 B ungepusht\n", self.md)
        self.assertIn("### Branches ohne Commits heute\n- main: +0 / −0, letzter Commit 2026-09-17\n", self.md)
        self.assertIn("### Unversioniert (Hauptordner, main)\n- tools/motion/: 0 geändert, 2 neu, 0 gelöscht, jüngste 2026-09-17 09:00 — tools/motion/neu.ts, tools/motion/src/x.ts\n", self.md)
        self.assertIn("### Unversioniert (/wt, claude/x)\n- keine\nStashes: 1\n", self.md)

    def test_chargen(self):
        self.assertIn("## Chargen\n### Protokoll-Einträge\n- „2026-09-17 — Medien aufs NAS verschoben“ — in 6 Chargen\n- projects/Kunde/Projekt/2026-09 Charge\n  - 2026-09-17 11:07 — AutoCut: Kantenprüfung\n", self.md)
        self.assertIn("### Neue Dateien unter Ergebnisse/\n- projects/Kunde/Projekt/2026-09 Charge: 7 Dateien — Export/a.mp4, Export/b.mp4 (+5)\n", self.md)
        self.assertIn("Änderungszeiten bleiben beim Abgleich erhalten", self.md)

    def test_sitzungen(self):
        self.assertIn("### 09:00–10:00 · Test-Sitzung · main · 16 Aufträge · 1 Tool-Fehler\n- Ordner: . · Sitzung s1\n- Aufträge: 1. „Auftrag eins“ 2. „Auftrag zwei“ (+14 weitere)\n- Schlussbericht: „Schlussbericht: alles erledigt.“\n- Tool-Fehler: „Fehler: Datei fehlt“\n- Dateien: projects/Ohne/Projekt/2026-09 Charge/_intern/x.py\n- Werkzeuge: Edit 1\n- Chargen: projects/Ohne/Projekt/2026-09 Charge\n", self.md)
        self.assertIn("### 11:00–11:06 · Offen · claude/x · 1 Aufträge · 5 Tool-Fehler\n", self.md)
        self.assertIn("- Schlussbericht: ohne Schlussbericht — letzte Antwort: „Ich prüfe.“\n", self.md)

    def test_gedaechtnis_und_hinweise(self):
        self.assertIn("## Gedächtnis\n- notiz-a: Eine Notiz\n", self.md)
        self.assertIn("## Hinweise\n- Protokoll fehlt: projects/Ohne/Projekt/2026-09 Charge", self.md)
        self.assertIn("- Fehler: Testfehler\n", self.md)

    def test_leer_ueberall_keine(self):
        md = rendern(leerer_stand())
        for abschnitt in ("### Auf main", "### Ungepusht", "### Branches ohne Commits heute", "### Protokoll-Einträge",
                          "### Neue Dateien unter Ergebnisse/", "## Sitzungen", "## Gedächtnis", "## Hinweise"):
            self.assertIn(abschnitt + "\n- keine\n", md)
        self.assertIn("Sitzungen 0 · Commits 0", md)
        self.assertIn("Stashes: 0\n", md)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Tests laufen lassen — fehlschlagen**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py`
Expected: Import-Fehler für `gedaechtnis_stand` und `bericht`.

- [ ] **Step 3: `tools/tagesbericht/gedaechtnis_stand.py` schreiben**

```python
"""Quelle Gedächtnis (Spec 2.4): am Tag geänderte Notizen mit ihrer Beschreibungszeile."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from text import kuerzen
from umgebung import tagesgrenzen

BESCHREIBUNG_MAX = 160


@dataclass
class Notiz:
    name: str
    beschreibung: str


def frontmatter(datei: Path) -> tuple[str, str]:
    """name und description aus dem YAML-Kopf (nur einzeilige Werte, Anführungszeichen entfernt)."""
    name = beschreibung = ""
    with open(datei, encoding="utf-8", errors="replace") as fh:
        if fh.readline().strip() != "---":
            return "", ""
        for zeile in fh:
            if zeile.strip() == "---":
                break
            if zeile.startswith("name:"):
                name = zeile[len("name:"):].strip().strip('"')
            elif zeile.startswith("description:"):
                beschreibung = zeile[len("description:"):].strip().strip('"').replace('\\"', '"')
    return name, beschreibung


def gedaechtnis_stand(ordner: Path, tag: date) -> tuple[list[Notiz], list[str]]:
    anfang, ende = tagesgrenzen(tag)
    von, bis = anfang.timestamp(), ende.timestamp()
    try:
        dateien = sorted(p for p in ordner.iterdir() if p.suffix == ".md" and p.name != "MEMORY.md")
    except OSError as e:
        return [], [f"Gedächtnis {ordner}: {e}"]
    notizen, fehler = [], []
    for datei in dateien:
        try:
            if not (von <= datei.stat().st_mtime < bis):
                continue
            name, beschreibung = frontmatter(datei)
        except OSError as e:
            fehler.append(f"{datei.name}: {e}")
            continue
        notizen.append(Notiz(name=name or datei.stem, beschreibung=kuerzen(beschreibung, BESCHREIBUNG_MAX)))
    return notizen, fehler
```

- [ ] **Step 4: `tools/tagesbericht/bericht.py` schreiben**

```python
"""Tagesstand eines Macs: Hinweise (Spec 2.5) und Markdown mit festen Überschriften (Spec 2.7)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from chargen_stand import ChargenStand
from gedaechtnis_stand import Notiz
from git_stand import Branch, GitStand
from sitzungen_stand import Sitzung, SitzungenStand

VIELE_FEHLER_AB = 5


@dataclass
class Tagesstand:
    mac: str
    tag: date
    stand: datetime
    repo: str
    git: GitStand
    chargen: ChargenStand
    sitzungen: SitzungenStand
    notizen: list[Notiz]
    fehler: list[str] = field(default_factory=list)


def hinweise(t: Tagesstand) -> list[str]:
    h = []
    mit_protokoll = set(t.chargen.je_charge_alle)
    for s in t.sitzungen.sitzungen:
        for c in s.chargen:
            if c not in mit_protokoll:
                h.append(f"Protokoll fehlt: {c} — Sitzung „{s.titel}“ ({s.von}–{s.bis})")
    for s in t.sitzungen.sitzungen:
        if s.schluss_offen:
            h.append(f"Ohne Schlussbericht: „{s.titel}“ ({s.von}–{s.bis})")
    for s in t.sitzungen.sitzungen:
        if s.fehler_anzahl >= VIELE_FEHLER_AB:
            h.append(f"Viele Tool-Fehler: „{s.titel}“ ({s.fehler_anzahl})")
    for b in t.git.branches:
        if b.vor:
            h.append(f"Ungepusht: {b.name} (+{b.vor})")
    for w in t.git.worktrees:
        if not w.ist_haupt and w.gruppen:
            h.append(f"Worktree mit Änderungen: {w.pfad} ({w.branch})")
    return h


def _abschnitt(z: list[str], titel: str, zeilen: list[str]) -> None:
    z.append(titel)
    z.extend(zeilen if zeilen else ["- keine"])


def _vorsprung(b: Branch) -> str:
    return "ohne origin/main" if b.vor is None else f"+{b.vor} / −{b.hinter}"


def _branchzusatz(b: Branch) -> str:
    return f", Worktree {b.worktree}" if b.worktree else ""


def _anfuehren(text: str) -> str:
    return f"„{text}“"


def _mit_rest(beispiele: list[str], rest: int) -> str:
    return ", ".join(beispiele) + (f" (+{rest})" if rest > 0 else "")


def _sitzung(s: Sitzung) -> list[str]:
    n_auftraege = len(s.auftraege) + s.weitere_auftraege
    z = [f"### {s.von}–{s.bis} · {s.titel} · {s.branch or '–'} · {n_auftraege} Aufträge · {s.fehler_anzahl} Tool-Fehler",
         f"- Ordner: {s.ordner or '–'} · Sitzung {s.kennung}"]
    if s.auftraege:
        auftraege = " ".join(f"{i}. {_anfuehren(a)}" for i, a in enumerate(s.auftraege, 1))
        z.append(f"- Aufträge: {auftraege}" + (f" (+{s.weitere_auftraege} weitere)" if s.weitere_auftraege else ""))
    if s.schluss_offen:
        z.append("- Schlussbericht: ohne Schlussbericht" + (f" — letzte Antwort: {_anfuehren(s.schluss)}" if s.schluss else ""))
    else:
        z.append(f"- Schlussbericht: {_anfuehren(s.schluss)}")
    if s.fehler:
        z.append("- Tool-Fehler: " + " · ".join(_anfuehren(f) for f in s.fehler))
    if s.dateien:
        z.append(f"- Dateien: {_mit_rest(s.dateien, s.weitere_dateien)}")
    if s.werkzeuge:
        z.append("- Werkzeuge: " + ", ".join(f"{name} {n}" for name, n in s.werkzeuge))
    if s.chargen:
        z.append("- Chargen: " + ", ".join(s.chargen))
    return z


def _worktree_name(pfad: str, repo: str, ist_haupt: bool) -> str:
    if ist_haupt:
        return "Hauptordner"
    return pfad[len(repo) + 1:] if pfad.startswith(repo + "/") else pfad


def rendern(t: Tagesstand) -> str:
    z: list[str] = []
    z.append(f"# Tagesstand {t.mac} — {t.tag.isoformat()}")
    z.append(f"Stand: {t.stand.strftime('%Y-%m-%d %H:%M')} · Repo {t.repo} · HEAD {t.git.head_branch} {t.git.head_hash}"
             f" · Sitzungen {len(t.sitzungen.sitzungen)} · Commits {t.git.commits_gesamt}")
    z.append("")
    z.append("## Git")
    _abschnitt(z, "### Auf main", [f"- {c.zeit} {c.hash} {c.betreff}" for c in t.git.auf_main])
    ungepusht: list[str] = []
    ohne: list[str] = []
    for b in t.git.branches:
        if b.commits_heute:
            ungepusht.append(f"- {b.name} ({_vorsprung(b)}, letzter Commit {b.letzter}{_branchzusatz(b)})")
            ungepusht.extend(f"  - {c.zeit} {c.hash} {c.betreff}" for c in b.commits_heute)
        else:
            ohne.append(f"- {b.name}: {_vorsprung(b)}, letzter Commit {b.letzter}{_branchzusatz(b)}")
    _abschnitt(z, "### Ungepusht", ungepusht)
    _abschnitt(z, "### Branches ohne Commits heute", ohne)
    for w in t.git.worktrees:
        zeilen = [f"- {g.pfad}: {g.geaendert} geändert, {g.neu} neu, {g.geloescht} gelöscht, jüngste {g.juengste or '–'}"
                  f" — {_mit_rest(g.beispiele, g.weitere)}" for g in w.gruppen]
        _abschnitt(z, f"### Unversioniert ({_worktree_name(w.pfad, t.repo, w.ist_haupt)}, {w.branch})", zeilen)
    z.append(f"Stashes: {t.git.stashes}")
    z.append("")
    z.append("## Chargen")
    eintraege = [f"- {_anfuehren(u)} — in {n} Chargen" for u, n in t.chargen.sammel]
    for charge, ueberschriften in t.chargen.je_charge.items():
        eintraege.append(f"- {charge}")
        eintraege.extend(f"  - {u}" for u in ueberschriften)
    _abschnitt(z, "### Protokoll-Einträge", eintraege)
    lieferungen = [f"- {l.charge}: {l.anzahl} Dateien — {_mit_rest(l.beispiele, l.anzahl - len(l.beispiele))}"
                   for l in t.chargen.lieferungen]
    if lieferungen:
        lieferungen.append("(Änderungszeiten bleiben beim Abgleich erhalten; Dateien können vom anderen Mac stammen.)")
    _abschnitt(z, "### Neue Dateien unter Ergebnisse/", lieferungen)
    z.append("")
    sitzungen: list[str] = []
    for s in t.sitzungen.sitzungen:
        sitzungen.extend(_sitzung(s))
    _abschnitt(z, "## Sitzungen", sitzungen)
    z.append("")
    _abschnitt(z, "## Gedächtnis", [f"- {n.name}: {n.beschreibung}" for n in t.notizen])
    z.append("")
    alle_fehler = t.fehler + t.git.fehler + t.chargen.fehler + t.sitzungen.fehler
    _abschnitt(z, "## Hinweise", [f"- {h}" for h in hinweise(t)] + [f"- Fehler: {f}" for f in alle_fehler])
    return "\n".join(z) + "\n"
```

- [ ] **Step 5: Tests laufen lassen — grün**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py`
Expected: `OK`. Scheitert `test_git` an der Stashes-Zeile: Sie steht direkt nach dem letzten Worktree-Abschnitt, ohne Leerzeile davor.

- [ ] **Step 6: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/tagesbericht/gedaechtnis_stand.py tools/tagesbericht/bericht.py tools/tagesbericht/testhilfe.py tools/tagesbericht/gedaechtnis_stand_test.py tools/tagesbericht/bericht_test.py && git -c core.quotepath=false diff --cached --name-only && git commit -q -m "feat(tagesbericht): Gedächtnis-Notizen, Hinweise und Markdown-Tagesstand

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: `studio_abgleich.sh --berichte` und Sammler-Aufruf

**Files:**
- Modify: `tools/studio_abgleich.sh` (Kopfkommentar Zeilen 6–11, `case` Zeilen 18–25, neue Funktionen nach `chargen_abgleichen`, Hauptablauf Zeilen 193–206)
- Modify: `tools/studio_abgleich_test.sh` (zwei Tests vor `echo "Test 5: NAS fehlt"`)

**Interfaces:**
- Consumes: bestehende Shell-Funktionen `abgleich`, `teil`, `nas_da`, Variablen `REPO`, `NAS`, `MODUS`, `TEILE`.
- Produces: Option `--berichte` (nur `berichte/` spiegeln, kein Sammler, Ende 0), Funktion `berichte_abgleichen`, Funktion `sammler` (ruft `$NIRO_SAMMLER_CMD` oder `python3 tools/tagesbericht/sammler.py --still --ohne-abgleich`, nie blockierend). Aufgabe 7 verlässt sich darauf, dass `sh tools/studio_abgleich.sh --berichte` `berichte/` in beide Richtungen spiegelt.

- [ ] **Step 1: Shell-Tests anfügen**

In `tools/studio_abgleich_test.sh` **vor** der Zeile `echo "Test 5: NAS fehlt"` einfügen:

```sh
echo "Test 10: --berichte spiegelt nur berichte/ und ruft den Sammler nicht"
neues_setup t10
printf '#!/bin/sh\ntouch "%s/t10/sammler_lief"\n' "$T" > "$T/t10/sammler.sh"; chmod +x "$T/t10/sammler.sh"
NIRO_SAMMLER_CMD="$T/t10/sammler.sh"; export NIRO_SAMMLER_CMD
mkdir -p "$NIRO_STUDIO_REPO/berichte/2026-09-17" "$NIRO_STUDIO_NAS/berichte/2026-09-16" "$NIRO_STUDIO_REPO/projects/K"
echo "lokal" > "$NIRO_STUDIO_REPO/berichte/2026-09-17/A.md"
echo "nas" > "$NIRO_STUDIO_NAS/berichte/2026-09-16/B.md"
echo "charge" > "$NIRO_STUDIO_REPO/projects/K/x.md"
AUS=$(lauf --berichte); RC=$?
pruefe "lokaler Bericht liegt auf dem NAS" '[ "$(cat "$NIRO_STUDIO_NAS/berichte/2026-09-17/A.md")" = "lokal" ]'
pruefe "NAS-Bericht liegt lokal" '[ "$(cat "$NIRO_STUDIO_REPO/berichte/2026-09-16/B.md")" = "nas" ]'
pruefe "projects/ nicht angefasst" '[ ! -e "$NIRO_STUDIO_NAS/projects/K/x.md" ]'
pruefe "Sammler nicht aufgerufen" '[ ! -e "$T/t10/sammler_lief" ]'
pruefe "Zusammenfassung und Exit 0" 'printf "%s" "$AUS" | grep -q "Berichte: 1 geholt, 1 hochgeladen" && [ "$RC" -eq 0 ]'

echo "Test 11: normaler Lauf ruft den Sammler und spiegelt danach berichte/"
neues_setup t11
printf '#!/bin/sh\nmkdir -p "%s/berichte/2026-09-17"\necho "vom Sammler" > "%s/berichte/2026-09-17/S.md"\n' "$NIRO_STUDIO_REPO" "$NIRO_STUDIO_REPO" > "$T/t11/sammler.sh"; chmod +x "$T/t11/sammler.sh"
NIRO_SAMMLER_CMD="$T/t11/sammler.sh"; export NIRO_SAMMLER_CMD
AUS=$(lauf)
pruefe "Bericht des Sammlers liegt auf dem NAS" '[ "$(cat "$NIRO_STUDIO_NAS/berichte/2026-09-17/S.md")" = "vom Sammler" ]'
pruefe "Zusammenfassung nennt Berichte" 'printf "%s" "$AUS" | grep -q "Berichte: 0 geholt, 1 hochgeladen"'
printf '#!/bin/sh\nexit 3\n' > "$T/t11/sammler.sh"
AUS=$(lauf); RC=$?
pruefe "Sammler-Fehler blockiert nicht" '[ "$RC" -eq 0 ] && printf "%s" "$AUS" | grep -q "Sammler: fehlgeschlagen"'
unset NIRO_SAMMLER_CMD

```

- [ ] **Step 2: Tests laufen lassen — Test 10/11 rot**

Run: `cd "/Users/jansantos/NIRO Studio" && sh tools/studio_abgleich_test.sh 2>&1 | grep -E 'FEHLER|bestanden|fehlgeschlagen'`
Expected: Zeilen `FEHLER` für Test 10 (unbekannte Option) und Test 11, am Ende „N Test(s) fehlgeschlagen".

- [ ] **Step 3: Skript ändern**

Kopfkommentar: nach der Zeile `#   sh tools/studio_abgleich.sh --nach-pull         alles + Abhängigkeiten (so rufen es die Git-Hooks)` einfügen:

```sh
#   sh tools/studio_abgleich.sh --berichte          nur berichte/ (Tagesstände) spiegeln — so ruft es der Sammler
```

und nach `# Regeln: …` den Satz ergänzen: `# berichte/ (Tagesstände beider Macs, Spec docs/superpowers/specs/2026-09-17-tagesbericht-design.md) wird wie projects/ gespiegelt; vorher läuft tools/tagesbericht/sammler.py.`

`case`: Zeile `--umstieg) MODUS=umstieg ;;` ergänzen um eine neue Zeile davor:

```sh
	--berichte) MODUS=berichte ;;
```

und in der Fehlermeldung der `*)`-Zeile `(--charge <Pfad> | --nach-pull | --berichte | --umstieg)`.

Nach der Funktion `chargen_abgleichen` (nach deren schließender `}`) einfügen:

```sh
berichte_abgleichen() {
	lokal="$REPO/berichte"; fern="$NAS/berichte"
	mkdir -p "$lokal" "$fern" || { teil "Berichte: Ordner nicht anlegbar"; return; }
	abgleich "$fern" "$lokal" "NAS → lokal (Berichte)"; geholt=$ANZAHL
	abgleich "$lokal" "$fern" "lokal → NAS (Berichte)"; hochgeladen=$ANZAHL
	teil "Berichte: $geholt geholt, $hochgeladen hochgeladen"
}

# Tagesstand dieses Macs schreiben (tools/tagesbericht/sammler.py), ohne eigenen Abgleich — der folgt gleich hier.
sammler() {
	skript="$REPO/tools/tagesbericht/sammler.py"
	if [ -n "${NIRO_SAMMLER_CMD:-}" ]; then
		"$NIRO_SAMMLER_CMD" >/dev/null 2>&1 || teil "Sammler: fehlgeschlagen"
	elif [ -f "$skript" ] && command -v python3 >/dev/null 2>&1; then
		python3 "$skript" --still --ohne-abgleich >/dev/null 2>&1 || teil "Sammler: fehlgeschlagen"
	fi
}
```

Hauptablauf am Ende ersetzen — von `gedaechtnis_verknuepfen` bis `exit 0`:

```sh
if [ "$MODUS" = "berichte" ]; then
	berichte_abgleichen
	echo "$TEILE"
	exit 0
fi
gedaechtnis_verknuepfen
chargen_abgleichen
[ -f "$REPO/tools/resolve/luts_sync.sh" ] && sh "$REPO/tools/resolve/luts_sync.sh"
sammler
berichte_abgleichen
[ "$MODUS" = "nach-pull" ] && abhaengigkeiten
echo "$TEILE"
exit 0
```

(Der `nas_da`-Block davor bleibt: Ohne NAS endet auch `--berichte` mit dem Hinweis und 0.)

- [ ] **Step 4: Tests laufen lassen — grün**

Run: `cd "/Users/jansantos/NIRO Studio" && sh tools/studio_abgleich_test.sh 2>&1 | tail -15`
Expected: alle `ok`, „Alle Tests bestanden.". Danach `sh tools/studio_abgleich.sh --berichte` einmal echt laufen lassen: Ausgabe „Berichte: 0 geholt, 0 hochgeladen" (oder Zahlen), und `ls "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio/berichte"` zeigt den neuen Ordner.

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/studio_abgleich.sh tools/studio_abgleich_test.sh && git -c core.quotepath=false diff --cached --name-only && git commit -q -m "feat(studio): studio_abgleich.sh --berichte, Sammler vor dem Berichte-Abgleich

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: `sammler.py` — CLI, Abgleich mit Zeitlimit, Hook-Hinweis

**Files:**
- Create: `tools/tagesbericht/sammler.py`
- Modify: `tools/tagesbericht/sammler_test.py` (Ende-zu-Ende-Tests vor dem `if __name__` einfügen)

**Interfaces:**
- Consumes: `umgebung.umgebung_laden/tag_parsen/Umgebung`, `git_stand.git_stand/sicherung`, `chargen_stand.chargen_stand`, `sitzungen_stand.sitzungen_stand`, `gedaechtnis_stand.gedaechtnis_stand`, `bericht.Tagesstand/rendern`; `sh tools/studio_abgleich.sh --berichte` (Aufgabe 6); Testhilfen aus Aufgaben 2–5.
- Produces: CLI `python3 tools/tagesbericht/sammler.py [--tag T] [--still] [--ohne-abgleich] [--hook]`, Funktionen `main(argv) -> int` (immer 0), `tagesstand(umg, tag, jetzt) -> Tagesstand`, `schreiben(ziel, text)` (Temp-Datei + `os.replace`), `abgleichen(umg, zeitlimit, still)`, `hinweis(umg) -> str`. Dateien `berichte/<Tag>/<Mac>.md` (heute und gestern bzw. `--tag`), `berichte/<heute>/<Mac>.patch` (nur für heute).

- [ ] **Step 1: Ende-zu-Ende-Tests schreiben**

`tools/tagesbericht/sammler_test.py` wird zu: Docstring, dann der folgende Kopf (Importe, Konstanten, `ohne_stand`), dann die
Klasse `SammlerEndeZuEnde`, danach unverändert der bestehende `if __name__ == "__main__":`-Block mit dem Runner (der `HIER`
aus dem Kopf verwendet):

```python
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import date
from pathlib import Path

from testhilfe import chargen_anlegen, gedaechtnis_anlegen, repo_anlegen, sitzungen_anlegen

HIER = Path(__file__).resolve().parent
SAMMLER = HIER / "sammler.py"
ABGLEICH_ECHT = HIER.parent / "studio_abgleich.sh"
HEUTE = date(2026, 9, 17)


def ohne_stand(text: str) -> str:
    return "\n".join(z for z in text.splitlines() if not z.startswith("Stand: "))


class SammlerEndeZuEnde(unittest.TestCase):
    def setUp(self):
        self.basis = Path(tempfile.mkdtemp(prefix="sammler_test_"))
        daten = repo_anlegen(self.basis, HEUTE)
        self.repo, self.wt = daten["repo"], daten["wt"]
        chargen_anlegen(self.repo, HEUTE)
        self.projects_dir = self.basis / "claude" / "projects"
        sitzungen_anlegen(self.projects_dir, self.repo, self.wt, HEUTE)
        self.gedaechtnis = self.basis / "gedaechtnis"
        gedaechtnis_anlegen(self.gedaechtnis, HEUTE)
        self.nas = self.basis / "nas" / "NIRO Studio"
        (self.basis / "nas").mkdir()
        shutil.copy(ABGLEICH_ECHT, self.repo / "tools" / "studio_abgleich.sh")
        self.env = {**os.environ,
                    "NIRO_STUDIO_REPO": str(self.repo), "NIRO_STUDIO_NAS": str(self.nas), "NIRO_STUDIO_MAC": "Test-Mac",
                    "NIRO_STUDIO_HEUTE": HEUTE.isoformat(), "NIRO_CLAUDE_PROJECTS_DIR": str(self.projects_dir),
                    "NIRO_CLAUDE_MEMORY_DIR": str(self.gedaechtnis),
                    "NIRO_RESOLVE_LUT_DIR": str(self.basis / "lut_lokal"), "NIRO_NAS_LUT_DIR": str(self.basis / "lut_nas" / "NIRO Grading")}
        for k in ("NIRO_SAMMLER_CMD", "NIRO_SAMMLER_ABGLEICH_CMD", "NIRO_SAMMLER_ABGLEICH_TIMEOUT"):
            self.env.pop(k, None)
        self.berichte = self.repo / "berichte"

    def tearDown(self):
        shutil.rmtree(self.basis, ignore_errors=True)

    def lauf(self, *args, **env):
        return subprocess.run([sys.executable, str(SAMMLER), *args], env={**self.env, **env}, capture_output=True,
                              text=True, cwd=str(self.repo), timeout=120)

    def test_schreibt_heute_und_gestern_ohne_abgleich(self):
        aus = self.lauf("--ohne-abgleich")
        self.assertEqual(aus.returncode, 0, aus.stderr)
        heute = (self.berichte / "2026-09-17" / "Test-Mac.md").read_text()
        gestern = (self.berichte / "2026-09-16" / "Test-Mac.md").read_text()
        patch = (self.berichte / "2026-09-17" / "Test-Mac.patch").read_text()
        self.assertTrue(heute.startswith("# Tagesstand Test-Mac — 2026-09-17\n"))
        self.assertIn("Sitzungen 2 · Commits 2", heute)
        for erwartet in ("A heute", "B ungepusht", "Test-Sitzung", "Offener Auftrag", "AutoCut: Kantenprüfung",
                         "— in 6 Chargen", "Export/a.mp4", "notiz-a", "Protokoll fehlt: projects/Ohne/Projekt/2026-09 Charge",
                         "Ungepusht: claude/x (+1)", "Worktree mit Änderungen"):
            self.assertIn(erwartet, heute)
        self.assertIn("A0 gestern", gestern)
        self.assertIn("Gestern-Auftrag", gestern)
        self.assertIn("Sitzungen 1 · Commits 1", gestern)
        self.assertFalse((self.berichte / "2026-09-16" / "Test-Mac.patch").exists())
        self.assertTrue(patch.startswith("# Sicherung Test-Mac "))
        self.assertIn("+Inhalt der neuen Datei", patch)
        self.assertFalse((self.nas / "berichte").exists())
        self.assertIn("Sammler: berichte/2026-09-17/Test-Mac.md", aus.stdout)

    def test_zweiter_lauf_gleicher_inhalt(self):
        self.lauf("--ohne-abgleich")
        erster = (self.berichte / "2026-09-17" / "Test-Mac.md").read_text()
        time.sleep(1.1)
        self.lauf("--ohne-abgleich")
        zweiter = (self.berichte / "2026-09-17" / "Test-Mac.md").read_text()
        self.assertEqual(ohne_stand(erster), ohne_stand(zweiter))

    def test_nur_ein_tag(self):
        aus = self.lauf("--tag", "2026-09-16", "--ohne-abgleich", "--still")
        self.assertEqual((aus.returncode, aus.stdout), (0, ""))
        self.assertTrue((self.berichte / "2026-09-16" / "Test-Mac.md").exists())
        self.assertFalse((self.berichte / "2026-09-17").exists())

    def test_abgleich_mit_echtem_skript(self):
        fremd = self.nas / "berichte" / "2026-09-15" / "Anderer-Mac.md"
        fremd.parent.mkdir(parents=True)
        fremd.write_text("# Tagesstand Anderer-Mac — 2026-09-15\nStand: 2026-09-15 18:00 · Repo x · HEAD main a · Sitzungen 2 · Commits 0\n")
        aus = self.lauf()
        self.assertEqual(aus.returncode, 0, aus.stderr)
        self.assertTrue((self.nas / "berichte" / "2026-09-17" / "Test-Mac.md").exists())
        self.assertTrue((self.nas / "berichte" / "2026-09-17" / "Test-Mac.patch").exists())
        self.assertEqual((self.berichte / "2026-09-15" / "Anderer-Mac.md").read_text(), fremd.read_text())

    def test_hook_hinweis(self):
        fremd = self.nas / "berichte" / "2026-09-15" / "Anderer-Mac.md"
        fremd.parent.mkdir(parents=True)
        fremd.write_text("# Tagesstand Anderer-Mac — 2026-09-15\nStand: 2026-09-15 18:00 · Repo x · HEAD main a · Sitzungen 2 · Commits 0\n")
        leer = self.nas / "berichte" / "2026-09-14" / "Anderer-Mac.md"
        leer.parent.mkdir(parents=True)
        leer.write_text("# Tagesstand Anderer-Mac — 2026-09-14\nStand: 2026-09-14 18:00 · Repo x · HEAD main a · Sitzungen 0 · Commits 0\n")
        aus = self.lauf("--hook")
        self.assertEqual(aus.returncode, 0, aus.stderr)
        self.assertEqual(aus.stdout, "Tagesbericht für 16.09.2026 fehlt — Trigger: „Tagesbericht: 2026-09-16“.\n")
        (self.berichte / "2026-09-16" / "Tagesbericht.md").write_text("# Tagesbericht\n")
        aus = self.lauf("--hook")
        self.assertEqual(aus.stdout, "Tagesbericht für 15.09.2026 fehlt — Trigger: „Tagesbericht: 2026-09-15“.\n")
        (self.berichte / "2026-09-15" / "Tagesbericht.md").write_text("# Tagesbericht\n")
        aus = self.lauf("--hook")
        self.assertEqual(aus.stdout, "")

    def test_abgleich_zeitlimit(self):
        schlaefer = self.basis / "schlaefer.sh"
        schlaefer.write_text("#!/bin/sh\nsleep 5\n")
        schlaefer.chmod(schlaefer.stat().st_mode | stat.S_IXUSR)
        start = time.monotonic()
        aus = self.lauf("--hook", NIRO_SAMMLER_ABGLEICH_CMD=str(schlaefer), NIRO_SAMMLER_ABGLEICH_TIMEOUT="1")
        self.assertLess(time.monotonic() - start, 4)
        self.assertEqual(aus.returncode, 0)
        self.assertIn("Abgleich abgebrochen", aus.stderr)
        self.assertTrue((self.berichte / "2026-09-17" / "Test-Mac.md").exists())

    def test_robust_ohne_sitzungen_nas_und_gedaechtnis(self):
        aus = self.lauf(NIRO_CLAUDE_PROJECTS_DIR=str(self.basis / "fehlt"), NIRO_STUDIO_NAS=str(self.basis / "weg" / "NIRO Studio"),
                        NIRO_CLAUDE_MEMORY_DIR=str(self.basis / "fehlt2"))
        self.assertEqual(aus.returncode, 0, aus.stderr)
        heute = (self.berichte / "2026-09-17" / "Test-Mac.md").read_text()
        self.assertIn("## Sitzungen\n- keine\n", heute)
        self.assertIn("Sitzungen 0 · Commits 2", heute)
        self.assertIn("- Fehler: Gedächtnis", heute)

    def test_kaputtes_repo_endet_mit_null(self):
        aus = self.lauf("--ohne-abgleich", NIRO_STUDIO_REPO=str(self.basis / "kein-repo"))
        self.assertEqual(aus.returncode, 0)
        self.assertTrue((self.basis / "kein-repo" / "berichte" / "2026-09-17" / "Test-Mac.md").exists())
```

- [ ] **Step 2: Tests laufen lassen — fehlschlagen**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py 2>&1 | tail -5`
Expected: die acht neuen Tests scheitern (`sammler.py` fehlt: `FileNotFoundError`/`returncode 2`).

- [ ] **Step 3: `tools/tagesbericht/sammler.py` schreiben**

```python
#!/usr/bin/env python3
"""Sammler: Tagesstand dieses Macs nach berichte/<Tag>/<Mac>.md (+ <Mac>.patch für heute), danach berichte/ übers NAS
abgleichen. Spec: docs/superpowers/specs/2026-09-17-tagesbericht-design.md

  python3 tools/tagesbericht/sammler.py                 heute und gestern neu schreiben, dann berichte/ abgleichen
  … --tag 2026-09-16 | --tag gestern | --tag heute      nur diesen Tag
  … --still                                             keine Ausgabe auf stdout
  … --ohne-abgleich                                     studio_abgleich.sh --berichte nicht aufrufen
  … --hook                                              SessionStart-Hook: still, Abgleich mit 8 s Zeitlimit, einzige
                                                        Ausgabe ist der Hinweis auf einen fehlenden Tagesbericht
Endet immer mit 0; Fehler stehen auf stderr."""
from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from bericht import Tagesstand, rendern
from chargen_stand import chargen_stand
from gedaechtnis_stand import gedaechtnis_stand
from git_stand import git_stand, sicherung
from sitzungen_stand import sitzungen_stand
from umgebung import Umgebung, tag_parsen, umgebung_laden

ABGLEICH_ZEITLIMIT = 120.0
ABGLEICH_ZEITLIMIT_HOOK = 8.0
HINWEIS_TAGE = 7
STAND_MUSTER = re.compile(r"Sitzungen (\d+) · Commits (\d+)")


def tagesstand(umg: Umgebung, tag: date, jetzt: datetime) -> Tagesstand:
    notizen, fehler = gedaechtnis_stand(umg.gedaechtnis, tag)
    return Tagesstand(mac=umg.mac, tag=tag, stand=jetzt, repo=str(umg.repo),
                      git=git_stand(umg.repo, tag), chargen=chargen_stand(umg.repo, tag),
                      sitzungen=sitzungen_stand(umg.sitzungsordner(), tag, umg.repo), notizen=notizen, fehler=fehler)


def schreiben(ziel: Path, text: str) -> None:
    """Über eine Temp-Datei im selben Ordner und os.replace — parallele Läufe stören sich nicht."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(ziel.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, ziel)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def abgleichen(umg: Umgebung, zeitlimit: float, still: bool) -> None:
    """`sh tools/studio_abgleich.sh --berichte` mit Zeitlimit; bei Überschreitung die ganze Prozessgruppe beenden."""
    ersatz = os.environ.get("NIRO_SAMMLER_ABGLEICH_CMD")
    skript = umg.repo / "tools" / "studio_abgleich.sh"
    if ersatz:
        befehl = [ersatz]
    elif skript.is_file():
        befehl = ["sh", str(skript), "--berichte"]
    else:
        return
    try:
        prozess = subprocess.Popen(befehl, cwd=str(umg.repo), stdout=subprocess.DEVNULL if still else None,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError as e:
        print(f"Sammler: Abgleich nicht gestartet: {e}", file=sys.stderr)
        return
    try:
        prozess.wait(timeout=zeitlimit)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(prozess.pid, signal.SIGTERM)
        except OSError:
            pass
        print(f"Sammler: Abgleich abgebrochen nach {zeitlimit:g} s — lokaler Stand bleibt, nächster Abgleich holt nach",
              file=sys.stderr)


def _aktiv(datei: Path) -> bool:
    """Stand-Zeile eines Tagesstands: Sitzungen oder Commits > 0."""
    try:
        with open(datei, encoding="utf-8", errors="replace") as fh:
            for _ in range(3):
                treffer = STAND_MUSTER.search(fh.readline())
                if treffer:
                    return int(treffer.group(1)) > 0 or int(treffer.group(2)) > 0
    except OSError:
        pass
    return False


def hinweis(umg: Umgebung) -> str:
    """Jüngster Tag vor heute (bis 7 Tage zurück) mit einem aktiven Tagesstand, aber ohne Tagesbericht.md."""
    for zurueck in range(1, HINWEIS_TAGE + 1):
        tag = umg.heute - timedelta(days=zurueck)
        ordner = umg.berichte / tag.isoformat()
        if not ordner.is_dir() or (ordner / "Tagesbericht.md").is_file():
            continue
        if any(_aktiv(p) for p in ordner.glob("*.md") if p.name != "Tagesbericht.md"):
            return f"Tagesbericht für {tag.strftime('%d.%m.%Y')} fehlt — Trigger: „Tagesbericht: {tag.isoformat()}“."
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Tagesstand dieses Macs schreiben und berichte/ abgleichen.")
    parser.add_argument("--tag", help="JJJJ-MM-TT, „gestern“ oder „heute“ (Standard: heute und gestern)")
    parser.add_argument("--still", action="store_true")
    parser.add_argument("--ohne-abgleich", action="store_true")
    parser.add_argument("--hook", action="store_true")
    args = parser.parse_args(argv)
    still = args.still or args.hook
    try:
        umg = umgebung_laden()
        jetzt = datetime.now()
        tage = [tag_parsen(args.tag, umg.heute)] if args.tag else [umg.heute, umg.heute - timedelta(days=1)]
        for tag in tage:
            stand = tagesstand(umg, tag, jetzt)
            ziel = umg.berichte / tag.isoformat() / f"{umg.mac}.md"
            schreiben(ziel, rendern(stand))
            if tag == umg.heute:
                schreiben(ziel.parent / f"{umg.mac}.patch", sicherung(umg.repo, umg.mac, jetzt))
            if not still:
                print(f"Sammler: {ziel.relative_to(umg.repo).as_posix()} — Sitzungen {len(stand.sitzungen.sitzungen)},"
                      f" Commits {stand.git.commits_gesamt}")
        if not args.ohne_abgleich:
            standard = ABGLEICH_ZEITLIMIT_HOOK if args.hook else ABGLEICH_ZEITLIMIT
            abgleichen(umg, float(os.environ.get("NIRO_SAMMLER_ABGLEICH_TIMEOUT") or standard), still)
        if args.hook:
            zeile = hinweis(umg)
            if zeile:
                print(zeile)
    except Exception as e:  # noqa: BLE001 — der Sammler blockiert nie eine Sitzung
        print(f"Sammler: {type(e).__name__}: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Tests laufen lassen — grün**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py 2>&1 | tail -5`
Expected: `OK`. Bekannte Stolperstellen: `test_abgleich_mit_echtem_skript` braucht das in Aufgabe 6 geänderte `studio_abgleich.sh` (Option `--berichte`); `test_hook_hinweis` erwartet 16.09., weil der Verlauf `s1` einen Auftrag von gestern enthält und der Sammler gestern mitschreibt.

- [ ] **Step 5: Mac-Name setzen, echter Probelauf auf diesem Mac (nur lesend außer `berichte/`)**

Erst den Namen setzen, sonst hieße die Datei nach dem Computernamen („MacBook Pro") und läge später als dritter Mac auf dem NAS:

```bash
cd "/Users/jansantos/NIRO Studio" && git config niro.mac "Studio-Mac" && time python3 tools/tagesbericht/sammler.py --ohne-abgleich && sed -n '1,40p' "berichte/$(date +%F)/Studio-Mac.md"
```

Expected: Laufzeit unter 5 s; Stand-Zeile mit Sitzungen ≥ 7 (Prototyp 17.09.: 7) und Commits ≥ 10 auf main; Abschnitt „Unversioniert (Hauptordner, main)" mit `tools/motion/`, `tools/musik/`, `tools/sfx/`, `CLAUDE.md`; `.patch` unter 2 MB (17.09.: 65 unversionierte Dateien, 0,5 MB). Ist die Laufzeit über 5 s, die Sitzungsdateien prüfen (`ls -la ~/.claude/projects/-Users-jansantos-NIRO-Studio/*.jsonl | sort -k5 -n | tail -3`) und melden — nicht optimieren.

- [ ] **Step 6: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/tagesbericht/sammler.py tools/tagesbericht/sammler_test.py && git -c core.quotepath=false diff --cached --name-only && git commit -q -m "feat(tagesbericht): sammler.py — Tagesstand schreiben, Abgleich mit Zeitlimit, Hook-Hinweis

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: SessionStart-Hook, SETUP.md, README

**Files:**
- Create: `.claude/settings.json`
- Modify: `SETUP.md` (Schritt 2, nach dem Absatz „Meldet der LUT-Abgleich …")
- Create: `tools/tagesbericht/README.md`

**Interfaces:**
- Consumes: `python3 tools/tagesbericht/sammler.py --hook` (Aufgabe 7).
- Produces: Hook, der bei `startup` und `resume` jeder Claude-Code-Sitzung im Repo läuft und höchstens eine Hinweiszeile in den Kontext gibt; Doku für beide Macs.

- [ ] **Step 1: Hook anlegen**

`.claude/settings.json` (neu; `.claude/launch.json` ist bereits versioniert, `settings.local.json` bleibt ignoriert):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PROJECT_DIR:-.}/tools/tagesbericht/sammler.py\" --hook 2>/dev/null || true",
            "timeout": 20
          }
        ]
      }
    ]
  }
}
```

Prüfen, dass der Befehl auch ohne die Variable läuft (Ausgabe leer oder eine Hinweiszeile, Exit 0):

```bash
cd "/Users/jansantos/NIRO Studio" && sh -c 'python3 "${CLAUDE_PROJECT_DIR:-.}/tools/tagesbericht/sammler.py" --hook 2>/dev/null || true'; echo "rc=$?"
```

Expected: `rc=0`; wenn für gestern ein Tagesstand mit Sitzungen existiert und kein `Tagesbericht.md`, genau eine Zeile „Tagesbericht für 16.09.2026 fehlt — Trigger: „Tagesbericht: 2026-09-16"."

- [ ] **Step 2: SETUP.md ergänzen**

Nach dem Absatz, der mit `Meldet der LUT-Abgleich fehlendes Schreibrecht` beginnt (Ende von Schritt 2, vor `## 3. Systemwerkzeuge`), einfügen:

```markdown
**Mac-Name für die Tagesberichte** (einmal je Mac; Studio-Rechner „Studio-Mac", Zweit-MacBook „MacBook"):

```bash
git config niro.mac "MacBook"
```

Beim Start jeder Claude-Session schreibt der Hook aus `.claude/settings.json` den Tagesstand dieses Macs nach
`berichte/<Datum>/<Mac>.md` (`tools/tagesbericht/sammler.py`) und spiegelt `berichte/` aufs NAS; die Funktion
„Tagesbericht" fasst beide Macs zusammen (`tools/tagesbericht/README.md`). Ohne `niro.mac` heißt die Datei nach dem
Computernamen.
```

- [ ] **Step 3: README schreiben**

`tools/tagesbericht/README.md`:

```markdown
# Tagesbericht — Sammler und Haupt-Check

Tagesstand je Mac (Git, Chargen, Claude-Sitzungen, Gedächtnis) als `berichte/<JJJJ-MM-TT>/<Mac>.md`, dazu
`<Mac>.patch` (Sicherung der unversionierten Werkzeug-Änderungen, nur für heute). `berichte/` liegt im Hauptordner des
Repos, ist gitignoriert und wird wie `projects/` übers NAS gespiegelt (`NIRO Studio/berichte/`, beide Richtungen,
neuere Datei gewinnt, nie löschen). Der Haupt-Check — Funktion „Tagesbericht", Anleitung `WORKFLOW-Tagesbericht.md` —
liest die Dateien beider Macs und schreibt `berichte/<Tag>/Tagesbericht.md`; er empfiehlt nur, er merged nichts.
Spec: `docs/superpowers/specs/2026-09-17-tagesbericht-design.md`. Gebaut 17.09.2026.

## Aufrufe

| Aufruf | Wirkung |
|---|---|
| `python3 tools/tagesbericht/sammler.py` | heute und gestern neu schreiben, dann `sh tools/studio_abgleich.sh --berichte` |
| `… --tag 2026-09-16` / `--tag gestern` / `--tag heute` | nur diesen Tag |
| `… --still` | keine Ausgabe auf stdout |
| `… --ohne-abgleich` | ohne Abgleich (so ruft `studio_abgleich.sh` den Sammler, damit keine Schleife entsteht) |
| `… --hook` | SessionStart-Hook: still, Abgleich mit 8 s Zeitlimit, einzige Ausgabe ist der Hinweis auf einen fehlenden Tagesbericht der letzten sieben Tage |

Endet immer mit 0; Fehler stehen auf stderr, betroffene Abschnitte bleiben „keine". Läuft aus jedem Ordner des Repos,
auch aus einem Worktree (Hauptordner = erste Zeile von `git worktree list`). Python 3 ≥ 3.9, nur Standardbibliothek.

## Auslöser

- **SessionStart-Hook** (`.claude/settings.json`, versioniert, gilt auf beiden Macs): `--hook`, Zeitlimit 20 s.
- **`tools/studio_abgleich.sh`** (ohne Option, `--charge`, `--nach-pull`): ruft `--still --ohne-abgleich` und spiegelt
  danach `berichte/`. `--berichte` spiegelt nur.
- **Trigger „Tagesbericht"** im Chat (siehe `WORKFLOW-Tagesbericht.md`).

## Mac-Name

`git config niro.mac "Studio-Mac"` bzw. `"MacBook"` (SETUP.md Schritt 2); sonst der Computername
(`scutil --get ComputerName`); `/` und `:` werden `-`. Umgebungsvariable `NIRO_STUDIO_MAC` überschreibt beides.

## Format `<Mac>.md`

    # Tagesstand <Mac> — <JJJJ-MM-TT>
    Stand: <JJJJ-MM-TT HH:MM> · Repo <Pfad> · HEAD <Branch> <Hash> · Sitzungen <n> · Commits <n>
    ## Git
    ### Auf main · ### Ungepusht · ### Branches ohne Commits heute · ### Unversioniert (<Worktree>, <Branch>) … · Stashes: n
    ## Chargen
    ### Protokoll-Einträge (Sammelzeile ab fünf gleichen Überschriften) · ### Neue Dateien unter Ergebnisse/
    ## Sitzungen
    ### <von>–<bis> · <Titel> · <Branch> · <n> Aufträge · <n> Tool-Fehler
    - Ordner · Aufträge (bis 12) · Schlussbericht (1.500 Zeichen) · Tool-Fehler (bis 5) · Dateien (bis 20) · Werkzeuge · Chargen
    ## Gedächtnis
    ## Hinweise   (Protokoll fehlt · Ohne Schlussbericht · Viele Tool-Fehler · Ungepusht · Worktree mit Änderungen · Fehler)

Leere Abschnitte enthalten „- keine". Tagesgrenzen in Ortszeit. Sitzungsquellen: alle Ordner
`~/.claude/projects/<Schlüssel>*` (Hauptordner, Worktrees, Unterordner); Subagenten-Verläufe und Sidechains zählen nicht.
`<Mac>.patch`: `git diff HEAD` je Worktree plus `git diff --no-index` je unversionierter Textdatei (≤ 1 MB), gesamt
höchstens 5 MB; wird bei jedem Lauf neu geschrieben, weil der Spiegel nie löscht.

## Umgebungsvariablen (Tests)

`NIRO_STUDIO_REPO`, `NIRO_STUDIO_NAS`, `NIRO_STUDIO_MAC`, `NIRO_STUDIO_HEUTE` (`JJJJ-MM-TT`), `NIRO_CLAUDE_PROJECTS_DIR`
(Standard `~/.claude/projects`), `NIRO_CLAUDE_MEMORY_DIR`, `NIRO_SAMMLER_ABGLEICH_CMD`, `NIRO_SAMMLER_ABGLEICH_TIMEOUT`
(Sekunden); für `studio_abgleich.sh`: `NIRO_SAMMLER_CMD` (Ersatz für den Sammler-Aufruf).

## Tests

```bash
python3 tools/tagesbericht/sammler_test.py     # alle *_test.py in diesem Ordner, Exit 0 = bestanden
sh tools/studio_abgleich_test.sh               # Tests 10/11: --berichte und Sammler-Aufruf
```
```

- [ ] **Step 4: Alle Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py 2>&1 | tail -3 && sh tools/studio_abgleich_test.sh 2>&1 | tail -2`
Expected: `OK` und „Alle Tests bestanden.".

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add .claude/settings.json SETUP.md tools/tagesbericht/README.md && git -c core.quotepath=false diff --cached --name-only && git commit -q -m "feat(studio): SessionStart-Hook für den Sammler; SETUP Mac-Name; README Tagesbericht

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Funktion „Tagesbericht" — Workflow, CLAUDE.md, Gedächtnis

**Files:**
- Create: `tools/tagesbericht/WORKFLOW-Tagesbericht.md`
- Modify: `CLAUDE.md` (Funktionstabelle Zeile 57 ff. und NAS-Absatz Zeilen 29–33)
- Create: `~/.claude/projects/-Users-jansantos-NIRO-Studio/memory/tagesbericht-funktion.md` (liegt über die Verknüpfung auf dem NAS) und eine Zeile in `MEMORY.md` daneben

**Interfaces:**
- Consumes: Sammler-CLI und Format (Aufgabe 7/8), `sh tools/studio_abgleich.sh --berichte` (Aufgabe 6).
- Produces: die Anleitung, nach der Claude beim Trigger den `Tagesbericht.md` schreibt; Trigger-Zeile; Gedächtnisnotiz.

- [ ] **Step 1: Workflow-Datei schreiben**

`tools/tagesbericht/WORKFLOW-Tagesbericht.md`:

```markdown
# Funktion „Tagesbericht" — Haupt-Check beider Studio-Macs

Trigger im Chat: „Tagesbericht" (heute) · „Tagesbericht: gestern" · „Tagesbericht: <JJJJ-MM-TT>".
Spec: `docs/superpowers/specs/2026-09-17-tagesbericht-design.md` · Sammler: `tools/tagesbericht/README.md`.

Der Bericht fasst zusammen, was an einem Tag auf beiden Macs gemacht wurde, welche Werkzeug-Änderungen entstanden sind,
was davon auf `main` gehört, wo es hakte und was offen bleibt. **Er empfiehlt nur.** Geschrieben wird ausschließlich
unter `berichte/`; keine Commits, Merges, Pushes, keine Änderungen an Chargen oder Werkzeug. Merges führt Claude nur in
einer eigenen Session auf ausdrücklichen Auftrag aus.

## Ablauf

1. **Tag bestimmen:** heute, gestern oder das Datum aus dem Trigger. Im Hauptordner des Repos arbeiten (erste Zeile von
   `git worktree list`).
2. **Sammeln und abgleichen:**

   ```bash
   git fetch -q
   python3 tools/tagesbericht/sammler.py --tag <JJJJ-MM-TT>
   ```

   Der Sammler schreibt den Tagesstand dieses Macs und spiegelt `berichte/` (holt die Datei des anderen Macs). Schlägt
   `git fetch` fehl, nur melden. Fehlt das NAS (Meldung „NAS nicht verbunden"), steht das im Bericht unter „Stand".
3. **Lesen:** alle `berichte/<Tag>/*.md` außer `Tagesbericht.md` (eine Datei je Mac); den jüngsten früheren
   `berichte/<Tag'>/Tagesbericht.md` für den Übertrag; bei Bedarf `berichte/<Tag>/<Mac>.patch` (Inhalt unversionierter
   Änderungen des jeweiligen Macs), Protokolle und Specs. Bekannte Macs = alle `<Mac>.md`-Namen unter `berichte/*/`;
   fehlt ein Mac für den Tag, seinen jüngsten vorhandenen Tag nennen.
4. **`berichte/<Tag>/Tagesbericht.md` schreiben** nach der Vorlage unten. Existiert schon einer, wird er ersetzt; die
   Zeile unter dem Titel nennt dann „ersetzt Fassung von <HH:MM>".
5. **Abgleichen und melden:** `sh tools/studio_abgleich.sh --berichte`; im Chat die Kurzfassung (eine Bildschirmseite:
   Stand, Empfehlungen, Probleme, Offen) und der Pfad der Datei.

## Vorlage `Tagesbericht.md`

    # Tagesbericht <TT.MM.JJJJ>
    Erstellt <JJJJ-MM-TT HH:MM> auf <Mac> · Quellen: <Mac1>.md (Stand HH:MM), <Mac2>.md (Stand HH:MM) · Vorbericht: <Datum oder „keiner“>

    ## Stand
    Je Mac: Zeit des Sammler-Laufs, Sitzungen, Commits. Fehlt ein Mac: „<Mac>: kein Tagesstand für <Tag>, letzter <Datum>“ ganz oben.

    ## Gemacht
    Je Mac, gruppiert nach Chargen und Werkzeug; ein bis zwei Sätze je Sitzung mit Quelle (Sitzungs-Kennung + Zeit oder Commit).
    Die Sammelzeile des Tagesstands („… — in N Chargen“) bleibt eine Zeile.

    ## Neue Funktionen und Werkzeug-Änderungen
    Je Werkzeug (autocut, motion, transcribe, resolve, photo, musik, sfx, studio): auf main gekommen · auf Branches · unversioniert (mit Mac).

    ## Empfehlung für main
    Nummeriert; je Punkt Was, Warum, Befehl, Mac. Nichts wird ausgeführt.
    - ungepushte Branch-Commits → Merge- oder Fast-Forward-Befehl
    - unversionierte Änderungen → Einschätzung „fertig / halbfertig / Wegwerf“ (Quelle: Schlussberichte, Patch) und Vorschlag Commit oder Verwerfen
    - überholte Branches (0 vor, viele hinter) → Löschbefehl
    - Punkte des anderen Macs als Auftrag „auf <Mac>: …“

    ## Probleme und Auffälligkeiten
    Gehäufte Tool-Fehler, abgebrochene Sitzungen, Sitzungen ohne Schlussbericht, offene Fragen aus Schlussberichten, Hinweise des Sammlers.

    ## Offen und Übertrag
    Offene Punkte des Tages; Punkte des Vorberichts mit Alter („seit 3 Tagen“); Erledigtes einmal als erledigt nennen, dann weg.

    ## Chargen-Stand
    Berührte Chargen, Lieferungen (neue Dateien unter Ergebnisse/), fehlende Protokoll-Einträge.

## Regeln

- Jede Aussage nennt Mac und Sitzung (Kennung, Zeit) oder Commit (Hash). Unsicheres steht als „vermutlich …".
- Nichts aus dem Gedächtnis ergänzen, was nicht in den Quellen des Tages steht; Tagesstände verdichten, nicht wiederholen.
- Deutsch, Stil der Protokolle. Kurzfassung im Chat höchstens eine Bildschirmseite.
- Keine Commits, Merges, Pushes, keine Änderungen außerhalb von `berichte/` — auch nicht „nur schnell" für einen
  offensichtlichen Punkt. Der User entscheidet und beauftragt in einer eigenen Session.
```

- [ ] **Step 2: CLAUDE.md ergänzen — vorher Zustand prüfen**

```bash
cd "/Users/jansantos/NIRO Studio" && git status --short CLAUDE.md && git diff --stat CLAUDE.md
```

Ist die Ausgabe leer: normal weiter (Bearbeiten und Commit in Step 4). Zeigt sie ` M CLAUDE.md` (ungesicherte Änderung einer anderen Session, am 17.09. der Absatz „Medien liegen auf dem NAS, nicht im Abgleich"): trotzdem bearbeiten — mit Edit (Zeichenkettenersetzung), nie mit Write —, aber **CLAUDE.md nicht committen**; im Abschlussbericht der Aufgabe melden: „CLAUDE.md enthält die Trigger-Zeile und den Berichte-Satz, dazu eine fremde ungesicherte Änderung (Absatz …); Commit von CLAUDE.md erst nach Freigabe des Users, damit die fremde Änderung nicht mit hineinrutscht."

Änderung 1 — in der Funktionstabelle nach der Zeile, die mit `| „Resolve: <Aufgabe>"` beginnt, anfügen:

```markdown
| „Tagesbericht" / „Tagesbericht: gestern" / „Tagesbericht: <JJJJ-MM-TT>" | Tagesstände beider Macs (Git, Chargen, Sitzungen, Gedächtnis) → `berichte/<Tag>/Tagesbericht.md`: Gemacht, neue Funktionen, Empfehlung für main (nur Empfehlung, kein Merge), Probleme, Offenes | `tools/tagesbericht/WORKFLOW-Tagesbericht.md` |
```

Änderung 2 — im Absatz **NAS-Spiegel statt GitHub** nach dem Satz `Chargen-Daten nur im Hauptordner des Repos lesen und schreiben (erste Zeile von \`git worktree list\`).` anfügen (gleicher Absatz):

```markdown
Ebenso gespiegelt wird `berichte/` (Tagesstand je Mac aus `tools/tagesbericht/sammler.py`, geschrieben vom SessionStart-Hook
und vom Abgleich, plus `Tagesbericht.md` der Funktion „Tagesbericht"); Mac-Name über `git config niro.mac`.
```

- [ ] **Step 3: Gedächtnisnotiz schreiben**

Datei `/Users/jansantos/.claude/projects/-Users-jansantos-NIRO-Studio/memory/tagesbericht-funktion.md`:

```markdown
---
name: tagesbericht-funktion
description: "Funktion „Tagesbericht“ seit 17.09.26: Sammler je Mac (tools/tagesbericht/sammler.py, SessionStart-Hook in .claude/settings.json) schreibt berichte/<Tag>/<Mac>.md + .patch übers NAS; Haupt-Check nur per Trigger und nur als Empfehlung (kein Merge); Mac-Namen Studio-Mac/MacBook via git config niro.mac"
metadata:
  type: project
---

Idee des Users 17.09.2026: „Tagesbericht von beiden Studio-Versionen Mac1 und Mac2 … was heute gemacht wurde, welche
neuen Funktionen dazukamen und was sinnvoll ist, in den Main zu packen. Auch wo es vielleicht Probleme gab."
Spec `docs/superpowers/specs/2026-09-17-tagesbericht-design.md`, Plan `docs/superpowers/plans/2026-09-17-tagesbericht.md`.

**Entscheidungen (User):** nur per Trigger („Tagesbericht", „Tagesbericht: gestern", „Tagesbericht: <JJJJ-MM-TT>"),
kein Zeitplan; der Bericht **empfiehlt nur** (Kandidaten + Befehle), Merges/Commits/Pushes nur in eigener Session auf
Auftrag; Sitzungsverläufe werden ausgewertet (Titel, Aufträge, Schlussbericht, Tool-Fehler, Dateien); Sicherungs-Patch
der unversionierten Werkzeug-Änderungen und Hook-Hinweis bei fehlendem Tagesbericht sind drin.

**Aufbau:** `tools/tagesbericht/` (umgebung, git_stand, chargen_stand, sitzungen_stand, gedaechtnis_stand, bericht,
sammler.py; Tests `sammler_test.py`). `berichte/` gitignoriert, gespiegelt über `NIRO Studio/berichte/` auf dem NAS
(`studio_abgleich.sh --berichte`; jeder Abgleich ruft vorher den Sammler). Anleitung des Haupt-Checks:
`tools/tagesbericht/WORKFLOW-Tagesbericht.md`.

**Why:** Werkzeug-Sessions ohne Commit hinterlassen sonst keine Spur (17.09.: 65 unversionierte Dateien aus drei
Sessions), der andere Mac ist von hier unsichtbar, und Ungepushtes ging beim Übergabeweg GitHub schon verloren
([[studio-auf-nas-bewertung]], [[zweit-macbook-motion-quellen]]).

**How to apply:** Beim Trigger die Workflow-Datei lesen und folgen; nur unter `berichte/` schreiben. Auf einem neuen
Mac einmal `git config niro.mac "<Name>"` setzen (SETUP.md). Der Hook läuft bei jedem Sitzungsstart (unter 5 s); meldet
er „Tagesbericht für … fehlt", den User kurz darauf hinweisen, nicht ungefragt den Bericht erstellen.
```

In `MEMORY.md` (gleicher Ordner) am Ende anfügen:

```markdown
- [Tagesbericht-Funktion](tagesbericht-funktion.md) — seit 17.09.26: Sammler je Mac (SessionStart-Hook) → berichte/<Tag>/<Mac>.md übers NAS; „Tagesbericht[: gestern|<Datum>]" schreibt Tagesbericht.md, nur Empfehlung, kein Merge; git config niro.mac
```

- [ ] **Step 4: Commit (ohne CLAUDE.md, falls fremd geändert)**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/tagesbericht/WORKFLOW-Tagesbericht.md
```

War CLAUDE.md in Step 2 sauber (keine Ausgabe von `git status --short CLAUDE.md`): zusätzlich `git add CLAUDE.md`. War sie
fremd geändert: CLAUDE.md **nicht** stagen. Dann:

```bash
cd "/Users/jansantos/NIRO Studio" && git -c core.quotepath=false diff --cached --name-only && git commit -q -m "docs(studio): Funktion „Tagesbericht“ — Workflow für den Haupt-Check, Trigger in CLAUDE.md

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

(Gedächtnis liegt nicht im Repo — nichts zu committen.)

---

### Task 10: Abnahme — echter Lauf, erster Tagesbericht, Push

Diese Aufgabe führt die Hauptsession aus (kein Subagent): Der erste Tagesbericht geht an den User.

**Files:**
- Keine neuen Dateien im Repo; `berichte/2026-09-17/` lokal und auf dem NAS.

- [ ] **Step 1: Alle Tests**

```bash
cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler_test.py 2>&1 | tail -3 && sh tools/studio_abgleich_test.sh 2>&1 | tail -2
```

Expected: `OK`, „Alle Tests bestanden.".

- [ ] **Step 2: Mac-Name setzen und echter Lauf mit Abgleich**

```bash
cd "/Users/jansantos/NIRO Studio" && git config niro.mac "Studio-Mac" && time python3 tools/tagesbericht/sammler.py && ls -la berichte/2026-09-17/ && sed -n '1,12p' berichte/2026-09-17/Studio-Mac.md && ls "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio/berichte/2026-09-17/"
```

Expected: `Studio-Mac.md`, `Studio-Mac.patch`, gestern-Datei; Stand-Zeile mit Sitzungen ≥ 7 und Commits ≥ 10 (Prototyp
17.09.: 7 Sitzungen, 10 Commits auf main + Spec-/Plan-Commits); dieselben Dateien auf dem NAS; Laufzeit unter 10 s.
Abweichungen nach unten (weniger Sitzungen als der Prototyp) → Sitzungsordner mit `ls ~/.claude/projects/ | grep NIRO-Studio`
vergleichen und melden.

- [ ] **Step 3: Hook-Ausgabe prüfen**

```bash
cd "/Users/jansantos/NIRO Studio" && python3 tools/tagesbericht/sammler.py --hook; echo "rc=$?"
```

Expected: eine Zeile „Tagesbericht für 16.09.2026 fehlt — Trigger: „Tagesbericht: 2026-09-16"." (16.09. hatte 26 Commits) und `rc=0`.

- [ ] **Step 4: Push auf main**

Regel (Gedächtnis `github-push-referenzen-oeffentlich`): vorher `git fetch`, Fast-Forward, gestagte Dateien prüfen.

```bash
cd "/Users/jansantos/NIRO Studio" && git fetch -q && git status -sb | head -1 && git log --oneline origin/main..main && git -c core.quotepath=false diff --name-only origin/main..main | grep -Ev '^(tools/tagesbericht/|tools/studio_abgleich|\.claude/settings\.json|\.gitignore|SETUP\.md|CLAUDE\.md|docs/superpowers/)' ; echo "--- fremde Pfade oben = leer erwartet ---"
```

Expected: nur eigene Pfade. Dann `git push -q origin main` und `git log -1 --format='%h %s' origin/main`.

- [ ] **Step 5: Erster Tagesbericht**

In der Hauptsession den Trigger „Tagesbericht: 2026-09-17" ausführen — nach `tools/tagesbericht/WORKFLOW-Tagesbericht.md`.
Ergebnis: `berichte/2026-09-17/Tagesbericht.md` lokal und auf dem NAS; Kurzfassung im Chat. Darin muss stehen: MacBook
hat noch keinen Tagesstand (Umstieg auf dem MacBook steht aus) und die offenen Punkte dieser Session.

- [ ] **Step 6: Abschlussmeldung an den User**

Kurz: was gebaut wurde, Testlage, Pfad des ersten Tagesberichts, offene Punkte: (a) auf dem MacBook `git pull` (Hook
läuft danach von selbst) und `git config niro.mac "MacBook"`; (b) CLAUDE.md-Commit, falls in Aufgabe 9 wegen fremder
Änderung ausgesetzt; (c) Verhalten des Hooks in der Desktop-App beobachten (SessionStart bei `resume`).

---

## Selbstprüfung des Plans (erledigt beim Schreiben)

- **Spec-Abdeckung:** 1 Ablage → Task 1/6/7 · 2 Sammler (2.1 Task 2, 2.2 Task 3, 2.3 Task 4, 2.4/2.5/2.7 Task 5, 2.6 Task 2, CLI Task 7) · 3 Abgleich → Task 6 · 4 Hook + Hinweis → Task 7/8 · 5 Haupt-Check → Task 9 · Fehlerbehandlung → Tests in Task 2/4/7 · Tests → je Task, Shell Task 6 · Doku → Task 8/9 · Reihenfolge 5 (Abnahme, Push, MacBook) → Task 10.
- **Abweichung vom Spec (aus dem Trockenlauf auf echten Daten 17.09.):** Texte, die mit `<task-notification>`, `<command-name>` oder `<local-command` beginnen, sind keine Aufträge (Systemnachrichten); bei Tool-Fehlern wird eine Zeile „Exit code N“ übersprungen und die nächste genommen; Lieferungen stehen relativ zu `Ergebnisse/`.
- **Abweichung vom Spec:** Die Hinweis-Logik prüft „Sitzungen/Commits > 0" in der Stand-Zeile statt nur „irgendein `<Mac>.md`", damit ein leerer Sonntag keinen Hinweis auslöst (Spec 4 sinngemäß: nur Tage mit Arbeit). Der Patch wird nur für heute geschrieben (der Arbeitsbaum hat keinen Tag).
- **Namen quer durch die Aufgaben:** `tagesgrenzen`, `kuerzen`, `erste_zeile`, `GitStand.commits_gesamt`, `ChargenStand.je_charge_alle/je_charge/sammel/lieferungen`, `Sitzung.schluss_offen/beginn`, `Tagesstand`, `rendern`, `hinweise`, `sicherung`, `--berichte`, `NIRO_SAMMLER_CMD`, `NIRO_SAMMLER_ABGLEICH_CMD`, `NIRO_SAMMLER_ABGLEICH_TIMEOUT` — in Tests und Code gleich geschrieben.
