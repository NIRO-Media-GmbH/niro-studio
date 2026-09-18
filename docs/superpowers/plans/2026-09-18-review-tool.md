# NIRO Review — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lokales Review-Werkzeug „NIRO Review" (neunte Studio-Funktion): Web-Oberfläche im NIRO-CI unter
`http://localhost:4711`, Ablage Kunde → Projekt → Video → V1, V2 … auf dem NAS, Kommentare an Frame oder Bereich,
CLI für Claude (Version ablegen, Kommentare holen, Umsetzung eintragen), LaunchAgent „immer an".

**Architecture:** Reine Python-Standardbibliothek (≥ 3.9) plus ffmpeg/ffprobe. Paket `tools/review/src/niro_review/`
mit sechs Modulen (Ablage, Modell, Medien, Kommentare, Server, LaunchAgent) und einer CLI; die Oberfläche ist eine
statische Seite (HTML/CSS/Vanilla-JS, kein Build), die der Server mitliefert. Alle Daten sind JSON-Dateien im
Review-Ordner auf dem NAS; jede Version ist unveränderlich; lokal gibt es nur einen Medien-Cache.

**Tech Stack:** Python 3.9+ (`http.server.ThreadingHTTPServer`, `plistlib`, `argparse`), ffmpeg 8 (h264_videotoolbox /
libx264), Vanilla JS (`requestVideoFrameCallback`), pytest 9 aus `tools/autocut/venv`.

Spec: `docs/superpowers/specs/2026-09-18-review-tool-design.md`.

## Global Constraints

- Python ≥ 3.9 (Apple-`/usr/bin/python3` ist 3.9.6): `from __future__ import annotations` in jedem Modul, kein
  `match`, keine `X | Y`-Typen zur Laufzeit, keine Abhängigkeiten außerhalb der Standardbibliothek.
- Tests laufen mit `tools/autocut/venv/bin/python -m pytest tools/review/tests -q` (Python 3.12, pytest 9.1.1).
- Wurzeln nur über `niro_review.ablage` (Umgebung: `NIRO_STUDIO_REPO`, `NIRO_STUDIO_NAS`, `NIRO_REVIEW_ROOT`,
  `NIRO_REVIEW_CACHE`); Standard-NAS
  `/Volumes/NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio`, Review-Wurzel
  `<NAS>/review`, Cache `~/Library/Caches/NIRO Review`.
- Alle Ordner- und Titelvergleiche NFC-normalisiert (`unicodedata.normalize("NFC", …)`); Dateien werden atomar
  geschrieben (Temp-Datei `.tmp-*` im selben Ordner + `os.replace`).
- Versionen sind unveränderlich: `video.mp4` einer Version wird nie ersetzt; Entfernen nur in `_papierkorb/`.
- Server nur auf `127.0.0.1`, Port 4711, kein Login; Medien mit Range (206/416/HEAD), 1-MiB-Blöcke; `/api/*` ohne
  NAS → 503 (außer `/api/zustand`).
- Exit-Codes der CLI: 0 ok · 1 Eingabefehler · 2 Voraussetzung fehlt (NAS, ffmpeg); `kommentare`: 0 neue, 1 keine
  neuen, 2 NAS fehlt.
- CI (aus `tools/motion/src/clients/niro/brand.json`): Grund `#1A211C`, Flächen `#232B26`/`#2C352F`, Linien `#3A453E`,
  Text `#F4F6F2`, gedämpft `#9AA59D`, Grün `#A1D334`, Blau `#7DD1FF`, Radius 12 px, Überschriften Meutas, Text Roboto.
- Alle Texte der Oberfläche und der CLI auf Deutsch; Kommentar-Status-Werte im JSON: `offen`, `umgesetzt`,
  `rueckfrage`, `erledigt`; Video-Zustände: `review-offen`, `bei-claude`, `freigegeben`, `leer`.
- Commits: nur Dateien unter `tools/review/`, `docs/`, `CLAUDE.md`, `SETUP.md` hinzufügen — `git status` zeigt
  fremde, unkommittierte Änderungen (Motion, WORKFLOW-AutoCut.md, WORKFLOW-Resolve.md); die nie mit-committen.
  Commit-Trailer: `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## Dateistruktur

    tools/review/
    ├── review.py                       Einstieg: src/ in sys.path, niro_review.cli.main()
    ├── src/niro_review/__init__.py     WERKZEUG_VERSION = "1.0"
    ├── src/niro_review/ablage.py       Wurzeln, Ziel aus Chargenpfad, NFC-Nachschlagen, atomares Schreiben, Pfadsicherheit, mac_name, jetzt
    ├── src/niro_review/modell.py       video.json / version.json, Versionsnummern, Zustand, Zähler, Titel aus Dateiname, Sortierung, Index, Detail
    ├── src/niro_review/medien.py       ffprobe → Medieninfo, Entscheidung kopie/umkodieren/alpha, ffmpeg-Befehle, Vorschaubild, Timecode
    ├── src/niro_review/kommentare.py   kommentare.json: anlegen/ändern/löschen/antworten, Umsetzung (alles-oder-nichts), Sortierung, ist_neu, Export md/json
    ├── src/niro_review/server.py       ReviewServer + Handler: UI, /api/*, /media/* mit Range und Cache-Füllung
    ├── src/niro_review/launchagent.py  Plist, installieren, deinstallieren
    ├── src/niro_review/cli.py          Unterbefehle hinzufuegen, kommentare, umsetzung, antworten, status, entfernen, server, installieren, deinstallieren, oeffnen
    ├── ui/index.html, ui/style.css, ui/app.js, ui/niro-symbol.svg, ui/fonts/Meutas-{Regular,Medium,SemiBold,Bold}.otf
    ├── tests/conftest.py + test_ablage.py, test_modell.py, test_medien.py, test_kommentare.py, test_server.py, test_launchagent.py, test_cli.py
    ├── WORKFLOW-Review.md              Ablauf für Claude
    └── README.md                       Einrichtung, Bedienung, Tastenkürzel

Code-Blöcke dieses Plans tragen `file=<Pfad>`; ein Block ersetzt die Datei vollständig (mehrere Blöcke derselben Datei
werden in Reihenfolge aneinandergehängt).

---

### Task 1: Grundgerüst und Ablage

**Files:**
- Create: `tools/review/review.py`, `tools/review/src/niro_review/__init__.py`, `tools/review/src/niro_review/ablage.py`
- Test: `tools/review/tests/conftest.py`, `tools/review/tests/test_ablage.py`

**Interfaces:**
- Produces: `ReviewFehler(text, code=1)` mit `.code`; `nfc(s)`; `repo_wurzel()`, `nas_wurzel()`, `review_wurzel()`,
  `cache_wurzel()`, `nas_verbunden()` → bool; `Ziel(kunde, projekt, charge)` + `ziel_aufloesen(angabe, repo=None)`;
  `finde_kind(eltern, name)` → Path; `atomar_schreiben(pfad, text)`, `json_lesen(pfad, standard=None)`,
  `json_schreiben(pfad, daten)`; `sicherer_pfad(wurzel, rel)` → Optional[Path]; `name_ok(s)` → bool;
  `mac_name()`, `jetzt()` (ISO-Sekunden lokal), `heute()` („JJJJ-MM-TT"), `datum_de(iso)` („TT.MM.JJJJ").

- [ ] **Step 1: Tests schreiben**

```python file=tools/review/tests/conftest.py
"""Testaufbau: Paket aus src/ importieren, Wurzeln auf Temp-Ordner, Testvideos per ffmpeg."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def wurzeln(tmp_path, monkeypatch):
    """Temp-Repo (mit projects/Kunde/Projekt/Charge), Review-Wurzel, Cache — alles über die Umgebung."""
    repo = tmp_path / "repo"
    charge = repo / "projects" / "Dold" / "Recruiting" / "2026-07 Dreh 27-28.07"
    charge.mkdir(parents=True)
    nas = tmp_path / "nas" / "NIRO Studio"
    nas.mkdir(parents=True)
    cache = tmp_path / "cache"
    monkeypatch.setenv("NIRO_STUDIO_REPO", str(repo))
    monkeypatch.setenv("NIRO_STUDIO_NAS", str(nas))
    monkeypatch.delenv("NIRO_REVIEW_ROOT", raising=False)
    monkeypatch.setenv("NIRO_REVIEW_CACHE", str(cache))
    return {"repo": repo, "charge": charge, "charge_rel": "projects/Dold/Recruiting/2026-07 Dreh 27-28.07",
            "nas": nas, "review": nas / "review", "cache": cache}


def _ffmpeg_da() -> bool:
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def _testvideo(ziel: Path, codec: list[str], dauer: float = 2.0) -> Path:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=size=320x180:rate=25:duration={dauer}",
                    "-f", "lavfi", "-i", f"sine=frequency=440:duration={dauer}", *codec, "-shortest", str(ziel)], check=True)
    return ziel


@pytest.fixture(scope="session")
def testvideo_h264(tmp_path_factory) -> Path:
    if not _ffmpeg_da():
        pytest.skip("ffmpeg fehlt")
    return _testvideo(tmp_path_factory.mktemp("medien") / "Dold 02 Fokus Bagger und Kran – Entwurf v1.mp4",
                      ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"])


@pytest.fixture(scope="session")
def testvideo_mpeg4(tmp_path_factory) -> Path:
    if not _ffmpeg_da():
        pytest.skip("ffmpeg fehlt")
    return _testvideo(tmp_path_factory.mktemp("medien") / "Taxodia-Weg Messe V2.mov",
                      ["-c:v", "mpeg4", "-q:v", "3", "-c:a", "pcm_s16le"])
```

```python file=tools/review/tests/test_ablage.py
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

from niro_review import ablage
from niro_review.ablage import ReviewFehler


def test_nfc_normalisiert():
    nfd = unicodedata.normalize("NFD", "Förch")
    assert ablage.nfc(nfd) == "Förch" and ablage.nfc(nfd) != nfd


def test_wurzeln_aus_umgebung(wurzeln):
    assert ablage.repo_wurzel() == wurzeln["repo"]
    assert ablage.review_wurzel() == wurzeln["review"]
    assert ablage.cache_wurzel() == wurzeln["cache"]
    assert ablage.nas_verbunden() is True


def test_review_root_direkt(wurzeln, monkeypatch, tmp_path):
    monkeypatch.setenv("NIRO_REVIEW_ROOT", str(tmp_path / "anders" / "review"))
    assert ablage.review_wurzel() == tmp_path / "anders" / "review"
    assert ablage.nas_verbunden() is False  # Elternordner fehlt


def test_ziel_relativ_mit_und_ohne_projects(wurzeln):
    z = ablage.ziel_aufloesen("projects/Dold/Recruiting/2026-07 Dreh 27-28.07")
    assert (z.kunde, z.projekt, z.charge) == ("Dold", "Recruiting", "projects/Dold/Recruiting/2026-07 Dreh 27-28.07")
    z2 = ablage.ziel_aufloesen("Dold/Recruiting/2026-07 Dreh 27-28.07/")
    assert z2 == z


def test_ziel_absolut_und_nfd(wurzeln):
    nfd = unicodedata.normalize("NFD", "Förch")
    charge = wurzeln["repo"] / "projects" / nfd / "Recruiting" / "2026-06 Dreh"
    charge.mkdir(parents=True)
    z = ablage.ziel_aufloesen(str(charge))
    assert z.kunde == "Förch" and z.charge == "projects/Förch/Recruiting/2026-06 Dreh"


def test_ziel_kunde_projekt(wurzeln):
    z = ablage.ziel_aufloesen("Dold/Recruiting")
    assert (z.kunde, z.projekt, z.charge) == ("Dold", "Recruiting", None)


def test_ziel_fehler(wurzeln, tmp_path):
    with pytest.raises(ReviewFehler):
        ablage.ziel_aufloesen("Dold")
    with pytest.raises(ReviewFehler):
        ablage.ziel_aufloesen(str(tmp_path / "woanders" / "a" / "b" / "c"))


def test_finde_kind_nfd(tmp_path):
    nfd = unicodedata.normalize("NFD", "Förch")
    (tmp_path / nfd).mkdir()
    gefunden = ablage.finde_kind(tmp_path, "Förch")
    assert gefunden.is_dir() and gefunden.name == nfd
    assert ablage.finde_kind(tmp_path, "Neu") == tmp_path / "Neu"


def test_json_atomar(tmp_path):
    p = tmp_path / "a" / "b.json"
    ablage.json_schreiben(p, {"x": "ä"})
    assert json.loads(p.read_text(encoding="utf-8")) == {"x": "ä"}
    assert ablage.json_lesen(p) == {"x": "ä"}
    assert ablage.json_lesen(tmp_path / "fehlt.json", {}) == {}
    assert not list((tmp_path / "a").glob(".tmp-*"))


def test_sicherer_pfad(tmp_path):
    (tmp_path / "Dold" / "Recruiting").mkdir(parents=True)
    (tmp_path / "Dold" / "Recruiting" / "video.mp4").write_bytes(b"x")
    assert ablage.sicherer_pfad(tmp_path, "Dold/Recruiting/video.mp4") == tmp_path / "Dold" / "Recruiting" / "video.mp4"
    assert ablage.sicherer_pfad(tmp_path, "Dold/../Recruiting") is None
    assert ablage.sicherer_pfad(tmp_path, "/etc/passwd") is None
    assert ablage.sicherer_pfad(tmp_path, "") is None
    assert ablage.sicherer_pfad(tmp_path, "Dold/./x") is None
    assert ablage.sicherer_pfad(tmp_path, "Dold/Neu/fehlt.mp4") == tmp_path / "Dold" / "Neu" / "fehlt.mp4"


def test_name_ok():
    assert ablage.name_ok("Dold 02 Fokus (David)")
    assert not ablage.name_ok("a/b") and not ablage.name_ok("..") and not ablage.name_ok(".versteckt") and not ablage.name_ok("")


def test_zeit_helfer():
    assert len(ablage.jetzt()) == 19 and ablage.jetzt()[10] == "T"
    assert ablage.datum_de("2026-09-18T14:02:11") == "18.09.2026"
    assert len(ablage.heute()) == 10
```

- [ ] **Step 2: Tests laufen lassen — erwartet ImportError**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests/test_ablage.py -q`
Expected: Fehler „No module named niro_review".

- [ ] **Step 3: Implementieren**

```python file=tools/review/review.py
#!/usr/bin/env python3
"""NIRO Review — Einstieg. Aufruf: python3 tools/review/review.py <Befehl> …  (Python ≥ 3.9, ffmpeg/ffprobe).

Spec: docs/superpowers/specs/2026-09-18-review-tool-design.md · Ablauf: tools/review/WORKFLOW-Review.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from niro_review.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
```

```python file=tools/review/src/niro_review/__init__.py
"""NIRO Review — lokales Review-Werkzeug (Spec docs/superpowers/specs/2026-09-18-review-tool-design.md)."""
WERKZEUG_VERSION = "1.0"
```

```python file=tools/review/src/niro_review/ablage.py
"""Ablage: Wurzeln (Repo, NAS, Review, Cache), Chargen-Pfad → Kunde/Projekt, NFC-sicheres Nachschlagen, atomares
Schreiben, Pfadsicherheit, Mac-Name, Zeitstempel. Spec „Ablage"."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

NAS_STANDARD = "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio"


class ReviewFehler(Exception):
    """Fehler mit Exit-Code: 1 = Eingabe, 2 = Voraussetzung fehlt (NAS, ffmpeg)."""

    def __init__(self, text: str, code: int = 1):
        super().__init__(text)
        self.code = code


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", str(s))


def repo_wurzel() -> Path:
    env = os.environ.get("NIRO_STUDIO_REPO")
    return Path(env) if env else Path(__file__).resolve().parents[4]


def nas_wurzel() -> Path:
    return Path(os.environ.get("NIRO_STUDIO_NAS") or NAS_STANDARD)


def review_wurzel() -> Path:
    env = os.environ.get("NIRO_REVIEW_ROOT")
    return Path(env) if env else nas_wurzel() / "review"


def nas_verbunden() -> bool:
    return review_wurzel().parent.is_dir()


def cache_wurzel() -> Path:
    env = os.environ.get("NIRO_REVIEW_CACHE")
    return Path(env) if env else Path.home() / "Library" / "Caches" / "NIRO Review"


@dataclass(frozen=True)
class Ziel:
    kunde: str
    projekt: str
    charge: Optional[str]  # „projects/<Kunde>/<Projekt>/<Charge>“ oder None (nur Kunde/Projekt)


def ziel_aufloesen(angabe: str, repo: Optional[Path] = None) -> Ziel:
    """Chargenpfad (relativ ab Studio-Wurzel, mit oder ohne „projects/“, oder absolut) oder „<Kunde>/<Projekt>“."""
    repo = repo or repo_wurzel()
    text = nfc(angabe).strip().rstrip("/")
    p = Path(text)
    if p.is_absolute():
        try:
            rel = p.resolve().relative_to((repo / "projects").resolve())
        except ValueError:
            raise ReviewFehler(f"„{angabe}“ liegt nicht unter {repo / 'projects'}.")
        teile = [nfc(t) for t in rel.parts]
    else:
        teile = [nfc(t) for t in text.split("/") if t]
        if teile and teile[0] == "projects":
            teile = teile[1:]
    if len(teile) == 2:
        return Ziel(teile[0], teile[1], None)
    if len(teile) == 3:
        return Ziel(teile[0], teile[1], "projects/" + "/".join(teile))
    raise ReviewFehler(f"„{angabe}“: erwartet projects/<Kunde>/<Projekt>/<Charge> oder <Kunde>/<Projekt>.")


def finde_kind(eltern: Path, name: str) -> Path:
    """Vorhandenes Kind (Ordner oder Datei) unabhängig von NFC/NFD finden, sonst NFC-Pfad (nicht angelegt)."""
    ziel = nfc(name)
    try:
        for kind in eltern.iterdir():
            if nfc(kind.name) == ziel:
                return kind
    except (FileNotFoundError, NotADirectoryError):
        pass
    return eltern / ziel


def atomar_schreiben(pfad: Path, text: str) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(pfad.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, pfad)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def json_lesen(pfad: Path, standard=None):
    try:
        with open(pfad, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, NotADirectoryError):
        return standard
    except json.JSONDecodeError as e:
        raise ReviewFehler(f"{pfad}: kein gültiges JSON ({e}).", 2)


def json_schreiben(pfad: Path, daten) -> None:
    atomar_schreiben(pfad, json.dumps(daten, ensure_ascii=False, indent=1) + "\n")


def name_ok(s: str) -> bool:
    """Ein Ordner- oder Titelsegment: nicht leer, kein Trenner, nicht „.“/„..“, nicht versteckt."""
    s = nfc(s) if s is not None else ""
    return bool(s) and "/" not in s and "\\" not in s and s not in (".", "..") and not s.startswith(".")


def sicherer_pfad(wurzel: Path, rel: str) -> Optional[Path]:
    """Relativer Pfad (schon URL-dekodiert) unter wurzel, NFD-tolerant — None bei „..“, „.“, absolut oder leer."""
    rel = nfc(rel or "")
    if not rel or rel.startswith("/") or "\\" in rel:
        return None
    teile = [t for t in rel.split("/") if t]
    if not teile or any(t in ("..", ".") for t in teile):
        return None
    ziel = wurzel
    for t in teile:
        ziel = finde_kind(ziel, t)
    try:
        ziel.resolve().relative_to(wurzel.resolve())
    except ValueError:
        return None
    return ziel


def mac_name() -> str:
    try:
        out = subprocess.run(["git", "config", "niro.mac"], capture_output=True, text=True, cwd=str(repo_wurzel()))
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except OSError:
        pass
    return platform.node().split(".")[0] or "Mac"


def jetzt() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def heute() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def datum_de(iso: str) -> str:
    return f"{iso[8:10]}.{iso[5:7]}.{iso[0:4]}" if iso and len(iso) >= 10 else "—"
```

- [ ] **Step 4: Tests grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests/test_ablage.py -q`
Expected: alle bestanden.

- [ ] **Step 5: Commit**

```bash
git add tools/review/review.py tools/review/src/niro_review/__init__.py tools/review/src/niro_review/ablage.py tools/review/tests/conftest.py tools/review/tests/test_ablage.py
git commit -m "feat(review): Grundgerüst und Ablage (Wurzeln, Ziel aus Chargenpfad, NFC, atomares Schreiben)"
```

---

### Task 2: Datenmodell (video.json, version.json, Versionen, Zustände, Index)

**Files:**
- Create: `tools/review/src/niro_review/modell.py`
- Test: `tools/review/tests/test_modell.py`

**Interfaces:**
- Consumes: `ablage.finde_kind`, `json_lesen`, `json_schreiben`, `jetzt`, `nfc`, `review_wurzel`, `name_ok`.
- Produces: `titel_aus_dateiname(name)`, `sortierung_aus_titel(titel)`, `sortier_schluessel(video)`,
  `video_ordner(kunde, projekt, titel, wurzel=None)`, `video_lesen(ordner)`, `video_anlegen(ordner, kunde, projekt,
  titel, charge, sortierung=None)`, `video_schreiben(ordner, daten)`, `versionsnummern(ordner)`, `naechste_version(ordner)`,
  `version_ordner(ordner, nr)`, `version_lesen(ordner, nr)`, `version_schreiben(ordner, nr, daten)`, `zustand(video,
  neueste)`, `zaehler(kommentare, geholt_am)`, `index_bauen(wurzel)`, `video_detail(ordner)`, `KOMMENTARE_LEER()`.
  Kommentar-Rohdaten liest das Modell nur als JSON (`kommentare.json`), die Regeln liegen in Task 4.

- [ ] **Step 1: Tests schreiben**

```python file=tools/review/tests/test_modell.py
from __future__ import annotations

import unicodedata

import pytest

from niro_review import modell
from niro_review.ablage import json_schreiben


@pytest.mark.parametrize("name,titel", [
    ("Dold 02 Fokus Bagger und Kran – Entwurf v1.mp4", "Dold 02 Fokus Bagger und Kran"),
    ("Dold 12 Fokus Staplerfahrer (David, Sebastian) – Entwurf v1 (Claude 2026-09-17).mp4", "Dold 12 Fokus Staplerfahrer (David, Sebastian)"),
    ("03_Viele Sprachen, ein Team_V6.mp4", "03_Viele Sprachen, ein Team"),
    ("Taxodia-Weg Messe V2.mov", "Taxodia-Weg Messe"),
    ("Craiss 01 Testimonial - v3.mp4", "Craiss 01 Testimonial"),
    ("Video ohne Version.mp4", "Video ohne Version"),
    ("Version 5 Bericht.mp4", "Version 5 Bericht"),
])
def test_titel_aus_dateiname(name, titel):
    assert modell.titel_aus_dateiname(name) == titel


def test_titel_nfc():
    nfd = unicodedata.normalize("NFD", "Förch Azubi V1.mp4")
    assert modell.titel_aus_dateiname(nfd) == "Förch Azubi"


def test_sortierung():
    assert modell.sortierung_aus_titel("Dold 02 Fokus Bagger") == "02"
    assert modell.sortierung_aus_titel("13 140 Jahre") == "13"
    assert modell.sortierung_aus_titel("Taxodia-Weg Messe") == "Taxodia-Weg Messe"
    videos = [{"titel": "b", "sortierung": "b"}, {"titel": "Dold 10", "sortierung": "10"}, {"titel": "Dold 02", "sortierung": "02"}, {"titel": "A", "sortierung": "A"}]
    assert [v["titel"] for v in sorted(videos, key=modell.sortier_schluessel)] == ["Dold 02", "Dold 10", "A", "b"]


def test_video_und_versionen(tmp_path):
    ordner = modell.video_ordner("Dold", "Recruiting", "Dold 02 Fokus", tmp_path)
    assert ordner == tmp_path / "Dold" / "Recruiting" / "Dold 02 Fokus"
    assert modell.video_lesen(ordner) is None
    assert modell.versionsnummern(ordner) == [] and modell.naechste_version(ordner) == 1
    video = modell.video_anlegen(ordner, "Dold", "Recruiting", "Dold 02 Fokus", "projects/Dold/Recruiting/2026-07 Dreh")
    assert video["sortierung"] == "02" and video["freigegeben"] is None and modell.video_lesen(ordner)["titel"] == "Dold 02 Fokus"
    modell.version_schreiben(ordner, 1, {"nr": 1, "abgeschlossen": None})
    (ordner / "V3").mkdir()  # ohne version.json zählt nicht
    modell.version_schreiben(ordner, 2, {"nr": 2, "abgeschlossen": None})
    assert modell.versionsnummern(ordner) == [1, 2] and modell.naechste_version(ordner) == 3
    assert modell.version_lesen(ordner, 2)["nr"] == 2 and modell.version_lesen(ordner, 9) is None


def test_zustand_und_zaehler():
    video = {"freigegeben": None}
    assert modell.zustand(video, None) == "leer"
    assert modell.zustand(video, {"abgeschlossen": None}) == "review-offen"
    assert modell.zustand(video, {"abgeschlossen": {"am": "x", "von": "Jan"}}) == "bei-claude"
    assert modell.zustand({"freigegeben": {"am": "x", "von": "Jan"}}, {"abgeschlossen": None}) == "freigegeben"
    komm = {"kommentare": [
        {"status": "offen", "angelegt": "2026-09-18T10:00:00"},
        {"status": "rueckfrage", "angelegt": "2026-09-18T11:00:00"},
        {"status": "erledigt", "angelegt": "2026-09-18T12:00:00"},
    ]}
    assert modell.zaehler(komm, None) == {"offen": 2, "neu": 3, "gesamt": 3}
    assert modell.zaehler(komm, "2026-09-18T10:30:00") == {"offen": 2, "neu": 2, "gesamt": 3}
    assert modell.zaehler({}, None) == {"offen": 0, "neu": 0, "gesamt": 0}


def test_index_und_detail(tmp_path):
    (tmp_path / "_papierkorb").mkdir()
    o1 = modell.video_ordner("Dold", "Recruiting", "Dold 10 Hobelwerk", tmp_path)
    modell.video_anlegen(o1, "Dold", "Recruiting", "Dold 10 Hobelwerk", "projects/Dold/Recruiting/2026-07 Dreh")
    modell.version_schreiben(o1, 1, {"nr": 1, "angelegt": "2026-09-18T10:00:00", "abgeschlossen": None, "geholt_am": None, "fps": 25.0})
    json_schreiben(o1 / "V1" / "kommentare.json", {"naechste_id": 2, "kommentare": [{"id": "K1", "status": "offen", "angelegt": "2026-09-18T10:05:00"}]})
    o2 = modell.video_ordner("Dold", "Recruiting", "Dold 02 Fokus", tmp_path)
    modell.video_anlegen(o2, "Dold", "Recruiting", "Dold 02 Fokus", "projects/Dold/Recruiting/2026-07 Dreh")
    modell.version_schreiben(o2, 1, {"nr": 1, "angelegt": "2026-09-18T10:00:00", "abgeschlossen": {"am": "x", "von": "Jan"}, "geholt_am": None})
    modell.version_schreiben(o2, 2, {"nr": 2, "angelegt": "2026-09-18T12:00:00", "abgeschlossen": None, "geholt_am": None})
    (tmp_path / "Dold" / "Recruiting" / "Müll").mkdir()  # ohne video.json → ignoriert
    index = modell.index_bauen(tmp_path)
    assert [k["name"] for k in index["kunden"]] == ["Dold"]
    projekt = index["kunden"][0]["projekte"][0]
    assert projekt["name"] == "Recruiting" and [v["titel"] for v in projekt["videos"]] == ["Dold 02 Fokus", "Dold 10 Hobelwerk"]
    v02, v10 = projekt["videos"]
    assert v02["neueste"] == 2 and v02["versionen"] == [1, 2] and v02["zustand"] == "review-offen"
    assert v10["offen"] == 1 and v10["neu"] == 1 and v10["vorschau"] == "/media/Dold/Recruiting/Dold%2010%20Hobelwerk/V1/thumb.jpg"
    assert projekt["offen"] == 1 and projekt["bei_claude"] == 0
    detail = modell.video_detail(o2)
    assert detail["video"]["titel"] == "Dold 02 Fokus" and [v["nr"] for v in detail["versionen"]] == [1, 2]
    assert detail["versionen"][0]["kommentare"] == [] and detail["zustand"] == "review-offen"
    assert modell.index_bauen(tmp_path / "gibtsnicht") == {"kunden": []}
```

- [ ] **Step 2: Tests laufen lassen — erwartet ImportError**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests/test_modell.py -q`
Expected: „cannot import name modell" / ModuleNotFoundError.

- [ ] **Step 3: Implementieren**

```python file=tools/review/src/niro_review/modell.py
"""Datenmodell: video.json / version.json, Versionsnummern, Zustände, Zähler, Titel aus Dateinamen, Sortierung,
Index für die Oberfläche. Kommentar-Regeln liegen in kommentare.py. Spec „Datenmodell"."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from .ablage import finde_kind, jetzt, json_lesen, json_schreiben, nfc, review_wurzel

VERSION_MUSTER = re.compile(r"^V(\d+)$")
_KLAMMER_CLAUDE = re.compile(r"\s*[\(\[]\s*claude[^\)\]]*[\)\]]\s*$", re.IGNORECASE)
_VERSIONSMARKE = re.compile(r"\s*(?:[–\-_]\s*)?(?:entwurf\s*)?v\d+\s*$", re.IGNORECASE)
_NUMMER = re.compile(r"(?<!\d)(\d{1,3})(?!\d)")


def KOMMENTARE_LEER() -> dict:
    return {"naechste_id": 1, "kommentare": []}


def titel_aus_dateiname(name: str) -> str:
    """Endung weg, Versionsmarken am Ende weg („ – Entwurf v1“, „_V6“, „ V2“, „(Claude 2026-09-17)“)."""
    stamm = nfc(Path(name).stem).strip()
    t = stamm
    for _ in range(3):
        t = _KLAMMER_CLAUDE.sub("", t)
        t = _VERSIONSMARKE.sub("", t)
    t = t.strip(" -–_")
    return t or stamm


def sortierung_aus_titel(titel: str) -> str:
    m = _NUMMER.search(nfc(titel)[:40])
    return m.group(1) if m else nfc(titel)


def sortier_schluessel(video: dict):
    s = str(video.get("sortierung") or video.get("titel") or "")
    titel = nfc(str(video.get("titel") or "")).lower()
    if s.isdigit():
        return (0, int(s), titel)
    return (1, 0, nfc(s).lower(), titel)


def video_ordner(kunde: str, projekt: str, titel: str, wurzel: Optional[Path] = None) -> Path:
    w = wurzel if wurzel is not None else review_wurzel()
    return finde_kind(finde_kind(finde_kind(w, kunde), projekt), titel)


def video_lesen(ordner: Path) -> Optional[dict]:
    daten = json_lesen(ordner / "video.json")
    return daten if isinstance(daten, dict) and daten.get("titel") else None


def video_schreiben(ordner: Path, daten: dict) -> None:
    json_schreiben(ordner / "video.json", daten)


def video_anlegen(ordner: Path, kunde: str, projekt: str, titel: str, charge: Optional[str],
                  sortierung: Optional[str] = None) -> dict:
    daten = {"titel": nfc(titel), "kunde": nfc(kunde), "projekt": nfc(projekt), "charge": charge,
             "sortierung": sortierung or sortierung_aus_titel(titel), "angelegt": jetzt(), "freigegeben": None}
    video_schreiben(ordner, daten)
    return daten


def version_ordner(ordner: Path, nr: int) -> Path:
    return ordner / f"V{int(nr)}"


def versionsnummern(ordner: Path) -> list:
    out = []
    try:
        for kind in ordner.iterdir():
            m = VERSION_MUSTER.match(kind.name)
            if m and (kind / "version.json").is_file():
                out.append(int(m.group(1)))
    except (FileNotFoundError, NotADirectoryError):
        pass
    return sorted(out)


def naechste_version(ordner: Path) -> int:
    n = versionsnummern(ordner)
    return (n[-1] + 1) if n else 1


def version_lesen(ordner: Path, nr: int) -> Optional[dict]:
    daten = json_lesen(version_ordner(ordner, nr) / "version.json")
    return daten if isinstance(daten, dict) else None


def version_schreiben(ordner: Path, nr: int, daten: dict) -> None:
    json_schreiben(version_ordner(ordner, nr) / "version.json", daten)


def zustand(video: dict, neueste: Optional[dict]) -> str:
    if video.get("freigegeben"):
        return "freigegeben"
    if neueste is None:
        return "leer"
    if neueste.get("abgeschlossen"):
        return "bei-claude"
    return "review-offen"


def zaehler(kommentare: Optional[dict], geholt_am: Optional[str]) -> dict:
    ks = (kommentare or {}).get("kommentare") or []
    offen = sum(1 for k in ks if k.get("status") in ("offen", "rueckfrage"))
    neu = sum(1 for k in ks if not geholt_am or (k.get("angelegt") or "") > geholt_am)
    return {"offen": offen, "neu": neu, "gesamt": len(ks)}


def _media(kunde: str, projekt: str, ordnername: str, nr: int, datei: str) -> str:
    return "/media/" + "/".join(quote(nfc(t), safe="") for t in (kunde, projekt, ordnername)) + f"/V{nr}/{datei}"


def _kinder(ordner: Path) -> list:
    try:
        return sorted((k for k in ordner.iterdir() if k.is_dir() and not k.name.startswith((".", "_"))),
                      key=lambda p: nfc(p.name).lower())
    except (FileNotFoundError, NotADirectoryError):
        return []


def _video_eintrag(kunde: str, projekt: str, ordner: Path, video: dict) -> dict:
    nrs = versionsnummern(ordner)
    neueste = version_lesen(ordner, nrs[-1]) if nrs else None
    komm = json_lesen(version_ordner(ordner, nrs[-1]) / "kommentare.json", {}) if nrs else {}
    z = zaehler(komm if isinstance(komm, dict) else {}, (neueste or {}).get("geholt_am"))
    return {"titel": video["titel"], "ordner": nfc(ordner.name), "kunde": kunde, "projekt": projekt,
            "sortierung": video.get("sortierung") or video["titel"], "charge": video.get("charge"),
            "zustand": zustand(video, neueste), "versionen": nrs, "neueste": nrs[-1] if nrs else None,
            "angelegt": (neueste or {}).get("angelegt") or video.get("angelegt"),
            "notiz": (neueste or {}).get("notiz") or "", "von": (neueste or {}).get("von"),
            "offen": z["offen"], "neu": z["neu"], "gesamt": z["gesamt"], "freigegeben": video.get("freigegeben"),
            "vorschau": _media(kunde, projekt, ordner.name, nrs[-1], "thumb.jpg") if nrs else None}


def index_bauen(wurzel: Path) -> dict:
    kunden = []
    for k in _kinder(wurzel):
        projekte = []
        for p in _kinder(k):
            videos = []
            for v in _kinder(p):
                video = video_lesen(v)
                if video:
                    videos.append(_video_eintrag(nfc(k.name), nfc(p.name), v, video))
            if not videos:
                continue
            videos.sort(key=sortier_schluessel)
            projekte.append({"name": nfc(p.name), "videos": videos,
                             "offen": sum(v["offen"] for v in videos),
                             "neu": sum(v["neu"] for v in videos),
                             "bei_claude": sum(1 for v in videos if v["zustand"] == "bei-claude"),
                             "review_offen": sum(1 for v in videos if v["zustand"] == "review-offen")})
        if projekte:
            kunden.append({"name": nfc(k.name), "projekte": projekte})
    return {"kunden": kunden}


def video_detail(ordner: Path) -> Optional[dict]:
    video = video_lesen(ordner)
    if not video:
        return None
    versionen = []
    for nr in versionsnummern(ordner):
        v = version_lesen(ordner, nr) or {"nr": nr}
        komm = json_lesen(version_ordner(ordner, nr) / "kommentare.json", None)
        v = dict(v)
        v["nr"] = nr
        v["kommentare"] = (komm or {}).get("kommentare") or [] if isinstance(komm, dict) else []
        v["video_url"] = _media(video["kunde"], video["projekt"], ordner.name, nr, "video.mp4")
        v["vorschau"] = _media(video["kunde"], video["projekt"], ordner.name, nr, "thumb.jpg")
        versionen.append(v)
    neueste = versionen[-1] if versionen else None
    return {"video": video, "ordner": nfc(ordner.name), "versionen": versionen, "zustand": zustand(video, neueste)}
```

- [ ] **Step 4: Tests grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests/test_modell.py -q`
Expected: alle bestanden.

- [ ] **Step 5: Commit**

```bash
git add tools/review/src/niro_review/modell.py tools/review/tests/test_modell.py
git commit -m "feat(review): Datenmodell — Videos, Versionen, Zustände, Index"
```

---

### Task 3: Medien (ffprobe, Kopie oder Umkodierung, Vorschaubild, Timecode)

**Files:**
- Create: `tools/review/src/niro_review/medien.py`
- Test: `tools/review/tests/test_medien.py`

**Interfaces:**
- Consumes: `ablage.ReviewFehler`.
- Produces: `Medieninfo` (dataclass: `dauer_s, fps, frames, breite, hoehe, groesse, container, video_codec, pix_fmt,
  audio_codec, alpha`), `werkzeuge_pruefen()`, `ffprobe(pfad)` → dict, `info_aus_probe(probe, groesse=0)` →
  Medieninfo, `entscheidung(info)` → `"kopie" | "umkodieren" | "alpha"`, `ffmpeg_befehl(quelle, ziel, encoder,
  hat_ton, pixel)` → list[str], `umkodieren(quelle, ziel, info)` → Encoder-Name, `vorschaubild(quelle, ziel,
  dauer_s)`, `timecode(frame, fps)` → „HH:MM:SS:FF" (None → „—"), `frame_aus_timecode(tc, fps)` → int.

- [ ] **Step 1: Tests schreiben**

```python file=tools/review/tests/test_medien.py
from __future__ import annotations

import shutil

import pytest

from niro_review import medien
from niro_review.ablage import ReviewFehler


def probe(codec="h264", pix="yuv420p", audio="aac", container="mov,mp4,m4a,3gp,3g2,mj2", nb_frames="574", dauer="23.040000"):
    streams = [{"codec_type": "video", "codec_name": codec, "pix_fmt": pix, "width": 2160, "height": 3840,
                "r_frame_rate": "25/1", "avg_frame_rate": "25/1", "nb_frames": nb_frames}]
    if audio:
        streams.append({"codec_type": "audio", "codec_name": audio})
    return {"streams": streams, "format": {"format_name": container, "duration": dauer, "size": "35497873"}}


def test_info_aus_probe():
    info = medien.info_aus_probe(probe(), 35497873)
    assert (info.fps, info.frames, info.breite, info.hoehe, info.groesse) == (25.0, 574, 2160, 3840, 35497873)
    assert info.dauer_s == pytest.approx(23.04) and info.video_codec == "h264" and info.audio_codec == "aac" and not info.alpha


def test_info_frames_aus_dauer_und_fps_bruch():
    p = probe(nb_frames=None, dauer="10.0")
    p["streams"][0]["avg_frame_rate"] = "24000/1001"
    p["streams"][0]["r_frame_rate"] = "24000/1001"
    del p["streams"][0]["nb_frames"]
    info = medien.info_aus_probe(p)
    assert info.fps == pytest.approx(23.976, abs=0.001) and info.frames == 240


def test_info_ohne_video():
    with pytest.raises(ReviewFehler):
        medien.info_aus_probe({"streams": [{"codec_type": "audio"}], "format": {}})


@pytest.mark.parametrize("kw,erwartet", [
    ({}, "kopie"),
    ({"audio": None}, "kopie"),
    ({"codec": "hevc"}, "umkodieren"),
    ({"pix": "yuv422p"}, "umkodieren"),
    ({"audio": "pcm_s16le"}, "umkodieren"),
    ({"container": "matroska,webm"}, "umkodieren"),
    ({"codec": "prores", "pix": "yuva444p10le"}, "alpha"),
    ({"codec": "png", "pix": "rgba"}, "alpha"),
])
def test_entscheidung(kw, erwartet):
    assert medien.entscheidung(medien.info_aus_probe(probe(**kw))) == erwartet


def test_ffmpeg_befehl():
    cmd = medien.ffmpeg_befehl("/q.mov", "/z.mp4", "h264_videotoolbox", True, 1920 * 1080)
    assert cmd[:2] == ["ffmpeg", "-y"] and "-c:v" in cmd and cmd[cmd.index("-c:v") + 1] == "h264_videotoolbox"
    assert "yuv420p" in cmd and "+faststart" in cmd and cmd[-1] == "/z.mp4" and "0:a:0?" in cmd
    assert cmd[cmd.index("-b:v") + 1] == "8M"
    cmd4k = medien.ffmpeg_befehl("/q.mov", "/z.mp4", "libx264", False, 2160 * 3840)
    assert "-crf" in cmd4k and "0:a:0?" not in cmd4k


@pytest.mark.parametrize("frame,fps,tc", [
    (0, 25.0, "00:00:00:00"), (50, 25.0, "00:00:02:00"), (729, 25.0, "00:00:29:04"), (90061, 25.0, "01:00:02:11"),
    (24, 23.976, "00:00:01:00"), (100, 50.0, "00:00:02:00"), (None, 25.0, "—"),
])
def test_timecode(frame, fps, tc):
    assert medien.timecode(frame, fps) == tc


def test_frame_aus_timecode():
    assert medien.frame_aus_timecode("00:00:29:04", 25.0) == 729
    assert medien.frame_aus_timecode("01:00:02:11", 25) == 90061
    with pytest.raises(ReviewFehler):
        medien.frame_aus_timecode("29:04", 25.0)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg fehlt")
def test_probe_kopie_und_umkodieren(testvideo_h264, testvideo_mpeg4, tmp_path):
    medien.werkzeuge_pruefen()
    info = medien.info_aus_probe(medien.ffprobe(testvideo_h264), testvideo_h264.stat().st_size)
    assert medien.entscheidung(info) == "kopie" and info.frames == 50 and info.fps == 25.0
    info2 = medien.info_aus_probe(medien.ffprobe(testvideo_mpeg4))
    assert medien.entscheidung(info2) == "umkodieren"
    ziel = tmp_path / "video.mp4"
    encoder = medien.umkodieren(testvideo_mpeg4, ziel, info2)
    assert encoder in ("h264_videotoolbox", "libx264") and ziel.stat().st_size > 0
    neu = medien.info_aus_probe(medien.ffprobe(ziel))
    assert neu.video_codec == "h264" and neu.pix_fmt == "yuv420p" and neu.audio_codec == "aac" and abs(neu.frames - 50) <= 1
    bild = tmp_path / "thumb.jpg"
    medien.vorschaubild(ziel, bild, neu.dauer_s)
    assert bild.stat().st_size > 1000
```

- [ ] **Step 2: Tests laufen lassen — erwartet ImportError**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests/test_medien.py -q`

- [ ] **Step 3: Implementieren**

```python file=tools/review/src/niro_review/medien.py
"""Medien: ffprobe → Medieninfo, Entscheidung Kopie/Umkodierung/Alpha, ffmpeg-Aufrufe, Vorschaubild, Timecode.
Spec „Befehle" (Review-Kopie) und „Datenmodell" (Frames sind die Wahrheit)."""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Optional

from .ablage import ReviewFehler

_ALPHA_PIX = {"rgba", "bgra", "argb", "abgr", "ya8", "ya16le", "ya16be", "rgba64le", "rgba64be", "bgra64le", "bgra64be"}


@dataclass
class Medieninfo:
    dauer_s: float
    fps: float
    frames: int
    breite: int
    hoehe: int
    groesse: int
    container: str
    video_codec: str
    pix_fmt: str
    audio_codec: Optional[str]
    alpha: bool


def werkzeuge_pruefen() -> None:
    for w in ("ffmpeg", "ffprobe"):
        if not shutil.which(w):
            raise ReviewFehler(f"{w} fehlt — SETUP.md Schritt 3 (brew install ffmpeg).", 2)


def ffprobe(pfad: Path) -> dict:
    cmd = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(pfad)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise ReviewFehler(f"ffprobe scheitert an „{Path(pfad).name}“: {r.stderr.strip()[-300:]}", 1)
    try:
        return json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        raise ReviewFehler(f"ffprobe liefert kein JSON für „{Path(pfad).name}“.", 1)


def _fps(stream: dict) -> float:
    for feld in ("avg_frame_rate", "r_frame_rate"):
        wert = stream.get(feld)
        if wert and wert not in ("0/0", "0", "0/1"):
            try:
                f = Fraction(wert)
                if f > 0:
                    return float(f)
            except (ValueError, ZeroDivisionError):
                pass
    return 25.0


def info_aus_probe(probe: dict, groesse: int = 0) -> Medieninfo:
    streams = probe.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video:
        raise ReviewFehler("Datei enthält keinen Videostream.", 1)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = probe.get("format") or {}
    fps = _fps(video)
    dauer = float(fmt.get("duration") or video.get("duration") or 0.0)
    frames = int(video.get("nb_frames") or 0) or int(round(dauer * fps))
    if not dauer and frames:
        dauer = frames / fps
    pix = str(video.get("pix_fmt") or "")
    alpha = pix.startswith("yuva") or pix.startswith("gbrap") or pix in _ALPHA_PIX
    return Medieninfo(dauer_s=dauer, fps=fps, frames=frames, breite=int(video.get("width") or 0),
                      hoehe=int(video.get("height") or 0), groesse=int(groesse or fmt.get("size") or 0),
                      container=str(fmt.get("format_name") or ""), video_codec=str(video.get("codec_name") or ""),
                      pix_fmt=pix, audio_codec=str(audio.get("codec_name")) if audio else None, alpha=alpha)


def entscheidung(info: Medieninfo) -> str:
    """kopie = Browser spielt die Datei direkt (MP4/MOV, H.264 yuv420p, AAC oder ohne Ton); sonst umkodieren."""
    if info.alpha:
        return "alpha"
    mp4 = any(t in ("mov", "mp4") for t in info.container.split(","))
    if mp4 and info.video_codec == "h264" and info.pix_fmt == "yuv420p" and info.audio_codec in (None, "aac"):
        return "kopie"
    return "umkodieren"


def ffmpeg_befehl(quelle, ziel, encoder: str = "h264_videotoolbox", hat_ton: bool = True, pixel: int = 0) -> list:
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(quelle), "-map", "0:v:0"]
    if hat_ton:
        cmd += ["-map", "0:a:0?"]
    cmd += ["-c:v", encoder, "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"]
    if encoder == "h264_videotoolbox":
        cmd += ["-b:v", "8M" if pixel <= 1920 * 1080 else "16M", "-allow_sw", "1"]
    else:
        cmd += ["-preset", "medium", "-crf", "18"]
    cmd += ["-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-map_metadata", "-1",
            "-f", "mp4", str(ziel)]
    return cmd


def umkodieren(quelle: Path, ziel: Path, info: Medieninfo) -> str:
    """Review-Kopie als MP4 (H.264 yuv420p, AAC); erst VideoToolbox, dann libx264. Gibt den Encoder zurück."""
    fehler = ""
    for encoder in ("h264_videotoolbox", "libx264"):
        cmd = ffmpeg_befehl(quelle, ziel, encoder, info.audio_codec is not None, info.breite * info.hoehe)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and Path(ziel).is_file() and Path(ziel).stat().st_size > 0:
            return encoder
        fehler = r.stderr.strip()[-300:]
    raise ReviewFehler(f"ffmpeg scheitert an „{Path(quelle).name}“: {fehler}", 2)


def vorschaubild(quelle: Path, ziel: Path, dauer_s: float) -> None:
    """JPEG bei 25 % der Dauer, 640 px breit; Rückfall auf das erste Bild."""
    for ss in (max(0.0, float(dauer_s or 0) * 0.25), 0.0):
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{ss:.3f}", "-i", str(quelle), "-frames:v", "1",
               "-vf", "scale=640:-2", "-q:v", "3", str(ziel)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and Path(ziel).is_file() and Path(ziel).stat().st_size > 0:
            return
    raise ReviewFehler(f"Vorschaubild scheitert an „{Path(quelle).name}“: {r.stderr.strip()[-200:]}", 2)


def timecode(frame: Optional[int], fps: float) -> str:
    if frame is None:
        return "—"
    basis = max(1, int(round(float(fps))))
    s, ff = divmod(int(frame), basis)
    m, ss = divmod(s, 60)
    h, mm = divmod(m, 60)
    return f"{h:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def frame_aus_timecode(tc: str, fps: float) -> int:
    teile = str(tc).strip().split(":")
    if len(teile) != 4 or not all(t.isdigit() for t in teile):
        raise ReviewFehler(f"Timecode „{tc}“: erwartet HH:MM:SS:FF.", 1)
    h, m, s, ff = (int(t) for t in teile)
    basis = max(1, int(round(float(fps))))
    return ((h * 60 + m) * 60 + s) * basis + ff
```

- [ ] **Step 4: Tests grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests/test_medien.py -q`

- [ ] **Step 5: Commit**

```bash
git add tools/review/src/niro_review/medien.py tools/review/tests/test_medien.py
git commit -m "feat(review): Medien — ffprobe, Kopie/Umkodierung, Vorschaubild, Timecode"
```

---

### Task 4: Kommentare (Regeln, Umsetzung, Export für Claude)

**Files:**
- Create: `tools/review/src/niro_review/kommentare.py`
- Test: `tools/review/tests/test_kommentare.py`

**Interfaces:**
- Consumes: `ablage.ReviewFehler, json_lesen, json_schreiben, jetzt, datum_de`; `medien.timecode, frame_aus_timecode`.
- Produces: `STATUS`, `STATUS_USER`, `laden(version_ordner)` → dict `{"naechste_id", "kommentare"}`,
  `speichern(version_ordner, daten)`, `finden(daten, kid)`, `anlegen(daten, autor, text, frame=None, bis_frame=None)`
  → Kommentar, `aendern(daten, kid, autor, text=None, status=None)`, `loeschen(daten, kid, autor)`,
  `antworten(daten, kid, autor, text)` → Antwort, `umsetzung_anwenden(daten, umsetzung, fps)` → Liste geänderter IDs,
  `sortiert(kommentare)`, `ist_neu(k, geholt_am)`, `export_md(video, version, daten, geholt_am_vorher, datum)` → str,
  `export_json(video, version, daten, geholt_am_vorher)` → dict.
- Kommentar-Felder: `id, frame, bis_frame, autor, text, angelegt, geaendert, status, antworten[], antwort_claude,
  tc_neu (Text), frame_neu (int)`.

- [ ] **Step 1: Tests schreiben**

```python file=tools/review/tests/test_kommentare.py
from __future__ import annotations

import pytest

from niro_review import kommentare as km
from niro_review.ablage import ReviewFehler


def daten_mit(*texte):
    d = {"naechste_id": 1, "kommentare": []}
    for t in texte:
        km.anlegen(d, "Jan", t, frame=10)
    return d


def test_anlegen_ids_und_felder():
    d = {"naechste_id": 1, "kommentare": []}
    k1 = km.anlegen(d, "Jan", "  Schmatzer raus ", frame=50)
    k2 = km.anlegen(d, "Jan", "Zu hektisch")
    k3 = km.anlegen(d, "David", "Bereich", frame=10, bis_frame=40)
    assert [k["id"] for k in d["kommentare"]] == ["K1", "K2", "K3"] and d["naechste_id"] == 4
    assert k1["text"] == "Schmatzer raus" and k1["frame"] == 50 and k1["bis_frame"] is None and k1["status"] == "offen"
    assert k2["frame"] is None and k3["bis_frame"] == 40 and k1["antworten"] == [] and k1["antwort_claude"] is None
    with pytest.raises(ReviewFehler):
        km.anlegen(d, "Jan", "   ")
    with pytest.raises(ReviewFehler):
        km.anlegen(d, "Jan", "x", frame=-1)
    k4 = km.anlegen(d, "Jan", "Out vor In", frame=30, bis_frame=20)
    assert k4["bis_frame"] is None


def test_aendern_und_loeschen_nur_autor():
    d = daten_mit("a", "b")
    km.aendern(d, "K1", "Jan", text="neu")
    assert d["kommentare"][0]["text"] == "neu" and d["kommentare"][0]["geaendert"]
    with pytest.raises(ReviewFehler):
        km.aendern(d, "K1", "David", text="fremd")
    km.aendern(d, "K1", "David", status="erledigt")  # Status darf jeder
    assert d["kommentare"][0]["status"] == "erledigt"
    with pytest.raises(ReviewFehler):
        km.aendern(d, "K1", "Jan", status="umgesetzt")
    with pytest.raises(ReviewFehler):
        km.loeschen(d, "K2", "David")
    km.loeschen(d, "K2", "Jan")
    assert [k["id"] for k in d["kommentare"]] == ["K1"]
    with pytest.raises(ReviewFehler):
        km.finden(d, "K9")


def test_antworten():
    d = daten_mit("a")
    a = km.antworten(d, "K1", "Claude", "Umgesetzt in V2")
    assert d["kommentare"][0]["antworten"] == [a] and a["autor"] == "Claude"
    with pytest.raises(ReviewFehler):
        km.antworten(d, "K1", "Claude", " ")


def test_umsetzung_alles_oder_nichts():
    d = daten_mit("a", "b", "c")
    with pytest.raises(ReviewFehler):
        km.umsetzung_anwenden(d, {"K1": {"status": "umgesetzt"}, "K9": {"status": "umgesetzt"}}, 25.0)
    assert all(k["status"] == "offen" for k in d["kommentare"])
    with pytest.raises(ReviewFehler):
        km.umsetzung_anwenden(d, {"K1": {"status": "kaputt"}}, 25.0)
    with pytest.raises(ReviewFehler):
        km.umsetzung_anwenden(d, {"K1": {"tc_neu": "3:12"}}, 25.0)
    ids = km.umsetzung_anwenden(d, {"K1": {"status": "umgesetzt", "antwort": "Schmatzer weg", "tc_neu": "00:00:03:12"},
                                    "K2": {"status": "rueckfrage", "antwort": "Welche Stelle?"},
                                    "K3": {"antwort": "nur Notiz", "frame_neu": 7}}, 25.0)
    assert ids == ["K1", "K2", "K3"]
    k1, k2, k3 = d["kommentare"]
    assert k1["status"] == "umgesetzt" and k1["antwort_claude"] == "Schmatzer weg" and k1["frame_neu"] == 87 and k1["tc_neu"] == "00:00:03:12"
    assert k2["status"] == "rueckfrage" and k3["status"] == "offen" and k3["frame_neu"] == 7 and k3["tc_neu"] == "00:00:00:07"


def test_sortiert_und_neu():
    d = {"naechste_id": 1, "kommentare": []}
    km.anlegen(d, "Jan", "spät", frame=500)
    km.anlegen(d, "Jan", "allgemein")
    km.anlegen(d, "Jan", "früh", frame=5)
    for i, k in enumerate(d["kommentare"]):
        k["angelegt"] = f"2026-09-18T10:0{i}:00"
    assert [k["text"] for k in km.sortiert(d["kommentare"])] == ["allgemein", "früh", "spät"]
    assert km.ist_neu(d["kommentare"][0], None)
    assert not km.ist_neu(d["kommentare"][0], "2026-09-18T10:00:30")
    assert km.ist_neu(d["kommentare"][1], "2026-09-18T10:00:30")
    d["kommentare"][0]["antworten"].append({"autor": "Jan", "text": "doch", "angelegt": "2026-09-18T11:00:00"})
    assert km.ist_neu(d["kommentare"][0], "2026-09-18T10:30:00")
    d["kommentare"][0]["antworten"][0]["autor"] = "Claude"
    assert not km.ist_neu(d["kommentare"][0], "2026-09-18T10:30:00")


def test_export():
    video = {"titel": "Dold 02 Fokus", "charge": "projects/Dold/Recruiting/2026-07 Dreh", "kunde": "Dold", "projekt": "Recruiting"}
    version = {"nr": 1, "fps": 25.0, "dauer_s": 23.04, "frames": 576, "breite": 2160, "hoehe": 3840, "notiz": "v1",
               "abgeschlossen": {"am": "2026-09-18T14:41:00", "von": "Jan"}, "geholt_am": None}
    d = {"naechste_id": 1, "kommentare": []}
    km.anlegen(d, "Jan", "Schmatzer | raus", frame=50)
    km.anlegen(d, "Jan", "Insgesamt\nzu hektisch")
    km.anlegen(d, "Jan", "Bereich", frame=100, bis_frame=150)
    km.antworten(d, "K1", "Claude", "erledigt in V2")
    km.umsetzung_anwenden(d, {"K1": {"status": "umgesetzt", "antwort": "weg", "tc_neu": "00:00:01:00"}}, 25.0)
    md = km.export_md(video, version, d, None, "18.09.2026")
    assert md.startswith("# Review-Kommentare „Dold 02 Fokus“ V1 (18.09.2026, abgeschlossen 18.09.2026 14:41 von Jan)")
    assert "| 1 | K2 | — | — | Insgesamt zu hektisch |  | offen | neu |" in md
    assert "| 2 | K1 | 00:00:02:00 |  | Schmatzer \\| raus | Claude: weg → V2 00:00:01:00 / Claude: erledigt in V2 | umgesetzt | neu |" in md
    assert "| 3 | K3 | 00:00:04:00 | bis 00:00:06:00 | Bereich |  | offen | neu |" in md
    js = km.export_json(video, version, d, "2026-09-18T10:00:00")
    assert js["quelle"] == "niro-review" and js["titel"] == "Dold 02 Fokus" and js["version"] == 1 and js["fps"] == 25.0
    assert [k["id"] for k in js["kommentare"]] == ["K2", "K1", "K3"] and js["kommentare"][1]["tc"] == "00:00:02:00"
    assert js["kommentare"][2]["tc_bis"] == "00:00:06:00" and all(k["neu"] for k in js["kommentare"])
    leer = km.export_md(video, version, {"naechste_id": 1, "kommentare": []}, None, "18.09.2026")
    assert "Keine Kommentare." in leer
```

- [ ] **Step 2: Tests laufen lassen — erwartet ImportError**

- [ ] **Step 3: Implementieren**

```python file=tools/review/src/niro_review/kommentare.py
"""Kommentare einer Version: anlegen, ändern, löschen, antworten (User über den Server), Umsetzung durch Claude
(alles-oder-nichts), Sortierung, „neu seit geholt_am“, Export als kommentare.md / kommentare.json. Spec „Datenmodell“
und „Export kommentare.md“."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .ablage import ReviewFehler, datum_de, jetzt, json_lesen, json_schreiben
from .medien import frame_aus_timecode, timecode

STATUS = ("offen", "umgesetzt", "rueckfrage", "erledigt")
STATUS_USER = ("offen", "erledigt")


def laden(version_ordner: Path) -> dict:
    d = json_lesen(version_ordner / "kommentare.json")
    if not isinstance(d, dict) or not isinstance(d.get("kommentare"), list):
        return {"naechste_id": 1, "kommentare": []}
    nummern = [_nummer(k.get("id")) for k in d["kommentare"] if isinstance(k, dict)]
    d["naechste_id"] = max([int(d.get("naechste_id") or 1)] + [n + 1 for n in nummern if n is not None])
    return d


def speichern(version_ordner: Path, daten: dict) -> None:
    json_schreiben(version_ordner / "kommentare.json", daten)


def _nummer(kid) -> Optional[int]:
    s = str(kid or "")
    return int(s[1:]) if s.startswith("K") and s[1:].isdigit() else None


def finden(daten: dict, kid: str) -> dict:
    for k in daten.get("kommentare") or []:
        if k.get("id") == kid:
            return k
    raise ReviewFehler(f"Kommentar {kid} unbekannt.")


def _text(text) -> str:
    t = str(text or "").strip()
    if not t:
        raise ReviewFehler("Kommentartext fehlt.")
    return t


def anlegen(daten: dict, autor: str, text: str, frame: Optional[int] = None, bis_frame: Optional[int] = None) -> dict:
    text = _text(text)
    autor = str(autor or "").strip() or "Unbekannt"
    if frame is not None:
        frame = int(frame)
        if frame < 0:
            raise ReviewFehler("Frame darf nicht negativ sein.")
    if bis_frame is not None:
        if frame is None:
            raise ReviewFehler("Bereich braucht einen Start-Frame.")
        bis_frame = int(bis_frame)
        if bis_frame <= frame:
            bis_frame = None
    n = int(daten.get("naechste_id") or 1)
    k = {"id": f"K{n}", "frame": frame, "bis_frame": bis_frame, "autor": autor, "text": text, "angelegt": jetzt(),
         "geaendert": None, "status": "offen", "antworten": [], "antwort_claude": None, "tc_neu": None, "frame_neu": None}
    daten.setdefault("kommentare", []).append(k)
    daten["naechste_id"] = n + 1
    return k


def aendern(daten: dict, kid: str, autor: str, text: Optional[str] = None, status: Optional[str] = None) -> dict:
    k = finden(daten, kid)
    if text is not None:
        if k.get("autor") != autor:
            raise ReviewFehler(f"{kid} stammt von {k.get('autor')} — nur der Autor ändert den Text.")
        k["text"] = _text(text)
        k["geaendert"] = jetzt()
    if status is not None:
        if status not in STATUS_USER:
            raise ReviewFehler(f"Status „{status}“: hier erlaubt sind offen und erledigt.")
        k["status"] = status
        k["geaendert"] = jetzt()
    return k


def loeschen(daten: dict, kid: str, autor: str) -> None:
    k = finden(daten, kid)
    if k.get("autor") != autor:
        raise ReviewFehler(f"{kid} stammt von {k.get('autor')} — nur der Autor löscht.")
    daten["kommentare"] = [x for x in daten["kommentare"] if x.get("id") != kid]


def antworten(daten: dict, kid: str, autor: str, text: str) -> dict:
    k = finden(daten, kid)
    a = {"autor": str(autor or "").strip() or "Unbekannt", "text": _text(text), "angelegt": jetzt()}
    k.setdefault("antworten", []).append(a)
    return a


def umsetzung_anwenden(daten: dict, umsetzung: dict, fps: float) -> list:
    """{"K1": {"status": …, "antwort": "…", "tc_neu": "HH:MM:SS:FF" | "frame_neu": int}} — erst alles prüfen, dann
    schreiben. Gibt die geänderten IDs in der Reihenfolge der Umsetzung zurück."""
    if not isinstance(umsetzung, dict) or not umsetzung:
        raise ReviewFehler("Umsetzung: erwartet ein JSON-Objekt {\"K1\": {...}}.")
    geplant = []
    for kid, eintrag in umsetzung.items():
        k = finden(daten, kid)  # ReviewFehler bei unbekannter ID — nichts geschrieben
        if not isinstance(eintrag, dict):
            raise ReviewFehler(f"{kid}: erwartet ein Objekt mit status/antwort/tc_neu.")
        status = eintrag.get("status")
        if status is not None and status not in STATUS:
            raise ReviewFehler(f"{kid}: Status „{status}“ unbekannt (offen, umgesetzt, rueckfrage, erledigt).")
        frame_neu = eintrag.get("frame_neu")
        if frame_neu is not None:
            frame_neu = int(frame_neu)
        elif eintrag.get("tc_neu") is not None:
            frame_neu = frame_aus_timecode(str(eintrag["tc_neu"]), fps)
        antwort = eintrag.get("antwort")
        geplant.append((k, status, str(antwort).strip() if antwort else None, frame_neu))
    for k, status, antwort, frame_neu in geplant:
        if status:
            k["status"] = status
        if antwort:
            k["antwort_claude"] = antwort
        if frame_neu is not None:
            k["frame_neu"] = frame_neu
            k["tc_neu"] = timecode(frame_neu, fps)
    return [k["id"] for k, _, _, _ in geplant]


def sortiert(kommentare: list) -> list:
    return sorted(kommentare, key=lambda k: (0, 0, _nummer(k.get("id")) or 0) if k.get("frame") is None
                  else (1, int(k["frame"]), _nummer(k.get("id")) or 0))


def ist_neu(k: dict, geholt_am: Optional[str]) -> bool:
    if not geholt_am:
        return True
    if (k.get("angelegt") or "") > geholt_am or (k.get("geaendert") or "") > geholt_am:
        return True
    return any((a.get("angelegt") or "") > geholt_am and a.get("autor") != "Claude" for a in k.get("antworten") or [])


def _zelle(text) -> str:
    return str(text or "").replace("\r", "").replace("\n", " ").replace("|", "\\|").strip()


def _antworten_text(k: dict, naechste: int, fps: float) -> str:
    teile = []
    if k.get("antwort_claude"):
        t = f"Claude: {k['antwort_claude']}"
        if k.get("frame_neu") is not None:
            t += f" → V{naechste} {timecode(k['frame_neu'], fps)}"
        teile.append(t)
    teile += [f"{a.get('autor')}: {a.get('text')}" for a in k.get("antworten") or []]
    return " / ".join(teile)


def export_md(video: dict, version: dict, daten: dict, geholt_am_vorher: Optional[str], datum: str) -> str:
    fps = float(version.get("fps") or 25.0)
    nr = int(version.get("nr") or 0)
    kopf = f"# Review-Kommentare „{video.get('titel')}“ V{nr} ({datum}"
    abg = version.get("abgeschlossen")
    if abg:
        kopf += f", abgeschlossen {datum_de(abg.get('am', ''))} {str(abg.get('am', ''))[11:16]} von {abg.get('von')}"
    kopf += ")"
    dauer = float(version.get("dauer_s") or 0)
    zeile = (f"Charge: {video.get('charge') or '—'} · {fps:g} fps · {dauer:.2f} s · {version.get('frames') or '?'} Frames · "
             f"{version.get('breite') or '?'}×{version.get('hoehe') or '?'}")
    if version.get("notiz"):
        zeile += f" · Notiz V{nr}: {_zelle(version['notiz'])}"
    zeilen = [kopf, "", zeile, ""]
    ks = sortiert(daten.get("kommentare") or [])
    if not ks:
        zeilen.append("Keine Kommentare.")
        return "\n".join(zeilen) + "\n"
    zeilen += ["| Nr | ID | TC | Bereich | Kommentar | Antworten | Status | Neu |", "|---|---|---|---|---|---|---|---|"]
    for i, k in enumerate(ks, start=1):
        tc = timecode(k["frame"], fps) if k.get("frame") is not None else "—"
        bereich = f"bis {timecode(k['bis_frame'], fps)}" if k.get("bis_frame") is not None else ("—" if k.get("frame") is None else "")
        neu = "neu" if ist_neu(k, geholt_am_vorher) else ""
        zeilen.append(f"| {i} | {k['id']} | {tc} | {bereich} | {_zelle(k.get('text'))} | "
                      f"{_zelle(_antworten_text(k, nr + 1, fps))} | {k.get('status')} | {neu} |")
    zeilen += ["", "Status: offen = vom User, umgesetzt/rueckfrage = Antwort von Claude, erledigt = vom User abgehakt. "
               "„neu“ = seit dem letzten Holen angelegt, geändert oder vom User beantwortet."]
    return "\n".join(zeilen) + "\n"


def export_json(video: dict, version: dict, daten: dict, geholt_am_vorher: Optional[str]) -> dict:
    fps = float(version.get("fps") or 25.0)
    out = []
    for k in sortiert(daten.get("kommentare") or []):
        e = dict(k)
        e["tc"] = timecode(k["frame"], fps) if k.get("frame") is not None else None
        e["tc_bis"] = timecode(k["bis_frame"], fps) if k.get("bis_frame") is not None else None
        e["neu"] = ist_neu(k, geholt_am_vorher)
        out.append(e)
    return {"quelle": "niro-review", "gelesen_am": jetzt(), "titel": video.get("titel"), "kunde": video.get("kunde"),
            "projekt": video.get("projekt"), "charge": video.get("charge"), "version": int(version.get("nr") or 0),
            "fps": fps, "dauer_s": version.get("dauer_s"), "frames": version.get("frames"),
            "abgeschlossen": version.get("abgeschlossen"), "geholt_am_vorher": geholt_am_vorher, "kommentare": out}
```

- [ ] **Step 4: Tests grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests/test_kommentare.py -q`

- [ ] **Step 5: Commit**

```bash
git add tools/review/src/niro_review/kommentare.py tools/review/tests/test_kommentare.py
git commit -m "feat(review): Kommentare — Regeln, Umsetzung alles-oder-nichts, Export für Claude"
```

---

### Task 5: Server (Oberfläche ausliefern, API, Medien mit Range und Cache)

**Files:**
- Create: `tools/review/src/niro_review/server.py`
- Test: `tools/review/tests/test_server.py`

**Interfaces:**
- Consumes: `modell.*`, `kommentare.*`, `ablage.sicherer_pfad, name_ok, jetzt, nfc, cache_wurzel, review_wurzel, mac_name`,
  `WERKZEUG_VERSION`.
- Produces: `ReviewServer(adresse, wurzel, cache, ui=UI_ORDNER, index_ttl=15.0)` (ThreadingHTTPServer;
  `.nas_verbunden()`, `.index(frisch=False)`, `.index_verwerfen()`, `.cache_fuellen(quelle, ziel, schluessel)`),
  `Handler`, `UI_ORDNER`, `starten(port, wurzel=None, cache=None)`.
- HTTP-Vertrag (JSON rein/raus, Fehler als `{"fehler": "…"}`):
  `GET /api/zustand` · `GET /api/index[?frisch=1]` · `GET /api/video?kunde=&projekt=&video=` ·
  `POST /api/kommentar {kunde, projekt, video, version, autor, text, frame?, bis_frame?}` (409 wenn abgeschlossen) ·
  `POST /api/kommentar/aendern {…, id, autor, text?, status?, loeschen?}` · `POST /api/antwort {…, id, autor, text}` ·
  `POST /api/version/abschliessen|wieder_oeffnen {kunde, projekt, video, version, autor}` ·
  `POST /api/video/freigeben|freigabe_zuruecknehmen {kunde, projekt, video, autor}` ·
  `GET|HEAD /media/<K>/<P>/<V>/V<n>/video.mp4|thumb.jpg` (Range, Header `X-Quelle: cache|nas`) · `GET /`, `GET /ui/*`.

- [ ] **Step 1: Tests schreiben**

```python file=tools/review/tests/test_server.py
from __future__ import annotations

import http.client
import json
import threading
import time

import pytest

from niro_review import kommentare as km
from niro_review import modell
from niro_review.server import ReviewServer


@pytest.fixture
def ui(tmp_path):
    ui = tmp_path / "ui"
    ui.mkdir()
    (ui / "index.html").write_text("<!doctype html><title>NIRO Review</title>", encoding="utf-8")
    (ui / "app.js").write_text("console.log('x')", encoding="utf-8")
    (tmp_path / "geheim.txt").write_text("nein", encoding="utf-8")
    return ui


def _starten(wurzel, cache, ui):
    srv = ReviewServer(("127.0.0.1", 0), wurzel, cache, ui=ui, index_ttl=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


@pytest.fixture
def srv(wurzeln, ui):
    s = _starten(wurzeln["review"], wurzeln["cache"], ui)
    yield s
    s.shutdown()
    s.server_close()


def anfrage(srv, methode, pfad, body=None, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=5)
    h = dict(headers or {})
    daten = None
    if body is not None:
        daten = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    c.request(methode, pfad, body=daten, headers=h)
    r = c.getresponse()
    inhalt = r.read()
    c.close()
    return r.status, {k.lower(): v for k, v in r.getheaders()}, inhalt


def js(srv, methode, pfad, body=None):
    status, _, inhalt = anfrage(srv, methode, pfad, body)
    return status, json.loads(inhalt.decode("utf-8") or "{}")


def video_anlegen(wurzeln, titel="Dold 02 Fokus", nr=1):
    ordner = modell.video_ordner("Dold", "Recruiting", titel, wurzeln["review"])
    if not modell.video_lesen(ordner):
        modell.video_anlegen(ordner, "Dold", "Recruiting", titel, wurzeln["charge_rel"])
    vo = modell.version_ordner(ordner, nr)
    vo.mkdir(parents=True, exist_ok=True)
    (vo / "video.mp4").write_bytes(b"0123456789" * 1000)
    (vo / "thumb.jpg").write_bytes(b"\xff\xd8bild")
    km.speichern(vo, {"naechste_id": 1, "kommentare": []})
    modell.version_schreiben(ordner, nr, {"nr": nr, "angelegt": "2026-09-18T10:00:00", "von": "Studio-Mac", "fps": 25.0,
                                          "frames": 50, "dauer_s": 2.0, "breite": 320, "hoehe": 180, "notiz": "",
                                          "basis": nr - 1 if nr > 1 else None, "abgeschlossen": None, "geholt_am": None})
    return ordner


def test_zustand_und_ui(srv, wurzeln):
    status, daten = js(srv, "GET", "/api/zustand")
    assert status == 200 and daten["nas_verbunden"] is True and daten["wurzel"] == str(wurzeln["review"])
    status, h, inhalt = anfrage(srv, "GET", "/")
    assert status == 200 and h["content-type"].startswith("text/html") and b"NIRO Review" in inhalt
    assert anfrage(srv, "GET", "/ui/app.js")[0] == 200
    assert anfrage(srv, "GET", "/ui/../geheim.txt")[0] == 404
    assert anfrage(srv, "GET", "/ui/fehlt.js")[0] == 404
    assert anfrage(srv, "GET", "/nix")[0] == 404


def test_index_und_video(srv, wurzeln):
    assert js(srv, "GET", "/api/index") == (200, {"kunden": []})
    video_anlegen(wurzeln)
    status, daten = js(srv, "GET", "/api/index?frisch=1")
    assert status == 200 and daten["kunden"][0]["projekte"][0]["videos"][0]["titel"] == "Dold 02 Fokus"
    status, daten = js(srv, "GET", "/api/video?kunde=Dold&projekt=Recruiting&video=Dold%2002%20Fokus")
    assert status == 200 and daten["versionen"][0]["nr"] == 1 and daten["zustand"] == "review-offen"
    assert daten["versionen"][0]["video_url"] == "/media/Dold/Recruiting/Dold%2002%20Fokus/V1/video.mp4"
    assert js(srv, "GET", "/api/video?kunde=Dold&projekt=Recruiting&video=Fehlt")[0] == 404
    assert js(srv, "GET", "/api/video?kunde=..&projekt=Recruiting&video=x")[0] == 404


def test_kommentar_roundtrip(srv, wurzeln):
    ordner = video_anlegen(wurzeln)
    basis = {"kunde": "Dold", "projekt": "Recruiting", "video": "Dold 02 Fokus", "version": 1}
    status, k = js(srv, "POST", "/api/kommentar", {**basis, "autor": "Jan", "text": "Schmatzer raus", "frame": 50})
    assert status == 200 and k["id"] == "K1" and k["frame"] == 50 and k["status"] == "offen"
    status, k2 = js(srv, "POST", "/api/kommentar", {**basis, "autor": "Jan", "text": "Bereich", "frame": 10, "bis_frame": 30})
    assert status == 200 and k2["bis_frame"] == 30
    assert js(srv, "POST", "/api/kommentar", {**basis, "autor": "Jan", "text": "  "})[0] == 400
    assert js(srv, "POST", "/api/kommentar", {**basis, "version": 7, "autor": "Jan", "text": "x"})[0] == 404
    status, daten = js(srv, "POST", "/api/kommentar/aendern", {**basis, "id": "K1", "autor": "David", "text": "fremd"})
    assert status == 400
    status, daten = js(srv, "POST", "/api/kommentar/aendern", {**basis, "id": "K1", "autor": "David", "status": "erledigt"})
    assert status == 200 and daten["status"] == "erledigt"
    status, daten = js(srv, "POST", "/api/antwort", {**basis, "id": "K1", "autor": "Jan", "text": "doch offen"})
    assert status == 200 and daten["autor"] == "Jan"
    status, daten = js(srv, "POST", "/api/kommentar/aendern", {**basis, "id": "K2", "autor": "Jan", "loeschen": True})
    assert status == 200 and daten["geloescht"] == "K2"
    gespeichert = km.laden(modell.version_ordner(ordner, 1))
    assert [k["id"] for k in gespeichert["kommentare"]] == ["K1"] and gespeichert["kommentare"][0]["antworten"][0]["text"] == "doch offen"
    status, daten = js(srv, "GET", "/api/video?kunde=Dold&projekt=Recruiting&video=Dold%2002%20Fokus")
    assert daten["versionen"][0]["kommentare"][0]["status"] == "erledigt"


def test_abschliessen_und_freigeben(srv, wurzeln):
    ordner = video_anlegen(wurzeln)
    basis = {"kunde": "Dold", "projekt": "Recruiting", "video": "Dold 02 Fokus", "version": 1, "autor": "Jan"}
    status, daten = js(srv, "POST", "/api/version/abschliessen", basis)
    assert status == 200 and daten["abgeschlossen"]["von"] == "Jan"
    status, daten = js(srv, "POST", "/api/kommentar", {**basis, "text": "zu spät", "frame": 1})
    assert status == 409 and "abgeschlossen" in daten["fehler"]
    assert js(srv, "GET", "/api/index")[1]["kunden"][0]["projekte"][0]["videos"][0]["zustand"] == "bei-claude"
    assert js(srv, "POST", "/api/version/wieder_oeffnen", basis)[1]["abgeschlossen"] is None
    assert js(srv, "POST", "/api/kommentar", {**basis, "text": "geht wieder", "frame": 1})[0] == 200
    status, daten = js(srv, "POST", "/api/video/freigeben", basis)
    assert status == 200 and daten["freigegeben"]["von"] == "Jan" and modell.video_lesen(ordner)["freigegeben"]["von"] == "Jan"
    assert js(srv, "GET", "/api/video?kunde=Dold&projekt=Recruiting&video=Dold%2002%20Fokus")[1]["zustand"] == "freigegeben"
    assert js(srv, "POST", "/api/video/freigabe_zuruecknehmen", basis)[1]["freigegeben"] is None
    assert js(srv, "POST", "/api/unbekannt", basis)[0] == 404


def test_media_range_und_cache(srv, wurzeln):
    video_anlegen(wurzeln)
    pfad = "/media/Dold/Recruiting/Dold%2002%20Fokus/V1/video.mp4"
    status, h, inhalt = anfrage(srv, "GET", pfad)
    assert status == 200 and len(inhalt) == 10000 and h["accept-ranges"] == "bytes" and h["content-type"] == "video/mp4"
    assert h["x-quelle"] == "nas"
    status, h, inhalt = anfrage(srv, "GET", pfad, headers={"Range": "bytes=0-99"})
    assert status == 206 and len(inhalt) == 100 and h["content-range"] == "bytes 0-99/10000" and h["content-length"] == "100"
    status, h, inhalt = anfrage(srv, "GET", pfad, headers={"Range": "bytes=9990-"})
    assert status == 206 and inhalt == b"0123456789" and h["content-range"] == "bytes 9990-9999/10000"
    status, h, inhalt = anfrage(srv, "GET", pfad, headers={"Range": "bytes=-10"})
    assert status == 206 and inhalt == b"0123456789"
    status, h, _ = anfrage(srv, "GET", pfad, headers={"Range": "bytes=20000-"})
    assert status == 416 and h["content-range"] == "bytes */10000"
    status, h, inhalt = anfrage(srv, "HEAD", pfad)
    assert status == 200 and inhalt == b"" and h["content-length"] == "10000"
    cache_datei = wurzeln["cache"] / "Dold" / "Recruiting" / "Dold 02 Fokus" / "V1" / "video.mp4"
    for _ in range(50):
        if cache_datei.is_file() and cache_datei.stat().st_size == 10000:
            break
        time.sleep(0.05)
    assert cache_datei.is_file() and cache_datei.stat().st_size == 10000
    status, h, _ = anfrage(srv, "GET", pfad, headers={"Range": "bytes=0-9"})
    assert status == 206 and h["x-quelle"] == "cache"
    assert anfrage(srv, "GET", "/media/Dold/Recruiting/Dold%2002%20Fokus/V1/thumb.jpg")[1]["content-type"] == "image/jpeg"
    assert anfrage(srv, "GET", "/media/Dold/Recruiting/Dold%2002%20Fokus/V1/version.json")[0] == 404
    assert anfrage(srv, "GET", "/media/../geheim.txt")[0] == 404
    assert anfrage(srv, "GET", "/media/Dold/Recruiting/Fehlt/V1/video.mp4")[0] == 404


def test_ohne_nas_503(tmp_path, ui):
    s = _starten(tmp_path / "weg" / "review", tmp_path / "cache", ui)
    try:
        status, daten = js(s, "GET", "/api/index")
        assert status == 503 and "NAS" in daten["fehler"]
        assert js(s, "GET", "/api/zustand")[1]["nas_verbunden"] is False
        assert js(s, "POST", "/api/kommentar", {"kunde": "a", "projekt": "b", "video": "c", "version": 1, "autor": "x", "text": "y"})[0] == 503
        assert anfrage(s, "GET", "/")[0] == 200
    finally:
        s.shutdown()
        s.server_close()
```

- [ ] **Step 2: Tests laufen lassen — erwartet ImportError**

- [ ] **Step 3: Implementieren**

```python file=tools/review/src/niro_review/server.py
"""HTTP-Server: Oberfläche (ui/), JSON-API, Medien mit Range-Streaming aus Cache oder NAS (Cache-Füllung im
Hintergrund). Nur 127.0.0.1, kein Login. Spec „Server und API"."""
from __future__ import annotations

import json
import os
import re
import shutil
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, unquote, urlsplit

from . import WERKZEUG_VERSION
from . import kommentare as km
from . import modell
from .ablage import ReviewFehler, cache_wurzel, jetzt, mac_name, name_ok, nfc, review_wurzel, sicherer_pfad

UI_ORDNER = Path(__file__).resolve().parents[2] / "ui"
BLOCK = 1024 * 1024
MEDIEN_DATEIEN = ("video.mp4", "thumb.jpg")
TYPEN = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".svg": "image/svg+xml", ".otf": "font/otf", ".ttf": "font/ttf", ".woff2": "font/woff2", ".mp4": "video/mp4",
         ".jpg": "image/jpeg", ".png": "image/png", ".json": "application/json", ".ico": "image/x-icon"}
_RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


class HttpFehler(Exception):
    def __init__(self, status: int, text: str):
        super().__init__(text)
        self.status = status


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, adresse, wurzel: Path, cache: Path, ui: Path = UI_ORDNER, index_ttl: float = 15.0):
        super().__init__(adresse, Handler)
        self.wurzel = Path(wurzel)
        self.cache = Path(cache)
        self.ui = Path(ui)
        self.index_ttl = index_ttl
        self.sperre = threading.RLock()
        self._index: Optional[dict] = None
        self._index_zeit = 0.0
        self.cache_laeuft: set = set()

    def nas_verbunden(self) -> bool:
        return self.wurzel.parent.is_dir()

    def index(self, frisch: bool = False) -> dict:
        with self.sperre:
            if frisch or self._index is None or time.time() - self._index_zeit > self.index_ttl:
                self._index = modell.index_bauen(self.wurzel)
                self._index_zeit = time.time()
            return self._index

    def index_verwerfen(self) -> None:
        with self.sperre:
            self._index = None

    def cache_fuellen(self, quelle: Path, ziel: Path, schluessel: str) -> None:
        with self.sperre:
            if schluessel in self.cache_laeuft:
                return
            self.cache_laeuft.add(schluessel)

        def lauf():
            tmp = ziel.with_name(ziel.name + ".teil")
            try:
                ziel.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(quelle, tmp)
                os.replace(tmp, ziel)
            except OSError:
                try:
                    tmp.unlink()
                except OSError:
                    pass
            finally:
                with self.sperre:
                    self.cache_laeuft.discard(schluessel)

        threading.Thread(target=lauf, daemon=True).start()


def _q1(q: dict, name: str) -> str:
    werte = q.get(name) or [""]
    return nfc(werte[0])


class Handler(BaseHTTPRequestHandler):
    server: ReviewServer
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # still
        pass

    # --- Einstiege -----------------------------------------------------------------------------------------------
    def do_GET(self):
        self._bedienen(False)

    def do_HEAD(self):
        self._bedienen(True)

    def do_POST(self):
        try:
            teile = urlsplit(self.path)
            pfad = unquote(teile.path)
            if not pfad.startswith("/api/"):
                raise HttpFehler(404, "Unbekannter Pfad.")
            if not self.server.nas_verbunden():
                raise HttpFehler(503, f"NAS nicht verbunden ({self.server.wurzel}).")
            self._json(self._api_post(pfad[5:], self._body()))
        except (BrokenPipeError, ConnectionResetError):
            pass
        except HttpFehler as e:
            self._json({"fehler": str(e)}, e.status)
        except ReviewFehler as e:
            self._json({"fehler": str(e)}, 400 if e.code == 1 else 503)
        except Exception as e:  # noqa: BLE001 — Server bleibt oben, Fehler sichtbar im Browser
            self._json({"fehler": f"{type(e).__name__}: {e}"}, 500)

    def _bedienen(self, kopf_nur: bool):
        try:
            teile = urlsplit(self.path)
            pfad = unquote(teile.path)
            q = parse_qs(teile.query)
            if pfad in ("/", "/index.html"):
                return self._datei(self.server.ui / "index.html", kopf_nur, cache="no-cache")
            if pfad.startswith("/ui/"):
                ziel = sicherer_pfad(self.server.ui, pfad[4:])
                if not ziel or not ziel.is_file():
                    raise HttpFehler(404, "Datei fehlt.")
                return self._datei(ziel, kopf_nur, cache="no-cache")
            if pfad.startswith("/media/"):
                return self._medien(pfad[7:], kopf_nur)
            if pfad == "/api/zustand":
                return self._json({"nas_verbunden": self.server.nas_verbunden(), "wurzel": str(self.server.wurzel),
                                   "cache": str(self.server.cache), "version": WERKZEUG_VERSION, "mac": mac_name(),
                                   "stand": jetzt()})
            if pfad.startswith("/api/"):
                if not self.server.nas_verbunden():
                    raise HttpFehler(503, f"NAS nicht verbunden ({self.server.wurzel}).")
                return self._json(self._api_get(pfad[5:], q))
            raise HttpFehler(404, "Unbekannter Pfad.")
        except (BrokenPipeError, ConnectionResetError):
            pass
        except HttpFehler as e:
            self._json({"fehler": str(e)}, e.status)
        except ReviewFehler as e:
            self._json({"fehler": str(e)}, 400 if e.code == 1 else 503)
        except Exception as e:  # noqa: BLE001
            self._json({"fehler": f"{type(e).__name__}: {e}"}, 500)

    # --- API -----------------------------------------------------------------------------------------------------
    def _api_get(self, weg: str, q: dict):
        if weg == "index":
            return self.server.index(frisch=_q1(q, "frisch") == "1")
        if weg == "video":
            ordner, _ = self._video({k: _q1(q, k) for k in ("kunde", "projekt", "video")})
            detail = modell.video_detail(ordner)
            if not detail:
                raise HttpFehler(404, "Video unbekannt.")
            return detail
        raise HttpFehler(404, "Unbekannter API-Pfad.")

    def _api_post(self, weg: str, body: dict):
        srv = self.server
        with srv.sperre:
            if weg == "kommentar":
                ordner, _ = self._video(body)
                nr, version = self._version(ordner, body)
                if version.get("abgeschlossen"):
                    raise HttpFehler(409, f"V{nr} ist abgeschlossen — erst „Wieder öffnen“, dann kommentieren.")
                vo = modell.version_ordner(ordner, nr)
                daten = km.laden(vo)
                k = km.anlegen(daten, body.get("autor"), body.get("text"), _int(body.get("frame")), _int(body.get("bis_frame")))
                km.speichern(vo, daten)
                srv.index_verwerfen()
                return k
            if weg == "kommentar/aendern":
                ordner, _ = self._video(body)
                nr, _ = self._version(ordner, body)
                vo = modell.version_ordner(ordner, nr)
                daten = km.laden(vo)
                kid = str(body.get("id") or "")
                if body.get("loeschen"):
                    km.loeschen(daten, kid, body.get("autor"))
                    km.speichern(vo, daten)
                    srv.index_verwerfen()
                    return {"geloescht": kid}
                k = km.aendern(daten, kid, body.get("autor"), body.get("text"), body.get("status"))
                km.speichern(vo, daten)
                srv.index_verwerfen()
                return k
            if weg == "antwort":
                ordner, _ = self._video(body)
                nr, _ = self._version(ordner, body)
                vo = modell.version_ordner(ordner, nr)
                daten = km.laden(vo)
                a = km.antworten(daten, str(body.get("id") or ""), body.get("autor"), body.get("text"))
                km.speichern(vo, daten)
                return a
            if weg in ("version/abschliessen", "version/wieder_oeffnen"):
                ordner, _ = self._video(body)
                nr, version = self._version(ordner, body)
                version["abgeschlossen"] = {"am": jetzt(), "von": _autor(body)} if weg.endswith("abschliessen") else None
                modell.version_schreiben(ordner, nr, version)
                srv.index_verwerfen()
                return version
            if weg in ("video/freigeben", "video/freigabe_zuruecknehmen"):
                ordner, video = self._video(body)
                video["freigegeben"] = {"am": jetzt(), "von": _autor(body)} if weg.endswith("freigeben") else None
                modell.video_schreiben(ordner, video)
                srv.index_verwerfen()
                return video
        raise HttpFehler(404, "Unbekannter API-Pfad.")

    def _video(self, q: dict):
        kunde, projekt, video = (str(q.get(k) or "") for k in ("kunde", "projekt", "video"))
        if not all(name_ok(x) for x in (kunde, projekt, video)):
            raise HttpFehler(404, "Video unbekannt.")
        ordner = modell.video_ordner(kunde, projekt, video, self.server.wurzel)
        daten = modell.video_lesen(ordner)
        if not daten:
            raise HttpFehler(404, "Video unbekannt.")
        return ordner, daten

    def _version(self, ordner: Path, body: dict):
        nr = _int(body.get("version"))
        if nr is None:
            raise HttpFehler(400, "Version fehlt.")
        version = modell.version_lesen(ordner, nr)
        if not version:
            raise HttpFehler(404, f"V{nr} unbekannt.")
        return nr, version

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        roh = self.rfile.read(n) if n > 0 else b""
        try:
            daten = json.loads(roh.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise HttpFehler(400, "Kein gültiges JSON.")
        if not isinstance(daten, dict):
            raise HttpFehler(400, "JSON-Objekt erwartet.")
        return {k: (nfc(v) if isinstance(v, str) else v) for k, v in daten.items()}

    # --- Medien --------------------------------------------------------------------------------------------------
    def _medien(self, rel: str, kopf_nur: bool):
        if rel.rsplit("/", 1)[-1] not in MEDIEN_DATEIEN:
            raise HttpFehler(404, "Datei fehlt.")
        nas = sicherer_pfad(self.server.wurzel, rel)
        cache = sicherer_pfad(self.server.cache, rel)
        nas_da = nas is not None and nas.is_file()
        quelle, herkunft = None, "nas"
        if cache is not None and cache.is_file():
            if not nas_da or cache.stat().st_size == nas.stat().st_size:
                quelle, herkunft = cache, "cache"
        if quelle is None and nas_da:
            quelle = nas
            if cache is not None and rel.endswith("video.mp4"):
                self.server.cache_fuellen(nas, cache, nfc(rel))
        if quelle is None:
            raise HttpFehler(404, "Datei fehlt.")
        self._datei(quelle, kopf_nur, cache="private, max-age=86400", range_header=self.headers.get("Range"),
                    extra={"X-Quelle": herkunft})

    def _datei(self, pfad: Path, kopf_nur: bool, cache: str = "no-cache", range_header: Optional[str] = None,
               extra: Optional[dict] = None):
        groesse = pfad.stat().st_size
        typ = TYPEN.get(pfad.suffix.lower(), "application/octet-stream")
        start, ende, status = 0, groesse - 1, 200
        if range_header:
            m = _RANGE.match(range_header.strip())
            a, b = (m.group(1), m.group(2)) if m else ("", "")
            if not m or (a == "" and b == ""):
                return self._416(groesse)
            if a == "":
                start, ende = max(0, groesse - int(b)), groesse - 1
            else:
                start, ende = int(a), (int(b) if b else groesse - 1)
            if start >= groesse or start > ende:
                return self._416(groesse)
            ende = min(ende, groesse - 1)
            status = 206
        laenge = max(0, ende - start + 1)
        self.send_response(status)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(laenge))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", cache)
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{ende}/{groesse}")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if kopf_nur or laenge == 0:
            return
        with open(pfad, "rb") as f:
            f.seek(start)
            rest = laenge
            while rest > 0:
                block = f.read(min(BLOCK, rest))
                if not block:
                    break
                self.wfile.write(block)
                rest -= len(block)

    def _416(self, groesse: int):
        self.send_response(416)
        self.send_header("Content-Range", f"bytes */{groesse}")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _json(self, daten, status: int = 200):
        roh = json.dumps(daten, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(roh)


def _int(wert) -> Optional[int]:
    if wert is None or wert == "":
        return None
    try:
        return int(wert)
    except (TypeError, ValueError):
        raise HttpFehler(400, f"Zahl erwartet, nicht „{wert}“.")


def _autor(body: dict) -> str:
    return str(body.get("autor") or "").strip() or "Unbekannt"


def starten(port: int = 4711, wurzel: Optional[Path] = None, cache: Optional[Path] = None) -> None:
    srv = ReviewServer(("127.0.0.1", port), wurzel or review_wurzel(), cache or cache_wurzel())
    print(f"NIRO Review {WERKZEUG_VERSION} · http://localhost:{port} · Wurzel {srv.wurzel} · Cache {srv.cache}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
```

- [ ] **Step 4: Tests grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests/test_server.py -q`

- [ ] **Step 5: Commit**

```bash
git add tools/review/src/niro_review/server.py tools/review/tests/test_server.py
git commit -m "feat(review): Server — API, Medien mit Range, Cache-Füllung, 503 ohne NAS"
```

---

### Task 6: LaunchAgent

**Files:**
- Create: `tools/review/src/niro_review/launchagent.py`
- Test: `tools/review/tests/test_launchagent.py`

**Interfaces:**
- Consumes: `ablage.ReviewFehler, repo_wurzel`.
- Produces: `ETIKETT = "de.niro.review"`, `plist_pfad()`, `log_pfad()`, `plist_inhalt(python, skript, repo, port, log,
  umgebung)` → bytes, `installieren(port=4711, launchctl=subprocess.run)` → Path, `deinstallieren(launchctl=subprocess.run)`
  → bool (Plist existierte).

- [ ] **Step 1: Tests schreiben**

```python file=tools/review/tests/test_launchagent.py
from __future__ import annotations

import plistlib
import subprocess
from pathlib import Path

import pytest

from niro_review import launchagent
from niro_review.ablage import ReviewFehler


def test_plist_inhalt():
    roh = launchagent.plist_inhalt("/usr/bin/python3", "/repo/tools/review/review.py", "/repo", 4711, "/log/server.log",
                                   {"NIRO_STUDIO_NAS": "/Volumes/X"})
    d = plistlib.loads(roh)
    assert d["Label"] == "de.niro.review"
    assert d["ProgramArguments"] == ["/usr/bin/python3", "/repo/tools/review/review.py", "server", "--port", "4711"]
    assert d["RunAtLoad"] is True and d["KeepAlive"] is True and d["WorkingDirectory"] == "/repo"
    assert d["StandardOutPath"] == "/log/server.log" and d["StandardErrorPath"] == "/log/server.log"
    assert d["EnvironmentVariables"]["NIRO_STUDIO_NAS"] == "/Volumes/X" and "PATH" in d["EnvironmentVariables"]


def test_installieren_und_deinstallieren(tmp_path, monkeypatch, wurzeln):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    einstieg = wurzeln["repo"] / "tools" / "review" / "review.py"
    einstieg.parent.mkdir(parents=True)
    einstieg.write_text("# Einstieg", encoding="utf-8")
    aufrufe = []

    def launchctl(cmd, **kw):
        aufrufe.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    plist = launchagent.installieren(4711, launchctl=launchctl)
    assert plist == tmp_path / "Library" / "LaunchAgents" / "de.niro.review.plist" and plist.is_file()
    d = plistlib.loads(plist.read_bytes())
    assert d["ProgramArguments"][1] == str(wurzeln["repo"] / "tools" / "review" / "review.py")
    assert d["EnvironmentVariables"]["NIRO_STUDIO_NAS"] == str(wurzeln["nas"])
    assert (tmp_path / "Library" / "Logs" / "NIRO Review").is_dir()
    assert aufrufe[0][:2] == ["launchctl", "bootout"] and aufrufe[1][:2] == ["launchctl", "bootstrap"] and aufrufe[1][3] == str(plist)
    assert launchagent.deinstallieren(launchctl=launchctl) is True and not plist.exists()
    assert aufrufe[2][:2] == ["launchctl", "bootout"]
    assert launchagent.deinstallieren(launchctl=launchctl) is False


def test_installieren_fehler(tmp_path, monkeypatch, wurzeln):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    einstieg = wurzeln["repo"] / "tools" / "review" / "review.py"
    einstieg.parent.mkdir(parents=True)
    einstieg.write_text("# Einstieg", encoding="utf-8")

    def launchctl(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 5 if cmd[1] == "bootstrap" else 0, "", "Input/output error")

    with pytest.raises(ReviewFehler):
        launchagent.installieren(4711, launchctl=launchctl)
```

- [ ] **Step 2: Tests laufen lassen — erwartet ImportError**

- [ ] **Step 3: Implementieren**

```python file=tools/review/src/niro_review/launchagent.py
"""LaunchAgent de.niro.review: Server bei Anmeldung starten, bei Absturz neu starten. Spec „LaunchAgent"."""
from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path

from .ablage import ReviewFehler, repo_wurzel

ETIKETT = "de.niro.review"
UMGEBUNG_SCHLUESSEL = ("NIRO_STUDIO_NAS", "NIRO_REVIEW_ROOT", "NIRO_REVIEW_CACHE", "NIRO_STUDIO_REPO")
PATH_STANDARD = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"


def plist_pfad() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{ETIKETT}.plist"


def log_pfad() -> Path:
    return Path.home() / "Library" / "Logs" / "NIRO Review" / "server.log"


def plist_inhalt(python: str, skript: str, repo: str, port: int, log: str, umgebung: dict) -> bytes:
    d = {"Label": ETIKETT, "ProgramArguments": [python, skript, "server", "--port", str(port)],
         "RunAtLoad": True, "KeepAlive": True, "WorkingDirectory": repo,
         "StandardOutPath": log, "StandardErrorPath": log, "ProcessType": "Background",
         "EnvironmentVariables": {"PATH": PATH_STANDARD, **umgebung}}
    return plistlib.dumps(d)


def _ziel() -> str:
    return f"gui/{os.getuid()}"


def installieren(port: int = 4711, launchctl=subprocess.run) -> Path:
    repo = repo_wurzel()
    skript = repo / "tools" / "review" / "review.py"
    if not skript.is_file():
        raise ReviewFehler(f"Einstieg fehlt: {skript}", 2)
    umgebung = {k: os.environ[k] for k in UMGEBUNG_SCHLUESSEL if os.environ.get(k)}
    plist = plist_pfad()
    log = log_pfad()
    log.parent.mkdir(parents=True, exist_ok=True)
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_bytes(plist_inhalt(sys.executable, str(skript), str(repo), port, str(log), umgebung))
    launchctl(["launchctl", "bootout", f"{_ziel()}/{ETIKETT}"], capture_output=True, text=True)
    r = launchctl(["launchctl", "bootstrap", _ziel(), str(plist)], capture_output=True, text=True)
    if r.returncode != 0:
        raise ReviewFehler(f"launchctl bootstrap scheitert ({r.returncode}): {(r.stderr or r.stdout or '').strip()}", 1)
    return plist


def deinstallieren(launchctl=subprocess.run) -> bool:
    launchctl(["launchctl", "bootout", f"{_ziel()}/{ETIKETT}"], capture_output=True, text=True)
    plist = plist_pfad()
    if plist.exists():
        plist.unlink()
        return True
    return False
```

- [ ] **Step 4: Tests grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests/test_launchagent.py -q`

- [ ] **Step 5: Commit**

```bash
git add tools/review/src/niro_review/launchagent.py tools/review/tests/test_launchagent.py
git commit -m "feat(review): LaunchAgent de.niro.review (installieren/deinstallieren)"
```

---

### Task 7: CLI (hinzufuegen, kommentare, umsetzung, antworten, status, entfernen, server, installieren, oeffnen)

**Files:**
- Create: `tools/review/src/niro_review/cli.py`
- Test: `tools/review/tests/test_cli.py`

**Interfaces:**
- Consumes: alles aus Task 1–6.
- Produces: `main(argv=None)` → int; `link(kunde, projekt, titel=None, port=4711)` → str;
  `version_anlegen(kunde, projekt, charge, titel, datei, nr=None, notiz="", sortierung=None, basis=None, trotzdem=False)`
  → dict `{"titel", "nr", "weg", "ordner", "version"}` (wird von den Tests direkt und von `cmd_hinzufuegen` genutzt).

- [ ] **Step 1: Tests schreiben**

```python file=tools/review/tests/test_cli.py
from __future__ import annotations

import json
import shutil

import pytest

from niro_review import cli
from niro_review import kommentare as km
from niro_review import modell
from niro_review.ablage import json_lesen, json_schreiben

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg fehlt")


def lauf(*argv):
    return cli.main([str(a) for a in argv])


def test_link():
    assert cli.link("Dold", "Recruiting") == "http://localhost:4711/#/Dold/Recruiting"
    assert cli.link("Dold", "Recruiting", "Dold 02 Fokus", 4800) == "http://localhost:4800/#/Dold/Recruiting/Dold%2002%20Fokus"


def test_hinzufuegen_fehler_ohne_nas(wurzeln, monkeypatch, tmp_path, testvideo_h264):
    monkeypatch.setenv("NIRO_REVIEW_ROOT", str(tmp_path / "weg" / "review"))
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264) == 2


@ffmpeg
def test_hinzufuegen_kopie_und_folgeversion(wurzeln, testvideo_h264, capsys):
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264, "--notiz", "Entwurf v1") == 0
    out = capsys.readouterr().out
    assert "Dold 02 Fokus Bagger und Kran V1" in out and "http://localhost:4711/#/Dold/Recruiting/Dold%2002%20Fokus%20Bagger%20und%20Kran" in out
    ordner = wurzeln["review"] / "Dold" / "Recruiting" / "Dold 02 Fokus Bagger und Kran"
    video = json_lesen(ordner / "video.json")
    assert video["charge"] == wurzeln["charge_rel"] and video["sortierung"] == "02"
    v1 = json_lesen(ordner / "V1" / "version.json")
    assert v1["nr"] == 1 and v1["umkodiert"] is False and v1["frames"] == 50 and v1["fps"] == 25.0 and v1["notiz"] == "Entwurf v1"
    assert v1["basis"] is None and v1["abgeschlossen"] is None and v1["geholt_am"] is None and v1["quelle"]
    assert (ordner / "V1" / "video.mp4").stat().st_size == testvideo_h264.stat().st_size
    assert (ordner / "V1" / "thumb.jpg").stat().st_size > 1000
    assert json_lesen(ordner / "V1" / "kommentare.json") == {"naechste_id": 1, "kommentare": []}
    assert (wurzeln["cache"] / "Dold" / "Recruiting" / "Dold 02 Fokus Bagger und Kran" / "V1" / "video.mp4").is_file()
    # zweite Version: nächste Nummer, gleicher Titel über --video
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264, "--video", "Dold 02 Fokus Bagger und Kran") == 0
    assert modell.versionsnummern(ordner) == [1, 2] and json_lesen(ordner / "V2" / "version.json")["basis"] == 1
    # belegte Nummer
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264, "--video", "Dold 02 Fokus Bagger und Kran", "--version", "1") == 1
    assert "nächste freie: V3" in capsys.readouterr().err
    # fehlende Datei
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", "/gibt/es/nicht.mp4") == 1


@ffmpeg
def test_hinzufuegen_umkodieren_und_stapel(wurzeln, testvideo_mpeg4, testvideo_h264, tmp_path):
    ordner = tmp_path / "exporte"
    ordner.mkdir()
    shutil.copy2(testvideo_mpeg4, ordner / "Taxodia-Weg Messe V2.mov")
    shutil.copy2(testvideo_h264, ordner / "Taxodia-Weg Kurz V1.mp4")
    (ordner / "_render_log.json").write_text("{}", encoding="utf-8")
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--ordner", ordner, "--muster", "*.m*", "--version", "1") == 0
    projekt = wurzeln["review"] / "Dold" / "Recruiting"
    assert sorted(p.name for p in projekt.iterdir()) == ["Taxodia-Weg Kurz", "Taxodia-Weg Messe"]
    v = json_lesen(projekt / "Taxodia-Weg Messe" / "V1" / "version.json")
    assert v["umkodiert"] is True and v["encoder"] in ("h264_videotoolbox", "libx264") and v["frames"] in (49, 50, 51)
    assert json_lesen(projekt / "Taxodia-Weg Kurz" / "V1" / "version.json")["umkodiert"] is False


@ffmpeg
def test_kommentare_umsetzung_status_entfernen(wurzeln, testvideo_h264, capsys):
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264) == 0
    ordner = wurzeln["review"] / "Dold" / "Recruiting" / "Dold 02 Fokus Bagger und Kran"
    # keine Kommentare → Exit 1, kein Export
    assert lauf("kommentare", wurzeln["charge_rel"]) == 1
    assert not (wurzeln["charge"] / "Material").exists()
    # Kommentare wie aus der Oberfläche
    daten = km.laden(ordner / "V1")
    km.anlegen(daten, "Jan", "Schmatzer raus", frame=25)
    km.anlegen(daten, "Jan", "Insgesamt zu hektisch")
    km.speichern(ordner / "V1", daten)
    v = modell.version_lesen(ordner, 1)
    v["abgeschlossen"] = {"am": "2026-09-18T14:41:00", "von": "Jan"}
    modell.version_schreiben(ordner, 1, v)
    assert lauf("kommentare", "Dold/Recruiting") == 0
    out = capsys.readouterr().out
    assert "2 neu" in out and "K1" in out and "00:00:01:00" in out and "abgeschlossen" in out
    feedback = list((wurzeln["charge"] / "Material" / "Feedback").iterdir())
    assert len(feedback) == 1 and feedback[0].name.endswith("Review Dold 02 Fokus Bagger und Kran V1")
    md = (feedback[0] / "kommentare.md").read_text(encoding="utf-8")
    assert "| K1 | 00:00:01:00 |" in md and "Insgesamt zu hektisch" in md
    js = json_lesen(feedback[0] / "kommentare.json")
    assert js["version"] == 1 and len(js["kommentare"]) == 2 and js["charge"] == wurzeln["charge_rel"]
    assert modell.version_lesen(ordner, 1)["geholt_am"]
    # nichts Neues mehr → 1; --alle → 0 und Export erneut
    assert lauf("kommentare", wurzeln["charge_rel"]) == 1
    assert lauf("kommentare", wurzeln["charge_rel"], "--alle") == 0
    # Umsetzung mit neuer Version
    umsetzung = wurzeln["repo"] / "umsetzung.json"
    json_schreiben(umsetzung, {"K1": {"status": "umgesetzt", "antwort": "Schmatzer weg", "tc_neu": "00:00:00:20"},
                               "K2": {"status": "rueckfrage", "antwort": "Welche Stellen genau?"}})
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264, "--video", "Dold 02 Fokus Bagger und Kran",
                "--umsetzung", umsetzung, "--notiz", "v2") == 0
    k = {x["id"]: x for x in km.laden(ordner / "V1")["kommentare"]}
    assert k["K1"]["status"] == "umgesetzt" and k["K1"]["frame_neu"] == 20 and k["K2"]["status"] == "rueckfrage"
    assert modell.version_lesen(ordner, 2)["basis"] == 1
    # unbekannte ID → Exit 1, keine Version angelegt
    json_schreiben(umsetzung, {"K9": {"status": "umgesetzt"}})
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264, "--video", "Dold 02 Fokus Bagger und Kran", "--umsetzung", umsetzung) == 1
    assert modell.versionsnummern(ordner) == [1, 2]
    # umsetzung / antworten als eigene Befehle
    json_schreiben(umsetzung, {"K2": {"status": "umgesetzt", "antwort": "jetzt klar"}})
    assert lauf("umsetzung", wurzeln["charge_rel"], "--video", "Dold 02 Fokus Bagger und Kran", "--version", "1", "--datei", umsetzung) == 0
    assert lauf("antworten", wurzeln["charge_rel"], "--video", "Dold 02 Fokus Bagger und Kran", "--version", "1", "--kommentar", "K2", "--text", "Danke") == 0
    k2 = km.finden(km.laden(ordner / "V1"), "K2")
    assert k2["status"] == "umgesetzt" and k2["antworten"][-1] == {**k2["antworten"][-1], "autor": "Claude", "text": "Danke"}
    # status
    assert lauf("status", "Dold/Recruiting") == 0
    out = capsys.readouterr().out
    assert "Dold 02 Fokus Bagger und Kran" in out and "V2" in out and "review-offen" in out
    # entfernen → Papierkorb
    assert lauf("entfernen", wurzeln["charge_rel"], "--video", "Dold 02 Fokus Bagger und Kran", "--version", "2") == 0
    assert modell.versionsnummern(ordner) == [1]
    assert lauf("entfernen", wurzeln["charge_rel"], "--video", "Dold 02 Fokus Bagger und Kran") == 0
    assert not ordner.exists()
    korb = list((wurzeln["review"] / "_papierkorb").iterdir())
    assert len(korb) == 2
    assert lauf("entfernen", wurzeln["charge_rel"], "--video", "Gibt es nicht") == 1


def test_hinzufuegen_alpha_abgelehnt(wurzeln, tmp_path, monkeypatch):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg fehlt")
    import subprocess
    alpha = tmp_path / "overlay.mov"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=160x90:rate=25:duration=1",
                    "-vf", "format=yuva444p10le", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(alpha)], check=True)
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", alpha) == 1
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", alpha, "--trotzdem") == 0
```

- [ ] **Step 2: Tests laufen lassen — erwartet ImportError**

- [ ] **Step 3: Implementieren**

```python file=tools/review/src/niro_review/cli.py
"""CLI von NIRO Review (Aufruf über tools/review/review.py). Befehle und Exit-Codes: Spec „Befehle"."""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from . import WERKZEUG_VERSION, ablage, kommentare as km, launchagent, medien, modell
from .ablage import ReviewFehler, jetzt, nfc

PORT = 4711


def link(kunde: str, projekt: str, titel: Optional[str] = None, port: int = PORT) -> str:
    teile = [kunde, projekt] + ([titel] if titel else [])
    return f"http://localhost:{port}/#/" + "/".join(quote(nfc(t), safe="") for t in teile)


def _nas_pruefen() -> None:
    if not ablage.nas_verbunden():
        raise ReviewFehler(f"NAS nicht verbunden: {ablage.review_wurzel().parent} fehlt.", 2)


def _quelle_rel(datei: Path) -> str:
    try:
        return str(datei.resolve().relative_to(ablage.repo_wurzel().resolve()))
    except ValueError:
        return str(datei.resolve())


def _umsetzung_lesen(pfad: Optional[str]) -> Optional[dict]:
    if not pfad:
        return None
    daten = ablage.json_lesen(Path(pfad))
    if daten is None:
        raise ReviewFehler(f"Umsetzung fehlt: {pfad}")
    return daten


def version_anlegen(kunde: str, projekt: str, charge: Optional[str], titel: str, datei: Path, nr: Optional[int] = None,
                    notiz: str = "", sortierung: Optional[str] = None, basis: Optional[int] = None,
                    trotzdem: bool = False, umsetzung: Optional[dict] = None) -> dict:
    """Version anlegen: prüfen, Review-Kopie in den Cache, Vorschaubild, aufs NAS, version.json zuletzt."""
    datei = Path(datei)
    if not datei.is_file():
        raise ReviewFehler(f"Datei fehlt: {datei}")
    wurzel = ablage.review_wurzel()
    ordner = modell.video_ordner(kunde, projekt, titel, wurzel)
    video = modell.video_lesen(ordner)
    nr = int(nr) if nr else modell.naechste_version(ordner)
    if nr < 1:
        raise ReviewFehler("Versionsnummer muss ≥ 1 sein.")
    vo = modell.version_ordner(ordner, nr)
    if modell.version_lesen(ordner, nr) or vo.exists():
        raise ReviewFehler(f"V{nr} von „{titel}“ existiert — nächste freie: V{modell.naechste_version(ordner)}.")
    basis_nr = basis if basis else (nr - 1 if nr > 1 else None)
    basis_daten = None
    if umsetzung is not None:
        if basis_nr is None or not modell.version_lesen(ordner, basis_nr):
            raise ReviewFehler(f"--umsetzung braucht eine Basisversion (V{basis_nr or '?'} fehlt).")
        basis_daten = km.laden(modell.version_ordner(ordner, basis_nr))
        basis_fps = float((modell.version_lesen(ordner, basis_nr) or {}).get("fps") or 25.0)
        km.umsetzung_anwenden(copy.deepcopy(basis_daten), umsetzung, basis_fps)  # nur prüfen — alles oder nichts
    info = medien.info_aus_probe(medien.ffprobe(datei), datei.stat().st_size)
    weg = medien.entscheidung(info)
    if weg == "alpha" and not trotzdem:
        raise ReviewFehler("Alpha-Overlay ohne Bild darunter — erst als Komposit rendern (oder --trotzdem).")
    cache_v = ablage.cache_wurzel() / nfc(kunde) / nfc(projekt) / nfc(titel) / f"V{nr}"
    cache_v.mkdir(parents=True, exist_ok=True)
    cache_video, cache_thumb = cache_v / "video.mp4", cache_v / "thumb.jpg"
    encoder = None
    if weg == "kopie":
        shutil.copy2(datei, cache_video)
    else:
        encoder = medien.umkodieren(datei, cache_video, info)
        info = medien.info_aus_probe(medien.ffprobe(cache_video), cache_video.stat().st_size)
    medien.vorschaubild(cache_video, cache_thumb, info.dauer_s)
    if video is None:
        video = modell.video_anlegen(ordner, kunde, projekt, titel, charge, sortierung)
    vo.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(cache_video, vo / "video.mp4")
        shutil.copy2(cache_thumb, vo / "thumb.jpg")
        if (vo / "video.mp4").stat().st_size != cache_video.stat().st_size:
            raise ReviewFehler("Kopie aufs NAS unvollständig (Größe weicht ab).", 2)
        km.speichern(vo, modell.KOMMENTARE_LEER())
        version = {"nr": nr, "angelegt": jetzt(), "von": ablage.mac_name(), "quelle": _quelle_rel(datei),
                   "dauer_s": round(info.dauer_s, 3), "fps": info.fps, "frames": info.frames, "breite": info.breite,
                   "hoehe": info.hoehe, "groesse": cache_video.stat().st_size, "umkodiert": weg != "kopie",
                   "encoder": encoder, "notiz": notiz or "", "basis": basis_nr, "abgeschlossen": None, "geholt_am": None}
        modell.version_schreiben(ordner, nr, version)
    except BaseException:
        shutil.rmtree(vo, ignore_errors=True)
        raise
    if umsetzung is not None and basis_daten is not None:
        km.umsetzung_anwenden(basis_daten, umsetzung, basis_fps)
        km.speichern(modell.version_ordner(ordner, basis_nr), basis_daten)
    return {"titel": nfc(titel), "nr": nr, "weg": "Kopie" if weg == "kopie" else f"umkodiert ({encoder})",
            "ordner": ordner, "version": version}


def cmd_hinzufuegen(args) -> int:
    _nas_pruefen()
    medien.werkzeuge_pruefen()
    ziel = ablage.ziel_aufloesen(args.charge)
    if ziel.charge is None:
        raise ReviewFehler("hinzufuegen braucht die Charge: projects/<Kunde>/<Projekt>/<Charge>.")
    kunde, projekt = args.kunde or ziel.kunde, args.projekt or ziel.projekt
    if bool(args.datei) == bool(args.ordner):
        raise ReviewFehler("Genau eines von --datei oder --ordner angeben.")
    if args.umsetzung and args.ordner:
        raise ReviewFehler("--umsetzung geht nur mit --datei.")
    umsetzung = _umsetzung_lesen(args.umsetzung)
    if args.datei:
        dateien = [Path(args.datei)]
    else:
        quelle = Path(args.ordner)
        if not quelle.is_dir():
            raise ReviewFehler(f"Ordner fehlt: {quelle}")
        dateien = sorted(p for p in quelle.glob(args.muster) if p.is_file() and not p.name.startswith("."))
        if not dateien:
            raise ReviewFehler(f"Keine Dateien in „{quelle}“ ({args.muster}).")
    fehler = 0
    letzter_titel = None
    for datei in dateien:
        titel = args.video if (args.video and args.datei) else modell.titel_aus_dateiname(datei.name)
        try:
            e = version_anlegen(kunde, projekt, ziel.charge, titel, datei, args.nr, args.notiz, args.sortierung,
                                args.basis, args.trotzdem, umsetzung)
        except ReviewFehler as ex:
            if args.datei:
                raise
            fehler += 1
            print(f"✗ {datei.name}: {ex}", file=sys.stderr)
            continue
        v = e["version"]
        print(f"✓ {e['titel']} V{e['nr']} ({e['weg']}, {v['dauer_s']:.2f} s, {v['breite']}×{v['hoehe']}, {v['fps']:g} fps)")
        letzter_titel = e["titel"]
    print(link(kunde, projekt, letzter_titel if len(dateien) == 1 else None, args.port))
    return 1 if fehler else 0


def _videos_finden(ziel: ablage.Ziel, titel: Optional[str]) -> list:
    wurzel = ablage.review_wurzel()
    projekt_ordner = ablage.finde_kind(ablage.finde_kind(wurzel, ziel.kunde), ziel.projekt)
    if not projekt_ordner.is_dir():
        raise ReviewFehler(f"Kein Review-Projekt {ziel.kunde}/{ziel.projekt} unter {wurzel}.")
    out = []
    for vo in sorted(projekt_ordner.iterdir()):
        video = modell.video_lesen(vo)
        if not video or (titel and nfc(video["titel"]) != nfc(titel)):
            continue
        if ziel.charge and video.get("charge") and nfc(video["charge"]) != nfc(ziel.charge) and not titel:
            continue
        out.append((vo, video))
    if not out:
        raise ReviewFehler(f"Kein passendes Video in {ziel.kunde}/{ziel.projekt}" + (f" („{titel}“)." if titel else "."))
    return sorted(out, key=lambda t: modell.sortier_schluessel(t[1]))


def _ein_video(args):
    ziel = ablage.ziel_aufloesen(args.charge)
    if not args.video:
        raise ReviewFehler("--video „<Titel>“ fehlt.")
    vo, video = _videos_finden(ziel, args.video)[0]
    return vo, video


def cmd_kommentare(args) -> int:
    _nas_pruefen()
    ziel = ablage.ziel_aufloesen(args.charge)
    neue_gesamt = exportiert = 0
    for vo, video in _videos_finden(ziel, args.video):
        nrs = modell.versionsnummern(vo)
        if not nrs:
            print(f"· {video['titel']}: keine Version")
            continue
        nr = args.nr or nrs[-1]
        version = modell.version_lesen(vo, nr)
        if not version:
            raise ReviewFehler(f"V{nr} von „{video['titel']}“ fehlt.")
        daten = km.laden(modell.version_ordner(vo, nr))
        geholt_vorher = version.get("geholt_am")
        neue = [k for k in km.sortiert(daten["kommentare"]) if km.ist_neu(k, geholt_vorher)]
        stand = "abgeschlossen" if version.get("abgeschlossen") else "noch offen"
        if not neue and not args.alle:
            print(f"· {video['titel']} V{nr}: keine neuen Kommentare ({len(daten['kommentare'])} bekannt, {stand})")
            continue
        charge_rel = video.get("charge") or ziel.charge
        if not charge_rel:
            raise ReviewFehler(f"„{video['titel']}“ hat keine Charge — Aufruf mit projects/<Kunde>/<Projekt>/<Charge>.")
        ziel_ordner = ablage.repo_wurzel() / charge_rel / "Material" / "Feedback" / f"{ablage.heute()} Review {video['titel']} V{nr}"
        md = km.export_md(video, version, daten, geholt_vorher, ablage.datum_de(ablage.heute()))
        js = km.export_json(video, version, daten, geholt_vorher)
        ablage.atomar_schreiben(ziel_ordner / "kommentare.md", md)
        ablage.json_schreiben(ziel_ordner / "kommentare.json", js)
        version["geholt_am"] = jetzt()
        modell.version_schreiben(vo, nr, version)
        neue_gesamt += len(neue)
        exportiert += 1
        print(f"✓ {video['titel']} V{nr}: {len(neue)} neu, {len(daten['kommentare'])} gesamt, {stand} → {ziel_ordner}")
        fps = float(version.get("fps") or 25.0)
        for k in neue:
            tc = medien.timecode(k["frame"], fps) if k.get("frame") is not None else "allgemein"
            bis = f"–{medien.timecode(k['bis_frame'], fps)}" if k.get("bis_frame") is not None else ""
            print(f"    {k['id']} {tc}{bis} {k.get('autor')}: {k.get('text')}")
        if args.json:
            print(json.dumps(js, ensure_ascii=False, indent=1))
    return 0 if neue_gesamt or (args.alle and exportiert) else 1


def cmd_umsetzung(args) -> int:
    _nas_pruefen()
    vo, video = _ein_video(args)
    version = modell.version_lesen(vo, args.nr)
    if not version:
        raise ReviewFehler(f"V{args.nr} von „{video['titel']}“ fehlt.")
    umsetzung = _umsetzung_lesen(args.datei)
    daten = km.laden(modell.version_ordner(vo, args.nr))
    ids = km.umsetzung_anwenden(daten, umsetzung, float(version.get("fps") or 25.0))
    km.speichern(modell.version_ordner(vo, args.nr), daten)
    print(f"✓ {video['titel']} V{args.nr}: {', '.join(ids)} eingetragen")
    return 0


def cmd_antworten(args) -> int:
    _nas_pruefen()
    vo, video = _ein_video(args)
    if not modell.version_lesen(vo, args.nr):
        raise ReviewFehler(f"V{args.nr} von „{video['titel']}“ fehlt.")
    daten = km.laden(modell.version_ordner(vo, args.nr))
    km.antworten(daten, args.kommentar, args.autor, args.text)
    km.speichern(modell.version_ordner(vo, args.nr), daten)
    print(f"✓ {video['titel']} V{args.nr} {args.kommentar}: Antwort eingetragen")
    return 0


def cmd_status(args) -> int:
    _nas_pruefen()
    index = modell.index_bauen(ablage.review_wurzel())
    ziel = ablage.ziel_aufloesen(args.charge) if args.charge else None
    zeilen = []
    for kunde in index["kunden"]:
        for projekt in kunde["projekte"]:
            if ziel and (kunde["name"] != ziel.kunde or projekt["name"] != ziel.projekt):
                continue
            for v in projekt["videos"]:
                if ziel and ziel.charge and v.get("charge") and nfc(v["charge"]) != nfc(ziel.charge):
                    continue
                zeilen.append(f"{kunde['name']}/{projekt['name']} · {v['titel']} · V{v['neueste']} · {v['zustand']} · "
                              f"{v['offen']} offen ({v['neu']} neu) · {link(kunde['name'], projekt['name'], v['titel'], args.port)}")
    print("\n".join(zeilen) if zeilen else "Keine Videos.")
    return 0


def cmd_entfernen(args) -> int:
    _nas_pruefen()
    vo, video = _ein_video(args)
    korb = ablage.review_wurzel() / "_papierkorb"
    korb.mkdir(parents=True, exist_ok=True)
    stempel = jetzt().replace(":", "-")
    if args.nr:
        quelle = modell.version_ordner(vo, args.nr)
        if not quelle.is_dir():
            raise ReviewFehler(f"V{args.nr} von „{video['titel']}“ fehlt.")
        ziel = korb / f"{stempel} {video['kunde']} {video['projekt']} {video['titel']} V{args.nr}"
    else:
        quelle = vo
        ziel = korb / f"{stempel} {video['kunde']} {video['projekt']} {video['titel']}"
    shutil.move(str(quelle), str(ziel))
    print(f"✓ nach {ziel} verschoben")
    return 0


def cmd_server(args) -> int:
    from . import server
    server.starten(args.port)
    return 0


def cmd_installieren(args) -> int:
    plist = launchagent.installieren(args.port)
    print(f"✓ LaunchAgent {launchagent.ETIKETT} installiert ({plist}) — http://localhost:{args.port} · Log {launchagent.log_pfad()}")
    return 0


def cmd_deinstallieren(args) -> int:
    war_da = launchagent.deinstallieren()
    print("✓ LaunchAgent entfernt" if war_da else "· kein LaunchAgent vorhanden")
    return 0


def cmd_oeffnen(args) -> int:
    url = f"http://localhost:{args.port}/"
    if args.ziel:
        teile = [t for t in nfc(args.ziel).split("/") if t]
        if teile and teile[0] == "projects":
            teile = teile[1:]
        if len(teile) >= 2:
            url = link(teile[0], teile[1], teile[2] if len(teile) > 2 else None, args.port)
    subprocess.run(["open", url], check=False)
    print(url)
    return 0


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="review.py", description=f"NIRO Review {WERKZEUG_VERSION} — lokales Review-Werkzeug")
    sub = p.add_subparsers(dest="befehl", required=True)

    def port(sp):
        sp.add_argument("--port", type=int, default=PORT)

    a = sub.add_parser("hinzufuegen", help="Version eines Videos ablegen")
    a.add_argument("charge")
    a.add_argument("--datei")
    a.add_argument("--ordner")
    a.add_argument("--muster", default="*.mp4")
    a.add_argument("--video", help="Titel (sonst aus dem Dateinamen)")
    a.add_argument("--version", dest="nr", type=int)
    a.add_argument("--notiz", default="")
    a.add_argument("--umsetzung", help="umsetzung.json für die Basisversion")
    a.add_argument("--basis", type=int)
    a.add_argument("--sortierung")
    a.add_argument("--kunde")
    a.add_argument("--projekt")
    a.add_argument("--trotzdem", action="store_true", help="auch Alpha-Dateien annehmen")
    port(a)
    k = sub.add_parser("kommentare", help="Kommentare holen und in die Charge exportieren")
    k.add_argument("charge")
    k.add_argument("--video")
    k.add_argument("--version", dest="nr", type=int)
    k.add_argument("--alle", action="store_true")
    k.add_argument("--json", action="store_true")
    u = sub.add_parser("umsetzung", help="Status/Antwort je Kommentar eintragen")
    u.add_argument("charge")
    u.add_argument("--video", required=True)
    u.add_argument("--version", dest="nr", type=int, required=True)
    u.add_argument("--datei", required=True)
    an = sub.add_parser("antworten", help="Antwort in einen Kommentar-Thread")
    an.add_argument("charge")
    an.add_argument("--video", required=True)
    an.add_argument("--version", dest="nr", type=int, required=True)
    an.add_argument("--kommentar", required=True)
    an.add_argument("--text", required=True)
    an.add_argument("--autor", default="Claude")
    s = sub.add_parser("status", help="Übersicht")
    s.add_argument("charge", nargs="?")
    port(s)
    e = sub.add_parser("entfernen", help="Video oder Version in den Papierkorb")
    e.add_argument("charge")
    e.add_argument("--video", required=True)
    e.add_argument("--version", dest="nr", type=int)
    sv = sub.add_parser("server", help="Server im Vordergrund")
    port(sv)
    i = sub.add_parser("installieren", help="LaunchAgent anlegen und laden")
    port(i)
    sub.add_parser("deinstallieren", help="LaunchAgent entladen und entfernen")
    o = sub.add_parser("oeffnen", help="Browser öffnen")
    o.add_argument("ziel", nargs="?")
    port(o)
    return p


BEFEHLE = {"hinzufuegen": cmd_hinzufuegen, "kommentare": cmd_kommentare, "umsetzung": cmd_umsetzung,
           "antworten": cmd_antworten, "status": cmd_status, "entfernen": cmd_entfernen, "server": cmd_server,
           "installieren": cmd_installieren, "deinstallieren": cmd_deinstallieren, "oeffnen": cmd_oeffnen}


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        return BEFEHLE[args.befehl](args)
    except ReviewFehler as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return e.code
```

- [ ] **Step 4: Tests grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests -q`

- [ ] **Step 5: Commit**

```bash
git add tools/review/src/niro_review/cli.py tools/review/tests/test_cli.py
git commit -m "feat(review): CLI — hinzufuegen, kommentare, umsetzung, antworten, status, entfernen, server, installieren, oeffnen"
```

---

### Task 8: Oberfläche (index.html, style.css, app.js, Fonts, Logo)

**Files:**
- Create: `tools/review/ui/index.html`, `tools/review/ui/style.css`, `tools/review/ui/app.js`
- Copy: `tools/motion/public/clients/niro/niro-symbol.svg` → `tools/review/ui/niro-symbol.svg`;
  `tools/motion/public/fonts/Meutas-{Regular,Medium,SemiBold,Bold}.otf` → `tools/review/ui/fonts/`
- Test: Sichtprüfung im Browser-Fenster der App (Task 10); `node --check tools/review/ui/app.js` als Syntaxprüfung.

**Interfaces:**
- Consumes: HTTP-Vertrag aus Task 5 (`/api/index`, `/api/video`, `/api/kommentar`, `/api/kommentar/aendern`,
  `/api/antwort`, `/api/version/*`, `/api/video/*`, `/api/zustand`, `/media/...`).
- Routing per Hash: `#/` Start · `#/<Kunde>/<Projekt>` Projekt · `#/<Kunde>/<Projekt>/<Titel>[/V<n>]` Player
  (Segmente `encodeURIComponent`).
- Autor im Browser: `localStorage["niroReviewAutor"]`.

- [ ] **Step 1: Assets kopieren**

```bash
mkdir -p tools/review/ui/fonts
cp tools/motion/public/clients/niro/niro-symbol.svg tools/review/ui/niro-symbol.svg
for w in Regular Medium SemiBold Bold; do cp "tools/motion/public/fonts/Meutas-$w.otf" tools/review/ui/fonts/; done
```

- [ ] **Step 2: index.html**

```html file=tools/review/ui/index.html
<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NIRO Review</title>
<link rel="icon" href="/ui/niro-symbol.svg" type="image/svg+xml">
<link rel="stylesheet" href="/ui/style.css">
</head>
<body>
<header class="kopf">
  <a class="marke" href="#/" title="Alle Projekte"><img src="/ui/niro-symbol.svg" alt=""><span>NIRO <b>Review</b></span></a>
  <nav class="krumen" id="krumen" aria-label="Pfad"></nav>
  <div class="kopf-rechts">
    <span class="nas" id="nas" title="NAS-Verbindung"><i></i>NAS</span>
    <button class="autor" id="autor-knopf" title="Wer kommentiert? (ändern)">—</button>
  </div>
</header>
<div class="banner" id="banner" hidden></div>
<main class="haupt">
  <aside class="seite" id="seite">
    <input id="suche" class="suche" type="search" placeholder="Suchen …" autocomplete="off" spellcheck="false">
    <nav id="baum" class="baum" aria-label="Kunden und Projekte"></nav>
  </aside>
  <section id="inhalt" class="inhalt"></section>
</main>
<div id="toasts" class="toasts" aria-live="polite"></div>
<dialog id="autor-dialog" class="dialog">
  <form method="dialog" id="autor-form">
    <h2>Wer kommentiert?</h2>
    <p class="gedaempft">Der Name steht an jedem Kommentar und wird im Browser gemerkt.</p>
    <div class="autor-wahl">
      <button type="submit" value="David">David</button>
      <button type="submit" value="Jan">Jan</button>
      <button type="submit" value="Sergio">Sergio</button>
    </div>
    <label class="feld">Anderer Name<input id="autor-frei" type="text" maxlength="40" autocomplete="off"></label>
    <div class="dialog-knoepfe"><button type="submit" value="__frei" class="primaer">Übernehmen</button></div>
  </form>
</dialog>
<script src="/ui/app.js"></script>
</body>
</html>
```

- [ ] **Step 3: style.css**

```css file=tools/review/ui/style.css
@font-face { font-family: "Meutas"; font-weight: 400; src: url("/ui/fonts/Meutas-Regular.otf") format("opentype"); }
@font-face { font-family: "Meutas"; font-weight: 500; src: url("/ui/fonts/Meutas-Medium.otf") format("opentype"); }
@font-face { font-family: "Meutas"; font-weight: 600; src: url("/ui/fonts/Meutas-SemiBold.otf") format("opentype"); }
@font-face { font-family: "Meutas"; font-weight: 700; src: url("/ui/fonts/Meutas-Bold.otf") format("opentype"); }

:root {
  --grund: #1A211C; --flaeche: #232B26; --flaeche-2: #2C352F; --flaeche-3: #354139; --linie: #3A453E;
  --text: #F4F6F2; --gedaempft: #9AA59D; --gruen: #A1D334; --gruen-dunkel: #6E9420; --blau: #7DD1FF; --rot: #FF7D7D;
  --gelb: #F2D14B; --radius: 12px; --radius-klein: 8px;
  --kopf-hoehe: 56px; --seite-breite: 280px;
  --schrift: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --titel: "Meutas", "Roboto", "Helvetica Neue", Arial, sans-serif;
  --mono: "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
html, body { height: 100%; margin: 0; }
body { background: var(--grund); color: var(--text); font: 14px/1.45 var(--schrift); -webkit-font-smoothing: antialiased; overflow: hidden; }
h1, h2, h3 { font-family: var(--titel); font-weight: 600; margin: 0; letter-spacing: 0.01em; }
a { color: inherit; text-decoration: none; }
button { font: inherit; color: inherit; background: var(--flaeche-2); border: 1px solid var(--linie); border-radius: var(--radius-klein); padding: 6px 12px; cursor: pointer; transition: background .12s, border-color .12s; }
button:hover { background: var(--flaeche-3); border-color: #4a574e; }
button:disabled { opacity: .45; cursor: default; }
button.primaer { background: var(--gruen); color: #10160c; border-color: var(--gruen); font-weight: 600; }
button.primaer:hover { background: #b5e64a; }
button.leise { background: transparent; border-color: transparent; color: var(--gedaempft); padding: 4px 8px; }
button.leise:hover { color: var(--text); background: var(--flaeche-2); }
button.gefahr:hover { color: var(--rot); }
input, textarea { font: inherit; color: var(--text); background: var(--flaeche); border: 1px solid var(--linie); border-radius: var(--radius-klein); padding: 8px 10px; outline: none; }
input:focus, textarea:focus { border-color: var(--gruen); }
.gedaempft { color: var(--gedaempft); }
.mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }
[hidden] { display: none !important; }

/* Kopf */
.kopf { height: var(--kopf-hoehe); display: flex; align-items: center; gap: 20px; padding: 0 18px; background: var(--flaeche); border-bottom: 1px solid var(--linie); }
.marke { display: flex; align-items: center; gap: 10px; font-family: var(--titel); font-size: 17px; font-weight: 500; white-space: nowrap; }
.marke img { height: 26px; width: auto; filter: invert(1) brightness(1.2); }
.marke b { color: var(--gruen); font-weight: 700; }
.krumen { flex: 1; display: flex; align-items: center; gap: 8px; color: var(--gedaempft); overflow: hidden; white-space: nowrap; }
.krumen a:hover { color: var(--text); }
.krumen .trenner { opacity: .5; }
.krumen .aktuell { color: var(--text); font-weight: 500; overflow: hidden; text-overflow: ellipsis; }
.kopf-rechts { display: flex; align-items: center; gap: 12px; }
.nas { display: inline-flex; align-items: center; gap: 6px; color: var(--gedaempft); font-size: 12px; }
.nas i { width: 8px; height: 8px; border-radius: 50%; background: var(--gedaempft); display: inline-block; }
.nas.ok i { background: var(--gruen); box-shadow: 0 0 6px var(--gruen); }
.nas.weg i { background: var(--rot); box-shadow: 0 0 6px var(--rot); }
.autor { border-radius: 999px; padding: 5px 14px; font-weight: 500; }
.banner { background: #4a2a2a; color: #ffd6d6; padding: 8px 18px; border-bottom: 1px solid #6b3a3a; font-size: 13px; }

/* Layout */
.haupt { display: flex; height: calc(100vh - var(--kopf-hoehe)); }
.seite { width: var(--seite-breite); flex: none; border-right: 1px solid var(--linie); background: var(--flaeche); display: flex; flex-direction: column; overflow: hidden; }
.suche { margin: 12px; }
.baum { overflow: auto; padding: 0 8px 12px; }
.baum .kunde { margin-top: 8px; }
.baum .kunde-name { padding: 6px 8px 2px; font-family: var(--titel); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--gedaempft); }
.baum .projekt { display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: var(--radius-klein); cursor: pointer; }
.baum .projekt:hover { background: var(--flaeche-2); }
.baum .projekt.aktiv { background: var(--flaeche-3); }
.baum .projekt .name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.zahl { min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; font-size: 11px; font-weight: 600; display: inline-flex; align-items: center; justify-content: center; background: var(--flaeche-3); color: var(--gedaempft); }
.zahl.gruen { background: var(--gruen); color: #10160c; }
.zahl.blau { background: var(--blau); color: #0b1a22; }
.inhalt { flex: 1; overflow: auto; min-width: 0; }
.leer { padding: 60px 40px; color: var(--gedaempft); text-align: center; }

/* Übersicht */
.uebersicht { padding: 24px 28px; }
.uebersicht h1 { font-size: 24px; margin-bottom: 4px; }
.uebersicht .unter { color: var(--gedaempft); margin-bottom: 22px; }
.raster { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 18px; }
.karte { background: var(--flaeche); border: 1px solid var(--linie); border-radius: var(--radius); overflow: hidden; cursor: pointer; transition: transform .12s, border-color .12s; display: flex; flex-direction: column; }
.karte:hover { transform: translateY(-2px); border-color: #4a574e; }
.karte .bild { aspect-ratio: 16 / 10; background: #0f1411; display: flex; align-items: center; justify-content: center; position: relative; }
.karte .bild img { max-width: 100%; max-height: 100%; object-fit: contain; }
.karte .bild .chip { position: absolute; top: 8px; left: 8px; }
.karte .bild .zustand { position: absolute; top: 8px; right: 8px; }
.karte .text { padding: 12px 14px 14px; display: flex; flex-direction: column; gap: 6px; }
.karte .titel { font-weight: 500; line-height: 1.3; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.karte .meta { display: flex; justify-content: space-between; align-items: center; color: var(--gedaempft); font-size: 12px; }
.karte.projekt-karte .text { padding: 16px; }
.karte.projekt-karte .titel { font-family: var(--titel); font-size: 17px; }
.chip { display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px; border-radius: 999px; font-size: 11.5px; font-weight: 600; letter-spacing: .02em; background: var(--flaeche-3); color: var(--text); white-space: nowrap; }
.chip.version { background: rgba(0,0,0,.55); color: var(--text); font-family: var(--mono); }
.chip.review-offen { background: var(--gruen); color: #10160c; }
.chip.bei-claude { background: var(--blau); color: #0b1a22; }
.chip.freigegeben { background: var(--gruen-dunkel); color: #eef8dc; }
.chip.leer { background: var(--flaeche-3); color: var(--gedaempft); }
.chip.status-offen { background: var(--flaeche-3); color: var(--text); }
.chip.status-umgesetzt { background: var(--gruen); color: #10160c; }
.chip.status-rueckfrage { background: var(--blau); color: #0b1a22; }
.chip.status-erledigt { background: transparent; border: 1px solid var(--linie); color: var(--gedaempft); }

/* Player */
.player { display: flex; flex-direction: column; height: 100%; }
.player-kopf { padding: 14px 20px 12px; border-bottom: 1px solid var(--linie); display: flex; align-items: center; gap: 16px; flex-wrap: wrap; background: var(--flaeche); }
.player-kopf h1 { font-size: 18px; flex: 1 1 320px; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.versionen { display: flex; gap: 6px; }
.versionen button { border-radius: 999px; padding: 4px 12px; font-family: var(--mono); font-weight: 600; }
.versionen button.aktiv { background: var(--text); color: var(--grund); border-color: var(--text); }
.aktionen { display: flex; gap: 8px; }
.player-koerper { flex: 1; display: flex; min-height: 0; }
.buehne { flex: 1; display: flex; flex-direction: column; min-width: 0; background: #0f1411; }
.video-rahmen { flex: 1; display: flex; align-items: center; justify-content: center; min-height: 0; position: relative; }
.video-rahmen video { max-width: 100%; max-height: 100%; width: auto; height: 100%; object-fit: contain; background: #000; outline: none; }
.video-rahmen .hinweis { position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,.7); padding: 6px 12px; border-radius: 999px; font-size: 12px; pointer-events: none; }
.leiste { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: var(--flaeche); border-top: 1px solid var(--linie); }
.leiste .knopf { width: 34px; height: 34px; padding: 0; display: inline-flex; align-items: center; justify-content: center; border-radius: var(--radius-klein); }
.leiste .knopf svg { width: 18px; height: 18px; fill: currentColor; }
.leiste .knopf.aktiv { color: var(--gruen); border-color: var(--gruen); }
.leiste .zeit { font-family: var(--mono); font-size: 13px; min-width: 96px; text-align: center; }
.leiste .zeit small { display: block; color: var(--gedaempft); font-size: 10.5px; }
.leiste input[type=range] { width: 80px; accent-color: var(--gruen); }
.scrubber { flex: 1; height: 34px; position: relative; cursor: pointer; display: flex; align-items: center; }
.scrubber .spur { position: absolute; left: 0; right: 0; height: 6px; background: var(--flaeche-3); border-radius: 3px; }
.scrubber .fortschritt { position: absolute; left: 0; height: 6px; background: var(--gruen); border-radius: 3px; width: 0; }
.scrubber .kopf { position: absolute; width: 14px; height: 14px; border-radius: 50%; background: var(--text); margin-left: -7px; box-shadow: 0 0 0 2px var(--grund); pointer-events: none; }
.scrubber .marker { position: absolute; top: 3px; width: 9px; height: 9px; border-radius: 50%; background: var(--blau); margin-left: -4.5px; border: 2px solid var(--grund); z-index: 2; transition: transform .1s; }
.scrubber .marker.bereich { border-radius: 4px; width: auto; margin-left: 0; height: 8px; top: 4px; opacity: .8; }
.scrubber .marker:hover, .scrubber .marker.hervor { transform: scale(1.4); background: var(--gruen); z-index: 3; }
.scrubber .marker.status-erledigt { background: var(--gedaempft); }
.scrubber .marker.status-umgesetzt { background: var(--gruen); }
.notiz { padding: 8px 16px; font-size: 12.5px; color: var(--gedaempft); background: var(--flaeche); border-top: 1px solid var(--linie); }
.notiz b { color: var(--text); font-weight: 500; }

/* Kommentare */
.kommentare { width: 380px; flex: none; border-left: 1px solid var(--linie); background: var(--flaeche); display: flex; flex-direction: column; min-height: 0; }
.kommentare .liste { flex: 1; overflow: auto; padding: 8px 0; }
.kommentare .kopfzeile { padding: 12px 16px 6px; display: flex; align-items: center; justify-content: space-between; color: var(--gedaempft); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; font-family: var(--titel); }
.kommentar { padding: 10px 16px; border-left: 3px solid transparent; }
.kommentar:hover { background: var(--flaeche-2); }
.kommentar.hervor { border-left-color: var(--gruen); background: var(--flaeche-2); }
.kommentar.status-erledigt { opacity: .6; }
.kommentar .zeile-1 { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.kommentar .tc { font-family: var(--mono); font-size: 12px; color: var(--blau); background: rgba(125,209,255,.12); padding: 1px 7px; border-radius: 6px; cursor: pointer; }
.kommentar .tc:hover { background: rgba(125,209,255,.25); }
.kommentar .tc.allgemein { color: var(--gedaempft); background: var(--flaeche-3); cursor: default; }
.kommentar .autor { font-weight: 600; font-size: 13px; }
.kommentar .wann { color: var(--gedaempft); font-size: 11.5px; margin-left: auto; white-space: nowrap; }
.kommentar .text { white-space: pre-wrap; word-break: break-word; }
.kommentar .antwort-claude { margin-top: 8px; padding: 8px 10px; border-radius: var(--radius-klein); background: var(--flaeche-3); border-left: 3px solid var(--gruen); font-size: 13px; }
.kommentar .antwort-claude.rueckfrage { border-left-color: var(--blau); }
.kommentar .antwort-claude b { color: var(--gruen); font-family: var(--titel); font-weight: 600; }
.kommentar .antwort-claude.rueckfrage b { color: var(--blau); }
.kommentar .sprung { margin-left: 8px; font-family: var(--mono); font-size: 12px; color: var(--blau); cursor: pointer; }
.kommentar .thread { margin-top: 6px; display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
.kommentar .thread .antwort { padding-left: 10px; border-left: 2px solid var(--linie); color: var(--text); }
.kommentar .thread .antwort b { font-weight: 600; color: var(--gedaempft); }
.kommentar .werkzeuge { display: flex; gap: 2px; margin-top: 6px; opacity: 0; transition: opacity .12s; }
.kommentar:hover .werkzeuge, .kommentar.hervor .werkzeuge { opacity: 1; }
.kommentar .antwort-form { display: flex; gap: 6px; margin-top: 6px; }
.kommentar .antwort-form input { flex: 1; padding: 6px 8px; }
.kommentar textarea.bearbeiten { width: 100%; min-height: 60px; margin-top: 4px; resize: vertical; }
.seit-block { margin: 8px 12px 4px; border: 1px solid var(--linie); border-radius: var(--radius); background: var(--flaeche-2); overflow: hidden; }
.seit-block summary { padding: 10px 14px; cursor: pointer; font-family: var(--titel); font-weight: 600; font-size: 13px; display: flex; align-items: center; gap: 8px; list-style: none; }
.seit-block summary::-webkit-details-marker { display: none; }
.seit-block summary::before { content: "▸"; color: var(--gedaempft); transition: transform .12s; }
.seit-block[open] summary::before { transform: rotate(90deg); }
.seit-block .eintrag { padding: 8px 14px 10px; border-top: 1px solid var(--linie); font-size: 13px; }
.seit-block .eintrag .orig { color: var(--gedaempft); }
.seit-block .eintrag .orig .tc { font-family: var(--mono); color: var(--blau); margin-right: 6px; }
.seit-block .eintrag .antwort { margin-top: 4px; }
.seit-block .eintrag .antwort b { color: var(--gruen); font-family: var(--titel); }
.seit-block .eintrag.rueckfrage .antwort b { color: var(--blau); }
.seit-block .eintrag .zeile { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
.seit-block label { display: inline-flex; align-items: center; gap: 6px; cursor: pointer; font-size: 12.5px; color: var(--gedaempft); }
.seit-block input[type=checkbox] { accent-color: var(--gruen); }
.eingabe { border-top: 1px solid var(--linie); padding: 12px 14px 14px; display: flex; flex-direction: column; gap: 8px; background: var(--flaeche); }
.eingabe .stelle { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 12px; color: var(--gedaempft); }
.eingabe .stelle .tc { font-family: var(--mono); color: var(--blau); background: rgba(125,209,255,.12); padding: 2px 8px; border-radius: 6px; }
.eingabe .stelle button { padding: 2px 9px; font-size: 12px; }
.eingabe .stelle button.aktiv { border-color: var(--blau); color: var(--blau); }
.eingabe textarea { min-height: 64px; resize: vertical; }
.eingabe .senden { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.eingabe .senden .hinweis { font-size: 11.5px; color: var(--gedaempft); }
.eingabe.gesperrt { opacity: .7; }
.eingabe .sperre { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: var(--gedaempft); font-size: 13px; }

/* Toasts, Dialog */
.toasts { position: fixed; right: 18px; bottom: 18px; display: flex; flex-direction: column; gap: 8px; z-index: 50; }
.toast { background: var(--flaeche-3); border: 1px solid var(--linie); border-radius: var(--radius); padding: 10px 14px; display: flex; align-items: center; gap: 12px; box-shadow: 0 8px 30px rgba(0,0,0,.4); max-width: 420px; }
.toast.fehler { border-color: var(--rot); }
.toast.gut { border-color: var(--gruen); }
.dialog { background: var(--flaeche); color: var(--text); border: 1px solid var(--linie); border-radius: var(--radius); padding: 24px 26px; width: 360px; }
.dialog::backdrop { background: rgba(0,0,0,.55); }
.dialog h2 { font-size: 20px; margin-bottom: 4px; }
.autor-wahl { display: flex; gap: 8px; margin: 16px 0; }
.autor-wahl button { flex: 1; padding: 10px; font-weight: 600; }
.feld { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--gedaempft); }
.dialog-knoepfe { display: flex; justify-content: flex-end; margin-top: 14px; }
@media (max-width: 1100px) { .kommentare { width: 320px; } :root { --seite-breite: 220px; } }
```

- [ ] **Step 4: app.js**

```javascript file=tools/review/ui/app.js
"use strict";
(() => {
  // ---------- Helfer ---------------------------------------------------------------------------------------------
  const $ = (sel, wurzel = document) => wurzel.querySelector(sel);
  const el = (tag, attrs = {}, ...kinder) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") e.className = v;
      else if (k === "text") e.textContent = v;
      else if (k === "html") e.innerHTML = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else if (k === "checked" || k === "disabled" || k === "open" || k === "hidden") e[k] = true;
      else e.setAttribute(k, v);
    }
    for (const kind of kinder.flat(Infinity)) if (kind !== null && kind !== undefined && kind !== false) e.append(kind);
    return e;
  };
  const enc = encodeURIComponent;
  const ICON = {
    play: '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>',
    pause: '<svg viewBox="0 0 24 24"><path d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg>',
    zurueck: '<svg viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6 8.5 6V6z"/></svg>',
    vor: '<svg viewBox="0 0 24 24"><path d="M16 6h2v12h-2zM6 18l8.5-6L6 6z"/></svg>',
    schleife: '<svg viewBox="0 0 24 24"><path d="M7 7h10v3l4-4-4-4v3H5v6h2zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2z"/></svg>',
    ton: '<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9zm13.5 3A4.5 4.5 0 0 0 14 8v8a4.5 4.5 0 0 0 2.5-4z"/></svg>',
    stumm: '<svg viewBox="0 0 24 24"><path d="M4.3 3 3 4.3 7.7 9H3v6h4l5 5v-6.7l4.3 4.3-1.4 1.4 2.8 2.8 1.3-1.3zM12 4 9.9 6.1 12 8.2zm4.5 8A4.5 4.5 0 0 0 14 8v2.2l2.5 2.5z"/></svg>',
    vollbild: '<svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7zm-2-4h2V7h3V5H5zm12 7h-3v2h5v-5h-2zm-3-12v2h3v3h2V5z"/></svg>',
  };
  const ZUSTAND = { "review-offen": "Review offen", "bei-claude": "bei Claude", freigegeben: "Freigegeben", leer: "keine Version" };
  const STATUS = { offen: "offen", umgesetzt: "umgesetzt", rueckfrage: "Rückfrage", erledigt: "erledigt" };

  const Z = {
    index: null, route: {}, detail: null, detailStand: "", versionNr: null, version: null,
    autor: "", suche: "", fps: 25, frames: 0, frame: 0, video: null, dom: {}, pollTimer: null, rvfc: null,
    eingabe: { aktiv: false, frame: null, bis: null, allgemein: false }, hervor: null, startFrame: null,
  };
  try { Z.autor = localStorage.getItem("niroReviewAutor") || ""; } catch (e) { Z.autor = ""; }

  async function api(pfad, body) {
    const optionen = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
    const r = await fetch("/api/" + pfad, optionen);
    const text = await r.text();
    let daten = {};
    try { daten = text ? JSON.parse(text) : {}; } catch (e) { daten = { fehler: text }; }
    if (!r.ok) throw new Error(daten.fehler || ("HTTP " + r.status));
    return daten;
  }

  function tc(frame, fps = Z.fps) {
    if (frame === null || frame === undefined) return "—";
    const b = Math.max(1, Math.round(fps));
    const s = Math.floor(frame / b), ff = frame % b;
    return [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60, ff].map((n) => String(n).padStart(2, "0")).join(":");
  }
  function wann(iso) {
    if (!iso) return "";
    const heute = new Date().toISOString().slice(0, 10);
    const t = iso.slice(11, 16);
    return iso.slice(0, 10) === heute ? t : `${iso.slice(8, 10)}.${iso.slice(5, 7)}. ${t}`;
  }
  function toast(text, art = "", knopf = null) {
    const t = el("div", { class: "toast " + art }, el("span", { text }));
    if (knopf) t.append(el("button", { class: "primaer", text: knopf.text, onclick: () => { knopf.tu(); t.remove(); } }));
    t.append(el("button", { class: "leise", text: "×", onclick: () => t.remove() }));
    $("#toasts").append(t);
    setTimeout(() => t.remove(), art === "fehler" ? 12000 : 7000);
  }
  const fehler = (e) => toast(e && e.message ? e.message : String(e), "fehler");

  // ---------- Routing --------------------------------------------------------------------------------------------
  function route() {
    const h = location.hash.replace(/^#\/?/, "");
    const t = h ? h.split("/").map((s) => { try { return decodeURIComponent(s); } catch (e) { return s; } }) : [];
    const r = { kunde: t[0] || null, projekt: t[1] || null, video: t[2] || null, version: null, frame: null };
    if (t[3] && /^V\d+$/.test(t[3])) r.version = parseInt(t[3].slice(1), 10);
    if (t[4] && /^F\d+$/.test(t[4])) r.frame = parseInt(t[4].slice(1), 10);
    return r;
  }
  function pfad(kunde, projekt, video, version, frame) {
    const teile = [kunde, projekt, video].filter((x) => x !== null && x !== undefined).map(enc);
    if (version) teile.push("V" + version);
    if (version && frame !== null && frame !== undefined) teile.push("F" + frame);
    return "#/" + teile.join("/");
  }
  const geheZu = (...a) => { location.hash = pfad(...a); };

  // ---------- Index, Baum, Krumen --------------------------------------------------------------------------------
  async function ladeIndex(frisch = false) {
    try { Z.index = await api("index" + (frisch ? "?frisch=1" : "")); }
    catch (e) { if (!Z.index) Z.index = { kunden: [] }; if (!/NAS/.test(e.message)) fehler(e); }
    return Z.index;
  }
  function projekte() {
    const out = [];
    for (const k of Z.index.kunden) for (const p of k.projekte) out.push({ kunde: k.name, ...p });
    return out;
  }
  function projekt(kunde, name) { return projekte().find((p) => p.kunde === kunde && p.name === name) || null; }
  function renderBaum() {
    const baum = $("#baum");
    const q = Z.suche.trim().toLowerCase();
    const r = Z.route;
    baum.replaceChildren();
    for (const k of Z.index.kunden) {
      const ps = k.projekte.filter((p) => !q || (k.name + " " + p.name).toLowerCase().includes(q) || p.videos.some((v) => v.titel.toLowerCase().includes(q)));
      if (!ps.length) continue;
      const kunde = el("div", { class: "kunde" }, el("div", { class: "kunde-name", text: k.name }));
      for (const p of ps) {
        kunde.append(el("a", { class: "projekt" + (r.kunde === k.name && r.projekt === p.name ? " aktiv" : ""), href: pfad(k.name, p.name) },
          el("span", { class: "name", text: p.name }),
          p.review_offen ? el("span", { class: "zahl gruen", text: String(p.offen || p.review_offen), title: "offene Kommentare / Videos im Review" }) : null,
          p.bei_claude ? el("span", { class: "zahl blau", text: String(p.bei_claude), title: "bei Claude" }) : null));
      }
      baum.append(kunde);
    }
    if (!baum.children.length) baum.append(el("div", { class: "leer", text: Z.index.kunden.length ? "Nichts gefunden." : "Noch keine Reviews." }));
  }
  function renderKrumen() {
    const r = Z.route, k = $("#krumen");
    k.replaceChildren();
    if (!r.kunde) return;
    k.append(el("a", { href: "#/", text: "Projekte" }), el("span", { class: "trenner", text: "›" }));
    if (!r.video) { k.append(el("span", { class: "aktuell", text: `${r.kunde} · ${r.projekt}` })); return; }
    k.append(el("a", { href: pfad(r.kunde, r.projekt), text: `${r.kunde} · ${r.projekt}` }), el("span", { class: "trenner", text: "›" }),
      el("span", { class: "aktuell", text: r.video }));
  }

  // ---------- Übersichten ----------------------------------------------------------------------------------------
  function chipZustand(z) { return el("span", { class: "chip zustand " + z, text: ZUSTAND[z] || z }); }
  function renderStart() {
    const inhalt = $("#inhalt");
    const ps = projekte();
    const raster = el("div", { class: "raster" });
    for (const p of ps) {
      const letzte = p.videos.map((v) => v.angelegt || "").sort().pop() || "";
      raster.append(el("div", { class: "karte projekt-karte", onclick: () => geheZu(p.kunde, p.name) },
        el("div", { class: "text" },
          el("div", { class: "gedaempft", text: p.kunde }),
          el("div", { class: "titel", text: p.name }),
          el("div", { class: "meta" }, el("span", { text: `${p.videos.length} Video${p.videos.length === 1 ? "" : "s"}` }), el("span", { text: wann(letzte) })),
          el("div", { class: "meta" },
            p.review_offen ? el("span", { class: "chip review-offen", text: `${p.review_offen} im Review` }) : el("span"),
            p.bei_claude ? el("span", { class: "chip bei-claude", text: `${p.bei_claude} bei Claude` }) : el("span")))));
    }
    inhalt.replaceChildren(el("div", { class: "uebersicht" }, el("h1", { text: "Projekte" }),
      el("div", { class: "unter", text: ps.length ? `${ps.length} Projekt${ps.length === 1 ? "" : "e"} im Review` : "Noch keine Reviews — Claude legt Stände mit „review.py hinzufuegen“ ab." }),
      raster));
  }
  function renderProjekt() {
    const r = Z.route, inhalt = $("#inhalt");
    const p = projekt(r.kunde, r.projekt);
    if (!p) { inhalt.replaceChildren(el("div", { class: "leer", text: `Kein Review-Projekt ${r.kunde}/${r.projekt}.` })); return; }
    const q = Z.suche.trim().toLowerCase();
    const raster = el("div", { class: "raster" });
    for (const v of p.videos) {
      if (q && !v.titel.toLowerCase().includes(q)) continue;
      raster.append(el("div", { class: "karte", onclick: () => geheZu(p.kunde, p.name, v.titel) },
        el("div", { class: "bild" },
          v.vorschau ? el("img", { src: v.vorschau, alt: "", loading: "lazy" }) : el("span", { class: "gedaempft", text: "kein Bild" }),
          v.neueste ? el("span", { class: "chip version", text: "V" + v.neueste }) : null,
          chipZustand(v.zustand)),
        el("div", { class: "text" },
          el("div", { class: "titel", text: v.titel, title: v.titel }),
          el("div", { class: "meta" },
            el("span", { text: v.gesamt ? `${v.gesamt} Kommentar${v.gesamt === 1 ? "" : "e"}${v.offen ? ` · ${v.offen} offen` : ""}` : "keine Kommentare" }),
            el("span", { text: wann(v.angelegt) })),
          v.notiz ? el("div", { class: "meta gedaempft", text: v.notiz, title: v.notiz }) : null)));
    }
    inhalt.replaceChildren(el("div", { class: "uebersicht" }, el("h1", { text: p.name }),
      el("div", { class: "unter", text: `${p.kunde} · ${p.videos.length} Video${p.videos.length === 1 ? "" : "s"}${p.review_offen ? ` · ${p.review_offen} im Review` : ""}${p.bei_claude ? ` · ${p.bei_claude} bei Claude` : ""}` }),
      raster.children.length ? raster : el("div", { class: "leer", text: "Nichts gefunden." })));
  }

  // ---------- Player ---------------------------------------------------------------------------------------------
  async function ladeDetail() {
    const r = Z.route;
    return api(`video?kunde=${enc(r.kunde)}&projekt=${enc(r.projekt)}&video=${enc(r.video)}`);
  }
  async function renderPlayer() {
    const r = Z.route, inhalt = $("#inhalt");
    let detail;
    try { detail = await ladeDetail(); }
    catch (e) { inhalt.replaceChildren(el("div", { class: "leer", text: "Video nicht gefunden: " + e.message })); return; }
    Z.detail = detail; Z.detailStand = JSON.stringify(detail);
    const nrs = detail.versionen.map((v) => v.nr);
    if (!nrs.length) { inhalt.replaceChildren(el("div", { class: "leer", text: "Dieses Video hat noch keine Version." })); return; }
    Z.versionNr = r.version && nrs.includes(r.version) ? r.version : nrs[nrs.length - 1];
    Z.startFrame = r.frame;
    Z.eingabe = { aktiv: false, frame: null, bis: null, allgemein: false };
    Z.hervor = null;
    bauePlayer();
    Z.pollTimer = setInterval(() => aktualisierePlayer().catch(() => {}), 5000);
  }
  function versionAktuell() { return Z.detail.versionen.find((v) => v.nr === Z.versionNr); }
  function versionBasis() {
    const v = versionAktuell();
    return v && v.basis ? Z.detail.versionen.find((x) => x.nr === v.basis) || null : null;
  }

  function bauePlayer() {
    const inhalt = $("#inhalt");
    const v = versionAktuell();
    Z.version = v; Z.fps = Number(v.fps) || 25; Z.frames = Number(v.frames) || 0; Z.frame = 0;
    const video = el("video", { src: v.video_url, playsinline: "", preload: "auto" });
    Z.video = video;
    const d = Z.dom = {};
    d.kopf = el("div", { class: "player-kopf" });
    d.zeit = el("span", { class: "zeit" }, el("span", { text: tc(0) }), el("small", { text: `F 0 / ${Z.frames}` }));
    d.fortschritt = el("div", { class: "fortschritt" });
    d.kopfPunkt = el("div", { class: "kopf" });
    d.marker = el("div", { class: "marker-schicht" });
    d.scrubber = el("div", { class: "scrubber", title: "Klicken oder ziehen" }, el("div", { class: "spur" }), d.fortschritt, d.marker, d.kopfPunkt);
    d.play = el("button", { class: "knopf", html: ICON.play, title: "Play/Pause (Leertaste)", onclick: umschalten });
    d.schleife = el("button", { class: "knopf", html: ICON.schleife, title: "Schleife", onclick: () => { video.loop = !video.loop; d.schleife.classList.toggle("aktiv", video.loop); } });
    d.ton = el("button", { class: "knopf", html: ICON.ton, title: "Stumm (M)", onclick: stumm });
    const lautstaerke = el("input", { type: "range", min: "0", max: "1", step: "0.02", value: "1", title: "Lautstärke", oninput: (ev) => { video.volume = Number(ev.target.value); video.muted = false; d.ton.innerHTML = ICON.ton; } });
    const leiste = el("div", { class: "leiste" },
      d.play,
      el("button", { class: "knopf", html: ICON.zurueck, title: "Ein Frame zurück (←)", onclick: () => schritt(-1) }),
      el("button", { class: "knopf", html: ICON.vor, title: "Ein Frame vor (→)", onclick: () => schritt(1) }),
      d.zeit, d.scrubber,
      el("span", { class: "zeit", text: tc(Math.max(0, Z.frames - 1)), title: "Dauer" }),
      d.schleife, d.ton, lautstaerke,
      el("button", { class: "knopf", html: ICON.vollbild, title: "Vollbild (F)", onclick: vollbild }));
    d.notiz = el("div", { class: "notiz" });
    const buehne = el("div", { class: "buehne" }, el("div", { class: "video-rahmen" }, video), leiste, d.notiz);
    d.seite = el("aside", { class: "kommentare" });
    inhalt.replaceChildren(el("div", { class: "player" }, d.kopf, el("div", { class: "player-koerper" }, buehne, d.seite)));
    renderKopf(); renderSeite();

    // Video-Ereignisse
    video.addEventListener("loadedmetadata", () => {
      if (!Z.frames && video.duration) { Z.frames = Math.round(video.duration * Z.fps); d.zeit.lastChild.textContent = `F 0 / ${Z.frames}`; }
      if (Z.startFrame !== null && Z.startFrame !== undefined) { springe(Z.startFrame); Z.startFrame = null; }
      renderMarker();
    });
    video.addEventListener("play", () => { d.play.innerHTML = ICON.pause; frameSchleife(); });
    video.addEventListener("pause", () => { d.play.innerHTML = ICON.play; });
    video.addEventListener("ended", () => { d.play.innerHTML = ICON.play; });
    video.addEventListener("timeupdate", () => { if (!video.requestVideoFrameCallback) setzeFrame(Math.round(video.currentTime * Z.fps)); });
    video.addEventListener("seeked", () => setzeFrame(Math.round(video.currentTime * Z.fps)));
    video.addEventListener("click", umschalten);
    video.addEventListener("error", () => toast("Video lässt sich nicht laden (" + (video.error ? video.error.message || video.error.code : "?") + ").", "fehler"));

    // Scrubber
    let zieht = false;
    const frameAusEreignis = (ev) => {
      const r = d.scrubber.getBoundingClientRect();
      const anteil = Math.min(1, Math.max(0, (ev.clientX - r.left) / r.width));
      return Math.round(anteil * Math.max(0, Z.frames - 1));
    };
    d.scrubber.addEventListener("pointerdown", (ev) => { if (ev.target.classList.contains("marker")) return; zieht = true; d.scrubber.setPointerCapture(ev.pointerId); video.pause(); springe(frameAusEreignis(ev)); });
    d.scrubber.addEventListener("pointermove", (ev) => { if (zieht) springe(frameAusEreignis(ev)); });
    d.scrubber.addEventListener("pointerup", () => { zieht = false; });
    d.scrubber.addEventListener("pointercancel", () => { zieht = false; });
  }

  function frameSchleife() {
    const video = Z.video;
    if (!video || !video.requestVideoFrameCallback) return;
    if (Z.rvfc) video.cancelVideoFrameCallback(Z.rvfc);
    const cb = (now, meta) => { if (Z.video !== video) return; setzeFrame(Math.round(meta.mediaTime * Z.fps)); if (!video.paused) Z.rvfc = video.requestVideoFrameCallback(cb); };
    Z.rvfc = video.requestVideoFrameCallback(cb);
  }
  function setzeFrame(f) {
    const max = Z.frames > 0 ? Z.frames - 1 : Math.max(f, 0);
    f = Math.max(0, Math.min(max, f));
    Z.frame = f;
    const d = Z.dom;
    if (!d.zeit) return;
    d.zeit.firstChild.textContent = tc(f);
    d.zeit.lastChild.textContent = `F ${f} / ${Z.frames}`;
    const anteil = Z.frames > 1 ? (f / (Z.frames - 1)) * 100 : 0;
    d.fortschritt.style.width = anteil + "%";
    d.kopfPunkt.style.left = anteil + "%";
  }
  function springe(f) {
    const video = Z.video;
    f = Math.max(0, Math.min(Z.frames > 0 ? Z.frames - 1 : f, Math.round(f)));
    video.currentTime = (f + 0.5) / Z.fps;
    setzeFrame(f);
  }
  function schritt(n) { Z.video.pause(); springe(Z.frame + n); }
  function umschalten() { const v = Z.video; if (v.paused) { if (v.ended || (Z.frames && Z.frame >= Z.frames - 1)) springe(0); v.play().catch(() => {}); } else v.pause(); }
  function stumm() { const v = Z.video; v.muted = !v.muted; Z.dom.ton.innerHTML = v.muted ? ICON.stumm : ICON.ton; }
  function vollbild() { const r = Z.video.closest(".video-rahmen"); if (document.fullscreenElement) document.exitFullscreen(); else if (r.requestFullscreen) r.requestFullscreen(); else if (Z.video.webkitEnterFullscreen) Z.video.webkitEnterFullscreen(); }

  // ---------- Kopf, Marker, Kommentar-Seite ---------------------------------------------------------------------
  function renderKopf() {
    const d = Z.dom, det = Z.detail, v = versionAktuell();
    const zustand = det.video.freigegeben ? "freigegeben" : (v.abgeschlossen ? "bei-claude" : "review-offen");
    const pillen = el("div", { class: "versionen" }, det.versionen.map((x) => el("button", { class: x.nr === Z.versionNr ? "aktiv" : "", text: "V" + x.nr, title: (x.notiz || "") + (x.abgeschlossen ? " · abgeschlossen" : ""), onclick: () => geheZu(Z.route.kunde, Z.route.projekt, Z.route.video, x.nr) })));
    const aktionen = el("div", { class: "aktionen" });
    if (det.video.freigegeben) {
      aktionen.append(el("button", { text: "Freigabe zurücknehmen", onclick: () => videoAktion("video/freigabe_zuruecknehmen") }));
    } else {
      aktionen.append(v.abgeschlossen
        ? el("button", { text: "Wieder öffnen", onclick: () => versionAktion("version/wieder_oeffnen") })
        : el("button", { class: "primaer", text: "Review abschließen", title: "Sperrt V" + v.nr + " für neue Kommentare — dann Claude Bescheid sagen", onclick: () => versionAktion("version/abschliessen") }));
      aktionen.append(el("button", { text: "Freigeben", title: "Video ist fertig", onclick: () => { if (confirm(`„${det.video.titel}“ freigeben?`)) videoAktion("video/freigeben"); } }));
    }
    d.kopf.replaceChildren(el("h1", { text: det.video.titel, title: det.video.titel }), chipZustand(zustand), pillen, aktionen);
    const teile = [`V${v.nr} · ${wann(v.angelegt)}${v.von ? " · " + v.von : ""} · ${Number(v.dauer_s || 0).toFixed(2)} s · ${v.breite}×${v.hoehe} · ${Z.fps} fps`];
    d.notiz.replaceChildren(...[el("span", { text: teile[0] }), v.notiz ? el("span", { html: " · <b>Notiz:</b> " }) : null, v.notiz ? el("span", { text: v.notiz }) : null,
      v.abgeschlossen ? el("span", { text: ` · abgeschlossen ${wann(v.abgeschlossen.am)} von ${v.abgeschlossen.von}` }) : null].filter(Boolean));
  }
  function kommentareSortiert(liste) {
    const nr = (k) => parseInt(String(k.id).slice(1), 10) || 0;
    return [...liste].sort((a, b) => (a.frame === null) !== (b.frame === null) ? (a.frame === null ? -1 : 1) : (a.frame === null ? nr(a) - nr(b) : (a.frame - b.frame) || nr(a) - nr(b)));
  }
  function renderMarker() {
    const d = Z.dom, v = versionAktuell();
    d.marker.replaceChildren();
    if (!Z.frames) return;
    for (const k of v.kommentare) {
      if (k.frame === null || k.frame === undefined) continue;
      const links = (k.frame / Math.max(1, Z.frames - 1)) * 100;
      const m = el("div", { class: "marker status-" + k.status + (Z.hervor === k.id ? " hervor" : ""), "data-id": k.id, title: `${tc(k.frame)} ${k.autor}: ${k.text}`, onclick: (ev) => { ev.stopPropagation(); Z.video.pause(); springe(k.frame); hervorheben(k.id); } });
      m.style.left = links + "%";
      if (k.bis_frame !== null && k.bis_frame !== undefined) { m.classList.add("bereich"); m.style.width = Math.max(0.5, ((k.bis_frame - k.frame) / Math.max(1, Z.frames - 1)) * 100) + "%"; }
      d.marker.append(m);
    }
  }
  function hervorheben(id) {
    Z.hervor = id;
    for (const e of Z.dom.seite.querySelectorAll(".kommentar")) e.classList.toggle("hervor", e.dataset.id === id);
    for (const e of Z.dom.marker.children) e.classList.toggle("hervor", e.dataset.id === id);
    const ziel = Z.dom.seite.querySelector(`.kommentar[data-id="${id}"]`);
    if (ziel) ziel.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
  function renderSeite() {
    const d = Z.dom, det = Z.detail, v = versionAktuell();
    const liste = el("div", { class: "liste" });
    const basis = versionBasis();
    if (basis) {
      const eintraege = basis.kommentare.filter((k) => k.antwort_claude || k.status === "umgesetzt" || k.status === "rueckfrage");
      if (eintraege.length) liste.append(seitBlock(basis, eintraege));
    }
    const ks = kommentareSortiert(v.kommentare);
    liste.append(el("div", { class: "kopfzeile" }, el("span", { text: `Kommentare V${v.nr}` }), el("span", { text: ks.length ? `${ks.length}` : "keine" })));
    for (const k of ks) liste.append(kommentarElement(k, v.nr));
    d.liste = liste;
    d.seite.replaceChildren(liste, eingabeElement(v, det));
    renderMarker();
  }
  function seitBlock(basis, eintraege) {
    const block = el("details", { class: "seit-block", open: true }, el("summary", {}, el("span", { text: `Seit V${basis.nr} geändert` }), el("span", { class: "zahl", text: String(eintraege.length) })));
    for (const k of kommentareSortiert(eintraege)) {
      const e = el("div", { class: "eintrag " + (k.status === "rueckfrage" ? "rueckfrage" : "") },
        el("div", { class: "orig" }, el("span", { class: "tc", text: k.frame !== null ? tc(k.frame) : "allg." }), el("span", { text: `${k.id} · ${k.autor}: ${k.text}` })),
        k.antwort_claude ? el("div", { class: "antwort" }, el("b", { text: k.status === "rueckfrage" ? "Claude · Rückfrage: " : "Claude: " }), el("span", { text: k.antwort_claude })) : null,
        el("div", { class: "zeile" },
          k.frame_neu !== null && k.frame_neu !== undefined ? el("button", { class: "leise", text: "→ " + tc(k.frame_neu), title: "Stelle in V" + Z.versionNr, onclick: () => { Z.video.pause(); springe(k.frame_neu); } }) : null,
          el("span", { class: "chip status-" + k.status, text: STATUS[k.status] || k.status }),
          el("label", {}, el("input", { type: "checkbox", checked: k.status === "erledigt", onchange: (ev) => kommentarStatus(basis.nr, k.id, ev.target.checked ? "erledigt" : "offen") }), "erledigt"),
          k.status === "rueckfrage" ? el("button", { class: "leise", text: "Antworten", onclick: (ev) => antwortForm(ev.target.closest(".eintrag"), basis.nr, k.id) }) : null));
      block.append(e);
    }
    return block;
  }
  function kommentarElement(k, versionNr) {
    const eigener = k.autor === Z.autor;
    const zeit = k.frame === null || k.frame === undefined
      ? el("span", { class: "tc allgemein", text: "allgemein" })
      : el("span", { class: "tc", text: tc(k.frame) + (k.bis_frame !== null && k.bis_frame !== undefined ? " → " + tc(k.bis_frame) : ""), title: "Zur Stelle springen", onclick: () => { Z.video.pause(); springe(k.frame); hervorheben(k.id); } });
    const e = el("div", { class: "kommentar status-" + k.status + (Z.hervor === k.id ? " hervor" : ""), "data-id": k.id, onclick: () => hervorheben(k.id) },
      el("div", { class: "zeile-1" }, zeit, el("span", { class: "autor", text: k.autor }), k.status !== "offen" ? el("span", { class: "chip status-" + k.status, text: STATUS[k.status] || k.status }) : null, el("span", { class: "wann", text: wann(k.angelegt) + (k.geaendert ? " ✎" : ""), title: k.id })),
      el("div", { class: "text", text: k.text }));
    if (k.antwort_claude) e.append(el("div", { class: "antwort-claude " + (k.status === "rueckfrage" ? "rueckfrage" : "") }, el("b", { text: k.status === "rueckfrage" ? "Claude · Rückfrage" : "Claude" }), el("span", { text: " " + k.antwort_claude }),
      k.frame_neu !== null && k.frame_neu !== undefined ? el("a", { class: "sprung", text: `→ V${versionNr + 1} ${tc(k.frame_neu)}`, href: pfad(Z.route.kunde, Z.route.projekt, Z.route.video, versionNr + 1, k.frame_neu), onclick: (ev) => ev.stopPropagation() }) : null));
    if (k.antworten && k.antworten.length) e.append(el("div", { class: "thread" }, k.antworten.map((a) => el("div", { class: "antwort" }, el("b", { text: a.autor + ": " }), el("span", { text: a.text })))));
    e.append(el("div", { class: "werkzeuge" },
      el("button", { class: "leise", text: "Antworten", onclick: (ev) => { ev.stopPropagation(); antwortForm(e, versionNr, k.id); } }),
      el("button", { class: "leise", text: k.status === "erledigt" ? "Wieder öffnen" : "Erledigt", onclick: (ev) => { ev.stopPropagation(); kommentarStatus(versionNr, k.id, k.status === "erledigt" ? "offen" : "erledigt"); } }),
      eigener ? el("button", { class: "leise", text: "Bearbeiten", onclick: (ev) => { ev.stopPropagation(); bearbeiten(e, versionNr, k); } }) : null,
      eigener ? el("button", { class: "leise gefahr", text: "Löschen", onclick: (ev) => { ev.stopPropagation(); if (confirm(`${k.id} löschen?`)) kommentarAendern(versionNr, { id: k.id, loeschen: true }); } }) : null));
    return e;
  }
  function antwortForm(container, versionNr, id) {
    if (container.querySelector(".antwort-form")) return;
    const input = el("input", { type: "text", placeholder: "Antwort …", maxlength: "2000" });
    const form = el("form", { class: "antwort-form", onsubmit: async (ev) => { ev.preventDefault(); if (!input.value.trim()) return; try { await api("antwort", { ...basisDaten(versionNr), id, autor: Z.autor, text: input.value.trim() }); form.remove(); await aktualisierePlayer(true); } catch (e) { fehler(e); } } },
      input, el("button", { class: "primaer", type: "submit", text: "Senden" }), el("button", { class: "leise", type: "button", text: "×", onclick: () => form.remove() }));
    container.append(form);
    input.focus();
  }
  function bearbeiten(e, versionNr, k) {
    if (e.querySelector("textarea.bearbeiten")) return;
    const ta = el("textarea", { class: "bearbeiten", text: k.text });
    const form = el("div", { class: "antwort-form" }, el("button", { class: "primaer", text: "Speichern", onclick: () => kommentarAendern(versionNr, { id: k.id, text: ta.value }) }), el("button", { class: "leise", text: "Abbrechen", onclick: () => { ta.remove(); form.remove(); } }));
    e.querySelector(".text").after(ta, form);
    ta.focus();
  }
  function basisDaten(versionNr) { return { kunde: Z.route.kunde, projekt: Z.route.projekt, video: Z.route.video, version: versionNr }; }
  async function kommentarAendern(versionNr, felder) {
    try { await api("kommentar/aendern", { ...basisDaten(versionNr), autor: Z.autor, ...felder }); await aktualisierePlayer(true); }
    catch (e) { fehler(e); }
  }
  const kommentarStatus = (versionNr, id, status) => kommentarAendern(versionNr, { id, status });
  async function versionAktion(weg) {
    try { await api(weg, { ...basisDaten(Z.versionNr), autor: Z.autor }); await aktualisierePlayer(true); toast(weg.endsWith("abschliessen") ? `V${Z.versionNr} abgeschlossen — sag Claude Bescheid („Review: ${Z.route.kunde}/${Z.route.projekt}“).` : `V${Z.versionNr} wieder offen.`, "gut"); }
    catch (e) { fehler(e); }
  }
  async function videoAktion(weg) {
    try { await api(weg, { kunde: Z.route.kunde, projekt: Z.route.projekt, video: Z.route.video, autor: Z.autor }); await aktualisierePlayer(true); ladeIndex(true).then(renderBaum); }
    catch (e) { fehler(e); }
  }

  // ---------- Eingabe --------------------------------------------------------------------------------------------
  function eingabeElement(v, det) {
    if (det.video.freigegeben) return el("div", { class: "eingabe gesperrt" }, el("div", { class: "sperre" }, el("span", { text: `Freigegeben ${wann(det.video.freigegeben.am)} von ${det.video.freigegeben.von}.` }), el("button", { text: "Freigabe zurücknehmen", onclick: () => videoAktion("video/freigabe_zuruecknehmen") })));
    if (v.abgeschlossen) return el("div", { class: "eingabe gesperrt" }, el("div", { class: "sperre" }, el("span", { text: `V${v.nr} ist abgeschlossen (bei Claude). Neue Kommentare erst nach „Wieder öffnen“.` }), el("button", { text: "Wieder öffnen", onclick: () => versionAktion("version/wieder_oeffnen") })));
    const d = Z.dom;
    d.stelle = el("div", { class: "stelle" });
    d.textarea = el("textarea", { placeholder: "Kommentar an der aktuellen Stelle … (C = hierher, ⌘↩ = senden)", onfocus: () => { Z.video.pause(); if (!Z.eingabe.aktiv) { Z.eingabe.aktiv = true; if (!Z.eingabe.allgemein && Z.eingabe.frame === null) Z.eingabe.frame = Z.frame; } renderStelle(); } });
    const eingabe = el("div", { class: "eingabe" }, d.stelle, d.textarea,
      el("div", { class: "senden" }, el("span", { class: "hinweis", text: "I/O = Bereich · Esc = Video weiter" }), el("button", { class: "primaer", text: "Kommentar senden", onclick: senden })));
    renderStelle();
    return eingabe;
  }
  function renderStelle() {
    const d = Z.dom, e = Z.eingabe;
    if (!d.stelle) return;
    const frame = e.aktiv && e.frame !== null ? e.frame : Z.frame;
    d.stelle.replaceChildren(...[
      el("button", { class: e.allgemein ? "aktiv" : "", text: "Allgemein", title: "ohne Zeitbezug", onclick: () => { e.allgemein = !e.allgemein; e.aktiv = true; if (!e.allgemein && e.frame === null) e.frame = Z.frame; renderStelle(); } }),
      e.allgemein ? el("span", { text: "kein Zeitbezug" }) : el("span", {}, el("span", { text: "am " }), el("span", { class: "tc", text: tc(frame) })),
      !e.allgemein ? el("button", { text: "hierher", title: "auf den aktuellen Frame setzen (I)", onclick: () => { e.aktiv = true; e.frame = Z.frame; if (e.bis !== null && e.bis <= e.frame) e.bis = null; renderStelle(); } }) : null,
      !e.allgemein ? (e.bis !== null
        ? el("span", {}, el("span", { text: "bis " }), el("span", { class: "tc", text: tc(e.bis) }), el("button", { class: "leise", text: "×", title: "Bereich aufheben", onclick: () => { e.bis = null; renderStelle(); } }))
        : el("button", { text: "Bereich bis hier", title: "Out auf den aktuellen Frame (O)", onclick: setzeOut })) : null].filter(Boolean));
  }
  function setzeIn() { const e = Z.eingabe; e.aktiv = true; e.allgemein = false; e.frame = Z.frame; if (e.bis !== null && e.bis <= e.frame) e.bis = null; renderStelle(); }
  function setzeOut() { const e = Z.eingabe; e.aktiv = true; e.allgemein = false; if (e.frame === null) e.frame = Z.frame; if (Z.frame <= e.frame) { toast("Out muss nach In liegen — erst weiter scrubben.", ""); return; } e.bis = Z.frame; renderStelle(); if (Z.dom.textarea) Z.dom.textarea.focus(); }
  async function senden() {
    const d = Z.dom, e = Z.eingabe;
    if (!d.textarea) return;
    const text = d.textarea.value.trim();
    if (!text) { d.textarea.focus(); return; }
    const frame = e.allgemein ? null : (e.frame !== null ? e.frame : Z.frame);
    try {
      await api("kommentar", { ...basisDaten(Z.versionNr), autor: Z.autor, text, frame, bis_frame: e.allgemein ? null : e.bis });
      d.textarea.value = "";
      Z.eingabe = { aktiv: false, frame: null, bis: null, allgemein: false };
      d.textarea.blur();
      await aktualisierePlayer(true);
      renderStelle();
    } catch (err) { fehler(err); }
  }

  // ---------- Aktualisierung -------------------------------------------------------------------------------------
  async function aktualisierePlayer(erzwingen = false) {
    if (!Z.detail) return;
    const detail = await ladeDetail();
    const stand = JSON.stringify(detail);
    if (!erzwingen && stand === Z.detailStand) return;
    const vorher = Z.detail.versionen.length;
    Z.detail = detail; Z.detailStand = stand;
    if (!versionAktuell()) { geheZu(Z.route.kunde, Z.route.projekt, Z.route.video); return; }
    renderKopf();
    const aktiv = document.activeElement === Z.dom.textarea;
    const entwurf = Z.dom.textarea ? Z.dom.textarea.value : "";
    renderSeite();
    if (Z.dom.textarea) { Z.dom.textarea.value = entwurf; if (aktiv) Z.dom.textarea.focus(); }
    if (detail.versionen.length > vorher) {
      const neu = detail.versionen[detail.versionen.length - 1];
      toast(`V${neu.nr} ist da${neu.notiz ? ": " + neu.notiz : ""}`, "gut", { text: "Öffnen", tu: () => geheZu(Z.route.kunde, Z.route.projekt, Z.route.video, neu.nr) });
    }
    ladeIndex(true).then(renderBaum).catch(() => {});
  }

  // ---------- Tastatur -------------------------------------------------------------------------------------------
  document.addEventListener("keydown", (ev) => {
    const ziel = ev.target;
    const tippt = ziel && (ziel.tagName === "TEXTAREA" || ziel.tagName === "INPUT");
    if (tippt) {
      if (ev.key === "Escape") { ziel.blur(); ev.preventDefault(); }
      else if (ev.key === "Enter" && (ev.metaKey || ev.ctrlKey) && ziel === Z.dom.textarea) { ev.preventDefault(); senden(); }
      return;
    }
    if (!Z.video || $("#autor-dialog").open) return;
    const fps = Math.max(1, Math.round(Z.fps));
    switch (ev.key) {
      case " ": ev.preventDefault(); umschalten(); break;
      case "ArrowLeft": ev.preventDefault(); schritt(ev.shiftKey ? -fps : -1); break;
      case "ArrowRight": ev.preventDefault(); schritt(ev.shiftKey ? fps : 1); break;
      case "Home": ev.preventDefault(); Z.video.pause(); springe(0); break;
      case "End": ev.preventDefault(); Z.video.pause(); springe(Z.frames - 1); break;
      case "i": case "I": setzeIn(); break;
      case "o": case "O": setzeOut(); break;
      case "c": case "C": ev.preventDefault(); if (Z.dom.textarea) Z.dom.textarea.focus(); break;
      case "m": case "M": stumm(); break;
      case "f": case "F": vollbild(); break;
      default:
        if (/^[1-9]$/.test(ev.key)) { const nr = parseInt(ev.key, 10); if (Z.detail.versionen.some((v) => v.nr === nr) && nr !== Z.versionNr) geheZu(Z.route.kunde, Z.route.projekt, Z.route.video, nr); }
    }
  });

  // ---------- Autor, NAS, Start ----------------------------------------------------------------------------------
  function autorAnzeigen() { $("#autor-knopf").textContent = Z.autor || "Name wählen"; }
  function autorDialog() {
    const dialog = $("#autor-dialog");
    $("#autor-frei").value = ["David", "Jan", "Sergio"].includes(Z.autor) ? "" : Z.autor;
    if (!dialog.open) dialog.showModal();
  }
  $("#autor-form").addEventListener("submit", (ev) => {
    const wert = ev.submitter && ev.submitter.value;
    const name = wert === "__frei" ? $("#autor-frei").value.trim() : wert;
    if (!name) { ev.preventDefault(); $("#autor-frei").focus(); return; }
    Z.autor = name.slice(0, 40);
    try { localStorage.setItem("niroReviewAutor", Z.autor); } catch (e) { /* privat */ }
    autorAnzeigen();
    if (Z.detail && Z.dom.seite) renderSeite();
  });
  $("#autor-dialog").addEventListener("cancel", (ev) => { if (!Z.autor) ev.preventDefault(); });
  $("#autor-knopf").addEventListener("click", autorDialog);
  $("#suche").addEventListener("input", (ev) => { Z.suche = ev.target.value; renderBaum(); if (Z.route.kunde && !Z.route.video) renderProjekt(); });

  async function nasPruefen() {
    const nas = $("#nas"), banner = $("#banner");
    try {
      const z = await api("zustand");
      nas.className = "nas " + (z.nas_verbunden ? "ok" : "weg");
      nas.title = (z.nas_verbunden ? "NAS verbunden · " : "NAS nicht verbunden · ") + z.wurzel + " · " + z.mac;
      banner.hidden = z.nas_verbunden;
      banner.textContent = z.nas_verbunden ? "" : "NAS nicht verbunden (" + z.wurzel + ") — Reviews erscheinen, sobald das NAS da ist.";
    } catch (e) { nas.className = "nas weg"; nas.title = "Server antwortet nicht"; }
  }

  async function navigieren() {
    Z.route = route();
    if (Z.pollTimer) { clearInterval(Z.pollTimer); Z.pollTimer = null; }
    if (Z.rvfc && Z.video) { try { Z.video.cancelVideoFrameCallback(Z.rvfc); } catch (e) { /* egal */ } Z.rvfc = null; }
    Z.video = null; Z.detail = null; Z.dom = {};
    if (!Z.index) await ladeIndex();
    renderBaum(); renderKrumen();
    const r = Z.route;
    if (!r.kunde) return renderStart();
    if (!r.video) return renderProjekt();
    await renderPlayer();
  }
  window.addEventListener("hashchange", () => navigieren().catch(fehler));
  autorAnzeigen();
  if (!Z.autor) autorDialog();
  nasPruefen();
  setInterval(nasPruefen, 10000);
  setInterval(() => { if (!Z.route.video) ladeIndex(true).then(() => { renderBaum(); if (Z.route.kunde) renderProjekt(); else renderStart(); }).catch(() => {}); }, 15000);
  navigieren().catch(fehler);
})();
```

- [ ] **Step 5: Syntax prüfen und committen**

```bash
node --check tools/review/ui/app.js
git add tools/review/ui
git commit -m "feat(review): Oberfläche — Übersicht, Player mit Frame-Timecode, Kommentare, Versionen (NIRO-CI)"
```

---

### Task 9: Dokumentation und Einbindung (WORKFLOW-Review.md, README.md, CLAUDE.md, SETUP.md)

**Files:**
- Create: `tools/review/WORKFLOW-Review.md`, `tools/review/README.md`
- Modify: `CLAUDE.md` (Funktionstabelle: neunte Zeile; Umgebung: Review-Server; Protokoll-Pflicht: Review-Ablage),
  `SETUP.md` (Schritt 8 „Review")
- Nicht anfassen: `tools/autocut/WORKFLOW-AutoCut.md` (fremde, unkommittierte Änderungen) — der Verweis steht in CLAUDE.md.

- [ ] **Step 1: WORKFLOW-Review.md**

```markdown file=tools/review/WORKFLOW-Review.md
# Review — Ablauf für Claude (seit 18.09.2026)

Spec `docs/superpowers/specs/2026-09-18-review-tool-design.md`. Werkzeug `tools/review/review.py` (Python ≥ 3.9,
ffmpeg). Oberfläche `http://localhost:4711` (LaunchAgent `de.niro.review`, `python3 tools/review/review.py installieren`).
Ablage auf dem NAS: `08_Claude Tools/NIRO Studio/review/<Kunde>/<Projekt>/<Video>/V<n>/` (video.mp4, thumb.jpg,
version.json, kommentare.json); lokaler Cache `~/Library/Caches/NIRO Review`. Dropbox Replay bleibt das Werkzeug für
**Kunden**-Runden (`tools/autocut/WORKFLOW-AutoCut.md` „Review in Replay"); NIRO Review ist der interne Kreislauf
User ↔ Claude.

    PY=python3
    RV="/Users/jansantos/NIRO Studio/tools/review/review.py"
    CHARGE="projects/<Kunde>/<Projekt>/<Charge>"

## Regel: jeder fertige Stand geht ins Review

Sobald ein Stand fertig ist, der begutachtet werden soll — Rohschnitt, Feinschnitt, Entwurf, finalisierter Export,
Animation **als Komposit** (Alpha-Overlays allein werden abgelehnt), Aftermovie —, wird er sofort abgelegt und der Link
im Chat genannt. Nicht ins Review: Kontaktbögen, Fotos, PDFs, reine Grafik-Alphas, Zwischenstände ohne Bild.

    "$PY" "$RV" hinzufuegen "$CHARGE" --datei "<MP4/MOV>" [--video "<Titel>"] [--notiz "<was ist das, was ist neu>"]
    "$PY" "$RV" hinzufuegen "$CHARGE" --ordner "<Ordner>" [--muster "*.mp4"] [--version 1] [--notiz "…"]

- Titel = Dateiname ohne Endung und ohne Versionsmarke (`– Entwurf v1`, `_V6`, ` V2`, `(Claude …)`); `--video` setzt
  ihn ausdrücklich. Ein Video = ein Titel über alle Versionen; V-Nummer ergibt sich (`--version` nur, wenn nötig).
- `--notiz` immer füllen: bei V1 was es ist, ab V2 was sich geändert hat (eine Zeile).
- Kopie oder Umkodierung (H.264/AAC) macht das Werkzeug; 4K bleibt 4K. Exit 1 = Eingabe (Datei, belegte Nummer, Alpha),
  Exit 2 = NAS oder ffmpeg fehlt → melden, nicht umgehen.
- Im Chat melden: Titel, V-Nummer, Link (`http://localhost:4711/#/<Kunde>/<Projekt>[/<Titel>]`), Notiz. Protokoll-Eintrag.

## Kommentare holen („Review: <Kunde>/<Projekt>[/<Video>]" oder „fertig")

    "$PY" "$RV" kommentare "$CHARGE" [--video "<Titel>"] [--alle]

- Exit 0 = neue Kommentare (Ausgabe zeigt sie, Export liegt in `<Charge>/Material/Feedback/<Datum> Review <Titel>
  V<n>/kommentare.md` + `.json`), Exit 1 = nichts Neues, Exit 2 = NAS fehlt.
- Bei Aufruf mit `<Kunde>/<Projekt>` (ohne Charge) werden alle Videos des Projekts geholt; die Charge steht in
  `kommentare.json` (`charge`). Ist die Version nicht abgeschlossen („noch offen"), trotzdem umsetzen — der User hat
  „fertig" gesagt; im Bericht erwähnen.
- `kommentare.md` lesen: `ID` (K1 …) ist die Referenz für Umsetzung, Protokoll und Chat; `TC` = Timecode in **dieser**
  Version, `Bereich` = Out; `Antworten` = Thread (User kann auf Rückfragen antworten); `Neu` = seit dem letzten Holen.
- Status-Werte: `offen` (User) · `umgesetzt` / `rueckfrage` (Claude) · `erledigt` (User hakt ab).

## Umsetzen

Regeln wie beim Replay-Ablauf: **Sofort umsetzen**, was eindeutig und werkzeugfähig ist (Pegel, Shot/Take tauschen,
Clip oder Grafik raus, Ausschnitt/Zoom/Begradigen, Grading einzelner Clips, Musik/SFX-Pegel, Untertitel, Grafik-Text).
**Handarbeit** (Verschieben/Rippeln in handbearbeiteten Timelines, Trims an Übergängen, Timing auf Musik) →
`rueckfrage` mit konkretem Vorschlag. **Rückfrage** bei Mehrdeutigkeit, mehreren Wegen, Konflikt mit festen Regeln
(max. 60 s, Sperren/Freigaben, nur Website-Infos, m/w/d, max. 2 Takes pro Sprecher, stärkste Aussage zuerst) — alle
Rückfragen gesammelt in einer Chat-Nachricht **und** als Status `rueckfrage` am Kommentar.

`umsetzung.json` (im Feedback-Ordner der Runde ablegen):

    {"K1": {"status": "umgesetzt", "antwort": "Schmatzer entfernt, Cut auf 00:00:02:03 gezogen", "tc_neu": "00:00:02:00"},
     "K2": {"status": "rueckfrage", "antwort": "Welche Stellen meinst du — nur die Drohne oder auch die Handkamera?"},
     "K3": {"status": "umgesetzt", "antwort": "Musik −3 dB ab 00:00:10:00"}}

- `tc_neu` (oder `frame_neu`) = Stelle in der **neuen** Version, wenn sie sich verschoben hat; die Oberfläche zeigt
  „→ V<n+1> 00:00:02:00" mit Sprung.
- Neue Version ablegen und Umsetzung in einem Schritt:

      "$PY" "$RV" hinzufuegen "$CHARGE" --datei "<neuer Render>" --video "<Titel>" --notiz "V2: …" --umsetzung "<umsetzung.json>"

  (`--umsetzung` bezieht sich auf die Vorversion; unbekannte IDs → Exit 1, nichts angelegt.) Ohne neuen Render (nur
  Rückfragen): `"$PY" "$RV" umsetzung "$CHARGE" --video "<Titel>" --version <n> --datei umsetzung.json`.
- Antwort in einen Thread (z. B. auf eine User-Antwort): `"$PY" "$RV" antworten "$CHARGE" --video "<Titel>" --version <n>
  --kommentar K2 --text "…"`.
- Bericht im Chat: je Kommentar-ID eine Zeile (umgesetzt / Rückfrage / Handarbeit), Link zur neuen Version, offene
  Rückfragen zuletzt. `umsetzung.md` im Feedback-Ordner wie beim Replay-Ablauf (Tabelle `Nr | ID | TC | Kommentar |
  Klasse | Änderung | TC neu`). Protokoll-Eintrag in `Protokoll.md` der Charge.

## Übersicht und Aufräumen

    "$PY" "$RV" status ["<Kunde>/<Projekt>" | "$CHARGE"]        Zustand je Video (review-offen / bei-claude / freigegeben)
    "$PY" "$RV" entfernen "$CHARGE" --video "<Titel>" [--version n]   nur nach Auftrag; landet in review/_papierkorb
    "$PY" "$RV" oeffnen "<Kunde>/<Projekt>"                       Browser öffnen

Nie: `video.mp4` einer Version ersetzen, kommentare.json von Hand kürzen, Versionen umbenennen. Ein neuer Render ist
immer eine neue Version.

## Zweit-Mac

Gleicher Code (git pull), gleiches NAS, eigener Cache und eigener LaunchAgent (`installieren` dort einmal ausführen).
Videos vom Zweit-Mac erscheinen am Studio-Mac sofort; Reviews macht der User am Studio-Mac. Nicht auf beiden Macs
gleichzeitig am selben Video arbeiten.

## Fehlerbilder

- „NAS nicht verbunden" (Exit 2 / Banner in der Oberfläche): NAS mounten, dann wiederholen; nichts lokal ablegen.
- „V2 existiert — nächste freie: V3": ohne `--version` aufrufen.
- „Alpha-Overlay ohne Bild darunter": Komposit rendern (Grafik über Schnitt) oder mit `--trotzdem` bewusst ablegen.
- Oberfläche leer nach Code-Update: LaunchAgent lädt den alten Prozess — `launchctl kickstart -k gui/$(id -u)/de.niro.review`.
- Video ruckelt beim Scrubben: Cache füllt sich beim ersten Abspielen (`~/Library/Caches/NIRO Review`); danach flüssig.
```

- [ ] **Step 2: README.md**

```markdown file=tools/review/README.md
# NIRO Review

Lokales Review-Werkzeug im NIRO-CI: Claude legt Videostände ab, du kommentierst im Browser an der Stelle im Video,
Claude setzt um und legt die nächste Version daneben. Ordnung Kunde → Projekt → Video → V1, V2 … auf dem NAS
(`08_Claude Tools/NIRO Studio/review/`), beide Macs sehen denselben Stand. Kunden-Feedback läuft weiter über
Dropbox Replay.

## Einrichten (einmal je Mac)

```bash
python3 tools/review/review.py installieren
```

Legt den LaunchAgent `de.niro.review` an (startet bei Anmeldung, startet nach Absturz neu), Adresse
`http://localhost:4711`, Log `~/Library/Logs/NIRO Review/server.log`. Braucht Python ≥ 3.9 und ffmpeg (SETUP.md).
Nach einem Code-Update (`git pull`) den Server neu starten:

```bash
launchctl kickstart -k gui/$(id -u)/de.niro.review
```

Entfernen: `python3 tools/review/review.py deinstallieren`. Ohne LaunchAgent: `python3 tools/review/review.py server`.

## Bedienen

- **Projekte** links, Videos als Karten mit Vorschaubild, Versions-Chip und Zustand (Review offen · bei Claude ·
  Freigegeben). Suchfeld filtert Projekte und Titel.
- **Player:** Timecode frame-genau, Scrubber mit Kommentar-Markern (Punkt = Stelle, Balken = Bereich), Versions-Pillen.
  Tippen im Kommentarfeld pausiert das Video; der Kommentar landet am aktuellen Frame. „Bereich bis hier" (oder `O`)
  macht einen Bereich, „Allgemein" einen Kommentar ohne Zeit.
- **Review abschließen** sperrt die Version für neue Kommentare und stellt sie auf „bei Claude" — dann im Chat
  „fertig" oder „Review: Kunde/Projekt" sagen. **Freigeben**, wenn das Video fertig ist.
- Ab V2 zeigt „Seit V1 geändert" jede Antwort von Claude mit Sprung zur neuen Stelle; dort abhaken („erledigt") oder auf
  Rückfragen antworten.
- Beim ersten Öffnen fragt die Seite nach dem Namen (David / Jan / Sergio / frei); er steht an jedem Kommentar.

## Tasten

| Taste | Wirkung |
|---|---|
| Leertaste | Play / Pause |
| ← / → | ein Frame zurück / vor (mit ⇧ eine Sekunde) |
| Home / End | Anfang / Ende |
| I / O | Bereich: In / Out auf den aktuellen Frame |
| C | Kommentarfeld fokussieren (pausiert) |
| ⌘↩ / Strg+↩ | Kommentar senden |
| Esc | Kommentarfeld verlassen |
| M / F | stumm / Vollbild |
| 1–9 | Version wechseln |

## Für Claude

Ablauf und Befehle: `WORKFLOW-Review.md`. Kurz: `hinzufuegen` (Version ablegen), `kommentare` (holen, Export in
`Material/Feedback/`), `umsetzung`/`antworten` (Status und Antworten), `status`, `entfernen` (Papierkorb).

## Tests

```bash
tools/autocut/venv/bin/python -m pytest tools/review/tests -q
```
```

- [ ] **Step 3: CLAUDE.md anpassen**

Drei Änderungen mit Edit (exakte Stellen):

1. Erste Zeile: `Master-Werkzeug von NIRO Media: acht Funktionen, ein Projektsystem, eine Session.` →
   `Master-Werkzeug von NIRO Media: neun Funktionen, ein Projektsystem, eine Session.`
2. Funktionstabelle, nach der Zeile „Tagesbericht" eine neue Zeile:
   `| „Review: <Kunde>/<Projekt>[/<Video>]" · „fertig" nach einem Review | Lokales Review-Werkzeug (http://localhost:4711, Ablage auf dem NAS, beide Macs): Kommentare holen, umsetzen, V+1 ablegen. **Jeder fertige Review-Stand** (Rohschnitt, Feinschnitt, Entwurf, Export, Animation als Komposit) wird sofort per `review.py hinzufuegen` abgelegt und der Link im Chat genannt; Replay nur noch für Kundenrunden | `tools/review/WORKFLOW-Review.md` |`
3. Abschnitt „Umgebung", neuer Punkt nach „Resolve (MCP)":
   `- **Review (review):** `python3 tools/review/review.py` (Standardbibliothek + ffmpeg); Server als LaunchAgent `de.niro.review` auf Port 4711 (`installieren` einmal je Mac, nach `git pull` `launchctl kickstart -k gui/$(id -u)/de.niro.review`); Ablage `<NAS>/08_Claude Tools/NIRO Studio/review/`, Cache `~/Library/Caches/NIRO Review`.`

Außerdem im Absatz „Protokoll-Pflicht" den Satz ergänzen: „Review-Ablagen (Titel, Version, Link) und geholte
Kommentar-Runden gehören in denselben Eintrag."

- [ ] **Step 4: SETUP.md — Schritt 8 vor „## Arbeiten mit dem Repo"**

```markdown
## 8. Review

```bash
python3 tools/review/review.py installieren
```

Richtet den Review-Server als LaunchAgent ein (`http://localhost:4711`, startet bei Anmeldung). Braucht ffmpeg aus
Schritt 3 und das verbundene NAS; Ablage und Bedienung in [tools/review/README.md](tools/review/README.md).
```

- [ ] **Step 5: Commit**

```bash
git add tools/review/WORKFLOW-Review.md tools/review/README.md CLAUDE.md SETUP.md
git commit -m "docs(review): Ablauf für Claude, README, neunte Funktion in CLAUDE.md, SETUP-Schritt"
```

---

### Task 10: Inbetriebnahme — LaunchAgent, Sichtprüfung im Browser, erste Befüllung Dold

**Files:**
- Keine neuen Quelldateien; Nacharbeiten an `tools/review/ui/*` oder `server.py` nach der Sichtprüfung (je Fix ein
  Commit). Memory-Datei `~/.claude/projects/-Users-jansantos-NIRO-Studio/memory/niro-review.md` + Zeile in `MEMORY.md`.

- [ ] **Step 1: Alle Tests**

Run: `tools/autocut/venv/bin/python -m pytest tools/review/tests -q` — erwartet: alle grün.
Zusätzlich mit Apple-Python 3.9: `/usr/bin/python3 -c "import sys; sys.path.insert(0, 'tools/review/src'); import niro_review.cli, niro_review.server; print('3.9 ok')"`.

- [ ] **Step 2: LaunchAgent installieren und prüfen**

```bash
python3 tools/review/review.py installieren
sleep 2; curl -s http://localhost:4711/api/zustand; echo; tail -n 5 ~/Library/Logs/NIRO\ Review/server.log
```
Erwartet: JSON mit `"nas_verbunden": true`, `"wurzel": "/Volumes/NIRO NAS/…/NIRO Studio/review"`.

- [ ] **Step 3: Erste Befüllung Dold (V1 = Entwürfe vom 17.09.)**

```bash
python3 tools/review/review.py hinzufuegen "projects/Dold/Recruiting/2026-07 Dreh 27-28.07" \
  --ordner "projects/Dold/Recruiting/2026-07 Dreh 27-28.07/Ergebnisse/Export/Entwürfe Resolve 2026-09-17" \
  --muster "*.mp4" --version 1 --notiz "Entwurf v1 vom 17.09. — Feedback vom 18.09. kam im Chat (billig geschnitten, Wackler, Gelb, Karten); v2 folgt"
python3 tools/review/review.py status "Dold/Recruiting"
```
Erwartet: 24 Videos `Dold 02 … Dold 26` als V1 (Kopie, 2160×3840, 25 fps), Link `http://localhost:4711/#/Dold/Recruiting`.
Liegen v2-Renders vor (`Ergebnisse/Export/…v2…`), als V2 mit Notiz nachlegen — sonst offen lassen und im Bericht nennen.

- [ ] **Step 4: Sichtprüfung im Browser-Fenster der App** (preview_start `{url: "http://localhost:4711"}`)

1. Startseite: Projektkarte „Dold · Recruiting", Baum links, NAS-Punkt grün, Namensabfrage → „Jan".
2. Projekt: 24 Karten mit Vorschaubild, Chip V1, Zustand „Review offen", sortiert 02 … 26.
3. Player (Dold 02): 9:16-Video spielt, Timecode läuft frame-genau (`requestVideoFrameCallback`), ←/→ steppen,
   Scrubber springt; Kommentar am Frame anlegen (Tippen pausiert), Bereich mit I/O, allgemeiner Kommentar; Marker
   erscheinen; Erledigt/Wieder öffnen; Bearbeiten/Löschen (eigene); „Review abschließen" sperrt die Eingabe, Chip
   „bei Claude", Toast; „Wieder öffnen".
4. CLI-Roundtrip: `review.py kommentare "projects/Dold/…"` liefert die Testkommentare als `kommentare.md`;
   `umsetzung.json` mit K1 umgesetzt + tc_neu → `hinzufuegen … --version 2 --umsetzung` (Testrender = dieselbe Datei) →
   Oberfläche: Toast „V2 ist da", Block „Seit V1 geändert" mit Sprung; Haken „erledigt". Danach V2 wieder entfernen
   (`entfernen --version 2`) und Testkommentare löschen, damit Dold sauber bei V1 steht.
5. Konsole ohne Fehler (`read_console_messages`), Netzwerk: `/media/...` mit 206.
6. Screenshot Übersicht + Player für den Bericht.

- [ ] **Step 5: Memory und Protokoll**

- Memory `niro-review.md` (type project): Zweck, Ablage-Pfade, Befehle, LaunchAgent, Regel „jeder fertige Stand ins
  Review", Stand der Dold-Befüllung; Zeile in `MEMORY.md` (kurz, < 200 Zeichen).
- `Protokoll.md` der Dold-Charge: Eintrag „Review-Ablage V1 (24 Videos), Link".
- Vorher/nachher `sh tools/studio_abgleich.sh --charge "projects/Dold/Recruiting/2026-07 Dreh 27-28.07"`.

- [ ] **Step 6: Abschluss-Commit und Bericht**

```bash
git status --short   # nur eigene Dateien stagen
git log --oneline -12
```
Bericht an den User: Link, was liegt, was offen ist (Zweit-Mac `installieren`, v2-Renders, Merge-Stand).

## Selbstprüfung des Plans

- Spec-Abdeckung: Kreislauf (Task 7 + 9), Ablage/Cache/NFC (1, 7), Datenmodell (2, 4), Befehle (7), Export (4),
  Server/API/Range/503 (5), Oberfläche inkl. Tasten/Seit-Block/Autor/Aktualisierung (8), Zweit-Mac (9 Doku, 6
  LaunchAgent), LaunchAgent (6), Fehlerbehandlung (1, 5, 7), Tests (1–7), Einbindung (9), Erste Befüllung (10).
  Nicht umgesetzt (bewusst, laut Spec „Nicht-Ziel"): Zeichnen, Vergleich, Upload im Browser, Login.
- Abweichung von der Spec: `tools/autocut/WORKFLOW-AutoCut.md` wird nicht geändert (fremde unkommittierte Änderungen);
  die Regel steht in CLAUDE.md. Kommentar-Feld `frame_neu` (int) ergänzt `tc_neu` (Text).
- Typen: `Ziel(kunde, projekt, charge)`, `version_anlegen(...)` → dict, `umsetzung_anwenden(daten, umsetzung, fps)` →
  list, API-Felder `kunde/projekt/video/version/autor/text/frame/bis_frame/id/status/loeschen` überall gleich.
