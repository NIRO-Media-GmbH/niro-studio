# AutoCut-Kantenprüfung Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AutoCut misst Schnitte am fertigen Export (Schwarzbild, Schnipsel, Knackser, Tonloch, Wort angeschnitten) und zeichnet Schnittbilder (Filmstreifen + Pegel + Wörter + Schnitte) — Spec `docs/superpowers/specs/2026-09-16-autocut-kantenpruefung-design.md`.

**Architecture:** Reine Logik in `kanten.py` (Schnappschuss, Regeln, Wortkanten, Gesamtprüfung), ffmpeg-Lesen in `kanten_medien.py`, Markdown in `kanten_bericht.py`, PNG in `schnittbild.py`; zwei CLI-Skripte nach dem Muster der vorhandenen `scripts/autocut_*.py` (Charge öffnen, deutsche Meldungen, Protokoll, Exit-Codes). Resolve wird nur gelesen (`read_timeline` + `GetLeftOffset`).

**Tech Stack:** Python 3.12 (AutoCut-venv), numpy, Pillow, PyYAML, ffmpeg/ffprobe 8, pytest; Fake-Resolve aus `tests/fake_resolve.py`.

## Global Constraints

- Schreiben nur in AutoCut-Schreibbereichen: `<Charge>/_intern/autocut/**`, `<Charge>/Ergebnisse/Rohschnitt/**`, `Protokoll.md` (über `Charge.assert_writable` / `append_protokoll`).
- Resolve nur lesen; kein Export per Skript, kein Projekt laden.
- Exit-Codes `autocut_kanten.py`: 0 = keine Befunde, 1 = Befunde, 2 = Voraussetzung fehlt/Fehler. `autocut_schnittbild.py`: 0 ok, 2 Fehler.
- Schwellen nur in `defaults.yaml` → Block `kanten:`; Tests lesen die Werte von dort (keine zweite Quelle).
- Deutsche Meldungen mit Ursache + Abhilfe; Dateinamen ohne Doppelpunkte (Timecode `HH-MM-SS-FF`).
- Herkunftsvermerk in `schnittbild.py`: „nach browser-use/video-use, helpers/timeline_view.py (MIT License, Copyright (c) 2026 Browser Use)".
- zsh: Pfade in Anführungszeichen, Flags ausschreiben. Tests: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q`.
- Commits nur mit ausdrücklichen Pfaden (`git commit -m … -- <pfade>`): im Hauptordner arbeitet parallel eine andere Session (Rappold/Motion).

## Dateien

| Datei | Aufgabe |
|---|---|
| `tools/autocut/src/niro_autocut/resolve_api.py` (ändern) | `read_timeline`: `left_offset`, `speed` je Item |
| `tools/autocut/tests/fake_resolve.py` (ändern) | `FakeTLItem.GetLeftOffset` |
| `tools/autocut/src/niro_autocut/kanten.py` (neu) | Schnappschuss, Schnitte, Maske, Timecode, Kontext, Regeln, Transkripte, Wortkanten, `pruefe` |
| `tools/autocut/src/niro_autocut/kanten_medien.py` (neu) | `export_info`, `bild_metriken` (Cache), `ton_lesen` |
| `tools/autocut/src/niro_autocut/kanten_bericht.py` (neu) | `bericht(erg) -> str` |
| `tools/autocut/src/niro_autocut/schnittbild.py` (neu) | `pegel_db`, `zeichne` |
| `tools/autocut/scripts/autocut_kanten.py` (neu) | CLI Prüfung |
| `tools/autocut/scripts/autocut_schnittbild.py` (neu) | CLI Bild |
| `tools/autocut/defaults.yaml` (ändern) | Block `kanten:` |
| `tools/autocut/tests/test_kanten.py`, `test_kanten_medien.py`, `test_kanten_bericht.py`, `test_schnittbild.py`, `test_kanten_script.py`, `test_schnittbild_script.py` (neu) | Tests |
| `tools/autocut/WORKFLOW-AutoCut.md`, `README.md`, `CLAUDE.md` (ändern) | Doku |

**Übernahme-Konvention:** Code-Blöcke mit vorangestelltem `<!-- datei: <pfad ab Studio-Root> neu -->` sind vollständige neue Dateien, `<!-- datei: <pfad> anhängen -->` wird an die bestehende Datei angehängt (mit einer Leerzeile davor). Alle anderen Änderungen sind als Edit (alt → neu) beschrieben.

---

### Task 1: `read_timeline` liefert Left-Offset und Tempo

**Files:**
- Modify: `tools/autocut/src/niro_autocut/resolve_api.py` (Methode `read_timeline`, Zeilen ~444–479)
- Modify: `tools/autocut/tests/fake_resolve.py` (Klasse `FakeTLItem`, nach `GetSourceEndFrame`)
- Test: `tools/autocut/tests/test_resolve_api.py::test_read_timeline_lists_tracks_items_and_markers`

**Interfaces:**
- Produces: jede Item-Zeile von `ResolveSession.read_timeline(timeline)["tracks"][<Spur>]["items"]` hat zusätzlich `"left_offset": int | None` (Timeline-Frames, `GetLeftOffset`) und `"speed": float | None` (`GetSpeed()["Percentage"]`).

- [ ] **Step 1: Test anpassen (schlägt fehl)**

In `tests/test_resolve_api.py` die erwartete V1-Zeile ersetzen:

```python
    assert v1[0] == {"name": "FX3_1.MP4", "file": FX, "start": 90000, "end": 90072, "duration": 72,
                     "src_in": 244, "src_out": 315, "enabled": True}
```
→
```python
    assert v1[0] == {"name": "FX3_1.MP4", "file": FX, "start": 90000, "end": 90072, "duration": 72,
                     "src_in": 244, "src_out": 315, "enabled": True, "left_offset": 244, "speed": 100.0}
```

- [ ] **Step 2: Test laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_resolve_api.py::test_read_timeline_lists_tracks_items_and_markers`
Expected: FAIL (Dict ohne `left_offset`/`speed`)

- [ ] **Step 3: Fake und `read_timeline` erweitern**

In `tests/fake_resolve.py`, Klasse `FakeTLItem`, direkt nach `GetSourceEndFrame` einfügen:

```python
    def GetLeftOffset(self, *a):
        """Quell-In in Timeline-Frames (Resolve 21.1: 50p-Quelle in 25p-Timeline liefert die halben Quellframes)."""
        fps = float(getattr(self.info["mediaPoolItem"], "props", {}).get("FPS", 25))
        return int(round(int(self.info["startFrame"]) * 25 / fps))
```

In `src/niro_autocut/resolve_api.py` vor `def _fps_str` eine Hilfsfunktion einfügen:

```python
def _speed_pct(v) -> float | None:
    """``TimelineItem.GetSpeed()`` liefert in 21.1 ``{"Percentage": …}``; eine Zahl wird direkt übernommen."""
    if isinstance(v, dict):
        v = v.get("Percentage")
    return None if v is None else float(v)
```

In `read_timeline` die Item-Zeile ersetzen:

```python
                                 "src_out": _safe(it.GetSourceEndFrame, None),
                                 "enabled": _safe(it.GetClipEnabled, None)})
```
→
```python
                                 "src_out": _safe(it.GetSourceEndFrame, None),
                                 "enabled": _safe(it.GetClipEnabled, None),
                                 "left_offset": _safe(lambda: int(it.GetLeftOffset()), None),
                                 "speed": _safe(lambda: _speed_pct(it.GetSpeed()), None)})
```

und im Docstring von `read_timeline` den ersten Satz ergänzen: „Alle Items je Spur (name, file, start, end, duration, src_in, src_out, enabled, left_offset, speed), Marker, Settings." sowie am Ende: „``left_offset`` (GetLeftOffset) ist exakt in Timeline-Frames — für Quellzeiten ``left_offset / fps`` verwenden."

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_resolve_api.py tests/test_resolve_scripts.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- tools/autocut/src/niro_autocut/resolve_api.py tools/autocut/tests/fake_resolve.py tools/autocut/tests/test_resolve_api.py && git commit -m "feat(autocut): read_timeline liest Left-Offset und Tempo je Item" -- tools/autocut/src/niro_autocut/resolve_api.py tools/autocut/tests/fake_resolve.py tools/autocut/tests/test_resolve_api.py
```

### Task 2: `kanten.py` — Schnappschuss, Schnitte, Ton-Maske, Timecode, Kontext

**Files:**
- Create: `tools/autocut/src/niro_autocut/kanten.py`
- Test: `tools/autocut/tests/test_kanten.py`

**Interfaces:**
- Consumes: `read_timeline`-Dict aus Task 1; `niro_autocut.charge.AutoCutError`, `DEFAULTS_FILE`.
- Produces:
  - `ARTEN: tuple[str, ...]` = `("Schwarzbild", "Schnipsel", "Knackser", "Tonloch", "Wort angeschnitten")`, `DATEINAME_ART: dict[str, str]`
  - `snapshot_from_readback(tl: dict, projekt: str, quelle: str = "resolve", gelesen_am: str | None = None) -> dict` — Schnappschuss laut Spec 1 (`spuren[<Spur>]` = Liste von Dicts `name, datei, start, dauer, quell_in, aktiv, tempo`)
  - `schnitte(snap: dict, art: str) -> list[int]` (`art` = `"bild"` | `"ton"`)
  - `ton_maske(snap: dict) -> np.ndarray` (bool, Länge `laenge`)
  - `timecode(frame: int, fps: float, start_tc: str = "01:00:00:00") -> str`, `tc_to_frame(tc: str, fps: float, start_tc: str = "01:00:00:00") -> int`
  - `items_bei(snap, frame) -> list[dict]`, `kontext(snap, frame, bild: list[int], ton: list[int]) -> dict` (`bild_schnitt`/`ton_schnitt` = `{"frame", "abstand"}` oder None, `items`)

- [ ] **Step 1: Tests schreiben**

<!-- datei: tools/autocut/tests/test_kanten.py neu -->
```python
"""Kantenprüfung (Spec 2026-09-16): Schnappschuss, Schnitte, Maske, Timecode, Befund-Regeln, Wortkanten — ohne ffmpeg."""
from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pytest
import yaml

from niro_autocut import kanten as K
from niro_autocut.charge import DEFAULTS_FILE, AutoCutError, Charge

TL = {"name": "T", "start_frame": 90000, "end_frame": 90100, "start_timecode": "01:00:00:00", "fps": "25",
      "tracks": {
          "V1": {"name": "FX3", "items": [
              {"name": "a.MP4", "file": "/x/a.MP4", "start": 90000, "end": 90040, "duration": 40, "src_in": 99,
               "src_out": 139, "enabled": True, "left_offset": 100, "speed": 100.0},
              {"name": "b.MP4", "file": "/x/b.MP4", "start": 90040, "end": 90100, "duration": 60, "src_in": 0,
               "src_out": 60, "enabled": False, "left_offset": 0, "speed": 50.0}]},
          "A1": {"name": "Ton", "items": [
              {"name": "a.MP4", "file": "/x/a.MP4", "start": 90000, "end": 90040, "duration": 40, "src_in": 99,
               "src_out": 139, "enabled": True, "left_offset": 100, "speed": None},
              {"name": "c.MP4", "file": "/x/c.MP4", "start": 90050, "end": 90090, "duration": 40, "src_in": 5,
               "src_out": 45, "enabled": True, "left_offset": None, "speed": None}]}},
      "markers": {}, "n_items": 4}


@pytest.fixture
def cfg() -> dict:
    return yaml.safe_load(DEFAULTS_FILE.read_text(encoding="utf-8"))["kanten"]


def _snap() -> dict:
    return K.snapshot_from_readback(TL, "P", gelesen_am="2026-09-16T12:00:00")


def test_snapshot_relative_frames_left_offset_and_flags():
    s = _snap()
    assert (s["timeline"], s["projekt"], s["fps"], s["laenge"], s["start_timecode"]) == ("T", "P", 25.0, 100, "01:00:00:00")
    assert s["spuren"]["V1"][0] == {"name": "a.MP4", "datei": "/x/a.MP4", "start": 0, "dauer": 40, "quell_in": 100,
                                    "aktiv": True, "tempo": 100.0}
    assert s["spuren"]["V1"][1]["aktiv"] is False and s["spuren"]["V1"][1]["tempo"] == 50.0
    assert s["spuren"]["A1"][1]["quell_in"] is None and s["spuren"]["A1"][1]["start"] == 50
    assert s["quelle"] == "resolve" and s["gelesen_am"] == "2026-09-16T12:00:00"


def test_snapshot_rejects_missing_end_or_fps():
    with pytest.raises(AutoCutError, match="kein Ende"):
        K.snapshot_from_readback({**TL, "end_frame": None}, "P")
    with pytest.raises(AutoCutError, match="Bildrate"):
        K.snapshot_from_readback({**TL, "fps": None}, "P")


def test_schnitte_skip_inactive_items_and_timeline_edges():
    s = _snap()
    assert K.schnitte(s, "bild") == [40]
    assert K.schnitte(s, "ton") == [40, 50, 90]


def test_ton_maske_excludes_item_edges():
    m = K.ton_maske(_snap())
    assert m.shape == (100,)
    assert not m[0] and m[1] and m[38] and not m[39] and not m[45]
    assert not m[50] and m[51] and m[88] and not m[89]


def test_timecode_and_back():
    assert K.timecode(0, 25) == "01:00:00:00"
    assert K.timecode(25 * 61 + 7, 25) == "01:01:01:07"
    assert K.tc_to_frame("01:01:01:07", 25) == 1532
    assert K.timecode(3, 50, "00:59:59:48") == "01:00:00:01"
    with pytest.raises(AutoCutError, match="Timecode"):
        K.tc_to_frame("1:2", 25)


def test_kontext_nearest_cuts_and_items():
    s = _snap()
    k = K.kontext(s, 42, K.schnitte(s, "bild"), K.schnitte(s, "ton"))
    assert k["bild_schnitt"] == {"frame": 40, "abstand": -2}
    assert k["ton_schnitt"] == {"frame": 40, "abstand": -2}
    assert k["items"] == []
    assert K.kontext(s, 10, [], [])["items"] == [{"spur": "A1", "name": "a.MP4"}, {"spur": "V1", "name": "a.MP4"}]
    assert K.kontext(s, 10, [], [])["bild_schnitt"] is None
```

- [ ] **Step 2: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_kanten.py`
Expected: FAIL (`ModuleNotFoundError: niro_autocut.kanten` bzw. ImportError)

- [ ] **Step 3: Implementierung**

<!-- datei: tools/autocut/src/niro_autocut/kanten.py neu -->
```python
"""Kantenprüfung: Schnitte einer AutoCut-Timeline am fertigen Export messen (Spec 2026-09-16).

Reine Logik ohne ffmpeg und ohne Resolve-Verbindung: Schnappschuss aus dem Timeline-Readback, Schnitt-Listen,
Ton-Maske, Timecodes, Befund-Regeln (Schwarzbild, Schnipsel, Knackser, Tonloch, Wort angeschnitten) und Kontext.
Medien lesen: ``kanten_medien.py`` · Bericht: ``kanten_bericht.py`` · Bild: ``schnittbild.py``.
"""
from __future__ import annotations

import datetime as _dt
import unicodedata
from pathlib import Path

import numpy as np

from .charge import AutoCutError

ARTEN = ("Schwarzbild", "Schnipsel", "Knackser", "Tonloch", "Wort angeschnitten")
DATEINAME_ART = {"Schwarzbild": "schwarzbild", "Schnipsel": "schnipsel", "Knackser": "knackser",
                 "Tonloch": "tonloch", "Wort angeschnitten": "wort"}


def _fps_wert(v) -> float:
    """„25", „23.976", 25.0 → float; „29.97 DF" → 29.97; nicht lesbar → 0.0."""
    try:
        return float(str(v).strip().split()[0])
    except (ValueError, IndexError):
        return 0.0


# --- Schnappschuss ---------------------------------------------------------------

def snapshot_from_readback(tl: dict, projekt: str, quelle: str = "resolve", gelesen_am: str | None = None) -> dict:
    """``ResolveSession.read_timeline``-Dict → Schnappschuss mit Frames relativ zum Timeline-Start (Spec 1)."""
    start = int(tl.get("start_frame") or 0)
    if tl.get("end_frame") is None:
        raise AutoCutError(f"Timeline '{tl.get('name')}' liefert kein Ende (GetEndFrame) — Readback unvollständig.")
    fps = _fps_wert(tl.get("fps"))
    if fps <= 0:
        raise AutoCutError(f"Timeline '{tl.get('name')}' ohne lesbare Bildrate (timelineFrameRate={tl.get('fps')!r}).")
    spuren: dict[str, list[dict]] = {}
    for key, track in (tl.get("tracks") or {}).items():
        rows = []
        for it in track.get("items") or []:
            if it.get("start") is None or it.get("duration") is None:
                continue
            q = it.get("left_offset")
            rows.append({"name": it.get("name"), "datei": it.get("file"), "start": int(it["start"]) - start,
                         "dauer": int(it["duration"]), "quell_in": None if q is None else int(q),
                         "aktiv": it.get("enabled") is not False,
                         "tempo": None if it.get("speed") is None else float(it["speed"])})
        spuren[key] = sorted(rows, key=lambda r: r["start"])
    return {"quelle": quelle, "gelesen_am": gelesen_am or _dt.datetime.now().isoformat(timespec="seconds"),
            "projekt": projekt, "timeline": tl.get("name"), "fps": fps, "start_frame": start,
            "start_timecode": tl.get("start_timecode") or "01:00:00:00", "laenge": int(tl["end_frame"]) - start,
            "spuren": spuren}


def schnitte(snap: dict, art: str) -> list[int]:
    """Start- und End-Frames aktiver Items auf V-Spuren (``art="bild"``) bzw. A-Spuren (``"ton"``), ohne 0 und Ende."""
    prefix = {"bild": "V", "ton": "A"}[art]
    n = int(snap["laenge"])
    out: set[int] = set()
    for key, rows in snap["spuren"].items():
        if not key.startswith(prefix):
            continue
        for r in rows:
            if r["aktiv"]:
                out.update(f for f in (r["start"], r["start"] + r["dauer"]) if 0 < f < n)
    return sorted(out)


def ton_maske(snap: dict) -> np.ndarray:
    """Bool je Frame: liegt dort ein aktives A-Item? Erstes und letztes Frame jedes Items zählen nicht (Blenden)."""
    n = int(snap["laenge"])
    m = np.zeros(n, dtype=bool)
    for key, rows in snap["spuren"].items():
        if not key.startswith("A"):
            continue
        for r in rows:
            a, b = max(0, r["start"] + 1), min(n, r["start"] + r["dauer"] - 1)
            if r["aktiv"] and b > a:
                m[a:b] = True
    return m


# --- Timecode ----------------------------------------------------------------------

def _tc_frames(tc: str, base: int) -> int:
    try:
        h, m, s, f = (int(x) for x in str(tc).replace(";", ":").split(":"))
    except ValueError as e:
        raise AutoCutError(f"Timecode nicht lesbar: {tc!r} (erwartet HH:MM:SS:FF)") from e
    return ((h * 60 + m) * 60 + s) * base + f


def timecode(frame: int, fps: float, start_tc: str = "01:00:00:00") -> str:
    """Frame ab Timeline-Start → „HH:MM:SS:FF" nach dem Start-Timecode (ohne Drop-Frame)."""
    base = max(1, int(round(fps)))
    total = _tc_frames(start_tc, base) + int(frame)
    ff, total = total % base, total // base
    ss, total = total % 60, total // 60
    return f"{total // 60:02d}:{total % 60:02d}:{ss:02d}:{ff:02d}"


def tc_to_frame(tc: str, fps: float, start_tc: str = "01:00:00:00") -> int:
    """„HH:MM:SS:FF" → Frame ab Timeline-Start."""
    base = max(1, int(round(fps)))
    return _tc_frames(tc, base) - _tc_frames(start_tc, base)


# --- Kontext -----------------------------------------------------------------------

def items_bei(snap: dict, frame: int) -> list[dict]:
    """Aktive Items, die das Frame abdecken (Spur, Clipname), Spuren in Namensreihenfolge."""
    return [{"spur": key, "name": r["name"]} for key in sorted(snap["spuren"]) for r in snap["spuren"][key]
            if r["aktiv"] and r["start"] <= frame < r["start"] + r["dauer"]]


def kontext(snap: dict, frame: int, bild: list[int], ton: list[int]) -> dict:
    """Nächster Bild- und Ton-Schnitt (Frame, Abstand zum Befund) und die Items am Frame."""
    def naechster(liste):
        if not liste:
            return None
        f = min(liste, key=lambda x: (abs(x - frame), x))
        return {"frame": int(f), "abstand": int(f - frame)}
    return {"bild_schnitt": naechster(bild), "ton_schnitt": naechster(ton), "items": items_bei(snap, frame)}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_kanten.py`
Expected: PASS (6 Tests; die Fixture `cfg` wird erst ab Task 3 benutzt)

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- tools/autocut/src/niro_autocut/kanten.py tools/autocut/tests/test_kanten.py && git commit -m "feat(autocut): Kantenprüfung — Schnappschuss, Schnitte, Ton-Maske, Timecode" -- tools/autocut/src/niro_autocut/kanten.py tools/autocut/tests/test_kanten.py
```

### Task 3: Befund-Regeln Bild und Ton + Schwellen in `defaults.yaml`

**Files:**
- Modify: `tools/autocut/defaults.yaml` (Block `kanten:` anhängen)
- Modify: `tools/autocut/src/niro_autocut/kanten.py` (anhängen)
- Test: `tools/autocut/tests/test_kanten.py` (anhängen)

**Interfaces:**
- Consumes: `kanten.py` aus Task 2.
- Produces (alle Befunde sind Dicts mit mindestens `art`, `frame`, `frames`, `wert`):
  - `laeufe(maske) -> list[tuple[int, int]]` (erstes Frame, letztes + 1)
  - `schwarz_befunde(mittel, streuung, cfg) -> list[dict]`
  - `schnipsel_befunde(diff, mittel, streuung, cfg) -> list[dict]`
  - `knack_messung(audio, sr: int, sample: int, cfg) -> dict` (`spitze`, `umgebung`, `verhaeltnis`, `versatz_ms`, `kanal` 0-basiert)
  - `knack_befunde(audio, sr: int, fps: float, ton_schnitte: list[int], cfg) -> tuple[list[dict], list[float]]` (Befund zusätzlich `spitze`, `versatz_ms`, `kanal` 1-basiert)
  - `rms_dbfs_je_frame(audio, sr: int, fps: float, n_frames: int) -> np.ndarray` (−200 = digitale Stille)
  - `tonloch_befunde(rms_db, maske, cfg) -> list[dict]`
  - `cfg` = `load_config(...)["kanten"]` mit den Schlüsseln aus Step 1.

- [ ] **Step 1: Schwellen anlegen**

<!-- datei: tools/autocut/defaults.yaml anhängen -->
```yaml
kanten:                     # Kantenprüfung am Export (Spec 2026-09-16); Startwerte, Kalibrierung am Taxodia-Export steht im WORKFLOW
  schwarz_mittel_max: 24.0      # Graustufen 0–255 aus dem Export (Limited Range: Schwarz ≈ 16)
  schwarz_streuung_max: 4.0     # Standardabweichung je Frame (96×54) — Schwarzbild hat keine Struktur
  wechsel_diff_min: 18.0        # mittlere Absolutdifferenz zum Vorframe (96×54) ab der ein Bildwechsel „hart" ist
  schnipsel_max_frames: 2       # zwei harte Wechsel höchstens so weit auseinander → Schnipsel
  knack_kante_ms: 10            # Suchfenster um das Schnitt-Sample
  knack_fenster_ms: 250         # Umgebung für das 99. Perzentil der zweiten Differenz
  knack_min: 0.02               # Mindest-Spitze der zweiten Differenz (Vollaussteuerung = 1.0)
  knack_faktor: 6.0             # Spitze / Umgebung ab der ein Knackser gemeldet wird
  tonloch_dbfs: -90.0           # RMS je Frame darunter = digitale Stille
  tonloch_min_frames: 2
  wort_min_ms: 80               # so viel muss von einem Wort an der O-Ton-Kante wegfallen
```

- [ ] **Step 2: Tests anhängen**

<!-- datei: tools/autocut/tests/test_kanten.py anhängen -->
```python
def test_laeufe():
    assert K.laeufe([False, True, True, False, True]) == [(1, 3), (4, 5)]
    assert K.laeufe([]) == []


def test_schwarzbild_runs(cfg):
    mittel, streuung = np.full(10, 80.0), np.full(10, 30.0)
    mittel[4:7], streuung[4:7] = cfg["schwarz_mittel_max"] - 8, 0.5
    got = K.schwarz_befunde(mittel, streuung, cfg)
    assert [(b["art"], b["frame"], b["frames"]) for b in got] == [("Schwarzbild", 4, 3)]
    assert got[0]["wert"] == round(cfg["schwarz_mittel_max"] - 8, 1)


def test_schnipsel_one_frame_merge_and_black(cfg):
    n, hoch = 60, cfg["wechsel_diff_min"] + 20
    d, mittel, streuung = np.zeros(n), np.full(n, 80.0), np.full(n, 30.0)
    d[10] = d[11] = hoch                                           # 1 Frame Schnipsel
    d[20] = d[20 + cfg["schnipsel_max_frames"] + 3] = hoch         # weit genug auseinander → normale Schnitte
    d[35] = d[36] = hoch
    mittel[35], streuung[35] = cfg["schwarz_mittel_max"] - 8, 0.5  # schwarzer Einzelframe → nur Schwarzbild
    d[45] = d[46] = d[47] = hoch                                   # Flackern → ein Befund über 2 Frames
    got = K.schnipsel_befunde(d, mittel, streuung, cfg)
    assert [(b["frame"], b["frames"]) for b in got] == [(10, 1), (45, 2)]
    assert got[0]["wert"] == round(hoch, 1)


def _ton(sekunden: float = 2.0, seed: int = 1) -> np.ndarray:
    sr = 48000
    rng = np.random.default_rng(seed)
    t = np.arange(int(sr * sekunden)) / sr
    x = 0.2 * np.sin(2 * np.pi * 220 * t) + 0.1 * np.sin(2 * np.pi * 1330 * t) + rng.normal(0, 0.001, t.size)
    return np.stack([x, x], axis=1).astype(np.float32)


def test_knackser_only_at_cut_sample(cfg):
    sr, fps, spf = 48000, 25.0, 1920
    sauber = _ton()
    assert K.knack_befunde(sauber, sr, fps, [12], cfg)[0] == []
    sprung = sauber.copy()
    sprung[12 * spf:, 0] += 0.3                                   # Sprung genau am Schnitt-Sample, nur links
    befunde, verh = K.knack_befunde(sprung, sr, fps, [12], cfg)
    assert [(b["art"], b["frame"], b["kanal"]) for b in befunde] == [("Knackser", 12, 1)]
    assert abs(befunde[0]["versatz_ms"]) <= cfg["knack_kante_ms"] and verh[0] >= cfg["knack_faktor"]
    daneben = sauber.copy()
    daneben[12 * spf + int(0.2 * sr):, 0] += 0.3                  # 200 ms neben dem Schnitt
    assert K.knack_befunde(daneben, sr, fps, [12], cfg)[0] == []


def test_knack_messung_handles_file_edges(cfg):
    x = _ton(0.05)
    assert K.knack_messung(x, 48000, 0, cfg)["verhaeltnis"] >= 0.0
    assert K.knack_messung(x[:2], 48000, 1, cfg)["spitze"] == 0.0


def test_tonloch_in_mask_only(cfg):
    sr, fps, spf, n = 48000, 25.0, 1920, 40
    lang, kurz = int(cfg["tonloch_min_frames"]) + 1, int(cfg["tonloch_min_frames"]) - 1
    x = np.random.default_rng(2).normal(0, 0.01, (n * spf, 2)).astype(np.float32)
    x[10 * spf:(10 + lang) * spf] = 0.0
    if kurz > 0:
        x[30 * spf:(30 + kurz) * spf] = 0.0
    rms = K.rms_dbfs_je_frame(x, sr, fps, n)
    assert rms[10] == -200.0 and rms[5] > -50
    maske = np.zeros(n, dtype=bool)
    maske[5:36] = True
    got = K.tonloch_befunde(rms, maske, cfg)
    assert [(b["frame"], b["frames"]) for b in got] == [(10, lang)]
    assert got[0]["wert"] == -200.0
    assert K.tonloch_befunde(rms, np.zeros(n, dtype=bool), cfg) == []
```

- [ ] **Step 3: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_kanten.py`
Expected: FAIL (`AttributeError: module 'niro_autocut.kanten' has no attribute 'laeufe'`)

- [ ] **Step 4: Implementierung anhängen**

<!-- datei: tools/autocut/src/niro_autocut/kanten.py anhängen -->
```python
# --- Befund-Regeln: Bild -----------------------------------------------------------

def laeufe(maske) -> list[tuple[int, int]]:
    """Zusammenhängende True-Bereiche als (erstes Frame, letztes Frame + 1)."""
    m = np.asarray(maske, dtype=bool).astype(np.int8)
    if m.size == 0:
        return []
    d = np.diff(np.concatenate(([0], m, [0])))
    return [(int(a), int(b)) for a, b in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1))]


def _schwarz(mittel, streuung, cfg: dict) -> np.ndarray:
    return (np.asarray(mittel) < cfg["schwarz_mittel_max"]) & (np.asarray(streuung) < cfg["schwarz_streuung_max"])


def schwarz_befunde(mittel, streuung, cfg: dict) -> list[dict]:
    """Schwarzbild: dunkle Frames ohne Struktur als zusammenhängende Läufe (Spec 3)."""
    mittel = np.asarray(mittel, dtype=float)
    return [{"art": "Schwarzbild", "frame": a, "frames": b - a, "wert": round(float(mittel[a:b].mean()), 1)}
            for a, b in laeufe(_schwarz(mittel, streuung, cfg))]


def schnipsel_befunde(diff, mittel, streuung, cfg: dict) -> list[dict]:
    """Schnipsel: zwei harte Bildwechsel höchstens ``schnipsel_max_frames`` auseinander. Direkt aufeinanderfolgende
    Schnipsel verschmelzen; komplett schwarze Schnipsel zählen nur als Schwarzbild."""
    d = np.asarray(diff, dtype=float)
    harte = np.flatnonzero(d >= cfg["wechsel_diff_min"])
    schwarz = _schwarz(mittel, streuung, cfg)
    out: list[dict] = []
    for f1, f2 in zip(harte[:-1], harte[1:]):
        f1, f2 = int(f1), int(f2)
        if f2 - f1 > cfg["schnipsel_max_frames"] or bool(schwarz[f1:f2].all()):
            continue
        wert = round(float(min(d[f1], d[f2])), 1)
        if out and out[-1]["frame"] + out[-1]["frames"] == f1:
            out[-1]["frames"] = f2 - out[-1]["frame"]
            out[-1]["wert"] = min(out[-1]["wert"], wert)
        else:
            out.append({"art": "Schnipsel", "frame": f1, "frames": f2 - f1, "wert": wert})
    return out


# --- Befund-Regeln: Ton ------------------------------------------------------------

def knack_messung(audio, sr: int, sample: int, cfg: dict) -> dict:
    """Spitze der zweiten Differenz ±``knack_kante_ms`` um das Schnitt-Sample gegen das 99. Perzentil der Umgebung
    (±``knack_fenster_ms`` ohne die Kante), je Kanal; zurück kommt der auffälligste Kanal (0-basiert)."""
    x = np.asarray(audio)
    if x.ndim == 1:
        x = x[:, None]
    kante = max(1, int(round(cfg["knack_kante_ms"] * sr / 1000)))
    fenster = int(round(cfg["knack_fenster_ms"] * sr / 1000))
    a, b = max(0, sample - fenster), min(len(x), sample + fenster)
    leer = {"spitze": 0.0, "umgebung": 0.0, "verhaeltnis": 0.0, "versatz_ms": 0.0, "kanal": 0}
    if b - a < 3:
        return leer
    seg = x[a:b].astype(np.float64)
    d2 = np.abs(seg[2:] - 2.0 * seg[1:-1] + seg[:-2])
    idx = np.arange(len(d2)) + a + 1
    nah = np.abs(idx - sample) <= kante
    if not nah.any() or nah.all():
        return leer
    spitze = d2[nah].max(axis=0)
    umgebung = np.percentile(d2[~nah], 99, axis=0)
    verh = spitze / np.maximum(umgebung, 1e-6)
    treffer = (spitze >= cfg["knack_min"]) & (verh >= cfg["knack_faktor"])
    k = int(np.argmax(np.where(treffer, verh, -1.0))) if treffer.any() else int(np.argmax(verh))
    pos = int(idx[nah][int(np.argmax(d2[nah][:, k]))])
    return {"spitze": float(spitze[k]), "umgebung": float(umgebung[k]), "verhaeltnis": float(verh[k]),
            "versatz_ms": round((pos - sample) * 1000 / sr, 1), "kanal": k}


def knack_befunde(audio, sr: int, fps: float, ton_schnitte: list[int], cfg: dict) -> tuple[list[dict], list[float]]:
    """Knackser je Ton-Schnitt (Spec 3). Rückgabe: Befunde und alle Verhältnisse (für die Kalibrierung)."""
    befunde, verhaeltnisse = [], []
    for f in ton_schnitte:
        m = knack_messung(audio, sr, int(round(f * sr / fps)), cfg)
        verhaeltnisse.append(round(m["verhaeltnis"], 2))
        if m["spitze"] >= cfg["knack_min"] and m["verhaeltnis"] >= cfg["knack_faktor"]:
            befunde.append({"art": "Knackser", "frame": int(f), "frames": 1, "wert": round(m["verhaeltnis"], 1),
                            "spitze": round(m["spitze"], 4), "versatz_ms": m["versatz_ms"], "kanal": m["kanal"] + 1})
    return befunde, verhaeltnisse


def rms_dbfs_je_frame(audio, sr: int, fps: float, n_frames: int) -> np.ndarray:
    """RMS in dBFS je Frame-Fenster (``sr/fps`` Samples) über alle Kanäle; digitale Stille = −200."""
    x = np.asarray(audio)
    if x.ndim == 1:
        x = x[:, None]
    out = np.full(int(n_frames), -200.0)
    spf = sr / fps
    for i in range(int(n_frames)):
        seg = x[int(round(i * spf)):int(round((i + 1) * spf))]
        if seg.size:
            r = float(np.sqrt(np.mean(np.square(seg, dtype=np.float64))))
            if r > 0:
                out[i] = max(-200.0, 20.0 * np.log10(r))
    return out


def tonloch_befunde(rms_db, maske, cfg: dict) -> list[dict]:
    """Tonloch: digitale Stille (RMS < ``tonloch_dbfs``) ab ``tonloch_min_frames``, wo ein aktiver Tonclip liegt."""
    rms_db = np.asarray(rms_db, dtype=float)
    m = np.asarray(maske, dtype=bool)
    n = min(rms_db.size, m.size)
    still = (rms_db[:n] < cfg["tonloch_dbfs"]) & m[:n]
    return [{"art": "Tonloch", "frame": a, "frames": b - a, "wert": round(float(rms_db[a:b].max()), 1)}
            for a, b in laeufe(still) if b - a >= cfg["tonloch_min_frames"]]
```

- [ ] **Step 5: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_kanten.py`
Expected: PASS (12 Tests)

- [ ] **Step 6: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- tools/autocut/defaults.yaml tools/autocut/src/niro_autocut/kanten.py tools/autocut/tests/test_kanten.py && git commit -m "feat(autocut): Kantenprüfung — Regeln Schwarzbild, Schnipsel, Knackser, Tonloch" -- tools/autocut/defaults.yaml tools/autocut/src/niro_autocut/kanten.py tools/autocut/tests/test_kanten.py
```

### Task 4: Transkripte, Wortkanten, Export-Wörter und Gesamtprüfung

**Files:**
- Modify: `tools/autocut/src/niro_autocut/kanten.py` (anhängen)
- Test: `tools/autocut/tests/test_kanten.py` (anhängen)

**Interfaces:**
- Consumes: Tasks 2–3; `Charge.load_index()`, `Charge.map_path()`, `Charge.cache_transcript(fp)`; Fixture `charge_dir` aus `tests/conftest.py` (Clip `FX3_0001.MP4`, Wörter Das 1,0–1,2 · ist 1,3–1,5 · meins. 1,6–2,0).
- Produces:
  - `class Transkripte(charge)` mit `eintrag(datei) -> dict | None` und `woerter(datei) -> list[dict] | None`
  - `wort_befunde(snap, transkripte, cfg) -> tuple[list[dict], dict]` (Befund zusätzlich `wort`, `seite` „in"|„out", `spur`, `clip`; Zähler `mit_transkript`, `ohne_transkript`, `ohne_liste`)
  - `export_woerter(snap, transkripte, von_s: float, bis_s: float) -> list[dict]` (`text`, `start`, `end` in Export-Sekunden)
  - `kennzahlen(werte) -> dict` (`n`, `median`, `p95`, `max`), `diff_verteilung(diff, bild_schnitte) -> dict` (`an_schnitten`, `uebrige`)
  - `pruefe(snap, bild: dict | None, audio, sr: int, transkripte, cfg) -> dict` mit `timeline`, `fps`, `laenge`, `umfang`, `zaehlung`, `befunde` (je Befund zusätzlich `nr`, `timecode`, `kontext`; Schnipsel `an_schnitt`), `verteilung`, `warnungen` (leer)

- [ ] **Step 1: Tests anhängen**

<!-- datei: tools/autocut/tests/test_kanten.py anhängen -->
```python
@pytest.fixture
def charge(charge_dir: Path) -> Charge:
    return Charge.open(charge_dir)


def _fx3(charge: Charge) -> str:
    return charge.load_index()[0]["path"]


class _Stub:
    """Ersatz für Transkripte: liefert für jeden Clip dieselbe Wortliste (oder None)."""

    def __init__(self, woerter):
        self._w = woerter

    def woerter(self, datei):
        return self._w


def test_transkripte_match_path_nfd_and_unique_name(charge):
    import json
    index = charge.load_index()
    index[0]["path"] = str(Path(index[0]["path"]).parent.parent / "Jörn" / "FX3_0001.MP4")
    (charge.intern / "transcripts_index.json").write_text(json.dumps(index), encoding="utf-8")
    t = K.Transkripte(charge)
    pfad = index[0]["path"]
    assert [w["text"] for w in t.woerter(pfad)] == ["Das", "ist", "meins."]
    assert t.woerter(unicodedata.normalize("NFD", pfad)) is not None
    assert t.woerter("/Volumes/SSD/woanders/FX3_0001.MP4") is not None      # eindeutiger Dateiname
    assert t.woerter("/x/unbekannt.MP4") is None and t.woerter(None) is None


def _ton_snap(datei: str, items: list[tuple[int, int, int]]) -> dict:
    """Schnappschuss mit A1-Items (start, dauer, quell_in) eines Clips."""
    return {"fps": 25.0, "laenge": 200, "start_timecode": "01:00:00:00", "timeline": "T",
            "spuren": {"A1": [{"name": Path(datei).name, "datei": datei, "start": s, "dauer": d, "quell_in": q,
                               "aktiv": True, "tempo": None} for s, d, q in items]}}


def test_wort_befunde_in_and_out_edges(charge, cfg):
    assert cfg["wort_min_ms"] <= 100
    snap = _ton_snap(_fx3(charge), [(0, 10, 35), (20, 1, 31)])      # Item 1: In 1,40 s in „ist", Out 1,80 s in „meins."
    snap["spuren"]["A1"].append({"name": "x.MP4", "datei": "/x/x.MP4", "start": 40, "dauer": 5, "quell_in": 0,
                                 "aktiv": True, "tempo": None})       # Clip ohne Transkript
    befunde, z = K.wort_befunde(snap, K.Transkripte(charge), cfg)
    assert [(b["seite"], b["wort"], b["frame"], b["wert"], b["spur"]) for b in befunde] == [
        ("in", "ist", 0, 100, "A1"), ("out", "meins.", 9, 200, "A1")]
    assert (z["mit_transkript"], z["ohne_transkript"], z["ohne_liste"]) == (2, 1, ["x.MP4"])


def test_wort_befunde_threshold_zero_length_and_tempo(cfg):
    assert 40 < cfg["wort_min_ms"] <= 120
    woerter = [{"text": "kurz", "start": 1.0, "end": 1.0}, {"text": "lang", "start": 2.0, "end": 3.0}]

    def item(name, start, dauer, quell_in, tempo=None):
        return {"name": name, "datei": name, "start": start, "dauer": dauer, "quell_in": quell_in, "aktiv": True,
                "tempo": tempo}

    snap = {"fps": 25.0, "laenge": 500, "start_timecode": "01:00:00:00", "timeline": "T", "spuren": {"A1": [
        item("a", 0, 10, 25),              # In genau auf einem Wort der Länge 0
        item("b", 100, 25, 50, 100.0),     # In = Wortanfang, Out = Wortende → nichts weg
        item("c", 200, 10, 51, 50.0),      # Tempo 50 % → nicht geprüft, nicht gezählt
        item("d", 300, 24, 51),            # In 40 ms im Wort → unter der Grenze
        item("e", 400, 22, 53),            # In 120 ms im Wort → Befund
    ]}}
    befunde, z = K.wort_befunde(snap, _Stub(woerter), cfg)
    assert [(b["clip"], b["seite"], b["wert"]) for b in befunde] == [("e", "in", 120)]
    assert z["mit_transkript"] == 4


def test_export_woerter_shift_and_window(charge):
    snap = _ton_snap(_fx3(charge), [(100, 25, 25)])                 # Export 4,0–5,0 s zeigt Quelle 1,0–2,0 s
    t = K.Transkripte(charge)
    assert K.export_woerter(snap, t, 4.25, 4.55) == [{"text": "ist", "start": 4.3, "end": 4.5}]
    assert [w["text"] for w in K.export_woerter(snap, t, 0.0, 10.0)] == ["Das", "ist", "meins."]


def test_kennzahlen_and_diff_verteilung():
    assert K.kennzahlen([]) == {"n": 0}
    assert K.kennzahlen([1, 2, 3, 4]) == {"n": 4, "median": 2.5, "p95": 3.85, "max": 4.0}
    d = np.array([0.0, 1.0, 2.0, 50.0, 2.0, 1.0, 3.0])
    v = K.diff_verteilung(d, [3])
    assert v["an_schnitten"]["n"] == 1 and v["an_schnitten"]["max"] == 50.0
    assert v["uebrige"] == {"n": 3, "median": 1.0, "p95": 2.8, "max": 3.0}


def test_pruefe_combines_rules_numbers_and_context(cfg):
    n, fps, sr, spf = 50, 25.0, 48000, 1920
    snap = {"quelle": "plan", "gelesen_am": "x", "projekt": "P", "timeline": "T", "fps": fps, "start_frame": 0,
            "start_timecode": "01:00:00:00", "laenge": n, "spuren": {
                "V1": [{"name": "v", "datei": "v", "start": 0, "dauer": 20, "quell_in": 0, "aktiv": True, "tempo": 100.0},
                       {"name": "w", "datei": "w", "start": 20, "dauer": 30, "quell_in": 0, "aktiv": True, "tempo": 100.0}],
                "A1": [{"name": "a", "datei": "/x/a", "start": 0, "dauer": 50, "quell_in": 0, "aktiv": True, "tempo": None}]}}
    mittel, streuung = np.full(n, 90.0, dtype=np.float32), np.full(n, 30.0, dtype=np.float32)
    diff = np.zeros(n, dtype=np.float32)
    diff[20] = cfg["wechsel_diff_min"] + 20
    mittel[35], streuung[35] = cfg["schwarz_mittel_max"] - 8, 0.5
    audio = np.random.default_rng(3).normal(0, 0.01, (n * spf, 2)).astype(np.float32)
    lang = int(cfg["tonloch_min_frames"]) + 1
    audio[40 * spf:(40 + lang) * spf] = 0.0
    erg = K.pruefe(snap, {"mittel": mittel, "streuung": streuung, "diff": diff}, audio, sr, _Stub(None), cfg)
    assert erg["zaehlung"] == {"Schwarzbild": 1, "Schnipsel": 0, "Knackser": 0, "Tonloch": 1, "Wort angeschnitten": 0}
    assert [(b["nr"], b["art"], b["frame"], b["timecode"]) for b in erg["befunde"]] == [
        (1, "Schwarzbild", 35, "01:00:01:10"), (2, "Tonloch", 40, "01:00:01:15")]
    assert erg["befunde"][0]["kontext"]["bild_schnitt"] == {"frame": 20, "abstand": -15}
    assert erg["umfang"] == {"bild_schnitte": 1, "ton_schnitte": 0, "mit_transkript": 0, "ohne_transkript": 1,
                             "ohne_liste": ["a"]}
    assert erg["verteilung"]["diff"]["an_schnitten"]["n"] == 1 and erg["warnungen"] == []
```

- [ ] **Step 2: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_kanten.py`
Expected: FAIL (`AttributeError: … has no attribute 'Transkripte'`)

- [ ] **Step 3: Implementierung anhängen**

<!-- datei: tools/autocut/src/niro_autocut/kanten.py anhängen -->
```python
# --- Wortkanten --------------------------------------------------------------------

def _nfc(p) -> str:
    return unicodedata.normalize("NFC", str(p))


class Transkripte:
    """Scribe-Wörter je Clip aus dem Transkript-Index der Charge: Treffer über den Pfad (auch über ``path_map``),
    sonst über einen eindeutigen Dateinamen."""

    def __init__(self, charge):
        self.charge = charge
        try:
            index = charge.load_index()
        except AutoCutError:
            index = []
        self.nach_pfad: dict[str, dict] = {}
        namen: dict[str, list[dict]] = {}
        for e in index:
            if not e.get("fingerprint") or not e.get("path"):
                continue
            for p in (e["path"], charge.map_path(e["path"])):
                self.nach_pfad[_nfc(p)] = e
            namen.setdefault(_nfc(Path(e["path"]).name), []).append(e)
        self.nach_name = {k: v[0] for k, v in namen.items() if len(v) == 1}
        self._woerter: dict[str, list[dict]] = {}

    def eintrag(self, datei) -> dict | None:
        if not datei:
            return None
        return self.nach_pfad.get(_nfc(datei)) or self.nach_name.get(_nfc(Path(str(datei)).name))

    def woerter(self, datei) -> list[dict] | None:
        """Wörter (``text``, ``start``, ``end`` in Quellsekunden) oder None, wenn der Clip kein Transkript hat."""
        e = self.eintrag(datei)
        if e is None:
            return None
        fp = e["fingerprint"]
        if fp not in self._woerter:
            daten = self.charge.cache_transcript(fp) or {}
            self._woerter[fp] = [w for w in daten.get("words") or []
                                 if w.get("start") is not None and w.get("end") is not None]
        return self._woerter[fp]


def _ton_items(snap: dict):
    """Aktive A-Items mit Quell-In und Tempo 100 % (oder unbekannt), Spuren in Namensreihenfolge."""
    for key in sorted(k for k in snap["spuren"] if k.startswith("A")):
        for r in snap["spuren"][key]:
            if r["aktiv"] and r["quell_in"] is not None and (r["tempo"] is None or abs(r["tempo"] - 100.0) < 0.01):
                yield key, r


def wort_befunde(snap: dict, transkripte, cfg: dict) -> tuple[list[dict], dict]:
    """Wort angeschnitten: O-Ton-Kante liegt in einem Wort, von dem mindestens ``wort_min_ms`` wegfallen (Spec 3)."""
    fps = float(snap["fps"])
    grenze = cfg["wort_min_ms"] / 1000.0
    befunde: list[dict] = []
    mit, ohne = 0, []
    for key, r in _ton_items(snap):
        woerter = transkripte.woerter(r["datei"])
        if woerter is None:
            ohne.append(r["name"] or str(r["datei"]))
            continue
        mit += 1
        for seite, t, frame in (("in", r["quell_in"] / fps, r["start"]),
                                ("out", (r["quell_in"] + r["dauer"]) / fps, r["start"] + r["dauer"] - 1)):
            for w in woerter:
                ws, we = float(w["start"]), float(w["end"])
                if not ws < t < we:
                    continue
                weg = (we - t) if seite == "out" else (t - ws)
                if weg >= grenze:
                    befunde.append({"art": "Wort angeschnitten", "frame": int(frame), "frames": 1,
                                    "wert": int(round(weg * 1000)), "wort": w.get("text"), "seite": seite,
                                    "spur": key, "clip": r["name"]})
    return befunde, {"mit_transkript": mit, "ohne_transkript": len(ohne), "ohne_liste": sorted(set(ohne))}


def export_woerter(snap: dict, transkripte, von_s: float, bis_s: float) -> list[dict]:
    """Wörter der aktiven Tonclips in Export-Sekunden, nur innerhalb ihres Items und des Bereichs [von_s, bis_s]."""
    fps = float(snap["fps"])
    out = []
    for _key, r in _ton_items(snap):
        woerter = transkripte.woerter(r["datei"])
        if not woerter:
            continue
        a, b = r["start"] / fps, (r["start"] + r["dauer"]) / fps
        versatz = a - r["quell_in"] / fps
        for w in woerter:
            s, e = float(w["start"]) + versatz, float(w["end"]) + versatz
            if e > max(a, von_s) and s < min(b, bis_s):
                out.append({"text": w.get("text"), "start": round(s, 3), "end": round(e, 3)})
    return sorted(out, key=lambda w: w["start"])


# --- Gesamtprüfung -----------------------------------------------------------------

def kennzahlen(werte) -> dict:
    """Anzahl, Median, 95. Perzentil und Maximum (für die Kalibrierung im Bericht)."""
    w = np.asarray(list(werte), dtype=float)
    if w.size == 0:
        return {"n": 0}
    return {"n": int(w.size), "median": round(float(np.median(w)), 2),
            "p95": round(float(np.percentile(w, 95)), 2), "max": round(float(w.max()), 2)}


def diff_verteilung(diff, bild_schnitte: list[int]) -> dict:
    """``diff`` an Bild-Schnitten gegen die übrigen Frames (ohne ±1 Frame um Schnitte, ohne Frame 0)."""
    d = np.asarray(diff, dtype=float)
    an = np.zeros(d.size, dtype=bool)
    for f in bild_schnitte:
        if 0 <= f < d.size:
            an[f] = True
    nahe = an.copy()
    nahe[1:] |= an[:-1]
    nahe[:-1] |= an[1:]
    if d.size:
        nahe[0] = True
    return {"an_schnitten": kennzahlen(d[an]), "uebrige": kennzahlen(d[~nahe])}


def pruefe(snap: dict, bild: dict | None, audio, sr: int, transkripte, cfg: dict) -> dict:
    """Alle Befund-Regeln auf Schnappschuss und Messwerte anwenden (ohne Bilder).

    ``bild``: Arrays ``mittel``, ``streuung``, ``diff`` je Frame oder None; ``audio``: Samples × Kanäle oder None.
    """
    fps, n = float(snap["fps"]), int(snap["laenge"])
    b_schnitte, t_schnitte = schnitte(snap, "bild"), schnitte(snap, "ton")
    befunde: list[dict] = []
    verteilung: dict = {}
    if bild is not None:
        befunde += schwarz_befunde(bild["mittel"], bild["streuung"], cfg)
        befunde += schnipsel_befunde(bild["diff"], bild["mittel"], bild["streuung"], cfg)
        verteilung["diff"] = diff_verteilung(bild["diff"], b_schnitte)
    if audio is not None:
        kb, verh = knack_befunde(audio, sr, fps, t_schnitte, cfg)
        befunde += kb
        befunde += tonloch_befunde(rms_dbfs_je_frame(audio, sr, fps, n), ton_maske(snap), cfg)
        verteilung["knack_verhaeltnis"] = kennzahlen(verh)
    wb, zaehler = wort_befunde(snap, transkripte, cfg)
    befunde += wb
    befunde.sort(key=lambda x: (x["frame"], ARTEN.index(x["art"])))
    for nr, x in enumerate(befunde, 1):
        x["nr"] = nr
        x["timecode"] = timecode(x["frame"], fps, snap["start_timecode"])
        x["kontext"] = kontext(snap, x["frame"], b_schnitte, t_schnitte)
        if x["art"] == "Schnipsel":
            x["an_schnitt"] = any(abs(s - x["frame"]) <= 1 or abs(s - (x["frame"] + x["frames"])) <= 1
                                  for s in b_schnitte)
    return {"timeline": snap["timeline"], "fps": fps, "laenge": n,
            "umfang": {"bild_schnitte": len(b_schnitte), "ton_schnitte": len(t_schnitte), **zaehler},
            "zaehlung": {a: sum(1 for x in befunde if x["art"] == a) for a in ARTEN},
            "befunde": befunde, "verteilung": verteilung, "warnungen": []}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_kanten.py`
Expected: PASS (18 Tests)

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- tools/autocut/src/niro_autocut/kanten.py tools/autocut/tests/test_kanten.py && git commit -m "feat(autocut): Kantenprüfung — Wortkanten, Export-Wörter, Gesamtprüfung" -- tools/autocut/src/niro_autocut/kanten.py tools/autocut/tests/test_kanten.py
```

### Task 5: Export lesen (`kanten_medien.py`) und Bericht (`kanten_bericht.py`)

**Files:**
- Create: `tools/autocut/src/niro_autocut/kanten_medien.py`
- Create: `tools/autocut/src/niro_autocut/kanten_bericht.py`
- Test: `tools/autocut/tests/test_kanten_medien.py`, `tools/autocut/tests/test_kanten_bericht.py`

**Interfaces:**
- Consumes: `media._which`, `media.ffprobe`, `media.fingerprint`, `media._assert_not_nas`; `kanten.ARTEN`.
- Produces:
  - `kanten_medien.SR = 48000`, `export_info(path) -> dict` (`datei`, `fps`, `frames`, `breite`, `hoehe`, `ton`, `dauer_s`)
  - `bild_metriken(path, cache_dir, n_erwartet: int | None = None) -> dict` (np.float32-Arrays `mittel`, `streuung`, `diff`)
  - `ton_lesen(path, sr: int = SR) -> np.ndarray` (float32, Samples × 2)
  - `kanten_bericht.bericht(erg: dict) -> str` — `erg` = Ergebnis von `kanten.pruefe` plus `export` (aus `export_info`), `schnappschuss` (`quelle`, `gelesen_am`, `projekt`), `parameter` (cfg); Befunde optional mit `bild` (Pfad)

- [ ] **Step 1: Tests schreiben**

<!-- datei: tools/autocut/tests/test_kanten_medien.py neu -->
```python
"""kanten_medien: ffprobe-Kennzahlen, Bild-Metriken mit Cache, Ton — an einem mit ffmpeg erzeugten Testclip."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from niro_autocut import kanten_medien as KM
from niro_autocut.charge import AutoCutError

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")


def _clip(pfad: Path, schwarz_frame: int) -> Path:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=25:duration=2",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
                    "-vf", f"drawbox=enable='eq(n,{schwarz_frame})':color=black:t=fill",
                    "-c:v", "mpeg4", "-q:v", "2", "-g", "1", "-c:a", "pcm_s16le", "-ac", "2", str(pfad)], check=True)
    return pfad


def test_export_info_metriken_cache_und_ton(tmp_path):
    clip = _clip(tmp_path / "t.mov", 20)
    info = KM.export_info(clip)
    assert (info["frames"], info["fps"], info["breite"], info["ton"]) == (50, 25.0, 160, True)
    m = KM.bild_metriken(clip, tmp_path / "cache", n_erwartet=50)
    assert m["mittel"].shape == (50,) and m["diff"][0] == 0.0
    assert m["mittel"][20] < 20 and m["streuung"][20] < 2 and m["mittel"][19] > 40
    assert m["diff"][20] > 20 and m["diff"][21] > 20
    assert len(list((tmp_path / "cache").glob("*.npz"))) == 1
    assert np.array_equal(KM.bild_metriken(clip, tmp_path / "cache")["diff"], m["diff"])     # Cache-Treffer
    x = KM.ton_lesen(clip)
    assert x.shape[1] == 2 and abs(x.shape[0] - 96000) <= 1024 and 0.05 < float(np.abs(x).max()) <= 1.0


def test_bild_und_ton_melden_unlesbaren_export(tmp_path):
    kaputt = tmp_path / "kaputt.mov"
    kaputt.write_bytes(b"kein video")
    with pytest.raises(AutoCutError, match="nicht lesbar"):
        KM.bild_metriken(kaputt, tmp_path / "cache")
    with pytest.raises(AutoCutError, match="nicht lesbar"):
        KM.ton_lesen(kaputt)
```

<!-- datei: tools/autocut/tests/test_kanten_bericht.py neu -->
```python
"""kanten_bericht: Markdown mit und ohne Befunde."""
from __future__ import annotations

from niro_autocut.kanten import ARTEN
from niro_autocut.kanten_bericht import bericht


def _erg(befunde: list[dict]) -> dict:
    return {"timeline": "T", "fps": 25.0, "laenge": 50,
            "export": {"datei": "/e/T.mov", "fps": 25.0, "frames": 50, "breite": 160, "hoehe": 90, "ton": True,
                       "dauer_s": 2.0},
            "schnappschuss": {"quelle": "plan", "gelesen_am": "2026-09-16T12:00:00", "projekt": "P"},
            "umfang": {"bild_schnitte": 3, "ton_schnitte": 2, "mit_transkript": 1, "ohne_transkript": 1,
                       "ohne_liste": ["x.MP4"]},
            "zaehlung": {a: sum(1 for b in befunde if b["art"] == a) for a in ARTEN},
            "befunde": befunde,
            "verteilung": {"diff": {"an_schnitten": {"n": 3, "median": 40.0, "p95": 50.0, "max": 55.0},
                                    "uebrige": {"n": 0}},
                           "knack_verhaeltnis": {"n": 2, "median": 1.2, "p95": 1.9, "max": 2.0}},
            "parameter": {"knack_faktor": 6.0}, "warnungen": ["Bild zu Befund 2: x"]}


def test_bericht_ohne_befunde():
    text = bericht(_erg([]))
    assert text.startswith("# Kantenprüfung — T\n") and "**Keine Befunde.**" in text and "| Nr |" not in text
    assert "Median 40.0" in text and "x.MP4" in text and "Warnung: Bild zu Befund 2: x" in text
    assert "knack_faktor 6.0" in text and text.endswith("\n")


def test_bericht_tabelle_mit_kontext():
    b = {"nr": 1, "art": "Knackser", "frame": 12, "frames": 1, "wert": 9.5, "spitze": 0.3, "versatz_ms": 0.0,
         "kanal": 1, "timecode": "01:00:00:12", "bild": "/p/k.png",
         "kontext": {"bild_schnitt": {"frame": 12, "abstand": 0}, "ton_schnitt": None,
                     "items": [{"spur": "A1", "name": "a|b.MP4"}]}}
    text = bericht(_erg([b]))
    assert "**1 Befund** — Knackser: 1" in text
    zeile = next(z for z in text.splitlines() if z.startswith("| 1 |"))
    assert "01:00:00:12" in zeile and "9.5 ×" in zeile and "a/b.MP4" in zeile and "`/p/k.png`" in zeile
    assert "Bild-Schnitt +0 F" in zeile and "Spitze 0.3" in zeile
```

- [ ] **Step 2: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_kanten_medien.py tests/test_kanten_bericht.py`
Expected: FAIL (ImportError `kanten_medien` / `kanten_bericht`)

- [ ] **Step 3: Implementierung**

<!-- datei: tools/autocut/src/niro_autocut/kanten_medien.py neu -->
```python
"""Export für die Kantenprüfung lesen (Spec 2026-09-16, Abschnitt 2): Kennzahlen per ffprobe, Graustufen-Metriken
je Frame (Mittel, Streuung, Differenz zum Vorframe; Cache je Fingerprint) und den Ton als float32-PCM."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .charge import AutoCutError
from .media import _assert_not_nas, _which, ffprobe, fingerprint

BREITE, HOEHE = 96, 54
SR = 48000


def export_info(path) -> dict:
    """Bildrate, Frame-Zahl, Größe, Ton und Dauer des Exports (ffprobe)."""
    info = ffprobe(path)
    return {"datei": str(path), "fps": float(info.fps), "frames": int(info.nb_frames), "breite": int(info.width),
            "hoehe": int(info.height), "ton": bool(info.has_audio), "dauer_s": round(float(info.duration_s), 3)}


def _metriken_lauf(path: Path, hwaccel: bool) -> tuple[dict | None, str]:
    cmd = [_which("ffmpeg"), "-hide_banner", "-loglevel", "error"]
    if hwaccel:
        cmd += ["-hwaccel", "videotoolbox"]
    cmd += ["-i", str(path), "-map", "0:v:0", "-vf", f"scale={BREITE}:{HOEHE}:flags=area,format=gray",
            "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    groesse = BREITE * HOEHE
    mittel, streuung, diff = [], [], []
    vorher = None
    with tempfile.TemporaryFile() as fehler:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=fehler)
        try:
            while True:
                buf = proc.stdout.read(groesse)
                if len(buf) < groesse:
                    break
                f = np.frombuffer(buf, dtype=np.uint8).astype(np.float32)
                mittel.append(float(f.mean()))
                streuung.append(float(f.std()))
                diff.append(0.0 if vorher is None else float(np.abs(f - vorher).mean()))
                vorher = f
        finally:
            proc.stdout.close()
            rc = proc.wait()
        fehler.seek(0)
        meldung = fehler.read().decode("utf-8", "replace").strip()[-500:]
    if rc != 0 or not mittel:
        return None, meldung or f"ffmpeg Exit {rc}"
    return {"mittel": np.asarray(mittel, dtype=np.float32), "streuung": np.asarray(streuung, dtype=np.float32),
            "diff": np.asarray(diff, dtype=np.float32)}, meldung


def bild_metriken(path, cache_dir, n_erwartet: int | None = None) -> dict:
    """Mittel, Streuung und Differenz zum Vorframe je Frame (Graustufen 96×54).

    Erst mit VideoToolbox, bei Fehler oder abweichender Frame-Zahl (``n_erwartet``) in Software; Ergebnis im Cache
    ``<cache_dir>/<fingerprint>.npz`` (Fingerprint: Name, Größe, mtime).
    """
    path, cache_dir = Path(path), Path(cache_dir)
    _assert_not_nas(cache_dir, "Kanten-Cache")
    ziel = cache_dir / f"{fingerprint(path)}.npz"
    if ziel.exists():
        with np.load(ziel) as z:
            return {k: z[k] for k in ("mittel", "streuung", "diff")}
    m, meldung = _metriken_lauf(path, hwaccel=True)
    if m is None or (n_erwartet is not None and m["mittel"].size != n_erwartet):
        m, meldung = _metriken_lauf(path, hwaccel=False)
    if m is None:
        raise AutoCutError(f"Bild des Exports nicht lesbar ({path.name}): {meldung}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    teil = cache_dir / f"{ziel.stem}.part.npz"
    np.savez(teil, **m)
    teil.replace(ziel)
    return m


def ton_lesen(path, sr: int = SR) -> np.ndarray:
    """Ton des Exports als float32-Array (Samples × 2 Kanäle, auf Stereo gemischt)."""
    cmd = [_which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-i", str(path), "-map", "0:a:0", "-vn",
           "-ac", "2", "-ar", str(sr), "-f", "f32le", "-acodec", "pcm_f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise AutoCutError(f"Ton des Exports nicht lesbar ({Path(path).name}): "
                           f"{r.stderr.decode('utf-8', 'replace').strip()[-500:]}")
    x = np.frombuffer(r.stdout, dtype=np.float32)
    return x[: x.size - x.size % 2].reshape(-1, 2)
```

<!-- datei: tools/autocut/src/niro_autocut/kanten_bericht.py neu -->
```python
"""Markdown-Bericht der Kantenprüfung: ``Ergebnisse/Rohschnitt/<video>-kanten.md`` (Spec 2026-09-16, Abschnitt 6)."""
from __future__ import annotations

from .kanten import ARTEN

EINHEIT = {"Schwarzbild": "Mittel", "Schnipsel": "Diff", "Knackser": "×", "Tonloch": "dBFS",
           "Wort angeschnitten": "ms"}


def _kz(k: dict | None) -> str:
    if not k or not k.get("n"):
        return "—"
    return f"n {k['n']}, Median {k['median']}, p95 {k['p95']}, Max {k['max']}"


def _kontext_text(x: dict) -> str:
    teile = []
    if x["art"] == "Knackser":
        teile.append(f"Spitze {x.get('spitze')} bei {x.get('versatz_ms')} ms, Kanal {x.get('kanal')}")
    elif x["art"] == "Wort angeschnitten":
        teile.append(f"„{x.get('wort')}“ an der {x.get('seite')}-Kante, {x.get('spur')} {x.get('clip')}")
    elif x["art"] == "Schnipsel":
        teile.append("an Schnitt" if x.get("an_schnitt") else "ohne Schnitt")
    k = x.get("kontext") or {}
    for key, label in (("bild_schnitt", "Bild-Schnitt"), ("ton_schnitt", "Ton-Schnitt")):
        if k.get(key):
            teile.append(f"{label} {k[key]['abstand']:+d} F")
    items = ", ".join(f"{i['spur']} {i['name']}" for i in (k.get("items") or [])[:4])
    if items:
        teile.append(items)
    return "; ".join(teile).replace("|", "/")


def bericht(erg: dict) -> str:
    ex, sn, um, z = erg["export"], erg["schnappschuss"], erg["umfang"], erg["zaehlung"]
    n = len(erg["befunde"])
    zeilen = [f"# Kantenprüfung — {erg['timeline']}", "",
              f"- Export: `{ex['datei']}` ({ex['frames']} Frames @ {ex['fps']} fps, {ex['breite']}×{ex['hoehe']}, "
              f"Ton {'ja' if ex['ton'] else 'nein'})",
              f"- Schnappschuss: {sn['quelle']} ({sn['gelesen_am']}, Projekt „{sn['projekt']}“)",
              f"- Umfang: {um['bild_schnitte']} Bild-Schnitte, {um['ton_schnitte']} Ton-Schnitte, "
              f"{um['mit_transkript']} Tonclips mit Transkript, {um['ohne_transkript']} ohne",
              "", "## Ergebnis", ""]
    if n == 0:
        zeilen.append("**Keine Befunde.**")
    else:
        zeilen.append(f"**{n} {'Befund' if n == 1 else 'Befunde'}** — "
                      + ", ".join(f"{a}: {z[a]}" for a in ARTEN if z.get(a)))
    zeilen.append("")
    if um.get("ohne_liste"):
        zeilen += ["Tonclips ohne Transkript (keine Wortprüfung): " + ", ".join(um["ohne_liste"][:12]), ""]
    if n:
        zeilen += ["Befunde sind Verdachtsfälle — erst das Schnittbild ansehen, dann handeln.", "",
                   "| Nr | Art | Timecode | Frames | Wert | Kontext | Bild |", "|---|---|---|---|---|---|---|"]
        for x in erg["befunde"]:
            bild = f"`{x['bild']}`" if x.get("bild") else "—"
            zeilen.append(f"| {x['nr']} | {x['art']} | {x['timecode']} | {x['frames']} | "
                          f"{x['wert']} {EINHEIT[x['art']]} | {_kontext_text(x)} | {bild} |")
        zeilen.append("")
    v = erg.get("verteilung") or {}
    zeilen += ["## Messwerte (Kalibrierung)", ""]
    if "diff" in v:
        zeilen.append(f"- Bild-Diff an Schnitten: {_kz(v['diff'].get('an_schnitten'))} · übrige Frames: "
                      f"{_kz(v['diff'].get('uebrige'))}")
    if "knack_verhaeltnis" in v:
        zeilen.append(f"- Knack-Verhältnis an Ton-Schnitten: {_kz(v['knack_verhaeltnis'])}")
    p = erg.get("parameter") or {}
    zeilen += ["", "Parameter: " + ", ".join(f"{k} {p[k]}" for k in sorted(p)), ""]
    zeilen += [f"- Warnung: {w}" for w in erg.get("warnungen") or []]
    return "\n".join(zeilen).rstrip() + "\n"
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_kanten_medien.py tests/test_kanten_bericht.py`
Expected: PASS (4 Tests)

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- tools/autocut/src/niro_autocut/kanten_medien.py tools/autocut/src/niro_autocut/kanten_bericht.py tools/autocut/tests/test_kanten_medien.py tools/autocut/tests/test_kanten_bericht.py && git commit -m "feat(autocut): Kantenprüfung — Export lesen und Bericht" -- tools/autocut/src/niro_autocut/kanten_medien.py tools/autocut/src/niro_autocut/kanten_bericht.py tools/autocut/tests/test_kanten_medien.py tools/autocut/tests/test_kanten_bericht.py
```

### Task 6: Schnittbild (`schnittbild.py`)

**Files:**
- Create: `tools/autocut/src/niro_autocut/schnittbild.py`
- Test: `tools/autocut/tests/test_schnittbild.py`

**Interfaces:**
- Consumes: `kanten.timecode`, `media._which`, `charge.AutoCutError`.
- Produces:
  - Layout-Konstanten `BREITE`, `STREIFEN_Y`, `STREIFEN_H`, `PEGEL_Y`, `PEGEL_H`, `HOEHE`, Farben `HG`, `ZELLE`
  - `pegel_db(video, von_s: float, bis_s: float, schritt_s: float = 0.01) -> np.ndarray`
  - `zeichne(video, von_s: float, bis_s: float, ausgabe, *, woerter=(), bild_schnitte=(), ton_schnitte=(), marken=(), frames: int = 10, beschriftung: str | None = None, tc_start: str | None = None, fps: float | None = None) -> Path`

- [ ] **Step 1: Tests schreiben**

<!-- datei: tools/autocut/tests/test_schnittbild.py neu -->
```python
"""schnittbild: PNG aus einem mit ffmpeg erzeugten Testclip (Filmstreifen, Pegel, Wörter, Schnitte, Marken)."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from niro_autocut import schnittbild as SB
from niro_autocut.charge import AutoCutError

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")


@pytest.fixture
def clip(tmp_path: Path) -> Path:
    p = tmp_path / "c.mov"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=25:duration=2",
                    "-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000:duration=2",
                    "-c:v", "mpeg4", "-q:v", "3", "-c:a", "pcm_s16le", str(p)], check=True)
    return p


def test_pegel_db_level_of_sine(clip):
    db = SB.pegel_db(clip, 0.0, 1.0)
    assert 90 <= db.size <= 101
    assert -30 < float(np.median(db)) < -15          # lavfi-Sinus: Amplitude 1/8 → RMS ≈ −21 dBFS


def test_zeichne_png_mit_woertern_schnitten_und_marken(clip, tmp_path):
    woerter = [{"text": "Hallo", "start": 0.2, "end": 0.6}, {"text": "Ja,", "start": 0.9, "end": 0.9},
               {"text": "draußen", "start": 1.5, "end": 1.9}, {"text": "ohne", "start": None, "end": None}]
    ziel = SB.zeichne(clip, 0.1, 1.9, tmp_path / "out" / "b.png", woerter=woerter, bild_schnitte=[1.0, 5.0],
                      ton_schnitte=[1.04], marken=[(1.0, "1 Knackser")], frames=6, beschriftung="Test",
                      tc_start="01:00:00:00", fps=25.0)
    assert ziel == tmp_path / "out" / "b.png"
    with Image.open(ziel) as im:
        assert im.size == (SB.BREITE, SB.HOEHE)
        rgb = im.convert("RGB")
        mitte = rgb.getpixel((SB.RAND + 150, SB.STREIFEN_Y + SB.STREIFEN_H // 2))
        assert mitte not in (SB.HG, SB.ZELLE)                     # Filmstreifen zeigt Bildinhalt
        pegel = [rgb.getpixel((x, y)) for x in range(SB.RAND + 10, SB.BREITE - SB.RAND - 10, 40)
                 for y in range(SB.PEGEL_Y + 5, SB.PEGEL_Y + SB.PEGEL_H - 5, 20)]
        assert any(p not in (SB.HG, SB.ZELLE) for p in pegel)       # Pegelband gezeichnet


def test_zeichne_fehler(clip, tmp_path):
    with pytest.raises(AutoCutError, match="nicht nach dem Anfang"):
        SB.zeichne(clip, 1.0, 1.0, tmp_path / "x.png")
    with pytest.raises(AutoCutError, match="nicht gefunden"):
        SB.zeichne(tmp_path / "fehlt.mov", 0.0, 1.0, tmp_path / "x.png")
```

- [ ] **Step 2: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_schnittbild.py`
Expected: FAIL (ImportError `schnittbild`)

- [ ] **Step 3: Implementierung**

<!-- datei: tools/autocut/src/niro_autocut/schnittbild.py neu -->
```python
"""Schnittbild: Filmstreifen, Pegelband, Wörter und Schnittlinien eines Zeitbereichs als ein PNG (Spec 2026-09-16, 4).

Idee und Grundlayout nach browser-use/video-use, helpers/timeline_view.py (MIT License, Copyright (c) 2026 Browser Use).
Eigene Umsetzung: Pegel in dBFS statt normierter Wellenform, Wörter in zwei Zeilen, Bild- und Ton-Schnittlinien,
Befund-Marken und Timecode-Leiste.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .charge import AutoCutError
from .kanten import timecode
from .media import _which

BREITE, RAND = 1920, 50
KOPF_Y, LABEL_Y, STREIFEN_Y, STREIFEN_H = 10, 42, 60, 180
WORT_Y = STREIFEN_Y + STREIFEN_H + 14
PEGEL_Y, PEGEL_H = WORT_Y + 40, 200
LEISTE_Y = PEGEL_Y + PEGEL_H + 8
HOEHE = LEISTE_Y + 56
DB_MIN = -60.0
HG, ZELLE, TEXT, DIM = (18, 18, 22), (28, 28, 34), (235, 235, 235), (125, 125, 135)
PEGEL, PAUSE = (140, 180, 255), (60, 100, 150, 90)
BILD_LINIE, TON_LINIE, MARKE = (0, 200, 220), (255, 150, 40), (235, 60, 60)
SCHRIFTEN = ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Helvetica.ttc",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")


def _schrift(groesse: int):
    for p in SCHRIFTEN:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, groesse)
            except OSError:
                continue
    return ImageFont.load_default()


def _standbild(video: Path, t: float, ziel: Path) -> Image.Image | None:
    cmd = [_which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(0.0, t):.3f}", "-i", str(video),
           "-frames:v", "1", "-vf", "scale=320:-2", "-q:v", "4", str(ziel)]
    if subprocess.run(cmd, capture_output=True).returncode != 0 or not ziel.exists():
        return None
    with Image.open(ziel) as im:
        return im.convert("RGB")


def pegel_db(video, von_s: float, bis_s: float, schritt_s: float = 0.01) -> np.ndarray:
    """RMS in dBFS je ``schritt_s`` (Mono-Mix, 16 kHz); ohne Ton oder bei Fehler ein leeres Array."""
    sr = 16000
    cmd = [_which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, von_s):.3f}", "-i", str(video),
           "-t", f"{max(0.01, bis_s - von_s):.3f}", "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le",
           "-acodec", "pcm_f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return np.zeros(0)
    x = np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)
    n = max(1, int(round(schritt_s * sr)))
    k = x.size // n
    if k == 0:
        return np.zeros(0)
    rms = np.sqrt(np.mean(x[: k * n].reshape(k, n) ** 2, axis=1))
    return np.maximum(20.0 * np.log10(np.maximum(rms, 1e-10)), -200.0)


def zeichne(video, von_s: float, bis_s: float, ausgabe, *, woerter=(), bild_schnitte=(), ton_schnitte=(), marken=(),
            frames: int = 10, beschriftung: str | None = None, tc_start: str | None = None,
            fps: float | None = None) -> Path:
    """PNG für [von_s, bis_s] (Sekunden in ``video``).

    ``woerter``: Dicts mit ``text``/``start``/``end`` in denselben Sekunden; ``bild_schnitte``/``ton_schnitte``:
    Sekunden; ``marken``: (Sekunde, Kurztext). Mit ``tc_start`` und ``fps`` zeigen Kopf, Frames und Leiste Timecodes
    (Sekunde 0 = ``tc_start``).
    """
    video, ausgabe = Path(video), Path(ausgabe)
    if not video.is_file():
        raise AutoCutError(f"Schnittbild: Datei nicht gefunden: {video}")
    if bis_s <= von_s:
        raise AutoCutError(f"Schnittbild: Ende {bis_s:.2f} s liegt nicht nach dem Anfang {von_s:.2f} s.")
    frames = max(1, int(frames))
    spanne = bis_s - von_s
    x0, x1 = RAND, BREITE - RAND

    def x_von(t: float) -> int:
        return int(round(x0 + (t - von_s) / spanne * (x1 - x0)))

    def zeit(t: float) -> str:
        return timecode(int(round(t * fps)), fps, tc_start) if (tc_start and fps) else f"{t:.2f}s"

    def y_db(v: float) -> int:
        return PEGEL_Y + PEGEL_H - int(round((max(DB_MIN, min(0.0, v)) - DB_MIN) / -DB_MIN * PEGEL_H))

    bild = Image.new("RGB", (BREITE, HOEHE), HG)
    z = ImageDraw.Draw(bild, "RGBA")
    gross, klein = _schrift(22), _schrift(13)
    kopf = f"{video.name}   {zeit(von_s)} → {zeit(bis_s)}   ({spanne:.2f} s)"
    if beschriftung:
        kopf += f"   · {beschriftung}"
    z.text((RAND, KOPF_Y), kopf, fill=TEXT, font=gross)

    # 1. Filmstreifen
    zelle = (x1 - x0 - 4 * (frames - 1)) // frames
    zeiten = [von_s + spanne / 2] if frames == 1 else [von_s + i * spanne / (frames - 1) for i in range(frames)]
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(zeiten):
            cx = x0 + i * (zelle + 4)
            z.rectangle((cx, STREIFEN_Y, cx + zelle, STREIFEN_Y + STREIFEN_H), fill=ZELLE)
            z.text((cx, LABEL_Y), zeit(t), fill=DIM, font=klein)
            t_bild = max(von_s, bis_s - 0.05) if (frames > 1 and i == frames - 1) else t
            im = _standbild(video, t_bild, Path(tmp) / f"{i:03d}.jpg")
            if im is None:
                continue
            sk = min(zelle / im.width, STREIFEN_H / im.height)
            im = im.resize((max(1, int(im.width * sk)), max(1, int(im.height * sk))), Image.LANCZOS)
            bild.paste(im, (cx + (zelle - im.width) // 2, STREIFEN_Y + (STREIFEN_H - im.height) // 2))

    # 2. Pegelband mit Pausen ≥ 400 ms
    z.rectangle((x0, PEGEL_Y, x1, PEGEL_Y + PEGEL_H), fill=ZELLE)
    gueltig = [w for w in woerter if w.get("start") is not None and w.get("end") is not None]
    ende = None
    for s, e in sorted((float(w["start"]), float(w["end"])) for w in gueltig):
        if ende is not None and s - ende >= 0.4 and s > von_s and ende < bis_s:
            z.rectangle((x_von(max(ende, von_s)), PEGEL_Y, x_von(min(s, bis_s)), PEGEL_Y + PEGEL_H), fill=PAUSE)
        ende = e if ende is None else max(ende, e)
    for linie in (-20.0, -40.0):
        y = y_db(linie)
        z.line((x0, y, x1, y), fill=(70, 70, 80), width=1)
        z.text((x1 + 6, y - 8), f"{int(linie)}", fill=DIM, font=klein)
    db = pegel_db(video, von_s, bis_s)
    pts = [(x_von(von_s + (i + 0.5) * 0.01), y_db(float(v))) for i, v in enumerate(db)
           if von_s + (i + 0.5) * 0.01 <= bis_s]
    if len(pts) > 1:
        z.polygon(pts + [(pts[-1][0], PEGEL_Y + PEGEL_H), (pts[0][0], PEGEL_Y + PEGEL_H)], fill=(*PEGEL, 80))
        z.line(pts, fill=PEGEL, width=1)

    # 3. Wörter in zwei Zeilen
    frei = [-10**6, -10**6]
    for w in sorted(gueltig, key=lambda w: float(w["start"])):
        s, e = float(w["start"]), float(w["end"])
        text = str(w.get("text") or "").strip()
        if not text or e < von_s or s > bis_s:
            continue
        x = x_von(max(s, von_s))
        breite = int(z.textlength(text, font=klein))
        for zeile in (0, 1):
            if x >= frei[zeile]:
                z.text((x, WORT_Y + zeile * 18), text, fill=TEXT, font=klein)
                frei[zeile] = x + breite + 6
                break
        z.line((x, PEGEL_Y - 5, x, PEGEL_Y), fill=DIM, width=1)

    # 4. Schnitte und Befund-Marken
    for t in bild_schnitte:
        if von_s <= t <= bis_s:
            x = x_von(t)
            z.line((x, STREIFEN_Y + STREIFEN_H + 2, x, PEGEL_Y + PEGEL_H), fill=BILD_LINIE, width=2)
    for t in ton_schnitte:
        if von_s <= t <= bis_s:
            x = x_von(t) + 2
            z.line((x, PEGEL_Y, x, PEGEL_Y + PEGEL_H), fill=TON_LINIE, width=2)
    for t, text in marken:
        if von_s <= t <= bis_s:
            x = x_von(t)
            for y in range(STREIFEN_Y, PEGEL_Y + PEGEL_H, 8):
                z.line((x, y, x, min(y + 4, PEGEL_Y + PEGEL_H)), fill=MARKE, width=2)
            z.text((x + 6, PEGEL_Y + 4), str(text), fill=MARKE, font=klein)

    # 5. Zeitleiste und Legende
    for i in range(7):
        t = von_s + i * spanne / 6
        x = x_von(t)
        z.line((x, LEISTE_Y, x, LEISTE_Y + 6), fill=DIM, width=1)
        z.text((max(0, x - 40), LEISTE_Y + 9), zeit(t), fill=DIM, font=klein)
    z.text((RAND, LEISTE_Y + 32), "cyan Bild-Schnitt · orange Ton-Schnitt · rot Befund · blau Pause ≥ 400 ms · "
           "Pegel −60…0 dBFS (Linien −20/−40)", fill=DIM, font=klein)
    ausgabe.parent.mkdir(parents=True, exist_ok=True)
    bild.save(ausgabe, "PNG", optimize=True)
    return ausgabe
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_schnittbild.py`
Expected: PASS (3 Tests)

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- tools/autocut/src/niro_autocut/schnittbild.py tools/autocut/tests/test_schnittbild.py && git commit -m "feat(autocut): Schnittbild — Filmstreifen, Pegel, Wörter, Schnitte als PNG (nach video-use, MIT)" -- tools/autocut/src/niro_autocut/schnittbild.py tools/autocut/tests/test_schnittbild.py
```

### Task 7: Skript `autocut_kanten.py`

**Files:**
- Create: `tools/autocut/scripts/autocut_kanten.py`
- Test: `tools/autocut/tests/test_kanten_script.py`

**Interfaces:**
- Consumes: `kanten` (Tasks 2–4), `kanten_medien`, `kanten_bericht` (Task 5), `schnittbild.zeichne` (Task 6), `resolve_api.ResolveSession/connect`, `charge.Charge/append_protokoll`; `tests/fake_resolve.FakeResolve`.
- Produces: CLI laut Spec 5; Funktionen `timeline_name(ch) -> str`, `export_datei(ch, name) -> Path`, `schnappschuss_lesen(ch, name) -> dict`, `video_kurz(ch) -> str`, `bilder(ch, snap, render, erg) -> None`, `pruefen(ch, snap, render, ohne_bilder) -> dict`, `main(argv) -> int`.

- [ ] **Step 1: Tests schreiben**

<!-- datei: tools/autocut/tests/test_kanten_script.py neu -->
```python
"""autocut_kanten.py Ende-zu-Ende: synthetischer Export + Schnappschuss → Befunde, Bericht, Bilder, Protokoll, Exit-Codes."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import time
import wave
from pathlib import Path

import numpy as np
import pytest
import yaml

from fake_resolve import FakeResolve
from niro_autocut.charge import DEFAULTS_FILE, Charge

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kanten = _load("autocut_kanten")
CFG = yaml.safe_load(DEFAULTS_FILE.read_text(encoding="utf-8"))["kanten"]
SR, FPS, SPF, N = 48000, 25, 1920, 75
LANG = int(CFG["tonloch_min_frames"]) + 1


def _export(ziel: Path, tmp: Path) -> Path:
    """3 s, 25 fps, 160×90: Frame 40 schwarz; Ton mit Sprung genau an Frame 50 (links) und Stille ab Frame 60."""
    t = np.arange(N * SPF) / SR
    x = 0.2 * np.sin(2 * np.pi * 220 * t) + 0.05 * np.sin(2 * np.pi * 1500 * t)
    x = x + np.random.default_rng(7).normal(0, 0.0005, t.size)
    ton = np.stack([x, x], axis=1)
    ton[50 * SPF:, 0] += 0.3
    ton[60 * SPF:(60 + LANG) * SPF] = 0.0
    wav = tmp / "ton.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(ton, -1, 1) * 32767).astype("<i2").tobytes())
    ziel.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"testsrc2=size=160x90:rate={FPS}:duration=3", "-i", str(wav),
                    "-vf", "drawbox=enable='eq(n,40)':color=black:t=fill", "-map", "0:v", "-map", "1:a",
                    "-c:v", "mpeg4", "-q:v", "2", "-g", "1", "-c:a", "pcm_s16le", "-shortest", str(ziel)], check=True)
    return ziel


def _snap(fx3: str, laenge: int = N) -> dict:
    def it(name, datei, start, dauer, quell_in, tempo=None):
        return {"name": name, "datei": datei, "start": start, "dauer": dauer, "quell_in": quell_in, "aktiv": True,
                "tempo": tempo}
    return {"quelle": "plan", "gelesen_am": "2026-09-16T12:00:00", "projekt": "Test", "timeline": "T", "fps": 25.0,
            "start_frame": 90000, "start_timecode": "01:00:00:00", "laenge": laenge, "spuren": {
                "V1": [it("v1", "/x/v1.MP4", 0, 50, 0, 100.0), it("v2", "/x/v2.MP4", 50, 25, 0, 100.0)],
                "A1": [it("FX3_0001.MP4", fx3, 0, 50, 0), it("FX3_0001.MP4", fx3, 50, 25, 35)]}}


@pytest.fixture
def aufbau(charge_dir: Path, tmp_path: Path) -> dict:
    fx3 = Charge.open(charge_dir).load_index()[0]["path"]
    export = _export(charge_dir / "Ergebnisse" / "Export" / "T.mov", tmp_path)
    rb = tmp_path / "snap.json"
    rb.write_text(json.dumps(_snap(fx3)), encoding="utf-8")
    return {"charge": charge_dir, "export": export, "readback": rb, "fx3": fx3, "tmp": tmp_path}


def test_befunde_bericht_bilder_protokoll(aufbau):
    ch = aufbau["charge"]
    assert kanten.main([str(ch), "--readback", str(aufbau["readback"])]) == 1
    erg = json.loads((ch / "_intern" / "autocut" / "kanten.json").read_text(encoding="utf-8"))
    assert [(b["art"], b["frame"]) for b in erg["befunde"]] == [
        ("Schwarzbild", 40), ("Knackser", 50), ("Wort angeschnitten", 50), ("Tonloch", 60)]
    assert erg["befunde"][3]["frames"] == LANG and erg["befunde"][2]["wort"] == "ist"
    assert all(b["bild"] and Path(b["bild"]).is_file() for b in erg["befunde"])
    assert Path(erg["befunde"][0]["bild"]).name == "kante_001_schwarzbild_01-00-01-15.png"
    bericht = (ch / "Ergebnisse" / "Rohschnitt" / "video-1-test-kanten.md").read_text(encoding="utf-8")
    assert "**4 Befunde**" in bericht and "01:00:02:00" in bericht
    assert (ch / "_intern" / "autocut" / "kanten_readback.json").is_file()
    assert "AutoCut: Kantenprüfung" in (ch / "Protokoll.md").read_text(encoding="utf-8")


def test_export_passt_nicht_oder_fehlt(aufbau, capsys):
    ch = aufbau["charge"]
    lang = aufbau["tmp"] / "lang.json"
    lang.write_text(json.dumps(_snap(aufbau["fx3"], laenge=80)), encoding="utf-8")
    assert kanten.main([str(ch), "--readback", str(lang), "--ohne-bilder"]) == 2
    assert "nicht aktuell" in capsys.readouterr().err
    aufbau["export"].unlink()
    assert kanten.main([str(ch), "--readback", str(aufbau["readback"])]) == 2
    assert "Kein Export für 'T'" in capsys.readouterr().err


def test_ohne_readback_liest_resolve_und_meldet_fehlende_timeline(aufbau, monkeypatch, capsys):
    ch = aufbau["charge"]
    (ch / "_intern" / "autocut" / "build.json").write_text(json.dumps({"timeline": "T", "video": "video-1-test.md"}),
                                                          encoding="utf-8")
    fr = FakeResolve()
    monkeypatch.setattr(kanten.RA, "connect", lambda: fr)
    assert kanten.main([str(ch)]) == 2
    err = capsys.readouterr().err
    assert "Timeline 'T' ist nicht im offenen Projekt" in err and "--readback" in err


def test_timeline_name_nimmt_neueste_datei(aufbau):
    ch = Charge.open(aufbau["charge"])
    (ch.autocut / "build.json").write_text(json.dumps({"timeline": "Roh"}), encoding="utf-8")
    (ch.autocut / "finalize.json").write_text(json.dumps({"timeline": "End", "status": "fehler"}), encoding="utf-8")
    (ch.autocut / "feinschnitt.json").write_text(json.dumps({"timeline": "Fein"}), encoding="utf-8")
    alt = time.time() - 100
    os.utime(ch.autocut / "build.json", (alt, alt))
    assert kanten.timeline_name(ch) == "Fein"
    os.utime(ch.autocut / "feinschnitt.json", (alt - 50, alt - 50))
    assert kanten.timeline_name(ch) == "Roh"          # finalize.json ohne status ok zählt nicht
```

- [ ] **Step 2: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_kanten_script.py`
Expected: FAIL (`FileNotFoundError` für `scripts/autocut_kanten.py`)

- [ ] **Step 3: Implementierung**

<!-- datei: tools/autocut/scripts/autocut_kanten.py neu -->
```python
"""AutoCut Kantenprüfung: Schnitte einer Timeline am fertigen Export messen — Schwarzbild, Schnipsel, Knackser,
Tonloch, Wort angeschnitten (Spec docs/superpowers/specs/2026-09-16-autocut-kantenpruefung-design.md).

Aufruf:
    venv/bin/python scripts/autocut_kanten.py "<Charge>" [--timeline "<Name>"] [--render "<Datei>"]
                                              [--readback "<json>"] [--ohne-bilder]

Ohne --readback wird die Timeline im offenen Resolve-Projekt NUR GELESEN. Der Export entsteht vorher per Review-Render
(tools/resolve/WORKFLOW-Resolve.md) oder durch den User; Standard ist die neueste Datei in Ergebnisse/Export, deren
Name mit dem Timeline-Namen beginnt. Schreibt _intern/autocut/kanten_readback.json, kanten.json,
work/kanten/<fingerprint>.npz, work/schnittbild/kante_*.png, Ergebnisse/Rohschnitt/<video>-kanten.md und das Protokoll.
Exit 0 = keine Befunde, 1 = Befunde, 2 = Voraussetzung fehlt oder Fehler.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import kanten as K  # noqa: E402
from niro_autocut import kanten_bericht as KB  # noqa: E402
from niro_autocut import kanten_medien as KM  # noqa: E402
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402
from niro_autocut.schnittbild import zeichne  # noqa: E402

FENSTER_S = 1.5
VIDEO_ENDUNGEN = {".mov", ".mp4", ".mxf", ".m4v"}


def _nfc(s) -> str:
    return unicodedata.normalize("NFC", str(s))


def timeline_name(ch: Charge) -> str:
    """Schlüssel ``timeline`` der zuletzt geschriebenen Datei aus feinschnitt.json, finalize.json (ok), build.json."""
    kandidaten = []
    for datei in ("feinschnitt.json", "finalize.json", "build.json"):
        d = ch.read_json(datei)
        if not isinstance(d, dict) or not d.get("timeline"):
            continue
        if datei == "finalize.json" and d.get("status") != "ok":
            continue
        kandidaten.append(((ch.autocut / datei).stat().st_mtime, str(d["timeline"])))
    if not kandidaten:
        raise AutoCutError(f"Keine gebaute AutoCut-Timeline in {ch.autocut} (feinschnitt.json, finalize.json, "
                           f"build.json) — --timeline angeben.")
    return max(kandidaten)[1]


def export_datei(ch: Charge, name: str) -> Path:
    """Neueste Videodatei in Ergebnisse/Export, deren Name mit dem Timeline-Namen beginnt."""
    ordner = ch.root / "Ergebnisse" / "Export"
    treffer = [p for p in ordner.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_ENDUNGEN
               and _nfc(p.name).startswith(_nfc(name))] if ordner.is_dir() else []
    if not treffer:
        raise AutoCutError(f"Kein Export für '{name}' in {ordner} — Review-Render (tools/resolve/WORKFLOW-Resolve.md) "
                           f"oder --render angeben.")
    return max(treffer, key=lambda p: p.stat().st_mtime)


def schnappschuss_lesen(ch: Charge, name: str) -> dict:
    """Timeline im offenen Resolve-Projekt nur lesen → Schnappschuss."""
    try:
        session = RA.ResolveSession(RA.connect(), path_map=ch.config.get("path_map"))
    except AutoCutError as e:
        raise AutoCutError(f"{e}\nOhne Resolve: --readback <kanten_readback.json> angeben.") from e
    tl = session.find_timeline(name)
    if tl is None:
        raise AutoCutError(f"Timeline '{name}' ist nicht im offenen Projekt '{session.project_name}' — das Projekt in "
                           f"Resolve öffnen (wird nur gelesen) oder --readback angeben.")
    return K.snapshot_from_readback(session.read_timeline(tl), session.project_name)


def video_kurz(ch: Charge) -> str:
    """Kurzname für den Bericht: ``video`` aus build.json, sonst der einzige Plan, sonst „video"."""
    build = ch.read_json("build.json") or {}
    if build.get("video"):
        return Path(str(build["video"])).stem
    plaene = ch.plan_files()
    return plaene[0].stem if len(plaene) == 1 else "video"


def bilder(ch: Charge, snap: dict, render: Path, erg: dict) -> None:
    """Je Befund ein Schnittbild (±1,5 s) nach _intern/autocut/work/schnittbild/."""
    fps = float(snap["fps"])
    ende = snap["laenge"] / fps
    b_s = [f / fps for f in K.schnitte(snap, "bild")]
    t_s = [f / fps for f in K.schnitte(snap, "ton")]
    transkripte = K.Transkripte(ch)
    for x in erg["befunde"]:
        mitte = (x["frame"] + x["frames"] / 2) / fps
        von, bis = max(0.0, mitte - FENSTER_S), min(ende, mitte + FENSTER_S)
        ziel = ch.work / "schnittbild" / (f"kante_{x['nr']:03d}_{K.DATEINAME_ART[x['art']]}_"
                                          f"{x['timecode'].replace(':', '-')}.png")
        ch.assert_writable(ziel)
        try:
            zeichne(render, von, bis, ziel, woerter=K.export_woerter(snap, transkripte, von, bis),
                    bild_schnitte=b_s, ton_schnitte=t_s, marken=[(x["frame"] / fps, f"{x['nr']} {x['art']}")],
                    beschriftung=f"Befund {x['nr']}: {x['art']} · {x['timecode']}",
                    tc_start=snap["start_timecode"], fps=fps)
            x["bild"] = str(ziel)
        except AutoCutError as e:
            x["bild"] = None
            erg["warnungen"].append(f"Bild zu Befund {x['nr']}: {e}")


def pruefen(ch: Charge, snap: dict, render: Path, ohne_bilder: bool) -> dict:
    """Export gegen Schnappschuss prüfen, messen, Befunde bilden (mit Bildern, außer ``ohne_bilder``)."""
    info = KM.export_info(render)
    if abs(info["fps"] - float(snap["fps"])) > 0.01 or info["frames"] != int(snap["laenge"]):
        raise AutoCutError(f"Export ist nicht aktuell: {render.name} hat {info['frames']} Frames @ {info['fps']} fps, "
                           f"die Timeline '{snap['timeline']}' {snap['laenge']} Frames @ {snap['fps']} fps — "
                           f"neu exportieren.")
    cfg = dict(ch.config.get("kanten") or {})
    bild = KM.bild_metriken(render, ch.work / "kanten", n_erwartet=int(snap["laenge"]))
    if bild["mittel"].size != int(snap["laenge"]):
        raise AutoCutError(f"ffmpeg las {bild['mittel'].size} Frames statt {snap['laenge']} aus {render.name}.")
    audio = KM.ton_lesen(render) if info["ton"] else None
    erg = K.pruefe(snap, bild, audio, KM.SR, K.Transkripte(ch), cfg)
    if audio is None:
        erg["warnungen"].append("Export ohne Ton — Knackser und Tonlöcher nicht geprüft.")
    erg.update({"export": info, "parameter": cfg,
                "schnappschuss": {"quelle": snap["quelle"], "gelesen_am": snap["gelesen_am"],
                                  "projekt": snap["projekt"]}})
    if not ohne_bilder:
        bilder(ch, snap, render, erg)
    return erg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Kantenprüfung am fertigen Export (Resolve nur lesend).")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--timeline", help="exakter Timeline-Name (Standard: zuletzt gebaute AutoCut-Timeline)")
    ap.add_argument("--render", help="Export-Datei (Standard: neueste in Ergebnisse/Export mit dem Timeline-Namen)")
    ap.add_argument("--readback", help="gespeicherter Schnappschuss statt Resolve (kanten_readback.json)")
    ap.add_argument("--ohne-bilder", action="store_true", help="keine Schnittbilder zu den Befunden")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        if args.readback:
            p = Path(args.readback).expanduser()
            if not p.is_file():
                raise AutoCutError(f"--readback nicht gefunden: {p}")
            snap = json.loads(p.read_text(encoding="utf-8"))
            name = args.timeline or str(snap.get("timeline"))
            if snap.get("timeline") != name:
                raise AutoCutError(f"Schnappschuss {p.name} gehört zu '{snap.get('timeline')}', geprüft werden soll "
                                   f"'{name}'.")
        else:
            name = args.timeline or timeline_name(ch)
            snap = schnappschuss_lesen(ch, name)
        ch.write_json("kanten_readback.json", snap)
        render = Path(args.render).expanduser() if args.render else export_datei(ch, name)
        if not render.is_file():
            raise AutoCutError(f"Export nicht gefunden: {render}")
        print(f"Timeline '{name}' (Schnappschuss {snap['quelle']}, {snap['laenge']} Frames) · Export {render.name} "
              f"— messe …", file=sys.stderr)
        erg = pruefen(ch, snap, render, args.ohne_bilder)
        ch.write_json("kanten.json", erg)
        bericht = ch.ergebnisse / f"{video_kurz(ch)}-kanten.md"
        ch.assert_writable(bericht)
        bericht.write_text(KB.bericht(erg), encoding="utf-8")
        n, z, um = len(erg["befunde"]), erg["zaehlung"], erg["umfang"]
        zeilen = [f"Kantenprüfung „{name}“ am Export {render.name}: {n} Befunde ("
                  + ", ".join(f"{a} {z[a]}" for a in K.ARTEN) + ")",
                  f"Umfang: {um['bild_schnitte']} Bild-Schnitte, {um['ton_schnitte']} Ton-Schnitte, "
                  f"{um['mit_transkript']} Tonclips mit Transkript; Schnappschuss {snap['quelle']} "
                  f"({snap['gelesen_am']})",
                  f"Bericht: {bericht}"]
        zeilen += [f"Warnung: {w}" for w in erg["warnungen"][:5]]
        append_protokoll(ch, "Kantenprüfung", zeilen)
        print("\n".join(zeilen))
        return 1 if n else 0
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_kanten_script.py`
Expected: PASS (4 Tests). Schlägt `test_befunde_bericht_bilder_protokoll` wegen eines zusätzlichen Schnipsel-Befunds aus `testsrc2` fehl: `kanten.json` lesen, `diff`-Werte ansehen und im Test den Clip statt `testsrc2` mit `-vf` fester Farbe (`color=c=gray:size=160x90:rate=25:duration=3`) plus `drawbox` erzeugen.

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- tools/autocut/scripts/autocut_kanten.py tools/autocut/tests/test_kanten_script.py && git commit -m "feat(autocut): Skript autocut_kanten.py — Kantenprüfung am Export" -- tools/autocut/scripts/autocut_kanten.py tools/autocut/tests/test_kanten_script.py
```

### Task 8: Skript `autocut_schnittbild.py`

**Files:**
- Create: `tools/autocut/scripts/autocut_schnittbild.py`
- Test: `tools/autocut/tests/test_schnittbild_script.py`

**Interfaces:**
- Consumes: `kanten.tc_to_frame`, `kanten.timecode`, `kanten.schnitte`, `kanten.export_woerter`, `kanten.Transkripte`; `media.proxy_for`; `schnittbild.zeichne`; Schnappschuss `_intern/autocut/kanten_readback.json` aus Task 7.
- Produces: CLI laut Spec 5; `sekunden(text: str) -> float`, `clip_bild(ch, args) -> Path`, `export_bild(ch, args) -> Path`, `main(argv) -> int` (druckt den PNG-Pfad auf stdout).

- [ ] **Step 1: Tests schreiben**

<!-- datei: tools/autocut/tests/test_schnittbild_script.py neu -->
```python
"""autocut_schnittbild.py: Clip- und Export-Modus, Zeitangaben, Fehler."""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

from niro_autocut.charge import AutoCutError, Charge

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sb = _load("autocut_schnittbild")


def _video(pfad: Path) -> Path:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=25:duration=3",
                    "-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000:duration=3",
                    "-c:v", "mpeg4", "-q:v", "3", "-c:a", "pcm_s16le", "-f", "mov", str(pfad)], check=True)
    return pfad


def test_sekunden():
    assert sb.sekunden("12.5") == 12.5 and sb.sekunden("01:02,5") == 62.5 and sb.sekunden("1:02:03.5") == 3723.5
    with pytest.raises(AutoCutError):
        sb.sekunden("x")
    with pytest.raises(AutoCutError):
        sb.sekunden("1:2:3:4")


def test_clip_modus(charge_dir, capsys):
    ch = Charge.open(charge_dir)
    _video(Path(ch.load_index()[0]["path"]))
    assert sb.main([str(charge_dir), "--clip", "FX3_0001.MP4", "--von", "0.5", "--bis", "0:01.8"]) == 0
    ziel = Path(capsys.readouterr().out.strip())
    assert ziel == ch.work / "schnittbild" / "FX3_0001_0.50-1.80.png" and ziel.is_file()
    assert sb.main([str(charge_dir), "--clip", "fehlt.MP4", "--von", "0", "--bis", "1"]) == 2
    assert "nicht im Transkript-Index" in capsys.readouterr().err
    assert sb.main([str(charge_dir), "--clip", "FX3_0001.MP4", "--von", "0"]) == 2
    assert "--von und --bis" in capsys.readouterr().err


def test_export_modus(charge_dir, tmp_path, capsys):
    ch = Charge.open(charge_dir)
    export = _video(tmp_path / "T.mov")
    assert sb.main([str(charge_dir), "--render", str(export), "--tc", "01:00:01:00"]) == 2
    assert "Schnappschuss fehlt" in capsys.readouterr().err
    fx3 = ch.load_index()[0]["path"]
    snap = {"quelle": "plan", "gelesen_am": "x", "projekt": "P", "timeline": "T", "fps": 25.0, "start_frame": 0,
            "start_timecode": "01:00:00:00", "laenge": 75, "spuren": {
                "V1": [{"name": "v", "datei": "v", "start": 0, "dauer": 30, "quell_in": 0, "aktiv": True, "tempo": 100.0},
                       {"name": "w", "datei": "w", "start": 30, "dauer": 45, "quell_in": 0, "aktiv": True, "tempo": 100.0}],
                "A1": [{"name": "FX3_0001.MP4", "datei": fx3, "start": 0, "dauer": 75, "quell_in": 0, "aktiv": True,
                        "tempo": None}]}}
    ch.write_json("kanten_readback.json", snap)
    assert sb.main([str(charge_dir), "--render", str(export), "--tc", "01:00:01:05"]) == 0
    ziel = Path(capsys.readouterr().out.strip())
    assert ziel.name == "export_01-00-01-05.png" and ziel.is_file()
    assert sb.main([str(charge_dir), "--render", str(export), "--frame", "500"]) == 2
    assert "außerhalb" in capsys.readouterr().err
```

- [ ] **Step 2: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_schnittbild_script.py`
Expected: FAIL (`FileNotFoundError` für `scripts/autocut_schnittbild.py`)

- [ ] **Step 3: Implementierung**

<!-- datei: tools/autocut/scripts/autocut_schnittbild.py neu -->
```python
"""AutoCut Schnittbild: Filmstreifen, Pegel, Wörter und Schnitte eines Zeitbereichs als PNG — für unklare In/Outs am
Rohclip (Stufe 1) oder für eine Stelle im Export (Kantenprüfung). Spec 2026-09-16.

Aufruf:
    venv/bin/python scripts/autocut_schnittbild.py "<Charge>" --clip <Dateiname|Pfad> --von <s|mm:ss.s> --bis <s|mm:ss.s>
    venv/bin/python scripts/autocut_schnittbild.py "<Charge>" --render "<Datei>" (--tc HH:MM:SS:FF | --frame <N>)
                                                   [--fenster 1.5] [--readback "<json>"]
    gemeinsam: [--frames 10] [--ausgabe "<png>"]

Rohclip: Eintrag im Transkript-Index der Charge (Pfad über path_map), Bild und Ton aus dem Proxy (sonst Original),
Wörter aus dem Scribe-Cache. Export: Schnitte und Wörter aus _intern/autocut/kanten_readback.json (oder --readback);
--frame zählt ab Timeline-Start. Schreibt nur das PNG (Standard _intern/autocut/work/schnittbild/) und druckt den Pfad.
Exit 0 ok, 2 Fehler.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import kanten as K  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge  # noqa: E402
from niro_autocut.media import proxy_for  # noqa: E402
from niro_autocut.schnittbild import zeichne  # noqa: E402


def _nfc(s) -> str:
    return unicodedata.normalize("NFC", str(s))


def sekunden(text: str) -> float:
    """„12.5" → 12.5 · „01:02,5" → 62.5 · „1:02:03.5" → 3723.5."""
    teile = str(text).strip().split(":")
    try:
        werte = [float(t.replace(",", ".")) for t in teile]
    except ValueError as e:
        raise AutoCutError(f"Zeitangabe nicht lesbar: {text!r} (Sekunden oder mm:ss.s)") from e
    if not 1 <= len(werte) <= 3:
        raise AutoCutError(f"Zeitangabe nicht lesbar: {text!r} (Sekunden oder mm:ss.s)")
    s = 0.0
    for w in werte:
        s = s * 60 + w
    return s


def clip_bild(ch: Charge, args) -> Path:
    """Schnittbild eines Rohclips aus dem Transkript-Index (Proxy bevorzugt) mit Scribe-Wörtern."""
    gesucht = _nfc(args.clip)
    eintraege = [e for e in ch.load_index() if e.get("path")
                 and gesucht in (_nfc(e.get("name", "")), _nfc(e["path"]), _nfc(Path(e["path"]).name))]
    if not eintraege:
        raise AutoCutError(f"Clip '{args.clip}' steht nicht im Transkript-Index der Charge.")
    if len(eintraege) > 1:
        raise AutoCutError(f"Clip '{args.clip}' ist mehrdeutig ({len(eintraege)} Einträge) — vollen Pfad angeben.")
    e = eintraege[0]
    original = Path(ch.map_path(e["path"]))
    quelle = proxy_for(original) or original
    if not quelle.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {quelle}\nIst das NAS gemountet? Sonst path_map in config.yaml setzen.")
    von, bis = sekunden(args.von), sekunden(args.bis)
    woerter = []
    if e.get("fingerprint"):
        woerter = (ch.cache_transcript(e["fingerprint"]) or {}).get("words") or []
    ziel = (Path(args.ausgabe).expanduser() if args.ausgabe
            else ch.work / "schnittbild" / f"{Path(e['path']).stem}_{von:.2f}-{bis:.2f}.png")
    ch.assert_writable(ziel)
    beschriftung = " · ".join(str(v) for v in (e.get("person"), e.get("kamera"),
                                               "Proxy" if quelle != original else "Original") if v)
    return zeichne(quelle, von, bis, ziel, woerter=woerter, frames=args.frames, beschriftung=beschriftung)


def export_bild(ch: Charge, args) -> Path:
    """Schnittbild einer Stelle im Export mit Schnitten und Wörtern aus dem Schnappschuss."""
    render = Path(args.render).expanduser()
    if not render.is_file():
        raise AutoCutError(f"Export nicht gefunden: {render}")
    snap_pfad = Path(args.readback).expanduser() if args.readback else ch.autocut / "kanten_readback.json"
    if not snap_pfad.is_file():
        raise AutoCutError(f"Schnappschuss fehlt: {snap_pfad} — erst scripts/autocut_kanten.py laufen lassen oder "
                           f"--readback angeben.")
    snap = json.loads(snap_pfad.read_text(encoding="utf-8"))
    fps = float(snap["fps"])
    if args.tc:
        frame = K.tc_to_frame(args.tc, fps, snap["start_timecode"])
    elif args.frame is not None:
        frame = int(args.frame)
    else:
        raise AutoCutError("Im Export-Modus --tc oder --frame angeben.")
    if not 0 <= frame < int(snap["laenge"]):
        raise AutoCutError(f"Frame {frame} liegt außerhalb der Timeline (0–{int(snap['laenge']) - 1}).")
    tc = K.timecode(frame, fps, snap["start_timecode"])
    mitte = frame / fps
    von, bis = max(0.0, mitte - args.fenster), min(snap["laenge"] / fps, mitte + args.fenster)
    ziel = (Path(args.ausgabe).expanduser() if args.ausgabe
            else ch.work / "schnittbild" / f"export_{tc.replace(':', '-')}.png")
    ch.assert_writable(ziel)
    return zeichne(render, von, bis, ziel, woerter=K.export_woerter(snap, K.Transkripte(ch), von, bis),
                   bild_schnitte=[f / fps for f in K.schnitte(snap, "bild")],
                   ton_schnitte=[f / fps for f in K.schnitte(snap, "ton")],
                   marken=[(mitte, tc)], frames=args.frames, beschriftung=str(snap.get("timeline")),
                   tc_start=snap["start_timecode"], fps=fps)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Schnittbild (Filmstreifen, Pegel, Wörter, Schnitte) als PNG.")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    modus = ap.add_mutually_exclusive_group(required=True)
    modus.add_argument("--clip", help="Rohclip: Dateiname oder Pfad aus dem Transkript-Index")
    modus.add_argument("--render", help="Export-Datei der Timeline")
    ap.add_argument("--von", help="Clip-Modus: Anfang (Sekunden oder mm:ss.s)")
    ap.add_argument("--bis", help="Clip-Modus: Ende (Sekunden oder mm:ss.s)")
    ap.add_argument("--tc", help="Export-Modus: Timecode HH:MM:SS:FF")
    ap.add_argument("--frame", type=int, help="Export-Modus: Frame ab Timeline-Start")
    ap.add_argument("--fenster", type=float, default=1.5, help="Export-Modus: Sekunden vor und nach der Stelle")
    ap.add_argument("--readback", help="Export-Modus: Schnappschuss (Standard _intern/autocut/kanten_readback.json)")
    ap.add_argument("--frames", type=int, default=10, help="Bilder im Filmstreifen")
    ap.add_argument("--ausgabe", help="PNG-Pfad (in den AutoCut-Schreibbereichen der Charge)")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        if args.clip:
            if not args.von or not args.bis:
                raise AutoCutError("Im Clip-Modus --von und --bis angeben.")
            ziel = clip_bild(ch, args)
        else:
            ziel = export_bild(ch, args)
        print(ziel)
        return 0
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_schnittbild_script.py`
Expected: PASS (3 Tests)

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- tools/autocut/scripts/autocut_schnittbild.py tools/autocut/tests/test_schnittbild_script.py && git commit -m "feat(autocut): Skript autocut_schnittbild.py — Rohclip und Export-Stelle als PNG" -- tools/autocut/scripts/autocut_schnittbild.py tools/autocut/tests/test_schnittbild_script.py
```

### Task 9: Kalibrierung am Taxodia-Export

**Files:**
- Create (nicht versioniert, Scratchpad): `taxodia_plan_schnappschuss.py`
- Create (Charge): `_intern/autocut/kanten_readback_plan.json`, `kanten_readback.json`, `kanten.json`, `work/kanten/*.npz`, `work/schnittbild/*.png`, `Ergebnisse/Rohschnitt/video-1-taxodia-weg-kanten.md`, Protokoll-Eintrag
- Modify (nur bei belegtem Bedarf): `tools/autocut/defaults.yaml` (Block `kanten:`)

**Interfaces:**
- Consumes: `autocut_kanten.py` (Task 7), Taxodia-Charge `CHARGE="/Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09"`, Export `Ergebnisse/Export/AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt.mov` (6845 Frames, 25 fps), Bauplan `_intern/feinschnitt_bauen.py` (`lade()`, `plan()`, `MUSIK_PLAN`, `FPS`, `ENDE`, `PROJEKT`), `_intern/sfx/sfx_plan.json` (`spur`, `rec_frame`, `dauer_frames`, `sfx_name`, `pfad_nas`).
- Produces: kalibrierte Schwellen (oder die bestätigten Startwerte) und Zahlen für Task 10.

- [ ] **Step 1: Resolve lesend prüfen**

MCP `run_script` (nur lesen): Projektname und ob die Timeline `AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt` existiert.
- Ist „Taxodia 09.26" offen → Step 3 ohne `--readback` (echter Readback).
- Sonst → Step 2 (Soll-Stand aus dem Bauplan); im Bericht steht dann `Schnappschuss plan`.

- [ ] **Step 2: Plan-Schnappschuss erzeugen (nur ohne offenes Projekt)**

Datei `<Scratchpad>/taxodia_plan_schnappschuss.py`:

```python
"""Schnappschuss (quelle „plan") der Taxodia-Feinschnitt-Timeline aus dem Bauplan — nur zur Kalibrierung der
Kantenprüfung, solange das Projekt nicht in Resolve geöffnet ist. Schreibt nur _intern/autocut/kanten_readback_plan.json."""
import datetime as dt
import importlib.util
import json
from pathlib import Path

CH = Path("/Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09")
spec = importlib.util.spec_from_file_location("fb", CH / "_intern" / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)
tl, shots = fb.lade()
p, fehler = fb.plan(tl, shots)
timeline = json.loads((CH / "_intern" / "autocut" / "feinschnitt.json").read_text(encoding="utf-8"))["timeline"]


def zeile(name, datei, start, dauer, quell_in, aktiv=True):
    return {"name": name, "datei": datei, "start": int(start), "dauer": int(dauer),
            "quell_in": None if quell_in is None else int(quell_in), "aktiv": bool(aktiv), "tempo": None}


spuren = {}
for spur, items in (("V1", p["V1"]), ("V2", p["V2_voll"]), ("V3", p["V3"]), ("V4", p["V4"]), ("A1", p["A1"])):
    spuren[spur] = [zeile(Path(i.clip).name, i.clip, i.rec_in_f, i.rec_out_f - i.rec_in_f, i.src_in_f, i.enabled)
                    for i in items]
for sp, datei, si, ri, ro, *_ in fb.MUSIK_PLAN:
    spuren.setdefault(sp, []).append(zeile(Path(str(datei)).name, str(datei), ri, ro - ri, si))
for e in json.loads((CH / "_intern" / "sfx" / "sfx_plan.json").read_text(encoding="utf-8")):
    spuren.setdefault(e["spur"], []).append(zeile(e["sfx_name"], e.get("pfad_nas"), e["rec_frame"], e["dauer_frames"], None))
for rows in spuren.values():
    rows.sort(key=lambda r: r["start"])
snap = {"quelle": "plan", "gelesen_am": dt.datetime.now().isoformat(timespec="seconds"), "projekt": fb.PROJEKT,
        "timeline": timeline, "fps": float(fb.FPS), "start_frame": 90000, "start_timecode": "01:00:00:00",
        "laenge": int(fb.ENDE), "spuren": spuren}
ziel = CH / "_intern" / "autocut" / "kanten_readback_plan.json"
ziel.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
print(ziel, {k: len(v) for k, v in spuren.items()}, "Planfehler:", fehler)
```

Run: `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "<Scratchpad>/taxodia_plan_schnappschuss.py"`
Expected: Pfad + Item-Zahlen je Spur (V1 30, A1 30 wie `feinschnitt.json` → `spuren`), `Planfehler: []`.

- [ ] **Step 3: Prüfung laufen lassen**

Run (ohne offenes Projekt): `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "/Users/jansantos/NIRO Studio/tools/autocut/scripts/autocut_kanten.py" "$CHARGE" --readback "$CHARGE/_intern/autocut/kanten_readback_plan.json"`
Run (Projekt offen): `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "/Users/jansantos/NIRO Studio/tools/autocut/scripts/autocut_kanten.py" "$CHARGE"`
Expected: Exit 0 oder 1, Zusammenfassung mit Befunden je Art; erster Lauf dekodiert den 4K-Export (einige Minuten, im Hintergrund starten), weitere Läufe nutzen den Cache.

- [ ] **Step 4: Befunde beurteilen**

- `Ergebnisse/Rohschnitt/video-1-taxodia-weg-kanten.md` lesen: Messwerte (`diff` an Schnitten vs. übrige, Knack-Verhältnis Median/p95/Max).
- Jedes Schnittbild der Befunde mit Read ansehen und je Befund notieren: echt (Ursache) oder Fehlalarm (Ursache).

- [ ] **Step 5: Schwellen nur bei belegtem Bedarf anpassen**

- Fehlalarme mit gemeinsamer Ursache (z. B. harte Grafik-Wechsel als Schnipsel, Musik-Transienten als Knackser) → betroffene Schwelle in `defaults.yaml` so setzen, dass echte Befunde bleiben; Kommentar in der Zeile mit „Taxodia 16.09.: …".
- `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q` → PASS (die Tests lesen die Schwellen aus `defaults.yaml`).
- Step 3 wiederholen (Cache) und die Befundzahlen festhalten.

- [ ] **Step 6: Commit (nur bei geänderten Schwellen)**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- tools/autocut/defaults.yaml && git commit -m "chore(autocut): Kantenprüfung — Schwellen am Taxodia-Export kalibriert" -- tools/autocut/defaults.yaml
```

### Task 10: Doku (WORKFLOW, README, CLAUDE.md)

**Files:**
- Modify: `tools/autocut/WORKFLOW-AutoCut.md`, `tools/autocut/README.md`, `CLAUDE.md`
- Test: `tools/autocut/tests/test_docs.py` (vorhanden: jedes `scripts/*.py` dokumentiert, AutoCut-Zeile in CLAUDE.md mit 3 Spalten)

**Interfaces:**
- Consumes: Zahlen aus Task 9 (Export-Frames, Befunde je Art, `diff`-Median an Schnitten/übrige, Knack-Verhältnis-Maximum, ggf. geänderte Schwellen).

- [ ] **Step 1: WORKFLOW-AutoCut.md**

1. Tabelle der Unterbefehle (nach der Zeile „Feinschnitt"):
   `| „Kanten" | – | Kantenprüfung am Export einer AutoCut-Timeline (Schwarzbild, Schnipsel, Knackser, Tonloch, Wort angeschnitten) mit Schnittbildern; Resolve nur lesend |`
2. Stufe 1, Schritt 3, nach „Die Plan-Zeilen dafür liefert `plan_rows.py` (mit `find_tc.py`).":
   `   **Unklare In/Outs** (Atmer, Blinzeln, Wackler an der Kante): `autocut_schnittbild.py "$CHARGE" --clip <Datei> --von <s> --bis <s>` legt Filmstreifen, Pegel und Wörter als PNG unter `_intern/autocut/work/schnittbild/` ab — mit Read ansehen, dann entscheiden.`
3. „Abnahme Stufe 6" → Liste „Prüfungen", neuer erster Punkt: `  - Kantenprüfung am Export (`autocut_kanten.py`): Befunde je Art, jeder Befund am Schnittbild beurteilt,`
4. Neuer Abschnitt direkt vor `## Fehlerbilder und Abhilfe`:

```markdown
## Kantenprüfung — „Kanten" (seit 16.09.2026)

Misst die Schnitte einer AutoCut-Timeline am **fertigen Export** (Spec
`docs/superpowers/specs/2026-09-16-autocut-kantenpruefung-design.md`, Idee aus `browser-use/video-use`). Resolve wird nur
gelesen; den Export erzeugt der Review-Render oder der User.

1. **Export** — Review-Render nach `tools/resolve/WORKFLOW-Resolve.md` (schreibend, nach Freigabe; Quick Export
   „H.265 Master" mit PCM-Ton) nach `Ergebnisse/Export/`, oder der User exportiert selbst. Der Dateiname beginnt mit
   dem Timeline-Namen.
2. **Prüfen** — `autocut_kanten.py "$CHARGE"`: nimmt die zuletzt gebaute AutoCut-Timeline und den neuesten passenden
   Export (sonst `--timeline`, `--render`). Ist das Projekt nicht offen: `--readback
   "$CHARGE/_intern/autocut/kanten_readback.json"` (Schnappschuss des letzten Laufs). Exit 0 = keine Befunde,
   1 = Befunde, 2 = Voraussetzung fehlt (kein oder veralteter Export, Timeline nicht im offenen Projekt).
3. **Befunde ansehen** — Bericht `Ergebnisse/Rohschnitt/<video>-kanten.md`; je Befund das Schnittbild
   `_intern/autocut/work/schnittbild/kante_<nr>_<art>_<timecode>.png` mit Read ansehen. Befunde sind Verdachtsfälle:
   erst das Bild, dann urteilen.

| Befund | Bedeutung | typische Abhilfe |
|---|---|---|
| Schwarzbild | dunkle Frames ohne Struktur | Bild darunter länger halten, Deckkraft der Grafik prüfen (6d) |
| Schnipsel | 1–2 Frames zwischen zwei harten Bildwechseln | Frame-Versatz an der Kante (Left-Offset), Lücke auf V2/V3 schließen |
| Knackser | Sprung im Ton genau am Ton-Schnitt | Kante in eine Pause legen; 1-Frame-Blende auf A1 nur nach Rücksprache |
| Tonloch | digitale Stille, obwohl ein Tonclip liegt | stumme Spur (Stereo Fixer, nachträglich angelegte Spur), Clip offline |
| Wort angeschnitten | O-Ton-Kante schneidet mindestens 80 ms eines Worts ab | In/Out auf die Wortgrenze aus dem Scribe-Cache legen |

4. **Beheben und wiederholen** — nach Freigabe beheben, neu exportieren, erneut prüfen: **höchstens 3 Runden**, danach
   den Rest mit Timecodes offen melden (Regel aus video-use). Von Hand Geändertes nie überschreiben.
5. **Einzelne Stelle ansehen** — `autocut_schnittbild.py "$CHARGE" --render "<Export>" --tc HH:MM:SS:FF [--fenster 1.5]`.

Schwellen: Block `kanten:` in `defaults.yaml`, je Charge in `config.yaml` überschreibbar. Ein Stereo-Mix kann eine stumme
Einzelspur unter Musik nicht zeigen — nur den Totalausfall als Tonloch.
```

   Direkt darunter einen Absatz **Kalibrierung Taxodia (16.09.2026)** mit den Zahlen aus Task 9 (Export-Frames, Schnappschuss-Quelle, Befunde je Art mit Urteil echt/Fehlalarm, `diff`-Median an Schnitten und übrige, Knack-Verhältnis-Maximum, geänderte Schwellen oder „Startwerte bestätigt").
5. „Fehlerbilder und Abhilfe", Tabelle am Ende ergänzen:
   `| Kantenprüfung: `Export ist nicht aktuell` | Export nach der letzten Änderung neu erstellen (Review-Render), dann erneut prüfen |`
   `| Kantenprüfung: `Timeline '…' ist nicht im offenen Projekt` | Projekt in Resolve öffnen (nur lesen) oder `--readback` mit dem letzten Schnappschuss |`
   `| Kantenprüfung: viele Schnipsel „ohne Schnitt" | harte Wechsel in Grafik-Animationen — Bilder ansehen; bei Fehlalarmen `wechsel_diff_min` in der Chargen-`config.yaml` erhöhen |`
6. „Ausgabe-Konvention", im Baum `<Charge>/_intern/autocut/` vor `└── work/…`:
   `├── kanten_readback.json · kanten.json   Kantenprüfung: Schnappschuss der Timeline (nur gelesen), Befunde + Messwerte`
   und in der `work/`-Zeile `work/kanten/` (Bild-Metriken je Export) und `work/schnittbild/` (PNGs) ergänzen; unter `Ergebnisse/Rohschnitt/` die Zeile `├── <video>-kanten.md                 Kantenprüfung: Befunde mit Timecode und Schnittbild`.

- [ ] **Step 2: README.md**

1. Trigger-Liste: `| „Feinschnitt"` → `| „Feinschnitt" | „Kanten"`.
2. Stufen-Tabelle nach „Feinschnitt": `| „Kanten" | – | Kantenprüfung am Export (Schwarzbild, Schnipsel, Knackser, Tonloch, Wort angeschnitten) + Schnittbilder; Resolve nur lesend |`
3. Schnellstart, nach der Finalisieren-Zeile:
   `    "$PY" "$TOOL/scripts/autocut_kanten.py" "$CHARGE"             # Kantenprüfung am Export (Resolve nur lesend)`
   `    "$PY" "$TOOL/scripts/autocut_schnittbild.py" "$CHARGE" --clip <Datei> --von 12.3 --bis 15.8   # Schnittbild Rohclip`
4. Aufbau, nach `finalize.py`:
   `      kanten.py              Kantenprüfung: Schnappschuss, Schnitte, Befund-Regeln, Wortkanten, Gesamtprüfung`
   `      kanten_medien.py       Export lesen: ffprobe, Graustufen-Metriken je Frame (Cache), Ton als PCM`
   `      kanten_bericht.py      Bericht <video>-kanten.md`
   `      schnittbild.py         PNG: Filmstreifen + Pegel + Wörter + Schnitte (nach video-use, MIT)`
5. Arbeitsdateien: `kanten_readback.json`, `kanten.json`, `work/kanten/`, `work/schnittbild/` und `Ergebnisse/Rohschnitt/<video>-kanten.md` ergänzen.

- [ ] **Step 3: CLAUDE.md**

AutoCut-Zeile: `· Finalisieren (Pegel, Zeitlupe) |` → `· Finalisieren (Pegel, Zeitlupe) · Kantenprüfung am Export |`

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q tests/test_docs.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- tools/autocut/WORKFLOW-AutoCut.md tools/autocut/README.md CLAUDE.md && git commit -m "docs(autocut): Kantenprüfung und Schnittbild im Workflow, README, CLAUDE.md" -- tools/autocut/WORKFLOW-AutoCut.md tools/autocut/README.md CLAUDE.md
```

### Task 11: Abschluss — volle Tests, Push, Gedächtnis

**Files:**
- Commit: Plan-Datei, Taxodia-Referenzen (nach Prüfung), keine Medien
- Modify (Gedächtnis): `video-use-bewertung.md`, `niro-autocut-neu.md`, `MEMORY.md`

- [ ] **Step 1: Volle Testsuite**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q`
Expected: PASS (alle Tests, keine neuen Warnungen aus eigenen Modulen)

- [ ] **Step 2: Taxodia-Dateien prüfen**

Run: `cd "/Users/jansantos/NIRO Studio" && git -c core.quotepath=false status --short -- "projects/Steuerkanzlei Ludwig x Taxodia" && git -c core.quotepath=false diff -- "projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/Protokoll.md" | head -80`
- Neue Dateien: nur Positivliste (md/json) — `kanten.json`, `kanten_readback*.json`, `video-1-taxodia-weg-kanten.md`; keine PNG/NPZ (müssen ignoriert sein: `git check-ignore -v` auf je eine Datei).
- `Protokoll.md` enthielt schon vor dieser Session eine nicht committete Änderung: Diff lesen; nur committen, wenn sie reine Protokoll-Einträge sind, sonst weglassen und im Bericht nennen.

- [ ] **Step 3: Commit Plan + Referenzen**

```bash
cd "/Users/jansantos/NIRO Studio" && git add -- docs/superpowers/plans/2026-09-16-autocut-kantenpruefung.md && git commit -m "docs: Plan AutoCut-Kantenprüfung" -- docs/superpowers/plans/2026-09-16-autocut-kantenpruefung.md
```
Taxodia-Referenzen (Pfade aus Step 2, einzeln mit `git add -- <pfad>` und `git commit -m "chore: Taxodia — Kantenprüfung am Feinschnitt-Export" -- <pfade>`).

- [ ] **Step 4: Gestagte/committete Dateien gegenprüfen und pushen**

Run: `cd "/Users/jansantos/NIRO Studio" && git -c core.quotepath=false log --stat --oneline origin/main..main | cat`
- Keine Medien, PDFs, Rohtranskripte, Share-Links, API-Keys; keine Dateien der parallelen Rappold-/Motion-Session.
Run: `git fetch origin && git rev-list --left-right --count main...origin/main`
- `0 0` bzw. nur lokale Commits voraus → `git push origin main`.
- Ist `origin/main` voraus: nicht rebasen, solange der Arbeitsbaum fremde Änderungen hat — den User fragen.
Expected: Push ok, `git rev-list --left-right --count main...origin/main` → `0 0`.

- [ ] **Step 5: Gedächtnis aktualisieren**

- `video-use-bewertung.md`: Stand „gebaut und gepusht" mit Commit-Bereich, Skriptnamen, Kalibrierungsergebnis.
- `niro-autocut-neu.md`: Kantenprüfung (`autocut_kanten.py`, `autocut_schnittbild.py`) seit 16.09. ergänzen.
- `MEMORY.md`: beide Zeilen anpassen.
- Zweit-Mac: nach `git pull` keine neuen Pakete nötig (numpy, Pillow, PyYAML sind im AutoCut-venv); `venv/bin/python -m pytest -q` als Kontrolle.
