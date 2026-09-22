# Telemetrie in der B-Roll-Auswahl (Stufe 3 v2) — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die gemessenen Telemetriewerte (KB-Brennweite in mm, Zoomfahrten, Bewegungsspitzen) fließen in die
automatische B-Roll-Auswahl — als Felder im kompakten Index für das Planen und als drei Prüfregeln in
`verify_layout()` für das Prüfen.

**Architecture:** Stufe 2b (`index_sections.py`) bleibt die einzige Stelle, an der Telemetrie in
`broll_index.json` geschrieben wird; neu dazu `bewegung_spitzen` je Abschnitt. `compact_index_v2()` hört auf,
die Telemetriefelder wegzufiltern. `verify_layout()` bekommt die Telemetrie-Datensätze als Parameter (wie die
Vorlagen 3a/6d über `telemetrie.laden()`/`finden()`), weil `kb_am()` und `zooms_im_bereich()` den Verlauf an
der exakten Schnittstelle brauchen und nicht den Abschnitts-Median.

**Tech Stack:** Python 3.12 (`tools/autocut/venv`), pytest, numpy, PyYAML. Kein Resolve, kein NAS in den Tests.

**Spec:** `docs/superpowers/specs/2026-09-22-autocut-broll-auswahl-telemetrie-design.md`

## Global Constraints

- Alle Regeln sind **optional**: fehlt Telemetrie für einen Clip, wird die Regel für diesen Shot übersprungen
  und gezählt — nie ein Abbruch, nie ein Fehler.
- **Regel 3c ist und bleibt eine Warnung.** Ihre beiden Schwellen (`bewegung_rand_s`, `bewegung_spitze_faktor`)
  sind unkalibriert. Eine Erhebung zum Fehler ist in diesem Plan ausdrücklich nicht vorgesehen.
- `brennweite_gleich_max` = 0,2 · `bewegung_rand_s` = 0,5 · `bewegung_spitze_faktor` = 3,0 — Werte wörtlich
  aus der Spec.
- Die neuen Config-Schlüssel gehören **nicht** in den Messungs-Hash: `OHNE_MESSWIRKUNG` in `telemetrie.py`
  muss um `bewegung_rand_s` und `bewegung_spitze_faktor` erweitert werden, sonst gilt jede vorhandene
  `telemetrie.json` als veraltet und alles wird neu gemessen.
- Claudes Klasse `brennweite` bleibt im Datensatz erhalten (Spec 2026-09-21); sie trägt nur keine Regel mehr.
- Kommentare und Docstrings auf Deutsch, wie im übrigen Modul.
- Nach jeder Task: `cd tools/autocut && venv/bin/python -m pytest -q` muss grün sein.

## File Structure

| Datei | Verantwortung | Task |
|---|---|---|
| `tools/autocut/src/niro_autocut/telemetrie.py` | neue Helfer `bewegung_spitzen()`, `bewegung_grundniveau()`; `OHNE_MESSWIRKUNG` erweitern | 1, 5 |
| `tools/autocut/src/niro_autocut/index_sections.py` | `telemetrie_anwenden()` schreibt `bewegung_spitzen` je Abschnitt | 1 |
| `tools/autocut/src/niro_autocut/broll_layout.py` | `compact_index_v2()` reicht durch; `verify_layout()` bekommt `tele`-Parameter und die drei Regeln | 2, 3, 4, 5 |
| `tools/autocut/scripts/autocut_place_broll.py` | lädt `telemetrie.json` und reicht sie an `verify_layout()` | 3 |
| `tools/autocut/defaults.yaml` | zwei neue Schlüssel unter `telemetrie:` | 5 |
| `tools/autocut/tests/test_telemetrie.py` | Helfer | 1, 5 |
| `tools/autocut/tests/test_index_sections.py` | 2b schreibt das Feld, Cache-Treffer ohne API | 1 |
| `tools/autocut/tests/test_broll_layout.py` | Durchreichen und die drei Regeln | 2, 3, 4, 5 |
| `tools/autocut/WORKFLOW-AutoCut.md`, `prompts/place-broll.md`, `README.md` | Doku | 6 |

---

### Task 1: `bewegung_spitzen` messen und in Stufe 2b schreiben

**Files:**
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (neuer Helfer, hinter `abschnitt_werte`, ~Zeile 676)
- Modify: `tools/autocut/src/niro_autocut/index_sections.py:217-223` (`telemetrie_anwenden`)
- Test: `tools/autocut/tests/test_telemetrie.py`, `tools/autocut/tests/test_index_sections.py`

**Interfaces:**
- Consumes: `fenster` je Clip-Datensatz — Liste `[t_s, wackeln, bewegung, bewegungsart, schaerfe]`, Fenster
  `fenster_s` (2,0 s) im Schritt 1 s.
- Produces: `bewegung_spitzen(rec: dict | None, von_s: float, bis_s: float) -> list[list[float]]` — Liste
  `[t_s, bewegung]`, aufsteigend nach `t_s`; leer ohne `fenster`. Abschnittsfeld `bewegung_spitzen` mit
  demselben Inhalt.

- [ ] **Step 1: Failing test für den Helfer**

In `tools/autocut/tests/test_telemetrie.py` anhängen:

```python
def test_bewegung_spitzen_liefert_lokale_maxima_im_bereich():
    rec = {"fenster": [[0.0, 0.1, 0.5, "fahrt", None],
                       [1.0, 0.1, 3.0, "schwenk_links", None],   # lokales Maximum
                       [2.0, 0.1, 0.4, "fahrt", None],
                       [3.0, 0.1, 1.2, "fahrt", None],
                       [4.0, 0.1, 0.3, "fahrt", None]]}          # 3.0 ist Maximum, 4.0 nicht
    assert T.bewegung_spitzen(rec, 0.0, 5.0) == [[1.0, 3.0], [3.0, 1.2]]
    assert T.bewegung_spitzen(rec, 2.5, 5.0) == [[3.0, 1.2]]     # Bereich grenzt ein
    assert T.bewegung_spitzen({"fenster": []}, 0.0, 5.0) == []
    assert T.bewegung_spitzen(None, 0.0, 5.0) == []
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py::test_bewegung_spitzen_liefert_lokale_maxima_im_bereich -v`
Expected: FAIL mit `AttributeError: module 'niro_autocut.telemetrie' has no attribute 'bewegung_spitzen'`

- [ ] **Step 3: Helfer schreiben**

In `telemetrie.py` direkt hinter `abschnitt_werte()` einfügen:

```python
def bewegung_spitzen(rec: dict | None, von_s: float, bis_s: float) -> list[list[float]]:
    """Lokale Maxima der Fenster-Reihe im Bereich [von_s, bis_s] als ``[t_s, bewegung]`` (Spec 2026-09-22).
    Ein Fenster ist Maximum, wenn seine ``bewegung`` die beider Nachbarn erreicht; am Rand der Reihe zählt der
    vorhandene Nachbar. Leer ohne ``fenster`` — die Auswahl nutzt die Liste nur als Hinweis, nie als Sperre."""
    fen = (rec or {}).get("fenster") or []
    out: list[list[float]] = []
    for i, f in enumerate(fen):
        t, bw = float(f[0]), float(f[2])
        if t < von_s or t > bis_s:
            continue
        if i > 0 and bw < float(fen[i - 1][2]):
            continue
        if i < len(fen) - 1 and bw < float(fen[i + 1][2]):
            continue
        out.append([t, round(bw, 3)])
    return out
```

- [ ] **Step 4: Test laufen lassen, grün prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py::test_bewegung_spitzen_liefert_lokale_maxima_im_bereich -v`
Expected: PASS

- [ ] **Step 5: Failing test für Stufe 2b**

In `tools/autocut/tests/test_index_sections.py` anhängen:

```python
def test_telemetrie_anwenden_schreibt_bewegung_spitzen():
    rec = {"fingerprint": "abc", "abschnitte": [{"von_s": 0, "bis_s": 5, "einstellung": "Totale",
                                                 "perspektive_hoehe": "Augenhöhe"}]}
    tele = {"quelle": "rtmd", "perspektive_hoehe": "Augenhöhe", "haltung": "gimbal", "fenster_s": 2.0,
            "fenster": [[0.0, 0.1, 0.5, "fahrt", None],
                        [1.0, 0.1, 3.0, "schwenk_links", None],
                        [2.0, 0.1, 0.4, "fahrt", None]]}
    neu, geaendert = S.telemetrie_anwenden(rec, tele, 2.0)
    assert geaendert is True
    assert neu["abschnitte"][0]["bewegung_spitzen"] == [[1.0, 3.0]]
    # idempotent: zweiter Lauf ändert nichts mehr
    neu2, geaendert2 = S.telemetrie_anwenden(neu, tele, 2.0)
    assert geaendert2 is False and neu2["abschnitte"][0]["bewegung_spitzen"] == [[1.0, 3.0]]


def test_telemetrie_anwenden_ohne_fenster_setzt_kein_feld():
    rec = {"fingerprint": "abc", "abschnitte": [{"von_s": 0, "bis_s": 5, "perspektive_hoehe": "Augenhöhe"}]}
    tele = {"quelle": "rtmd", "perspektive_hoehe": "Augenhöhe", "fenster": [], "fenster_s": 2.0}
    neu, _ = S.telemetrie_anwenden(rec, tele, 2.0)
    assert "bewegung_spitzen" not in neu["abschnitte"][0]
```

- [ ] **Step 6: Test laufen lassen, Fehlschlag prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_index_sections.py -k bewegung_spitzen -v`
Expected: FAIL mit `KeyError: 'bewegung_spitzen'`

- [ ] **Step 7: `telemetrie_anwenden` erweitern**

In `index_sections.py`: den Import in Zeile 23 um `bewegung_spitzen` ergänzen, dann Zeile 218-222 ersetzen:

```python
        von, bis = float(b.get("von_s", 0)), float(b.get("bis_s", 0))
        w = {**abschnitt_werte(tele, von, bis, fenster_s), **abschnitt_brennweite(tele, von, bis)}
        spitzen = bewegung_spitzen(tele, von, bis)
        if spitzen:
            w["bewegung_spitzen"] = spitzen
        for k in ("bewegungsart", "haltung", "brennweite_mm", "zoom", "bewegung_spitzen"):
            if w.get(k) is not None:
                geaendert |= b.get(k) != w[k]
                b[k] = w[k]
```

- [ ] **Step 8: Tests laufen lassen, grün prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_index_sections.py tests/test_telemetrie.py -q`
Expected: alle PASS

- [ ] **Step 9: Commit**

```bash
git add tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/src/niro_autocut/index_sections.py tools/autocut/tests/test_telemetrie.py tools/autocut/tests/test_index_sections.py
git commit -m "feat(autocut): bewegung_spitzen je Abschnitt in Stufe 2b

Lokale Maxima der Fenster-Reihe als [t_s, bewegung] im Abschnitt, damit die
Auswahl Bewegungsspitzen sieht statt nur Abschnitts-Mittelwerte. Cache-Treffer
bekommen das Feld ohne API-Aufruf (bestehender Zweig in index_sections_clip).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: `compact_index_v2()` reicht die Telemetriefelder durch

**Files:**
- Modify: `tools/autocut/src/niro_autocut/broll_layout.py:720-733`
- Test: `tools/autocut/tests/test_broll_layout.py`

**Interfaces:**
- Consumes: Abschnittsfelder aus Task 1 und aus Stufe 2b (`brennweite_mm`, `zoom`, `bewegungsart`, `haltung`,
  `bewegung_spitzen`).
- Produces: `compact_index_v2(index)` liefert je Abschnitt zusätzlich die fünf Schlüssel `brennweite_mm`,
  `zoom`, `bewegungsart`, `haltung`, `bewegung_spitzen`; fehlende Werte sind `None` bzw. `[]`.

- [ ] **Step 1: Failing test**

In `tools/autocut/tests/test_broll_layout.py` anhängen:

```python
def test_compact_index_v2_reicht_telemetriewerte_durch():
    idx = _idx()
    a = idx["clips"][0]["abschnitte"][0]
    a.update(brennweite_mm=71.6, zoom="langsam", bewegungsart="schwenk_links", haltung="gimbal",
             bewegung_spitzen=[[1.0, 3.0]])
    cx = L.compact_index_v2(idx)
    ab = cx[0]["abschnitte"][0]
    assert ab["brennweite_mm"] == 71.6 and ab["zoom"] == "langsam"
    assert ab["bewegungsart"] == "schwenk_links" and ab["haltung"] == "gimbal"
    assert ab["bewegung_spitzen"] == [[1.0, 3.0]]
    assert ab["brennweite"] == "weit"          # Claudes Klasse bleibt erhalten


def test_compact_index_v2_ohne_telemetrie_liefert_none():
    cx = L.compact_index_v2(_idx())
    ab = cx[0]["abschnitte"][0]
    assert ab["brennweite_mm"] is None and ab["zoom"] is None
    assert ab["bewegungsart"] is None and ab["haltung"] is None and ab["bewegung_spitzen"] == []
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_broll_layout.py -k compact_index_v2 -v`
Expected: FAIL mit `KeyError: 'brennweite_mm'`

- [ ] **Step 3: `compact_index_v2` erweitern**

In `broll_layout.py` die Abschnitts-Komprehension (Zeile 723-726) ersetzen:

```python
        abschnitte = [{"von_s": a["von_s"], "bis_s": a["bis_s"], "kurz": a.get("beschreibung", ""), "q": a.get("qualitaet"),
                       "einstellung": a.get("einstellung"), "perspektive": _perspektive(a), "brennweite": a.get("brennweite"),
                       "richtung": a.get("bewegungsrichtung"), "motiv": a.get("hauptmotiv"),
                       # gemessen (Spec 2026-09-22): die Auswahl plant auf diesen Werten, nicht auf den Klassen
                       "brennweite_mm": a.get("brennweite_mm"), "zoom": a.get("zoom"),
                       "bewegungsart": a.get("bewegungsart"), "haltung": a.get("haltung"),
                       "bewegung_spitzen": a.get("bewegung_spitzen") or []}
                      for a in (c.get("abschnitte") or []) if a.get("verwendbar")]
```

- [ ] **Step 4: Tests laufen lassen, grün prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_broll_layout.py -q`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add tools/autocut/src/niro_autocut/broll_layout.py tools/autocut/tests/test_broll_layout.py
git commit -m "feat(autocut): kompakter Index reicht die gemessenen Werte durch

compact_index_v2 filterte brennweite_mm, zoom, bewegungsart, haltung und
bewegung_spitzen bisher weg; die Auswahl plante auf der Brennweitenklasse, die
in der Kalibrierung nur zu 47 % mit der gemessenen KB-Brennweite übereinstimmte.
Claudes Klasse bleibt im Datensatz, trägt aber keine Regel mehr.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Telemetrie in `verify_layout()` + Regel 3a (Brennweitenfolge)

**Files:**
- Modify: `tools/autocut/src/niro_autocut/broll_layout.py:561` (Signatur), `:666-680` (Cut-Flow-Schleife)
- Modify: `tools/autocut/scripts/autocut_place_broll.py` (Telemetrie laden und übergeben)
- Test: `tools/autocut/tests/test_broll_layout.py`

**Interfaces:**
- Consumes: `telemetrie.laden(autocut_dir) -> list[dict]`, `telemetrie.finden(tele, path) -> dict | None`,
  `telemetrie.kb_am(rec, t_s, spanne_s=0.5, seite="mitte") -> float | None`,
  `telemetrie.genutzter_quellbereich_s(src_in_f, n_f, clip_fps, langsam, ziel_fps=25.0) -> tuple[float, float]`,
  `telemetrie.gleiche_brennweite(kb_a, kb_b, abstand_max) -> bool`,
  `telemetrie.brennweite_abstand(kb_a, kb_b) -> float`,
  `telemetrie.telemetrie_hinweise(recs, cfg) -> list[str]`. **Alle vier existieren bereits** — nicht neu schreiben.
- Produces: `verify_layout(plan, tp_dict, index, cl, cfg, fps, tele=None)` — neuer optionaler letzter Parameter
  `tele: list[dict] | None`. Fehler-Text der Regel beginnt mit `"Strecke {nr}: "` und enthält `"KB"`.

- [ ] **Step 1: Failing test**

In `tools/autocut/tests/test_broll_layout.py` anhängen:

```python
def _tele(datei, kb_mm, zooms=None, fenster=None):
    """Telemetrie-Datensatz wie in telemetrie.json; konstante Brennweite = ein kb_verlauf-Eintrag."""
    return {"path": f"/nas/Standort 1/Sortiert/B-Roll/Flur/{datei}", "clip": datei.split(".")[0],
            "quelle": "rtmd", "fps": 25.0, "dauer_s": 12.0, "fenster_s": 2.0,
            "kb_verlauf": [[0.0, kb_mm]], "zooms": zooms or [], "fenster": fenster or []}


def test_verify_layout_brennweitenfolge_meldet_gleiche_kb_am_schnitt():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    tele = [_tele("FX3_1.MP4", 25.0), _tele("FX3_2.MP4", 25.0), _tele("FX3_3.MP4", 70.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any("KB" in e and "FX3_1" in e and "FX3_2" in e for e in r.errors)   # 25,0 → 25,0 mm
    assert not any("KB" in e and "FX3_3" in e for e in r.errors)                # 25,0 → 70,0 mm ist weit genug


def test_verify_layout_brennweitenfolge_ohne_telemetrie_still():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, None)
    assert not any("KB" in e for e in r.errors)
    assert any("keine Telemetrie" in w for w in r.warnings)
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_broll_layout.py -k brennweitenfolge -v`
Expected: FAIL mit `TypeError: verify_layout() takes 6 positional arguments but 7 were given`

- [ ] **Step 3: Signatur und Regel einbauen**

In `broll_layout.py` oben ergänzen:

```python
from . import telemetrie as TM
```

Signatur (Zeile 561):

```python
def verify_layout(plan: LayoutPlan, tp_dict: dict, index: dict, cl: Cutlist, cfg: dict, fps: float,
                  tele: list[dict] | None = None) -> VerifyResult:
```

In der Cut-Flow-Schleife (Zeile 669 ff.) die Klassen-Dublette umbauen und die Regel ergänzen. Der Wächter
`a["strecke"] != b["strecke"]` bleibt: zwischen zwei Strecken liegt das Sprecher-Fenster, dort stoßen die
Shots nicht aneinander.

```python
    grenze = float((cfg.get("telemetrie") or {}).get("brennweite_gleich_max", 0.2))
    ungeprueft = 0
    for a, b in zip(seq, seq[1:]):
        if a["strecke"] != b["strecke"] or a["nachlauf_fehlt"] or b["nachlauf_fehlt"]:
            continue
        kb_a, kb_b = _kb_am_schnitt(a, tele, fps, "ende"), _kb_am_schnitt(b, tele, fps, "anfang")
        gleiche_kb = None
        if kb_a is not None and kb_b is not None:
            # NICHT selbst rechnen: brennweite_abstand() rundet auf vier Stellen, damit 60/50 genau 0,2 ergibt
            # (float: 1.2 - 1 = 0.19999999999999996 wäre sonst fälschlich „gleich")
            gleiche_kb = TM.gleiche_brennweite(kb_a, kb_b, grenze)
            if gleiche_kb:
                r.errors.append(f"Strecke {a['strecke']}: {a['name']} → {b['name']} schneiden dieselbe KB-Brennweite "
                                f"({kb_a:g} → {kb_b:g} mm, Abstand {TM.brennweite_abstand(kb_a, kb_b):.0%}) — anderen Shot wählen.")
        else:
            ungeprueft += 1
        if a["einstellung"] == b["einstellung"] and a["perspektive"] == b["perspektive"] and \
                (gleiche_kb if gleiche_kb is not None else a["brennweite"] == b["brennweite"]):
            r.errors.append(f"Strecke {a['strecke']}: {a['name']} → {b['name']} haben dieselbe Einstellung ({a['einstellung']}) "
                            f"und Perspektive ({a['perspektive']}) bei gleicher Brennweite — anderer Shot.")
        if a["setup_hash"] and b["setup_hash"] and _hamming(a["setup_hash"], b["setup_hash"]) < min_dist:
            r.warnings.append(f"Strecke {a['strecke']}: {a['name']} → {b['name']} sehen fast gleich aus (Setup-Abstand "
                              f"{_hamming(a['setup_hash'], b['setup_hash'])}).")
    if ungeprueft:
        r.warnings.append(f"{ungeprueft} Schnitte ohne Brennweitenverlauf — keine Telemetrie oder Datensatz von vor der "
                          f"Umstellung; Brennweitenregel dort nicht geprüft.")
    if not tele:
        r.warnings.append("keine Telemetrie — Brennweiten- und Zoomregel nicht geprüft.")
    else:
        # veraltete Datensätze der genutzten Clips melden, wie es die Vorlagen 3a/6d tun
        for hinweis in TM.telemetrie_hinweise([TM.finden(tele, p["clip"]) for p in seq], cfg.get("telemetrie") or {}):
            r.warnings.append(hinweis)
```

Und den Helfer direkt vor `verify_layout()` einfügen:

```python
def _kb_am_schnitt(p: dict, tele: list[dict] | None, fps: float, seite: str) -> float | None:
    """Scheinbare KB-Brennweite am Anfang bzw. Ende eines platzierten Shots; None ohne Verlauf.
    Bei Zeitlupe zählt der tatsächlich genutzte Quellbereich (wie 6d)."""
    if not tele:
        return None
    rec = TM.finden(tele, p["clip"])
    if not rec:
        return None
    clip_fps = float(rec.get("fps") or fps)
    von, bis = TM.genutzter_quellbereich_s(p["src_in_f"], p["rec_out_f"] - p["rec_in_f"], clip_fps,
                                           langsam=(p.get("tempo") or 1) > 1, ziel_fps=fps)
    return TM.kb_am(rec, bis if seite == "ende" else von, seite=seite)
```

- [ ] **Step 4: Tests laufen lassen, grün prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_broll_layout.py -q`
Expected: alle PASS (der alte Text „dieselbe Einstellung … Perspektive“ bleibt prüfbar, siehe
`test_verify_layout_rules`; schlägt er fehl, die Assertion dort auf den neuen Wortlaut anpassen)

- [ ] **Step 5: Skript anbinden**

In `tools/autocut/scripts/autocut_place_broll.py` den Import ergänzen:

```python
from niro_autocut import telemetrie as TM  # noqa: E402
```

und an **jeder** Aufrufstelle von `verify_layout(...)` die Telemetrie mitgeben:

```python
    tele = TM.laden(ch.autocut)
    r = verify_layout(plan, tp, index, cl, bcfg, fps, tele)
```

- [ ] **Step 6: Skript-Test laufen lassen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_resolve_scripts.py -q && venv/bin/python -m pytest -q`
Expected: alle PASS

- [ ] **Step 7: Commit**

```bash
git add tools/autocut/src/niro_autocut/broll_layout.py tools/autocut/scripts/autocut_place_broll.py tools/autocut/tests/test_broll_layout.py
git commit -m "feat(autocut): Brennweitenfolge in Stufe 3 v2 — nie zweimal dieselbe KB am Schnitt

verify_layout bekommt die Telemetrie-Datensätze und prüft die scheinbare
KB-Brennweite an der Schnittstelle (kb_am, bei Zeitlupe über den genutzten
Quellbereich). Die Shot-Dublette läuft über den mm-Abstand statt über Claudes
Klasse; ohne Verlauf fällt sie auf die Klasse zurück und der Shot wird gezählt.

Geprüft wird nur, wo Shots wirklich aneinanderstoßen — zwischen zwei Strecken
liegt das Sprecher-Fenster.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Regel 3b — kein schneller Zoom im genutzten Bereich

**Files:**
- Modify: `tools/autocut/src/niro_autocut/broll_layout.py` (Shot-Schleife in `verify_layout`, bei den übrigen
  Shot-Prüfungen um Zeile 636)
- Test: `tools/autocut/tests/test_broll_layout.py`

**Interfaces:**
- Consumes: `telemetrie.zooms_im_bereich(rec, von_s, bis_s, nur_schnelle=True) -> list[dict]` — Einträge mit
  `von_s`, `bis_s`, `von_mm`, `bis_mm`, `tempo_max`, `urteil`.
- Produces: Fehlertext enthält `"schneller Zoom"` und das Spitzentempo.

- [ ] **Step 1: Failing test**

```python
def test_verify_layout_schneller_zoom_im_genutzten_bereich():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    schnell = [{"von_s": 1.0, "bis_s": 2.0, "von_mm": 74.1, "bis_mm": 25.4, "tempo_max": 242.0,
                "tempo_mittel": 180.0, "urteil": "schnell"}]
    langsam = [{"von_s": 1.0, "bis_s": 2.0, "von_mm": 30.0, "bis_mm": 35.0, "tempo_max": 28.0,
                "tempo_mittel": 20.0, "urteil": "langsam"}]
    tele = [_tele("FX3_1.MP4", 25.0, schnell), _tele("FX3_2.MP4", 70.0, langsam), _tele("FX3_3.MP4", 35.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any("schneller Zoom" in e and "FX3_1" in e for e in r.errors)
    assert not any("schneller Zoom" in e and "FX3_2" in e for e in r.errors)


def test_verify_layout_schneller_zoom_mit_abweichung_erlaubt():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    plan.strecken[0].szenen[0].shots[0].abweichung = True
    plan.strecken[0].szenen[0].shots[0].abweichung_grund = "Plan verlangt genau diese Fahrt"
    schnell = [{"von_s": 1.0, "bis_s": 2.0, "von_mm": 74.1, "bis_mm": 25.4, "tempo_max": 242.0,
                "tempo_mittel": 180.0, "urteil": "schnell"}]
    tele = [_tele("FX3_1.MP4", 25.0, schnell), _tele("FX3_2.MP4", 70.0), _tele("FX3_3.MP4", 35.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert not any("schneller Zoom" in e for e in r.errors)
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_broll_layout.py -k schneller_zoom -v`
Expected: FAIL — keine Fehlermeldung mit „schneller Zoom“

- [ ] **Step 3: Regel einbauen**

In der Shot-Schleife von `verify_layout`, direkt nach der `abweichung`-Prüfung (Zeile 636 f.):

```python
        rec = TM.finden(tele, p["clip"]) if tele else None
        von = bis = None
        if rec:
            clip_fps = float(rec.get("fps") or fps)
            # außerhalb der abweichung-Bedingung: Task 5 rechnet auf denselben Grenzen weiter
            von, bis = TM.genutzter_quellbereich_s(p["src_in_f"], p["rec_out_f"] - p["rec_in_f"], clip_fps,
                                                   langsam=(p.get("tempo") or 1) > 1, ziel_fps=fps)
            if not p["abweichung"]:
                for z in TM.zooms_im_bereich(rec, von, bis):
                    r.errors.append(f"{tag}: schneller Zoom im genutzten Bereich ({z['von_mm']:g} → {z['bis_mm']:g} mm, "
                                    f"Spitze {z['tempo_max']:.0f} %/s) — anderen Bereich wählen oder `abweichung` mit Grund.")
```

- [ ] **Step 4: Tests laufen lassen, grün prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_broll_layout.py -q`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add tools/autocut/src/niro_autocut/broll_layout.py tools/autocut/tests/test_broll_layout.py
git commit -m "feat(autocut): Stufe 3 v2 lehnt schnelle Zoomfahrten im genutzten Bereich ab

zooms_im_bereich auf dem tatsächlich genutzten Quellbereich (Zeitlupe über
genutzter_quellbereich_s). Ausweg bleibt abweichung mit Grund. Die Grenze
(100 %/s Spitze, Sprung 12 % in 0,12 s) ist am 21.09. an 10 Beispielen abgenommen.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Regel 3c — Schnittgrenze in einer Bewegungsspitze (nur Warnung)

**Files:**
- Modify: `tools/autocut/defaults.yaml` (Block `telemetrie:`)
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (`OHNE_MESSWIRKUNG`, neuer Helfer)
- Modify: `tools/autocut/src/niro_autocut/broll_layout.py` (Shot-Schleife in `verify_layout`)
- Test: `tools/autocut/tests/test_telemetrie.py`, `tools/autocut/tests/test_broll_layout.py`

**Interfaces:**
- Produces: `bewegung_grundniveau(rec: dict | None, t_s: float, abstand_s: float = 3.0) -> float | None` —
  Median der `bewegung` aller Fenster, die mindestens `abstand_s` von `t_s` entfernt liegen; None ohne solche
  Fenster. Warnungstext enthält `"Bewegungsspitze"`.

- [ ] **Step 1: Config-Schlüssel eintragen**

In `tools/autocut/defaults.yaml` unter `telemetrie:` hinter `digitalzoom_max` ergänzen:

```yaml
  bewegung_rand_s: 0.5          # Abstand einer Schnittgrenze zu einer Bewegungsspitze (UNKALIBRIERT, nur Warnung)
  bewegung_spitze_faktor: 3.0   # ab dem Vielfachen des Grundniveaus zählt eine Spitze (UNKALIBRIERT, nur Warnung)
```

- [ ] **Step 2: Failing test für Hash und Helfer**

In `tools/autocut/tests/test_telemetrie.py` anhängen:

```python
def test_neue_schluessel_aendern_den_config_hash_nicht():
    """Sonst gälte jede vorhandene telemetrie.json als veraltet und würde neu gemessen."""
    import yaml
    from pathlib import Path
    cfg = yaml.safe_load((Path(__file__).resolve().parents[1] / "defaults.yaml").read_text())["telemetrie"]
    vorher = T.config_hash({k: v for k, v in cfg.items()
                            if k not in ("bewegung_rand_s", "bewegung_spitze_faktor")})
    assert T.config_hash(cfg) == vorher


def test_bewegung_grundniveau_nimmt_nur_entfernte_fenster():
    rec = {"fenster": [[0.0, 0.1, 0.4, "fahrt", None],
                       [1.0, 0.1, 0.6, "fahrt", None],
                       [4.0, 0.1, 9.0, "schwenk_links", None],   # die Spitze selbst
                       [8.0, 0.1, 0.5, "fahrt", None]]}
    assert T.bewegung_grundniveau(rec, 4.0, 3.0) == 0.5          # Median von 0,4 / 0,6 / 0,5
    assert T.bewegung_grundniveau({"fenster": []}, 4.0, 3.0) is None
```

- [ ] **Step 3: Test laufen lassen, Fehlschlag prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py -k "config_hash_nicht or grundniveau" -v`
Expected: FAIL — Hash weicht ab, `bewegung_grundniveau` fehlt

- [ ] **Step 4: Helfer und Hash-Ausnahme schreiben**

In `telemetrie.py` Zeile 388 erweitern:

```python
OHNE_MESSWIRKUNG = ("parallel", "brennweite_gleich_max", "digitalzoom_faktor", "digitalzoom_max",
                    "bewegung_rand_s", "bewegung_spitze_faktor")
```

Und hinter `bewegung_spitzen()` einfügen:

```python
def bewegung_grundniveau(rec: dict | None, t_s: float, abstand_s: float = 3.0) -> float | None:
    """Median der ``bewegung`` aller Fenster, die mindestens ``abstand_s`` von ``t_s`` entfernt liegen — das
    Grundniveau des Clips ohne die Spitze selbst. None ohne solche Fenster (Spec 2026-09-22)."""
    fern = [float(f[2]) for f in ((rec or {}).get("fenster") or []) if abs(float(f[0]) - t_s) >= abstand_s]
    return float(np.median(fern)) if fern else None
```

- [ ] **Step 5: Tests laufen lassen, grün prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py -q`
Expected: alle PASS

- [ ] **Step 6: Failing test für die Regel**

In `tools/autocut/tests/test_broll_layout.py` anhängen:

```python
def test_verify_layout_bewegungsspitze_an_der_schnittgrenze_warnt_nur():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    # Shot 1 endet bei 3,0 s; Spitze bei 3,0 s mit 9,0 gegen Grundniveau 0,5 = Faktor 18
    fen = [[0.0, 0.1, 0.4, "fahrt", None], [1.0, 0.1, 0.6, "fahrt", None],
           [3.0, 0.1, 9.0, "schwenk_links", None], [8.0, 0.1, 0.5, "fahrt", None]]
    tele = [_tele("FX3_1.MP4", 25.0, None, fen), _tele("FX3_2.MP4", 70.0), _tele("FX3_3.MP4", 35.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any("Bewegungsspitze" in w for w in r.warnings)
    assert not any("Bewegungsspitze" in e for e in r.errors)     # NIE ein Fehler: Schwellen unkalibriert
```

- [ ] **Step 7: Test laufen lassen, Fehlschlag prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_broll_layout.py -k bewegungsspitze -v`
Expected: FAIL — keine Warnung mit „Bewegungsspitze“

- [ ] **Step 8: Regel einbauen**

In der Shot-Schleife von `verify_layout`, direkt hinter dem Zoom-Block aus Task 4:

```python
        if rec and von is not None:
            tcfg = cfg.get("telemetrie") or {}
            rand = float(tcfg.get("bewegung_rand_s", 0.5))
            faktor = float(tcfg.get("bewegung_spitze_faktor", 3.0))
            for t_s, bw in TM.bewegung_spitzen(rec, von - rand, bis + rand):
                if min(abs(t_s - von), abs(t_s - bis)) > rand:
                    continue
                grund_px = TM.bewegung_grundniveau(rec, t_s)
                if grund_px and bw >= faktor * grund_px:
                    r.warnings.append(f"{tag}: Schnittgrenze bei {t_s:g} s liegt in einer Bewegungsspitze "
                                      f"({bw:g} gegen Grundniveau {grund_px:g}) — Hinweis, Schwellen unkalibriert.")
```

- [ ] **Step 9: Tests laufen lassen, grün prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest -q`
Expected: alle PASS

- [ ] **Step 10: Commit**

```bash
git add tools/autocut/defaults.yaml tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/src/niro_autocut/broll_layout.py tools/autocut/tests/test_telemetrie.py tools/autocut/tests/test_broll_layout.py
git commit -m "feat(autocut): Hinweis auf Schnittgrenzen in einer Bewegungsspitze (Warnung)

Warnt, wenn ein Shot an einer lokalen Bewegungsspitze beginnt oder endet, die
mindestens bewegung_spitze_faktor über dem Grundniveau des Clips liegt.

Bewusst nur eine Warnung: beide Schwellen sind UNKALIBRIERT. Die Kalibrierung
vom 22.09. hat gezeigt, dass keine gemessene Bewegungsgröße gewollte von
ungewollter Kamerabewegung trennt (30 Urteile, beide Kandidatenmuster schlechter
als die triviale Konstante). Eine Erhebung zum Fehler setzt eine Kalibrierung
voraus, die diesen Testsatz schlägt.

Die neuen Schlüssel stehen in OHNE_MESSWIRKUNG — sonst gälte jede vorhandene
telemetrie.json als veraltet.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Bericht und Doku

**Files:**
- Modify: `tools/autocut/src/niro_autocut/broll_layout.py` (`render_layout_md`, Zeile 740-768)
- Modify: `tools/autocut/WORKFLOW-AutoCut.md` (Stufe 2b, Stufe 3, Telemetrie-Abschnitt)
- Modify: `tools/autocut/prompts/place-broll.md`
- Modify: `tools/autocut/README.md`
- Test: `tools/autocut/tests/test_broll_layout.py`, `tools/autocut/tests/test_docs.py`

**Interfaces:**
- Consumes: `VerifyResult.warnings` aus den Tasks 3–5.
- Produces: Spalte „KB" in der Shot-Tabelle von `render_layout_md`.

- [ ] **Step 1: Failing test für die Berichtsspalte**

```python
def test_render_layout_md_zeigt_kb_brennweite():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    tele = [_tele("FX3_1.MP4", 25.4), _tele("FX3_2.MP4", 70.0), _tele("FX3_3.MP4", 35.0)]
    placed, _ = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    r = L.raster(TP, CL, CFG, plan)
    md = L.render_layout_md(plan, placed, r, idx, CL, tele=tele)
    assert "| KB |" in md and "25,4 mm" in md
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_broll_layout.py -k render_layout_md_zeigt_kb -v`
Expected: FAIL mit `TypeError: render_layout_md() got an unexpected keyword argument 'tele'`

- [ ] **Step 3: Bericht erweitern**

`render_layout_md` bekommt den Parameter `tele: list[dict] | None = None`, die Kopfzeile der Shot-Tabelle
(Zeile 753) die Spalte `KB` hinter `Brennweite`, und je Zeile:

```python
            kb = _kb_am_schnitt(p, tele, fps, "anfang")
            kb_txt = "–" if kb is None else f"{kb:g} mm".replace(".", ",")
```

`kb_txt` in die Zeile einsetzen; im Aufrufer `autocut_place_broll.py` `tele=tele` mitgeben.

- [ ] **Step 4: Test laufen lassen, grün prüfen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_broll_layout.py -q`
Expected: alle PASS

- [ ] **Step 5: Doku nachziehen**

`WORKFLOW-AutoCut.md`:
- Stufe 2b: `bewegung_spitzen` in der Feldliste ergänzen.
- Stufe 3, Punkt 4 („Prüfen"): die drei Regeln nennen — Brennweitenfolge und schneller Zoom als Fehler,
  Bewegungsspitze als Warnung mit dem Zusatz „Schwellen unkalibriert".
- Telemetrie-Abschnitt: „Abnehmer" um „Stufe 3 (Brennweitenfolge, Zoom, Bewegungsspitzen)" erweitern; unter
  „Kalibrierwerte" das negative Ergebnis vom 22.09. aufnehmen (zwei Runden, 30 Urteile, beide Muster 10 von 18
  gegen 15 der trivialen Konstante; kein Vorfilter).

`prompts/place-broll.md`: die fünf neuen Felder des kompakten Index beschreiben und die Regeln, auf die der Plan
achten muss (kein Schnitt auf gleiche KB, keine schnellen Zoomfahrten im genutzten Bereich).

`README.md`: Tabellenzeile zu Stufe 3 um die Telemetrie-Regeln ergänzen.

- [ ] **Step 6: Doku-Test laufen lassen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_docs.py -q && venv/bin/python -m pytest -q`
Expected: alle PASS

- [ ] **Step 7: Commit**

```bash
git add tools/autocut/src/niro_autocut/broll_layout.py tools/autocut/scripts/autocut_place_broll.py tools/autocut/WORKFLOW-AutoCut.md tools/autocut/prompts/place-broll.md tools/autocut/README.md tools/autocut/tests/test_broll_layout.py
git commit -m "docs(autocut): Stufe-3-Bericht mit KB-Spalte, Workflow und Prompt nachgezogen

Der B-Roll-Bericht zeigt je Shot die gemessene KB-Brennweite am Anfang. Workflow
und place-broll-Prompt nennen die neuen Indexfelder und die drei Regeln; der
Telemetrie-Abschnitt hält das negative Kalibrierergebnis vom 22.09. fest.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Abnahme auf MEK (nach Task 6, keine API-Kosten)

Charge: `projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh`.
Medien auf `NIRO-SSD-03` unter `01_Projekt-2xAds1xImagefilm_24.06.26`. Vorher `Protokoll.md` der Charge
fortschreiben (Pflicht laut `CLAUDE.md`), und wenn das NAS verbunden ist, vorher und nachher
`sh tools/studio_abgleich.sh --charge "<Pfad>"`.

1. `venv/bin/python scripts/autocut_telemetrie.py "<Charge>"` — der Config-Hash der vorhandenen Datei
   (`508cf894e9e3`) weicht vom heutigen ab, der Lauf misst alle 463 Clips neu. Nur I/O über die SSD.
2. `venv/bin/python scripts/autocut_index_sections.py "<Charge>"` — trägt die Abschnittsfelder aus dem
   Cache nach, **ohne API-Aufruf** (`felder_quelle` ist dort noch 0 von 1026).
3. `venv/bin/python scripts/autocut_place_broll.py "<Charge>" --compact`
4. `venv/bin/python scripts/autocut_place_broll.py "<Charge>" --verify-only` auf den vorhandenen
   `broll_plan.json`. Erwartung aus der Vorab-Probe: **5 Brennweiten-Verstöße bei 43 echten Schnitten** und
   **mindestens 7 Zoom-Verstöße bei 68 Shots**. Weichen die Zahlen ab, erst die Ursache klären, nicht die
   Regel anpassen.
5. Erst danach neu planen und beide Pläne auf denselben Strecken vergleichen.

## Nicht in diesem Plan

- **Vorfilter vor dem Index** — am 22.09. widerlegt.
- **Digitaler Zoom in v2** — 3a und 6d setzen ihn, v2 nicht; eigener Plan, falls der Vergleich zeigt, dass die
  Brennweitenregel zu oft keinen Ausweg lässt.
- **Erkennen von Absicht** — braucht den Bildinhalt, nicht die Telemetrie.
- **Ablösung von Stufe 3a** — erst nach dem Vergleich zu entscheiden; 3a bleibt unverändert.
