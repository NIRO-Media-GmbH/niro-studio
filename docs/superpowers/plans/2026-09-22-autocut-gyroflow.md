# Gyroflow-Stabilisierung für B-Roll — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die im Feinschnitt genutzten B-Roll-Shots werden mit Gyroflow stabilisiert — über 8-KB-bis-MB-Sidecars neben den Medien und das OFX-Plugin im Schnitt, ohne gerenderte Zweitmedien.

**Architecture:** Ein neues Modul `niro_autocut.gyroflow` ruft die Gyroflow-CLI headless auf und legt je genutzter Quelldatei eine `.gyroflow`-Projektdatei neben die Mediendatei (`--export-project 2`, mit Gyrodaten, damit sie Pfadwechsel übersteht). Das Glättungs-Preset kommt aus `telemetrie.json` (`haltung`, `wackeln`); Gyroflows `max_zoom` deckelt **Gyroflows eigenen** Beschnitt. **Korrektur 23.09.:** Die ursprüngliche Fassung dieses Plans behauptete, das halte der Brennweitenregel ihre 1,25× frei — falsch, `digitalzoom()` lässt bis `digitalzoom_max` (1,5) zu, Gesamtzoom also bis 1,8×. Siehe Spec Abschnitt 4. Angewendet wird im 6d-Bau per Fusion-Comp je V3-Clip, damit die Readback-Kette gültig bleibt.

**Tech Stack:** Python 3.12 (`tools/autocut/venv`), Gyroflow-CLI 1.6.1, Gyroflow-OFX in DaVinci Resolve Studio 21.1, pytest 9.1. Keine neue Abhängigkeit.

**Spec:** `docs/superpowers/specs/2026-09-22-autocut-gyroflow-design.md`

## Global Constraints

- **Python:** `tools/autocut/venv/bin/python`. Keine neue Abhängigkeit — nur Standardbibliothek plus was schon da ist.
- **Tests:** `cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q`. Tests dürfen **nie** die echte Gyroflow-CLI oder echtes Drehmaterial brauchen.
- **Gyroflow-CLI:** `/Applications/Gyroflow.app/Contents/MacOS/gyroflow`, konfigurierbar über `gyroflow.cli`.
- **Export-Typ:** immer `--export-project 2` (mit Gyrodaten). Typ 1 und 3 werden nicht für Sidecars verwendet.
- **Deckel-Ungleichung:** `max_zoom ≤ digitalzoom_max / digitalzoom_faktor × 100`, mit den Standardwerten also **≤ 120**. **Korrektur 23.09.: Das ist keine Zusage über den Gesamtzoom** — die Brennweitenregel nimmt bis `digitalzoom_max` (1,5), nicht nur `digitalzoom_faktor`. Der Deckel begrenzt nur Gyroflow; die Einspeisung des Gyroflow-Beschnitts in die Regel ist vereinbart und steht aus.
- **Config-Pfade:** `cfg["gyroflow"][…]` für das Neue; `cfg["telemetrie"]["digitalzoom_max"]` und `cfg["telemetrie"]["digitalzoom_faktor"]` für die Grenzen (sie liegen unter `telemetrie:`, nicht auf oberster Ebene).
- **Schreibschutz:** `Charge.assert_writable` wird **nicht** aufgeweicht. Sidecars neben den Medien laufen ausschließlich über `sidecar_pfad()` (Task 3).
- **Resolve:** Standard nur lesen. Schreibend nur im Projekt, das der User in derselben Session freigibt, nur anhängend, nie während der Wiedergabe.
- **Sprache:** Docstrings, Kommentare, Feldnamen und Berichte auf Deutsch — wie im übrigen `niro_autocut`.
- **Commits:** je Task einer, Nachricht auf Deutsch im Stil des Repos (`feat(autocut): …`, `docs(autocut): …`), abgeschlossen mit `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

---

### Task 1: Verifikation — Gate vor jedem Bau

Die Spec nennt fünf offene Punkte; drei brauchen laufendes Resolve. **Vor diesem Task wird nichts implementiert.** Ergebnis ist ein Nachtrag in der Spec, kein Code. Fällt Punkt 4 negativ aus, ändert sich Task 9 — fällt Punkt 1 negativ aus, ändert sich der Umfang.

**Files:**
- Modify: `docs/superpowers/specs/2026-09-22-autocut-gyroflow-design.md` (Abschnitt „Offene Punkte" durch „Befund 1" ersetzen)

**Interfaces:**
- Consumes: nichts
- Produces: die Entscheidung, ob Task 9 als Fusion-Comp gebaut wird, und die Tool-Kennung des Gyroflow-OFX als Zeichenkette für Task 9

- [ ] **Step 1: Plugin erneuern (Handgriff des Users)**

Den User bitten: Gyroflow öffnen → Panel „Video editor plugins" → DaVinci-Resolve-Plugin installieren/aktualisieren. Danach Resolve starten und unter Einstellungen → Video-Plugins prüfen, dass `Gyroflow.ofx.bundle` aktiv ist. Ohne diesen Schritt ist das Plugin v1.3.0 von November 2023 und trägt ein Quarantäne-Flag.

Prüfen:

```bash
/usr/libexec/PlistBuddy -c "Print :CFBundleVersion" /Library/OFX/Plugins/Gyroflow.ofx.bundle/Contents/Info.plist
```

Erwartet: eine Version **über** 1.3.0. Bleibt es 1.3.0, hat der Handgriff nicht gewirkt — nicht weitermachen.

- [ ] **Step 2: Tool-Kennung in Fusion abfragen**

Mit laufendem Resolve und einem geöffneten Projekt über den MCP `run_script`:

```python
fusion = resolve.Fusion()
tools = fusion.GetToolList()
result = sorted(n for n in (tools.values() if hasattr(tools, "values") else tools) if "gyro" in str(n).lower())
```

Erwartet: mindestens ein Eintrag, der `gyroflow` enthält (OFX-Tools tragen üblicherweise ein Präfix wie `ofx.xyz.gyroflow…`). Kommt nichts zurück, ist das Plugin in Resolve nicht aktiv — zurück zu Step 1.

Die gefundene Kennung notieren; Task 9 braucht sie wörtlich.

- [ ] **Step 3: AddFusionComp + AddTool + SetInput an einem Wegwerf-Clip**

Nur in einem Projekt, das der User in dieser Session ausdrücklich freigegeben hat. Vorher den Projektnamen lesen, nennen und mit der Freigabe abgleichen.

```python
tl = project.GetCurrentTimeline()
item = tl.GetItemListInTrack("video", 1)[0]
comp = item.AddFusionComp()
tool = comp.AddTool("<Kennung aus Step 2>")
namen = sorted(tool.GetInputList().keys()) if tool else []
result = {"tool": bool(tool), "inputs": namen}
```

Erwartet: `tool` = `True` und eine Input-Liste, in der ein Projektdatei-Parameter erkennbar ist. Den Namen dieses Parameters notieren. Danach den Fusion-Comp wieder entfernen (eigenes Objekt derselben Session).

- [ ] **Step 4: Tempo-Test — das eigentliche Risiko**

Einen B-Roll-Shot zweimal auf eine Wegwerf-Timeline legen: einmal 100 %, einmal mit `SetSpeed` 50 %. Auf beide dasselbe Sidecar setzen. Je ein Standbild aus der Mitte beider Instanzen ziehen und vergleichen.

Erwartet bei Erfolg: beide Instanzen zeigen dieselbe Stabilisierung, die Zeitlupe nur langsamer. Bei Misserfolg driftet oder springt die 50-%-Instanz.

**Wenn der Test fehlschlägt:** in der Spec festhalten, dass Zeitlupen-Shots beim heutigen Weg (`Stabilize()` + DRT-Modus) bleiben, und Task 9 so bauen, dass Shots mit `tempo50` übersprungen werden. Der Rest des Plans bleibt unverändert gültig.

- [ ] **Step 5: `adaptive_zoom_fovs` dekodieren (ohne Resolve)**

```bash
cd /private/tmp && cp "<ein a7-IV- oder FX3-Clip>" probe.MP4 \
  && /Applications/Gyroflow.app/Contents/MacOS/gyroflow probe.MP4 --export-project 3 -f \
  && python3 -c "import json; d=json.load(open('probe.gyroflow')); v=d['gyro_source']['adaptive_zoom_fovs']; print(type(v).__name__, str(v)[:120])"
```

Der Wert ist kodiert. Versuchen, ihn zu dekodieren (base85/zlib sind die naheliegenden Kandidaten). Gelingt es, die Dekodierung für Task 6 notieren. **Gelingt es nicht, ist das kein Blocker** — Task 6 hat den dokumentierten Rückfall auf den Deckelwert.

- [ ] **Step 6: DJI-Gyro prüfen (ohne Resolve)**

Je einen Mavic- und einen Avata-Clip durch `--export-project 2` schicken und in der Ausgabe nach `detected_source` sehen. Findet Gyroflow deren Gyro, kommen sie in den Umfang; sonst bleiben sie beim optischen Weg.

- [ ] **Step 7: Befund in die Spec schreiben und committen**

Den Abschnitt „Offene Punkte — zuerst zu klären, mit laufendem Resolve" durch „Befund 1 (Datum)" ersetzen: je Punkt das Ergebnis, die notierte Tool-Kennung, der Parametername, das Tempo-Urteil.

```bash
cd "/Users/jansantos/NIRO Studio"
git add docs/superpowers/specs/2026-09-22-autocut-gyroflow-design.md
git commit -m "docs(autocut): Gyroflow-Spec — Befund der Verifikation (OFX in Fusion, Tempo, Zoom-Readback)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Preset aus der Telemetrie und Deckel-Prüfung

**Files:**
- Create: `tools/autocut/src/niro_autocut/gyroflow.py`
- Create: `tools/autocut/tests/test_gyroflow.py`
- Modify: `tools/autocut/defaults.yaml` (neuer Block `gyroflow:` ans Ende)

**Interfaces:**
- Consumes: nichts aus früheren Tasks
- Produces:
  - `CLI_STANDARD: str`
  - `pruefe_deckel(cfg: dict) -> None` — wirft `AutoCutError`, wenn ein `max_zoom` die Ungleichung verletzt
  - `preset_fuer(rec: dict, cfg: dict) -> dict` — Telemetrie-Datensatz → Gyroflow-Preset
  - `preset_hash(preset: dict) -> str` — 12 Hex-Zeichen

- [ ] **Step 1: Config-Block in `defaults.yaml` anhängen**

```yaml
gyroflow:                   # Gyroflow-Stabilisierung für B-Roll (Spec 2026-09-22): Sidecar neben der Mediendatei,
                            # angewendet per OFX im Schnitt — kein Render, keine zweite Medienhaltung.
  cli: "/Applications/Gyroflow.app/Contents/MacOS/gyroflow"
  zeitueberschreitung_s: 300   # je Clip; Lesen der Gyrospur kostet die ganze Datei (≈ 300 MB/s übers NAS)
  # Glättung je Haltung aus telemetrie.json. Startwerte 22.09., am ersten echten Durchlauf zu prüfen.
  glaettung: {stativ: 0.2, gimbal: 0.4, hand: 0.7}
  # Gyroflows eigene Zoom-Obergrenze in Prozent (100 = kein Beschnitt). Muss die Ungleichung
  # max_zoom ≤ digitalzoom_max / digitalzoom_faktor × 100 einhalten (1,5 / 1,25 × 100 = 120);
  # pruefe_deckel() bricht sonst ab. KEINE Zusage über den Gesamtzoom — siehe Korrektur oben.
  max_zoom: {stativ: 105, gimbal: 110, hand: 120}
```

- [ ] **Step 2: Die failing tests schreiben**

`tools/autocut/tests/test_gyroflow.py`:

```python
"""gyroflow.py — Preset aus der Telemetrie, Deckel-Prüfung, Sidecar-Pfad, Clip-Export, Charge-Lauf (Spec 2026-09-22)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from niro_autocut import gyroflow as G
from niro_autocut.charge import AutoCutError

CFG = {
    "gyroflow": {
        "cli": "/Applications/Gyroflow.app/Contents/MacOS/gyroflow",
        "zeitueberschreitung_s": 300,
        "glaettung": {"stativ": 0.2, "gimbal": 0.4, "hand": 0.7},
        "max_zoom": {"stativ": 105, "gimbal": 110, "hand": 120},
    },
    "telemetrie": {"digitalzoom_faktor": 1.25, "digitalzoom_max": 1.5},
}


def test_deckel_haelt_die_ungleichung_ein():
    G.pruefe_deckel(CFG)   # 120 ≤ 1.5 / 1.25 × 100 = 120 — Gleichheit ist erlaubt


def test_deckel_zu_hoch_bricht_ab():
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["max_zoom"]["hand"] = 130
    with pytest.raises(AutoCutError, match="max_zoom"):
        G.pruefe_deckel(cfg)


def test_preset_nimmt_glaettung_und_deckel_der_haltung():
    p = G.preset_fuer({"haltung": "hand"}, CFG)
    assert p["version"] == 2
    st = p["stabilization"]
    assert st["max_zoom"] == 120
    assert {"name": "smoothness", "value": 0.7} in st["smoothing_params"]


def test_preset_ohne_haltung_nimmt_die_vorsichtigste_stufe():
    p = G.preset_fuer({"haltung": None}, CFG)
    assert p["stabilization"]["max_zoom"] == 105
    assert {"name": "smoothness", "value": 0.2} in p["stabilization"]["smoothing_params"]


def test_preset_hash_haengt_am_inhalt_nicht_an_der_reihenfolge():
    a = G.preset_fuer({"haltung": "gimbal"}, CFG)
    b = json.loads(json.dumps(a))
    assert G.preset_hash(a) == G.preset_hash(b)
    assert len(G.preset_hash(a)) == 12
    assert G.preset_hash(a) != G.preset_hash(G.preset_fuer({"haltung": "hand"}, CFG))
```

- [ ] **Step 3: Tests laufen lassen, Fehlschlag bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow.py -q
```

Erwartet: FAIL mit `ModuleNotFoundError: No module named 'niro_autocut.gyroflow'`.

- [ ] **Step 4: `gyroflow.py` anlegen**

```python
"""Gyroflow-Stabilisierung für B-Roll (Spec 2026-09-22): Projektdatei je genutzter Quelldatei neben die Mediendatei,
angewendet per OFX im Schnitt. Kein Render, keine zweite Medienhaltung.

Das Glättungs-Preset kommt aus der Telemetrie (``haltung``), nicht aus einem Festwert. Gyroflows eigener Zoom wird über
``max_zoom`` (Prozent, 100 = kein Beschnitt) so gedeckelt, dass der Brennweitenregel ihre ``digitalzoom_faktor``
garantiert bleiben — deshalb braucht es keine Rückkopplung zwischen beiden Beschnitten.
"""
from __future__ import annotations

import hashlib
import json

from .charge import AutoCutError

CLI_STANDARD = "/Applications/Gyroflow.app/Contents/MacOS/gyroflow"
HALTUNG_VORSICHTIG = "stativ"   # Rückfall ohne Telemetrie: wenig glätten, wenig Rand nehmen


def pruefe_deckel(cfg: dict) -> None:
    """Bricht ab, wenn ein ``max_zoom`` der Brennweitenregel ihren Sollzoom nehmen würde.

    ``max_zoom`` ≤ ``digitalzoom_max`` / ``digitalzoom_faktor`` × 100. Wer ``digitalzoom_*`` ändert, muss ``max_zoom``
    mitziehen — sonst stecken beide Beschnitte zusammen über ``digitalzoom_max``."""
    tele = cfg.get("telemetrie") or {}
    faktor, obergrenze = tele.get("digitalzoom_faktor"), tele.get("digitalzoom_max")
    if not faktor or not obergrenze:
        raise AutoCutError("telemetrie.digitalzoom_faktor und telemetrie.digitalzoom_max fehlen in der Config.")
    grenze = float(obergrenze) / float(faktor) * 100.0
    for haltung, wert in ((cfg.get("gyroflow") or {}).get("max_zoom") or {}).items():
        if float(wert) > grenze + 1e-9:
            raise AutoCutError(
                f"gyroflow.max_zoom[{haltung}] = {wert} überschreitet {grenze:.0f} "
                f"(= digitalzoom_max {obergrenze} / digitalzoom_faktor {faktor} × 100).\n"
                f"Entweder max_zoom senken oder telemetrie.digitalzoom_max anheben.")


def preset_fuer(rec: dict, cfg: dict) -> dict:
    """Telemetrie-Datensatz → Gyroflow-Preset. Ohne ``haltung`` gilt die vorsichtigste Stufe."""
    gf = cfg.get("gyroflow") or {}
    haltung = rec.get("haltung") or HALTUNG_VORSICHTIG
    glaettung = (gf.get("glaettung") or {}).get(haltung)
    max_zoom = (gf.get("max_zoom") or {}).get(haltung)
    if glaettung is None or max_zoom is None:
        raise AutoCutError(f"gyroflow.glaettung/max_zoom kennen die Haltung {haltung!r} nicht.")
    return {"version": 2,
            "stabilization": {"smoothing_params": [{"name": "smoothness", "value": float(glaettung)}],
                              "max_zoom": float(max_zoom)}}


def preset_hash(preset: dict) -> str:
    """12 Hex-Zeichen über den Preset-Inhalt; hängt nicht an der Schlüsselreihenfolge."""
    return hashlib.sha1(json.dumps(preset, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
```

- [ ] **Step 5: Tests laufen lassen, Erfolg bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow.py -q
```

Erwartet: 5 passed.

Der Test `test_deckel_haelt_die_ungleichung_ein` prüft dabei den Gleichheitsfall (120 = 120) — genau die Standardwerte aus `defaults.yaml`.

- [ ] **Step 6: Commit**

```bash
cd "/Users/jansantos/NIRO Studio"
git add tools/autocut/src/niro_autocut/gyroflow.py tools/autocut/tests/test_gyroflow.py tools/autocut/defaults.yaml
git commit -m "feat(autocut): Gyroflow-Preset aus der Telemetrie, max_zoom gegen die Brennweitenregel geprüft

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Sidecar-Pfad mit eigener Schreibregel

`Charge.assert_writable` erlaubt nur `_intern/autocut/`, `Ergebnisse/Rohschnitt/` und das Protokoll. Der Sidecar neben der Mediendatei fällt nicht darunter. Der Schutz wird **nicht** aufgeweicht — dieser eine Fall bekommt eine eigene, enge Regel.

**Files:**
- Modify: `tools/autocut/src/niro_autocut/gyroflow.py`
- Modify: `tools/autocut/tests/test_gyroflow.py`

**Interfaces:**
- Consumes: `AutoCutError` aus `.charge`
- Produces: `sidecar_pfad(video: str | Path, erlaubte_pfade: set[str]) -> Path`

- [ ] **Step 1: Die failing tests anhängen**

An `tools/autocut/tests/test_gyroflow.py` anhängen:

```python
def test_sidecar_liegt_neben_der_mediendatei(tmp_path: Path):
    v = tmp_path / "FX3_0001.MP4"
    v.write_bytes(b"x")
    p = G.sidecar_pfad(v, {str(v)})
    assert p == tmp_path / "FX3_0001.gyroflow"


def test_sidecar_verweigert_unbekannte_datei(tmp_path: Path):
    v = tmp_path / "FX3_0001.MP4"
    v.write_bytes(b"x")
    with pytest.raises(AutoCutError, match="nicht in telemetrie.json"):
        G.sidecar_pfad(v, set())


def test_sidecar_verweigert_fehlende_datei(tmp_path: Path):
    v = tmp_path / "gibtsnicht.MP4"
    with pytest.raises(AutoCutError, match="nicht gefunden"):
        G.sidecar_pfad(v, {str(v)})
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow.py -q -k sidecar
```

Erwartet: FAIL mit `AttributeError: module 'niro_autocut.gyroflow' has no attribute 'sidecar_pfad'`.

- [ ] **Step 3: `sidecar_pfad` implementieren**

In `gyroflow.py` ergänzen — `from pathlib import Path` oben mit aufnehmen:

```python
def sidecar_pfad(video: str | Path, erlaubte_pfade: set[str]) -> Path:
    """Pfad der ``.gyroflow``-Datei neben der Mediendatei — die einzige Stelle, an der außerhalb der Chargen-Ordner
    geschrieben wird.

    Enge Regel statt aufgeweichtem ``Charge.assert_writable``: geschrieben wird nur neben eine **existierende**
    Mediendatei, die unter genau diesem Pfad in ``telemetrie.json`` geführt ist. Die Endung ist immer ``.gyroflow``,
    der Stamm der der Mediendatei — ein Überschreiben von Material ist damit ausgeschlossen."""
    p = Path(video).expanduser().resolve()
    if str(p) not in {str(Path(e).expanduser().resolve()) for e in erlaubte_pfade}:
        raise AutoCutError(f"Sidecar verweigert: {p} ist nicht in telemetrie.json geführt.")
    if not p.is_file():
        raise AutoCutError(f"Sidecar verweigert: {p} nicht gefunden. Ist das NAS gemountet?")
    return p.with_suffix(".gyroflow")
```

- [ ] **Step 4: Tests laufen lassen, Erfolg bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow.py -q
```

Erwartet: 8 passed.

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio"
git add tools/autocut/src/niro_autocut/gyroflow.py tools/autocut/tests/test_gyroflow.py
git commit -m "feat(autocut): Sidecar-Pfad neben der Mediendatei mit eigener enger Schreibregel

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Clip-Export mit Cache

**Files:**
- Modify: `tools/autocut/src/niro_autocut/gyroflow.py`
- Modify: `tools/autocut/tests/test_gyroflow.py`

**Interfaces:**
- Consumes: `preset_fuer`, `preset_hash`, `sidecar_pfad` (Tasks 2–3); `fingerprint` aus `.media`
- Produces: `CACHE_DIR: str = "gyroflow"`; `clip_export(ch, video, rec, cfg, erlaubte_pfade, force=False) -> tuple[dict, bool]` — Datensatz und ob er aus dem Cache kam

Der Datensatz je Clip trägt: `path`, `clip`, `sidecar`, `kamera`, `haltung`, `preset_hash`, `fingerprint`, `exportiert_am`, `zoom_ist`, `zoom_gedeckelt`, `fehler`. `zoom_ist`/`zoom_gedeckelt` setzt erst Task 5 — hier bleiben sie `None`.

- [ ] **Step 1: Die failing tests anhängen**

Die Tests dürfen die echte CLI nicht aufrufen. Eine Attrappe als ausführbares Shell-Skript, das eine Sidecar-Datei schreibt:

```python
def _cli_attrappe(tmp_path: Path) -> str:
    """Ausführbare Attrappe: schreibt neben die Eingabedatei eine .gyroflow-Datei und zählt die Aufrufe."""
    p = tmp_path / "gyroflow_fake.sh"
    p.write_text(
        '#!/bin/sh\n'
        'echo "$@" >> "$(dirname "$1")/aufrufe.log"\n'
        'out="${1%.*}.gyroflow"\n'
        'printf \'{"version":2,"stabilization":{"max_zoom":120.0}}\' > "$out"\n',
        encoding="utf-8")
    p.chmod(0o755)
    return str(p)


def _charge(tmp_path: Path):
    from niro_autocut.charge import Charge
    root = tmp_path / "2026-09 Testdreh"
    (root / "_intern" / "autocut").mkdir(parents=True)
    (root / "Ergebnisse" / "Rohschnitt").mkdir(parents=True)
    return Charge(root=root, intern=root / "_intern", autocut=root / "_intern" / "autocut",
                  work=root / "_intern" / "autocut" / "work", ergebnisse=root / "Ergebnisse" / "Rohschnitt",
                  plaene=root / "Ergebnisse" / "O-Ton-Pläne", protokoll=root / "Protokoll.md", config=CFG)


def test_clip_export_schreibt_sidecar_neben_die_mediendatei(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)

    rec, aus_cache = G.clip_export(ch, v, {"haltung": "hand", "kamera": "FX3"}, cfg, {str(v)})

    assert aus_cache is False
    assert rec["fehler"] is None
    assert Path(rec["sidecar"]) == medien / "FX3_0001.gyroflow"
    assert (medien / "FX3_0001.gyroflow").is_file()
    assert "--export-project 2" in (medien / "aufrufe.log").read_text(encoding="utf-8")


def test_clip_export_nimmt_beim_zweiten_lauf_den_cache(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)

    G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})
    _, aus_cache = G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})

    assert aus_cache is True
    assert (medien / "aufrufe.log").read_text(encoding="utf-8").count("--export-project") == 1


def test_clip_export_misst_neu_wenn_sich_das_preset_aendert(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)

    G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})
    _, aus_cache = G.clip_export(ch, v, {"haltung": "gimbal"}, cfg, {str(v)})

    assert aus_cache is False


def test_clip_export_meldet_fehler_statt_abzubrechen(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    kaputt = tmp_path / "kaputt.sh"
    kaputt.write_text('#!/bin/sh\necho "kein Gyro gefunden" >&2\nexit 1\n', encoding="utf-8")
    kaputt.chmod(0o755)
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = str(kaputt)

    rec, _ = G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})

    assert rec["fehler"] and "kein Gyro" in rec["fehler"]
    assert rec["sidecar"] is None
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow.py -q -k clip_export
```

Erwartet: FAIL mit `AttributeError: module 'niro_autocut.gyroflow' has no attribute 'clip_export'`.

- [ ] **Step 3: `clip_export` implementieren**

In `gyroflow.py` ergänzen (`import datetime as _dt`, `import os`, `import subprocess` oben mit aufnehmen, sowie `from .media import fingerprint`):

```python
CACHE_DIR = "gyroflow"


def _cli_aufrufen(cli: str, video: Path, preset: dict, zeitlimit: float) -> None:
    """Gyroflow headless: Projektdatei schreiben, nicht rendern. Wirft AutoCutError mit der Fehlerausgabe."""
    befehl = [cli, str(video), "--export-project", "2", "--preset", json.dumps(preset), "-f"]
    try:
        erg = subprocess.run(befehl, capture_output=True, text=True, timeout=zeitlimit)
    except FileNotFoundError:
        raise AutoCutError(f"Gyroflow-CLI nicht gefunden: {cli}\nPfad in defaults.yaml unter gyroflow.cli prüfen.")
    except subprocess.TimeoutExpired:
        raise AutoCutError(f"Gyroflow hat {video.name} nach {zeitlimit:.0f}s nicht beendet "
                           f"(gyroflow.zeitueberschreitung_s). Liegt die Datei auf einem langsamen Laufwerk?")
    if erg.returncode != 0:
        raise AutoCutError((erg.stderr or erg.stdout or "").strip() or f"Gyroflow endete mit Code {erg.returncode}.")


def clip_export(ch, video, rec: dict, cfg: dict, erlaubte_pfade: set[str],
                force: bool = False) -> tuple[dict, bool]:
    """Sidecar je Quelldatei erzeugen; gibt den Datensatz und zurück, ob er aus dem Cache kam.

    Ein Fehler an einem Clip beendet den Lauf nicht — er landet als ``fehler`` im Datensatz, wie in der Telemetrie."""
    gf = cfg.get("gyroflow") or {}
    video = Path(video)
    preset = preset_fuer(rec, cfg)
    ph = preset_hash(preset)
    fp = fingerprint(video)
    cache = Path(ch.autocut) / CACHE_DIR / f"{fp}.json"

    if cache.exists() and not force:
        try:
            alt = json.loads(cache.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            alt = None
        if isinstance(alt, dict) and not alt.get("fehler") and alt.get("preset_hash") == ph \
                and alt.get("sidecar") and Path(alt["sidecar"]).is_file():
            alt["path"], alt["clip"] = str(video), video.stem
            return alt, True

    datensatz = {"path": str(video), "clip": video.stem, "sidecar": None, "kamera": rec.get("kamera"),
                 "haltung": rec.get("haltung"), "preset_hash": ph, "fingerprint": fp,
                 "exportiert_am": _dt.datetime.now().isoformat(timespec="seconds"),
                 "zoom_ist": None, "zoom_gedeckelt": None, "fehler": None}
    try:
        ziel = sidecar_pfad(video, erlaubte_pfade)
        _cli_aufrufen(gf.get("cli") or CLI_STANDARD, video, preset, float(gf.get("zeitueberschreitung_s") or 300))
        if not ziel.is_file():
            raise AutoCutError(f"Gyroflow meldete Erfolg, aber {ziel.name} fehlt.")
        datensatz["sidecar"] = str(ziel)
    except AutoCutError as e:
        datensatz["fehler"] = str(e)

    ch.assert_writable(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    teil = cache.with_name(f"{cache.name}.{os.getpid()}.part")
    teil.write_text(json.dumps(datensatz, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(teil, cache)
    return datensatz, False
```

- [ ] **Step 4: Tests laufen lassen, Erfolg bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow.py -q
```

Erwartet: 12 passed.

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio"
git add tools/autocut/src/niro_autocut/gyroflow.py tools/autocut/tests/test_gyroflow.py
git commit -m "feat(autocut): Gyroflow-Sidecar je Quelldatei mit Cache über Fingerprint und Preset-Hash

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Tatsächlich verbrauchten Zoom lesen

Nur für den Bericht — der Haushalt hält schon durch den Deckel aus Task 2. Deshalb ist der Rückfall hier vollwertig, kein Notbehelf.

**Files:**
- Modify: `tools/autocut/src/niro_autocut/gyroflow.py`
- Modify: `tools/autocut/tests/test_gyroflow.py`

**Interfaces:**
- Consumes: nichts Neues
- Produces: `zoom_ist_lesen(projekt: dict, max_zoom: float) -> tuple[float, bool]` — (Zoom als Faktor ≥ 1,0, ob gedeckelt)

**Hinweis:** Wie `adaptive_zoom_fovs` dekodiert wird, steht im Befund aus Task 1, Step 5. Gelang die Dekodierung dort nicht, wird nur der Rückfallzweig implementiert und die beiden Tests, die echte Werte prüfen, entfallen — der Test `test_zoom_ist_faellt_auf_den_deckel_zurueck` bleibt und deckt das Verhalten ab.

- [ ] **Step 1: Die failing tests anhängen**

```python
def test_zoom_ist_faellt_auf_den_deckel_zurueck():
    wert, gedeckelt = G.zoom_ist_lesen({"gyro_source": {}}, 120.0)
    assert wert == pytest.approx(1.20)
    assert gedeckelt is True


def test_zoom_ist_rechnet_prozent_in_faktor_um():
    # adaptive_zoom_fovs liegen als dekodierte Liste vor; Maximum zählt
    projekt = {"gyro_source": {"adaptive_zoom_fovs_dekodiert": [1.02, 1.11, 1.07]}}
    wert, gedeckelt = G.zoom_ist_lesen(projekt, 120.0)
    assert wert == pytest.approx(1.11)
    assert gedeckelt is False


def test_zoom_ist_meldet_wenn_der_deckel_griff():
    projekt = {"gyro_source": {"adaptive_zoom_fovs_dekodiert": [1.19, 1.20]}}
    wert, gedeckelt = G.zoom_ist_lesen(projekt, 120.0)
    assert wert == pytest.approx(1.20)
    assert gedeckelt is True
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow.py -q -k zoom_ist
```

Erwartet: FAIL mit `AttributeError: module 'niro_autocut.gyroflow' has no attribute 'zoom_ist_lesen'`.

- [ ] **Step 3: `zoom_ist_lesen` implementieren**

```python
def zoom_ist_lesen(projekt: dict, max_zoom: float) -> tuple[float, bool]:
    """Tatsächlich verbrauchter Zoom als Faktor ≥ 1,0 und ob der Deckel griff.

    Gyroflow rechnet in Prozent (100 = kein Beschnitt). Ohne dekodierte Werte gilt der Deckel als Obergrenze — der
    Haushalt hält dadurch ohnehin, der Bericht nennt den Wert dann als Obergrenze statt als Messwert."""
    deckel = float(max_zoom) / 100.0
    werte = (projekt.get("gyro_source") or {}).get("adaptive_zoom_fovs_dekodiert")
    if not werte:
        return deckel, True
    wert = max(float(w) for w in werte)
    return wert, wert >= deckel - 1e-9
```

- [ ] **Step 4: Tests laufen lassen, Erfolg bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow.py -q
```

Erwartet: 15 passed.

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio"
git add tools/autocut/src/niro_autocut/gyroflow.py tools/autocut/tests/test_gyroflow.py
git commit -m "feat(autocut): verbrauchten Gyroflow-Zoom lesen, Rückfall auf den Deckelwert

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Charge-Lauf und `gyroflow.json`

**Files:**
- Modify: `tools/autocut/src/niro_autocut/gyroflow.py`
- Modify: `tools/autocut/tests/test_gyroflow.py`

**Interfaces:**
- Consumes: `clip_export` (Task 4), `pruefe_deckel` (Task 2)
- Produces: `gyroflow_charge(ch, clips: list[dict], telemetrie: list[dict], cfg: dict, force=False) -> dict`

`clips` sind die Einträge aus `gyroflow_clips.json` (`{datei, tempo50}`, Task 8). Rückgabe: `{"clips": [...], "uebersprungen": [...], "stand": "..."}`, geschrieben nach `_intern/autocut/gyroflow.json`.

- [ ] **Step 1: Die failing tests anhängen**

```python
def test_charge_lauf_fasst_mehrfach_genutzte_dateien_zusammen(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)
    clips = [{"datei": str(v), "tempo50": False}, {"datei": str(v), "tempo50": True}]
    tele = [{"path": str(v), "clip": "FX3_0001", "kamera": "FX3", "haltung": "hand", "quelle": "rtmd"}]

    erg = G.gyroflow_charge(ch, clips, tele, cfg)

    assert len(erg["clips"]) == 1
    assert (medien / "aufrufe.log").read_text(encoding="utf-8").count("--export-project") == 1
    assert json.loads((ch.autocut / "gyroflow.json").read_text(encoding="utf-8"))["clips"][0]["clip"] == "FX3_0001"


def test_charge_lauf_ueberspringt_clips_ohne_gyrospur(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "ZV_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)
    tele = [{"path": str(v), "clip": "ZV_0001", "kamera": "ZV-E10", "haltung": "hand", "quelle": "keine"}]

    erg = G.gyroflow_charge(ch, [{"datei": str(v), "tempo50": False}], tele, cfg)

    assert erg["clips"] == []
    assert erg["uebersprungen"][0]["grund"] == "keine Gyrospur"
    assert not (medien / "aufrufe.log").exists()


def test_charge_lauf_ueberspringt_stabilized_dateien(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "DJI_0001_stabilized.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)
    tele = [{"path": str(v), "clip": "DJI_0001_stabilized", "kamera": "DJI", "haltung": "gimbal", "quelle": "rtmd"}]

    erg = G.gyroflow_charge(ch, [{"datei": str(v), "tempo50": False}], tele, cfg)

    assert erg["uebersprungen"][0]["grund"] == "Avata-Export (_stabilized)"


def test_charge_lauf_ueberspringt_clips_ohne_telemetrie(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0009.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)

    erg = G.gyroflow_charge(ch, [{"datei": str(v), "tempo50": False}], [], cfg)

    assert erg["uebersprungen"][0]["grund"] == "kein Telemetrie-Eintrag"


def test_charge_lauf_prueft_den_deckel_vor_dem_ersten_export(tmp_path: Path):
    ch = _charge(tmp_path)
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["max_zoom"]["hand"] = 130
    with pytest.raises(AutoCutError, match="max_zoom"):
        G.gyroflow_charge(ch, [], [], cfg)
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow.py -q -k charge_lauf
```

Erwartet: FAIL mit `AttributeError: module 'niro_autocut.gyroflow' has no attribute 'gyroflow_charge'`.

- [ ] **Step 3: `gyroflow_charge` implementieren**

```python
def gyroflow_charge(ch, clips: list[dict], telemetrie: list[dict], cfg: dict, force: bool = False) -> dict:
    """Sidecars für die genutzten B-Roll-Shots; je Quelldatei einer, auch bei Mehrfachnutzung.

    Übersprungen wird mit Grund statt still: ohne Gyrospur, ohne Telemetrie-Eintrag, oder ``_stabilized`` im Namen
    (Avata-Export — nie erneut stabilisieren, wie in 6d)."""
    pruefe_deckel(cfg)
    nach_pfad = {str(Path(r["path"]).expanduser().resolve()): r for r in telemetrie if r.get("path")}
    erlaubte = set(nach_pfad)

    ergebnisse, uebersprungen, gesehen = [], [], set()
    for eintrag in clips:
        p = str(Path(eintrag["datei"]).expanduser().resolve())
        if p in gesehen:
            continue
        gesehen.add(p)
        rec = nach_pfad.get(p)
        if rec is None:
            uebersprungen.append({"datei": p, "grund": "kein Telemetrie-Eintrag"})
        elif "_stabilized" in Path(p).stem:
            uebersprungen.append({"datei": p, "grund": "Avata-Export (_stabilized)"})
        elif rec.get("quelle") != "rtmd":
            uebersprungen.append({"datei": p, "grund": "keine Gyrospur"})
        else:
            datensatz, _ = clip_export(ch, p, rec, cfg, erlaubte, force=force)
            ergebnisse.append(datensatz)

    erg = {"clips": ergebnisse, "uebersprungen": uebersprungen,
           "stand": _dt.datetime.now().isoformat(timespec="seconds")}
    ziel = Path(ch.autocut) / "gyroflow.json"
    ch.assert_writable(ziel)
    ziel.write_text(json.dumps(erg, ensure_ascii=False, indent=1), encoding="utf-8")
    return erg
```

- [ ] **Step 4: Tests laufen lassen, Erfolg bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow.py -q
```

Erwartet: 20 passed.

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio"
git add tools/autocut/src/niro_autocut/gyroflow.py tools/autocut/tests/test_gyroflow.py
git commit -m "feat(autocut): Charge-Lauf für Gyroflow-Sidecars, Überspringen mit Grund

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Skript, Bericht und Workflow-Doku

**Files:**
- Create: `tools/autocut/scripts/autocut_gyroflow.py`
- Create: `tools/autocut/src/niro_autocut/gyroflow_bericht.py`
- Create: `tools/autocut/tests/test_gyroflow_bericht.py`
- Modify: `tools/autocut/WORKFLOW-AutoCut.md`

**Interfaces:**
- Consumes: `gyroflow_charge` (Task 6); `Charge`, `AutoCutError`, `append_protokoll` aus `.charge`
- Produces: `bericht_md(erg: dict, clips: list[dict]) -> str`; CLI `autocut_gyroflow.py "<Charge>" [--force] [--dry-run]`

- [ ] **Step 1: Den failing test für den Bericht schreiben**

`tools/autocut/tests/test_gyroflow_bericht.py`:

```python
"""gyroflow_bericht.py — Bericht über Sidecars, Überspringungen und gedeckelte Clips (Spec 2026-09-22)."""
from __future__ import annotations

from niro_autocut.gyroflow_bericht import bericht_md


def test_bericht_nennt_sidecars_ueberspringungen_und_deckel():
    erg = {
        "clips": [
            {"clip": "FX3_0001", "kamera": "FX3", "haltung": "hand", "zoom_ist": 1.20,
             "zoom_gedeckelt": True, "sidecar": "/m/FX3_0001.gyroflow", "fehler": None},
            {"clip": "FX3_0002", "kamera": "FX3", "haltung": "gimbal", "zoom_ist": 1.06,
             "zoom_gedeckelt": False, "sidecar": "/m/FX3_0002.gyroflow", "fehler": None},
        ],
        "uebersprungen": [{"datei": "/m/ZV_0001.MP4", "grund": "keine Gyrospur"}],
        "stand": "2026-09-22T21:00:00",
    }
    md = bericht_md(erg, [{"datei": "/m/FX3_0001.MP4", "tempo50": True}])

    assert "2 Sidecars" in md
    assert "FX3_0001" in md and "FX3_0002" in md
    assert "keine Gyrospur" in md and "ZV_0001" in md
    assert "gedeckelt" in md.lower()
    assert "50 %" in md            # Zeitlupen-Shots werden eigens genannt


def test_bericht_nennt_fehler_je_clip():
    erg = {"clips": [{"clip": "FX3_0003", "kamera": "FX3", "haltung": "hand", "zoom_ist": None,
                      "zoom_gedeckelt": None, "sidecar": None, "fehler": "kein Gyro gefunden"}],
           "uebersprungen": [], "stand": "2026-09-22T21:00:00"}
    md = bericht_md(erg, [])
    assert "kein Gyro gefunden" in md
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow_bericht.py -q
```

Erwartet: FAIL mit `ModuleNotFoundError: No module named 'niro_autocut.gyroflow_bericht'`.

- [ ] **Step 3: `gyroflow_bericht.py` schreiben**

```python
"""Bericht zum Gyroflow-Lauf (Spec 2026-09-22): welche Clips ein Sidecar bekamen, welche warum nicht, wo der
Zoom-Deckel griff. Der Deckel hält den Rand-Haushalt ohnehin ein — die Liste zeigt, wo Gyroflow schwächer glättete
als es könnte, damit der User entscheiden kann, telemetrie.digitalzoom_max anzuheben."""
from __future__ import annotations

from pathlib import Path


def bericht_md(erg: dict, clips: list[dict]) -> str:
    clips_ = erg.get("clips") or []
    uebersprungen = erg.get("uebersprungen") or []
    tempo50 = {Path(c["datei"]).stem for c in (clips or []) if c.get("tempo50")}
    fehler = [c for c in clips_ if c.get("fehler")]
    gedeckelt = [c for c in clips_ if c.get("zoom_gedeckelt")]

    z = [f"# Gyroflow — {len(clips_)} Sidecars ({erg.get('stand', '')})", ""]
    z.append(f"{len(clips_) - len(fehler)} von {len(clips_)} Clips stabilisiert, "
             f"{len(uebersprungen)} übersprungen, {len(fehler)} mit Fehler.")
    z += ["", "| Clip | Kamera | Haltung | Zoom | Tempo |", "|---|---|---|---|---|"]
    for c in clips_:
        zoom = "—" if c.get("zoom_ist") is None else f"{c['zoom_ist']:.2f}×"
        if c.get("zoom_gedeckelt"):
            zoom += " (gedeckelt)"
        z.append(f"| {c.get('clip')} | {c.get('kamera') or '—'} | {c.get('haltung') or '—'} | {zoom} | "
                 f"{'50 %' if c.get('clip') in tempo50 else '100 %'} |")

    if gedeckelt:
        z += ["", "## Deckel griff", "",
              "Bei diesen Clips glättet Gyroflow schwächer, als es könnte — der Rand ist ausgereizt. "
              "Mehr Glättung gäbe es nur über ein höheres `telemetrie.digitalzoom_max`.", ""]
        z += [f"- {c.get('clip')} ({c.get('haltung') or '—'})" for c in gedeckelt]

    if uebersprungen:
        z += ["", "## Übersprungen", ""]
        z += [f"- {Path(u['datei']).name} — {u['grund']}" for u in uebersprungen]

    if fehler:
        z += ["", "## Fehler", ""]
        z += [f"- {c.get('clip')} — {c['fehler']}" for c in fehler]

    return "\n".join(z) + "\n"
```

- [ ] **Step 4: Test laufen lassen, Erfolg bestätigen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest tests/test_gyroflow_bericht.py -q
```

Erwartet: 2 passed.

- [ ] **Step 5: Das Skript schreiben**

`tools/autocut/scripts/autocut_gyroflow.py`, im Muster von `autocut_telemetrie.py`:

```python
"""Gyroflow-Sidecars für die im Feinschnitt genutzten B-Roll-Shots (Spec 2026-09-22) → <clip>.gyroflow neben der
Mediendatei, _intern/autocut/gyroflow.json, Bericht Ergebnisse/Rohschnitt/gyroflow.md.

Aufruf:
    venv/bin/python scripts/autocut_gyroflow.py "<Charge>" [--force] [--dry-run]

Eingabe: _intern/autocut/gyroflow_clips.json (schreibt der Probelauf von feinschnitt_bauen.py) und
_intern/autocut/telemetrie.json. Rendert nie. Exit 1 bei Fehlern, 130 bei Abbruch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402
from niro_autocut.gyroflow import gyroflow_charge  # noqa: E402
from niro_autocut.gyroflow_bericht import bericht_md  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Gyroflow-Sidecars für die genutzten B-Roll-Shots.")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--force", action="store_true", help="Cache verwerfen und alle Sidecars neu erzeugen")
    ap.add_argument("--dry-run", action="store_true", help="nur nennen, was passieren würde")
    a = ap.parse_args(argv)

    try:
        ch = Charge.open_basis(a.charge)
        clips_datei = ch.autocut / "gyroflow_clips.json"
        if not clips_datei.exists():
            raise AutoCutError(
                f"{clips_datei} fehlt.\nZuerst den Probelauf von _intern/feinschnitt_bauen.py laufen lassen — "
                f"er schreibt die genutzten B-Roll-Shots aus der BROLL-Tabelle.")
        clips = json.loads(clips_datei.read_text(encoding="utf-8"))
        tele_datei = ch.autocut / "telemetrie.json"
        if not tele_datei.exists():
            raise AutoCutError(f"{tele_datei} fehlt.\nZuerst scripts/autocut_telemetrie.py für diese Charge laufen lassen.")
        telemetrie = json.loads(tele_datei.read_text(encoding="utf-8"))

        if a.dry_run:
            print(f"{len(clips)} genutzte Shots, {len({c['datei'] for c in clips})} Quelldateien.")
            return 0

        erg = gyroflow_charge(ch, clips, telemetrie, ch.config, force=a.force)
        md = bericht_md(erg, clips)
        ziel = ch.ergebnisse / "gyroflow.md"
        ch.assert_writable(ziel)
        ziel.write_text(md, encoding="utf-8")
        print(md)
        append_protokoll(ch, "Gyroflow-Sidecars",
                         [f"{len(erg['clips'])} Sidecars, {len(erg['uebersprungen'])} übersprungen",
                          f"Bericht: {ziel}"])
        return 1 if any(c.get("fehler") for c in erg["clips"]) else 0
    except AutoCutError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Gesamten Testlauf prüfen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q
```

Erwartet: alle Tests grün, inklusive der 22 neuen. Vorher bestehende Tests dürfen nicht brechen.

- [ ] **Step 7: `WORKFLOW-AutoCut.md` ergänzen**

In der Bausteintabelle bei 6d eine Zeile ergänzen und den Abschnitt 6d um einen Unterabschnitt „Gyroflow-Sidecars" erweitern: Aufruf, Eingaben (`gyroflow_clips.json`, `telemetrie.json`), Ausgaben (`<clip>.gyroflow` neben den Medien, `gyroflow.json`, `gyroflow.md`), die Deckel-Ungleichung und der Hinweis, dass Clips ohne Gyrospur beim heutigen `Stabilize()`-Weg bleiben. In der Dateibaum-Übersicht `gyroflow.json` und `gyroflow/` (Cache) unter `_intern/autocut/` eintragen.

- [ ] **Step 8: Commit**

```bash
cd "/Users/jansantos/NIRO Studio"
git add tools/autocut/scripts/autocut_gyroflow.py tools/autocut/src/niro_autocut/gyroflow_bericht.py \
        tools/autocut/tests/test_gyroflow_bericht.py tools/autocut/WORKFLOW-AutoCut.md
git commit -m "feat(autocut): Skript und Bericht für die Gyroflow-Sidecars, Workflow-Doku

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: Probelauf schreibt die Clipliste

Erst hiermit ist die Reihenfolge „Plan → Sidecars → Bau" erzwungen statt nur empfohlen: ohne ausgefüllte `BROLL`-Tabelle gibt es keine Clipliste, ohne Clipliste keinen Export.

**Files:**
- Modify: `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py` (Probelauf-Zweig, um Zeile 168 herum, wo `if BROLL:` steht)

**Interfaces:**
- Consumes: `BROLL` (Tabelle in der Vorlage), `broll_auswahl.json` (löst Shot → `datei` auf)
- Produces: `_intern/autocut/gyroflow_clips.json` — `[{"datei": "<absoluter Pfad>", "tempo50": true|false}, …]`

- [ ] **Step 1: Die Stelle lesen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut" && sed -n '160,200p' vorlagen/feinschnitt/feinschnitt_bauen.py
sed -n '360,395p' vorlagen/feinschnitt/feinschnitt_bauen.py
```

Dort steht, wie eine `BROLL`-Zeile auf einen Shot und dessen `s["datei"]` abgebildet wird (Zeile 384 nutzt `s["datei"]` bereits für `TM.stabil_vorschlag`). Dieselbe Auflösung wird hier wiederverwendet — nicht neu erfinden.

- [ ] **Step 2: Im Probelauf die Liste schreiben**

Im Probelauf-Zweig, nachdem die `BROLL`-Zeilen auf Shots aufgelöst sind und bevor der Bau-Zweig beginnt:

```python
    # Gyroflow-Sidecars (Spec 2026-09-22): die genutzten B-Roll-Quelldateien für scripts/autocut_gyroflow.py.
    # Nur hier liegen BROLL (was benutzt wird) und broll_auswahl.json (welche Datei das ist) zusammen vor.
    gyro_clips, gesehen = [], set()
    for zeile in BROLL:
        s = shot_fuer(zeile[0])                      # dieselbe Auflösung wie oben für stabil_vorschlag
        tempo50 = bool(zeile[5]) if len(zeile) > 5 else False
        if s["datei"] in gesehen:
            continue
        gesehen.add(s["datei"])
        gyro_clips.append({"datei": s["datei"], "tempo50": tempo50})
    ziel = AC / "gyroflow_clips.json"
    ziel.write_text(json.dumps(gyro_clips, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(gyro_clips)} B-Roll-Quelldateien für Gyroflow → {ziel}")
    print("  weiter mit: tools/autocut/venv/bin/python tools/autocut/scripts/autocut_gyroflow.py \"<Charge>\"")
```

`shot_fuer` ist der Name, den Step 1 als bestehende Auflösung zutage fördert — wird sie dort anders gerufen, hier diesen Namen einsetzen. `AC` ist der schon vorhandene Pfad auf `_intern/autocut` (siehe Zeile 66, `TM.laden(AC)`).

- [ ] **Step 3: Gegen eine echte Charge prüfen**

```bash
cd "/Users/jansantos/NIRO Studio"
ls projects/*/*/*/_intern/feinschnitt_bauen.py
```

In einer Charge mit ausgefüllter `BROLL`-Tabelle die geänderte Vorlage einspielen und den **Probelauf** (ohne `--bauen`) starten. Er verbindet sich nur lesend mit Resolve.

Erwartet: `gyroflow_clips.json` entsteht, enthält je genutzte Quelldatei einen Eintrag mit absolutem Pfad, und die Zahl stimmt mit der Zeilenzahl der `BROLL`-Tabelle nach Dublettenabzug überein.

- [ ] **Step 4: Den ersten echten Lauf machen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut"
venv/bin/python scripts/autocut_gyroflow.py "<Charge>" --dry-run
venv/bin/python scripts/autocut_gyroflow.py "<Charge>"
```

Erwartet: neben jeder genutzten Mediendatei eine `.gyroflow`-Datei, `gyroflow.md` mit der Tabelle, keine Fehler. Stichprobe: eine Sidecar-Datei öffnen und prüfen, dass `calibration_data.camera_model` zur Kamera passt und `stabilization.max_zoom` dem Preset entspricht.

**Dies ist der Punkt, an dem die Startwerte aus Task 2 geprüft werden:** eine Handkamera-Aufnahme mit dem Sidecar in Resolve ansehen und beurteilen, ob 0,7 Glättung passt. Weicht das Urteil ab, die Werte in `defaults.yaml` anpassen und in der Spec als kalibriert vermerken.

- [ ] **Step 5: Commit**

```bash
cd "/Users/jansantos/NIRO Studio"
git add tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py
git commit -m "feat(autocut): Feinschnitt-Probelauf schreibt die genutzten B-Roll-Quelldateien für Gyroflow

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Gyroflow-OFX im 6d-Bau anwenden

**Form abhängig von Task 1.** Tool-Kennung und Parametername stammen aus dem dortigen Befund; fiel der Tempo-Test negativ aus, werden Shots mit `tempo50` übersprungen und behalten den heutigen `Stabilize()`-Weg.

**Files:**
- Modify: `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py` (Bau-Zweig, V3-Abschnitt um Zeile 384)
- Modify: `tools/autocut/WORKFLOW-AutoCut.md` (Abschnitt 6d, V3-Beschreibung)

**Interfaces:**
- Consumes: `gyroflow.json` (Task 6) für `clip → sidecar`; die Tool-Kennung und der Parametername aus Task 1
- Produces: je V3-Item mit Sidecar ein Fusion-Comp mit gesetztem Gyroflow-OFX; `feinschnitt.json` bekommt `gyroflow_gesetzt` (Zahl) und `gyroflow_abweichungen` (Liste `{shot, grund}`)

- [ ] **Step 1: Sidecar-Zuordnung laden**

Im Bau-Zweig, wo heute `Stabilize()` entschieden wird (Zeile 384/385):

```python
    # Gyroflow ersetzt Stabilize() für Clips mit Sidecar; alle anderen behalten den bisherigen Weg.
    GYRO = {}
    _gf = AC / "gyroflow.json"
    if _gf.exists():
        GYRO = {c["clip"]: c["sidecar"] for c in json.loads(_gf.read_text(encoding="utf-8"))["clips"]
                if c.get("sidecar") and not c.get("fehler")}
```

- [ ] **Step 2: Statt `Stabilize()` den Fusion-Comp setzen**

An der Stelle, an der heute `item.Stabilize()` gerufen wird:

```python
        sidecar = GYRO.get(Path(s["datei"]).stem)
        if sidecar and not (tempo50 and not GYRO_BEI_ZEITLUPE):
            comp = item.AddFusionComp()
            werkzeug = comp.AddTool(GYRO_TOOL_ID)
            if werkzeug is None:
                gyroflow_abweichungen.append({"shot": zeile[0], "grund": "OFX-Tool nicht verfügbar"})
                item.Stabilize()                      # Rückfall auf den bisherigen Weg
            else:
                werkzeug.SetInput(GYRO_PARAM_PROJEKT, sidecar)
                gyroflow_gesetzt += 1
        elif stabil:
            item.Stabilize()
```

Oben in der Vorlage als anpassbare Konstanten:

```python
# Gyroflow-OFX (Spec 2026-09-22; Kennung und Parametername aus dem Befund der Verifikation):
GYRO_TOOL_ID = "<Kennung aus Task 1, Step 2>"
GYRO_PARAM_PROJEKT = "<Parametername aus Task 1, Step 3>"
GYRO_BEI_ZEITLUPE = True   # False, wenn der Tempo-Test aus Task 1, Step 4 fehlschlug
```

- [ ] **Step 3: Readback in `feinschnitt.json` aufnehmen**

Im Readback-Block `gyroflow_gesetzt` und `gyroflow_abweichungen` mitschreiben — wie `zoom_gesetzt`/`zoom_abweichungen` es heute tun.

- [ ] **Step 4: An einer echten Charge bauen und prüfen**

Nur im Projekt, das der User in dieser Session freigegeben hat; Projektnamen vorher lesen, nennen und abgleichen. Nicht schreiben, während der User abspielt.

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut"
venv/bin/python "<Charge>/_intern/feinschnitt_bauen.py"            # Probelauf
venv/bin/python "<Charge>/_intern/feinschnitt_bauen.py" --bauen
```

Erwartet: `gyroflow_gesetzt` entspricht der Zahl der V3-Shots mit Sidecar, `gyroflow_abweichungen` ist leer. In Resolve stichprobenartig zwei V3-Clips öffnen: der Fusion-Comp trägt das Gyroflow-Tool mit dem richtigen Sidecar-Pfad, und das Bild ist ruhiger als vorher.

- [ ] **Step 5: Review-Stand ablegen**

Nach dem Bau wie üblich:

```bash
cd "/Users/jansantos/NIRO Studio/tools/autocut"
venv/bin/python "<Charge>/_intern/autocut_review.py"
```

Notiz: „Feinschnitt: Gyroflow-Stabilisierung". Den Link im Chat nennen.

- [ ] **Step 6: Doku und Commit**

In `WORKFLOW-AutoCut.md` die V3-Beschreibung in 6d anpassen: Gyroflow für Clips mit Sidecar, `Stabilize()` als Rückfall für alle anderen, die drei Konstanten der Vorlage erklärt.

```bash
cd "/Users/jansantos/NIRO Studio"
git add tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py tools/autocut/WORKFLOW-AutoCut.md
git commit -m "feat(autocut): Gyroflow-OFX per Fusion-Comp im 6d-Bau, Stabilize() als Rückfall

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Protokoll und Abgleich**

`Protokoll.md` der Charge fortschreiben (Datum, was gemacht, gelieferte Dateien, Entscheidungen, Review-Link), dann:

```bash
cd "/Users/jansantos/NIRO Studio" && sh tools/studio_abgleich.sh --charge "projects/<Kunde>/<Projekt>/<Charge>"
```

---

## Selbstprüfung des Plans

**Spec-Abdeckung:** Abschnitt 1 (`gyroflow_sidecars.py`) → Tasks 3–6; Eingabe `gyroflow_clips.json` → Task 8; Schreibschutz → Task 3; Cache → Task 4. Abschnitt 2 (Preset aus der Telemetrie) → Task 2, kalibriert in Task 8, Step 4. Abschnitt 3 (Fusion-Comp, Einordnung in 6d) → Tasks 8–9. Abschnitt 4 (Rand-Haushalt über `max_zoom`) → Task 2 (`pruefe_deckel`) und Task 5 (`zoom_ist`, nur Bericht). Abschnitt 5 (Plugin-Erneuerung) → Task 1, Step 1. Fehler und Randfälle: Zeitlupe → Task 1 Step 4 und Task 9 Step 2; Clips ohne Gyrospur, `_stabilized`, Mehrfachnutzung → Task 6; DJI → Task 1 Step 6. Offene Punkte 1–5 → Task 1.

**Abweichung vom Spec-Namen:** Die Spec nennt das Werkzeug `gyroflow_sidecars.py`. Der Plan legt das Modul als `niro_autocut/gyroflow.py` mit dem Skript `scripts/autocut_gyroflow.py` an — das folgt dem Muster von `telemetrie.py`/`autocut_telemetrie.py` und ist die Konvention des Repos. Beim Ausführen von Task 7 den Namen in der Spec entsprechend nachziehen.

**Platzhalter:** Drei Stellen tragen bewusst Werte, die erst Task 1 liefert — `GYRO_TOOL_ID`, `GYRO_PARAM_PROJEKT` und die Dekodierung von `adaptive_zoom_fovs`. Sie sind als solche markiert und stehen hinter dem Gate; sie zu raten wäre schlechter, als sie zu messen. Für `adaptive_zoom_fovs` existiert ein vollwertiger Rückfall (Task 5).

**Typen:** `clip_export` gibt `tuple[dict, bool]` wie `telemetrie.clip_messen` es tut; `gyroflow_charge` gibt `{"clips", "uebersprungen", "stand"}`, was Task 7 (`bericht_md`) und Task 9 (`GYRO`-Zuordnung) genau so lesen. `sidecar_pfad` gibt `Path`, `zoom_ist_lesen` gibt `tuple[float, bool]`, `preset_hash` gibt `str` — jeweils an den Aufrufstellen so verwendet.
