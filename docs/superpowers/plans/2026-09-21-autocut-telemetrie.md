# AutoCut Kamera-Telemetrie — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Je Clip Gyro, Beschleunigung, Brennweite und Fokus aus der Sony-rtmd-Datenspur (FX3, a7 IV) lesen, daraus Wackeln, ruhige Fenster, Haltung, Bewegungsart, Brennweiten- und Perspektivklasse ableiten (`telemetrie.json`), mit optischem Rückfall für Clips ohne Datenspur — und drei Abnehmer anschließen: Sichtung/Aftermovie, Stufe 2b, Feinschnitt 6d.

**Architecture:** Vier fokussierte Module unter `tools/autocut/src/niro_autocut/`: `rtmd.py` (Datenspur lesen/parsen, Sidecar-XML, Kamera), `telemetrie_optisch.py` (Graustufen + numpy-Phasenkorrelation), `telemetrie.py` (Kennzahlen, Clip-Messung, Cache, Charge-Lauf, `stabil_vorschlag`, Abschnittswerte), `telemetrie_bericht.py` (Markdown-Bericht, Vergleich mit dem B-Roll-Index) sowie `telemetrie_kalibrierung.py` (Gyro ↔ optisch auf demselben Fenster). CLI `scripts/autocut_telemetrie.py`. Beide Messwege liefern dieselbe Größe: Verschiebung des Bildinhalts je 25-fps-Frame in px @480 — der Gyro über die KB-Brennweite umgerechnet.

**Tech Stack:** Python 3.12 (AutoCut-venv: numpy, scipy, PyYAML; **keine neue Abhängigkeit**), ffmpeg 9 (`-map 0:d:0 -c copy -f data`, `rawvideo gray`), pytest. Kein Resolve, NAS nur lesend.

Spec: `docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md` (inkl. Nachtrag 21.09. mit Messwerten).

## Global Constraints

- Python-Aufruf immer `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python"`; Tests: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q`.
- Schreiben nur unter `<Charge>/_intern/autocut/**` (inkl. `telemetrie/` Cache) und `<Charge>/Ergebnisse/Rohschnitt/**` (Bericht `telemetrie.md`) — Schreibbereiche von `Charge.open_basis`; nie auf `/Volumes/` (NAS). **Abweichung vom Spec:** der Bericht liegt unter `Ergebnisse/Rohschnitt/telemetrie.md` (wie `broll-index.md`), nicht unter `Ergebnisse/Sortierung/`.
- Charge über `Charge.open_basis(root)` öffnen (kein Schnittplan nötig; Chargen-Ordner muss unter `projects/<Kunde>/<Projekt>/` liegen).
- Deutsch in Code-Kommentaren, Docstrings, Feldnamen, Meldungen; Stil wie `kanten.py`/`kanten_medien.py`/`kanten_bericht.py` (Modul-Docstring mit Zweck, Funktionen mit kurzen Docstrings, Zeilen ≤ 125 Zeichen).
- Fehler mit deutscher, handlungsleitender Meldung als `AutoCutError`; je Clip nie abbrechen — Fehler in den Datensatz (`fehler`), Zusammenfassung am Ende.
- Messgrößen: `wackeln` = Mittel von |Δdx|,|Δdy| zwischen Nachbarframes bei 25 fps in px @480; `bewegung` = Mittel von |dx|,|dy|; `f_px = 480 · kb_mm / 36`; `dx = ω_schwenk · π/180 · f_px / 25`. IMU-Rate aus Tag 0xE435 (2000 Hz), sonst Proben je Sample × fps. Beschleunigungs-Gate relativ zum Clip-Median (±10 %), nie absolut (FX3 misst konstant 1,15 g).
- Gyro-Feld heißt **`bewegungsart`** (statisch | schwenk_links | schwenk_rechts | tilt_auf | tilt_ab | fahrt | gemischt); das Claude-Feld `kamerabewegung` des Erst-Index bleibt unangetastet. `schwenk_links` = Kamera dreht nach links = Bildinhalt wandert nach rechts (dx > 0).
- Cache je Clip `_intern/autocut/telemetrie/<fingerprint>.json` (Fingerprint = `media.fingerprint`: Name, Größe, mtime), atomar (`.part` + `os.replace`); `--force` misst neu.
- Standardwerte unter `telemetrie:` in `defaults.yaml`, je Charge in `_intern/autocut/config.yaml` überschreibbar (`load_config`).
- Commits: Nur die Dateien der jeweiligen Task stagen (`git add <Pfade>`), nie `git add -A` — im Arbeitsbaum liegen fremde offene Änderungen (tools/motion, tools/resolve). Commit-Text deutsch, Präfix `feat(autocut):`/`test(autocut):`/`docs(autocut):`, Abschluss `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- `tests/test_docs.py::test_every_existing_script_is_documented` verlangt, dass jedes `scripts/*.py` in WORKFLOW, README oder SETUP steht — Doku gehört zur Task, die das Skript anlegt.
- **Zweiter Mac (Tagesstand MacBook 19.09.):** unkommittierte Änderungen in `tools/autocut/defaults.yaml` (`proxy_pflicht`), `cutlist.py`, `resolve_probe.py`, `test_cutlist.py` sowie ein Worktree `claude/festive-mccarthy-4e4efb` mit `media.py`, `resolve_api.py`, `sync.py`, `timeline_model.py`. Dieser Plan ändert keine dieser Dateien (nur Imports aus `media.py`); `defaults.yaml` wird nur am Ende ergänzt.

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `tools/autocut/src/niro_autocut/rtmd.py` (neu) | Datenspur per ffmpeg lesen; rtmd-Samples (Header `00 1c 01 00`, KLV-Sätze mit lokalen Tags) parsen; IMU-Blöcke, RDD-18-Distanzen, `RtmdDaten`; Sidecar-XML `<Clip>M01.XML` → Modell; `kamera_erkennen` |
| `tools/autocut/src/niro_autocut/telemetrie_optisch.py` (neu) | Graustufen-Frames 480×270 @25 fps per ffmpeg; Phasenkorrelation in numpy (Hanning, Kreuzleistungsspektrum, Subpixel); Verschiebungsreihe |
| `tools/autocut/src/niro_autocut/telemetrie.py` (neu) | Kennzahlen (Umrechnung, wackeln/bewegung, Fenster, haltung, bewegungsart, Lage, Klassen); `clip_messen`; Cache; `clips_finden`; `telemetrie_charge`; `laden`/`finden`; `abschnitt_werte`; `stabil_vorschlag` |
| `tools/autocut/src/niro_autocut/telemetrie_bericht.py` (neu) | `Ergebnisse/Rohschnitt/telemetrie.md`: unruhigste Clips, Verteilungen, Clips ohne Daten, Vergleich mit `broll_index.json` |
| `tools/autocut/src/niro_autocut/telemetrie_kalibrierung.py` (neu) | Gyro ↔ optisch auf demselben Fenster je Clip; Achsen/Vorzeichen, Faktor je Kamera, Spearman; Gegenprobe gegen `ruhe.json` |
| `tools/autocut/scripts/autocut_telemetrie.py` (neu) | CLI: Messung, Bericht, `--kalibrieren` |
| `tools/autocut/defaults.yaml` | Block `telemetrie:` |
| `tools/autocut/src/niro_autocut/index_sections.py` | Stufe 2b: Kontextzeile, Überschreiben von `brennweite`/`perspektive_hoehe`, `bewegungsart`/`haltung` je Abschnitt, `felder_quelle` |
| `tools/autocut/scripts/autocut_index_sections.py` | `--dry-run` nennt Clips mit Telemetrie |
| `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py` | 6d: `BROLL` mit optionaler 7. Spalte `stabil`, Vorschlag im Probelauf, `Stabilize()` nur für ausgewählte Shots |
| `tools/autocut/vorlagen/README.md`, `tools/autocut/README.md`, `tools/autocut/WORKFLOW-AutoCut.md`, `tools/autocut/tests/test_docs.py` | Doku |
| `tools/autocut/tests/test_rtmd.py`, `test_telemetrie_optisch.py`, `test_telemetrie.py`, `test_telemetrie_bericht.py`, `test_telemetrie_script.py`, `test_telemetrie_kalibrierung.py`, `test_index_sections.py` (Ergänzung) | Tests |
| `tools/autocut/tests/fixtures/rtmd_fx3_25p.bin`, `rtmd_a7iv_50p.bin` (Task 7) | 0,3 s echte Datenspur je Kamera |

---

### Task 1: `rtmd.py` — Datenspur lesen, Samples parsen, IMU/Brennweite auswerten, Sidecar, Kamera

**Files:**
- Create: `tools/autocut/src/niro_autocut/rtmd.py`
- Test: `tools/autocut/tests/test_rtmd.py`

**Interfaces:**
- Consumes: `niro_autocut.charge.AutoCutError`, `niro_autocut.media._which`
- Produces:
  - `HEADER = b"\x00\x1c\x01\x00"`, `UL = bytes.fromhex("060e2b34")`, Tag-Konstanten `TAG_FOKUS_M=0x8001`, `TAG_KB_MM=0x8004`, `TAG_BRENNWEITE_MM=0x8005`, `TAG_IMU_HZ=0xE435`, `TAG_GYRO=0xE43B`, `TAG_GYRO_SKALA=0xE439`, `TAG_ACC=0xE44B`, `TAG_ACC_SKALA=0xE449`
  - `datenspur_lesen(path) -> bytes` (leer = keine Datenspur)
  - `ber(buf, i) -> tuple[int, int]`, `distanz(v: int) -> float`
  - `samples(buf) -> list[dict[int, bytes]]`
  - `imu_block(block: bytes, skala: float) -> np.ndarray` (n, 3)
  - `@dataclass RtmdDaten(samples: int, imu_hz: float | None, proben_je_sample: int, gyro: np.ndarray, acc: np.ndarray, brennweite_mm: list[float], kb_mm: list[float], fokus_m: list[float])`
  - `auswerten(sample_list) -> RtmdDaten`
  - `sidecar_modell(path) -> str | None`
  - `kamera_erkennen(path, modell: str | None = None) -> str` (`FX3` | `a7IV` | `DJI` | `Sony <Modell>` | `unbekannt`)
  - `paket_bauen(tags: dict[int, bytes], groesse: int = 0) -> bytes` (Test-Helfer im Modul: baut ein rtmd-Sample mit Header und einem KLV-Satz; `groesse` > 0 füllt auf feste Sample-Größe auf)

- [ ] **Step 1: Failing Tests schreiben**

```python
# tools/autocut/tests/test_rtmd.py
"""rtmd.py — Sony-Datenspur: BER, RDD-18-Distanz, Sample-Parser, IMU-Blöcke, Auswertung, Sidecar, Kamera (ohne NAS)."""
from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import pytest

from niro_autocut import rtmd as R

FIXTURES = Path(__file__).parent / "fixtures"


def _imu(werte: list[tuple[int, int, int]], groesse: int = 6) -> bytes:
    """IMU-Block wie in der Kamera: n (u32), groesse (u32), dann n × groesse Bytes, je Probe int16 x, y, z."""
    out = struct.pack(">II", len(werte), groesse)
    for x, y, z in werte:
        out += struct.pack(">hhh", x, y, z) + b"\x00" * (groesse - 6)
    return out


def test_ber_kurz_und_lang():
    assert R.ber(b"\x24", 0) == (36, 1)
    assert R.ber(b"\x83\x00\x00\x24", 0) == (36, 4)


def test_distanz_rdd18():
    # Werte aus FX3_0330 (Nachtrag 21.09.): 0xc2cc → 71,6 mm KB, 0xc2a5 → 67,7 mm, 0xe62e → 15,82 m Fokus
    assert round(R.distanz(0xC2CC) * 1000, 1) == 71.6
    assert round(R.distanz(0xC2A5) * 1000, 1) == 67.7
    assert round(R.distanz(0xE62E), 2) == 15.82


def test_samples_parst_zwei_pakete_mit_fuellung():
    a = R.paket_bauen({0x8004: bytes.fromhex("c2cc"), 0x8005: bytes.fromhex("c2a5")}, groesse=256)
    b = R.paket_bauen({0x8004: bytes.fromhex("c2a5")}, groesse=256)
    s = R.samples(a + b)
    assert len(s) == 2 and s[0][0x8004] == bytes.fromhex("c2cc") and s[1][0x8004] == bytes.fromhex("c2a5")


def test_samples_ueberspringt_muell_vor_dem_header():
    p = R.paket_bauen({0x8004: bytes.fromhex("c2cc")})
    assert len(R.samples(b"\xf0\x10\x20\x00" + p)) == 1
    assert R.samples(b"") == [] and R.samples(b"\x00\x1c\x01\x00") == []


def test_imu_block_skaliert_und_liest_nur_xyz():
    blk = _imu([(655, -131, 65), (0, 0, 0)], groesse=8)
    g = R.imu_block(blk, 65.5)
    assert g.shape == (2, 3) and np.allclose(g[0], [10.0, -2.0, 1.0]) and np.allclose(g[1], 0)
    assert R.imu_block(struct.pack(">II", 0, 6), 65.5).shape == (0, 3)


def test_auswerten_gyro_acc_hz_brennweite_fokus():
    tags = {R.TAG_GYRO: _imu([(655, 0, 0)] * 4), R.TAG_GYRO_SKALA: struct.pack(">f", 65.5),
            R.TAG_ACC: _imu([(0, 8192, 0)] * 4), R.TAG_ACC_SKALA: struct.pack(">f", 8192.0),
            R.TAG_IMU_HZ: struct.pack(">I", 2000), R.TAG_KB_MM: bytes.fromhex("c2cc"),
            R.TAG_BRENNWEITE_MM: bytes.fromhex("c2a5"), R.TAG_FOKUS_M: bytes.fromhex("e62e")}
    d = R.auswerten(R.samples(R.paket_bauen(tags) + R.paket_bauen(tags)))
    assert d.samples == 2 and d.imu_hz == 2000.0 and d.proben_je_sample == 4
    assert d.gyro.shape == (8, 3) and np.allclose(d.gyro[:, 0], 10.0)
    assert d.acc.shape == (8, 3) and np.allclose(d.acc[:, 1], 1.0)
    assert d.kb_mm == [71.6, 71.6] and d.brennweite_mm == [67.7, 67.7] and d.fokus_m == [15.82, 15.82]


def test_auswerten_ohne_imu_und_mit_ffff():
    d = R.auswerten(R.samples(R.paket_bauen({R.TAG_KB_MM: b"\xff\xff"})))
    assert d.samples == 1 and d.imu_hz is None and d.gyro.shape == (0, 3) and d.kb_mm == []


def test_sidecar_modell_und_kamera(tmp_path):
    clip = tmp_path / "FX3_0330.MP4"
    clip.write_bytes(b"x")
    (tmp_path / "FX3_0330M01.XML").write_text(
        '<?xml version="1.0"?><NonRealTimeMeta xmlns="urn:schemas-professionalDisc:nonRealTimeMeta:ver.2.20">'
        '<Device manufacturer="Sony" modelName="ILME-FX3" serialNo="1"/></NonRealTimeMeta>', encoding="utf-8")
    assert R.sidecar_modell(clip) == "ILME-FX3"
    assert R.sidecar_modell(tmp_path / "ohne.MP4") is None
    assert R.kamera_erkennen(clip, "ILME-FX3") == "FX3"
    assert R.kamera_erkennen("a7MK4_20260913_2128.MP4", "ILCE-7M4") == "a7IV"
    assert R.kamera_erkennen("a7MK4_20260913_2128.MP4") == "a7IV"
    assert R.kamera_erkennen("DJI_0504.MOV") == "DJI"
    assert R.kamera_erkennen("C0001.MP4", "ILME-FX30") == "Sony ILME-FX30"
    assert R.kamera_erkennen("C0001.MP4") == "unbekannt"


@pytest.mark.parametrize("name,fps,proben", [("rtmd_fx3_25p.bin", 25.0, 80), ("rtmd_a7iv_50p.bin", 50.0, 40)])
def test_echte_datenspur(name, fps, proben):
    """Echte 0,3-s-Auszüge (Task 7 legt sie an) — bis dahin übersprungen."""
    f = FIXTURES / name
    if not f.exists():
        pytest.skip(f"{name} fehlt (Kalibrierlauf Task 7)")
    d = R.auswerten(R.samples(f.read_bytes()))
    assert d.samples >= 5 and d.imu_hz == 2000.0 and d.proben_je_sample == proben
    assert d.gyro.shape[0] == d.samples * proben and np.abs(d.gyro).max() < 500
    betrag = np.linalg.norm(d.acc, axis=1)
    assert 0.8 < np.median(betrag) < 1.3          # a7 IV ≈ 1,0 g, FX3 ≈ 1,15 g
    assert 10 < np.median(d.kb_mm) < 600
```

- [ ] **Step 2: Tests laufen lassen — sie müssen fehlschlagen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_rtmd.py -q`
Expected: FAIL/ERROR mit `ModuleNotFoundError: No module named 'niro_autocut.rtmd'`

- [ ] **Step 3: Modul schreiben**

```python
# tools/autocut/src/niro_autocut/rtmd.py
"""Sony-rtmd-Datenspur (FX3, a7 IV) lesen und auswerten: Gyro, Beschleunigung, Brennweite, Fokus; Sidecar-XML → Kamera.

Aufbau der Datenspur (gemessen 21.09.2026, Spec-Nachtrag): ein rtmd-Sample je Videoframe, 19 456 Bytes, Header
``00 1c 01 00`` + 24 Bytes, dann KLV-Sätze (16-Byte-Key ab ``06 0e 2b 34``, BER-Länge, lokale Tags ``>HH`` Tag/Länge + Wert),
Rest Füllung. IMU-Block (0xE43B Gyro, 0xE44B Beschleunigung): n (u32), groesse (u32), n × groesse Bytes, je Probe int16 x/y/z;
Skalen 0xE439/0xE449 (float32, LSB je °/s bzw. je g); 0xE435 = IMU-Rate (u32, 2000). Distanzen (0x8001 Fokus, 0x8004 KB,
0x8005 Brennweite) im RDD-18-Format, 0xFFFF = unbekannt. Achsen: x links, y oben, z vorwärts.
Alles nur lesend; ``datenspur_lesen`` liest die ganze Datei (≈ 300 MB/s übers NAS).
"""
from __future__ import annotations

import struct
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .charge import AutoCutError
from .media import _which

HEADER = b"\x00\x1c\x01\x00"
UL = bytes.fromhex("060e2b34")
KLV_KEY = bytes.fromhex("060e2b3402530101" "0c02010101010000")   # Key des Sony-Satzes mit den Objektivdaten (Beispiel)
TAG_FOKUS_M, TAG_KB_MM, TAG_BRENNWEITE_MM = 0x8001, 0x8004, 0x8005
TAG_IMU_HZ = 0xE435
TAG_GYRO, TAG_GYRO_SKALA = 0xE43B, 0xE439
TAG_ACC, TAG_ACC_SKALA = 0xE44B, 0xE449
MODELLE = {"ILME-FX3": "FX3", "ILCE-7M4": "a7IV"}
KEINE_DATENSPUR = (b"matches no streams", b"does not contain any stream")


@dataclass
class RtmdDaten:
    samples: int                      # rtmd-Samples = Videoframes
    imu_hz: float | None              # aus Tag 0xE435, sonst None (dann Proben je Sample × fps)
    proben_je_sample: int             # IMU-Proben je rtmd-Sample (80 bei 25p, 40 bei 50p)
    gyro: np.ndarray                  # (n, 3) °/s, alle Proben in Reihenfolge; (0, 3) ohne IMU
    acc: np.ndarray                   # (n, 3) g
    brennweite_mm: list[float] = field(default_factory=list)   # je Sample
    kb_mm: list[float] = field(default_factory=list)
    fokus_m: list[float] = field(default_factory=list)


def datenspur_lesen(path: str | Path) -> bytes:
    """Datenspur 0:d:0 als Rohbytes; leer, wenn die Datei keine Datenspur hat (Mavic, fremde Kamera)."""
    p = Path(path)
    if not p.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {p}\nIst das NAS gemountet?")
    cmd = [_which("ffmpeg"), "-v", "error", "-i", str(p), "-map", "0:d:0", "-c", "copy", "-f", "data", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        if any(m in r.stderr for m in KEINE_DATENSPUR):
            return b""
        raise AutoCutError(f"Datenspur nicht lesbar für {p.name}: {r.stderr[-300:].decode(errors='replace')}")
    return r.stdout


def ber(buf: bytes, i: int) -> tuple[int, int]:
    """BER-Länge ab buf[i]: (Länge, Index nach der Länge)."""
    b = buf[i]
    if b < 0x80:
        return b, i + 1
    n = b & 0x7F
    return int.from_bytes(buf[i + 1:i + 1 + n], "big"), i + 1 + n


def distanz(v: int) -> float:
    """RDD-18: obere 4 Bit Exponent (Zweierkomplement, Basis 10), untere 12 Bit Mantisse; Meter."""
    e = v >> 12
    e = e - 16 if e >= 8 else e
    return (v & 0x0FFF) * 10.0 ** e


def samples(buf: bytes) -> list[dict[int, bytes]]:
    """Alle rtmd-Samples: je Sample ein Dict Tag → Wert (erster Treffer je Tag über alle KLV-Sätze des Samples)."""
    out: list[dict[int, bytes]] = []
    i = 0
    while i + 28 < len(buf):
        if buf[i:i + 4] != HEADER:
            nxt = buf.find(HEADER, i + 1)
            if nxt == -1:
                break
            i = nxt
            continue
        j, tags = i + 28, {}
        while j + 17 < len(buf) and buf[j:j + 4] == UL:
            ln, k = ber(buf, j + 16)
            ende = min(k + ln, len(buf))
            while k + 4 <= ende:
                t, l = struct.unpack(">HH", buf[k:k + 4])
                tags.setdefault(t, buf[k + 4:k + 4 + l])
                k += 4 + l
            j = ende
        if tags:
            out.append(tags)
        i = max(j, i + 28)
    return out


def imu_block(block: bytes, skala: float) -> np.ndarray:
    """IMU-Block → (n, 3) float64 in °/s bzw. g; leer bei n = 0, zu kleiner Probe oder Skala ≤ 0."""
    if len(block) < 8:
        return np.zeros((0, 3), np.float64)
    n, groesse = struct.unpack(">II", block[:8])
    if n == 0 or groesse < 6 or skala <= 0 or len(block) < 8 + n * groesse:
        return np.zeros((0, 3), np.float64)
    raw = np.frombuffer(block[8:8 + n * groesse], dtype=">i2")
    return raw.reshape(n, groesse // 2)[:, :3].astype(np.float64) / skala


def auswerten(sample_list: list[dict[int, bytes]]) -> RtmdDaten:
    """Samples → RtmdDaten (Gyro/Acc aneinandergehängt, Distanzen je Sample; 0xFFFF und fehlende Tags übersprungen)."""
    gyro, acc, f_ist, f_kb, fokus = [], [], [], [], []
    hz = None
    for s in sample_list:
        if TAG_GYRO in s and TAG_GYRO_SKALA in s and len(s[TAG_GYRO_SKALA]) == 4:
            gyro.append(imu_block(s[TAG_GYRO], struct.unpack(">f", s[TAG_GYRO_SKALA])[0]))
        if TAG_ACC in s and TAG_ACC_SKALA in s and len(s[TAG_ACC_SKALA]) == 4:
            acc.append(imu_block(s[TAG_ACC], struct.unpack(">f", s[TAG_ACC_SKALA])[0]))
        if hz is None and TAG_IMU_HZ in s and len(s[TAG_IMU_HZ]) == 4:
            hz = float(struct.unpack(">I", s[TAG_IMU_HZ])[0]) or None
        for tag, ziel, faktor, stellen in ((TAG_BRENNWEITE_MM, f_ist, 1000.0, 1), (TAG_KB_MM, f_kb, 1000.0, 1),
                                           (TAG_FOKUS_M, fokus, 1.0, 2)):
            if tag in s and len(s[tag]) == 2:
                v = struct.unpack(">H", s[tag])[0]
                if v != 0xFFFF:
                    ziel.append(round(distanz(v) * faktor, stellen))
    g = np.concatenate(gyro) if gyro else np.zeros((0, 3), np.float64)
    a = np.concatenate(acc) if acc else np.zeros((0, 3), np.float64)
    proben = int(gyro[0].shape[0]) if gyro else 0
    return RtmdDaten(samples=len(sample_list), imu_hz=hz, proben_je_sample=proben, gyro=g, acc=a,
                     brennweite_mm=f_ist, kb_mm=f_kb, fokus_m=fokus)


def sidecar_modell(path: str | Path) -> str | None:
    """Kameramodell aus der Sony-Sidecar ``<Clip>M01.XML`` neben der Datei (``<Device modelName="ILME-FX3"/>``)."""
    p = Path(path)
    xml = p.with_name(p.stem + "M01.XML")
    if not xml.is_file():
        return None
    try:
        for el in ET.parse(xml).iter():
            if str(el.tag).endswith("Device") and el.get("modelName"):
                return el.get("modelName")
    except ET.ParseError:
        return None
    return None


def kamera_erkennen(path: str | Path, modell: str | None = None) -> str:
    """Kamera-Kürzel: Sidecar-Modell zuerst, dann Dateinamen-Präfix (FX3_, a7MK4_, DJI_), sonst „unbekannt"."""
    if modell:
        if modell in MODELLE:
            return MODELLE[modell]
        return f"Sony {modell}" if modell.startswith(("ILME", "ILCE", "ZV")) else modell
    name = Path(path).name.upper()
    if name.startswith("FX3"):
        return "FX3"
    if name.startswith("A7"):
        return "a7IV"
    if name.startswith("DJI"):
        return "DJI"
    return "unbekannt"


def paket_bauen(tags: dict[int, bytes], groesse: int = 0) -> bytes:
    """Ein rtmd-Sample mit Header und einem KLV-Satz aus ``tags`` (für Tests); ``groesse`` > 0 füllt auf feste Länge auf."""
    body = b"".join(struct.pack(">HH", t, len(v)) + v for t, v in tags.items())
    laenge = bytes([len(body)]) if len(body) < 0x80 else b"\x83" + len(body).to_bytes(3, "big")
    paket = HEADER + b"\x00" * 24 + KLV_KEY + laenge + body
    if groesse > len(paket):
        paket += b"\xf0\x10\x20\x00" * ((groesse - len(paket)) // 4) + b"\x00" * ((groesse - len(paket)) % 4)
    return paket
```

- [ ] **Step 4: Tests laufen lassen — sie müssen bestehen (Fixture-Tests übersprungen)**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_rtmd.py -q`
Expected: `8 passed, 2 skipped`

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/src/niro_autocut/rtmd.py tools/autocut/tests/test_rtmd.py && git commit -q -m "feat(autocut): rtmd.py — Sony-Datenspur parsen (Gyro, Beschleunigung, Brennweite, Fokus), Sidecar-XML, Kamera

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: `telemetrie_optisch.py` — Graustufen-Frames und numpy-Phasenkorrelation

**Files:**
- Create: `tools/autocut/src/niro_autocut/telemetrie_optisch.py`
- Test: `tools/autocut/tests/test_telemetrie_optisch.py`

**Interfaces:**
- Consumes: `niro_autocut.media._which`, `AutoCutError`
- Produces:
  - `BREITE = 480`, `HOEHE = 270`
  - `graustufen(path, fps=25.0, von_s=None, dauer_s=None, breite=480, hoehe=270) -> np.ndarray` (n, hoehe, breite) uint8
  - `phasenkorrelation(a, b) -> tuple[float, float]` — Verschiebung des Bildinhalts von a nach b; dx > 0 nach rechts, dy > 0 nach unten
  - `verschiebungen(frames) -> np.ndarray` (n−1, 2) float64

- [ ] **Step 1: Failing Tests schreiben**

```python
# tools/autocut/tests/test_telemetrie_optisch.py
"""telemetrie_optisch.py — Phasenkorrelation (Vorzeichen, Ganz- und Subpixel) und Frame-Dekodierung mit ffmpeg testsrc."""
from __future__ import annotations

import shutil
import subprocess

import numpy as np
import pytest

from niro_autocut import telemetrie_optisch as O


def _bild(rng, h=270, w=480, rand=40):
    """Geglättetes Rauschbild mit Rand, aus dem verschobene Ausschnitte geschnitten werden."""
    base = rng.random((h + rand, w + rand)).astype(np.float32)
    k = np.ones((5, 5), np.float32) / 25
    from numpy.lib.stride_tricks import sliding_window_view
    sm = sliding_window_view(base, (5, 5)).reshape(-1, 25) @ k.ravel()
    return sm.reshape(h + rand - 4, w + rand - 4)


def test_phasenkorrelation_vorzeichen_und_subpixel():
    rng = np.random.default_rng(1)
    sm = _bild(rng)
    a = sm[10:280, 10:490]
    for sx, sy in ((5, 0), (-3, 2), (0, 7)):
        b = sm[10 - sy:280 - sy, 10 - sx:490 - sx]      # Inhalt von a um (sx, sy) verschoben: rechts/unten positiv
        dx, dy = O.phasenkorrelation(a, b)
        assert abs(dx - sx) < 0.1 and abs(dy - sy) < 0.1, (sx, sy, dx, dy)
    b = 0.5 * (sm[10:280, 8:488] + sm[10:280, 7:487])   # 2,5 px nach rechts
    dx, dy = O.phasenkorrelation(a, b)
    assert abs(dx - 2.5) < 0.15 and abs(dy) < 0.1


def test_phasenkorrelation_identisch_null():
    rng = np.random.default_rng(2)
    a = _bild(rng)[10:280, 10:490]
    assert O.phasenkorrelation(a, a) == (0.0, 0.0)


def test_verschiebungen_reihe():
    rng = np.random.default_rng(3)
    sm = _bild(rng)
    frames = np.stack([sm[10:280, 10 + k:490 + k] for k in (0, 2, 4, 4)])   # Inhalt wandert je Schritt 2 px nach links
    v = O.verschiebungen(frames)
    assert v.shape == (3, 2)
    assert np.allclose(v[:, 0], [-2, -2, 0], atol=0.1) and np.allclose(v[:, 1], 0, atol=0.1)
    assert O.verschiebungen(frames[:1]).shape == (0, 2)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")
def test_graustufen_dekodiert_testsrc(tmp_path):
    clip = tmp_path / "test.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:duration=2",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    fr = O.graustufen(clip)
    assert fr.shape == (50, 270, 480) and fr.dtype == np.uint8
    teil = O.graustufen(clip, von_s=1.0, dauer_s=0.4)
    assert 8 <= teil.shape[0] <= 11
    assert O.verschiebungen(fr[:5]).shape == (4, 2)
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_telemetrie_optisch.py -q`
Expected: ERROR `No module named 'niro_autocut.telemetrie_optisch'`

- [ ] **Step 3: Modul schreiben**

```python
# tools/autocut/src/niro_autocut/telemetrie_optisch.py
"""Optischer Messweg der Telemetrie: Graustufen-Frames 480×270 bei 25 fps und globale Verschiebung zwischen Nachbarframes
per Phasenkorrelation (numpy statt cv2, damit es im AutoCut-venv läuft). Rückfall für Clips ohne rtmd (Mavic) und
Referenz der Kalibrierung. Übernimmt das Verfahren aus ``ruhe.py`` der Hochzeitszauber-Charge.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from .charge import AutoCutError
from .media import _which

BREITE, HOEHE = 480, 270
_FENSTER: dict[tuple[int, int], np.ndarray] = {}


def graustufen(path: str | Path, fps: float = 25.0, von_s: float | None = None, dauer_s: float | None = None,
               breite: int = BREITE, hoehe: int = HOEHE) -> np.ndarray:
    """Frames als (n, hoehe, breite) uint8; ``von_s``/``dauer_s`` schneiden per ffmpeg ``-ss``/``-t`` (Suche im Index)."""
    p = Path(path)
    if not p.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {p}\nIst das NAS gemountet?")
    cmd = [_which("ffmpeg"), "-v", "error"]
    if von_s is not None:
        cmd += ["-ss", f"{von_s:.3f}"]
    if dauer_s is not None:
        cmd += ["-t", f"{dauer_s:.3f}"]
    cmd += ["-i", str(p), "-an", "-vf", f"fps={fps:g},scale={breite}:{hoehe}", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise AutoCutError(f"Frames nicht dekodierbar für {p.name}: {r.stderr[-300:].decode(errors='replace')}")
    n = len(r.stdout) // (breite * hoehe)
    return np.frombuffer(r.stdout, np.uint8)[: n * breite * hoehe].reshape(n, hoehe, breite)


def _fenster(h: int, w: int) -> np.ndarray:
    if (h, w) not in _FENSTER:
        _FENSTER[(h, w)] = np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
    return _FENSTER[(h, w)]


def _subpixel(cm1: float, c0: float, cp1: float) -> float:
    d = cm1 - 2.0 * c0 + cp1
    return 0.0 if d == 0 else 0.5 * (cm1 - cp1) / d


def phasenkorrelation(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """Verschiebung des Bildinhalts von ``a`` nach ``b`` in Pixeln: dx > 0 nach rechts, dy > 0 nach unten (Subpixel)."""
    h, w = a.shape
    win = _fenster(h, w)
    fa = np.fft.fft2((a.astype(np.float32) - float(a.mean())) * win)
    fb = np.fft.fft2((b.astype(np.float32) - float(b.mean())) * win)
    r = fa * np.conj(fb)
    r /= np.abs(r) + 1e-9
    c = np.real(np.fft.ifft2(r))
    iy, ix = np.unravel_index(int(np.argmax(c)), c.shape)
    py = iy + _subpixel(c[(iy - 1) % h, ix], c[iy, ix], c[(iy + 1) % h, ix])
    px = ix + _subpixel(c[iy, (ix - 1) % w], c[iy, ix], c[iy, (ix + 1) % w])
    if px > w / 2:
        px -= w
    if py > h / 2:
        py -= h
    return float(-px), float(-py)


def verschiebungen(frames: np.ndarray) -> np.ndarray:
    """(n−1, 2): Verschiebung des Inhalts von Frame i nach i+1 in px."""
    if len(frames) < 2:
        return np.zeros((0, 2), np.float64)
    return np.array([phasenkorrelation(frames[i], frames[i + 1]) for i in range(len(frames) - 1)], np.float64)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_telemetrie_optisch.py -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/src/niro_autocut/telemetrie_optisch.py tools/autocut/tests/test_telemetrie_optisch.py && git commit -q -m "feat(autocut): telemetrie_optisch.py — Graustufen-Frames und numpy-Phasenkorrelation (optischer Messweg)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: `telemetrie.py` (Teil 1) — Kennzahlen aus der Verschiebungsreihe

**Files:**
- Create: `tools/autocut/src/niro_autocut/telemetrie.py`
- Test: `tools/autocut/tests/test_telemetrie.py`

**Interfaces:**
- Consumes: nichts aus anderen Tasks (reine numpy-Rechnung); `cfg` = `defaults.yaml["telemetrie"]` (Task 4 legt den Block an; die Tests bauen das Dict selbst)
- Produces:
  - `ZIEL_FPS = 25.0`, `BEWEGUNGSARTEN`, `HALTUNGEN`
  - `f_px(kb_mm, breite=480) -> float`
  - `gyro_je_frame(werte, proben_je_sample, fps, ziel_fps=25.0) -> np.ndarray` (m, 3)
  - `verschiebung_aus_rate(rate, kb_mm, cfg, ziel_fps=25.0) -> np.ndarray` (m, 2)
  - `wackeln_bewegung(dxy) -> tuple[float, float]`
  - `hf_anteil(dxy, fps=25.0, grenze_hz=3.0) -> float`
  - `schwellen_px(kb_mm, cfg) -> tuple[float, float]` (min_px Schwenk/Tilt, stativ_px)
  - `bewegungsart(dxy, cfg, min_px, stativ_px) -> str`
  - `haltung(dxy, stativ_px, cfg) -> str`
  - `fenster(dxy, cfg, min_px, stativ_px) -> list[dict]` (`t_s`, `wackeln`, `bewegung`, `bewegungsart`)
  - `mehrheit(werte, anteil=0.6) -> str`
  - `lage(acc, toleranz=0.10, vorzeichen_pitch=1.0) -> dict` (`pitch_grad`, `roll_grad`, `grund`)
  - `brennweitenklasse(kb_mm, grenzen) -> str`, `perspektive_hoehe(pitch_grad, grenzen) -> str | None`
  - `kennzahlen(dxy, cfg, kb_mm) -> dict` (`wackeln`, `bewegung`, `haltung`, `hf_anteil`, `bewegungsart`, `fenster`, `ruhige_fenster`)

- [ ] **Step 1: Failing Tests schreiben**

```python
# tools/autocut/tests/test_telemetrie.py
"""telemetrie.py — Kennzahlen (synthetische Verläufe), später Clip-Messung, Cache, Charge-Lauf, 2b/6d-Helfer (Task 4)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from niro_autocut import telemetrie as T

CFG = {"fenster_s": 2.0, "schritt_s": 1.0, "tiefpass_s": 0.5, "ruhig_max_px": 0.15, "stativ_max_grad_s": 0.3,
       "stativ_max_px": 0.02, "schwenk_min_grad_s": 3.0, "schwenk_min_px": 1.0, "hf_grenze_hz": 3.0,
       "hand_hf_anteil_min": 0.35, "brennweite_klassen_kb": [30, 60], "pitch_klassen_grad": [-60, -8, 8],
       "achsen": {"schwenk": 1, "tilt": 0}, "vorzeichen": {"schwenk": -1, "tilt": 1, "pitch": 1},
       "px_faktor": {"FX3": 1.0, "a7IV": 1.0}, "optisch_fuer": [], "optisch_breite": 480, "parallel": 2}


def _sinus(hz: float, amp: float, n: int = 100, fps: float = 25.0) -> np.ndarray:
    t = np.arange(n) / fps
    return np.stack([amp * np.sin(2 * math.pi * hz * t), np.zeros(n)], axis=1)


def test_f_px_und_gyro_je_frame():
    assert T.f_px(36.0) == 480.0 and round(T.f_px(283.8), 1) == 3784.0
    g = np.tile(np.array([[1.0, 2.0, 3.0]]), (160, 1))
    g[80:] *= 2
    m = T.gyro_je_frame(g, 80, 25.0)
    assert m.shape == (2, 3) and np.allclose(m[0], [1, 2, 3]) and np.allclose(m[1], [2, 4, 6])
    assert T.gyro_je_frame(g, 40, 50.0).shape == (2, 3)          # 50p: 40 Proben je Frame, 2 Frames je Zielframe
    assert T.gyro_je_frame(np.zeros((0, 3)), 80, 25.0).shape == (0, 3)


def test_verschiebung_aus_rate_achsen_und_vorzeichen():
    rate = np.zeros((4, 3))
    rate[:, 1] = 10.0                                    # Schwenk um y mit 10 °/s
    dxy = T.verschiebung_aus_rate(rate, 36.0, CFG)     # f_px 480 → 10 °/s ≙ 3,351 px je Frame
    assert dxy.shape == (4, 2) and np.allclose(dxy[:, 0], -3.351, atol=0.01) and np.allclose(dxy[:, 1], 0)
    rate2 = np.zeros((4, 3))
    rate2[:, 0] = 5.0                                    # Tilt um x
    dxy2 = T.verschiebung_aus_rate(rate2, 36.0, CFG)
    assert np.allclose(dxy2[:, 0], 0) and np.allclose(dxy2[:, 1], 1.676, atol=0.01)


def test_wackeln_bewegung_wie_ruhe_py():
    dxy = np.array([[0, 0], [1, 0], [0, 0], [1, 0]], float)
    wk, bw = T.wackeln_bewegung(dxy)
    assert wk == 0.5 and bw == 0.25            # Mittel über beide Spalten: |Δdx| = 1,1,1 / |Δdy| = 0 → 0,5; |dx| Mittel 0,5, |dy| 0 → 0,25
    assert T.wackeln_bewegung(np.zeros((1, 2))) == (0.0, 0.0)


def test_hf_anteil_trennt_schnell_von_langsam():
    assert T.hf_anteil(_sinus(6.0, 1.0)) > 0.9
    assert T.hf_anteil(_sinus(0.5, 3.0)) < 0.1
    assert T.hf_anteil(np.zeros((100, 2))) == 0.0 and T.hf_anteil(np.zeros((4, 2))) == 0.0


def test_schwellen_px_mit_und_ohne_brennweite():
    min_px, stativ_px = T.schwellen_px(36.0, CFG)
    assert round(min_px, 3) == 1.005 and round(stativ_px, 4) == 0.1005     # 3 °/s bzw. 0,3 °/s bei f_px 480
    assert T.schwellen_px(None, CFG) == (1.0, 0.02)


@pytest.mark.parametrize("dxy,erwartet", [
    (np.zeros((50, 2)), "statisch"),
    (np.tile([[2.0, 0.0]], (50, 1)), "schwenk_links"),
    (np.tile([[-2.0, 0.0]], (50, 1)), "schwenk_rechts"),
    (np.tile([[0.0, 2.0]], (50, 1)), "tilt_auf"),
    (np.tile([[0.0, -2.0]], (50, 1)), "tilt_ab"),
    (np.vstack([np.tile([[2.0, 0.0]], (25, 1)), np.tile([[-2.0, 0.0]], (25, 1))]), "gemischt"),
    (np.tile([[2.0, 2.0]], (50, 1)), "gemischt"),
])
def test_bewegungsart_klassen(dxy, erwartet):
    assert T.bewegungsart(dxy, CFG, 1.0, 0.02) == erwartet


def test_bewegungsart_fahrt_ohne_dominante_richtung():
    rng = np.random.default_rng(0)
    dxy = rng.normal(0, 0.3, (50, 2))                  # Bewegung da, Mittel ≈ 0 → Fahrt
    assert T.bewegungsart(dxy, CFG, 1.0, 0.02) == "fahrt"


def test_haltung():
    assert T.haltung(np.zeros((100, 2)), 0.02, CFG) == "stativ"
    assert T.haltung(_sinus(6.0, 1.0), 0.02, CFG) == "hand"
    assert T.haltung(_sinus(0.3, 3.0), 0.02, CFG) == "gimbal"


def test_fenster_und_mehrheit():
    fen = T.fenster(np.tile([[2.0, 0.0]], (100, 1)), CFG, 1.0, 0.02)
    assert [f["t_s"] for f in fen] == [0.0, 1.0, 2.0, 3.0] and all(f["bewegungsart"] == "schwenk_links" for f in fen)
    assert [f["t_s"] for f in T.fenster(np.zeros((74, 2)), CFG, 1.0, 0.02)] == [0.0, 1.0]     # 3-s-Clip optisch: 74 Verschiebungen
    assert fen[0]["wackeln"] == 0.0 and fen[0]["bewegung"] == 1.0
    kurz = T.fenster(np.zeros((20, 2)), CFG, 1.0, 0.02)
    assert len(kurz) == 1 and kurz[0]["t_s"] == 0.0
    assert T.fenster(np.zeros((1, 2)), CFG, 1.0, 0.02) == []
    assert T.mehrheit(["fahrt", "fahrt", "statisch"]) == "fahrt" and T.mehrheit(["fahrt", "statisch"]) == "gemischt"
    assert T.mehrheit([]) == "gemischt"


def test_lage_pitch_roll_und_gate():
    ruhig = np.tile([[0.0, 1.15, 0.0]], (200, 1))                       # FX3-Betrag 1,15 g, waagerecht
    l = T.lage(ruhig)
    assert l["pitch_grad"] == 0.0 and l["roll_grad"] == 0.0 and l["grund"] is None
    unten = np.tile([[0.0, math.cos(math.radians(30)), -math.sin(math.radians(30))]], (200, 1))
    assert T.lage(unten)["pitch_grad"] == -30.0                          # Kamera schaut 30° nach unten
    assert T.lage(unten, vorzeichen_pitch=-1.0)["pitch_grad"] == 30.0
    schief = np.tile([[math.sin(math.radians(2)), math.cos(math.radians(2)), 0.0]], (200, 1))
    assert T.lage(schief)["roll_grad"] == 2.0
    wild = np.tile([[0.0, 1.0, 0.0]], (200, 1)) * np.linspace(0.5, 1.5, 200)[:, None]
    assert T.lage(wild)["pitch_grad"] is None and "schwankt" in T.lage(wild)["grund"]
    assert T.lage(np.zeros((0, 3)))["grund"] == "keine Beschleunigungsdaten"


def test_klassen():
    assert [T.brennweitenklasse(k, [30, 60]) for k in (24, 30, 50, 60, 71.6, 283.8)] == ["weit", "normal", "normal", "normal", "tele", "tele"]
    assert [T.perspektive_hoehe(p, [-60, -8, 8]) for p in (-90, -60, -12, -8, 0, 7.9, 8, 20)] == \
        ["Vogelperspektive", "Vogelperspektive", "Aufsicht", "Aufsicht", "Augenhöhe", "Augenhöhe", "Untersicht", "Untersicht"]
    assert T.perspektive_hoehe(None, [-60, -8, 8]) is None


def test_kennzahlen_gesamt():
    k = T.kennzahlen(np.tile([[2.0, 0.0]], (100, 1)), CFG, 36.0)
    assert k["wackeln"] == 0.0 and k["bewegung"] == 1.0 and k["haltung"] == "gimbal" and k["bewegungsart"] == "schwenk_links"
    assert k["fenster"][0] == [0.0, 0.0, 1.0, "schwenk_links"] and k["ruhige_fenster"] == [0.0, 1.0, 2.0, 3.0]
    assert k["hf_anteil"] == 0.0
    unruhig = T.kennzahlen(_sinus(6.0, 1.0), CFG, None)
    assert unruhig["haltung"] == "hand" and unruhig["ruhige_fenster"] == [] and unruhig["hf_anteil"] > 0.9
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_telemetrie.py -q`
Expected: ERROR `No module named 'niro_autocut.telemetrie'`

- [ ] **Step 3: Modul schreiben (Teil 1 — Kennzahlen)**

```python
# tools/autocut/src/niro_autocut/telemetrie.py
"""Kamera-Telemetrie je Clip (Spec 2026-09-19): Kennzahlen aus der Sony-rtmd-Datenspur (Gyro, Beschleunigung, Brennweite)
oder aus der optischen Verschiebungsreihe, Clip-Messung mit Cache, Charge-Lauf, Abschnittswerte für Stufe 2b und der
Stabilisierungs-Vorschlag für 6d.

Beide Messwege liefern dieselbe Größe: Verschiebung des Bildinhalts je 25-fps-Frame in px @480 (``dx`` > 0 nach rechts,
``dy`` > 0 nach unten). Der Gyro wird über die KB-Brennweite umgerechnet: ``f_px = 480 · kb_mm / 36``,
``dx = ω_schwenk · π/180 · f_px / 25``. ``wackeln`` = Mittel von |Δdx|,|Δdy| zwischen Nachbarframes (Zittern),
``bewegung`` = Mittel von |dx|,|dy| (langsame Kamerabewegung) — wie ``jitter``/``bewegung`` in ``ruhe.py``.
Bewegungsart: ``schwenk_links`` = Kamera dreht nach links = Bildinhalt wandert nach rechts.
"""
from __future__ import annotations

import datetime as _dt
import json
import math
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from .charge import AutoCutError
from .media import ffprobe, fingerprint
from .rtmd import auswerten, datenspur_lesen, kamera_erkennen, samples, sidecar_modell
from .telemetrie_optisch import graustufen, verschiebungen

ZIEL_FPS = 25.0
BEWEGUNGSARTEN = ["statisch", "schwenk_links", "schwenk_rechts", "tilt_auf", "tilt_ab", "fahrt", "gemischt"]
HALTUNGEN = ["stativ", "gimbal", "hand"]
CACHE_DIR = "telemetrie"
VIDEO_EXTS = {".mp4", ".mov", ".mxf"}


# --- Kennzahlen ---------------------------------------------------------------------------------------------------------

def f_px(kb_mm: float, breite: int = 480) -> float:
    """Brennweite in Pixeln bei Bildbreite ``breite`` (Kleinbild 36 mm breit)."""
    return breite * float(kb_mm) / 36.0


def gyro_je_frame(werte: np.ndarray, proben_je_sample: int, fps: float, ziel_fps: float = ZIEL_FPS) -> np.ndarray:
    """IMU-Proben (n, k) → Mittel je Zielframe (m, k); Proben je Zielframe = proben_je_sample · fps / ziel_fps."""
    if len(werte) == 0 or proben_je_sample <= 0:
        return np.zeros((0, werte.shape[1] if werte.ndim == 2 else 3), np.float64)
    je = max(1, int(round(proben_je_sample * fps / ziel_fps)))
    m = len(werte) // je
    return werte[: m * je].reshape(m, je, -1).mean(axis=1)


def verschiebung_aus_rate(rate: np.ndarray, kb_mm: float, cfg: dict, ziel_fps: float = ZIEL_FPS) -> np.ndarray:
    """(m, 3) °/s je Frame → (m, 2) px: dx aus der Schwenk-Achse, dy aus der Tilt-Achse (Achsen/Vorzeichen aus cfg)."""
    k = math.pi / 180.0 * f_px(kb_mm, int(cfg["optisch_breite"])) / ziel_fps
    a, v = cfg["achsen"], cfg["vorzeichen"]
    dx = float(v["schwenk"]) * rate[:, int(a["schwenk"])] * k
    dy = float(v["tilt"]) * rate[:, int(a["tilt"])] * k
    return np.stack([dx, dy], axis=1)


def wackeln_bewegung(dxy: np.ndarray) -> tuple[float, float]:
    """(wackeln, bewegung) in px je Frame wie ``ruhe.py``: Mittel von |Δ| zwischen Nachbarframes bzw. Mittel von |Wert|."""
    if len(dxy) == 0:
        return 0.0, 0.0
    bewegung = float(np.abs(dxy).mean())
    if len(dxy) < 2:
        return 0.0, bewegung
    return float(np.abs(np.diff(dxy, axis=0)).mean()), bewegung


def hf_anteil(dxy: np.ndarray, fps: float = ZIEL_FPS, grenze_hz: float = 3.0) -> float:
    """Leistungsanteil der Verschiebungsreihe ab ``grenze_hz`` (Mittel über dx und dy), 0–1; 0 bei zu kurzer/leerer Reihe."""
    n = len(dxy)
    if n < 8:
        return 0.0
    freq = np.fft.rfftfreq(n, d=1.0 / fps)
    anteile = []
    for c in range(dxy.shape[1]):
        x = dxy[:, c] - dxy[:, c].mean()
        p = np.abs(np.fft.rfft(x)) ** 2
        gesamt = float(p[1:].sum())
        if gesamt > 0:
            anteile.append(float(p[freq >= grenze_hz].sum()) / gesamt)
    return float(np.mean(anteile)) if anteile else 0.0


def schwellen_px(kb_mm: float | None, cfg: dict) -> tuple[float, float]:
    """(min_px für Schwenk/Tilt, stativ_px): aus °/s über f_px, wenn die KB-Brennweite bekannt ist, sonst px-Standardwerte."""
    if kb_mm:
        k = math.pi / 180.0 * f_px(kb_mm, int(cfg["optisch_breite"])) / ZIEL_FPS
        return float(cfg["schwenk_min_grad_s"]) * k, float(cfg["stativ_max_grad_s"]) * k
    return float(cfg["schwenk_min_px"]), float(cfg["stativ_max_px"])


def _tiefpass(x: np.ndarray, breite: int) -> np.ndarray:
    """Gleitendes Mittel über ``breite`` Frames je Spalte, Ränder auf die vorhandenen Werte normiert."""
    if breite <= 1 or len(x) == 0:
        return x.astype(np.float64)
    k = np.ones(breite) / breite
    norm = np.convolve(np.ones(len(x)), k, mode="same")
    return np.stack([np.convolve(x[:, c], k, mode="same") / norm for c in range(x.shape[1])], axis=1)


def bewegungsart(dxy: np.ndarray, cfg: dict, min_px: float, stativ_px: float) -> str:
    """Bewegungsart eines Fensters: statisch, Schwenk/Tilt mit Richtung, gemischt (Richtungswechsel oder beide Achsen), fahrt."""
    if len(dxy) == 0:
        return "statisch"
    wk, bw = wackeln_bewegung(dxy)
    if wk < stativ_px and bw < stativ_px:
        return "statisch"
    glatt = _tiefpass(dxy, int(round(float(cfg["tiefpass_s"]) * ZIEL_FPS)))
    h = len(glatt) // 2
    if h >= 2:
        for c in (0, 1):
            a, b = float(glatt[:h, c].mean()), float(glatt[h:, c].mean())
            if abs(a) >= min_px and abs(b) >= min_px and a * b < 0:
                return "gemischt"
    mx, my = float(glatt[:, 0].mean()), float(glatt[:, 1].mean())
    ax, ay = abs(mx), abs(my)
    if ax >= min_px and ax >= 1.5 * ay:
        return "schwenk_links" if mx > 0 else "schwenk_rechts"
    if ay >= min_px and ay >= 1.5 * ax:
        return "tilt_auf" if my > 0 else "tilt_ab"
    if ax >= min_px and ay >= min_px:
        return "gemischt"
    return "fahrt"


def haltung(dxy: np.ndarray, stativ_px: float, cfg: dict) -> str:
    """stativ (keine Bewegung), hand (viel Energie über hf_grenze_hz) oder gimbal (Bewegung fast nur darunter)."""
    wk, bw = wackeln_bewegung(dxy)
    if wk < stativ_px and bw < stativ_px:
        return "stativ"
    anteil = hf_anteil(dxy, ZIEL_FPS, float(cfg["hf_grenze_hz"]))
    return "hand" if anteil >= float(cfg["hand_hf_anteil_min"]) else "gimbal"


def fenster(dxy: np.ndarray, cfg: dict, min_px: float, stativ_px: float) -> list[dict]:
    """Fenster von ``fenster_s`` mit Schritt ``schritt_s``; das letzte darf halb so lang sein; kurze Clips: ein Fenster (ab 2 Frames)."""
    n = len(dxy)
    w = max(2, int(round(float(cfg["fenster_s"]) * ZIEL_FPS)))
    s = max(1, int(round(float(cfg["schritt_s"]) * ZIEL_FPS)))
    # erstes Fenster immer (ab 2 Frames), weitere nur, wenn noch mindestens ein halbes Fenster übrig ist
    starts = [st for st in range(0, n, s) if st == 0 or n - st >= w // 2] if n >= 2 else []
    out = []
    for st in starts:
        teil = dxy[st:st + w]
        wk, bw = wackeln_bewegung(teil)
        out.append({"t_s": round(st / ZIEL_FPS, 1), "wackeln": round(wk, 3), "bewegung": round(bw, 3),
                    "bewegungsart": bewegungsart(teil, cfg, min_px, stativ_px)})
    return out


def mehrheit(werte: list[str], anteil: float = 0.6) -> str:
    """Häufigster Wert, wenn er mindestens ``anteil`` der Fenster stellt, sonst „gemischt"."""
    if not werte:
        return "gemischt"
    wert, n = Counter(werte).most_common(1)[0]
    return wert if n / len(werte) >= anteil else "gemischt"


def lage(acc: np.ndarray, toleranz: float = 0.10, vorzeichen_pitch: float = 1.0) -> dict:
    """Pitch (< 0: Kamera schaut nach unten) und Roll aus dem Median-Schwerkraftvektor der ruhigen Proben
    (|a| innerhalb ±toleranz um den Clip-Median — FX3 misst konstant 1,15 g, daher relativ, nie absolut)."""
    if len(acc) == 0:
        return {"pitch_grad": None, "roll_grad": None, "grund": "keine Beschleunigungsdaten"}
    betrag = np.linalg.norm(acc, axis=1)
    med = float(np.median(betrag))
    if med <= 0:
        return {"pitch_grad": None, "roll_grad": None, "grund": "Beschleunigung null"}
    ruhig = np.abs(betrag - med) <= toleranz * med
    if float(ruhig.mean()) < 0.5:
        return {"pitch_grad": None, "roll_grad": None,
                "grund": f"Beschleunigung schwankt ({100 * (1 - float(ruhig.mean())):.0f} % der Proben außerhalb ±{toleranz * 100:.0f} %)"}
    a = np.median(acc[ruhig], axis=0)          # x links, y oben, z vorwärts
    pitch = vorzeichen_pitch * math.degrees(math.atan2(a[2], math.hypot(a[0], a[1])))
    roll = math.degrees(math.atan2(a[0], a[1]))
    return {"pitch_grad": round(pitch + 0.0, 1), "roll_grad": round(roll + 0.0, 1), "grund": None}


def brennweitenklasse(kb_mm: float, grenzen: list | tuple) -> str:
    """weit unter grenzen[0], tele über grenzen[1], dazwischen normal (Grenzen zählen zu normal)."""
    if kb_mm < grenzen[0]:
        return "weit"
    if kb_mm > grenzen[1]:
        return "tele"
    return "normal"


def perspektive_hoehe(pitch_grad: float | None, grenzen: list | tuple) -> str | None:
    """Vogelperspektive ≤ grenzen[0], Aufsicht ≤ grenzen[1], Untersicht ≥ grenzen[2], sonst Augenhöhe; None ohne Pitch."""
    if pitch_grad is None:
        return None
    if pitch_grad <= grenzen[0]:
        return "Vogelperspektive"
    if pitch_grad <= grenzen[1]:
        return "Aufsicht"
    if pitch_grad >= grenzen[2]:
        return "Untersicht"
    return "Augenhöhe"


def kennzahlen(dxy: np.ndarray, cfg: dict, kb_mm: float | None) -> dict:
    """wackeln, bewegung, haltung, bewegungsart (Mehrheit der Fenster), fenster, ruhige_fenster aus einer Verschiebungsreihe."""
    min_px, stativ_px = schwellen_px(kb_mm, cfg)
    wk, bw = wackeln_bewegung(dxy)
    fen = fenster(dxy, cfg, min_px, stativ_px)
    return {"wackeln": round(wk, 3), "bewegung": round(bw, 3), "haltung": haltung(dxy, stativ_px, cfg),
            "hf_anteil": round(hf_anteil(dxy, ZIEL_FPS, float(cfg["hf_grenze_hz"])), 3),
            "bewegungsart": mehrheit([f["bewegungsart"] for f in fen]),
            "fenster": [[f["t_s"], f["wackeln"], f["bewegung"], f["bewegungsart"]] for f in fen],
            "ruhige_fenster": [f["t_s"] for f in fen if f["wackeln"] <= float(cfg["ruhig_max_px"])]}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_telemetrie.py -q`
Expected: `19 passed` (7 parametrisierte Fälle + 12 Tests). Sollte `test_bewegungsart_fahrt_ohne_dominante_richtung` mit einem anderen Zufallswert „gemischt" liefern, den Seed beibehalten (0) — er ist Teil des Tests.

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/tests/test_telemetrie.py && git commit -q -m "feat(autocut): telemetrie.py — Kennzahlen (Umrechnung Gyro → px, wackeln/bewegung, Fenster, Haltung, Bewegungsart, Lage, Klassen)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: `telemetrie.py` (Teil 2) — Clip-Messung, Cache, Clip-Quellen, Charge-Lauf, 2b/6d-Helfer, `defaults.yaml`

**Files:**
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (anhängen)
- Modify: `tools/autocut/defaults.yaml` (Block `telemetrie:` **am Dateiende nach `replay:` anhängen** — das MacBook hat unkommittierte Änderungen vor `path_map:` (`proxy_pflicht`, Tagesstand 19.09.); Anhängen vermeidet den Konflikt)
- Test: `tools/autocut/tests/test_telemetrie.py` (anhängen)

**Interfaces:**
- Consumes: Task 1 (`datenspur_lesen`, `samples`, `auswerten`, `sidecar_modell`, `kamera_erkennen`), Task 2 (`graustufen`, `verschiebungen`), Task 3, `media.ffprobe`/`media.fingerprint`, `Charge.open_basis` (`ch.autocut`, `ch.intern`, `ch.assert_writable`, `ch.write_json`, `ch.read_json`, `ch.load_index`, `ch.config`)
- Produces:
  - `clip_messen(path, cfg, ohne_optisch=False) -> dict` (Datensatz nach Spec-Datenmodell)
  - `clip_mit_cache(ch, path, cfg, force=False, ohne_optisch=False) -> tuple[dict, bool]` (Datensatz, Cache-Treffer)
  - `clips_finden(ch, ordner=None) -> list[dict]` (`{"path", "ordner"}`)
  - `telemetrie_charge(ch, clips, cfg, limit=None, force=False, ohne_optisch=False, parallel=None, melden=print) -> dict` (`clips`, `fehler`, `cache_treffer`, `gemessen`); schreibt `telemetrie.json` (Liste)
  - `laden(autocut_dir) -> list[dict]`, `finden(tele, path) -> dict | None`
  - `abschnitt_werte(rec, von_s, bis_s, fenster_s=2.0) -> dict` (`bewegungsart`, `haltung`)
  - `stabil_vorschlag(von_s, bis_s, rec, cfg) -> tuple[bool, str]`

- [ ] **Step 1: Failing Tests anhängen**

```python
# tools/autocut/tests/test_telemetrie.py — anhängen
import json
import shutil
import struct
import subprocess
from pathlib import Path

from niro_autocut import rtmd as R
from niro_autocut.charge import Charge, load_config
from niro_autocut.media import MediaInfo


def _info(path: str, fps: float = 25.0, dauer: float = 4.0) -> MediaInfo:
    return MediaInfo(path=path, duration_s=dauer, fps=fps, width=3840, height=2160, rotation=0, nb_frames=int(dauer * fps),
                     timecode=None, has_audio=True, sample_rate=48000, channels=2)


def _rtmd_puffer(frames: int = 100, proben: int = 80, gyro_y: float = 0.0, acc=(0.0, 1.15, 0.0), kb: bytes = bytes.fromhex("c2cc")) -> bytes:
    """Synthetische Datenspur: je Frame ein Sample mit konstantem Gyro (°/s um y) und Schwerkraftvektor."""
    def imu(v):
        out = struct.pack(">II", proben, 6)
        for _ in range(proben):
            out += struct.pack(">hhh", *v)
        return out
    g = imu((0, int(round(gyro_y * 65.5)), 0))
    a = imu(tuple(int(round(x * 8192)) for x in acc))
    tags = {R.TAG_GYRO: g, R.TAG_GYRO_SKALA: struct.pack(">f", 65.5), R.TAG_ACC: a, R.TAG_ACC_SKALA: struct.pack(">f", 8192.0),
            R.TAG_IMU_HZ: struct.pack(">I", 2000), R.TAG_KB_MM: kb, R.TAG_BRENNWEITE_MM: bytes.fromhex("c2a5"),
            R.TAG_FOKUS_M: bytes.fromhex("e62e")}
    return R.paket_bauen(tags) * frames


def test_defaults_haben_telemetrie_block():
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    for k in ("fenster_s", "ruhig_max_px", "achsen", "vorzeichen", "px_faktor", "optisch_fuer", "optisch_breite", "parallel"):
        assert k in cfg


def test_clip_messen_rtmd_weg(monkeypatch, tmp_path):
    clip = tmp_path / "FX3_0001.MP4"
    clip.write_bytes(b"x")
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: _rtmd_puffer(frames=100, gyro_y=10.0))
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "rtmd" and rec["kamera"] == "FX3" and rec["imu_hz"] == 2000.0 and rec["samples"] == 100
    assert rec["kb_mm"] == 71.6 and rec["brennweite_mm"] == 67.7 and rec["fokus_m"] == 15.82 and rec["zoomfahrt"] is False
    assert rec["brennweitenklasse"] == "tele" and rec["pitch_grad"] == 0.0 and rec["perspektive_hoehe"] == "Augenhöhe"
    assert rec["bewegungsart"] == "schwenk_rechts"          # Gyro-y +10 °/s → dx negativ (vorzeichen −1) → Inhalt nach links
    assert rec["haltung"] == "gimbal" and rec["wackeln"] == 0.0 and rec["bewegung"] > 3        # 10 °/s bei 71,6 mm KB ≈ 6,7 px dx, Mittel über dx/dy ≈ 3,3
    assert len(rec["fenster"]) == 4 and rec["ruhige_fenster"] == [0.0, 1.0, 2.0, 3.0] and rec["fehler"] is None


def test_clip_messen_faellt_ohne_datenspur_auf_optisch(monkeypatch, tmp_path):
    clip = tmp_path / "DJI_0504.MOV"
    clip.write_bytes(b"x")
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: b"")
    monkeypatch.setattr(T, "graustufen", lambda p, fps, breite, hoehe: np.zeros((30, hoehe, breite), np.uint8))
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "optisch" and rec["kamera"] == "DJI" and rec["kb_mm"] is None and rec["haltung"] == "stativ"
    ohne = T.clip_messen(clip, CFG, ohne_optisch=True)
    assert ohne["quelle"] == "keine" and ohne["fenster"] == []


def test_clip_messen_optisch_fuer_kamera_behaelt_brennweite(monkeypatch, tmp_path):
    clip = tmp_path / "a7MK4_1.MP4"
    clip.write_bytes(b"x")
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p), fps=50.0))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: _rtmd_puffer(frames=200, proben=40, gyro_y=10.0))
    monkeypatch.setattr(T, "graustufen", lambda p, fps, breite, hoehe: np.zeros((30, hoehe, breite), np.uint8))
    rec = T.clip_messen(clip, {**CFG, "optisch_fuer": ["a7IV"]})
    assert rec["quelle"] == "optisch" and rec["kb_mm"] == 71.6 and rec["brennweitenklasse"] == "tele" and rec["haltung"] == "stativ"


def test_clip_messen_fehler_wird_datensatz(monkeypatch, tmp_path):
    clip = tmp_path / "FX3_0002.MP4"
    clip.write_bytes(b"x")
    monkeypatch.setattr(T, "ffprobe", lambda p: (_ for _ in ()).throw(T.AutoCutError("ffprobe kaputt")))
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "keine" and "ffprobe kaputt" in rec["fehler"] and rec["clip"] == "FX3_0002"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")
def test_telemetrie_charge_mit_inventar_und_cache(basis_charge, tmp_path):
    clip = tmp_path / "nas" / "DJI_0001.mp4"
    clip.parent.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:duration=3",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    (ac / "inventar.json").write_text(json.dumps([{"ordner": "Mavic", "name": clip.name, "path": str(clip)}]), encoding="utf-8")
    ch = Charge.open_basis(basis_charge)
    cfg = load_config(basis_charge)["telemetrie"]
    clips = T.clips_finden(ch)
    assert clips == [{"path": str(clip), "ordner": "Mavic"}]
    out = T.telemetrie_charge(ch, clips, cfg, melden=lambda *a, **k: None)
    assert out["gemessen"] == 1 and out["cache_treffer"] == 0 and out["fehler"] == []
    tele = T.laden(ac)
    assert len(tele) == 1 and tele[0]["quelle"] == "optisch" and tele[0]["clip"] == "DJI_0001" and tele[0]["fingerprint"]
    assert len(list((ac / "telemetrie").glob("*.json"))) == 1
    assert 0 <= tele[0]["wackeln"] < 5 and len(tele[0]["fenster"]) == 2                # testsrc: 3 s → Fenster bei 0 und 1 s
    again = T.telemetrie_charge(ch, clips, cfg, melden=lambda *a, **k: None)
    assert again["cache_treffer"] == 1 and again["gemessen"] == 0
    neu = T.telemetrie_charge(ch, clips, cfg, force=True, melden=lambda *a, **k: None)
    assert neu["gemessen"] == 1


def test_clips_finden_reihenfolge_und_ordner(basis_charge, tmp_path):
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    with pytest.raises(T.AutoCutError):
        T.clips_finden(ch)
    d = tmp_path / "B-Roll" / "Flur"
    d.mkdir(parents=True)
    (d / "FX3_0003.MP4").write_bytes(b"x")
    (d / "Proxy").mkdir()
    (d / "Proxy" / "FX3_0003.mov").write_bytes(b"x")
    (d / ".versteckt.mp4").write_bytes(b"x")
    assert T.clips_finden(ch, [str(tmp_path / "B-Roll")]) == [{"path": str(d / "FX3_0003.MP4"), "ordner": "Flur"}]
    (ac / "broll_index.json").write_text(json.dumps({"clips": [{"path": "/nas/x/FX3_9.MP4", "ordner": "Allgemein"}]}), encoding="utf-8")
    (ac / "inventar.json").write_text(json.dumps([{"path": "/nas/y/FX3_1.MP4", "ordner": "FX3"}]), encoding="utf-8")
    assert T.clips_finden(ch)[0]["path"] == "/nas/x/FX3_9.MP4"          # broll_index vor inventar
    (ac / "broll_index.json").unlink()
    assert T.clips_finden(ch)[0]["path"] == "/nas/y/FX3_1.MP4"


def test_finden_und_abschnitt_werte():
    tele = [{"path": "/nas/a/FX3_1.MP4", "clip": "FX3_1", "haltung": "hand",
             "fenster": [[0.0, 0.3, 1.0, "schwenk_links"], [1.0, 0.3, 1.0, "schwenk_links"], [2.0, 0.05, 0.1, "statisch"]]},
            {"path": "/nas/b/FX3_2.MP4", "clip": "FX3_2"}, {"path": "/nas/c/FX3_2.MP4", "clip": "FX3_2"}]
    assert T.finden(tele, "/nas/a/FX3_1.MP4")["clip"] == "FX3_1"
    assert T.finden(tele, "/ssd/a/FX3_1.MP4")["clip"] == "FX3_1"          # gleicher Dateiname, eindeutig
    assert T.finden(tele, "/ssd/FX3_2.MP4") is None                       # mehrdeutig
    assert T.finden(tele, "/nas/FX3_3.MP4") is None
    assert T.abschnitt_werte(tele[0], 0.0, 2.0) == {"bewegungsart": "schwenk_links", "haltung": "hand"}
    assert T.abschnitt_werte(tele[0], 2.5, 4.0) == {"bewegungsart": "statisch", "haltung": "hand"}
    assert T.abschnitt_werte(tele[1], 0.0, 1.0) == {"bewegungsart": None, "haltung": None}


@pytest.mark.parametrize("rec,von,bis,erwartet,grund", [
    (None, 0, 2, True, "keine Telemetrie"),
    ({"quelle": "keine", "fehler": None}, 0, 2, True, "keine Telemetrie"),
    ({"quelle": "rtmd", "fehler": None, "haltung": "stativ", "wackeln": 0.0, "fenster": [[0.0, 0.0, 0.0, "statisch"]]}, 0, 2, False, "Stativ"),
    ({"quelle": "rtmd", "fehler": None, "haltung": "gimbal", "wackeln": 0.05, "fenster": [[0.0, 0.05, 1.0, "fahrt"]]}, 0, 2, False, "Gimbal"),
    ({"quelle": "rtmd", "fehler": None, "haltung": "hand", "wackeln": 0.4, "fenster": [[0.0, 0.4, 1.0, "fahrt"], [1.0, 0.1, 1.0, "fahrt"]]}, 0.0, 1.0, True, "Hand, wackeln 0,40"),
    ({"quelle": "rtmd", "fehler": None, "haltung": "hand", "wackeln": 0.4, "fenster": [[0.0, 0.4, 1.0, "fahrt"], [1.0, 0.1, 1.0, "fahrt"]]}, 2.5, 3.0, False, "Hand, aber ruhig"),
])
def test_stabil_vorschlag(rec, von, bis, erwartet, grund):
    stabil, text = T.stabil_vorschlag(von, bis, rec, CFG)
    assert stabil is erwartet and grund in text
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_telemetrie.py -q`
Expected: die neuen Tests scheitern mit `AttributeError: module 'niro_autocut.telemetrie' has no attribute 'clip_messen'` bzw. `KeyError: 'telemetrie'` beim Defaults-Test.

- [ ] **Step 3: `defaults.yaml` — Block am Dateiende anhängen (nach `replay:`)**

```yaml
telemetrie:                 # Kamera-Telemetrie je Clip (Spec 2026-09-19): Gyro/Beschleunigung/Brennweite aus der Sony-rtmd-Spur,
                            # optischer Rückfall (Phasenkorrelation) für Clips ohne Datenspur. Beide Wege: px @480 je 25-fps-Frame.
  fenster_s: 2.0            # Fensterlänge für ruhige Fenster und Bewegungsart
  schritt_s: 1.0
  tiefpass_s: 0.5           # gleitendes Mittel vor der Richtungsentscheidung
  ruhig_max_px: 0.15        # Fenster gilt als ruhig (Startwert = optische Faustregel 18.09.: ruhige Handkamera 0,05–0,15)
  stativ_max_grad_s: 0.3    # darunter Stativ/statisch (Gyro-Weg; über f_px in px je Frame umgerechnet)
  stativ_max_px: 0.02       # … optischer Weg ohne Brennweite
  schwenk_min_grad_s: 3.0   # dominante Drehung ab hier Schwenk/Tilt
  schwenk_min_px: 1.0
  hf_grenze_hz: 3.0         # Grenze zwischen Gimbal-/Fahrt-Bewegung und Hand-Zittern
  hand_hf_anteil_min: 0.35  # Leistungsanteil ab hf_grenze_hz, ab dem „hand" statt „gimbal" (Kalibrierung: Hochzeitszauber, MEK)
  brennweite_klassen_kb: [30, 60]    # KB-Brennweite: < 30 weit, > 60 tele, sonst normal
  pitch_klassen_grad: [-60, -8, 8]   # Pitch: ≤ −60 Vogelperspektive, ≤ −8 Aufsicht, ≥ 8 Untersicht, sonst Augenhöhe
  achsen: {schwenk: 1, tilt: 0}                    # Gyro-Spalten (x links, y oben, z vorwärts): Schwenk um y, Tilt um x
  vorzeichen: {schwenk: -1, tilt: 1, pitch: 1}     # Kalibrierung; Stichprobe 21.09.: Gyro-y ↔ dx negativ (Inhalt wandert entgegen)
  px_faktor: {FX3: 1.0, a7IV: 1.0}                 # IBIS-Dämpfung je Kamera (Kalibrierung: Gyro-px ↔ optisch-px)
  optisch_fuer: []          # Kameras, deren Gyro-Wert nicht belastbar ist (Rangkorrelation < 0,7) → optischer Weg
  optisch_breite: 480       # Bildbreite der Messung (Höhe 9:16-passend 270)
  parallel: 2               # Clips gleichzeitig (Lesen der ganzen Datei ≈ 300 MB/s übers NAS)
```

- [ ] **Step 4: Modul-Teil 2 anhängen**

```python
# tools/autocut/src/niro_autocut/telemetrie.py — anhängen

# --- Clip-Messung ---------------------------------------------------------------------------------------------------------

def _leer(path: Path, kamera: str, modell: str | None) -> dict:
    return {"path": str(path), "clip": path.stem, "kamera": kamera, "modell": modell, "dauer_s": None, "fps": None,
            "quelle": "keine", "imu_hz": None, "samples": 0, "brennweite_mm": None, "kb_mm": None, "kb_min": None,
            "kb_max": None, "zoomfahrt": False, "fokus_m": None, "brennweitenklasse": None, "pitch_grad": None,
            "roll_grad": None, "lage_grund": None, "perspektive_hoehe": None, "haltung": None, "hf_anteil": None,
            "bewegungsart": None, "wackeln": None, "bewegung": None, "fenster": [], "ruhige_fenster": [], "fehler": None}


def clip_messen(path: str | Path, cfg: dict, ohne_optisch: bool = False) -> dict:
    """Ein Clip: rtmd-Weg (Gyro über KB-Brennweite in px), sonst optischer Weg, sonst ``quelle: keine``; Fehler im Datensatz."""
    p = Path(path)
    modell = sidecar_modell(p)
    kamera = kamera_erkennen(p, modell)
    out = _leer(p, kamera, modell)
    try:
        info = ffprobe(p)
        out["dauer_s"], out["fps"] = round(float(info.duration_s), 2), float(info.fps)
        daten = None
        buf = datenspur_lesen(p)
        if buf:
            daten = auswerten(samples(buf))
        kb = None
        if daten is not None:
            out["samples"] = daten.samples
            if daten.kb_mm:
                kb = float(np.median(daten.kb_mm))
                out["kb_mm"], out["kb_min"], out["kb_max"] = round(kb, 1), round(min(daten.kb_mm), 1), round(max(daten.kb_mm), 1)
                out["zoomfahrt"] = bool(out["kb_max"] / max(out["kb_min"], 0.1) > 1.3)
                out["brennweitenklasse"] = brennweitenklasse(kb, cfg["brennweite_klassen_kb"])
            if daten.brennweite_mm:
                out["brennweite_mm"] = round(float(np.median(daten.brennweite_mm)), 1)
            if daten.fokus_m:
                out["fokus_m"] = round(float(np.median(daten.fokus_m)), 2)
            if len(daten.acc):
                l = lage(daten.acc, vorzeichen_pitch=float(cfg["vorzeichen"].get("pitch", 1)))
                out["pitch_grad"], out["roll_grad"], out["lage_grund"] = l["pitch_grad"], l["roll_grad"], l["grund"]
                out["perspektive_hoehe"] = perspektive_hoehe(l["pitch_grad"], cfg["pitch_klassen_grad"])
        gyro_ok = (daten is not None and len(daten.gyro) > 0 and daten.proben_je_sample > 0 and kb is not None
                   and kamera not in (cfg.get("optisch_fuer") or []))
        if gyro_ok:
            out["imu_hz"] = float(daten.imu_hz or daten.proben_je_sample * info.fps)
            rate = gyro_je_frame(daten.gyro, daten.proben_je_sample, info.fps)
            faktor = float((cfg.get("px_faktor") or {}).get(kamera, 1.0))
            dxy = verschiebung_aus_rate(rate, kb, cfg) * faktor
            out.update(quelle="rtmd", **kennzahlen(dxy, cfg, kb))
        elif not ohne_optisch:
            breite = int(cfg["optisch_breite"])
            frames = graustufen(p, ZIEL_FPS, breite=breite, hoehe=int(round(breite * 9 / 16)))
            out.update(quelle="optisch", **kennzahlen(verschiebungen(frames), cfg, kb))
    except AutoCutError as e:
        out["fehler"] = str(e)
    return out


def clip_mit_cache(ch, path: str | Path, cfg: dict, force: bool = False, ohne_optisch: bool = False) -> tuple[dict, bool]:
    """Datensatz aus ``_intern/autocut/telemetrie/<fingerprint>.json`` oder neu messen (atomar geschrieben)."""
    fp = fingerprint(path)
    cache = Path(ch.autocut) / CACHE_DIR / f"{fp}.json"
    if cache.exists() and not force:
        rec = json.loads(cache.read_text(encoding="utf-8"))
        if rec.get("quelle") != "keine" or ohne_optisch:
            return rec, True
    rec = clip_messen(path, cfg, ohne_optisch)
    rec["fingerprint"] = fp
    rec["gemessen_am"] = _dt.datetime.now().isoformat(timespec="seconds")
    ch.assert_writable(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    part = cache.with_name(cache.name + ".part")
    part.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(part, cache)
    return rec, False


# --- Clip-Quellen und Charge-Lauf ------------------------------------------------------------------------------------------

def _videos(root: Path) -> list[dict]:
    """Videodateien unter ``root`` (rekursiv, ohne Proxy-Ordner und versteckte Dateien); ``ordner`` relativ zur Wurzel."""
    out = []
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in VIDEO_EXTS or f.name.startswith("."):
            continue
        if any(part == "Proxy" or part.startswith(".") for part in f.relative_to(root).parts[:-1]):
            continue
        out.append({"path": str(f), "ordner": "/".join(f.relative_to(root).parts[:-1])})
    return out


def clips_finden(ch, ordner: list[str] | None = None) -> list[dict]:
    """Clip-Liste: --ordner → broll_index.json → inventar.json → B-Roll-Wurzeln des Transkript-Index → media.json."""
    if ordner:
        clips = []
        for o in ordner:
            root = Path(o).expanduser()
            if not root.is_dir():
                raise AutoCutError(f"Ordner nicht gefunden: {root}\nIst das NAS gemountet?")
            clips += _videos(root)
        return clips
    ac = Path(ch.autocut)
    index = ch.read_json("broll_index.json")
    if index and index.get("clips"):
        return [{"path": str(c["path"]), "ordner": c.get("ordner") or ""} for c in index["clips"]]
    inventar = ch.read_json("inventar.json")
    if inventar:
        return [{"path": str(c["path"]), "ordner": c.get("ordner") or ""} for c in inventar]
    if (Path(ch.intern) / "transcripts_index.json").exists():
        from .broll_index import discover_broll
        clips = discover_broll(ch.load_index())
        if clips:
            return [{"path": c["path"], "ordner": c.get("ordner") or ""} for c in clips]
    media = ch.read_json("media.json")
    if media and media.get("clips"):
        return [{"path": p, "ordner": Path(p).parent.name} for p in media["clips"]]
    raise AutoCutError(f"Keine Clips gefunden: weder --ordner noch broll_index.json, inventar.json, Transkript-Index oder "
                       f"media.json unter {ac}.")


def telemetrie_charge(ch, clips: list[dict], cfg: dict, limit: int | None = None, force: bool = False,
                      ohne_optisch: bool = False, parallel: int | None = None, melden=print) -> dict:
    """Alle Clips messen (Cache je Clip, parallel), ``telemetrie.json`` (Liste) schreiben; Fehler je Clip sammeln."""
    todo = clips[:limit] if limit else clips
    fehlend = [c["path"] for c in todo if not Path(c["path"]).is_file()]
    if todo and len(fehlend) == len(todo):
        raise AutoCutError(f"Keine der {len(todo)} Dateien erreichbar (z. B. {fehlend[0]}) — ist das NAS gemountet?")
    ergebnisse: dict[str, dict] = {}
    fehler: list[str] = []
    treffer = gemessen = 0
    ex = ThreadPoolExecutor(max_workers=max(1, int(parallel or cfg.get("parallel", 2))))
    try:
        futs = {ex.submit(clip_mit_cache, ch, c["path"], cfg, force, ohne_optisch): c for c in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            c = futs[fut]
            name = Path(c["path"]).name
            try:
                rec, aus_cache = fut.result()
            except AutoCutError as e:
                fehler.append(f"{name}: {e}")
                melden(f"[{i}/{len(todo)}] FEHLER {name}: {e}", flush=True)
                continue
            rec["ordner"] = c.get("ordner") or ""
            if rec.get("fehler"):
                fehler.append(f"{name}: {rec['fehler']}")
            treffer += int(aus_cache)
            gemessen += int(not aus_cache)
            ergebnisse[c["path"]] = rec
            melden(f"[{i}/{len(todo)}] {'Cache' if aus_cache else rec['quelle']:<7} {name}: {rec.get('haltung') or '-'} / "
                   f"{rec.get('bewegungsart') or '-'} / wackeln {rec['wackeln'] if rec.get('wackeln') is not None else '-'}", flush=True)
    except KeyboardInterrupt:
        ex.shutdown(wait=False, cancel_futures=True)
        raise
    ex.shutdown(wait=True)
    liste = [ergebnisse[c["path"]] for c in todo if c["path"] in ergebnisse]
    ch.write_json("telemetrie.json", liste)
    return {"clips": liste, "fehler": fehler, "cache_treffer": treffer, "gemessen": gemessen}


def laden(autocut_dir: str | Path) -> list[dict]:
    """``telemetrie.json`` als Liste; leer, wenn es sie nicht gibt."""
    p = Path(autocut_dir) / "telemetrie.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else list(data.get("clips") or [])


def finden(tele: list[dict], path: str | Path) -> dict | None:
    """Datensatz zum Pfad: exakt, sonst über den Dateinamen (nur wenn eindeutig — Material kann NAS → SSD gewandert sein)."""
    s = str(path)
    for r in tele:
        if r.get("path") == s:
            return r
    name = Path(s).name
    treffer = [r for r in tele if Path(str(r.get("path", ""))).name == name]
    return treffer[0] if len(treffer) == 1 else None


# --- Helfer für Stufe 2b und 6d ---------------------------------------------------------------------------------------------

def _fenster_im_bereich(rec: dict, von_s: float, bis_s: float, fenster_s: float) -> list[list]:
    """Fenster, deren Mitte im Bereich liegt; gibt es keine (Bereich kürzer als ein Fenster), alle überlappenden."""
    alle = rec.get("fenster") or []
    mitte = [f for f in alle if von_s <= f[0] + fenster_s / 2 <= bis_s]
    return mitte or [f for f in alle if f[0] < bis_s and f[0] + fenster_s > von_s]


def abschnitt_werte(rec: dict | None, von_s: float, bis_s: float, fenster_s: float = 2.0) -> dict:
    """``bewegungsart`` (Mehrheit der Fenster im Bereich) und ``haltung`` des Clips für einen Abschnitt; None ohne Daten."""
    if not rec or not rec.get("fenster"):
        return {"bewegungsart": None, "haltung": (rec or {}).get("haltung")}
    fen = _fenster_im_bereich(rec, von_s, bis_s, fenster_s)
    return {"bewegungsart": mehrheit([f[3] for f in fen]) if fen else None, "haltung": rec.get("haltung")}


def stabil_vorschlag(von_s: float, bis_s: float, rec: dict | None, cfg: dict) -> tuple[bool, str]:
    """6d: stabilisieren? hand mit wackeln > ruhig_max_px → ja; stativ/gimbal → nein; ohne Telemetrie → ja (bisheriger Standard).
    ``wackeln`` = Mittel der Fenster im genutzten Quellbereich, sonst der Clip-Wert."""
    if not rec or rec.get("quelle") in (None, "keine") or rec.get("fehler"):
        return True, "keine Telemetrie → Standard stabilisieren"
    fen = _fenster_im_bereich(rec, von_s, bis_s, float(cfg["fenster_s"]))
    wk = float(np.mean([f[1] for f in fen])) if fen else float(rec.get("wackeln") or 0.0)
    grenze = float(cfg["ruhig_max_px"])
    h = rec.get("haltung")
    if h == "stativ":
        return False, f"Stativ (wackeln {wk:.2f} px)".replace(".", ",")
    if h == "gimbal":
        return False, f"Gimbal (wackeln {wk:.2f} px)".replace(".", ",")
    if wk > grenze:
        return True, f"Hand, wackeln {wk:.2f} px > {grenze:.2f}".replace(".", ",")
    return False, f"Hand, aber ruhig (wackeln {wk:.2f} px ≤ {grenze:.2f})".replace(".", ",")
```

- [ ] **Step 5: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_telemetrie.py -q`
Expected: alle bestehen (Teil 1 + 14 neue inkl. 6 parametrisierte). Hinweis zu `test_clip_messen_rtmd_weg`: 10 °/s bei 71,6 mm KB ergeben ≈ 6,7 px dx je Frame, `bewegung` mittelt über dx und dy (≈ 3,3); `haltung == "gimbal"`, weil eine konstante Rate keine Energie über 3 Hz hat.

- [ ] **Step 6: Gesamte Test-Suite**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q`
Expected: alles grün (auch die bestehenden Tests mit ffmpeg 9 — schlägt hier etwas fehl, das nichts mit Telemetrie zu tun hat, den Befund im Protokoll der Session festhalten und in der Task-Meldung nennen, nicht still reparieren).

- [ ] **Step 7: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/tests/test_telemetrie.py tools/autocut/defaults.yaml && git commit -q -m "feat(autocut): Telemetrie je Clip messen (rtmd/optisch), Cache, Clip-Quellen, Charge-Lauf, Abschnittswerte, Stabilisierungs-Vorschlag; defaults.yaml telemetrie:

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Bericht `telemetrie_bericht.py`, CLI `autocut_telemetrie.py`, Grund-Doku

**Files:**
- Create: `tools/autocut/src/niro_autocut/telemetrie_bericht.py`
- Create: `tools/autocut/scripts/autocut_telemetrie.py`
- Modify: `tools/autocut/README.md` (Stufen-Tabelle, Schnellstart, Aufbau, Arbeitsdateien), `tools/autocut/WORKFLOW-AutoCut.md` (neuer Abschnitt „Telemetrie" vor „## Kantenprüfung"), `tools/autocut/tests/test_docs.py` (`SPEC_SCRIPTS` + `"autocut_telemetrie.py"`)
- Test: `tools/autocut/tests/test_telemetrie_bericht.py`, `tools/autocut/tests/test_telemetrie_script.py`

**Interfaces:**
- Consumes: Task 4 (`clips_finden`, `telemetrie_charge`, `laden`), `Charge.open_basis`, `append_protokoll`; Task 6 liefert später `telemetrie_kalibrierung.kalibrieren`/`tabelle` — die CLI ruft sie hinter `--kalibrieren` auf und importiert das Modul erst dort (bis Task 6 fertig ist, meldet `--kalibrieren` den fehlenden Import als `AutoCutError`)
- Produces:
  - `bericht_md(tele: list[dict], titel: str, index: dict | None = None) -> str`
  - `vergleich_index(tele: list[dict], index: dict) -> dict` (`brennweite`, `perspektive_hoehe`, `haltung`: je `{"n": int, "gleich": int, "kreuz": Counter[(gyro, claude)]}`)
  - CLI `main(argv) -> int` (0 ok, 1 Fehler/Clips mit Fehler, 130 Abbruch)

- [ ] **Step 1: Failing Tests schreiben**

```python
# tools/autocut/tests/test_telemetrie_bericht.py
"""telemetrie_bericht.py — Markdown-Bericht: Kopf, Verteilung je Kamera, unruhigste Clips, Fehler, Vergleich mit dem Index."""
from __future__ import annotations

from niro_autocut import telemetrie_bericht as B

TELE = [
    {"path": "/nas/FX3/FX3_1.MP4", "clip": "FX3_1", "kamera": "FX3", "ordner": "FX3", "quelle": "rtmd", "haltung": "gimbal",
     "bewegungsart": "fahrt", "brennweitenklasse": "normal", "perspektive_hoehe": "Augenhöhe", "wackeln": 0.04, "bewegung": 0.5,
     "ruhige_fenster": [0.0, 1.0], "fenster": [[0.0, 0.04, 0.5, "fahrt"], [1.0, 0.04, 0.5, "fahrt"]], "fehler": None, "roll_grad": 0.4},
    {"path": "/nas/A7/a7_1.MP4", "clip": "a7_1", "kamera": "a7IV", "ordner": "A7iv", "quelle": "rtmd", "haltung": "hand",
     "bewegungsart": "schwenk_links", "brennweitenklasse": "tele", "perspektive_hoehe": "Aufsicht", "wackeln": 0.41, "bewegung": 2.0,
     "ruhige_fenster": [], "fenster": [[0.0, 0.41, 2.0, "schwenk_links"]], "fehler": None, "roll_grad": 2.6},
    {"path": "/nas/Mavic/DJI_1.MOV", "clip": "DJI_1", "kamera": "DJI", "ordner": "Mavic", "quelle": "optisch", "haltung": "gimbal",
     "bewegungsart": "fahrt", "brennweitenklasse": None, "perspektive_hoehe": None, "wackeln": 0.02, "bewegung": 0.3,
     "ruhige_fenster": [0.0], "fenster": [[0.0, 0.02, 0.3, "fahrt"]], "fehler": None, "roll_grad": None},
    {"path": "/nas/FX3/FX3_2.MP4", "clip": "FX3_2", "kamera": "FX3", "ordner": "FX3", "quelle": "keine", "haltung": None,
     "bewegungsart": None, "brennweitenklasse": None, "perspektive_hoehe": None, "wackeln": None, "bewegung": None,
     "ruhige_fenster": [], "fenster": [], "fehler": "Datei nicht gefunden: /nas/FX3/FX3_2.MP4", "roll_grad": None},
]
INDEX = {"clips": [
    {"path": "/nas/FX3/FX3_1.MP4", "kamerabewegung": "Gimbal",
     "abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}]},
    {"path": "/nas/A7/a7_1.MP4", "kamerabewegung": "Handkamera",
     "abschnitte": [{"von_s": 0, "bis_s": 2, "brennweite": "normal", "perspektive_hoehe": "Aufsicht"},
                    {"von_s": 2, "bis_s": 4, "brennweite": "tele", "perspektive_hoehe": "Augenhöhe"}]},
    {"path": "/nas/Mavic/DJI_1.MOV", "kamerabewegung": "Drohne", "abschnitte": [{"von_s": 0, "bis_s": 3, "brennweite": "weit"}]},
]}


def test_bericht_kopf_verteilung_und_unruhigste():
    md = B.bericht_md(TELE, "Kunde A / Projekt B / 2026-09 Dreh")
    assert md.startswith("# Kamera-Telemetrie — Kunde A / Projekt B / 2026-09 Dreh")
    assert "4 Clips" in md and "rtmd 2" in md and "optisch 1" in md and "keine 1" in md and "Fehler 1" in md
    assert "| FX3 |" in md and "| a7IV |" in md and "| DJI |" in md
    assert "## Unruhigste Clips" in md and md.index("a7_1") < md.index("FX3_1")          # nach wackeln absteigend
    assert "0,41" in md and "schief 2,6°" in md
    assert "## Clips ohne Daten oder mit Fehler" in md and "FX3_2" in md and "Datei nicht gefunden" in md
    assert "## Vergleich" not in md


def test_vergleich_index_zaehlt_uebereinstimmung():
    v = B.vergleich_index(TELE, INDEX)
    assert v["brennweite"]["n"] == 3 and v["brennweite"]["gleich"] == 2                    # FX3 normal=normal, a7 A1 tele≠normal, A2 tele=tele
    assert v["perspektive_hoehe"]["n"] == 3 and v["perspektive_hoehe"]["gleich"] == 2
    assert v["haltung"]["n"] == 3 and v["haltung"]["kreuz"][("gimbal", "Gimbal")] == 1 and v["haltung"]["kreuz"][("hand", "Handkamera")] == 1
    md = B.bericht_md(TELE, "T", INDEX)
    assert "## Vergleich mit dem B-Roll-Index" in md and "Brennweite: 2 von 3" in md and "| gimbal | Gimbal | 1 |" in md


def test_bericht_ohne_clips():
    md = B.bericht_md([], "Leer")
    assert "0 Clips" in md and "## Unruhigste Clips" in md
```

```python
# tools/autocut/tests/test_telemetrie_script.py
"""autocut_telemetrie.py — CLI auf einer Fake-Charge: Lauf, Bericht, Protokoll, --dry-run, --ohne-optisch, Fehlerfälle."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

SKRIPT = Path(__file__).resolve().parents[1] / "scripts" / "autocut_telemetrie.py"


def _lade():
    spec = importlib.util.spec_from_file_location("autocut_telemetrie", SKRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _charge_mit_clip(basis_charge: Path, tmp_path: Path) -> Path:
    clip = tmp_path / "nas" / "Mavic" / "DJI_0001.mp4"
    clip.parent.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:duration=3",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    (ac / "inventar.json").write_text(json.dumps([{"ordner": "Mavic", "name": clip.name, "path": str(clip)}]), encoding="utf-8")
    return clip


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")
def test_lauf_schreibt_json_bericht_und_protokoll(basis_charge, tmp_path, capsys):
    _charge_mit_clip(basis_charge, tmp_path)
    skript = _lade()
    assert skript.main([str(basis_charge)]) == 0
    tele = json.loads((basis_charge / "_intern" / "autocut" / "telemetrie.json").read_text(encoding="utf-8"))
    assert len(tele) == 1 and tele[0]["quelle"] == "optisch"
    md = (basis_charge / "Ergebnisse" / "Rohschnitt" / "telemetrie.md").read_text(encoding="utf-8")
    assert md.startswith("# Kamera-Telemetrie") and "DJI_0001" in md
    assert "AutoCut: Telemetrie" in (basis_charge / "Protokoll.md").read_text(encoding="utf-8")
    out = capsys.readouterr().out
    assert "1 Clips" in out and "telemetrie.md" in out


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")
def test_dry_run_und_ohne_optisch(basis_charge, tmp_path):
    _charge_mit_clip(basis_charge, tmp_path)
    skript = _lade()
    assert skript.main([str(basis_charge), "--dry-run"]) == 0
    assert not (basis_charge / "_intern" / "autocut" / "telemetrie.json").exists()
    assert skript.main([str(basis_charge), "--ohne-optisch"]) == 0
    tele = json.loads((basis_charge / "_intern" / "autocut" / "telemetrie.json").read_text(encoding="utf-8"))
    assert tele[0]["quelle"] == "keine"


def test_fehler_ohne_charge_und_ohne_clips(basis_charge, tmp_path, capsys):
    skript = _lade()
    assert skript.main([str(tmp_path / "nirgendwo")]) == 1
    assert "FEHLER" in capsys.readouterr().err
    (basis_charge / "_intern" / "autocut").mkdir(parents=True)
    assert skript.main([str(basis_charge)]) == 1
    assert "Keine Clips" in capsys.readouterr().err
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_telemetrie_bericht.py tests/test_telemetrie_script.py -q`
Expected: ERROR `No module named 'niro_autocut.telemetrie_bericht'` bzw. `FileNotFoundError` für das Skript

- [ ] **Step 3: Bericht-Modul schreiben**

```python
# tools/autocut/src/niro_autocut/telemetrie_bericht.py
"""Bericht ``Ergebnisse/Rohschnitt/telemetrie.md``: Kopf, Verteilung je Kamera, unruhigste Clips, Clips ohne Daten,
optional Vergleich mit dem B-Roll-Index (Stufe 2b: Brennweite, Perspektive Höhe; Erst-Index: Kamerabewegung ↔ Haltung)."""
from __future__ import annotations

import datetime as _dt
from collections import Counter
from pathlib import Path

from .telemetrie import BEWEGUNGSARTEN, HALTUNGEN, finden

TOP = 25
SCHIEF_AB_GRAD = 2.0


def _de(x, stellen: int = 2) -> str:
    if x is None:
        return "–"
    return f"{x:.{stellen}f}".replace(".", ",")


def _md(s) -> str:
    return str(s if s is not None else "–").replace("|", "\\|")


def _verteilung(tele: list[dict]) -> list[str]:
    zeilen = ["| Kamera | Clips | Quelle rtmd/optisch/keine | Haltung " + "/".join(HALTUNGEN)
              + " | Bewegungsart " + "/".join(BEWEGUNGSARTEN) + " | Brennweite weit/normal/tele | Perspektive Augenhöhe/Aufsicht/Untersicht/Vogel |",
              "|---|---|---|---|---|---|---|"]
    for kam in sorted({r.get("kamera") or "unbekannt" for r in tele}):
        rs = [r for r in tele if (r.get("kamera") or "unbekannt") == kam]
        q = Counter(r.get("quelle") for r in rs)
        h = Counter(r.get("haltung") for r in rs)
        b = Counter(r.get("bewegungsart") for r in rs)
        f = Counter(r.get("brennweitenklasse") for r in rs)
        p = Counter(r.get("perspektive_hoehe") for r in rs)
        zeilen.append(f"| {kam} | {len(rs)} | {q['rtmd']}/{q['optisch']}/{q['keine']} | " + "/".join(str(h[x]) for x in HALTUNGEN)
                      + " | " + "/".join(str(b[x]) for x in BEWEGUNGSARTEN) + f" | {f['weit']}/{f['normal']}/{f['tele']} | "
                      f"{p['Augenhöhe']}/{p['Aufsicht']}/{p['Untersicht']}/{p['Vogelperspektive']} |")
    return zeilen


def _unruhigste(tele: list[dict]) -> list[str]:
    zeilen = ["| Clip | Kamera | Ordner | wackeln | bewegung | Haltung | Bewegungsart | ruhige Fenster (s) | Hinweis |",
              "|---|---|---|---|---|---|---|---|---|"]
    ok = [r for r in tele if r.get("wackeln") is not None]
    for r in sorted(ok, key=lambda r: -float(r["wackeln"]))[:TOP]:
        hinweis = []
        roll = r.get("roll_grad")
        if roll is not None and abs(float(roll)) > SCHIEF_AB_GRAD:
            hinweis.append(f"schief {_de(abs(float(roll)), 1)}°")
        if r.get("zoomfahrt"):
            hinweis.append("Zoomfahrt")
        ruhig = r.get("ruhige_fenster") or []
        zeilen.append(f"| {_md(r.get('clip'))} | {_md(r.get('kamera'))} | {_md(r.get('ordner'))} | {_de(r['wackeln'])} | "
                      f"{_de(r.get('bewegung'))} | {_md(r.get('haltung'))} | {_md(r.get('bewegungsart'))} | "
                      f"{', '.join(f'{t:g}' for t in ruhig[:12]) + (' …' if len(ruhig) > 12 else '') or '–'} | {', '.join(hinweis) or '–'} |")
    return zeilen


def vergleich_index(tele: list[dict], index: dict) -> dict:
    """Übereinstimmung Telemetrie ↔ Claude: je Abschnitt Brennweite und Perspektive Höhe (Stufe 2b), je Clip Haltung ↔ Kamerabewegung."""
    out = {k: {"n": 0, "gleich": 0, "kreuz": Counter()} for k in ("brennweite", "perspektive_hoehe", "haltung")}
    for c in index.get("clips") or []:
        r = finden(tele, str(c.get("path", "")))
        if not r or r.get("quelle") in (None, "keine"):
            continue
        if r.get("haltung") and c.get("kamerabewegung"):
            v = out["haltung"]
            v["n"] += 1
            v["kreuz"][(r["haltung"], c["kamerabewegung"])] += 1
            v["gleich"] += int((r["haltung"], c["kamerabewegung"]) in {("hand", "Handkamera"), ("gimbal", "Gimbal"), ("stativ", "statisch"),
                                                                       ("stativ", "Schwenk"), ("gimbal", "Fahrt"), ("gimbal", "Drohne")})
        for a in c.get("abschnitte") or []:
            if r.get("brennweitenklasse") and a.get("brennweite"):
                v = out["brennweite"]
                v["n"] += 1
                v["kreuz"][(r["brennweitenklasse"], a["brennweite"])] += 1
                v["gleich"] += int(r["brennweitenklasse"] == a["brennweite"])
            if r.get("perspektive_hoehe") and a.get("perspektive_hoehe"):
                v = out["perspektive_hoehe"]
                v["n"] += 1
                v["kreuz"][(r["perspektive_hoehe"], a["perspektive_hoehe"])] += 1
                v["gleich"] += int(r["perspektive_hoehe"] == a["perspektive_hoehe"])
    return out


def _kreuz(titel: str, v: dict, links: str, rechts: str) -> list[str]:
    if not v["n"]:
        return [f"{titel}: keine vergleichbaren Einträge.", ""]
    z = [f"{titel}: {v['gleich']} von {v['n']} gleich ({100 * v['gleich'] / v['n']:.0f} %).", "",
         f"| {links} | {rechts} | Anzahl |", "|---|---|---|"]
    z += [f"| {a} | {b} | {n} |" for (a, b), n in sorted(v["kreuz"].items(), key=lambda kv: -kv[1])]
    return z + [""]


def bericht_md(tele: list[dict], titel: str, index: dict | None = None) -> str:
    q = Counter(r.get("quelle") for r in tele)
    fehler = [r for r in tele if r.get("fehler") or r.get("quelle") in (None, "keine")]
    zeilen = [f"# Kamera-Telemetrie — {titel}", "",
              f"Stand: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M')} · {len(tele)} Clips (rtmd {q['rtmd']}, optisch {q['optisch']}, "
              f"keine {q['keine']}, Fehler {sum(1 for r in tele if r.get('fehler'))}). Werte in px @480 je 25-fps-Frame; "
              f"Quelle ``_intern/autocut/telemetrie.json``.", "",
              "## Verteilung je Kamera", ""] + _verteilung(tele) + ["", f"## Unruhigste Clips (bis {TOP}, nach wackeln)", ""] + _unruhigste(tele) + [""]
    zeilen += ["## Clips ohne Daten oder mit Fehler", ""]
    zeilen += [f"- {_md(r.get('clip'))} ({_md(r.get('kamera'))}, {_md(r.get('quelle'))}): {_md(r.get('fehler') or 'keine Datenspur, optisch nicht gemessen')}"
               for r in fehler] or ["- keine", ""]
    if index:
        v = vergleich_index(tele, index)
        zeilen += ["", "## Vergleich mit dem B-Roll-Index", ""]
        zeilen += _kreuz("Brennweite", v["brennweite"], "Telemetrie", "Claude (2b)")
        zeilen += _kreuz("Perspektive Höhe", v["perspektive_hoehe"], "Telemetrie", "Claude (2b)")
        zeilen += _kreuz("Haltung", v["haltung"], "Telemetrie", "Claude (Erst-Index kamerabewegung)")
    return "\n".join(zeilen).rstrip() + "\n"
```

- [ ] **Step 4: CLI schreiben**

```python
# tools/autocut/scripts/autocut_telemetrie.py
"""Kamera-Telemetrie je Clip (Gyro, Beschleunigung, Brennweite aus der Sony-rtmd-Spur; optischer Rückfall) →
<Charge>/_intern/autocut/telemetrie.json, Cache telemetrie/<fingerprint>.json, Bericht Ergebnisse/Rohschnitt/telemetrie.md.

Aufruf:
    venv/bin/python scripts/autocut_telemetrie.py "<Charge>" [--ordner <Pfad> ...] [--limit N] [--force] [--ohne-optisch]
                                                   [--parallel N] [--dry-run] [--kalibrieren]

Clip-Quelle: --ordner, sonst broll_index.json, inventar.json, B-Roll-Wurzeln des Transkript-Index, media.json.
--kalibrieren misst Gyro und optischen Weg auf demselben 4-s-Fenster je Clip und schreibt telemetrie_kalibrierung.json
(Achsen, Vorzeichen, px_faktor je Kamera, Spearman; Werte für defaults.yaml). Exit 1 bei Fehlern, 130 bei Abbruch.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402
from niro_autocut.telemetrie import clips_finden, telemetrie_charge  # noqa: E402
from niro_autocut.telemetrie_bericht import bericht_md  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Kamera-Telemetrie je Clip (telemetrie.json + Bericht).")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--ordner", nargs="+", help="Videoordner statt der Chargen-Quellen (rekursiv)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--force", action="store_true", help="Cache je Clip verwerfen und neu messen")
    ap.add_argument("--ohne-optisch", action="store_true", help="Clips ohne Datenspur nicht optisch messen (quelle: keine)")
    ap.add_argument("--parallel", type=int)
    ap.add_argument("--dry-run", action="store_true", help="nur Clip-Liste und Quelle zeigen, nichts messen oder schreiben")
    ap.add_argument("--kalibrieren", action="store_true", help="Gyro ↔ optisch auf demselben Fenster (telemetrie_kalibrierung.json)")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open_basis(args.charge)
        cfg = ch.config["telemetrie"]
        clips = clips_finden(ch, args.ordner)
        todo = clips[:args.limit] if args.limit else clips
        print(f"Charge: {ch.root}\n{len(clips)} Clips" + (f", dieser Lauf {len(todo)}" if args.limit else "")
              + f" · Ordner: {', '.join(sorted({c['ordner'] or '(Wurzel)' for c in clips})[:8])}\n")
        if args.dry_run:
            print("Probelauf — nichts gemessen, nichts geschrieben.")
            return 0
        if args.kalibrieren:
            from niro_autocut.telemetrie_kalibrierung import kalibrieren, tabelle
            erg = kalibrieren(ch, todo, cfg, parallel=args.parallel)
            print(tabelle(erg))
            append_protokoll(ch, "Telemetrie-Kalibrierung", [f"{erg['anzahl']} Clips, Datei {ch.autocut / 'telemetrie_kalibrierung.json'}"]
                             + [f"{k}: {v['empfehlung']}" for k, v in erg["kameras"].items()])
            return 0
        out = telemetrie_charge(ch, todo, cfg, limit=None, force=args.force, ohne_optisch=args.ohne_optisch, parallel=args.parallel)
        md = bericht_md(out["clips"], f"{ch.kunde} / {ch.projekt} / {ch.root.name}", ch.read_json("broll_index.json"))
        ziel = ch.ergebnisse / "telemetrie.md"
        ch.assert_writable(ziel)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(md, encoding="utf-8")
        zeilen = [f"Telemetrie: {len(out['clips'])} Clips ({out['gemessen']} gemessen, {out['cache_treffer']} Cache-Treffer, "
                  f"{len(out['fehler'])} Fehler)" + (f", Testlauf --limit {args.limit}" if args.limit else ""),
                  f"Dateien: {ch.autocut / 'telemetrie.json'}, {ziel}"] + [f"Fehler: {f}" for f in out["fehler"][:10]]
        append_protokoll(ch, "Telemetrie", zeilen)
        print("\n" + "\n".join(zeilen))
        return 1 if out["fehler"] else 0
    except KeyboardInterrupt:
        print("\nAbgebrochen — fertige Clips liegen im Cache (telemetrie/).", file=sys.stderr)
        return 130
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1
    except ImportError as e:
        print(f"FEHLER: {e} — Kalibrierung noch nicht verfügbar.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Grund-Doku**

README.md — in der Stufen-Tabelle (nach der Zeile „Kanten") eine Zeile:

```
| „Telemetrie" | – | Gyro, Beschleunigung, Brennweite je Clip aus der Sony-rtmd-Spur (optischer Rückfall) → `telemetrie.json`, `telemetrie.md`: wackeln, ruhige Fenster, Haltung, Bewegungsart, Brennweiten- und Perspektivklasse; Abnehmer Sichtung/Aftermovie, Stufe 2b, 6d |
```

README.md — Schnellstart (nach der `autocut_kanten.py`-Zeile):

```
    "$PY" "$TOOL/scripts/autocut_telemetrie.py" "$CHARGE" [--ordner <Pfad>] [--dry-run]   # Telemetrie je Clip: telemetrie.json + Bericht
    "$PY" "$TOOL/scripts/autocut_telemetrie.py" "$CHARGE" --kalibrieren                    # einmalig: Gyro ↔ optisch (defaults.yaml telemetrie:)
```

README.md — Aufbau `src/niro_autocut/` (nach `wiedergabe.py`):

```
      rtmd.py                Sony-rtmd-Datenspur: Samples, IMU-Blöcke, Brennweite/Fokus, Sidecar-XML, Kamera
      telemetrie.py          Kennzahlen (Gyro → px @480, wackeln, Fenster, Haltung, Bewegungsart, Lage), Clip-Messung, Cache, 2b/6d-Helfer
      telemetrie_optisch.py  Graustufen-Frames + numpy-Phasenkorrelation (Rückfall ohne Datenspur, Kalibrier-Referenz)
      telemetrie_bericht.py  Bericht telemetrie.md, Vergleich mit dem B-Roll-Index
      telemetrie_kalibrierung.py  Gyro ↔ optisch auf demselben Fenster: Achsen, Vorzeichen, px_faktor, Spearman
```

README.md — Arbeitsdateien: `telemetrie.json` (+ Cache `telemetrie/<fingerprint>.json`), `telemetrie_kalibrierung.json` in die `_intern/autocut/`-Liste; `telemetrie.md` in die `Ergebnisse/Rohschnitt/`-Liste.

WORKFLOW-AutoCut.md — neuer Abschnitt direkt vor `## Kantenprüfung — „Kanten"`:

```
## Telemetrie — „Telemetrie" (seit 21.09.2026)

`autocut_telemetrie.py "<Charge>" [--ordner <Pfad> …] [--limit N] [--force] [--ohne-optisch] [--dry-run]` liest je Clip die
Sony-rtmd-Datenspur (FX3, a7 IV: Gyro und Beschleunigung mit 2000 Hz, KB-Brennweite, Fokus) und schreibt
`_intern/autocut/telemetrie.json` (Liste je Clip) plus `Ergebnisse/Rohschnitt/telemetrie.md`. Clips ohne Datenspur (Mavic)
werden optisch gemessen (Phasenkorrelation 480×270 @25 fps). Beide Wege liefern dieselbe Größe: Verschiebung des Bildinhalts
je 25-fps-Frame in px @480 — `wackeln` (Zittern) und `bewegung` wie `jitter`/`bewegung` in `ruhe.py`.
Clip-Quelle: `--ordner`, sonst `broll_index.json`, `inventar.json`, B-Roll-Wurzeln des Transkript-Index, `media.json`.
Cache je Clip unter `_intern/autocut/telemetrie/<fingerprint>.json`; Lesen der Datenspur kostet die ganze Datei (≈ 300 MB/s
übers NAS). Felder je Clip: `quelle` (rtmd/optisch/keine), `kamera`, `kb_mm`/`brennweitenklasse` (weit < 30, tele > 60),
`pitch_grad`/`perspektive_hoehe`, `roll_grad`, `haltung` (stativ/gimbal/hand), `bewegungsart` (statisch, schwenk_links/rechts,
tilt_auf/ab, fahrt, gemischt — `schwenk_links` = Kamera dreht nach links), `wackeln`, `bewegung`, `fenster` (2 s, Schritt 1 s),
`ruhige_fenster` (wackeln ≤ `telemetrie.ruhig_max_px`). Schwellen und Kamerafaktoren in `defaults.yaml` unter `telemetrie:`.
Abnehmer: Sonderfall Aftermovie (ersetzt `ruhe.py`/`ruhe_fenster.py`), Stufe 2b (Brennweite/Perspektive aus Metadaten,
`bewegungsart`/`haltung` je Abschnitt) und 6d (Stabilisieren nur bei Bedarf). Kalibrierung: `--kalibrieren` (unten, Kalibrierwerte).
Spec: `docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md`.
```

test_docs.py — `SPEC_SCRIPTS` um `"autocut_telemetrie.py"` ergänzen.

- [ ] **Step 6: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_telemetrie_bericht.py tests/test_telemetrie_script.py tests/test_docs.py -q`
Expected: alle bestehen (`test_fehler_ohne_charge_und_ohne_clips`: `Charge.open_basis` verlangt `projects/<Kunde>/<Projekt>/`, `tmp_path/nirgendwo` liefert `AutoCutError` → Exit 1)

- [ ] **Step 7: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/src/niro_autocut/telemetrie_bericht.py tools/autocut/scripts/autocut_telemetrie.py tools/autocut/tests/test_telemetrie_bericht.py tools/autocut/tests/test_telemetrie_script.py tools/autocut/tests/test_docs.py tools/autocut/README.md tools/autocut/WORKFLOW-AutoCut.md && git commit -q -m "feat(autocut): autocut_telemetrie.py — CLI, Bericht telemetrie.md mit Index-Vergleich, Doku

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: `telemetrie_kalibrierung.py` — Gyro ↔ optisch auf demselben Fenster

**Files:**
- Create: `tools/autocut/src/niro_autocut/telemetrie_kalibrierung.py`
- Test: `tools/autocut/tests/test_telemetrie_kalibrierung.py`

**Interfaces:**
- Consumes: Task 1 (`datenspur_lesen`, `samples`, `auswerten`, `sidecar_modell`, `kamera_erkennen`), Task 2 (`graustufen`, `verschiebungen`), Task 3 (`gyro_je_frame`, `f_px`, `wackeln_bewegung`, `ZIEL_FPS`), `media.ffprobe`, `scipy.stats.spearmanr`
- Produces:
  - `clip_kalibrieren(path, cfg, von_s, dauer_s=4.0) -> dict | None` (`path`, `clip`, `kamera`, `kb_mm`, `k`, `rate` (m×3 Liste, °/s), `opt` (m×2 Liste, px))
  - `auswerten_kalibrierung(messungen: list[dict], cfg, ruhe: dict | None = None) -> dict`
  - `kalibrieren(ch, clips, cfg, dauer_s=4.0, parallel=None, melden=print) -> dict` (schreibt `telemetrie_kalibrierung.json`)
  - `tabelle(erg) -> str`

- [ ] **Step 1: Failing Tests schreiben**

```python
# tools/autocut/tests/test_telemetrie_kalibrierung.py
"""telemetrie_kalibrierung.py — Achsen/Vorzeichen/Faktor/Spearman aus synthetischen Gyro-↔-optisch-Paaren."""
from __future__ import annotations

import math

import numpy as np

from niro_autocut import telemetrie_kalibrierung as K
from test_telemetrie import CFG


def _messung(rng, kamera: str, faktor: float, n: int = 100, kb: float = 36.0, rauschen: float = 0.05, wackel: float = 1.0) -> dict:
    """Optische Verschiebung = faktor · (−Gyro-y für dx, +Gyro-x für dy) · k + Rauschen; Gyro-z unkorreliert."""
    k = math.pi / 180.0 * K.f_px(kb) / K.ZIEL_FPS
    rate = np.stack([rng.normal(0, 3 * wackel, n), rng.normal(0, 4 * wackel, n), rng.normal(0, 2, n)], axis=1)
    opt = np.stack([-faktor * rate[:, 1] * k + rng.normal(0, rauschen, n), faktor * rate[:, 0] * k + rng.normal(0, rauschen, n)], axis=1)
    return {"path": f"/nas/{kamera}_{rng.integers(1e6)}.MP4", "clip": "c", "kamera": kamera, "kb_mm": kb, "k": k,
            "rate": rate.tolist(), "opt": opt.tolist()}


def test_auswerten_findet_achsen_vorzeichen_faktor():
    rng = np.random.default_rng(5)
    mess = [_messung(rng, "FX3", 1.0, wackel=w) for w in np.linspace(0.2, 2.0, 12)] + \
           [_messung(rng, "a7IV", 0.6, wackel=w) for w in np.linspace(0.2, 2.0, 12)]
    erg = K.auswerten_kalibrierung(mess, CFG)
    fx = erg["kameras"]["FX3"]
    assert fx["achse_schwenk"] == 1 and fx["vorzeichen_schwenk"] == -1 and fx["achse_tilt"] == 0 and fx["vorzeichen_tilt"] == 1
    assert abs(fx["px_faktor"] - 1.0) < 0.1 and fx["spearman"] > 0.9 and fx["belastbar"] is True and fx["clips"] == 12
    a7 = erg["kameras"]["a7IV"]
    assert abs(a7["px_faktor"] - 0.6) < 0.1 and a7["belastbar"] is True
    e = erg["empfehlung"]
    assert e["achsen"] == {"schwenk": 1, "tilt": 0} and e["vorzeichen"] == {"schwenk": -1, "tilt": 1} and e["optisch_fuer"] == []
    assert abs(e["px_faktor"]["a7IV"] - 0.6) < 0.1


def test_auswerten_markiert_unbelastbare_kamera():
    rng = np.random.default_rng(6)
    mess = []
    for _ in range(20):                                          # 20 Clips: Zufalls-Spearman ≥ 0,7 praktisch ausgeschlossen
        m = _messung(rng, "DJI", 1.0)
        m["opt"] = rng.normal(0, 1, (100, 2)).tolist()          # optisch hat nichts mit dem Gyro zu tun
        mess.append(m)
    erg = K.auswerten_kalibrierung(mess, CFG)
    assert erg["kameras"]["DJI"]["belastbar"] is False and erg["empfehlung"]["optisch_fuer"] == ["DJI"]


def test_auswerten_klammert_saettigung_aus_und_vergleicht_cv2():
    rng = np.random.default_rng(7)
    mess = [_messung(rng, "FX3", 1.0) for _ in range(6)]
    mess[0]["opt"] = (np.array(mess[0]["opt"]) + 70.0).tolist()          # gesättigte Frames (> 40 px) zählen nicht
    ruhe = {m["clip"] + str(i): 0.0 for i, m in enumerate(mess)}
    for i, m in enumerate(mess):
        m["clip"] = m["clip"] + str(i)
        ruhe[m["clip"]] = K.wackeln_bewegung(np.array(m["opt"]))[0] * 1.02  # cv2-Wert ≈ numpy-Wert
    erg = K.auswerten_kalibrierung(mess, CFG, ruhe=ruhe)
    assert erg["kameras"]["FX3"]["clips"] == 5 and abs(erg["kameras"]["FX3"]["px_faktor"] - 1.0) < 0.15
    assert erg["cv2_vergleich"]["n"] == 5 and abs(erg["cv2_vergleich"]["verhaeltnis_median"] - 1.02) < 0.01 and erg["cv2_vergleich"]["r"] > 0.99


def test_tabelle_und_leer():
    erg = K.auswerten_kalibrierung([], CFG)
    assert erg["kameras"] == {} and "keine Clips" in K.tabelle(erg)
    rng = np.random.default_rng(8)
    erg = K.auswerten_kalibrierung([_messung(rng, "FX3", 1.0) for _ in range(3)], CFG)
    t = K.tabelle(erg)
    assert "FX3" in t and "px_faktor" in t and "Spearman" in t
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_telemetrie_kalibrierung.py -q`
Expected: ERROR `No module named 'niro_autocut.telemetrie_kalibrierung'`

- [ ] **Step 3: Modul schreiben**

```python
# tools/autocut/src/niro_autocut/telemetrie_kalibrierung.py
"""Kalibrierung Gyro ↔ optisch (Spec 2026-09-19, Abschnitt Kalibrierung): beide Messwege auf demselben Fenster je Clip.

Je Kamera: Achse und Vorzeichen für Schwenk (→ dx) und Tilt (→ dy) aus der Korrelation der Gyro-Raten mit der optischen
Verschiebung, Kamerafaktor (IBIS-Dämpfung) als robuste Steigung Gyro-px → optisch-px, Rangkorrelation (Spearman) der
Wackel-Werte je Clip; Gegenprobe der numpy-Phasenkorrelation gegen vorhandene cv2-Werte (``ruhe.json``).
Frames mit |optisch| ≥ 40 px zählen nicht (Phasenkorrelation sättigt; Stichprobe 21.09.).
"""
from __future__ import annotations

import datetime as _dt
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from .charge import AutoCutError
from .media import ffprobe
from .rtmd import auswerten, datenspur_lesen, kamera_erkennen, samples, sidecar_modell
from .telemetrie import ZIEL_FPS, f_px, gyro_je_frame, wackeln_bewegung
from .telemetrie_optisch import graustufen, verschiebungen

SAETTIGUNG_PX = 40.0
MIN_FRAMES = 10
BELASTBAR_AB = 0.7


def clip_kalibrieren(path: str | Path, cfg: dict, von_s: float, dauer_s: float = 4.0) -> dict | None:
    """Gyro-Raten je 25-fps-Frame (roh, 3 Achsen) und optische Verschiebung über dasselbe Fenster; None ohne Gyro/Brennweite."""
    p = Path(path)
    info = ffprobe(p)
    buf = datenspur_lesen(p)
    if not buf:
        return None
    d = auswerten(samples(buf))
    if len(d.gyro) == 0 or d.proben_je_sample <= 0 or not d.kb_mm:
        return None
    i0 = int(round(von_s * info.fps))
    i1 = int(round((von_s + dauer_s) * info.fps))
    gyro = d.gyro[i0 * d.proben_je_sample:i1 * d.proben_je_sample]
    rate = gyro_je_frame(gyro, d.proben_je_sample, info.fps)
    opt = verschiebungen(graustufen(p, ZIEL_FPS, von_s, dauer_s, int(cfg["optisch_breite"]), int(round(int(cfg["optisch_breite"]) * 9 / 16))))
    m = min(len(rate) - 1, len(opt))
    if m < MIN_FRAMES:
        return None
    kb = float(np.median(d.kb_mm))
    return {"path": str(p), "clip": p.stem, "kamera": kamera_erkennen(p, sidecar_modell(p)), "kb_mm": round(kb, 1),
            "k": math.pi / 180.0 * f_px(kb, int(cfg["optisch_breite"])) / ZIEL_FPS, "rate": rate[:m].tolist(), "opt": opt[:m].tolist()}


def _korrelation(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def auswerten_kalibrierung(messungen: list[dict], cfg: dict, ruhe: dict | None = None) -> dict:
    """Je Kamera Achsen/Vorzeichen, px_faktor (Median der Steigungen je Clip), Spearman; Empfehlung für defaults.yaml."""
    kameras: dict[str, dict] = {}
    for kam in sorted({m["kamera"] for m in messungen}):
        ms = [m for m in messungen if m["kamera"] == kam]
        rates, opts, clips = [], [], []
        for m in ms:
            rate, opt = np.array(m["rate"], float), np.array(m["opt"], float)
            ok = (np.abs(opt) < SAETTIGUNG_PX).all(axis=1)
            if ok.sum() < MIN_FRAMES:
                continue
            rates.append(rate[ok] * m["k"])
            opts.append(opt[ok])
            clips.append(m)
        if not clips:
            continue
        r_all, o_all = np.concatenate(rates), np.concatenate(opts)
        r_dx = [_korrelation(r_all[:, a], o_all[:, 0]) for a in range(3)]
        achse_s = int(np.argmax(np.abs(r_dx)))
        vz_s = 1 if r_dx[achse_s] >= 0 else -1
        r_dy = [_korrelation(r_all[:, a], o_all[:, 1]) if a != achse_s else 0.0 for a in range(3)]
        achse_t = int(np.argmax(np.abs(r_dy)))
        vz_t = 1 if r_dy[achse_t] >= 0 else -1
        steigungen, wg, wo = [], [], []
        for r, o in zip(rates, opts):
            pred = np.stack([vz_s * r[:, achse_s], vz_t * r[:, achse_t]], axis=1)
            nenner = float((pred ** 2).sum())
            if nenner > 0:
                steigungen.append(float((pred * o).sum() / nenner))
            wg.append(wackeln_bewegung(pred)[0])
            wo.append(wackeln_bewegung(o)[0])
        faktor = float(np.median(steigungen)) if steigungen else 1.0
        rho = float(spearmanr(wg, wo).statistic) if len(wg) >= 3 else 0.0
        if math.isnan(rho):
            rho = 0.0
        kameras[kam] = {"clips": len(clips), "frames": int(len(r_all)), "achse_schwenk": achse_s, "vorzeichen_schwenk": vz_s,
                        "r_schwenk": round(r_dx[achse_s], 3), "achse_tilt": achse_t, "vorzeichen_tilt": vz_t,
                        "r_tilt": round(r_dy[achse_t], 3), "px_faktor": round(faktor, 3), "spearman": round(rho, 3),
                        "belastbar": bool(rho >= BELASTBAR_AB)}
        kameras[kam]["empfehlung"] = (f"px_faktor {kameras[kam]['px_faktor']}, Spearman {kameras[kam]['spearman']}"
                                     + ("" if kameras[kam]["belastbar"] else " → optisch_fuer"))
    # Empfehlung: Achsen/Vorzeichen aus der belastbaren Kamera mit den meisten Frames, Faktor je Kamera
    belastbar = {k: v for k, v in kameras.items() if v["belastbar"]}
    basis = max(belastbar.values(), key=lambda v: v["frames"]) if belastbar else None
    empfehlung = {"achsen": {"schwenk": basis["achse_schwenk"], "tilt": basis["achse_tilt"]} if basis else dict(cfg["achsen"]),
                  "vorzeichen": {"schwenk": basis["vorzeichen_schwenk"], "tilt": basis["vorzeichen_tilt"]} if basis else
                  {"schwenk": cfg["vorzeichen"]["schwenk"], "tilt": cfg["vorzeichen"]["tilt"]},
                  "px_faktor": {k: v["px_faktor"] for k, v in belastbar.items()},
                  "optisch_fuer": sorted(k for k, v in kameras.items() if not v["belastbar"])}
    cv2 = None
    if ruhe:
        paare = [(wackeln_bewegung(np.array(m["opt"], float))[0], float(ruhe[m["clip"]])) for m in messungen
                 if m["clip"] in ruhe and ruhe[m["clip"]] is not None and (np.abs(np.array(m["opt"])) < SAETTIGUNG_PX).all()]
        if paare:
            a, b = np.array(paare).T
            verh = np.median(b[a > 0] / a[a > 0]) if (a > 0).any() else float("nan")
            cv2 = {"n": len(paare), "r": round(_korrelation(a, b), 4), "verhaeltnis_median": round(float(verh), 3)}
    return {"erstellt_am": _dt.datetime.now().isoformat(timespec="seconds"), "anzahl": len(messungen), "kameras": kameras,
            "empfehlung": empfehlung, "cv2_vergleich": cv2}


def kalibrieren(ch, clips: list[dict], cfg: dict, dauer_s: float = 4.0, parallel: int | None = None, melden=print) -> dict:
    """Alle Clips messen (Fenster ab ``von_s`` aus ``_intern/sichtung/katalog.json``, sonst 0,5 s), auswerten, JSON schreiben."""
    katalog = Path(ch.intern) / "sichtung" / "katalog.json"
    von: dict[str, float] = {}
    ruhe: dict[str, float] | None = None
    if katalog.exists():
        von = {r["clip"]: float(r.get("von_s", 0.5)) for r in json.loads(katalog.read_text(encoding="utf-8"))}
    ruhe_pfad = Path(ch.intern) / "sichtung" / "ruhe.json"
    if ruhe_pfad.exists():
        ruhe = {r["clip"]: r.get("jitter") for r in json.loads(ruhe_pfad.read_text(encoding="utf-8")) if "jitter" in r}
    messungen, fehler = [], []
    ex = ThreadPoolExecutor(max_workers=max(1, int(parallel or cfg.get("parallel", 2))))
    try:
        futs = {ex.submit(clip_kalibrieren, c["path"], cfg, von.get(Path(c["path"]).stem, 0.5), dauer_s): c for c in clips}
        for i, fut in enumerate(as_completed(futs), 1):
            name = Path(futs[fut]["path"]).name
            try:
                m = fut.result()
            except AutoCutError as e:
                fehler.append(f"{name}: {e}")
                melden(f"[{i}/{len(clips)}] FEHLER {name}: {e}", flush=True)
                continue
            if m is None:
                melden(f"[{i}/{len(clips)}] {name}: ohne Gyro/Brennweite oder zu kurz — übersprungen", flush=True)
                continue
            messungen.append(m)
            melden(f"[{i}/{len(clips)}] {name}: {len(m['rate'])} Frames, KB {m['kb_mm']} mm", flush=True)
    except KeyboardInterrupt:
        ex.shutdown(wait=False, cancel_futures=True)
        raise
    ex.shutdown(wait=True)
    erg = auswerten_kalibrierung(messungen, cfg, ruhe)
    erg["fehler"] = fehler
    erg["clips"] = [{"clip": m["clip"], "kamera": m["kamera"], "kb_mm": m["kb_mm"], "frames": len(m["rate"]),
                     "wackeln_optisch": round(wackeln_bewegung(np.array(m["opt"]))[0], 3)} for m in messungen]
    ch.write_json("telemetrie_kalibrierung.json", erg)
    return erg


def tabelle(erg: dict) -> str:
    if not erg.get("kameras"):
        return "Kalibrierung: keine Clips mit Gyro und Brennweite."
    z = [f"{'Kamera':<8} {'Clips':>5} {'Frames':>7} {'Schwenk':>9} {'r':>6} {'Tilt':>7} {'r':>6} {'px_faktor':>9} {'Spearman':>8}  belastbar"]
    for k, v in erg["kameras"].items():
        z.append(f"{k:<8} {v['clips']:>5} {v['frames']:>7} {('xyz'[v['achse_schwenk']] + ('+' if v['vorzeichen_schwenk'] > 0 else '−')):>9} "
                 f"{v['r_schwenk']:>6.2f} {('xyz'[v['achse_tilt']] + ('+' if v['vorzeichen_tilt'] > 0 else '−')):>7} {v['r_tilt']:>6.2f} "
                 f"{v['px_faktor']:>9.3f} {v['spearman']:>8.2f}  {'ja' if v['belastbar'] else 'NEIN → optisch_fuer'}")
    e = erg["empfehlung"]
    z.append(f"\nEmpfehlung defaults.yaml telemetrie: achsen {e['achsen']}, vorzeichen {e['vorzeichen']}, px_faktor {e['px_faktor']}, "
             f"optisch_fuer {e['optisch_fuer']}")
    if erg.get("cv2_vergleich"):
        c = erg["cv2_vergleich"]
        z.append(f"Gegenprobe cv2 (ruhe.json): {c['n']} Clips, r = {c['r']}, Verhältnis cv2/numpy Median {c['verhaeltnis_median']}")
    return "\n".join(z)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_telemetrie_kalibrierung.py -q`
Expected: `4 passed`. (`from test_telemetrie import CFG` funktioniert, weil pytest `tests/` als Rootdir-Modulpfad nutzt — `conftest.py` liegt dort; sonst `sys.path`-Eintrag wie in `test_readback.py` für `fake_resolve`.)

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/src/niro_autocut/telemetrie_kalibrierung.py tools/autocut/tests/test_telemetrie_kalibrierung.py && git commit -q -m "feat(autocut): Telemetrie-Kalibrierung Gyro ↔ optisch (Achsen, Vorzeichen, px_faktor, Spearman, cv2-Gegenprobe)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Kalibrierlauf mit echtem Material (Hochzeitszauber, MEK) — Schwellen, Faktoren, Fixtures

Diese Task braucht das gemountete NAS (`/Volumes/NIRO NAS`) und dauert durch das Lesen der Dateien ≈ 30 Minuten Rechenzeit.
Sie schreibt in zwei Chargen (`_intern/autocut/`, `Ergebnisse/Rohschnitt/`, `Protokoll.md`) — vorher und nachher den
NAS-Abgleich laufen lassen (CLAUDE.md, Protokoll-Pflicht). Nichts in Resolve.

**Files:**
- Modify: `tools/autocut/defaults.yaml` (`telemetrie:` — Werte aus der Kalibrierung)
- Create: `tools/autocut/tests/fixtures/rtmd_fx3_25p.bin`, `tools/autocut/tests/fixtures/rtmd_a7iv_50p.bin`
- Modify: `docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md` (Nachtrag „Kalibrierung 21.09."), `tools/autocut/WORKFLOW-AutoCut.md` (Absatz „Kalibrierwerte" im Abschnitt Telemetrie)

**Interfaces:**
- Consumes: Task 5 CLI, Task 6 Kalibrierung, `sh tools/studio_abgleich.sh --charge …`
- Produces: kalibrierte `defaults.yaml`, Fixtures für `test_rtmd.py::test_echte_datenspur`

- [ ] **Step 1: NAS prüfen, Chargen abgleichen**

```bash
cd "/Users/jansantos/NIRO Studio" && ls "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/MN Deko und Verleih/02_Projekte/01_Projekt-Hochzeitsmesse Aftermovie/03_Medien/01_Footage/FX3" | head -3
sh tools/studio_abgleich.sh --charge "projects/MN Deko und Verleih/Hochzeitsmesse Aftermovie/2026-09 Hochzeitsmesse 13.09"
sh tools/studio_abgleich.sh --charge "projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh"
```
Expected: drei FX3-Dateien gelistet; Abgleich ohne Fehler (Ausgabe „neuere Datei gewinnt"-Zeilen oder nichts).

- [ ] **Step 2: Kalibrierung Hochzeitszauber (368 Clips: 301 FX3 Gimbal, 59 a7 IV Hand, 8 DJI)**

```bash
cd "/Users/jansantos/NIRO Studio" && HZ="projects/MN Deko und Verleih/Hochzeitsmesse Aftermovie/2026-09 Hochzeitsmesse 13.09" && tools/autocut/venv/bin/python tools/autocut/scripts/autocut_telemetrie.py "$HZ" --kalibrieren --parallel 2 2>&1 | tail -15
```
Expected: Tabelle je Kamera (FX3, a7IV; DJI fehlt mangels Gyro), Zeile „Gegenprobe cv2 (ruhe.json): … r = 0,9x, Verhältnis … ≈ 1,0".
Entscheidungsregeln:
- `r_schwenk` und `r_tilt` beider Kameras ≥ 0,6 im Betrag und dieselbe Achse/Vorzeichen → Empfehlung übernehmen. Weichen die
  Kameras in Achse oder Vorzeichen voneinander ab, den Lauf mit `--limit 40` je Kamera wiederholen (`--ordner` auf den FX3- bzw.
  A7iv-Ordner) und die Kamera mit dem höheren |r| als Basis nehmen; die Abweichung im Spec-Nachtrag festhalten.
- Gegenprobe cv2: r < 0,9 oder Verhältnis außerhalb 0,8–1,25 → erst `telemetrie_optisch.py` prüfen (Vorzeichen, Fenster), nicht die
  Faktoren übernehmen.
- `belastbar` NEIN bei einer Kamera → sie steht in `optisch_fuer`; im Spec-Nachtrag begründen (IBIS).

- [ ] **Step 3: `defaults.yaml` mit den Kalibrierwerten füllen**

Im Block `telemetrie:` die Zeilen `achsen`, `vorzeichen` (schwenk, tilt; `pitch` bleibt vorerst 1), `px_faktor` und `optisch_fuer`
auf die Empfehlung aus Schritt 2 setzen; im Kommentar das Datum und die Zahl der Clips nennen, z. B.
`px_faktor: {FX3: 0.97, a7IV: 0.62}   # Kalibrierung 21.09.2026, Hochzeitszauber 301/59 Clips, Spearman 0,9x/0,8x`.

- [ ] **Step 4: Messlauf Hochzeitszauber und Schwelle `hand_hf_anteil_min`**

```bash
cd "/Users/jansantos/NIRO Studio" && HZ="projects/MN Deko und Verleih/Hochzeitsmesse Aftermovie/2026-09 Hochzeitsmesse 13.09" && tools/autocut/venv/bin/python tools/autocut/scripts/autocut_telemetrie.py "$HZ" --force --parallel 2 2>&1 | tail -8
```
Dann die Verteilung des Hochfrequenzanteils je Kamera ansehen:

```bash
cd "/Users/jansantos/NIRO Studio" && tools/autocut/venv/bin/python - <<'PY'
import json, numpy as np
HZ = "projects/MN Deko und Verleih/Hochzeitsmesse Aftermovie/2026-09 Hochzeitsmesse 13.09/_intern/autocut/telemetrie.json"
tele = json.load(open(HZ, encoding="utf-8"))
for kam in ("FX3", "a7IV"):
    hf = np.array([r["hf_anteil"] for r in tele if r["kamera"] == kam and r["quelle"] == "rtmd" and r["hf_anteil"] is not None and r["haltung"] != "stativ"])
    q = np.percentile(hf, [10, 25, 50, 75, 90]) if len(hf) else []
    print(kam, len(hf), "hf_anteil P10/25/50/75/90:", [round(float(x), 3) for x in q])
    print("   haltung:", {h: sum(1 for r in tele if r["kamera"] == kam and r["haltung"] == h) for h in ("stativ", "gimbal", "hand")})
PY
```
Entscheidungsregel: `hand_hf_anteil_min` = Mitte zwischen P75 der FX3 (Gimbal) und P25 der a7 IV (Hand). Liegt P75(FX3) über
P25(a7IV) (Überlappung), die Schwelle auf P50(a7IV) − (P50(a7IV) − P50(FX3)) / 2 setzen und den Überlappungsanteil im Spec-Nachtrag
nennen. Wert in `defaults.yaml` eintragen, Lauf mit `--force` wiederholen, Verteilung „haltung" je Kamera im Bericht prüfen
(`Ergebnisse/Rohschnitt/telemetrie.md`): FX3 überwiegend gimbal, a7 IV überwiegend hand.

- [ ] **Step 5: Messlauf MEK (463 B-Roll-Clips mit Stufe-2b-Feldern) und Vergleich mit dem Index**

```bash
cd "/Users/jansantos/NIRO Studio" && MEK="projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh" && tools/autocut/venv/bin/python tools/autocut/scripts/autocut_telemetrie.py "$MEK" --parallel 2 2>&1 | tail -8 && sed -n '/## Vergleich mit dem B-Roll-Index/,$p' "$MEK/Ergebnisse/Rohschnitt/telemetrie.md"
```
Entscheidungsregeln:
- **Perspektive Höhe:** Zeigt die Kreuztabelle überwiegend (Aufsicht ↔ Untersicht) vertauscht (mehr Zeilen `| Aufsicht | Untersicht |`
  und `| Untersicht | Aufsicht |` als gleichnamige), ist das Pitch-Vorzeichen falsch → `vorzeichen: {…, pitch: -1}` in `defaults.yaml`
  und den MEK-Lauf mit `--force` wiederholen. Übereinstimmung danach ≥ 70 % erwartet; darunter die Grenzen `pitch_klassen_grad`
  (−8/8) auf ±12 prüfen und die bessere Variante nehmen (im Spec-Nachtrag beide Werte nennen).
- **Brennweite:** Übereinstimmung ≥ 70 % erwartet (Claude schätzt Objektivklasse aus dem Bild). Darunter die Grenzen
  `brennweite_klassen_kb` [30, 60] gegen [35, 70] prüfen; die Kreuztabelle zeigt, wohin die Abweichungen fallen.
- **Haltung:** Anteil `hand` ↔ `Handkamera` und `gimbal` ↔ `Gimbal` notieren; keine Änderung der Schwelle aus Schritt 4, nur Doku.

- [ ] **Step 6: Fixtures extrahieren und Fixture-Tests laufen lassen**

```bash
cd "/Users/jansantos/NIRO Studio" && F="/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/MN Deko und Verleih/02_Projekte/01_Projekt-Hochzeitsmesse Aftermovie/03_Medien/01_Footage" && ffmpeg -v error -y -t 0.3 -i "$F/FX3/FX3_0330.MP4" -map 0:d:0 -c copy -f data tools/autocut/tests/fixtures/rtmd_fx3_25p.bin && ffmpeg -v error -y -t 0.3 -i "$F/A7iv/a7MK4_20260913_2128.MP4" -map 0:d:0 -c copy -f data tools/autocut/tests/fixtures/rtmd_a7iv_50p.bin && ls -la tools/autocut/tests/fixtures/rtmd_*.bin
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_rtmd.py -q
```
Expected: FX3 ≈ 8 Samples (≈ 156 KB), a7 IV ≈ 15 Samples (≈ 292 KB); `10 passed` (keine Skips mehr).

- [ ] **Step 7: Spec-Nachtrag und WORKFLOW-Kalibrierwerte**

Im Spec einen Abschnitt `## Nachtrag 21.09.2026 — Kalibrierung` anhängen: Tabelle aus Schritt 2 (Kamera, Clips, Frames, Achse/Vorzeichen
Schwenk und Tilt mit r, px_faktor, Spearman, belastbar), cv2-Gegenprobe (n, r, Verhältnis), `hand_hf_anteil_min` mit den Perzentilen aus
Schritt 4, MEK-Übereinstimmungen aus Schritt 5 (Brennweite, Perspektive, Haltung in Prozent) und die daraus gesetzten Werte.
Im WORKFLOW-Abschnitt „Telemetrie" einen Absatz „Kalibrierwerte (21.09.2026)" mit denselben Zahlen in zwei, drei Sätzen.

- [ ] **Step 8: Protokoll und Abgleich beider Chargen**

Die CLI hat je Lauf einen Protokoll-Eintrag geschrieben (Telemetrie-Kalibrierung, Telemetrie). Danach:

```bash
cd "/Users/jansantos/NIRO Studio" && sh tools/studio_abgleich.sh --charge "projects/MN Deko und Verleih/Hochzeitsmesse Aftermovie/2026-09 Hochzeitsmesse 13.09" && sh tools/studio_abgleich.sh --charge "projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh"
```

- [ ] **Step 9: Tests und Commit**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/defaults.yaml tools/autocut/tests/fixtures/rtmd_fx3_25p.bin tools/autocut/tests/fixtures/rtmd_a7iv_50p.bin docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md tools/autocut/WORKFLOW-AutoCut.md && git commit -q -m "feat(autocut): Telemetrie kalibriert (Hochzeitszauber, MEK): Achsen, Vorzeichen, px_faktor, hand_hf_anteil_min; rtmd-Fixtures

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: Stufe 2b — Telemetrie in `index_sections.py` und `autocut_index_sections.py`

**Files:**
- Modify: `tools/autocut/src/niro_autocut/index_sections.py` (Import, `telemetrie_text`, `section_meta_text(rec, tele=None)`, `telemetrie_anwenden`, `_cache_schreiben`, `index_sections_clip(..., telemetrie=None)`, `index_sections`)
- Modify: `tools/autocut/scripts/autocut_index_sections.py` (`--dry-run`-Zeile, Protokoll-Zeile)
- Modify: `tools/autocut/tests/test_index_sections.py` (drei neue Tests; Signatur von `fake_clip` in `test_index_sections_counts_repairs_over_all_clips`)
- Modify: `tools/autocut/WORKFLOW-AutoCut.md` (Stufe 2b: zwei Sätze), `tools/autocut/prompts/index-sections.md` (ein Satz zur Kontextzeile)

**Interfaces:**
- Consumes: Task 4 (`laden`, `finden`, `abschnitt_werte`)
- Produces:
  - `telemetrie_text(tele, abschnitte) -> str`
  - `telemetrie_anwenden(rec, tele, fenster_s=2.0) -> tuple[dict, bool]`
  - `index_sections_clip(charge, rec, client, cfg, system_prompt, force=False, describe=describe_sections, telemetrie=None)`
  - `index_sections(...)` liefert zusätzlich `mit_telemetrie: int`; `nachlauf.mit_telemetrie` in `broll_index.json`

- [ ] **Step 1: Failing Tests anhängen (und die bestehende Fake-Signatur anpassen)**

In `test_index_sections_counts_repairs_over_all_clips` die Zeile `def fake_clip(charge, c, client, cfg, prompt, force):` ersetzen durch
`def fake_clip(charge, c, client, cfg, prompt, force, telemetrie=None):`. Dann anhängen:

```python
# tools/autocut/tests/test_index_sections.py — anhängen
TELE = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "clip": "FX3_1", "quelle": "rtmd", "kb_mm": 71.6, "brennweitenklasse": "tele",
        "pitch_grad": -12.0, "perspektive_hoehe": "Aufsicht", "haltung": "gimbal", "wackeln": 0.05, "fehler": None,
        "fenster": [[0.0, 0.05, 1.0, "schwenk_links"], [1.0, 0.05, 1.0, "schwenk_links"], [2.0, 0.05, 1.0, "schwenk_links"],
                    [3.0, 0.05, 1.0, "schwenk_links"], [4.0, 0.02, 0.1, "statisch"], [5.0, 0.02, 0.1, "statisch"],
                    [6.0, 0.02, 0.1, "statisch"]]}
_CFG_T = {"index": {"model": "claude-opus-5"},
          "index_sections": {"tile_px": 480, "per_section": 2, "max_sections": 5, "effort": "medium", "max_tokens": 2500},
          "telemetrie": {"fenster_s": 2.0}}


def test_telemetrie_text_und_anwenden():
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "normal", "perspektive_hoehe": "Augenhöhe"},
                          {"von_s": 4, "bis_s": 8, "brennweite": "tele", "perspektive_hoehe": "Aufsicht"}]}
    text = S.telemetrie_text(TELE, rec["abschnitte"])
    assert "KB 71.6 mm = tele" in text and "Pitch -12° = Aufsicht" in text and "Haltung gimbal" in text
    assert "A1 schwenk_links, A2 statisch" in text
    assert S.telemetrie_text(None, rec["abschnitte"]) == "" and S.telemetrie_text({"quelle": "keine"}, []) == ""
    neu, geaendert = S.telemetrie_anwenden(rec, TELE)
    assert geaendert and neu["felder_quelle"] == {"brennweite": "rtmd", "perspektive_hoehe": "rtmd"}
    assert [a["brennweite"] for a in neu["abschnitte"]] == ["tele", "tele"]
    assert [a["perspektive_hoehe"] for a in neu["abschnitte"]] == ["Aufsicht", "Aufsicht"]
    assert [a["bewegungsart"] for a in neu["abschnitte"]] == ["schwenk_links", "statisch"] and neu["abschnitte"][0]["haltung"] == "gimbal"
    assert S.telemetrie_anwenden(rec, None) == (rec, False)
    wieder, geaendert2 = S.telemetrie_anwenden(neu, TELE)
    assert not geaendert2 and wieder == neu
    assert "brennweite" not in S.telemetrie_anwenden({"abschnitte": [{"von_s": 0, "bis_s": 2}]}, TELE)[0]["abschnitte"][0]


def test_index_sections_clip_wendet_telemetrie_bei_cache_treffer_an(tmp_path):
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "fingerprint": "abcdefabcdef0000", "orientierung": "16:9",
           "abschnitte": [{"von_s": 0, "bis_s": 4, "beschreibung": "Flur", "qualitaet": 4, "verwendbar": True, "einstellung": "Halbtotale",
                           "perspektive_hoehe": "Augenhöhe", "perspektive_ansicht": "seitlich", "brennweite": "normal",
                           "bewegungsrichtung": "keine", "hauptmotiv": "Flur", "setup_hash": "0123456789abcdef"}]}
    (ch.autocut / "broll_index" / "abcdefabcdef0000.json").write_text(json.dumps(rec), encoding="utf-8")

    def kein_api(*a, **k):
        raise AssertionError("kein API-Aufruf bei Cache-Treffer")

    out = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", describe=kein_api, telemetrie=TELE)
    assert out["_cache"] is True and out["abschnitte"][0]["brennweite"] == "tele" and out["felder_quelle"]["brennweite"] == "rtmd"
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["abschnitte"][0]["perspektive_hoehe"] == "Aufsicht" and cached["abschnitte"][0]["bewegungsart"] == "schwenk_links"
    ohne = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", describe=kein_api)
    assert ohne["_cache"] is True and ohne["abschnitte"][0]["brennweite"] == "normal"


def test_index_sections_clip_api_mit_telemetrie(tmp_path):
    _frames(tmp_path)
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "fingerprint": "abcdefabcdef0000", "orientierung": "16:9",
           "abschnitte": [{"von_s": 0, "bis_s": 4, "beschreibung": "Flur", "qualitaet": 4, "verwendbar": True}]}

    def fake_describe(client, sheet, meta_text, cfg, prompt):
        assert "Kamera-Telemetrie" in meta_text and "KB 71.6 mm = tele" in meta_text
        return {"abschnitte": [{"nr": 1, "einstellung": "Halbtotale", "perspektive_hoehe": "Augenhöhe", "perspektive_ansicht": "seitlich",
                                "brennweite": "normal", "bewegungsrichtung": "keine", "hauptmotiv": "Flur"}],
                "_usage": {"input": 1, "output": 1, "cache_read": 0, "cache_write": 0}}

    out = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", describe=fake_describe, telemetrie=TELE)
    a = out["abschnitte"][0]
    assert a["brennweite"] == "tele" and a["perspektive_hoehe"] == "Aufsicht" and a["bewegungsart"] == "schwenk_links" and a["haltung"] == "gimbal"
    assert out["felder_quelle"] == {"brennweite": "rtmd", "perspektive_hoehe": "rtmd"}
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["felder_quelle"]["brennweite"] == "rtmd" and "_cache" not in cached


def test_index_sections_zaehlt_telemetrie(tmp_path, monkeypatch):
    ch, rec = _rec2(tmp_path)
    (ch.autocut / "telemetrie.json").write_text(json.dumps([{**TELE, "path": rec["path"]}]), encoding="utf-8")
    monkeypatch.setattr(S, "_make_client", lambda cfg: object())
    monkeypatch.setattr(S, "load_system_prompt", lambda: "prompt")
    gesehen = {}

    def fake_clip(charge, c, client, cfg, prompt, force, telemetrie=None):
        gesehen[c["datei"]] = telemetrie
        return {**c, "abschnitte": [{**a, **_GOOD_ITEM, "setup_hash": "0" * 16} for a in c["abschnitte"]],
                "nachlauf": {"usage": dict(_USAGE), "reparaturen": 0}, "_cache": False}

    monkeypatch.setattr(S, "index_sections_clip", fake_clip)
    out = S.index_sections(ch, {"clips": [rec]}, _CFG2, parallel=1)
    assert out["mit_telemetrie"] == 1 and gesehen[rec["datei"]]["clip"] == "FX3_1"
    assert json.loads((ch.autocut / "broll_index.json").read_text())["nachlauf"]["mit_telemetrie"] == 1
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_index_sections.py -q`
Expected: die vier neuen Tests scheitern (`AttributeError: … has no attribute 'telemetrie_text'`, `TypeError: unexpected keyword argument 'telemetrie'`); die alten bestehen.

- [ ] **Step 3: `index_sections.py` ändern**

Import ergänzen (nach `from .charge import …`):

```python
from .telemetrie import abschnitt_werte, finden, laden as telemetrie_laden
```

Vor `section_meta_text` einfügen und `section_meta_text` ersetzen:

```python
def telemetrie_text(tele: dict | None, abschnitte: list[dict]) -> str:
    """Kontextzeile für den Abschnittsbogen aus der gemessenen Kamera-Telemetrie; leer ohne Daten."""
    if not tele or tele.get("quelle") in (None, "keine"):
        return ""
    teile = []
    if tele.get("kb_mm"):
        teile.append(f"KB {tele['kb_mm']:g} mm = {tele.get('brennweitenklasse')}")
    if tele.get("pitch_grad") is not None:
        teile.append(f"Pitch {tele['pitch_grad']:g}° = {tele.get('perspektive_hoehe')}")
    if tele.get("haltung"):
        teile.append(f"Haltung {tele['haltung']}")
    arten = [abschnitt_werte(tele, float(a.get("von_s", 0)), float(a.get("bis_s", 0)))["bewegungsart"] for a in abschnitte]
    if any(arten):
        teile.append("Bewegungsart je Abschnitt: " + ", ".join(f"A{i} {x or '?'}" for i, x in enumerate(arten, 1)))
    if not teile:
        return ""
    return "Kamera-Telemetrie (gemessen; brennweite und perspektive_hoehe setzt das Schnittprogramm daraus fest): " + " · ".join(teile)


def section_meta_text(rec: dict, tele: dict | None = None) -> str:
    lines = [f"Clip: {rec.get('datei') or Path(str(rec.get('path', ''))).name}",
             f"Motiv-Ordner: {rec.get('ordner') or '(keiner)'} · Standort: {rec.get('standort') or '(unbekannt)'}",
             f"Kamerabewegung laut Erst-Index: {rec.get('kamerabewegung') or '?'}"]
    t = telemetrie_text(tele, rec.get("abschnitte") or [])
    if t:
        lines.append(t)
    lines.append("")
    for i, a in enumerate(rec.get("abschnitte") or [], 1):
        lines.append(f"Abschnitt {i} = Zeile A{i}: {a.get('von_s')}–{a.get('bis_s')} s — {a.get('beschreibung') or ''}")
    n = len(rec.get("abschnitte") or [])
    lines += ["", f"Antworte mit GENAU {n} Einträgen in abschnitte (nr 1 bis {n}, Reihenfolge wie oben) — auch wenn Abschnitte "
                  f"gleich aussehen, dann dieselben Werte wiederholen. Ein einzelner Eintrag für mehrere Abschnitte ist falsch."]
    return "\n".join(lines)


def telemetrie_anwenden(rec: dict, tele: dict | None, fenster_s: float = 2.0) -> tuple[dict, bool]:
    """Metadatenklassen in die Abschnitte: brennweite/perspektive_hoehe überschreiben (Quelle in felder_quelle),
    bewegungsart/haltung ergänzen. Liefert (Datensatz, geändert?); ohne Telemetrie unverändert."""
    if not tele or tele.get("quelle") in (None, "keine"):
        return rec, False
    quelle: dict[str, str] = {}
    neu = []
    geaendert = False
    for a in rec.get("abschnitte") or []:
        b = dict(a)
        if tele.get("brennweitenklasse") and "brennweite" in b:
            quelle["brennweite"] = str(tele["quelle"])
            geaendert |= b.get("brennweite") != tele["brennweitenklasse"]
            b["brennweite"] = tele["brennweitenklasse"]
        if tele.get("perspektive_hoehe") and "perspektive_hoehe" in b:
            quelle["perspektive_hoehe"] = str(tele["quelle"])
            geaendert |= b.get("perspektive_hoehe") != tele["perspektive_hoehe"]
            b["perspektive_hoehe"] = tele["perspektive_hoehe"]
        w = abschnitt_werte(tele, float(b.get("von_s", 0)), float(b.get("bis_s", 0)), fenster_s)
        for k in ("bewegungsart", "haltung"):
            if w.get(k) is not None:
                geaendert |= b.get(k) != w[k]
                b[k] = w[k]
        neu.append(b)
    out = {**rec, "abschnitte": neu}
    if quelle:
        geaendert |= rec.get("felder_quelle") != quelle
        out["felder_quelle"] = quelle
    return out, geaendert


def _cache_schreiben(charge, rec: dict) -> None:
    """Clip-Datensatz atomar in den Cache (ohne ``_``-Schlüssel)."""
    cache_dir = Path(charge.autocut) / CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{rec['fingerprint']}.json"
    charge.assert_writable(cache_file)
    persist = {k: v for k, v in rec.items() if not k.startswith("_")}
    part = cache_file.with_name(cache_file.name + ".part")
    part.write_text(json.dumps(persist, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(part, cache_file)
```

`index_sections_clip` — Signatur und drei Stellen (`...` steht für unveränderten Code dazwischen):

```python
def index_sections_clip(charge, rec: dict, client, cfg: dict, system_prompt: str, force: bool = False, describe=describe_sections,
                        telemetrie: dict | None = None) -> dict:
    ...
    scfg = cfg["index_sections"]
    icfg = cfg["index"]
    fenster_s = float((cfg.get("telemetrie") or {}).get("fenster_s", 2.0))
    max_sections = int(scfg.get("max_sections", 5))
    if not force and not needs_sections(rec, max_sections):
        neu, geaendert = telemetrie_anwenden(rec, telemetrie, fenster_s)
        if geaendert:
            _cache_schreiben(charge, neu)
        return {**neu, "_cache": True}
    ...
    meta_text = section_meta_text({**rec, "abschnitte": abs_}, telemetrie)
    ...
    out = {**rec, "abschnitte": merged, "abschnittsbogen": str(sheet), "warnungen": warnungen,
           "nachlauf": {...}}
    out, _ = telemetrie_anwenden(out, telemetrie, fenster_s)
    _cache_schreiben(charge, out)
    return {**out, "_cache": False}
```
(Die bisherigen Zeilen `cache_dir = …` bis `os.replace(part, cache_file)` am Ende entfallen zugunsten von `_cache_schreiben`.)

`index_sections` — Telemetrie laden, je Clip übergeben, zählen. Nach `usage_sum = …` und vor `ex = ThreadPoolExecutor(…)`:

```python
    tele = telemetrie_laden(Path(charge.autocut))
    mit_tele = 0
```

Die Zeile `futs = {ex.submit(index_sections_clip, charge, c, client, cfg, prompt, force): c for c in todo}` ersetzen durch:

```python
        futs = {}
        for c in todo:
            t = finden(tele, str(c["path"]))
            mit_tele += int(t is not None)
            futs[ex.submit(index_sections_clip, charge, c, client, cfg, prompt, force, telemetrie=t)] = c
```

Die beiden Schlussblöcke ersetzen durch:

```python
    new_clips = [results.get(str(c["path"]), c) for c in clips]
    out = {**index, "clips": new_clips, "nachlauf": {"erstellt_am": _dt.datetime.now().isoformat(timespec="seconds"),
                                                     "anzahl": len(results), "cache_treffer": hits, "usage_summe": usage_sum,
                                                     "reparaturen": reparaturen, "fehler": errors, "mit_telemetrie": mit_tele}}
    charge.write_json("broll_index.json", out)
    return {"anzahl": len(results), "cache_treffer": hits, "fehler": errors, "usage_summe": usage_sum,
            "reparaturen": reparaturen, "uebersprungen": len(clips) - len(todo), "mit_telemetrie": mit_tele}
```

- [ ] **Step 4: CLI `autocut_index_sections.py`**

Import `from niro_autocut.telemetrie import finden, laden as telemetrie_laden`. Nach der Kostenzeile (vor `if args.dry_run`):

```python
        tele = telemetrie_laden(ch.autocut)
        mit_tele = sum(1 for c in todo if finden(tele, str(c["path"])))
        print(f"Telemetrie: {mit_tele} von {len(todo)} Clips" + ("" if mit_tele else
              " — erst scripts/autocut_telemetrie.py ausführen, dann kommen Brennweite und Perspektive Höhe aus den Metadaten.") + "\n")
```
In `zeilen` nach der Token-Zeile: `f"Telemetrie genutzt: {out['mit_telemetrie']} Clips (brennweite/perspektive_hoehe aus Metadaten, bewegungsart/haltung je Abschnitt)"`.

- [ ] **Step 5: Doku**

WORKFLOW-AutoCut.md, Abschnitt „Ablauf Stufe 2b": ergänzen — „Liegt `telemetrie.json` vor (`autocut_telemetrie.py`), bekommt der
Abschnittsbogen eine Kontextzeile mit KB-Brennweite, Pitch, Haltung und Bewegungsart je Abschnitt; nach der Antwort setzt der Code
`brennweite` und `perspektive_hoehe` aus den Metadaten fest (`felder_quelle` im Datensatz) und ergänzt je Abschnitt `bewegungsart`
und `haltung`. Cache-Treffer bekommen die Felder ohne API-Aufruf. Ohne Telemetrie bleibt alles wie bisher; `--dry-run` zeigt die Zahl."
prompts/index-sections.md, nach Regel 3 (Unsicherheit): „Steht eine Zeile „Kamera-Telemetrie (gemessen …)" im Hintergrund, sind KB-Brennweite
und Pitch gemessen — brennweite und perspektive_hoehe trotzdem nach Schema ausfüllen (das Schnittprogramm ersetzt sie durch die
Messwerte); die Bewegungsart der Kamera hilft, Motivbewegung von Kamerabewegung zu trennen."

- [ ] **Step 6: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_index_sections.py tests/test_docs.py -q`
Expected: alle bestehen

- [ ] **Step 7: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/src/niro_autocut/index_sections.py tools/autocut/scripts/autocut_index_sections.py tools/autocut/tests/test_index_sections.py tools/autocut/WORKFLOW-AutoCut.md tools/autocut/prompts/index-sections.md && git commit -q -m "feat(autocut): Stufe 2b nutzt Telemetrie — Kontextzeile, brennweite/perspektive_hoehe aus Metadaten, bewegungsart/haltung je Abschnitt

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Feinschnitt 6d — Stabilisieren nur bei Bedarf (`feinschnitt_bauen.py`-Vorlage)

**Files:**
- Modify: `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py` (Imports, `BROLL`-Kommentar, `plan()`, `bericht()`, `bauen()`)
- Modify: `tools/autocut/vorlagen/README.md`, `tools/autocut/WORKFLOW-AutoCut.md` (6d)
- Test: `tools/autocut/tests/test_vorlagen_telemetrie.py` (Syntax + Textprüfung der Vorlage; die reine Logik ist in Task 4 getestet)

**Interfaces:**
- Consumes: Task 4 (`telemetrie.laden`, `finden`, `stabil_vorschlag`), `charge.load_config`
- Produces: `v3_meta[*]["stabil"]`, `["stabil_grund"]`, `["roll_grad"]`; `feinschnitt.json` → `plan_v3` mit diesen Feldern, `stabilisiert[shot]` = True/False/None (None = übersprungen)

- [ ] **Step 1: Failing Test schreiben**

```python
# tools/autocut/tests/test_vorlagen_telemetrie.py
"""6d-Vorlage: kompiliert, nutzt stabil_vorschlag, dokumentiert die 7. BROLL-Spalte, Stabilize nur für ausgewählte Shots."""
from __future__ import annotations

import py_compile
from pathlib import Path

VORLAGE = Path(__file__).resolve().parents[1] / "vorlagen" / "feinschnitt" / "feinschnitt_bauen.py"
README = VORLAGE.parents[1] / "README.md"


def test_vorlage_kompiliert_und_nutzt_telemetrie():
    py_compile.compile(str(VORLAGE), doraise=True)
    text = VORLAGE.read_text(encoding="utf-8")
    assert "from niro_autocut import telemetrie as TM" in text
    assert "TM.stabil_vorschlag(" in text and "TM.finden(" in text and "TM.laden(" in text
    assert "stabil_hand" in text and '"stabil_grund"' in text
    assert 'if not m["stabil"]' in text                      # Stabilize() nur für ausgewählte Shots


def test_readme_nennt_die_spalte():
    assert "stabil" in README.read_text(encoding="utf-8") and "telemetrie.json" in README.read_text(encoding="utf-8")
```

- [ ] **Step 2: Test laufen lassen — Fehlschlag erwartet**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_vorlagen_telemetrie.py -q`
Expected: `2 failed` (Texte fehlen)

- [ ] **Step 3: Vorlage ändern**

Imports (nach `from niro_autocut.timeline_model import Item, MarkerSpec`):

```python
from niro_autocut import telemetrie as TM  # noqa: E402
from niro_autocut.charge import load_config  # noqa: E402
```

Nach `FPS = 25 …`:

```python
TELE = TM.laden(AC)                      # _intern/autocut/telemetrie.json (autocut_telemetrie.py); leer = Standard stabilisieren
TCFG = load_config(CH)["telemetrie"]
```

`BROLL`-Kommentar und Typ:

```python
# --- V3: B-Roll (Shot aus broll_auswahl.json, Versatz im Shot [Timeline-Frames bei 100 %], Länge, Record-In, Beat, 50 %[, stabil]) --
# Versatz + genutzte Länge (bei 50 % die halbe Länge) müssen in der Auswahl des Users liegen — kürzen ja, nie verlängern.
# 7. Spalte optional: True/False erzwingt Stabilize() bzw. lässt es aus; weggelassen = Vorschlag aus telemetrie.json
# (hand und wackeln > telemetrie.ruhig_max_px → stabilisieren; stativ/gimbal → nicht; ohne Telemetrie → stabilisieren).
BROLL: list[tuple] = [
    # (10, 27, 54, 345, "4", True),          # Shot 10 ab Frame 27 seiner Auswahl, 54 Frames lang, Record 345, Beat #4, 50 %
    # (11, 0, 40, 400, "5", False, False),   # … und ausdrücklich nicht stabilisieren
]
```

In `plan()` die V3-Schleife:

```python
    for eintrag in sorted(BROLL, key=lambda x: x[3]):
        nr, off, n, rec, beat, langsam, *rest = eintrag
        stabil_hand = rest[0] if rest else None
        s = shots.get(nr)
        if s is None:
            fehler.append(f"S{nr:02d}: Shot fehlt in broll_auswahl.json")
            continue
        faktor = s["clip_fps"] / FPS
        if langsam and s["clip_fps"] < 2 * FPS:
            fehler.append(f"S{nr:02d}: 50 % bei {s['clip_fps']:g}-fps-Quelle — Bilder stünden doppelt (Zeitlupe nur ab {2 * FPS} fps)")
        genutzt = n / 2 if langsam else n  # Timeline-Frames bei 100 % aus der Auswahl
        if off < 0 or off + genutzt > s["dauer_f"] + 1e-9:
            fehler.append(f"S{nr:02d}: Versatz {off} + genutzt {genutzt} > Auswahl {s['dauer_f']} — verlängert!")
        src_in = int(round((s["left_offset_f"] + off) * faktor))
        src_out = src_in + int(round(n * faktor))  # angehängt bei 100 %; SetSpeed 50 halbiert den Quellbereich
        quelle_genutzt = int(round(n if langsam else n * faktor))
        tele_rec = TM.finden(TELE, s["datei"])
        vorschlag, grund = TM.stabil_vorschlag(src_in / s["clip_fps"], (src_in + quelle_genutzt) / s["clip_fps"], tele_rec, TCFG)
        stabil = vorschlag if stabil_hand is None else bool(stabil_hand)
        if stabil_hand is not None and stabil != vorschlag:
            grund += " — von Hand überstimmt"
        v3.append(Item("V3", s["datei"], src_in, src_out, rec, rec + n, True, beat, "broll", True))
        v3_meta.append({"shot": nr, "clip": s["clip"], "rec_in_f": rec, "dauer_f": n, "langsam": langsam, "src_in_f": src_in,
                        "quelle_genutzt_50p": quelle_genutzt,
                        "auswahl_50p": [int(round(s["left_offset_f"] * faktor)), int(round((s["left_offset_f"] + s["dauer_f"]) * faktor))],
                        "stabil": stabil, "stabil_grund": grund,
                        "roll_grad": (tele_rec or {}).get("roll_grad")})
```

In `bericht(p)` am Ende:

```python
    print(f"Stabilisierung ({len(TELE)} Clips in telemetrie.json):")
    for m in p["v3_meta"]:
        roll = m.get("roll_grad")
        schief = f"  schief {abs(roll):.1f}°".replace(".", ",") if roll is not None and abs(roll) > 2.0 else ""
        print(f"  S{m['shot']:02d} {'stabilisieren' if m['stabil'] else 'lassen       '}  {m['stabil_grund']}{schief}")
```

In `bauen()` die Stabilisier-Schleife:

```python
        # Stabilisieren nach dem Tempo (Analyse über den tatsächlich genutzten Quellbereich) — nur wo der Plan es vorsieht (Telemetrie)
        for n_, m in enumerate(p["v3_meta"], 1):
            t0, shot = dt.datetime.now(), f"S{m['shot']:02d}"
            if not m["stabil"]:
                stab[shot] = None
                print(f"  Stabilisierung {n_}/{len(p['v3_meta'])} {shot}: übersprungen ({m['stabil_grund']})", flush=True)
                continue
            stab[shot] = bool(RA._safe(v3_items[m["rec_in_f"]].Stabilize, False))
            print(f"  Stabilisiert {n_}/{len(p['v3_meta'])} {shot}: {stab[shot]} ({(dt.datetime.now() - t0).total_seconds():.1f} s)", flush=True)
        out["stabilisiert"] = stab
```

- [ ] **Step 4: Doku**

`vorlagen/README.md` (Abschnitt zu `feinschnitt_bauen.py` bzw. Übersichtstabelle): „`BROLL` hat eine optionale 7. Spalte `stabil`
(True/False); ohne sie kommt der Vorschlag aus `_intern/autocut/telemetrie.json` (`autocut_telemetrie.py` vorher laufen lassen):
Stativ/Gimbal bleiben unstabilisiert, Handkamera mit `wackeln` > `telemetrie.ruhig_max_px` wird stabilisiert. Der Probelauf druckt je
Shot Vorschlag und Grund; `roll_grad` > 2° erscheint als „schief"."
WORKFLOW 6d („### 6d Feinschnitt-Bau", Punkt 2, Zeile V3): „**V3** B-Roll: bei 100 % anhängen → `RetimeProcess` Nearest → `SetSpeed` 50 %
→ `Stabilize()` nur für Shots mit `stabil` (Vorschlag aus `telemetrie.json`, Spalte 7 in `BROLL` überstimmt)."

- [ ] **Step 5: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_vorlagen_telemetrie.py tests/test_docs.py -q`
Expected: alle bestehen

- [ ] **Step 6: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py tools/autocut/vorlagen/README.md tools/autocut/WORKFLOW-AutoCut.md tools/autocut/tests/test_vorlagen_telemetrie.py && git commit -q -m "feat(autocut): 6d-Vorlage stabilisiert B-Roll nur bei Bedarf (Telemetrie-Vorschlag, BROLL-Spalte stabil)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: Doku-Abschluss, Aftermovie-Sonderfall, Spec-Status, Gesamtlauf

**Files:**
- Modify: `tools/autocut/WORKFLOW-AutoCut.md` (Sonderfall Aftermovie: Schritt „Ruhe"; Stufen-Tabelle im Kopf: Zeile „Telemetrie"; „Bekannte Fallen": ein Punkt), `tools/autocut/README.md` (Grundsätze: keine neue Abhängigkeit), `docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md` (Status, Berichtspfad)

- [ ] **Step 1: WORKFLOW — Kopf-Tabelle und Sonderfall**

Kopf-Tabelle (nach der Zeile „Kanten"):
```
| „Telemetrie" | – | Gyro/Beschleunigung/Brennweite je Clip aus der Sony-rtmd-Spur (optischer Rückfall) → `telemetrie.json` + Bericht: wackeln, ruhige Fenster, Haltung, Bewegungsart, Brennweiten-/Perspektivklasse; Grundlage für Sichtung, 2b, 6d |
```
Sonderfall Aftermovie, Absatz mit „Ruhe-Regel": `_intern/skripte/ruhe.py`, `ruhe_fenster.py` durch
„`autocut_telemetrie.py "<Charge>"` (Abschnitt „Telemetrie": `ruhige_fenster`, `wackeln`, `haltung`, `bewegungsart` je Clip in
`_intern/autocut/telemetrie.json`; Hochzeitszauber lief noch mit `_intern/skripte/ruhe.py`/`ruhe_fenster.py`, optisch)" ersetzen.
„Bekannte Fallen", neuer Punkt: „**Telemetrie:** Lesen der Datenspur kostet die ganze Datei (≈ 300 MB/s übers NAS) — Läufe über ganze
Drehs im Hintergrund starten; Cache je Clip. Der Gyro sieht die Handbewegung, IBIS glättet das Bild — deshalb `px_faktor` je Kamera
aus der Kalibrierung, nie 1,0 raten. FX3-Beschleunigung misst 1,15 g: Gates relativ zum Clip-Median."

- [ ] **Step 2: Spec-Status**

Kopfzeile des Spec: `Status: umgesetzt 21.09.2026 (Plan docs/superpowers/plans/2026-09-21-autocut-telemetrie.md); Bericht liegt unter
Ergebnisse/Rohschnitt/telemetrie.md (Schreibbereich von Charge.open_basis), nicht unter Ergebnisse/Sortierung/.`

- [ ] **Step 3: Gesamtlauf**

Run: `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q`
Expected: alles grün; Anzahl der Tests in der Task-Meldung nennen.

- [ ] **Step 4: Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git add tools/autocut/WORKFLOW-AutoCut.md tools/autocut/README.md docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md && git commit -q -m "docs(autocut): Telemetrie im Workflow (Kopf-Tabelle, Aftermovie-Sonderfall, Fallen), Spec-Status

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
