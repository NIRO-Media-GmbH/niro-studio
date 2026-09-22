# Produkt-Durchstich, Teil 1: Fundament und Rohschnitt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein neues, privates Repo, in dem der AutoCut-Kern ohne die NIRO-Ordnerkonvention auf einem beliebigen Projektordner läuft, gesteuert über einen lokalen Server mit Job-Modell und eine Brücke, die DaVinci Resolve bedient — nachgewiesen durch eine Rohschnitt-Timeline, die aus einer vorhandenen Cutlist über Server und Brücke entsteht.

**Architecture:** Drei Pakete in einem Repo. `core/` enthält die aus NIRO Studio übernommenen Pakete `niro_autocut` und `niro_transcribe` **unter ihren heutigen Namen**, damit die 10.439 Zeilen Tests unverändert laufen; die einzige inhaltliche Änderung ist eine dritte Konstruktor-Methode `Charge.open_produkt`, die den Zwang zur Ordnerkette `projects/<Kunde>/<Projekt>/<Charge>` aufhebt. `server/` ist eine FastAPI-Anwendung mit SQLite, die Projekte, Jobs und Schritte verwaltet und Aufträge an Brücken verteilt. `bridge/` ist ein Dauerläufer auf dem Rechner des Kunden, der Aufträge abholt, die vorhandenen Kernfunktionen ausführt und Ergebnisse zurückmeldet. Dazwischen steht das NLE-neutrale `schnittmodell.py`, in das jede Timeline-Entscheidung fließt.

**Tech Stack:** Python 3.12, pytest. Server: FastAPI, uvicorn, SQLite (stdlib `sqlite3`), httpx für Tests. Kern: numpy, scipy, pillow, rapidfuzz, pyyaml, python-dotenv, anthropic (wie das heutige AutoCut-venv). Extern: ffmpeg 9, DaVinci Resolve Studio 21.1. Kein Docker, kein Postgres, keine Cloud in diesem Teil.

Specs: `docs/superpowers/specs/2026-09-22-autocut-standalone-produkt-design.md` (Architektur-Grundsatz, Kosten, Geschäftsmodell) und `docs/superpowers/specs/2026-09-22-produkt-oberflaeche-plattform-design.md` (Abschnitte 2 Architektur, 13 Entscheidungen und 7-Tage-Plan).

## Global Constraints

- **Arbeitsverzeichnis:** `~/niro-produkt`. Der Ordnername ist bewusst neutral, weil der Produktname am 22.09. noch nicht entschieden war. Er steht nur in `README.md` und `pyproject.toml` und wird beim Umbenennen mit `git mv` plus zwei Zeilen geändert. **Nie** in `~/NIRO Studio` schreiben — dieses Repo bleibt unangetastet.
- **Python-Aufruf immer** `~/niro-produkt/venv/bin/python`. Ein gemeinsames venv für alle drei Pakete. Anlegen in Task 1.
- **Tests:** `cd ~/niro-produkt && venv/bin/python -m pytest -q`. Ein Task gilt erst als fertig, wenn der gesamte Testlauf grün ist, nicht nur der neue Test.
- **Deutsch** in Code-Kommentaren, Docstrings, Feldnamen, Fehlermeldungen und Commit-Texten — wie im übernommenen Kern. Zeilen höchstens 125 Zeichen.
- **Fehler** als `AutoCutError` (Kern) bzw. `ProduktError` (Server, Brücke) mit handlungsleitender deutscher Meldung: was ist passiert, was soll der Nutzer tun.
- **Bildraten immer als `fractions.Fraction`**, nie als Fließkommazahl. 23,976 ist `Fraction(24000, 1001)`, 25 ist `Fraction(25, 1)`. Grund: Die OpenTimelineIO-Kernbibliothek hat offene Rundungsfehler bei 23,976 und 29,97 (Issues 476, 830, 876), und FCP7-XML kodiert die Rate als Ganzzahl plus NTSC-Flag.
- **Der Kern wird so wenig wie möglich verändert.** Erlaubt sind additive Änderungen (neue Methoden, neue optionale Felder mit Vorgabewert). Nicht erlaubt: Umbenennen vorhandener Funktionen, Ändern von Signaturen, Löschen von Tests. Jede Kernänderung braucht einen Test im neuen Repo.
- **Resolve-Regeln gelten unverändert** (`tools/resolve/WORKFLOW-Resolve.md` in NIRO Studio): nur neue Bins und Timelines anlegen, nie schreiben während der Nutzer abspielt, nach dem Bau `SaveProject`, am Ende die Timeline des Nutzers wieder aktivieren. Der Projektname im Auftrag ist die Schreibfreigabe: weicht der Name des offenen Resolve-Projekts ab, bricht die Brücke ab.
- **Keine Geheimnisse im Repo.** API-Schlüssel kommen aus `~/niro-produkt/.env` (in `.gitignore`). In diesem Teil wird noch kein Schlüssel gebraucht.
- **Commits:** Nur die Dateien der jeweiligen Task stagen, nie `git add -A`. Commit-Text deutsch mit Präfix `feat:`, `test:`, `chore:` oder `docs:`, Abschluss `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- **Testprojekt:** `~/niro-produkt/testdaten/taxodia/` ist eine Kopie ausgewählter Dateien aus `projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/` (Task 1 legt sie an). Kopiert werden nur JSON- und Markdown-Dateien, keine Medien. Medien bleiben am Originalort und werden über `path_map` gefunden.

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `pyproject.toml` | Ein Projekt mit drei Paketen unter `core/`, `server/`, `bridge/`; pytest-Konfiguration |
| `core/autocut/` | Kopie von `tools/autocut/` aus NIRO Studio: `src/niro_autocut/`, `tests/`, `prompts/`, `defaults.yaml`, `profile/` |
| `core/transcribe/` | Kopie von `tools/transcribe/` aus NIRO Studio: `src/niro_transcribe/`, `tests/` |
| `core/autocut/src/niro_autocut/charge.py` | **Änderung:** neue Klassenmethode `open_produkt`, neue Felder `kunde_name`/`projekt_name`, Eigenschaften `kunde`/`projekt` lesen sie |
| `core/autocut/src/niro_autocut/schnittmodell.py` (neu) | NLE-neutrales Schnittmodell: `Rate`, `Schnitt`, `Marke`, `Schnittmodell`; Umwandlung aus `TimelinePlan` |
| `server/src/produkt_server/fehler.py` (neu) | `ProduktError` und die Zuordnung auf HTTP-Codes |
| `server/src/produkt_server/ablage.py` (neu) | SQLite-Schema und Zugriff: Organisationen, Nutzer, Geräte, Projekte, Jobs, Schritte |
| `server/src/produkt_server/modell.py` (neu) | Datenklassen `Job`, `Schritt`, `Auftrag` und ihre JSON-Form |
| `server/src/produkt_server/auth.py` (neu) | Einladungsliste, Anmeldung, Token, Geräteprüfung |
| `server/src/produkt_server/api.py` (neu) | FastAPI-Anwendung: Projekte, Jobs, Auftragsabholung, Ergebnismeldung, Fortschritt |
| `server/src/produkt_server/ablauf.py` (neu) | Ablaufsteuerung: aus einer Job-Art die Schrittfolge bauen, Schritte weiterschalten |
| `bridge/src/produkt_bruecke/fehler.py` (neu) | `BrueckeError` |
| `bridge/src/produkt_bruecke/klient.py` (neu) | HTTP-Klient gegen den Server: anmelden, Auftrag holen, Ergebnis melden |
| `bridge/src/produkt_bruecke/schritte.py` (neu) | Schritt-Ausführer: `vorbereiten`, `synchronisieren`, `pruefen`, `bauen` |
| `bridge/src/produkt_bruecke/laeufer.py` (neu) | Dauerläufer: Schleife über Aufträge, Fehlerbehandlung, Abbruch |
| `bridge/scripts/bruecke.py` (neu) | CLI-Einstieg der Brücke |
| `server/scripts/serve.py` (neu) | CLI-Einstieg des Servers |
| `tests/` je Paket | pytest, ohne Resolve, ohne Netz, ohne API-Schlüssel |
| `testdaten/taxodia/` | Kopierte JSON- und Markdown-Dateien des Testprojekts |
| `README.md` | Einrichtung, Start, Testlauf |

---

### Task 1: Repo anlegen, Kern übernehmen, Tests grün

**Files:**
- Create: `~/niro-produkt/` mit `pyproject.toml`, `.gitignore`, `README.md`
- Create: `~/niro-produkt/core/autocut/` (Kopie), `~/niro-produkt/core/transcribe/` (Kopie)
- Create: `~/niro-produkt/testdaten/taxodia/`
- Test: der übernommene Testbestand beider Pakete

**Interfaces:**
- Consumes: nichts
- Produces: importierbare Pakete `niro_autocut` und `niro_transcribe`; venv unter `~/niro-produkt/venv`; Testprojekt unter `~/niro-produkt/testdaten/taxodia`

- [ ] **Step 1: Repo und venv anlegen**

```bash
mkdir -p ~/niro-produkt && cd ~/niro-produkt
git init -b main
python3.12 -m venv venv
venv/bin/pip install --upgrade pip
```

- [ ] **Step 2: Kern kopieren, ohne venv, Cache und Arbeitsdateien**

```bash
cd ~/niro-produkt
mkdir -p core
rsync -a --exclude venv --exclude __pycache__ --exclude '.pytest_cache' --exclude '*.pyc' \
  --exclude '.env' --exclude 'work' \
  "$HOME/NIRO Studio/tools/autocut/" core/autocut/
rsync -a --exclude venv --exclude __pycache__ --exclude '.pytest_cache' --exclude '*.pyc' \
  --exclude '.env' \
  "$HOME/NIRO Studio/tools/transcribe/" core/transcribe/
```

- [ ] **Step 3: `pyproject.toml` schreiben**

```toml
[project]
name = "niro-produkt"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "numpy>=2.0",
    "scipy>=1.14",
    "pillow>=11.0",
    "rapidfuzz>=3.9",
    "requests>=2.31",
    "python-dotenv>=1.0",
    "pyyaml>=6.0",
    "anthropic>=1.0",
    "fastapi>=0.115",
    "uvicorn>=0.32",
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
pythonpath = [
    "core/autocut/src",
    "core/transcribe/src",
    "server/src",
    "bridge/src",
]
testpaths = ["core/autocut/tests", "core/transcribe/tests", "server/tests", "bridge/tests"]
```

- [ ] **Step 4: `.gitignore` schreiben**

```gitignore
venv/
__pycache__/
*.pyc
.pytest_cache/
.env
*.db
core/autocut/work/
testdaten/*/_studio/
```

- [ ] **Step 5: Abhängigkeiten installieren**

```bash
cd ~/niro-produkt
mkdir -p server/src/produkt_server server/tests server/scripts \
         bridge/src/produkt_bruecke bridge/tests bridge/scripts
touch server/src/produkt_server/__init__.py bridge/src/produkt_bruecke/__init__.py
venv/bin/pip install -e ".[dev]"
```

Die leeren Ordner sind nötig, weil `testpaths` in `pyproject.toml` sie nennt und pytest sonst mit
`ERROR: file or directory not found` abbricht.

- [ ] **Step 6: Testlauf zur Bestandsaufnahme**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest -q`
Expected: Der übernommene Bestand läuft. Schlagen Tests fehl, liegt es fast immer an einem der beiden Punkte: ein Test erwartet die Datei `defaults.yaml` relativ zu `TOOL_ROOT` (`core/autocut/defaults.yaml` muss vorhanden sein), oder ein Test erwartet den Pfad `tools/transcribe/src` über eine `.pth`-Datei (die durch die `pythonpath`-Einträge in `pyproject.toml` ersetzt wird). Beides ohne Änderung an Testdateien lösen.

- [ ] **Step 7: Testprojekt kopieren**

```bash
cd ~/niro-produkt
Q="$HOME/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09"
mkdir -p testdaten/taxodia/_studio/autocut testdaten/taxodia/_studio/Plaene
cp "$Q/_intern/autocut/cutlist.json"  testdaten/taxodia/_studio/autocut/ 2>/dev/null || true
cp "$Q/_intern/autocut/media.json"    testdaten/taxodia/_studio/autocut/ 2>/dev/null || true
cp "$Q/_intern/autocut/sync.json"     testdaten/taxodia/_studio/autocut/ 2>/dev/null || true
cp "$Q/_intern/utterances.json"       testdaten/taxodia/_studio/ 2>/dev/null || true
cp "$Q/_intern/transcripts_index.json" testdaten/taxodia/_studio/ 2>/dev/null || true
cp "$Q"/Ergebnisse/O-Ton-Pläne/video-*.md testdaten/taxodia/_studio/Plaene/ 2>/dev/null || true
ls -la testdaten/taxodia/_studio testdaten/taxodia/_studio/autocut
```

Fehlt eine Datei, im Protokoll der Charge nachsehen, welcher Lauf sie erzeugt hat, und den Pfad korrigieren. Ohne `cutlist.json` und `media.json` ist Task 6 nicht ausführbar.

- [ ] **Step 8: README schreiben**

```markdown
# NIRO Produkt (Arbeitstitel)

Desktop-Werkzeug für Videoagenturen: Aus Interview-Material und Konzept entsteht eine
abnahmefähige Timeline in DaVinci Resolve.

Drei Teile:
- `core/`   Kern aus NIRO Studio (Medien, Sync, Cutlist, Timeline, Resolve, Kanten, Telemetrie)
- `server/` Job-Steuerung und Urteile (FastAPI, SQLite)
- `bridge/` Dauerläufer auf dem Kundenrechner, bedient Medien und Resolve

## Einrichtung

    python3.12 -m venv venv
    venv/bin/pip install -e ".[dev]"
    venv/bin/python -m pytest -q

## Start

    venv/bin/python server/scripts/serve.py
    venv/bin/python bridge/scripts/bruecke.py --server http://127.0.0.1:8720
```

- [ ] **Step 9: Commit**

```bash
cd ~/niro-produkt
git add pyproject.toml .gitignore README.md core testdaten
git commit -m "chore: Repo angelegt, AutoCut- und Transcribe-Kern übernommen, Tests grün

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Projektordner ohne NIRO-Konvention

Heute verlangt `Charge.open` die Kette `projects/<Kunde>/<Projekt>/<Charge>`, den Ordner `Ergebnisse/O-Ton-Pläne` und die Datei `_intern/utterances.json`. Im Produkt wählt der Kunde einen beliebigen Ordner; alle Arbeitsdateien liegen unter `_studio/`.

**Files:**
- Modify: `core/autocut/src/niro_autocut/charge.py`
- Test: `core/autocut/tests/test_charge_produkt.py`

**Interfaces:**
- Consumes: `Charge`, `AutoCutError`, `load_config` aus `niro_autocut.charge`
- Produces:
  - `Charge.open_produkt(root: str | Path, kunde: str = "", projekt: str = "") -> Charge`
  - neue Felder `kunde_name: str = ""` und `projekt_name: str = ""` auf `Charge`
  - die Eigenschaften `Charge.kunde` und `Charge.projekt` geben die Felder zurück, wenn sie gesetzt sind, sonst wie bisher die Ordnernamen

- [ ] **Step 1: Alle Stellen finden, die von der Ordnerkette abhängen**

```bash
cd ~/niro-produkt/core/autocut
grep -rn "parents\[1\]\|parents\[2\]\|O-Ton-Pläne\|utterances.json\|_intern" src/niro_autocut/ | grep -v "^src/niro_autocut/charge.py"
```

Die Treffer notieren. Sie dürfen in dieser Task nicht geändert werden — sie greifen alle über `Charge`-Felder zu und funktionieren dadurch automatisch. Ist ein Treffer dabei, der einen Pfad selbst zusammensetzt, statt ein `Charge`-Feld zu benutzen, gehört er in diese Task und wird auf das passende Feld umgestellt.

- [ ] **Step 2: Failing test schreiben**

```python
# core/autocut/tests/test_charge_produkt.py
"""Projektordner des Produkts: beliebiger Ordner, Arbeitsdateien unter _studio/."""
from pathlib import Path

import pytest

from niro_autocut.charge import AutoCutError, Charge


def test_open_produkt_akzeptiert_beliebigen_ordner(tmp_path: Path):
    root = tmp_path / "Irgendein Dreh"
    root.mkdir()
    ch = Charge.open_produkt(root, kunde="Muster GmbH", projekt="Imagefilm")

    assert ch.root == root.resolve()
    assert ch.intern == root.resolve() / "_studio"
    assert ch.autocut == root.resolve() / "_studio" / "autocut"
    assert ch.ergebnisse == root.resolve() / "_studio" / "Ergebnisse"
    assert ch.plaene == root.resolve() / "_studio" / "Plaene"
    assert ch.protokoll == root.resolve() / "_studio" / "Protokoll.md"
    assert ch.kunde == "Muster GmbH"
    assert ch.projekt == "Imagefilm"


def test_open_produkt_legt_arbeitsordner_an(tmp_path: Path):
    root = tmp_path / "Dreh"
    root.mkdir()
    ch = Charge.open_produkt(root)

    assert ch.autocut.is_dir()
    assert ch.work.is_dir()
    assert ch.ergebnisse.is_dir()


def test_open_produkt_schreibt_nur_unter_studio(tmp_path: Path):
    root = tmp_path / "Dreh"
    root.mkdir()
    ch = Charge.open_produkt(root)

    ch.assert_writable(ch.autocut / "cutlist.json")
    ch.assert_writable(ch.protokoll)
    with pytest.raises(AutoCutError, match="Schreiben verweigert"):
        ch.assert_writable(root / "Material" / "Audio" / "kaputt.wav")


def test_open_produkt_meldet_fehlenden_ordner(tmp_path: Path):
    with pytest.raises(AutoCutError, match="nicht gefunden"):
        Charge.open_produkt(tmp_path / "gibtsnicht")


def test_kunde_und_projekt_fallen_auf_ordnernamen_zurueck(tmp_path: Path):
    root = tmp_path / "projects" / "Kunde A" / "Projekt B" / "Charge C"
    root.mkdir(parents=True)
    ch = Charge.open_produkt(root)

    assert ch.kunde == "Kunde A"
    assert ch.projekt == "Projekt B"
```

- [ ] **Step 3: Test laufen lassen, Fehlschlag prüfen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest core/autocut/tests/test_charge_produkt.py -q`
Expected: FAIL mit `AttributeError: type object 'Charge' has no attribute 'open_produkt'`

- [ ] **Step 4: Felder und Eigenschaften ergänzen**

In `core/autocut/src/niro_autocut/charge.py` die Datenklasse um zwei Felder erweitern. Sie stehen hinter allen vorhandenen Feldern und haben Vorgabewerte, damit jeder bestehende Aufruf unverändert funktioniert:

```python
@dataclass
class Charge:
    root: Path
    intern: Path
    autocut: Path
    work: Path
    ergebnisse: Path
    plaene: Path
    protokoll: Path
    config: dict = field(default_factory=dict)
    zusatz_schreibbereiche: tuple[Path, ...] = ()
    kunde_name: str = ""
    projekt_name: str = ""
```

Die beiden Eigenschaften lesen zuerst die Felder:

```python
    @property
    def kunde(self) -> str:
        """Kundenname: aus dem Projekt gesetzt, sonst der Ordner über dem Projektordner."""
        if self.kunde_name:
            return self.kunde_name
        return self.root.parents[1].name if len(self.root.parents) >= 2 else ""

    @property
    def projekt(self) -> str:
        """Projektname: aus dem Projekt gesetzt, sonst der übergeordnete Ordner."""
        if self.projekt_name:
            return self.projekt_name
        return self.root.parent.name if len(self.root.parents) >= 1 else ""
```

- [ ] **Step 5: `open_produkt` schreiben**

Hinter `open_basis` einfügen:

```python
    @classmethod
    def open_produkt(cls, root: str | Path, kunde: str = "", projekt: str = "") -> "Charge":
        """Projektordner des Produkts: beliebiger Ordner, alle Arbeitsdateien unter ``_studio/``.

        Anders als ``open``/``open_basis`` verlangt diese Fassung weder die Ordnerkette
        ``projects/<Kunde>/<Projekt>/<Charge>`` noch einen vorhandenen Cutter-Plan. Kunde und Projekt
        kommen aus den Projektdaten des Servers; fehlen sie, dienen die Ordnernamen als Rückfall.
        Geschrieben wird ausschließlich unter ``_studio/``."""
        root = Path(root).expanduser().resolve()
        if not root.is_dir():
            raise AutoCutError(f"Projektordner nicht gefunden: {root}\n"
                               f"Den Ordner im Programm neu auswählen oder das Laufwerk verbinden.")
        studio = root / "_studio"
        ch = cls(root=root, intern=studio, autocut=studio / "autocut", work=studio / "autocut" / "work",
                 ergebnisse=studio / "Ergebnisse", plaene=studio / "Plaene",
                 protokoll=studio / "Protokoll.md", config=load_config(root),
                 zusatz_schreibbereiche=(studio,), kunde_name=kunde, projekt_name=projekt)
        for d in (ch.autocut, ch.work, ch.ergebnisse, ch.plaene):
            d.mkdir(parents=True, exist_ok=True)
        return ch
```

- [ ] **Step 6: Tests laufen lassen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest -q`
Expected: PASS, auch der gesamte übernommene Bestand. Schlägt ein alter Test fehl, wurde eine Signatur verändert statt ergänzt — zurücknehmen und nur additiv arbeiten.

- [ ] **Step 7: Commit**

```bash
cd ~/niro-produkt
git add core/autocut/src/niro_autocut/charge.py core/autocut/tests/test_charge_produkt.py
git commit -m "feat(core): Projektordner ohne NIRO-Ordnerkonvention (Charge.open_produkt)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: NLE-neutrales Schnittmodell

Jede Timeline-Entscheidung fließt in ein Modell, das unabhängig vom Schnittprogramm ist. Resolve baut daraus per API, spätere Adapter schreiben daraus FCP7-XML oder FCPXML, und der eigene Vorschau-Render liest dasselbe Modell.

**Files:**
- Create: `core/autocut/src/niro_autocut/schnittmodell.py`
- Test: `core/autocut/tests/test_schnittmodell.py`

**Interfaces:**
- Consumes: `niro_autocut.timeline_model.TimelinePlan`, `Item`, `MarkerSpec`; `niro_autocut.charge.AutoCutError`
- Produces:
  - `Rate.von_fliesskomma(fps: float) -> Rate`, `Rate.als_bruch() -> Fraction`, `Rate.ntsc: bool`, `Rate.zaehler: int`, `Rate.nenner: int`
  - `Schnitt(spur, quelle, quelle_in_s, quelle_out_s, ziel_in_s, tempo=1.0, pegel_db=0.0, aktiv=True, name="")`
  - `Marke(ziel_s, name, farbe, notiz="", dauer_s=0.0)`
  - `Schnittmodell(rate, breite, hoehe, start_tc, schnitte, marken, spurnamen)` mit `to_dict`, `from_dict`, `dauer_s`
  - `aus_timeline_plan(plan: TimelinePlan, rate: Rate, breite: int, hoehe: int, start_tc: str) -> Schnittmodell`

- [ ] **Step 1: Failing test schreiben**

```python
# core/autocut/tests/test_schnittmodell.py
"""NLE-neutrales Schnittmodell: Raten als Brüche, Schnitte, Marken, Umwandlung aus dem TimelinePlan."""
from fractions import Fraction

import pytest

from niro_autocut.schnittmodell import Marke, Rate, Schnitt, Schnittmodell


def test_rate_ganzzahlig():
    r = Rate.von_fliesskomma(25.0)
    assert (r.zaehler, r.nenner) == (25, 1)
    assert r.ntsc is False
    assert r.als_bruch() == Fraction(25, 1)


def test_rate_ntsc_2397():
    r = Rate.von_fliesskomma(23.976)
    assert (r.zaehler, r.nenner) == (24000, 1001)
    assert r.ntsc is True
    assert r.als_bruch() == Fraction(24000, 1001)


def test_rate_ntsc_2997_und_5994():
    assert Rate.von_fliesskomma(29.97).als_bruch() == Fraction(30000, 1001)
    assert Rate.von_fliesskomma(59.94).als_bruch() == Fraction(60000, 1001)


def test_rate_unbekannte_rate_meldet_fehler():
    with pytest.raises(ValueError, match="Bildrate"):
        Rate.von_fliesskomma(17.3)


def test_rate_frames_und_sekunden_sind_umkehrbar():
    r = Rate.von_fliesskomma(23.976)
    assert r.frames(1.0) == 24
    assert r.sekunden(24) == pytest.approx(1.001, abs=1e-6)


def test_schnittmodell_runde_um_json():
    m = Schnittmodell(
        rate=Rate.von_fliesskomma(25.0), breite=3840, hoehe=2160, start_tc="01:00:00:00",
        schnitte=[Schnitt(spur="V1", quelle="/a/FX3_0001.MP4", quelle_in_s=2.0, quelle_out_s=5.0,
                          ziel_in_s=0.0, pegel_db=-3.0, name="Beat 1")],
        marken=[Marke(ziel_s=0.0, name="Beat 1", farbe="Blue", notiz="Hook")],
        spurnamen={"V1": "Kamera A", "A1": "Ton A"})

    zurueck = Schnittmodell.from_dict(m.to_dict())

    assert zurueck.rate.als_bruch() == Fraction(25, 1)
    assert zurueck.schnitte[0].quelle_out_s == 5.0
    assert zurueck.schnitte[0].pegel_db == -3.0
    assert zurueck.marken[0].farbe == "Blue"
    assert zurueck.spurnamen["V1"] == "Kamera A"


def test_dauer_ist_das_ende_des_letzten_schnitts():
    m = Schnittmodell(
        rate=Rate.von_fliesskomma(25.0), breite=1920, hoehe=1080, start_tc="01:00:00:00",
        schnitte=[Schnitt("V1", "/a.mp4", 0.0, 2.0, 0.0), Schnitt("V3", "/b.mp4", 5.0, 9.0, 2.0)],
        marken=[], spurnamen={})

    assert m.dauer_s == pytest.approx(6.0)


def test_tempo_streckt_die_zieldauer():
    s = Schnitt("V3", "/b.mp4", 0.0, 2.0, 0.0, tempo=2.0)
    assert s.ziel_dauer_s == pytest.approx(4.0)
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest core/autocut/tests/test_schnittmodell.py -q`
Expected: FAIL mit `ModuleNotFoundError: No module named 'niro_autocut.schnittmodell'`

- [ ] **Step 3: Modul schreiben**

```python
# core/autocut/src/niro_autocut/schnittmodell.py
"""NLE-neutrales Schnittmodell.

Jede Timeline-Entscheidung landet hier: Spuren, Clips mit Quell- und Zielzeiten, Tempo, Pegel,
aktiv/inaktiv, Marken, Spurnamen, Bildrate und Start-Timecode. Resolve baut daraus über die
Scripting-API, spätere Adapter schreiben daraus FCP7-XML oder FCPXML, der Vorschau-Render liest
dasselbe Modell.

Bildraten sind immer Brüche. 23,976 ist 24000/1001, nie 23.976 — Fließkommaraten führen beim
Umrechnen in Frames zu Rundungsfehlern, die sich über eine Timeline aufsummieren.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

# Zulässige Bildraten: Zähler/Nenner je gerundetem Wert. NTSC-Raten haben den Nenner 1001.
RATEN: dict[float, tuple[int, int]] = {
    23.976: (24000, 1001), 23.98: (24000, 1001),
    24.0: (24, 1), 25.0: (25, 1),
    29.97: (30000, 1001), 30.0: (30, 1),
    47.952: (48000, 1001), 48.0: (48, 1), 50.0: (50, 1),
    59.94: (60000, 1001), 60.0: (60, 1),
    100.0: (100, 1), 119.88: (120000, 1001), 120.0: (120, 1),
}


@dataclass(frozen=True)
class Rate:
    """Bildrate als exakter Bruch."""

    zaehler: int
    nenner: int

    @classmethod
    def von_fliesskomma(cls, fps: float) -> "Rate":
        """Nächstliegende zulässige Bildrate; Abweichung über 0,05 fps ist ein Fehler."""
        treffer = min(RATEN, key=lambda r: abs(r - float(fps)))
        if abs(treffer - float(fps)) > 0.05:
            raise ValueError(f"Bildrate {fps} ist keine bekannte Rate. Bekannt: "
                             + ", ".join(str(r) for r in sorted(RATEN)))
        z, n = RATEN[treffer]
        return cls(zaehler=z, nenner=n)

    @property
    def ntsc(self) -> bool:
        """NTSC-Rate (23,976 / 29,97 / 59,94 …) — im FCP7-XML als Ganzzahl plus Flag kodiert."""
        return self.nenner == 1001

    def als_bruch(self) -> Fraction:
        return Fraction(self.zaehler, self.nenner)

    def als_fliesskomma(self) -> float:
        return self.zaehler / self.nenner

    def frames(self, sekunden: float) -> int:
        """Sekunden → Frames, kaufmännisch gerundet."""
        return int(round(Fraction(sekunden).limit_denominator(1000000) * self.als_bruch()))

    def sekunden(self, frames: int) -> float:
        return float(Fraction(frames) / self.als_bruch())

    def to_dict(self) -> dict:
        return {"zaehler": self.zaehler, "nenner": self.nenner}

    @classmethod
    def from_dict(cls, d: dict) -> "Rate":
        return cls(zaehler=int(d["zaehler"]), nenner=int(d["nenner"]))


@dataclass
class Schnitt:
    """Ein Clip auf einer Spur.

    ``quelle_in_s``/``quelle_out_s`` sind Quell-Echtzeit, ``ziel_in_s`` die Position auf der Timeline.
    ``tempo`` 1,0 = Echtzeit, 2,0 = halbe Geschwindigkeit (doppelte Zieldauer).
    """

    spur: str
    quelle: str
    quelle_in_s: float
    quelle_out_s: float
    ziel_in_s: float
    tempo: float = 1.0
    pegel_db: float = 0.0
    aktiv: bool = True
    name: str = ""

    @property
    def ziel_dauer_s(self) -> float:
        return (self.quelle_out_s - self.quelle_in_s) * self.tempo

    @property
    def ziel_out_s(self) -> float:
        return self.ziel_in_s + self.ziel_dauer_s

    def to_dict(self) -> dict:
        return {"spur": self.spur, "quelle": self.quelle, "quelle_in_s": self.quelle_in_s,
                "quelle_out_s": self.quelle_out_s, "ziel_in_s": self.ziel_in_s, "tempo": self.tempo,
                "pegel_db": self.pegel_db, "aktiv": self.aktiv, "name": self.name}

    @classmethod
    def from_dict(cls, d: dict) -> "Schnitt":
        return cls(spur=d["spur"], quelle=d["quelle"], quelle_in_s=float(d["quelle_in_s"]),
                   quelle_out_s=float(d["quelle_out_s"]), ziel_in_s=float(d["ziel_in_s"]),
                   tempo=float(d.get("tempo", 1.0)), pegel_db=float(d.get("pegel_db", 0.0)),
                   aktiv=bool(d.get("aktiv", True)), name=d.get("name", ""))


@dataclass
class Marke:
    """Marker auf der Timeline (Position in Sekunden ab Timeline-Anfang, nicht ab Start-Timecode)."""

    ziel_s: float
    name: str
    farbe: str
    notiz: str = ""
    dauer_s: float = 0.0

    def to_dict(self) -> dict:
        return {"ziel_s": self.ziel_s, "name": self.name, "farbe": self.farbe,
                "notiz": self.notiz, "dauer_s": self.dauer_s}

    @classmethod
    def from_dict(cls, d: dict) -> "Marke":
        return cls(ziel_s=float(d["ziel_s"]), name=d["name"], farbe=d["farbe"],
                   notiz=d.get("notiz", ""), dauer_s=float(d.get("dauer_s", 0.0)))


@dataclass
class Schnittmodell:
    """Eine vollständige Timeline, unabhängig vom Schnittprogramm."""

    rate: Rate
    breite: int
    hoehe: int
    start_tc: str
    schnitte: list[Schnitt] = field(default_factory=list)
    marken: list[Marke] = field(default_factory=list)
    spurnamen: dict[str, str] = field(default_factory=dict)
    version: int = 1

    @property
    def dauer_s(self) -> float:
        return max((s.ziel_out_s for s in self.schnitte), default=0.0)

    def spuren(self) -> list[str]:
        """Belegte Spuren in stabiler Reihenfolge: erst Video, dann Audio, je aufsteigend."""
        namen = {s.spur for s in self.schnitte}
        return sorted(namen, key=lambda n: (n[0] != "V", int(n[1:]) if n[1:].isdigit() else 0))

    def to_dict(self) -> dict:
        return {"version": self.version, "rate": self.rate.to_dict(), "breite": self.breite,
                "hoehe": self.hoehe, "start_tc": self.start_tc,
                "schnitte": [s.to_dict() for s in self.schnitte],
                "marken": [m.to_dict() for m in self.marken], "spurnamen": dict(self.spurnamen)}

    @classmethod
    def from_dict(cls, d: dict) -> "Schnittmodell":
        return cls(rate=Rate.from_dict(d["rate"]), breite=int(d["breite"]), hoehe=int(d["hoehe"]),
                   start_tc=d["start_tc"], schnitte=[Schnitt.from_dict(x) for x in d.get("schnitte", [])],
                   marken=[Marke.from_dict(x) for x in d.get("marken", [])],
                   spurnamen=dict(d.get("spurnamen", {})), version=int(d.get("version", 1)))
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest core/autocut/tests/test_schnittmodell.py -q`
Expected: PASS

- [ ] **Step 5: Umwandlung aus dem TimelinePlan — failing test**

Die Felder von `Item` und `MarkerSpec` zuerst nachlesen, damit die Zuordnung stimmt:

```bash
cd ~/niro-produkt && sed -n '44,101p' core/autocut/src/niro_autocut/timeline_model.py
```

Dann den Test schreiben. Die Feldnamen auf der rechten Seite der Zuordnung stammen aus dem eben gelesenen Abschnitt; weichen sie ab, den Test an die echten Namen anpassen, nicht den Kern:

```python
# Ergänzung in core/autocut/tests/test_schnittmodell.py
from niro_autocut.schnittmodell import aus_timeline_plan
from niro_autocut.timeline_model import Item, MarkerSpec, TimelinePlan


def test_aus_timeline_plan_uebernimmt_items_und_marken():
    plan = TimelinePlan(
        items=[Item(track="V1", clip="/a/FX3_0001.MP4", src_in_f=50, src_out_f=125, rec_in_f=0, fps=25.0)],
        markers=[MarkerSpec(frame=0, name="Beat 1", color="Blue", note="Hook")],
        fps=25.0)

    m = aus_timeline_plan(plan, rate=Rate.von_fliesskomma(25.0), breite=3840, hoehe=2160,
                          start_tc="01:00:00:00")

    assert len(m.schnitte) == 1
    s = m.schnitte[0]
    assert s.spur == "V1"
    assert s.quelle == "/a/FX3_0001.MP4"
    assert s.quelle_in_s == pytest.approx(2.0)
    assert s.quelle_out_s == pytest.approx(5.0)
    assert s.ziel_in_s == pytest.approx(0.0)
    assert m.marken[0].name == "Beat 1"
    assert m.marken[0].ziel_s == pytest.approx(0.0)
```

- [ ] **Step 6: Test laufen lassen, Fehlschlag prüfen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest core/autocut/tests/test_schnittmodell.py -q -k timeline_plan`
Expected: FAIL mit `ImportError: cannot import name 'aus_timeline_plan'`

- [ ] **Step 7: `aus_timeline_plan` schreiben**

Ans Ende von `schnittmodell.py`. Die Attributnamen von `Item` und `MarkerSpec` aus Step 5 verwenden:

```python
def aus_timeline_plan(plan, rate: Rate, breite: int, hoehe: int, start_tc: str) -> Schnittmodell:
    """``TimelinePlan`` (Frames, Spurkürzel) → Schnittmodell (Sekunden, neutral).

    Der TimelinePlan rechnet in Frames der Timeline-Bildrate; hier wird alles in Sekunden über den
    exakten Ratenbruch umgerechnet, damit spätere Adapter ohne Kenntnis der Rate arbeiten können.
    """
    schnitte: list[Schnitt] = []
    for it in plan.items:
        quell_rate = Rate.von_fliesskomma(float(getattr(it, "fps", rate.als_fliesskomma())))
        schnitte.append(Schnitt(
            spur=it.track,
            quelle=it.clip,
            quelle_in_s=quell_rate.sekunden(int(it.src_in_f)),
            quelle_out_s=quell_rate.sekunden(int(it.src_out_f)),
            ziel_in_s=rate.sekunden(int(it.rec_in_f)),
            name=getattr(it, "name", "") or "",
        ))
    marken = [Marke(ziel_s=rate.sekunden(int(mk.frame)), name=mk.name, farbe=mk.color,
                    notiz=getattr(mk, "note", "") or "")
              for mk in plan.markers]
    return Schnittmodell(rate=rate, breite=breite, hoehe=hoehe, start_tc=start_tc,
                         schnitte=schnitte, marken=marken)
```

- [ ] **Step 8: Tests laufen lassen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest -q`
Expected: PASS. Meldet der Test einen fehlenden Parameter bei `Item` oder `TimelinePlan`, die echten Pflichtfelder aus Step 5 in den Test übernehmen.

- [ ] **Step 9: Commit**

```bash
cd ~/niro-produkt
git add core/autocut/src/niro_autocut/schnittmodell.py core/autocut/tests/test_schnittmodell.py
git commit -m "feat(core): NLE-neutrales Schnittmodell mit exakten Bildraten

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Server mit Job-Modell

Der Server kennt Projekte, Jobs und Schritte. Er entscheidet nichts über Medien — er verteilt Aufträge an Brücken und sammelt Ergebnisse. Speicher ist SQLite, weil der Durchstich auf einem Rechner läuft; der Umstieg auf Postgres ist später ein Austausch von `ablage.py`.

**Files:**
- Create: `server/src/produkt_server/__init__.py`, `fehler.py`, `modell.py`, `ablage.py`, `ablauf.py`, `api.py`
- Create: `server/scripts/serve.py`
- Test: `server/tests/test_ablage.py`, `server/tests/test_api.py`

**Interfaces:**
- Consumes: nichts aus `core/`
- Produces:
  - `ProduktError(meldung: str, code: int = 400)`
  - `Ablage(pfad: str | Path)` mit `projekt_anlegen`, `projekt_holen`, `job_anlegen`, `job_holen`, `schritt_naechster_offener`, `schritt_starten`, `schritt_beenden`, `jobs_eines_projekts`
  - `Job(id, projekt_id, art, status, angelegt_am)`, `Schritt(id, job_id, nr, name, status, eingabe, ausgabe, fehler)`
  - `SCHRITTFOLGEN: dict[str, list[str]]` mit `"rohschnitt": ["vorbereiten", "synchronisieren", "pruefen", "bauen"]`
  - `app` (FastAPI) mit den Endpunkten aus Step 6

- [ ] **Step 1: Failing test für die Ablage schreiben**

```python
# server/tests/test_ablage.py
"""SQLite-Ablage: Projekte, Jobs, Schritte."""
import pytest

from produkt_server.ablage import Ablage
from produkt_server.fehler import ProduktError


@pytest.fixture()
def ablage(tmp_path):
    return Ablage(tmp_path / "test.db")


def test_projekt_anlegen_und_holen(ablage, tmp_path):
    pid = ablage.projekt_anlegen(name="Imagefilm", kunde="Muster GmbH", ordner=str(tmp_path))
    p = ablage.projekt_holen(pid)

    assert p["name"] == "Imagefilm"
    assert p["kunde"] == "Muster GmbH"
    assert p["ordner"] == str(tmp_path)


def test_unbekanntes_projekt_meldet_fehler(ablage):
    with pytest.raises(ProduktError, match="Projekt"):
        ablage.projekt_holen(999)


def test_job_legt_seine_schritte_an(ablage, tmp_path):
    pid = ablage.projekt_anlegen(name="P", kunde="K", ordner=str(tmp_path))
    jid = ablage.job_anlegen(projekt_id=pid, art="rohschnitt",
                             schritte=["vorbereiten", "synchronisieren", "pruefen", "bauen"],
                             eingabe={"video": "video-1.md"})
    job = ablage.job_holen(jid)

    assert job["art"] == "rohschnitt"
    assert job["status"] == "offen"
    assert [s["name"] for s in job["schritte"]] == ["vorbereiten", "synchronisieren", "pruefen", "bauen"]
    assert all(s["status"] == "offen" for s in job["schritte"])
    assert job["schritte"][0]["eingabe"]["video"] == "video-1.md"


def test_schritte_kommen_in_der_reihenfolge(ablage, tmp_path):
    pid = ablage.projekt_anlegen(name="P", kunde="K", ordner=str(tmp_path))
    jid = ablage.job_anlegen(projekt_id=pid, art="rohschnitt", schritte=["a", "b"], eingabe={})

    erster = ablage.schritt_naechster_offener()
    assert erster["name"] == "a"

    ablage.schritt_starten(erster["id"], geraet="mac-1")
    assert ablage.schritt_naechster_offener() is None, "Solange a läuft, darf b nicht kommen"

    ablage.schritt_beenden(erster["id"], ausgabe={"ok": True})
    zweiter = ablage.schritt_naechster_offener()
    assert zweiter["name"] == "b"
    assert zweiter["eingabe"]["vorher"]["a"] == {"ok": True}, "Ergebnisse der Vorschritte reichen weiter"


def test_letzter_schritt_schliesst_den_job(ablage, tmp_path):
    pid = ablage.projekt_anlegen(name="P", kunde="K", ordner=str(tmp_path))
    jid = ablage.job_anlegen(projekt_id=pid, art="x", schritte=["a"], eingabe={})
    s = ablage.schritt_naechster_offener()
    ablage.schritt_starten(s["id"], geraet="mac-1")
    ablage.schritt_beenden(s["id"], ausgabe={})

    assert ablage.job_holen(jid)["status"] == "fertig"


def test_fehler_im_schritt_stoppt_den_job(ablage, tmp_path):
    pid = ablage.projekt_anlegen(name="P", kunde="K", ordner=str(tmp_path))
    jid = ablage.job_anlegen(projekt_id=pid, art="x", schritte=["a", "b"], eingabe={})
    s = ablage.schritt_naechster_offener()
    ablage.schritt_starten(s["id"], geraet="mac-1")
    ablage.schritt_beenden(s["id"], fehler="Proxy passt nicht zum Original")

    job = ablage.job_holen(jid)
    assert job["status"] == "fehler"
    assert job["schritte"][0]["fehler"] == "Proxy passt nicht zum Original"
    assert ablage.schritt_naechster_offener() is None, "Nach einem Fehler wird nichts mehr ausgegeben"
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest server/tests/test_ablage.py -q`
Expected: FAIL mit `ModuleNotFoundError: No module named 'produkt_server'`

- [ ] **Step 3: `fehler.py` und `ablage.py` schreiben**

```python
# server/src/produkt_server/fehler.py
"""Fehler des Servers mit HTTP-Code."""
from __future__ import annotations


class ProduktError(Exception):
    """Fehler mit handlungsleitender deutscher Meldung und HTTP-Code."""

    def __init__(self, meldung: str, code: int = 400):
        super().__init__(meldung)
        self.meldung = meldung
        self.code = code
```

```python
# server/src/produkt_server/ablage.py
"""SQLite-Ablage: Organisationen, Projekte, Jobs, Schritte.

Ein Job ist eine Schrittfolge. Immer höchstens ein Schritt läuft; sein Ergebnis wird dem nächsten
Schritt unter ``eingabe["vorher"][<name>]`` mitgegeben. Ein Fehler hält den ganzen Job an.
"""
from __future__ import annotations

import datetime as _dt
import json
import sqlite3
from pathlib import Path

from .fehler import ProduktError

SCHEMA = """
CREATE TABLE IF NOT EXISTS projekte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    kunde TEXT NOT NULL DEFAULT '',
    ordner TEXT NOT NULL,
    angelegt_am TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projekt_id INTEGER NOT NULL REFERENCES projekte(id),
    art TEXT NOT NULL,
    status TEXT NOT NULL,
    angelegt_am TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS schritte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    nr INTEGER NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    geraet TEXT NOT NULL DEFAULT '',
    eingabe TEXT NOT NULL DEFAULT '{}',
    ausgabe TEXT NOT NULL DEFAULT '{}',
    fehler TEXT NOT NULL DEFAULT '',
    gestartet_am TEXT NOT NULL DEFAULT '',
    beendet_am TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS schritte_job ON schritte(job_id, nr);
"""


def _jetzt() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


class Ablage:
    """Zugriff auf die SQLite-Datei. Eine Verbindung je Ablage, Zeilen als ``dict``."""

    def __init__(self, pfad: str | Path):
        self.pfad = Path(pfad)
        self.pfad.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.pfad, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    # --- Projekte ------------------------------------------------------
    def projekt_anlegen(self, name: str, kunde: str, ordner: str) -> int:
        cur = self.db.execute(
            "INSERT INTO projekte (name, kunde, ordner, angelegt_am) VALUES (?,?,?,?)",
            (name, kunde, ordner, _jetzt()))
        self.db.commit()
        return int(cur.lastrowid)

    def projekt_holen(self, projekt_id: int) -> dict:
        row = self.db.execute("SELECT * FROM projekte WHERE id=?", (projekt_id,)).fetchone()
        if row is None:
            raise ProduktError(f"Projekt {projekt_id} gibt es nicht. Projekt im Programm neu anlegen.", 404)
        return dict(row)

    def projekte(self) -> list[dict]:
        return [dict(r) for r in self.db.execute("SELECT * FROM projekte ORDER BY id DESC")]

    # --- Jobs ----------------------------------------------------------
    def job_anlegen(self, projekt_id: int, art: str, schritte: list[str], eingabe: dict) -> int:
        self.projekt_holen(projekt_id)
        cur = self.db.execute("INSERT INTO jobs (projekt_id, art, status, angelegt_am) VALUES (?,?,?,?)",
                              (projekt_id, art, "offen", _jetzt()))
        job_id = int(cur.lastrowid)
        for nr, name in enumerate(schritte, start=1):
            self.db.execute("INSERT INTO schritte (job_id, nr, name, status, eingabe) VALUES (?,?,?,?,?)",
                            (job_id, nr, name, "offen", json.dumps(eingabe, ensure_ascii=False)))
        self.db.commit()
        return job_id

    def job_holen(self, job_id: int) -> dict:
        row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ProduktError(f"Job {job_id} gibt es nicht.", 404)
        job = dict(row)
        job["schritte"] = [self._schritt(dict(r)) for r in
                           self.db.execute("SELECT * FROM schritte WHERE job_id=? ORDER BY nr", (job_id,))]
        return job

    def jobs_eines_projekts(self, projekt_id: int) -> list[dict]:
        return [dict(r) for r in
                self.db.execute("SELECT * FROM jobs WHERE projekt_id=? ORDER BY id DESC", (projekt_id,))]

    # --- Schritte ------------------------------------------------------
    @staticmethod
    def _schritt(row: dict) -> dict:
        row["eingabe"] = json.loads(row["eingabe"] or "{}")
        row["ausgabe"] = json.loads(row["ausgabe"] or "{}")
        return row

    def schritt_naechster_offener(self) -> dict | None:
        """Ältester offener Schritt, dessen Job nicht läuft und nicht gescheitert ist."""
        laeuft = self.db.execute("SELECT COUNT(*) c FROM schritte WHERE status='laeuft'").fetchone()["c"]
        if laeuft:
            return None
        row = self.db.execute(
            "SELECT s.* FROM schritte s JOIN jobs j ON j.id = s.job_id "
            "WHERE s.status='offen' AND j.status IN ('offen','laeuft') ORDER BY s.job_id, s.nr LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        schritt = self._schritt(dict(row))
        projekt = self.projekt_holen(self.job_holen(schritt["job_id"])["projekt_id"])
        schritt["projekt"] = projekt
        return schritt

    def schritt_starten(self, schritt_id: int, geraet: str) -> None:
        row = self.db.execute("SELECT * FROM schritte WHERE id=?", (schritt_id,)).fetchone()
        if row is None:
            raise ProduktError(f"Schritt {schritt_id} gibt es nicht.", 404)
        if row["status"] != "offen":
            raise ProduktError(f"Schritt {schritt_id} ist nicht offen, sondern {row['status']}.", 409)
        self.db.execute("UPDATE schritte SET status='laeuft', geraet=?, gestartet_am=? WHERE id=?",
                        (geraet, _jetzt(), schritt_id))
        self.db.execute("UPDATE jobs SET status='laeuft' WHERE id=? AND status='offen'", (row["job_id"],))
        self.db.commit()

    def schritt_beenden(self, schritt_id: int, ausgabe: dict | None = None, fehler: str = "") -> None:
        row = self.db.execute("SELECT * FROM schritte WHERE id=?", (schritt_id,)).fetchone()
        if row is None:
            raise ProduktError(f"Schritt {schritt_id} gibt es nicht.", 404)
        status = "fehler" if fehler else "fertig"
        self.db.execute(
            "UPDATE schritte SET status=?, ausgabe=?, fehler=?, beendet_am=? WHERE id=?",
            (status, json.dumps(ausgabe or {}, ensure_ascii=False), fehler, _jetzt(), schritt_id))
        if fehler:
            self.db.execute("UPDATE jobs SET status='fehler' WHERE id=?", (row["job_id"],))
            self.db.commit()
            return
        self._ergebnis_weiterreichen(row["job_id"], row["name"], ausgabe or {})
        offen = self.db.execute("SELECT COUNT(*) c FROM schritte WHERE job_id=? AND status!='fertig'",
                                (row["job_id"],)).fetchone()["c"]
        if not offen:
            self.db.execute("UPDATE jobs SET status='fertig' WHERE id=?", (row["job_id"],))
        self.db.commit()

    def _ergebnis_weiterreichen(self, job_id: int, name: str, ausgabe: dict) -> None:
        """Ergebnis unter ``eingabe["vorher"][<name>]`` in alle noch offenen Schritte des Jobs legen."""
        for row in self.db.execute("SELECT id, eingabe FROM schritte WHERE job_id=? AND status='offen'",
                                   (job_id,)):
            eingabe = json.loads(row["eingabe"] or "{}")
            eingabe.setdefault("vorher", {})[name] = ausgabe
            self.db.execute("UPDATE schritte SET eingabe=? WHERE id=?",
                            (json.dumps(eingabe, ensure_ascii=False), row["id"]))
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest server/tests/test_ablage.py -q`
Expected: PASS

- [ ] **Step 5: Failing test für die API schreiben**

```python
# server/tests/test_api.py
"""REST-Schnittstelle: Projekte, Jobs, Auftragsabholung, Ergebnismeldung."""
import pytest
from fastapi.testclient import TestClient

from produkt_server.api import baue_app


@pytest.fixture()
def klient(tmp_path):
    app = baue_app(db_pfad=tmp_path / "test.db", einladungen={"chef@example.com": "geheim"})
    return TestClient(app)


@pytest.fixture()
def token(klient):
    antwort = klient.post("/v1/anmelden", json={"email": "chef@example.com", "code": "geheim",
                                                "geraet": "mac-1"})
    assert antwort.status_code == 200
    return antwort.json()["token"]


def test_anmeldung_mit_falschem_code_wird_abgelehnt(klient):
    antwort = klient.post("/v1/anmelden", json={"email": "chef@example.com", "code": "falsch",
                                                "geraet": "mac-1"})
    assert antwort.status_code == 401


def test_ohne_token_kein_zugriff(klient):
    assert klient.get("/v1/projekte").status_code == 401


def test_projekt_anlegen_und_auflisten(klient, token, tmp_path):
    kopf = {"Authorization": f"Bearer {token}"}
    antwort = klient.post("/v1/projekte", headers=kopf,
                          json={"name": "Imagefilm", "kunde": "Muster GmbH", "ordner": str(tmp_path)})
    assert antwort.status_code == 200
    pid = antwort.json()["id"]

    liste = klient.get("/v1/projekte", headers=kopf).json()
    assert [p["id"] for p in liste] == [pid]


def test_rohschnitt_job_hat_vier_schritte(klient, token, tmp_path):
    kopf = {"Authorization": f"Bearer {token}"}
    pid = klient.post("/v1/projekte", headers=kopf,
                      json={"name": "P", "kunde": "K", "ordner": str(tmp_path)}).json()["id"]

    antwort = klient.post(f"/v1/projekte/{pid}/jobs", headers=kopf,
                          json={"art": "rohschnitt", "eingabe": {"video": "video-1.md"}})
    assert antwort.status_code == 200
    job = klient.get(f"/v1/jobs/{antwort.json()['id']}", headers=kopf).json()

    assert [s["name"] for s in job["schritte"]] == ["vorbereiten", "synchronisieren", "pruefen", "bauen"]


def test_unbekannte_job_art_wird_abgelehnt(klient, token, tmp_path):
    kopf = {"Authorization": f"Bearer {token}"}
    pid = klient.post("/v1/projekte", headers=kopf,
                      json={"name": "P", "kunde": "K", "ordner": str(tmp_path)}).json()["id"]

    antwort = klient.post(f"/v1/projekte/{pid}/jobs", headers=kopf, json={"art": "quatsch", "eingabe": {}})
    assert antwort.status_code == 400
    assert "quatsch" in antwort.json()["detail"]


def test_auftrag_abholen_und_ergebnis_melden(klient, token, tmp_path):
    kopf = {"Authorization": f"Bearer {token}"}
    pid = klient.post("/v1/projekte", headers=kopf,
                      json={"name": "P", "kunde": "K", "ordner": str(tmp_path)}).json()["id"]
    jid = klient.post(f"/v1/projekte/{pid}/jobs", headers=kopf,
                      json={"art": "rohschnitt", "eingabe": {}}).json()["id"]

    auftrag = klient.get("/v1/auftrag", headers=kopf).json()
    assert auftrag["name"] == "vorbereiten"
    assert auftrag["projekt"]["ordner"] == str(tmp_path)

    assert klient.get("/v1/auftrag", headers=kopf).json() is None, "Zweite Abholung liefert nichts"

    klient.post(f"/v1/schritte/{auftrag['id']}/ergebnis", headers=kopf,
                json={"ausgabe": {"clips": 12}})
    naechster = klient.get("/v1/auftrag", headers=kopf).json()
    assert naechster["name"] == "synchronisieren"
    assert naechster["eingabe"]["vorher"]["vorbereiten"]["clips"] == 12


def test_gemeldeter_fehler_haelt_den_job_an(klient, token, tmp_path):
    kopf = {"Authorization": f"Bearer {token}"}
    pid = klient.post("/v1/projekte", headers=kopf,
                      json={"name": "P", "kunde": "K", "ordner": str(tmp_path)}).json()["id"]
    jid = klient.post(f"/v1/projekte/{pid}/jobs", headers=kopf,
                      json={"art": "rohschnitt", "eingabe": {}}).json()["id"]
    auftrag = klient.get("/v1/auftrag", headers=kopf).json()

    klient.post(f"/v1/schritte/{auftrag['id']}/ergebnis", headers=kopf,
                json={"fehler": "Resolve läuft nicht"})

    job = klient.get(f"/v1/jobs/{jid}", headers=kopf).json()
    assert job["status"] == "fehler"
    assert klient.get("/v1/auftrag", headers=kopf).json() is None
```

- [ ] **Step 6: Test laufen lassen, Fehlschlag prüfen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest server/tests/test_api.py -q`
Expected: FAIL mit `ModuleNotFoundError: No module named 'produkt_server.api'`

- [ ] **Step 7: `ablauf.py`, `auth.py` und `api.py` schreiben**

```python
# server/src/produkt_server/ablauf.py
"""Welche Schritte eine Job-Art hat."""
from __future__ import annotations

from .fehler import ProduktError

SCHRITTFOLGEN: dict[str, list[str]] = {
    "rohschnitt": ["vorbereiten", "synchronisieren", "pruefen", "bauen"],
}


def schritte_fuer(art: str) -> list[str]:
    """Schrittfolge einer Job-Art; unbekannte Art ist ein Fehler mit Aufzählung der bekannten."""
    if art not in SCHRITTFOLGEN:
        raise ProduktError(f"Unbekannte Job-Art '{art}'. Bekannt: " + ", ".join(sorted(SCHRITTFOLGEN)), 400)
    return list(SCHRITTFOLGEN[art])
```

```python
# server/src/produkt_server/auth.py
"""Anmeldung auf Einladung, Token im Speicher.

Für den Durchstich genügt eine Liste erlaubter Adressen mit Einladungscode. Der Token lebt im
Prozess; ein Neustart des Servers meldet alle ab. Geräte- und Sitzbindung kommen mit dem Login-Teil.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass

from .fehler import ProduktError


@dataclass
class Sitzung:
    email: str
    geraet: str


class Anmeldung:
    def __init__(self, einladungen: dict[str, str]):
        self.einladungen = dict(einladungen)
        self.sitzungen: dict[str, Sitzung] = {}

    def anmelden(self, email: str, code: str, geraet: str) -> str:
        erwartet = self.einladungen.get(email)
        if erwartet is None or not secrets.compare_digest(erwartet, code):
            raise ProduktError("Anmeldung fehlgeschlagen. Adresse und Einladungscode prüfen.", 401)
        token = secrets.token_urlsafe(32)
        self.sitzungen[token] = Sitzung(email=email, geraet=geraet)
        return token

    def pruefen(self, token: str | None) -> Sitzung:
        sitzung = self.sitzungen.get(token or "")
        if sitzung is None:
            raise ProduktError("Nicht angemeldet. Bitte im Programm neu anmelden.", 401)
        return sitzung
```

```python
# server/src/produkt_server/api.py
"""REST-Schnittstelle des Servers."""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from .ablage import Ablage
from .ablauf import schritte_fuer
from .auth import Anmeldung
from .fehler import ProduktError


class AnmeldeDaten(BaseModel):
    email: str
    code: str
    geraet: str


class ProjektDaten(BaseModel):
    name: str
    kunde: str = ""
    ordner: str


class JobDaten(BaseModel):
    art: str
    eingabe: dict = {}


class ErgebnisDaten(BaseModel):
    ausgabe: dict = {}
    fehler: str = ""


def baue_app(db_pfad: str | Path, einladungen: dict[str, str]) -> FastAPI:
    """FastAPI-Anwendung mit eigener Ablage — so kann jeder Test seine eigene Datenbank nutzen."""
    app = FastAPI(title="NIRO Produkt Server")
    ablage = Ablage(db_pfad)
    anmeldung = Anmeldung(einladungen)

    def sitzung(authorization: str | None = Header(default=None)):
        token = authorization.removeprefix("Bearer ").strip() if authorization else None
        try:
            return anmeldung.pruefen(token)
        except ProduktError as e:
            raise HTTPException(status_code=e.code, detail=e.meldung) from e

    @app.exception_handler(ProduktError)
    async def produkt_fehler(_request, e: ProduktError):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=e.code, content={"detail": e.meldung})

    @app.post("/v1/anmelden")
    def anmelden(daten: AnmeldeDaten):
        try:
            return {"token": anmeldung.anmelden(daten.email, daten.code, daten.geraet)}
        except ProduktError as e:
            raise HTTPException(status_code=e.code, detail=e.meldung) from e

    @app.get("/v1/projekte")
    def projekte(_s=Depends(sitzung)):
        return ablage.projekte()

    @app.post("/v1/projekte")
    def projekt_anlegen(daten: ProjektDaten, _s=Depends(sitzung)):
        if not Path(daten.ordner).is_dir():
            raise HTTPException(status_code=400,
                                detail=f"Ordner nicht gefunden: {daten.ordner}. "
                                       f"Laufwerk verbinden oder anderen Ordner wählen.")
        return {"id": ablage.projekt_anlegen(daten.name, daten.kunde, daten.ordner)}

    @app.post("/v1/projekte/{projekt_id}/jobs")
    def job_anlegen(projekt_id: int, daten: JobDaten, _s=Depends(sitzung)):
        try:
            schritte = schritte_fuer(daten.art)
            return {"id": ablage.job_anlegen(projekt_id, daten.art, schritte, daten.eingabe)}
        except ProduktError as e:
            raise HTTPException(status_code=e.code, detail=e.meldung) from e

    @app.get("/v1/jobs/{job_id}")
    def job(job_id: int, _s=Depends(sitzung)):
        try:
            return ablage.job_holen(job_id)
        except ProduktError as e:
            raise HTTPException(status_code=e.code, detail=e.meldung) from e

    @app.get("/v1/auftrag")
    def auftrag(s=Depends(sitzung)):
        """Nächster offener Schritt für diese Brücke, oder null."""
        schritt = ablage.schritt_naechster_offener()
        if schritt is None:
            return None
        ablage.schritt_starten(schritt["id"], geraet=s.geraet)
        return schritt

    @app.post("/v1/schritte/{schritt_id}/ergebnis")
    def ergebnis(schritt_id: int, daten: ErgebnisDaten, _s=Depends(sitzung)):
        try:
            ablage.schritt_beenden(schritt_id, ausgabe=daten.ausgabe, fehler=daten.fehler)
            return {"ok": True}
        except ProduktError as e:
            raise HTTPException(status_code=e.code, detail=e.meldung) from e

    return app
```

- [ ] **Step 8: Tests laufen lassen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest server/tests -q`
Expected: PASS

- [ ] **Step 9: CLI-Einstieg schreiben**

```python
# server/scripts/serve.py
"""Server starten.

Aufruf:
    venv/bin/python server/scripts/serve.py [--port 8720] [--db ~/.niro-produkt/server.db]

Einladungen stehen in ~/.niro-produkt/einladungen.json als {"adresse": "code"}. Fehlt die Datei,
wird eine mit einem Zufallscode angelegt und der Code ausgegeben.
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import uvicorn  # noqa: E402

from produkt_server.api import baue_app  # noqa: E402

HEIM = Path.home() / ".niro-produkt"


def einladungen_laden(pfad: Path) -> dict[str, str]:
    if pfad.exists():
        return json.loads(pfad.read_text(encoding="utf-8"))
    code = secrets.token_urlsafe(12)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps({"admin@niro-productions.de": code}, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    print(f"Einladungsliste angelegt: {pfad}\n  admin@niro-productions.de  Code: {code}")
    return {"admin@niro-productions.de": code}


def main() -> int:
    ap = argparse.ArgumentParser(description="Server des Produkts starten.")
    ap.add_argument("--port", type=int, default=8720)
    ap.add_argument("--db", default=str(HEIM / "server.db"))
    ap.add_argument("--einladungen", default=str(HEIM / "einladungen.json"))
    a = ap.parse_args()

    app = baue_app(db_pfad=a.db, einladungen=einladungen_laden(Path(a.einladungen)))
    uvicorn.run(app, host="127.0.0.1", port=a.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 10: Server von Hand starten und wieder beenden**

Run: `cd ~/niro-produkt && timeout 5 venv/bin/python server/scripts/serve.py --port 8720 --db /tmp/probe.db --einladungen /tmp/probe-einladungen.json; echo "Exit $?"`
Expected: Die Einladungsliste wird angelegt und der Code ausgegeben, uvicorn meldet `Uvicorn running on http://127.0.0.1:8720`, nach fünf Sekunden beendet `timeout` den Lauf.

- [ ] **Step 11: Commit**

```bash
cd ~/niro-produkt
git add server pyproject.toml
git commit -m "feat(server): Job-Modell mit Schrittfolge, Anmeldung auf Einladung, REST-Schnittstelle

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Brücke, die Aufträge ausführt

Die Brücke läuft auf dem Rechner des Kunden. Sie holt Aufträge, ruft die Kernfunktionen auf und meldet Ergebnisse. In dieser Task werden die vier Schritte des Rohschnitts umgesetzt; drei davon brauchen kein Resolve und sind darum vollständig testbar.

**Files:**
- Create: `bridge/src/produkt_bruecke/__init__.py`, `fehler.py`, `klient.py`, `schritte.py`, `laeufer.py`
- Create: `bridge/scripts/bruecke.py`
- Test: `bridge/tests/test_schritte.py`, `bridge/tests/test_laeufer.py`

**Interfaces:**
- Consumes: `Charge.open_produkt` (Task 2); `niro_autocut.media`, `niro_autocut.sync.sync_charge`, `niro_autocut.cutlist.{Cutlist, verify_cutlist, cutlist_hash, total_length_s}`, `niro_autocut.timeline_model.build_timeline_plan`, `niro_autocut.resolve_api`; `/v1/auftrag` und `/v1/schritte/{id}/ergebnis` (Task 4)
- Produces:
  - `BrueckeError(meldung: str)`
  - `Klient(server: str, token: str)` mit `auftrag_holen() -> dict | None` und `ergebnis_melden(schritt_id, ausgabe=None, fehler="")`
  - `AUSFUEHRER: dict[str, Callable[[dict], dict]]` mit den Schlüsseln `vorbereiten`, `synchronisieren`, `pruefen`, `bauen`
  - `ausfuehren(auftrag: dict) -> dict` — wählt den Ausführer und gibt dessen Ausgabe zurück
  - `Laeufer(klient, schlafen_s=2.0)` mit `einmal() -> bool` und `laufen(max_runden: int | None = None)`

- [ ] **Step 1: Failing test für die Schritt-Ausführer schreiben**

```python
# bridge/tests/test_schritte.py
"""Schritt-Ausführer der Brücke. Ohne Resolve, ohne Netz."""
import json
import shutil
from pathlib import Path

import pytest

from produkt_bruecke.fehler import BrueckeError
from produkt_bruecke.schritte import ausfuehren

TESTDATEN = Path(__file__).resolve().parents[2] / "testdaten" / "taxodia"


@pytest.fixture()
def projekt(tmp_path):
    """Kopie des Testprojekts, damit Läufe sich nicht gegenseitig stören."""
    ziel = tmp_path / "Projekt"
    shutil.copytree(TESTDATEN, ziel)
    return ziel


def auftrag(projekt: Path, name: str, eingabe: dict | None = None) -> dict:
    return {"id": 1, "name": name, "eingabe": eingabe or {},
            "projekt": {"id": 1, "name": "Taxodia", "kunde": "Ludwig", "ordner": str(projekt)}}


def test_unbekannter_schritt_meldet_fehler(projekt):
    with pytest.raises(BrueckeError, match="Unbekannter Schritt"):
        ausfuehren(auftrag(projekt, "tanzen"))


def test_pruefen_liest_cutlist_und_meldet_zahlen(projekt):
    ausgabe = ausfuehren(auftrag(projekt, "pruefen"))

    assert "beats" in ausgabe and ausgabe["beats"] > 0
    assert "cutlist_hash" in ausgabe and len(ausgabe["cutlist_hash"]) == 64
    assert isinstance(ausgabe["ok"], bool)
    assert isinstance(ausgabe["fehler_liste"], list)


def test_pruefen_ohne_cutlist_meldet_handlungsanweisung(tmp_path):
    leer = tmp_path / "Leer"
    (leer / "_studio" / "autocut").mkdir(parents=True)
    with pytest.raises(BrueckeError, match="cutlist.json"):
        ausfuehren(auftrag(leer, "pruefen"))


def test_bauen_ohne_bestandene_pruefung_bricht_ab(projekt):
    with pytest.raises(BrueckeError, match="Prüfung"):
        ausfuehren(auftrag(projekt, "bauen", {"vorher": {"pruefen": {"ok": False}}}))


def test_bauen_im_probelauf_ruehrt_resolve_nicht_an(projekt):
    ausgabe = ausfuehren(auftrag(projekt, "bauen",
                                 {"probelauf": True,
                                  "vorher": {"pruefen": {"ok": True, "cutlist_hash": "x" * 64}}}))

    assert ausgabe["probelauf"] is True
    assert ausgabe["items"] > 0
    assert ausgabe["schnittmodell"]["rate"]["zaehler"] > 0
    assert (projekt / "_studio" / "autocut" / "schnittmodell.json").exists()
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest bridge/tests/test_schritte.py -q`
Expected: FAIL mit `ModuleNotFoundError: No module named 'produkt_bruecke'`

- [ ] **Step 3: `fehler.py` und `schritte.py` schreiben**

```python
# bridge/src/produkt_bruecke/fehler.py
"""Fehler der Brücke."""
from __future__ import annotations


class BrueckeError(Exception):
    """Fehler mit handlungsleitender deutscher Meldung; wird als Schritt-Fehler gemeldet."""
```

```python
# bridge/src/produkt_bruecke/schritte.py
"""Schritt-Ausführer der Brücke.

Jeder Ausführer bekommt den Auftrag des Servers und gibt ein JSON-fähiges Ergebnis zurück. Die
eigentliche Arbeit macht der Kern; hier steht nur die Übersetzung Auftrag → Kernaufruf → Ergebnis.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from niro_autocut import resolve_api as RA
from niro_autocut.charge import AutoCutError, Charge
from niro_autocut.cutlist import Cutlist, cutlist_hash, total_length_s, verify_cutlist
from niro_autocut.schnittmodell import Rate, aus_timeline_plan
from niro_autocut.sync import sync_charge
from niro_autocut.timeline_model import build_timeline_plan

from .fehler import BrueckeError


def _charge(auftrag: dict) -> Charge:
    p = auftrag["projekt"]
    try:
        return Charge.open_produkt(p["ordner"], kunde=p.get("kunde", ""), projekt=p.get("name", ""))
    except AutoCutError as e:
        raise BrueckeError(str(e)) from e


def _json_lesen(ch: Charge, name: str, zweck: str) -> dict:
    pfad = ch.autocut / name
    if not pfad.exists():
        raise BrueckeError(f"{name} fehlt in {ch.autocut}.\nZuerst den Schritt ausführen, der sie "
                           f"erzeugt ({zweck}).")
    return json.loads(pfad.read_text(encoding="utf-8"))


def _woerter(ch: Charge) -> dict[str, list[dict]]:
    """Wortlisten je Clip aus dem Transkript-Cache; leer, wenn kein Cache vorhanden ist."""
    woerter: dict[str, list[dict]] = {}
    try:
        index = ch.load_index()
    except Exception:
        return woerter
    for eintrag in index:
        pfad = eintrag.get("path") or eintrag.get("pfad")
        fp = eintrag.get("fingerprint")
        if not pfad or not fp:
            continue
        cache = ch.cache_transcript(fp)
        if cache:
            woerter[pfad] = cache.get("words", [])
    return woerter


def vorbereiten(auftrag: dict) -> dict:
    """Medien prüfen: ffprobe je Clip aus media.json, Proxy gegen Original, Format melden."""
    ch = _charge(auftrag)
    media = _json_lesen(ch, "media.json", "vorbereiten aus dem Projekt-Assistenten")
    clips = media.get("clips", {})
    probleme: list[str] = []
    for pfad in clips:
        zugriff = ch.map_path(pfad)
        if not Path(zugriff).exists():
            probleme.append(f"Datei fehlt: {zugriff}")
    return {"clips": len(clips), "format": media.get("format", {}), "probleme": probleme}


def synchronisieren(auftrag: dict) -> dict:
    """Kamerapaare per Kreuzkorrelation synchronisieren (Kern: sync_charge)."""
    ch = _charge(auftrag)
    media = _json_lesen(ch, "media.json", "vorbereiten")
    try:
        sync = sync_charge(ch, media)
    except AutoCutError as e:
        raise BrueckeError(str(e)) from e
    paare = sync.get("paare", [])
    return {"paare": len(paare), "ok": sum(1 for p in paare if p.get("ok"))}


def pruefen(auftrag: dict) -> dict:
    """Cutlist hart prüfen (Kern: verify_cutlist)."""
    ch = _charge(auftrag)
    pfad = ch.autocut / "cutlist.json"
    if not pfad.exists():
        raise BrueckeError(f"cutlist.json fehlt in {ch.autocut}.\nZuerst den Schnittplan freigeben, "
                           f"dann entsteht die Cutlist.")
    cl = Cutlist.load(pfad)
    media = json.loads((ch.autocut / "media.json").read_text(encoding="utf-8")) \
        if (ch.autocut / "media.json").exists() else {"clips": {}}
    dauern = {p: (d.get("original") or {}).get("duration_s", 0.0) for p, d in media.get("clips", {}).items()}
    ergebnis = verify_cutlist(cl, ch, _woerter(ch), dauern)
    return {"ok": bool(ergebnis.ok), "beats": len(cl.beats),
            "laenge_s": round(total_length_s(cl, ch.config), 2),
            "cutlist_hash": cutlist_hash(pfad),
            "fehler_liste": list(ergebnis.errors), "warnungen": list(ergebnis.warnings)}


def bauen(auftrag: dict) -> dict:
    """Timeline bauen. Ohne bestandene Prüfung wird nichts angefasst.

    ``eingabe["probelauf"]`` rechnet nur den Plan und schreibt das Schnittmodell, ohne Resolve.
    """
    ch = _charge(auftrag)
    vorher = (auftrag.get("eingabe") or {}).get("vorher", {})
    pruefung = vorher.get("pruefen", {})
    if not pruefung.get("ok"):
        raise BrueckeError("Die Prüfung der Cutlist ist nicht bestanden — es wird nichts gebaut.\n"
                           "Erst die gemeldeten Fehler in der Cutlist beheben.")
    cl = Cutlist.load(ch.autocut / "cutlist.json")
    media = _json_lesen(ch, "media.json", "vorbereiten")
    sync = json.loads((ch.autocut / "sync.json").read_text(encoding="utf-8")) \
        if (ch.autocut / "sync.json").exists() else {"paare": []}
    plan = build_timeline_plan(cl, media, sync, _woerter(ch), ch.config)

    fmt = media.get("format", {})
    rate = Rate.von_fliesskomma(float(fmt.get("fps", 25.0)))
    modell = aus_timeline_plan(plan, rate=rate, breite=int(fmt.get("width", 1920)),
                               hoehe=int(fmt.get("height", 1080)),
                               start_tc=str(ch.config.get("start_tc", "01:00:00:00")))
    ziel = ch.autocut / "schnittmodell.json"
    ch.assert_writable(ziel)
    ziel.write_text(json.dumps(modell.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    if (auftrag.get("eingabe") or {}).get("probelauf"):
        return {"probelauf": True, "items": len(plan.items), "marken": len(plan.markers),
                "schnittmodell": modell.to_dict()}

    freigabe = (auftrag.get("eingabe") or {}).get("resolve_projekt", "")
    try:
        resolve = RA.connect()
    except Exception as e:
        raise BrueckeError("DaVinci Resolve ist nicht erreichbar.\nResolve Studio starten, Projekt "
                           "öffnen und unter Einstellungen „External scripting = Local\" setzen.") from e
    sitzung = RA.ResolveSession(resolve, path_map=ch.config.get("path_map"))
    offen = _projektname(sitzung, resolve)
    if freigabe and offen != freigabe:
        raise BrueckeError(f"In Resolve ist „{offen}\" offen, freigegeben ist „{freigabe}\".\n"
                           f"Das richtige Projekt öffnen oder die Freigabe im Programm ändern.")
    return {"probelauf": False, "items": len(plan.items), "marken": len(plan.markers),
            "resolve_projekt": offen, "schnittmodell": modell.to_dict()}


def _projektname(sitzung, resolve) -> str:
    """Name des offenen Resolve-Projekts — erst über die Sitzung, sonst über den Projektmanager.

    Welches Attribut ``ResolveSession`` für das Projekt führt, wird beim Ausführen einmal nachgesehen
    (``grep -n "self.project\|GetCurrentProject" core/autocut/src/niro_autocut/resolve_api.py``) und
    hier festgeschrieben; der zweite Weg ist der dokumentierte API-Weg und trägt in jedem Fall.
    """
    projekt = getattr(sitzung, "project", None)
    if projekt is None:
        projekt = resolve.GetProjectManager().GetCurrentProject()
    if projekt is None:
        raise BrueckeError("In Resolve ist kein Projekt offen.\nProjekt öffnen und erneut starten.")
    return projekt.GetName()


AUSFUEHRER: dict[str, Callable[[dict], dict]] = {
    "vorbereiten": vorbereiten,
    "synchronisieren": synchronisieren,
    "pruefen": pruefen,
    "bauen": bauen,
}


def ausfuehren(auftrag: dict) -> dict:
    """Den zum Auftrag passenden Ausführer aufrufen."""
    name = auftrag.get("name", "")
    fn = AUSFUEHRER.get(name)
    if fn is None:
        raise BrueckeError(f"Unbekannter Schritt '{name}'. Bekannt: " + ", ".join(sorted(AUSFUEHRER)))
    return fn(auftrag)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest bridge/tests/test_schritte.py -q`
Expected: PASS. Schlägt `test_pruefen_liest_cutlist_und_meldet_zahlen` an der Signatur von `verify_cutlist` fehl, die echte Signatur nachlesen (`sed -n '272,290p' core/autocut/src/niro_autocut/cutlist.py`) und den Aufruf anpassen — nicht den Kern.

- [ ] **Step 5: Failing test für Klient und Läufer schreiben**

```python
# bridge/tests/test_laeufer.py
"""Läufer der Brücke: Auftrag holen, ausführen, Ergebnis melden."""
import pytest

from produkt_bruecke.fehler import BrueckeError
from produkt_bruecke.laeufer import Laeufer


class KlientAttrappe:
    """Klient-Ersatz: liefert vorgegebene Aufträge und merkt sich die Meldungen."""

    def __init__(self, auftraege):
        self.auftraege = list(auftraege)
        self.meldungen = []

    def auftrag_holen(self):
        return self.auftraege.pop(0) if self.auftraege else None

    def ergebnis_melden(self, schritt_id, ausgabe=None, fehler=""):
        self.meldungen.append({"id": schritt_id, "ausgabe": ausgabe, "fehler": fehler})


def test_ohne_auftrag_passiert_nichts():
    klient = KlientAttrappe([])
    assert Laeufer(klient).einmal() is False
    assert klient.meldungen == []


def test_erfolgreicher_schritt_wird_gemeldet(monkeypatch):
    klient = KlientAttrappe([{"id": 7, "name": "pruefen", "eingabe": {}, "projekt": {}}])
    monkeypatch.setattr("produkt_bruecke.laeufer.ausfuehren", lambda a: {"beats": 3})

    assert Laeufer(klient).einmal() is True
    assert klient.meldungen == [{"id": 7, "ausgabe": {"beats": 3}, "fehler": ""}]


def test_fehler_wird_als_text_gemeldet_und_bricht_die_bruecke_nicht_ab(monkeypatch):
    klient = KlientAttrappe([{"id": 9, "name": "bauen", "eingabe": {}, "projekt": {}}])

    def kaputt(_auftrag):
        raise BrueckeError("Resolve läuft nicht")

    monkeypatch.setattr("produkt_bruecke.laeufer.ausfuehren", kaputt)

    assert Laeufer(klient).einmal() is True
    assert klient.meldungen[0]["fehler"] == "Resolve läuft nicht"


def test_unerwarteter_fehler_wird_ebenfalls_gemeldet(monkeypatch):
    klient = KlientAttrappe([{"id": 11, "name": "pruefen", "eingabe": {}, "projekt": {}}])

    def kaputt(_auftrag):
        raise ZeroDivisionError("division by zero")

    monkeypatch.setattr("produkt_bruecke.laeufer.ausfuehren", kaputt)

    assert Laeufer(klient).einmal() is True
    assert "ZeroDivisionError" in klient.meldungen[0]["fehler"]


def test_laufen_haelt_nach_der_rundenzahl_an(monkeypatch):
    klient = KlientAttrappe([])
    laeufer = Laeufer(klient, schlafen_s=0.0)
    laeufer.laufen(max_runden=3)
    assert klient.meldungen == []
```

- [ ] **Step 6: Test laufen lassen, Fehlschlag prüfen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest bridge/tests/test_laeufer.py -q`
Expected: FAIL mit `ModuleNotFoundError: No module named 'produkt_bruecke.laeufer'`

- [ ] **Step 7: `klient.py` und `laeufer.py` schreiben**

```python
# bridge/src/produkt_bruecke/klient.py
"""HTTP-Klient der Brücke gegen den Server."""
from __future__ import annotations

import httpx

from .fehler import BrueckeError


class Klient:
    def __init__(self, server: str, token: str, zeitlimit_s: float = 30.0):
        self.server = server.rstrip("/")
        self.kopf = {"Authorization": f"Bearer {token}"}
        self.http = httpx.Client(timeout=zeitlimit_s)

    @classmethod
    def anmelden(cls, server: str, email: str, code: str, geraet: str) -> "Klient":
        antwort = httpx.post(f"{server.rstrip('/')}/v1/anmelden",
                             json={"email": email, "code": code, "geraet": geraet}, timeout=30.0)
        if antwort.status_code != 200:
            raise BrueckeError(f"Anmeldung am Server fehlgeschlagen ({antwort.status_code}): "
                               f"{antwort.text}\nAdresse und Einladungscode prüfen.")
        return cls(server=server, token=antwort.json()["token"])

    def auftrag_holen(self) -> dict | None:
        antwort = self.http.get(f"{self.server}/v1/auftrag", headers=self.kopf)
        if antwort.status_code != 200:
            raise BrueckeError(f"Auftrag holen fehlgeschlagen ({antwort.status_code}): {antwort.text}")
        return antwort.json()

    def ergebnis_melden(self, schritt_id: int, ausgabe: dict | None = None, fehler: str = "") -> None:
        antwort = self.http.post(f"{self.server}/v1/schritte/{schritt_id}/ergebnis", headers=self.kopf,
                                 json={"ausgabe": ausgabe or {}, "fehler": fehler})
        if antwort.status_code != 200:
            raise BrueckeError(f"Ergebnis melden fehlgeschlagen ({antwort.status_code}): {antwort.text}")
```

```python
# bridge/src/produkt_bruecke/laeufer.py
"""Dauerläufer: Auftrag holen, ausführen, Ergebnis melden.

Ein Fehler im Schritt beendet die Brücke nie — er wird als Text gemeldet, der Server hält den Job an,
und die Brücke wartet auf den nächsten Auftrag.
"""
from __future__ import annotations

import time
import traceback

from .fehler import BrueckeError
from .schritte import ausfuehren


class Laeufer:
    def __init__(self, klient, schlafen_s: float = 2.0):
        self.klient = klient
        self.schlafen_s = schlafen_s

    def einmal(self) -> bool:
        """Einen Auftrag abarbeiten. Rückgabe: ob es einen gab."""
        auftrag = self.klient.auftrag_holen()
        if not auftrag:
            return False
        try:
            ausgabe = ausfuehren(auftrag)
        except BrueckeError as e:
            self.klient.ergebnis_melden(auftrag["id"], fehler=str(e))
            return True
        except Exception as e:  # noqa: BLE001 — unerwartete Fehler gehören in die Meldung, nicht ins Log
            self.klient.ergebnis_melden(auftrag["id"],
                                        fehler=f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}")
            return True
        self.klient.ergebnis_melden(auftrag["id"], ausgabe=ausgabe)
        return True

    def laufen(self, max_runden: int | None = None) -> None:
        runden = 0
        while max_runden is None or runden < max_runden:
            runden += 1
            if not self.einmal() and self.schlafen_s:
                time.sleep(self.schlafen_s)
```

- [ ] **Step 8: Tests laufen lassen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest -q`
Expected: PASS

- [ ] **Step 9: CLI-Einstieg der Brücke schreiben**

```python
# bridge/scripts/bruecke.py
"""Brücke starten: holt Aufträge vom Server und führt sie auf diesem Rechner aus.

Aufruf:
    venv/bin/python bridge/scripts/bruecke.py --server http://127.0.0.1:8720 \
        --email admin@niro-productions.de --code <Einladungscode> [--runden N]
"""
from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "bridge" / "src"))
sys.path.insert(0, str(WURZEL / "core" / "autocut" / "src"))
sys.path.insert(0, str(WURZEL / "core" / "transcribe" / "src"))

from produkt_bruecke.fehler import BrueckeError  # noqa: E402
from produkt_bruecke.klient import Klient  # noqa: E402
from produkt_bruecke.laeufer import Laeufer  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Brücke des Produkts starten.")
    ap.add_argument("--server", default="http://127.0.0.1:8720")
    ap.add_argument("--email", required=True)
    ap.add_argument("--code", required=True)
    ap.add_argument("--geraet", default=platform.node())
    ap.add_argument("--runden", type=int, default=None, help="nach N Runden beenden (Standard: endlos)")
    a = ap.parse_args()

    try:
        klient = Klient.anmelden(a.server, a.email, a.code, a.geraet)
    except BrueckeError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1
    print(f"Brücke angemeldet als {a.email} auf {a.geraet}, Server {a.server}")
    Laeufer(klient).laufen(max_runden=a.runden)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 10: Commit**

```bash
cd ~/niro-produkt
git add bridge
git commit -m "feat(bruecke): Schritt-Ausführer für Rohschnitt und Dauerläufer mit Fehlermeldung

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Durchstich von Ende zu Ende

Server und Brücke zusammen, an echten Projektdaten. Erst als Test ohne Resolve, dann von Hand mit Resolve.

**Files:**
- Test: `server/tests/test_durchstich.py`
- Modify: `README.md` (Abschnitt „Durchstich")

**Interfaces:**
- Consumes: alles aus den Tasks 1 bis 5
- Produces: nichts Neues — der Nachweis, dass die Kette trägt

- [ ] **Step 1: Failing test schreiben**

```python
# server/tests/test_durchstich.py
"""Server und Brücke zusammen: Job anlegen, Brücke arbeitet ihn ab, Ergebnisse stehen im Job."""
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from produkt_bruecke.laeufer import Laeufer
from produkt_server.api import baue_app

TESTDATEN = Path(__file__).resolve().parents[2] / "testdaten" / "taxodia"


class KlientUeberTestClient:
    """Brücken-Klient, der statt HTTP den TestClient benutzt."""

    def __init__(self, tc: TestClient, token: str):
        self.tc = tc
        self.kopf = {"Authorization": f"Bearer {token}"}

    def auftrag_holen(self):
        return self.tc.get("/v1/auftrag", headers=self.kopf).json()

    def ergebnis_melden(self, schritt_id, ausgabe=None, fehler=""):
        self.tc.post(f"/v1/schritte/{schritt_id}/ergebnis", headers=self.kopf,
                     json={"ausgabe": ausgabe or {}, "fehler": fehler})


@pytest.fixture()
def umgebung(tmp_path):
    projekt = tmp_path / "Projekt"
    shutil.copytree(TESTDATEN, projekt)
    app = baue_app(db_pfad=tmp_path / "d.db", einladungen={"a@b.de": "code"})
    tc = TestClient(app)
    token = tc.post("/v1/anmelden", json={"email": "a@b.de", "code": "code",
                                          "geraet": "test"}).json()["token"]
    return tc, token, projekt


def test_rohschnitt_job_laeuft_bis_zum_bau_durch(umgebung):
    tc, token, projekt = umgebung
    kopf = {"Authorization": f"Bearer {token}"}
    pid = tc.post("/v1/projekte", headers=kopf,
                  json={"name": "Taxodia", "kunde": "Ludwig", "ordner": str(projekt)}).json()["id"]
    jid = tc.post(f"/v1/projekte/{pid}/jobs", headers=kopf,
                  json={"art": "rohschnitt", "eingabe": {"probelauf": True}}).json()["id"]

    laeufer = Laeufer(KlientUeberTestClient(tc, token), schlafen_s=0.0)
    for _ in range(10):
        if not laeufer.einmal():
            break

    job = tc.get(f"/v1/jobs/{jid}", headers=kopf).json()
    namen = {s["name"]: s for s in job["schritte"]}

    assert namen["pruefen"]["status"] == "fertig", namen["pruefen"]["fehler"]
    assert namen["bauen"]["status"] == "fertig", namen["bauen"]["fehler"]
    assert job["status"] == "fertig"
    assert namen["bauen"]["ausgabe"]["items"] > 0
    assert (projekt / "_studio" / "autocut" / "schnittmodell.json").exists()


def test_fehlgeschlagene_pruefung_haelt_vor_dem_bau_an(umgebung):
    tc, token, projekt = umgebung
    kopf = {"Authorization": f"Bearer {token}"}
    (projekt / "_studio" / "autocut" / "cutlist.json").unlink()
    pid = tc.post("/v1/projekte", headers=kopf,
                  json={"name": "T", "kunde": "L", "ordner": str(projekt)}).json()["id"]
    jid = tc.post(f"/v1/projekte/{pid}/jobs", headers=kopf,
                  json={"art": "rohschnitt", "eingabe": {"probelauf": True}}).json()["id"]

    laeufer = Laeufer(KlientUeberTestClient(tc, token), schlafen_s=0.0)
    for _ in range(10):
        if not laeufer.einmal():
            break

    job = tc.get(f"/v1/jobs/{jid}", headers=kopf).json()
    namen = {s["name"]: s for s in job["schritte"]}

    assert job["status"] == "fehler"
    assert "cutlist.json" in namen["pruefen"]["fehler"]
    assert namen["bauen"]["status"] == "offen", "Nach einem Fehler wird nicht weitergebaut"
```

- [ ] **Step 2: Test laufen lassen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest server/tests/test_durchstich.py -q`
Expected: Zuerst wahrscheinlich FAIL. Häufigster Grund: Der Schritt `synchronisieren` braucht die Originalmedien, die im Testprojekt nicht liegen. Lösung ohne Kernänderung: in `testdaten/taxodia/_studio/config.yaml` einen `path_map`-Eintrag auf den Originalort setzen, oder die Job-Eingabe um `{"ohne_sync": true}` erweitern und in `synchronisieren` als erste Zeile behandeln:

```python
    if (auftrag.get("eingabe") or {}).get("ohne_sync"):
        return {"paare": 0, "ok": 0, "uebersprungen": True}
```

Den zweiten Weg wählen und den Test mit `"eingabe": {"probelauf": True, "ohne_sync": True}` aufrufen — damit läuft der Test ohne Medien, und der Probelauf mit Medien bleibt möglich.

- [ ] **Step 3: Anpassung umsetzen und Tests laufen lassen**

Run: `cd ~/niro-produkt && venv/bin/python -m pytest -q`
Expected: PASS, gesamter Bestand

- [ ] **Step 4: Lauf von Hand mit Resolve**

Resolve Studio starten, das Taxodia-Projekt öffnen, „External scripting = Local" prüfen. Dann in drei Terminals:

```bash
# 1
cd ~/niro-produkt && venv/bin/python server/scripts/serve.py

# 2 — Code aus der Ausgabe von Terminal 1 übernehmen
cd ~/niro-produkt && venv/bin/python bridge/scripts/bruecke.py \
  --server http://127.0.0.1:8720 --email admin@niro-productions.de --code <Code>

# 3
cd ~/niro-produkt
TOKEN=$(curl -s -X POST http://127.0.0.1:8720/v1/anmelden \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@niro-productions.de","code":"<Code>","geraet":"cli"}' | venv/bin/python -c 'import json,sys;print(json.load(sys.stdin)["token"])')
PID=$(curl -s -X POST http://127.0.0.1:8720/v1/projekte -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"Taxodia\",\"kunde\":\"Ludwig\",\"ordner\":\"$HOME/niro-produkt/testdaten/taxodia\"}" \
  | venv/bin/python -c 'import json,sys;print(json.load(sys.stdin)["id"])')
curl -s -X POST "http://127.0.0.1:8720/v1/projekte/$PID/jobs" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"art":"rohschnitt","eingabe":{"probelauf":true,"ohne_sync":true}}'
```

Expected: Terminal 2 arbeitet vier Schritte ab, Terminal 3 zeigt die Job-Nummer, und `testdaten/taxodia/_studio/autocut/schnittmodell.json` enthält Schnitte und Marken. Der Probelauf fasst Resolve nicht an; für den echten Bau `"probelauf": false` und `"resolve_projekt": "<Name des offenen Projekts>"` setzen.

- [ ] **Step 5: README um den Durchstich ergänzen**

Die Befehle aus Step 4 unter der Überschrift `## Durchstich von Hand` in `README.md` aufnehmen, mit dem Hinweis, dass `<Code>` aus der Ausgabe des Servers beim ersten Start stammt.

- [ ] **Step 6: Commit**

```bash
cd ~/niro-produkt
git add server/tests/test_durchstich.py bridge/src/produkt_bruecke/schritte.py README.md
git commit -m "test: Durchstich Server und Brücke am Taxodia-Projekt

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Was dieser Teil nicht enthält

Die folgenden Punkte stehen in den Specs und bekommen eigene Pläne, sobald dieser Teil läuft:

| Teil | Inhalt |
|---|---|
| 2 | KI-Schritte: Transkription über den Server, Aussagen-Pool, Schnittplan, Cutlist mit Verify-Schleife, Modell-Schicht mit Kosten- und Budgetzählung |
| 3 | Oberfläche: React im Fenster, Projekt-Assistent mit Erkennung, Kostenvoranschlag, Fortschritt |
| 4 | Automatische B-Roll mit den Telemetrie-Regeln, Ton, Kantenprüfung, Review lokal |
| 5 | Tauri-Hülle, Installer, Signierung, Auto-Update, Windows |
| 6 | Credit-Ledger mit Stripe, Premiere- und Final-Cut-Writer, Grafik-Generator |

## Offene Punkte, die beim Ausführen entschieden werden

- **Signatur von `verify_cutlist`:** Der Aufruf in `schritte.pruefen` ist nach der Signatur aus `cutlist.py` Zeile 272 geschrieben. Weicht die Reihenfolge der Parameter ab, wird der Aufruf angepasst, nicht der Kern.
- **Felder von `Item` und `MarkerSpec`:** Task 3 Step 5 liest sie; die Zuordnung in `aus_timeline_plan` folgt dem, was dort steht.
- **Medien im Test:** Wenn der Weg über `path_map` zu den Originalen zuverlässig ist, ersetzt er in Task 6 die Abkürzung `ohne_sync`.
- **Projektzugriff in `ResolveSession`:** `_projektname` in Task 5 hat zwei Wege, weil nicht geprüft ist, unter welchem Attribut die Sitzung das Projekt führt. Beim Ausführen einmal nachsehen und den zutreffenden Weg behalten.
