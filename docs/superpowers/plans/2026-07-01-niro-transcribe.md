# NIRO Transcribe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein chat-gesteuertes Werkzeug, das aus WAV-Interviews + PDF-Skript + Briefs pro Ziel-Video eine dramaturgisch/marketingpsychologisch sinnvolle O-Ton-Auswahl mit von–bis-Timestamps als lesbares Dokument ausgibt.

**Architecture:** Python-Paket mit getesteten mechanischen Bausteinen (Transkription via ElevenLabs Scribe + lokalem Whisper, Cache, PDF-Extraktion, Dokument-Rendering). Die kreative Arbeit (Transkript-Abgleich, Aussagen-Zerlegung, Auswahl & Reihenfolge, kritischer Zweit-Durchgang) übernimmt Claude Opus 4.8 direkt in der Session, gesteuert durch versionierte Prompt-/Arbeitsanweisungs-Dateien und abgesichert durch einen Timestamp-Verifikations-Helfer.

**Tech Stack:** Python 3.11+, `requests` (ElevenLabs), `faster-whisper` (lokales Whisper, pip-installierbar, keine Kompilierung), `pypdf`, `pyyaml`, `pytest`.

## Global Constraints

- Sprache der Inhalte und aller Ausgabe-Dokumente: **Deutsch**.
- Oberste Priorität: **Ergebnis vor Skript-Treue** (Qualität/Reihenfolge der Aussagen zählt mehr als wörtliche Skript-Umsetzung).
- **Keine erfundenen Timestamps** — jede von–bis-Zeit muss gegen das Transkript verifizierbar sein.
- Dateiname-Interpretation ist **tolerant** (Muster `Typ_Bereich_Name` ist nur der Normalfall) und wird **sichtbar ins Dokument** geschrieben.
- Standard-Wiederverwendung: **exklusiv** (jede Aussage global nur einem Video), pro Durchlauf umschaltbar.
- Nur **Audio (WAV)** wird verarbeitet; kein Video-Mapping, kein DaVinci-Import in dieser Version.
- Transkript-Ergebnisse werden **gecacht** (Schlüssel = Datei-Hash), damit erneute Läufe nicht neu transkribieren.
- Python 3.11+. Alle Module unter `src/niro_transcribe/`, Tests unter `tests/`.

---

## File Structure

```
src/niro_transcribe/
├── __init__.py
├── config.py            # API-Keys/Settings aus Umgebung
├── models.py            # Dataclasses: Word, Transcript, InterviewMeta, Statement, VideoBrief, GlobalConfig, SelectedStatement, VideoPlan
├── timefmt.py           # Sekunden -> "MM:SS"/"HH:MM:SS"
├── project.py           # Projektordner finden/anlegen, Audiodateien listen
├── filenames.py         # heuristischer Dateiname-Rater (Best Guess)
├── cache.py             # Datei-Hash + JSON-Cache pro Engine
├── pdf_extract.py       # PDF -> Text
├── briefs.py            # briefs.yaml -> VideoBrief[]/GlobalConfig
├── verify.py            # Timestamp-Verifikation gegen Transkript
├── report.py            # VideoPlan -> Markdown, Gesamt-Übersicht
└── transcribe/
    ├── __init__.py      # transcribe_file(): beide Engines + Cache
    ├── elevenlabs.py    # Scribe-Client
    └── whisper.py       # faster-whisper-Wrapper
prompts/
├── reconcile.md         # Arbeitsanweisung: 2 Transkripte -> 1 saubere Fassung
├── segment.md           # Arbeitsanweisung: Transkript -> Aussagen-Pool
├── select-and-order.md  # Arbeitsanweisung: Auswahl + Reihenfolge + Framework
└── critical-review.md   # Arbeitsanweisung: kritischer Zweit-Durchgang
WORKFLOW.md              # End-to-End-Runbook, das Claude pro Projekt abarbeitet
SETUP.md                 # Einmaliges Setup (Keys, faster-whisper)
pyproject.toml
.env.example
tests/
└── ...
```

---

## Task 1: Projekt-Setup & Config

**Files:**
- Create: `pyproject.toml`
- Create: `src/niro_transcribe/__init__.py`
- Create: `src/niro_transcribe/config.py`
- Create: `.env.example`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `Config` dataclass mit `elevenlabs_api_key: str`, `whisper_model: str`; Klassenmethode `Config.load(env: dict | None = None) -> Config`.

- [ ] **Step 1: pyproject.toml anlegen**

```toml
[project]
name = "niro-transcribe"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31",
    "faster-whisper>=1.0",
    "pypdf>=4.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 2: Paket- und Test-Grundgerüst**

`src/niro_transcribe/__init__.py`:

```python
"""NIRO Transcribe — Interview-Transkription und O-Ton-Auswahl."""

__version__ = "0.1.0"
```

`.env.example`:

```bash
# ElevenLabs Scribe API-Key (https://elevenlabs.io -> Profile -> API Keys)
ELEVENLABS_API_KEY=
# Lokales Whisper-Modell für faster-whisper
NIRO_WHISPER_MODEL=large-v3
```

- [ ] **Step 3: Failing test schreiben**

`tests/test_config.py`:

```python
import pytest
from niro_transcribe.config import Config


def test_load_reads_key_from_env():
    cfg = Config.load({"ELEVENLABS_API_KEY": "abc123"})
    assert cfg.elevenlabs_api_key == "abc123"
    assert cfg.whisper_model == "large-v3"  # Default


def test_load_custom_whisper_model():
    cfg = Config.load({"ELEVENLABS_API_KEY": "x", "NIRO_WHISPER_MODEL": "medium"})
    assert cfg.whisper_model == "medium"


def test_load_missing_key_raises():
    with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
        Config.load({})
```

- [ ] **Step 4: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: niro_transcribe.config`

- [ ] **Step 5: Config implementieren**

`src/niro_transcribe/config.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    elevenlabs_api_key: str
    whisper_model: str = "large-v3"

    @classmethod
    def load(cls, env: dict | None = None) -> "Config":
        env = env if env is not None else dict(os.environ)
        key = env.get("ELEVENLABS_API_KEY", "").strip()
        if not key:
            raise ValueError("ELEVENLABS_API_KEY fehlt (siehe .env.example)")
        return cls(
            elevenlabs_api_key=key,
            whisper_model=env.get("NIRO_WHISPER_MODEL", "large-v3").strip() or "large-v3",
        )
```

- [ ] **Step 6: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS (3 passed)

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml src/niro_transcribe/__init__.py src/niro_transcribe/config.py .env.example tests/test_config.py
git commit -m "feat: project scaffolding and config loader"
```

---

## Task 2: Datenmodelle

**Files:**
- Create: `src/niro_transcribe/timefmt.py`
- Create: `src/niro_transcribe/models.py`
- Test: `tests/test_models.py`
- Test: `tests/test_timefmt.py`

**Interfaces:**
- Produces:
  - `fmt_time(seconds: float) -> str` — `"MM:SS"` unter 1h, sonst `"H:MM:SS"`.
  - `Word(text: str, start: float, end: float)`
  - `Transcript(source_file: str, engine: str, text: str, words: list[Word], language: str = "de")` mit `to_dict()`/`from_dict(d)` und `duration() -> float`.
  - `InterviewMeta(quelldatei: str, typ: str, bereich: str, name: str)`
  - `Statement(id: str, quelldatei: str, person: str, bereich: str, von: float, bis: float, text: str, thema: str)` mit `to_dict()`/`from_dict(d)` und `von_bis() -> str` (nutzt `fmt_time`).
  - `VideoBrief(titel: str, fokus: str, person: str, ziel_laenge_sek: int | None = None, dramaturgie: str | None = None, tonalitaet: str | None = None)`
  - `GlobalConfig(wiederverwendung: str = "exklusiv", anzahl_videos: int | None = None)`
  - `SelectedStatement(statement: Statement, begruendung: str, position: int)`
  - `VideoPlan(titel: str, framework: str, framework_begruendung: str, geschaetzte_laenge_sek: int, statements: list[SelectedStatement], roter_faden: str)`

- [ ] **Step 1: Failing test für timefmt**

`tests/test_timefmt.py`:

```python
from niro_transcribe.timefmt import fmt_time


def test_fmt_under_hour():
    assert fmt_time(134.0) == "02:14"


def test_fmt_rounds_down_to_second():
    assert fmt_time(134.9) == "02:14"


def test_fmt_over_hour():
    assert fmt_time(3725.0) == "1:02:05"
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_timefmt.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: timefmt implementieren**

`src/niro_transcribe/timefmt.py`:

```python
from __future__ import annotations


def fmt_time(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_timefmt.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Failing test für models**

`tests/test_models.py`:

```python
from niro_transcribe.models import Word, Transcript, Statement


def test_transcript_roundtrip():
    t = Transcript(
        source_file="a.wav",
        engine="scribe",
        text="hallo welt",
        words=[Word("hallo", 0.0, 0.5), Word("welt", 0.5, 1.0)],
    )
    d = t.to_dict()
    back = Transcript.from_dict(d)
    assert back == t
    assert back.language == "de"


def test_transcript_duration():
    t = Transcript("a.wav", "scribe", "x", [Word("x", 1.0, 3.5)])
    assert t.duration() == 3.5


def test_statement_von_bis_and_roundtrip():
    s = Statement(
        id="s1", quelldatei="a.wav", person="Milena", bereich="Werkzeugmechanik",
        von=134.0, bis=143.0, text="Früher haben wir …", thema="Wandel",
    )
    assert s.von_bis() == "02:14–02:23"
    assert Statement.from_dict(s.to_dict()) == s
```

- [ ] **Step 6: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 7: models implementieren**

`src/niro_transcribe/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from .timefmt import fmt_time


@dataclass
class Word:
    text: str
    start: float
    end: float

    def to_dict(self) -> dict:
        return {"text": self.text, "start": self.start, "end": self.end}

    @classmethod
    def from_dict(cls, d: dict) -> "Word":
        return cls(text=d["text"], start=d["start"], end=d["end"])


@dataclass
class Transcript:
    source_file: str
    engine: str
    text: str
    words: list[Word] = field(default_factory=list)
    language: str = "de"

    def duration(self) -> float:
        return self.words[-1].end if self.words else 0.0

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "engine": self.engine,
            "text": self.text,
            "words": [w.to_dict() for w in self.words],
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Transcript":
        return cls(
            source_file=d["source_file"],
            engine=d["engine"],
            text=d["text"],
            words=[Word.from_dict(w) for w in d.get("words", [])],
            language=d.get("language", "de"),
        )


@dataclass
class InterviewMeta:
    quelldatei: str
    typ: str
    bereich: str
    name: str


@dataclass
class Statement:
    id: str
    quelldatei: str
    person: str
    bereich: str
    von: float
    bis: float
    text: str
    thema: str

    def von_bis(self) -> str:
        return f"{fmt_time(self.von)}–{fmt_time(self.bis)}"

    def to_dict(self) -> dict:
        return {
            "id": self.id, "quelldatei": self.quelldatei, "person": self.person,
            "bereich": self.bereich, "von": self.von, "bis": self.bis,
            "text": self.text, "thema": self.thema,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Statement":
        return cls(
            id=d["id"], quelldatei=d["quelldatei"], person=d["person"],
            bereich=d["bereich"], von=d["von"], bis=d["bis"],
            text=d["text"], thema=d["thema"],
        )


@dataclass
class VideoBrief:
    titel: str
    fokus: str
    person: str
    ziel_laenge_sek: int | None = None
    dramaturgie: str | None = None
    tonalitaet: str | None = None


@dataclass
class GlobalConfig:
    wiederverwendung: str = "exklusiv"
    anzahl_videos: int | None = None


@dataclass
class SelectedStatement:
    statement: Statement
    begruendung: str
    position: int


@dataclass
class VideoPlan:
    titel: str
    framework: str
    framework_begruendung: str
    geschaetzte_laenge_sek: int
    statements: list[SelectedStatement]
    roter_faden: str
```

- [ ] **Step 8: Tests laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_models.py tests/test_timefmt.py -v`
Expected: PASS (6 passed)

- [ ] **Step 9: Commit**

```bash
git add src/niro_transcribe/timefmt.py src/niro_transcribe/models.py tests/test_models.py tests/test_timefmt.py
git commit -m "feat: core data models and time formatting"
```

---

## Task 3: Dateiname-Rater

**Files:**
- Create: `src/niro_transcribe/filenames.py`
- Test: `tests/test_filenames.py`

**Interfaces:**
- Consumes: `InterviewMeta` aus `models`.
- Produces: `guess_meta(filename: str) -> InterviewMeta` — toleranter Best Guess. Trenner `_`, `-`, Leerzeichen. Interpretationsregel: erstes Token = `typ`, letztes = `name`, Rest = `bereich`; bei 2 Tokens `typ`+`name` (bereich=""); bei 1 Token `name`=Stem. Der Wert ist bewusst nur ein Vorschlag, den Claude im Workflow prüft.

- [ ] **Step 1: Failing test**

`tests/test_filenames.py`:

```python
from niro_transcribe.filenames import guess_meta


def test_three_parts_underscore():
    m = guess_meta("Interview_Werkzeugmechaniker_Milena.wav")
    assert (m.typ, m.bereich, m.name) == ("Interview", "Werkzeugmechaniker", "Milena")
    assert m.quelldatei == "Interview_Werkzeugmechaniker_Milena.wav"


def test_multi_word_bereich():
    m = guess_meta("Interview_CNC_Fräsen_Anna.wav")
    assert (m.typ, m.bereich, m.name) == ("Interview", "CNC Fräsen", "Anna")


def test_mixed_separators():
    m = guess_meta("Interview-Lager Max.wav")
    assert (m.typ, m.bereich, m.name) == ("Interview", "Lager", "Max")


def test_two_parts():
    m = guess_meta("Interview_Sabine.wav")
    assert (m.typ, m.bereich, m.name) == ("Interview", "", "Sabine")


def test_single_token():
    m = guess_meta("Milena.wav")
    assert (m.typ, m.bereich, m.name) == ("", "", "Milena")
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_filenames.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementieren**

`src/niro_transcribe/filenames.py`:

```python
from __future__ import annotations

import re
from pathlib import Path
from .models import InterviewMeta


def guess_meta(filename: str) -> InterviewMeta:
    stem = Path(filename).stem
    parts = [p for p in re.split(r"[_\-\s]+", stem) if p]
    if len(parts) >= 3:
        typ, name, bereich = parts[0], parts[-1], " ".join(parts[1:-1])
    elif len(parts) == 2:
        typ, name, bereich = parts[0], parts[1], ""
    elif len(parts) == 1:
        typ, name, bereich = "", parts[0], ""
    else:
        typ = name = bereich = ""
    return InterviewMeta(quelldatei=filename, typ=typ, bereich=bereich, name=name)
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_filenames.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/filenames.py tests/test_filenames.py
git commit -m "feat: tolerant filename metadata guesser"
```

---

## Task 4: Cache

**Files:**
- Create: `src/niro_transcribe/cache.py`
- Test: `tests/test_cache.py`

**Interfaces:**
- Produces:
  - `file_hash(path: str | Path) -> str` — SHA-256 (gestreamt).
  - `TranscriptCache(cache_dir: str | Path)` mit `load(file_hash: str, engine: str) -> dict | None` und `save(file_hash: str, engine: str, data: dict) -> None`.

- [ ] **Step 1: Failing test**

`tests/test_cache.py`:

```python
from niro_transcribe.cache import file_hash, TranscriptCache


def test_file_hash_stable(tmp_path):
    f = tmp_path / "a.wav"
    f.write_bytes(b"audio-bytes")
    h1 = file_hash(f)
    h2 = file_hash(f)
    assert h1 == h2 and len(h1) == 64


def test_cache_roundtrip(tmp_path):
    cache = TranscriptCache(tmp_path / "cache")
    assert cache.load("hash1", "scribe") is None
    cache.save("hash1", "scribe", {"text": "hallo"})
    assert cache.load("hash1", "scribe") == {"text": "hallo"}
    # andere Engine -> getrennt
    assert cache.load("hash1", "whisper") is None
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_cache.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementieren**

`src/niro_transcribe/cache.py`:

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def file_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class TranscriptCache:
    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)

    def _path(self, file_hash: str, engine: str) -> Path:
        return self.cache_dir / f"{file_hash}.{engine}.json"

    def load(self, file_hash: str, engine: str) -> dict | None:
        p = self._path(file_hash, engine)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def save(self, file_hash: str, engine: str, data: dict) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._path(file_hash, engine).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_cache.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/cache.py tests/test_cache.py
git commit -m "feat: hash-based transcript cache"
```

---

## Task 5: PDF-Extraktion

**Files:**
- Create: `src/niro_transcribe/pdf_extract.py`
- Test: `tests/test_pdf_extract.py`

**Interfaces:**
- Produces: `extract_text(pdf_path: str | Path) -> str` — verkettet den Text aller Seiten mit `\n\n`.

- [ ] **Step 1: Failing test (erzeugt eine kleine PDF als Fixture)**

`tests/test_pdf_extract.py`:

```python
from pypdf import PdfWriter
from niro_transcribe.pdf_extract import extract_text


def _make_pdf(path, pages):
    # pypdf kann leere Seiten schreiben; wir prüfen die Verkettungs-/Leselogik
    w = PdfWriter()
    for _ in pages:
        w.add_blank_page(width=200, height=200)
    with open(path, "wb") as f:
        w.write(f)


def test_extract_returns_string_per_page(tmp_path):
    pdf = tmp_path / "skript.pdf"
    _make_pdf(pdf, ["s1", "s2"])
    text = extract_text(pdf)
    assert isinstance(text, str)
    # zwei Seiten -> ein Seitentrenner
    assert text.count("\n\n") >= 1
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_pdf_extract.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementieren**

`src/niro_transcribe/pdf_extract.py`:

```python
from __future__ import annotations

from pathlib import Path
from pypdf import PdfReader


def extract_text(pdf_path: str | Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(pages)
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_pdf_extract.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/pdf_extract.py tests/test_pdf_extract.py
git commit -m "feat: PDF text extraction"
```

---

## Task 6: Briefs-Loader

**Files:**
- Create: `src/niro_transcribe/briefs.py`
- Create: `briefs.example.yaml`
- Test: `tests/test_briefs.py`

**Interfaces:**
- Consumes: `VideoBrief`, `GlobalConfig` aus `models`.
- Produces: `load_briefs(path: str | Path) -> tuple[list[VideoBrief], GlobalConfig]`. YAML-Struktur: Top-Level `global:` (optional) und `videos:` (Liste).

- [ ] **Step 1: Beispiel-YAML anlegen**

`briefs.example.yaml`:

```yaml
global:
  wiederverwendung: exklusiv   # exklusiv | mehrfach
  anzahl_videos: 5
videos:
  - titel: "Video 1 — Einstieg & Ausbildung"
    fokus: "Warum der Betrieb ein guter Start ins Berufsleben ist"
    person: durchmischen
    ziel_laenge_sek: 90
  - titel: "Video 3 — Nachhaltigkeit"
    fokus: "Nachhaltigkeit in der Fertigung"
    person: "Milena"
    ziel_laenge_sek: 85
    dramaturgie: "Problem-Agitate-Solve"
    tonalitaet: "sachlich, glaubwürdig"
```

- [ ] **Step 2: Failing test**

`tests/test_briefs.py`:

```python
from niro_transcribe.briefs import load_briefs


def test_load_briefs(tmp_path):
    y = tmp_path / "briefs.yaml"
    y.write_text(
        "global:\n"
        "  wiederverwendung: mehrfach\n"
        "  anzahl_videos: 2\n"
        "videos:\n"
        "  - titel: V1\n"
        "    fokus: Einstieg\n"
        "    person: durchmischen\n"
        "    ziel_laenge_sek: 90\n"
        "  - titel: V2\n"
        "    fokus: Technik\n"
        "    person: Milena\n"
        "    dramaturgie: AIDA\n",
        encoding="utf-8",
    )
    briefs, gconf = load_briefs(y)
    assert gconf.wiederverwendung == "mehrfach"
    assert gconf.anzahl_videos == 2
    assert len(briefs) == 2
    assert briefs[0].titel == "V1" and briefs[0].ziel_laenge_sek == 90
    assert briefs[1].person == "Milena" and briefs[1].dramaturgie == "AIDA"
    assert briefs[1].ziel_laenge_sek is None


def test_load_briefs_defaults_global(tmp_path):
    y = tmp_path / "briefs.yaml"
    y.write_text("videos:\n  - titel: V1\n    fokus: x\n    person: durchmischen\n", encoding="utf-8")
    _, gconf = load_briefs(y)
    assert gconf.wiederverwendung == "exklusiv"
    assert gconf.anzahl_videos is None
```

- [ ] **Step 3: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_briefs.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implementieren**

`src/niro_transcribe/briefs.py`:

```python
from __future__ import annotations

from pathlib import Path
import yaml
from .models import VideoBrief, GlobalConfig


def load_briefs(path: str | Path) -> tuple[list[VideoBrief], GlobalConfig]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    g = data.get("global", {}) or {}
    gconf = GlobalConfig(
        wiederverwendung=g.get("wiederverwendung", "exklusiv"),
        anzahl_videos=g.get("anzahl_videos"),
    )
    briefs: list[VideoBrief] = []
    for v in data.get("videos", []) or []:
        briefs.append(
            VideoBrief(
                titel=v["titel"],
                fokus=v["fokus"],
                person=v["person"],
                ziel_laenge_sek=v.get("ziel_laenge_sek"),
                dramaturgie=v.get("dramaturgie"),
                tonalitaet=v.get("tonalitaet"),
            )
        )
    return briefs, gconf
```

- [ ] **Step 5: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_briefs.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
git add src/niro_transcribe/briefs.py briefs.example.yaml tests/test_briefs.py
git commit -m "feat: briefs.yaml loader"
```

---

## Task 7: Projektstruktur

**Files:**
- Create: `src/niro_transcribe/project.py`
- Test: `tests/test_project.py`

**Interfaces:**
- Produces: `Project` mit Attributen `root`, `audio_dir`, `cache_dir`, `output_dir`, `skript_pdf` (Path), `briefs_yaml` (Path); Klassenmethode `Project.open(root) -> Project` (legt `audio/`, `cache/`, `output/` an); Methode `audio_files() -> list[Path]` (sortiert, nur `.wav`, case-insensitiv).

- [ ] **Step 1: Failing test**

`tests/test_project.py`:

```python
from niro_transcribe.project import Project


def test_open_creates_dirs(tmp_path):
    proj = Project.open(tmp_path)
    assert proj.audio_dir.is_dir()
    assert proj.cache_dir.is_dir()
    assert proj.output_dir.is_dir()
    assert proj.skript_pdf == tmp_path / "skript.pdf"
    assert proj.briefs_yaml == tmp_path / "briefs.yaml"


def test_audio_files_sorted_wav_only(tmp_path):
    proj = Project.open(tmp_path)
    (proj.audio_dir / "b.wav").write_bytes(b"1")
    (proj.audio_dir / "a.WAV").write_bytes(b"1")
    (proj.audio_dir / "notes.txt").write_text("x")
    names = [p.name for p in proj.audio_files()]
    assert names == ["a.WAV", "b.wav"]
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_project.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementieren**

`src/niro_transcribe/project.py`:

```python
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
            audio_dir=root / "audio",
            cache_dir=root / "cache",
            output_dir=root / "output",
            skript_pdf=root / "skript.pdf",
            briefs_yaml=root / "briefs.yaml",
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
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_project.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/project.py tests/test_project.py
git commit -m "feat: project folder discovery and setup"
```

---

## Task 8: ElevenLabs Scribe-Client

**Files:**
- Create: `src/niro_transcribe/transcribe/__init__.py` (leer für jetzt)
- Create: `src/niro_transcribe/transcribe/elevenlabs.py`
- Test: `tests/test_elevenlabs.py`

**Interfaces:**
- Consumes: `Transcript`, `Word` aus `models`.
- Produces: `transcribe_scribe(path, api_key, *, poster=requests.post) -> Transcript`. Ruft `POST https://api.elevenlabs.io/v1/speech-to-text` mit Header `xi-api-key`, multipart-Feld `file`, Daten `model_id=scribe_v1`, `language_code=deu`. Antwort-JSON: `{"text": str, "words": [{"text","start","end","type"}]}`. Nur Einträge mit `type == "word"` werden zu `Word`. `poster` ist injizierbar für Tests.

- [ ] **Step 1: Failing test (mit gefälschtem poster)**

`tests/test_elevenlabs.py`:

```python
from niro_transcribe.transcribe.elevenlabs import transcribe_scribe


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_transcribe_scribe_parses_words(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"RIFFfake")
    calls = {}

    def fake_poster(url, headers=None, data=None, files=None, timeout=None):
        calls["url"] = url
        calls["headers"] = headers
        calls["data"] = data
        return FakeResponse({
            "text": "hallo welt",
            "words": [
                {"text": "hallo", "start": 0.0, "end": 0.5, "type": "word"},
                {"text": " ", "start": 0.5, "end": 0.5, "type": "spacing"},
                {"text": "welt", "start": 0.5, "end": 1.0, "type": "word"},
            ],
        })

    t = transcribe_scribe(wav, "key123", poster=fake_poster)
    assert calls["headers"]["xi-api-key"] == "key123"
    assert calls["data"]["model_id"] == "scribe_v1"
    assert t.engine == "scribe"
    assert t.text == "hallo welt"
    assert [w.text for w in t.words] == ["hallo", "welt"]
    assert t.words[1].start == 0.5
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_elevenlabs.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementieren**

`src/niro_transcribe/transcribe/__init__.py`:

```python
```

`src/niro_transcribe/transcribe/elevenlabs.py`:

```python
from __future__ import annotations

from pathlib import Path
import requests
from ..models import Transcript, Word

SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


def transcribe_scribe(path, api_key: str, *, poster=requests.post) -> Transcript:
    path = Path(path)
    with open(path, "rb") as fh:
        files = {"file": (path.name, fh, "audio/wav")}
        resp = poster(
            SCRIBE_URL,
            headers={"xi-api-key": api_key},
            data={"model_id": "scribe_v1", "language_code": "deu"},
            files=files,
            timeout=600,
        )
    resp.raise_for_status()
    payload = resp.json()
    words = [
        Word(text=w["text"], start=float(w["start"]), end=float(w["end"]))
        for w in payload.get("words", [])
        if w.get("type") == "word"
    ]
    return Transcript(
        source_file=path.name,
        engine="scribe",
        text=payload.get("text", ""),
        words=words,
    )
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_elevenlabs.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/transcribe/__init__.py src/niro_transcribe/transcribe/elevenlabs.py tests/test_elevenlabs.py
git commit -m "feat: ElevenLabs Scribe client"
```

---

## Task 9: Whisper-Wrapper (faster-whisper)

**Files:**
- Create: `src/niro_transcribe/transcribe/whisper.py`
- Test: `tests/test_whisper.py`

**Interfaces:**
- Consumes: `Transcript`, `Word` aus `models`.
- Produces: `transcribe_whisper(path, model_size="large-v3", *, transcriber=None) -> Transcript`. `transcriber` ist eine Funktion `(path, model_size) -> tuple[Iterable[segment], text]`, wobei jedes `segment` `.words` mit Objekten `(word, start, end)` hat. Default lädt `faster_whisper.WhisperModel` und ruft `.transcribe(path, language="de", word_timestamps=True)`. Injektion hält den Test schnell und offline.

- [ ] **Step 1: Failing test (mit gefälschtem transcriber)**

`tests/test_whisper.py`:

```python
from types import SimpleNamespace
from niro_transcribe.transcribe.whisper import transcribe_whisper


def test_transcribe_whisper_flattens_words(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"RIFFfake")

    def fake_transcriber(path, model_size):
        seg1 = SimpleNamespace(words=[
            SimpleNamespace(word="hallo", start=0.0, end=0.5),
            SimpleNamespace(word=" welt", start=0.5, end=1.0),
        ])
        return [seg1], "hallo welt"

    t = transcribe_whisper(wav, transcriber=fake_transcriber)
    assert t.engine == "whisper"
    assert t.text == "hallo welt"
    assert [w.text for w in t.words] == ["hallo", "welt"]  # getrimmt
    assert t.words[1].end == 1.0
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_whisper.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementieren**

`src/niro_transcribe/transcribe/whisper.py`:

```python
from __future__ import annotations

from pathlib import Path
from ..models import Transcript, Word


def _default_transcriber(path, model_size):
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="auto", compute_type="auto")
    segments, _info = model.transcribe(str(path), language="de", word_timestamps=True)
    segments = list(segments)
    text = "".join(seg.text for seg in segments).strip()
    return segments, text


def transcribe_whisper(path, model_size: str = "large-v3", *, transcriber=None) -> Transcript:
    path = Path(path)
    transcriber = transcriber or _default_transcriber
    segments, text = transcriber(path, model_size)
    words: list[Word] = []
    for seg in segments:
        for w in (seg.words or []):
            words.append(Word(text=w.word.strip(), start=float(w.start), end=float(w.end)))
    return Transcript(source_file=path.name, engine="whisper", text=text, words=words)
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_whisper.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/transcribe/whisper.py tests/test_whisper.py
git commit -m "feat: local Whisper wrapper via faster-whisper"
```

---

## Task 10: Transkriptions-Orchestrator mit Cache

**Files:**
- Modify: `src/niro_transcribe/transcribe/__init__.py`
- Test: `tests/test_transcribe_runner.py`

**Interfaces:**
- Consumes: `TranscriptCache`, `file_hash` aus `cache`; `Transcript` aus `models`; `transcribe_scribe`, `transcribe_whisper`.
- Produces: `transcribe_file(path, cache, api_key, whisper_model="large-v3", *, scribe_fn=transcribe_scribe, whisper_fn=transcribe_whisper) -> dict[str, Transcript]` mit Schlüsseln `"scribe"` und `"whisper"`. Nutzt/aktualisiert den Cache pro Engine; ruft die Engine nur bei Cache-Miss.

- [ ] **Step 1: Failing test**

`tests/test_transcribe_runner.py`:

```python
from niro_transcribe.transcribe import transcribe_file
from niro_transcribe.cache import TranscriptCache
from niro_transcribe.models import Transcript, Word


def _mk(engine):
    return Transcript(source_file="a.wav", engine=engine, text=engine,
                      words=[Word(engine, 0.0, 1.0)])


def test_transcribe_file_uses_and_fills_cache(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"audio")
    cache = TranscriptCache(tmp_path / "cache")
    calls = {"scribe": 0, "whisper": 0}

    def scribe_fn(path, api_key, **kw):
        calls["scribe"] += 1
        return _mk("scribe")

    def whisper_fn(path, model_size="large-v3", **kw):
        calls["whisper"] += 1
        return _mk("whisper")

    out1 = transcribe_file(wav, cache, "key", scribe_fn=scribe_fn, whisper_fn=whisper_fn)
    assert set(out1) == {"scribe", "whisper"}
    assert out1["scribe"].text == "scribe"
    assert calls == {"scribe": 1, "whisper": 1}

    # zweiter Lauf -> alles aus Cache, keine neuen Aufrufe
    out2 = transcribe_file(wav, cache, "key", scribe_fn=scribe_fn, whisper_fn=whisper_fn)
    assert calls == {"scribe": 1, "whisper": 1}
    assert out2["whisper"].text == "whisper"
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_transcribe_runner.py -v`
Expected: FAIL — `ImportError: cannot import name 'transcribe_file'`

- [ ] **Step 3: Implementieren**

`src/niro_transcribe/transcribe/__init__.py`:

```python
from __future__ import annotations

from ..cache import TranscriptCache, file_hash
from ..models import Transcript
from .elevenlabs import transcribe_scribe
from .whisper import transcribe_whisper

__all__ = ["transcribe_file", "transcribe_scribe", "transcribe_whisper"]


def transcribe_file(
    path,
    cache: TranscriptCache,
    api_key: str,
    whisper_model: str = "large-v3",
    *,
    scribe_fn=transcribe_scribe,
    whisper_fn=transcribe_whisper,
) -> dict[str, Transcript]:
    h = file_hash(path)
    result: dict[str, Transcript] = {}

    cached = cache.load(h, "scribe")
    if cached is None:
        t = scribe_fn(path, api_key)
        cache.save(h, "scribe", t.to_dict())
    else:
        t = Transcript.from_dict(cached)
    result["scribe"] = t

    cached = cache.load(h, "whisper")
    if cached is None:
        t = whisper_fn(path, model_size=whisper_model)
        cache.save(h, "whisper", t.to_dict())
    else:
        t = Transcript.from_dict(cached)
    result["whisper"] = t

    return result
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_transcribe_runner.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/transcribe/__init__.py tests/test_transcribe_runner.py
git commit -m "feat: transcription orchestrator with caching"
```

---

## Task 11: Timestamp-Verifikation

**Files:**
- Create: `src/niro_transcribe/verify.py`
- Test: `tests/test_verify.py`

**Interfaces:**
- Consumes: `Statement`, `Transcript` aus `models`.
- Produces: `verify_statement(stmt: Statement, transcript: Transcript, *, min_overlap_words: int = 1) -> list[str]`. Gibt eine Liste von Problem-Meldungen zurück (leer = ok). Prüft: `von < bis`; `von >= 0`; `bis <= transcript.duration() + 0.5`; mindestens `min_overlap_words` Transkript-Wörter liegen (per Mittelpunkt) im Intervall `[von, bis]`.

- [ ] **Step 1: Failing test**

`tests/test_verify.py`:

```python
from niro_transcribe.models import Statement, Transcript, Word
from niro_transcribe.verify import verify_statement


def _tr():
    return Transcript("a.wav", "scribe", "eins zwei drei", [
        Word("eins", 0.0, 1.0), Word("zwei", 1.0, 2.0), Word("drei", 2.0, 3.0),
    ])


def _stmt(von, bis):
    return Statement("s1", "a.wav", "Max", "Lager", von, bis, "zwei", "x")


def test_valid_statement_has_no_problems():
    assert verify_statement(_stmt(0.9, 2.1), _tr()) == []


def test_reversed_times_flagged():
    probs = verify_statement(_stmt(2.0, 1.0), _tr())
    assert any("von" in p and "bis" in p for p in probs)


def test_out_of_bounds_flagged():
    probs = verify_statement(_stmt(0.0, 10.0), _tr())
    assert any("Dauer" in p for p in probs)


def test_no_overlapping_words_flagged():
    probs = verify_statement(_stmt(0.0, 0.05), _tr())
    assert any("kein" in p.lower() for p in probs)
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_verify.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementieren**

`src/niro_transcribe/verify.py`:

```python
from __future__ import annotations

from .models import Statement, Transcript


def verify_statement(stmt: Statement, transcript: Transcript, *, min_overlap_words: int = 1) -> list[str]:
    problems: list[str] = []
    if stmt.von < 0:
        problems.append(f"von ({stmt.von}) ist negativ")
    if stmt.von >= stmt.bis:
        problems.append(f"von ({stmt.von}) liegt nicht vor bis ({stmt.bis})")
    duration = transcript.duration()
    if stmt.bis > duration + 0.5:
        problems.append(f"bis ({stmt.bis}) überschreitet die Transkript-Dauer ({duration})")

    overlap = 0
    for w in transcript.words:
        mid = (w.start + w.end) / 2
        if stmt.von <= mid <= stmt.bis:
            overlap += 1
    if overlap < min_overlap_words:
        problems.append("kein Transkript-Wort liegt im Intervall [von, bis]")

    return problems
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_verify.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/verify.py tests/test_verify.py
git commit -m "feat: timestamp verification against transcript"
```

---

## Task 12: Dokument-Rendering

**Files:**
- Create: `src/niro_transcribe/report.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: `VideoPlan`, `SelectedStatement`, `Statement`, `InterviewMeta` aus `models`.
- Produces:
  - `render_video_plan(plan: VideoPlan) -> str` — Markdown pro Video: Kopf (Titel, Framework + Begründung, geschätzte Länge via `fmt_time`), Tabelle `# | Person | Bereich | Quelldatei | von–bis | Wortlaut | Warum hier` (Statements nach `position` sortiert), Abschnitt „Roter Faden".
  - `render_overview(plans: list[VideoPlan], metas: list[InterviewMeta], unused: list[Statement]) -> str` — Markdown-Gesamtübersicht: erkannte Datei-Interpretationen (aus `metas`), Personen je Video, Liste ungenutzter starker Aussagen.

- [ ] **Step 1: Failing test**

`tests/test_report.py`:

```python
from niro_transcribe.models import (
    Statement, SelectedStatement, VideoPlan, InterviewMeta,
)
from niro_transcribe.report import render_video_plan, render_overview


def _sel(pos, person, von, bis, text, grund):
    st = Statement(f"s{pos}", "Interview_Lager_Max.wav", person, "Lager", von, bis, text, "x")
    return SelectedStatement(statement=st, begruendung=grund, position=pos)


def _plan():
    return VideoPlan(
        titel="Video 3 — Nachhaltigkeit",
        framework="Problem-Agitate-Solve",
        framework_begruendung="passt zum Fokus",
        geschaetzte_laenge_sek=85,
        statements=[
            _sel(2, "Anna", 10.0, 15.0, "Zweite Aussage", "Beweis"),
            _sel(1, "Max", 134.0, 143.0, "Erste Aussage", "Hook"),
        ],
        roter_faden="Vom Problem zur Lösung.",
    )


def test_render_video_plan_contains_key_fields():
    md = render_video_plan(_plan())
    assert "Video 3 — Nachhaltigkeit" in md
    assert "Problem-Agitate-Solve" in md
    assert "01:25" in md  # 85s geschätzte Länge
    assert "02:14–02:23" in md  # Max' Statement
    # Reihenfolge: Position 1 (Max) vor Position 2 (Anna)
    assert md.index("Erste Aussage") < md.index("Zweite Aussage")
    assert "Roter Faden" in md


def test_render_overview_lists_interpretations_and_unused():
    metas = [InterviewMeta("Interview_Lager_Max.wav", "Interview", "Lager", "Max")]
    unused = [Statement("u1", "Interview_Lager_Max.wav", "Max", "Lager", 5.0, 8.0, "ungenutzt stark", "x")]
    md = render_overview([_plan()], metas, unused)
    assert "Interview_Lager_Max.wav" in md
    assert "Max" in md and "Lager" in md
    assert "ungenutzt stark" in md
```

- [ ] **Step 2: Test laufen lassen (muss fehlschlagen)**

Run: `python -m pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementieren**

`src/niro_transcribe/report.py`:

```python
from __future__ import annotations

from .models import VideoPlan, InterviewMeta, Statement
from .timefmt import fmt_time


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def render_video_plan(plan: VideoPlan) -> str:
    lines: list[str] = []
    lines.append(f"# {plan.titel}\n")
    lines.append(
        f"*Framework: {plan.framework} — {plan.framework_begruendung} · "
        f"geschätzte Länge: {fmt_time(plan.geschaetzte_laenge_sek)}*\n"
    )
    lines.append("| # | Person | Bereich | Quelldatei | von–bis | Wortlaut | Warum hier |")
    lines.append("|---|--------|---------|------------|---------|----------|------------|")
    for sel in sorted(plan.statements, key=lambda s: s.position):
        s = sel.statement
        lines.append(
            f"| {sel.position} | {_md_escape(s.person)} | {_md_escape(s.bereich)} | "
            f"`{_md_escape(s.quelldatei)}` | {s.von_bis()} | {_md_escape(s.text)} | "
            f"{_md_escape(sel.begruendung)} |"
        )
    lines.append("")
    lines.append("## Roter Faden\n")
    lines.append(plan.roter_faden)
    lines.append("")
    return "\n".join(lines)


def render_overview(
    plans: list[VideoPlan], metas: list[InterviewMeta], unused: list[Statement]
) -> str:
    lines: list[str] = []
    lines.append("# Gesamt-Übersicht\n")

    lines.append("## Erkannte Datei-Interpretationen\n")
    lines.append("| Quelldatei | Typ | Bereich | Name |")
    lines.append("|------------|-----|---------|------|")
    for m in metas:
        lines.append(
            f"| `{_md_escape(m.quelldatei)}` | {_md_escape(m.typ)} | "
            f"{_md_escape(m.bereich)} | {_md_escape(m.name)} |"
        )
    lines.append("")

    lines.append("## Personen je Video\n")
    for p in plans:
        personen = sorted({sel.statement.person for sel in p.statements})
        lines.append(f"- **{p.titel}**: {', '.join(personen)}")
    lines.append("")

    lines.append("## Ungenutzte starke Aussagen\n")
    if not unused:
        lines.append("_keine_")
    for s in unused:
        lines.append(f"- `{_md_escape(s.quelldatei)}` {s.von_bis()} — {_md_escape(s.text)}")
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Test laufen lassen (muss bestehen)**

Run: `python -m pytest tests/test_report.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/report.py tests/test_report.py
git commit -m "feat: Markdown report and overview rendering"
```

---

## Task 13: Arbeitsanweisungen für die kreative Arbeit (Prompts)

Diese Dateien sind das Deliverable — die präzisen Anweisungen, die Claude Opus 4.8 in der Session befolgt. Kein automatisierter Test; die Prüfung ist die inhaltliche Vollständigkeit gegen die unten genannten Pflicht-Abschnitte.

**Files:**
- Create: `prompts/reconcile.md`
- Create: `prompts/segment.md`
- Create: `prompts/select-and-order.md`
- Create: `prompts/critical-review.md`

- [ ] **Step 1: `prompts/reconcile.md` schreiben**

```markdown
# Arbeitsanweisung: Transkript-Abgleich

**Eingabe:** Zwei Transkripte derselben Audiodatei — `scribe` (ElevenLabs) und
`whisper` — je mit Wort-Timestamps.

**Ziel:** EINE saubere, korrekte deutsche Fassung.

**Regeln:**
1. **Timestamps von Scribe sind der Anker.** Übernimm Scribes Zeiten; Whisper nur
   zur Korrektur von Wortfehlern, Eigennamen, Fachbegriffen und Lücken.
2. Wo beide übereinstimmen: übernehmen.
3. Wo sie abweichen: die plausiblere Variante wählen (Fachkontext,
   Grammatik, Vollständigkeit). Im Zweifel Scribe.
4. Keine Inhalte erfinden. Füllwörter/Versprecher dürfen bereinigt werden, aber
   der Sinn bleibt unangetastet.
5. Behalte pro Wort/Segment die Start-/Endzeit, damit spätere Aussagen exakte
   von–bis-Zeiten bekommen.

**Ausgabe:** bereinigter Fließtext + eine Wortliste mit Timestamps (als Grundlage
für die Aussagen-Zerlegung).
```

- [ ] **Step 2: `prompts/segment.md` schreiben**

```markdown
# Arbeitsanweisung: Aussagen-Zerlegung

**Eingabe:** ein abgeglichenes Transkript (mit Timestamps), plus die erkannte
Datei-Interpretation (`typ/bereich/name`).

**Ziel:** ein Pool einzelner, zitierfähiger **Aussagen**.

**Regeln:**
1. Eine Aussage ist eine in sich geschlossene Sinneinheit — ein vollständiger,
   für sich stehender Gedanke (nicht Satzfragmente, nicht ganze Absätze).
2. Jede Aussage bekommt: `von`, `bis` (aus den Wort-Timestamps),
   `person` (= Name aus Datei-Interpretation), `bereich`, `quelldatei`,
   `text` (Wortlaut), `thema` (kurzes Label).
3. Setze `von`/`bis` auf die Wortgrenzen der ersten/letzten Wörter der Aussage.
4. Bevorzuge natürliche Schnittpunkte (Atempausen, Satzenden) — die Zeiten
   müssen in DaVinci als saubere Schnittkante taugen.
5. Lieber etwas großzügiger schneiden (kleiner Puffer am Rand) als zu knapp.

**Ausgabe:** Liste von Aussagen im `Statement`-Format (siehe `models.py`).
Jede Aussage MUSS mit `verify_statement()` gegen das Transkript geprüft werden;
markierte Probleme vor der Weiterverarbeitung beheben.
```

- [ ] **Step 3: `prompts/select-and-order.md` schreiben**

```markdown
# Arbeitsanweisung: Auswahl & Reihenfolge

**Eingabe:** der Aussagen-Pool (alle Interviews), die PDF-Rahmendaten, die Briefs
pro Ziel-Video, die globale Einstellung (`exklusiv`/`mehrfach`).

**Ziel:** pro Video ein `VideoPlan` mit ausgewählten, geordneten Aussagen.

**Vorgehen:**
1. **Framework wählen** pro Video passend zum Fokus (z. B. AIDA,
   Problem-Agitate-Solve, Hero's Journey). Gibt der Brief eine Dramaturgie vor,
   diese verwenden. Wahl begründen.
2. **Kandidaten filtern:** Bei fester `person` im Brief nur deren Aussagen (plus
   ggf. verbindende); bei `durchmischen` bewusst mehrere Personen kombinieren, so
   dass keine einzelne das ganze Video trägt.
3. **Auswählen & ordnen** entlang des Frameworks. Achte auf:
   - starker Hook zuerst,
   - logischer/emotionaler Bogen,
   - klarer Abschluss / Call-to-Action,
   - keine inhaltlichen Redundanzen,
   - Ziel-Länge (Summe der Aussagen-Dauern ≈ `ziel_laenge_sek`).
4. **Marketingpsychologie:** konkrete, bildhafte, glaubwürdige O-Töne bevorzugen;
   Nutzen/Emotion vor Aufzählung; Spannungsbogen halten.
5. **Exklusivität:** Bei `exklusiv` global koordinieren — plane ALLE Videos
   gemeinsam und vergib jede Aussage nur einmal. Verteile die stärksten Aussagen
   sinnvoll, statt sie dem ersten Video zu geben.
6. Jede Position bekommt eine kurze **Begründung** („Warum hier").

**Ausgabe:** ein `VideoPlan` je Video + Liste der ungenutzten starken Aussagen.
```

- [ ] **Step 4: `prompts/critical-review.md` schreiben**

```markdown
# Arbeitsanweisung: Kritischer Zweit-Durchgang

**Eingabe:** die im ersten Durchgang erstellten `VideoPlan`s.

**Ziel:** jeden Plan kritisch prüfen und verbessern, bevor er ausgegeben wird.

**Checkliste je Video:**
1. **Flow:** Ergibt die Reihenfolge erzählerisch Sinn? Gibt es Brüche?
2. **Redundanz:** Sagen zwei Aussagen dasselbe? Eine streichen/ersetzen.
3. **Emotionaler Bogen:** Baut sich Spannung auf? Gibt es einen starken Einstieg
   und einen klaren Abschluss?
4. **Brief-Treue:** Passt es zu Fokus, Person-Vorgabe und Ziel-Länge?
5. **Marketingwirkung:** Würde das die Zielgruppe überzeugen/bewegen?
6. **Timestamps:** Alle mit `verify_statement()` erneut geprüft, keine Probleme?
7. **Exklusivität:** Keine Aussage doppelt über Videos (falls `exklusiv`)?

**Regel:** Wenn ein Punkt nicht erfüllt ist, den Plan überarbeiten (Aussage
tauschen/umordnen) und erneut prüfen. Erst danach ausgeben.
```

- [ ] **Step 5: Vollständigkeit prüfen**

Sicherstellen, dass alle vier Dateien existieren und jeweils die oben genannten Pflicht-Abschnitte enthalten (Regeln/Checkliste, Ein-/Ausgabe). Prüfen mit:

Run: `ls prompts/ && wc -l prompts/*.md`
Expected: vier `.md`-Dateien, jede nicht leer.

- [ ] **Step 6: Commit**

```bash
git add prompts/
git commit -m "docs: creative work instructions (reconcile, segment, select, review)"
```

---

## Task 14: End-to-End-Runbook & Setup-Doku

Bindet alles zusammen: die Schritt-für-Schritt-Anleitung, die Claude pro Projekt in der Session abarbeitet, plus die einmalige Einrichtung.

**Files:**
- Create: `SETUP.md`
- Create: `WORKFLOW.md`
- Create: `README.md`

- [ ] **Step 1: `SETUP.md` schreiben**

```markdown
# Setup (einmalig)

## 1. Python-Umgebung
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 2. ElevenLabs-Key
- Key unter https://elevenlabs.io → Profile → API Keys erstellen.
- `.env.example` nach `.env` kopieren und `ELEVENLABS_API_KEY` eintragen.

## 3. Lokales Whisper (faster-whisper)
- Wird über `pip install` (Schritt 1) mitinstalliert.
- Erstes Ausführen lädt das Modell (`large-v3`) automatisch herunter.
- Bei wenig RAM/Zeit: in `.env` `NIRO_WHISPER_MODEL=medium` setzen.

## 4. Prüfen
```bash
python -m pytest -q
```
Alle Tests müssen grün sein.
```

- [ ] **Step 2: `WORKFLOW.md` schreiben**

```markdown
# Workflow — pro Dreh (von Claude in der Session ausgeführt)

Voraussetzung: Setup abgeschlossen (siehe SETUP.md), `.env` gefüllt.

1. **Projekt anlegen.** `Project.open(<projektordner>)` erstellt `audio/`,
   `cache/`, `output/`. Der Nutzer legt die WAVs per Finder in `audio/` und sagt
   im Chat Bescheid; `skript.pdf` und Briefs kommen über den Chat (Claude
   speichert PDF nach `skript.pdf` und schreibt `briefs.yaml`).
2. **Einlesen.** `audio_files()` listen; `guess_meta()` je Datei →
   Interpretationen (Claude prüft/korrigiert sie im Chat, wenn nötig).
   `extract_text(skript.pdf)` → Rahmendaten. `load_briefs(briefs.yaml)`.
3. **Transkribieren.** Für jede WAV `transcribe_file()` (Scribe + Whisper,
   gecacht).
4. **Abgleichen.** Pro Datei nach `prompts/reconcile.md` → saubere Fassung.
5. **Zerlegen.** Pro Datei nach `prompts/segment.md` → Aussagen; jede mit
   `verify_statement()` prüfen; Probleme beheben. Ergebnis: Aussagen-Pool.
6. **Auswählen & ordnen.** Nach `prompts/select-and-order.md` → `VideoPlan` je
   Video (+ ungenutzte Aussagen). `exklusiv`/`mehrfach` aus `GlobalConfig`.
7. **Kritischer Zweit-Durchgang.** Nach `prompts/critical-review.md` überarbeiten.
8. **Ausgeben.** `render_video_plan()` je Video → `output/<video>.md`;
   `render_overview()` → `output/uebersicht.md`. Optional PDF-Export.
9. **Zusammenfassen** im Chat: was wurde erzeugt, worauf achten
   (z. B. unsichere Datei-Interpretationen, ungenutzte starke Aussagen).
```

- [ ] **Step 3: `README.md` schreiben**

```markdown
# NIRO Transcribe

Chat-gesteuertes Werkzeug: aus WAV-Interviews + PDF-Skript + Briefs pro Ziel-Video
entstehen dramaturgisch/marketingpsychologisch sortierte O-Ton-Übersichten mit
von–bis-Timestamps für DaVinci.

- **Setup:** siehe [SETUP.md](SETUP.md)
- **Ablauf pro Dreh:** siehe [WORKFLOW.md](WORKFLOW.md)
- **Design/Spec:** siehe [docs/superpowers/specs/2026-07-01-niro-transcribe-design.md](docs/superpowers/specs/2026-07-01-niro-transcribe-design.md)

Transkription: ElevenLabs Scribe + lokales Whisper (faster-whisper).
Gehirn: Claude Opus 4.8 (in der Session).
```

- [ ] **Step 4: Gesamttests laufen lassen**

Run: `python -m pytest -q`
Expected: alle Tests grün.

- [ ] **Step 5: Commit**

```bash
git add SETUP.md WORKFLOW.md README.md
git commit -m "docs: setup guide, end-to-end workflow runbook, README"
```

---

## Self-Review (durchgeführt)

**Spec-Abdeckung:**
- Voll-Batch, chat-gesteuert → WORKFLOW.md (Task 14). ✅
- PDF + Brief pro Video → Task 5 (PDF), Task 6 (Briefs). ✅
- Scribe + Whisper + Abgleich → Task 8, 9, 10 (mechanisch) + `prompts/reconcile.md` (Task 13). ✅
- Gehirn = Opus in Session → Tasks 13/14. ✅
- Ausgabe lesbares Dokument → Task 12. ✅
- Tolerante Dateiname-Interpretation, sichtbar im Dokument → Task 3 + `render_overview` (Task 12). ✅
- Framework pro Video, Brief-Override → `prompts/select-and-order.md`. ✅
- Wiederverwendung exklusiv/mehrfach umschaltbar → `GlobalConfig` (Task 2/6) + Auswahl-Prompt. ✅
- Keine erfundenen Timestamps → Task 11 + Prompts. ✅
- Cache → Task 4/10. ✅
- Nicht im Scope (DaVinci-Import, Video-Mapping) → nicht eingeplant. ✅

**Placeholder-Scan:** keine TBD/TODO; alle Code-Schritte enthalten vollständigen Code.

**Typ-Konsistenz:** `Transcript.to_dict/from_dict`, `Statement.von_bis`, `transcribe_file`-Signatur, `verify_statement`, `render_video_plan/render_overview` durchgängig identisch referenziert.

**Offene Umsetzungspunkte (aus Spec Abschnitt 11):** Whisper-Modellgröße (in `.env` konfigurierbar, Task 1), Chunking sehr langer Interviews (im Reconcile-Prompt als Vorgehen, kein Code nötig), mehrere WAVs pro Person (im Pool über `person` zusammengeführt).
```

