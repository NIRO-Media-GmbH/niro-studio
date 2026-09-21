# AutoCut Zoomfahrten und Brennweitenwechsel — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aus der KB-Brennweite der Sony-rtmd-Spur je Clip Zoomfahrten erkennen und als langsam/schnell beurteilen (`kb_verlauf`, `zooms` in `telemetrie.json`), die Brennweitenklassen durch Millimeter ersetzen (Bericht, Stufe 2b) und in den Vorlagen 3a/6d die Regel „nie zweimal dieselbe Brennweite direkt hintereinander" mit automatischem digitalem Zoom und Hinweisen auf schnelle Zooms umsetzen — Schwellen danach mit dem User an echten Beispielen kalibrieren.

**Architecture:** Die ganze Logik liegt als reine, verhaltensgetestete Funktionen in `tools/autocut/src/niro_autocut/telemetrie.py`: Zoom-Erkennung auf einer 25-fps-Brennweitenreihe (Median 0,2 s, Tempo = Änderung von ln(KB) in % pro s), Helfer für Brennweite im Bereich, `digitalzoom` und `brennweitenfolge` (die komplette Paar-Regel). `rtmd.py` liefert dazu die Sample-Nummer je Brennweitenwert. Bericht (`telemetrie_bericht.py`), Stufe 2b (`index_sections.py`) und die Vorlagen 3a/6d rufen die Helfer nur auf, formatieren Hinweiszeilen und setzen beim Bau `ZoomX`/`ZoomY`.

**Tech Stack:** Python 3.12 (AutoCut-venv: numpy, scipy, PyYAML, Pillow; **keine neue Abhängigkeit**), ffmpeg 9 (ohne drawtext), pytest. Resolve nur in den Vorlagen beim Bau, NAS nur lesend.

Spec: `docs/superpowers/specs/2026-09-21-autocut-zoom-brennweite-design.md` (Hintergrund: `docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md`).

## Global Constraints

- **Worktree:** Umsetzung in einem Git-Worktree (superpowers:using-git-worktrees), Branch `autocut-zoom-brennweite`, Pfad
  `/Users/jansantos/NIRO Studio/.claude/worktrees/autocut-zoom-brennweite`. Der Worktree braucht die venv als Verknüpfung:
  `ln -s "/Users/jansantos/NIRO Studio/tools/autocut/venv" tools/autocut/venv` (im Worktree-Root ausführen). Alle Befehle
  der Tasks 1–8 laufen im Worktree-Root; Tests: `cd tools/autocut && venv/bin/python -m pytest -q`.
- **Basis grün:** `main` ab 6fb900b (Doku-Test auf „zehn Funktionen" nachgezogen): Gesamtlauf `601 passed, 1 skipped`.
  „Grün" heißt in diesem Plan: alles bestanden, nur der opt-in-Skip.
- **Chargen-Daten nur im Hauptordner:** `projects/` gibt es nur in `/Users/jansantos/NIRO Studio` (CLAUDE.md). Die
  Kalibrier-Tasks 9/10 rufen den Code des Worktrees mit absoluten Chargen-Pfaden des Hauptordners auf.
- **Zeilen ≤ 125 Zeichen** in Code, Tests und YAML; Deutsch in Kommentaren, Docstrings, Feldnamen, Meldungen; Stil wie
  `telemetrie.py` (Abschnitts-Kommentare `# --- … ---`, kurze Docstrings mit Einheiten).
- **Logik nur in `telemetrie.py`**, getestet mit handgerechneten Erwartungswerten; die Vorlagen rufen `kb_am`,
  `zoom_hinweise` und `brennweitenfolge` auf und setzen Resolve-Eigenschaften (Resolve-Aufrufe ungetestet, Syntax geprüft).
- **Einheiten:** Zeiten der Helfer sind Quell-Sekunden im Clip (rtmd-Sample i = Quellframe i, t = i / clip_fps).
  Timeline-Frames zählen mit 25 fps. 6d: genutzter Quellbereich über `TM.genutzter_quellbereich_s` (bei 50 % halb so
  lang); 3a: Tempo 100 %. Brennweite am Schnitt = `kb_am(A, Ende des genutzten Bereichs von A, seite="ende")` gegen
  `kb_am(B, Anfang des genutzten Bereichs von B, seite="anfang")`, je mal vorhandenem Zoom.
- **Robustheit:** Fehler je Clip brechen nie einen Lauf ab (unverändert). Datensätze ohne `kb_verlauf`/`zooms` (vor der
  Umstellung gemessen, Drohne) gelten als „Brennweite unbekannt" — kein Absturz, keine Regel.
- **Konfiguration (`defaults.yaml`, Block `telemetrie:`, nur am Blockende ergänzen):** neu `zoom_min_proz`,
  `zoom_rausch_proz_s`, `zoom_schnell_proz_s`, `zoom_ruck_max`, `zoom_stocken_anteil`, `zoom_verlauf_hz` (Task 1),
  `brennweite_gleich_max`, `digitalzoom_faktor`, `digitalzoom_max` (Task 4); entfällt `brennweite_klassen_kb` (Task 6).
  Jede Änderung ändert den Config-Hash der Telemetrie — der nächste Lauf misst jeden Clip einmal neu (gewollt).
- **Ergänzungen zum Spec (bewusst, im Code dokumentiert):** `zoom_rausch_proz_s` (1,0 %/s; der Spec nennt „eine
  Rauschgrenze" ohne Wert) und `zoom_stocken_anteil` (0,2 = die 20 % des Specs, als Schlüssel, damit die Kalibrierung ihn
  stellen kann); Zoom-Datensatz zusätzlich `ruckartig` (bool); `RtmdDaten.kb_index` (Samples ohne KB-Tag oder mit 0xFFFF
  fehlen in `kb_mm` — ohne Index verrutscht die Zeitachse); `digitalzoom(…, b_erlaubt=True)` (Spalte `zoom` legt auch B
  fest); `brennweitenfolge` liefert zusätzlich `fehler`; ein erzwungener Zoom unter 1,0 ist wie einer über
  `digitalzoom_max` ein Plan-Fehler (Rand würde sichtbar).
- **Commits:** nur die Dateien der Task stagen (`git add <Pfade>`), nie `git add -A`. Im Hauptordner liegt fremde offene
  Arbeit (`CLAUDE.md`, `tools/motion/**`, `tools/resolve/WORKFLOW-Resolve.md`, `tools/thumbnail/**`,
  `docs/superpowers/*thumbnail*`). Nicht anfassen: `media.py`, `resolve_api.py`, `sync.py`, `timeline_model.py`,
  `cutlist.py`, `resolve_probe.py` (offene Änderungen auf dem MacBook). Commit-Text deutsch, `feat(autocut):` /
  `test(autocut):` / `docs(autocut):`, Abschluss `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- `tests/test_docs.py` verlangt, dass jedes `scripts/*.py` dokumentiert ist — dieser Plan legt kein neues Skript im
  Werkzeug an (die Kalibrier-Skripte liegen in der Kalibrier-Charge).
- **Änderungsanweisungen:** „Ersetzen in `<Datei>`" = den ersten Block genau einmal im Text finden und durch den zweiten
  ersetzen; „Anhängen an `<Datei>`" = am Dateiende anfügen (bei `.py` mit zwei Leerzeilen Abstand); „Neue Datei" = anlegen.

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `tools/autocut/src/niro_autocut/telemetrie.py` | Zoomfahrten (Task 1), Einbau in `clip_messen`/`ruhige_fenster` (Task 2), Brennweite im Bereich und Texte (Task 3), Brennweitenfolge und digitaler Zoom (Task 4); `brennweitenklasse` entfällt (Task 6) |
| `tools/autocut/src/niro_autocut/rtmd.py` | `RtmdDaten.kb_index` (Task 2) |
| `tools/autocut/src/niro_autocut/telemetrie_bericht.py` | Brennweite in mm je Kamera, Abschnitt „Schnelle Zoomfahrten", Vergleich ohne Brennweite (Task 5) |
| `tools/autocut/src/niro_autocut/index_sections.py` | Stufe 2b: `brennweite_mm`/`zoom` je Abschnitt, Claudes Klasse bleibt, Kontextzeile in mm (Task 6) |
| `tools/autocut/scripts/autocut_index_sections.py`, `tools/autocut/prompts/index-sections.md` | Meldungen und Regel 4 ohne Brennweiten-Überschreiben (Task 6) |
| `tools/autocut/defaults.yaml` | Block `telemetrie:` (Tasks 1, 4, 6, 10) |
| `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py` | 6d: Spalte 8 `zoom`, Hinweise, `ZoomX`/`ZoomY` beim Bau, Readback (Task 7) |
| `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py` | 3a: Spalte 7 `zoom`, Hinweise, `ZoomX`/`ZoomY` beim Bau, Readback (Task 8) |
| `tools/autocut/WORKFLOW-AutoCut.md`, `tools/autocut/README.md`, `tools/autocut/vorlagen/README.md` | Doku (Tasks 2, 5–8, 10) |
| `tools/autocut/tests/test_telemetrie.py`, `test_rtmd.py`, `test_telemetrie_bericht.py`, `test_index_sections.py`, `test_vorlagen_telemetrie.py` | Tests |
| `tools/autocut/tests/fixtures/kb_zoom_kalibrierung.json` (Task 10) | echte KB-Reihen: Drehteller-Referenz und MEK-Gegenprobe |
| `docs/superpowers/specs/2026-09-21-autocut-zoom-brennweite-design.md` | Status, Nachtrag „Kalibrierung Zoom" (Task 10) |
| Kalibrier-Charge `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten/` (nicht im Repo) | `Protokoll.md`, `_intern/skripte/zoom_beispiele.py` (Task 9), `_intern/skripte/zoom_kalibrieren.py` (Task 10), `beispiele.json`, `urteile.json`, `kb_reihen.json`, `work/zoom-beispiele.mp4` |

---

### Task 1: Zoomfahrten erkennen — reine Funktionen in `telemetrie.py`

**Files:**
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (Modul-Docstring; neuer Abschnitt „Zoomfahrten" vor `# --- Clip-Messung`)
- Modify: `tools/autocut/defaults.yaml` (Block `telemetrie:` am Dateiende um sechs Schlüssel ergänzen)
- Test: `tools/autocut/tests/test_telemetrie.py` (`CFG` ergänzen, Tests anhängen)

**Interfaces:**
- Consumes: `ZIEL_FPS`, `_tiefpass(x, breite)` aus `telemetrie.py`; `cfg` = `defaults.yaml["telemetrie"]`
- Produces:
  - Konstanten `ZOOM_MEDIAN_S = 0.2`, `ZOOM_GLAETTUNG_S = 0.2`, `ZOOM_LUECKE_S = 0.3`, `ZOOM_KERN_RAND = 0.10`,
    `ZOOM_RUCK_SCHRITT_S = 0.2`, `URTEILE_ZOOM = ["langsam", "schnell"]`
  - `kb_je_frame(kb_mm: list[float], kb_index: list[int] | None, fps: float, samples: int, ziel_fps: float = ZIEL_FPS) -> np.ndarray`
  - `zoom_tempo(kb25: np.ndarray, ziel_fps: float = ZIEL_FPS) -> np.ndarray` (% pro s je Zielframe)
  - `zoom_bereiche(v: np.ndarray, cfg: dict, ziel_fps: float = ZIEL_FPS) -> list[tuple[int, int]]` (Frames [a, b))
  - `zoom_ruck(betrag: np.ndarray, stocken_anteil: float, ziel_fps: float = ZIEL_FPS) -> tuple[float, bool]` (ruck, stockt)
  - `zoomfahrten(kb25: np.ndarray, cfg: dict, ziel_fps: float = ZIEL_FPS) -> list[dict]` — je Fahrt
    `{von_s, bis_s, von_mm, bis_mm, tempo_max, tempo_mittel, ruck, ruckartig, urteil}`
  - `kb_verlauf(kb25: np.ndarray, cfg: dict, ziel_fps: float = ZIEL_FPS) -> list[list[float]]`
  - `zoom_messen(kb_mm: list[float], kb_index: list[int] | None, fps: float, samples: int, cfg: dict) -> dict` (`kb_verlauf`, `zooms`)
  - `defaults.yaml`: `zoom_min_proz 3.0`, `zoom_rausch_proz_s 1.0`, `zoom_schnell_proz_s 20.0`, `zoom_ruck_max 0.6`,
    `zoom_stocken_anteil 0.2`, `zoom_verlauf_hz 5`

- [ ] **Step 1: Failing Tests schreiben**

**Ersetzen in `tools/autocut/tests/test_telemetrie.py`:**

```python
       "px_faktor": {"FX3": 1.0, "a7IV": 1.0}, "optisch_fuer": [], "optisch_breite": 480, "parallel": 2}
```

**durch:**

```python
       "px_faktor": {"FX3": 1.0, "a7IV": 1.0}, "optisch_fuer": [], "optisch_breite": 480, "parallel": 2,
       "zoom_min_proz": 3.0, "zoom_rausch_proz_s": 1.0, "zoom_schnell_proz_s": 20.0, "zoom_ruck_max": 0.6,
       "zoom_stocken_anteil": 0.2, "zoom_verlauf_hz": 5}
```

**Anhängen an `tools/autocut/tests/test_telemetrie.py`:**

```python
# --- Zoomfahrten (Spec 2026-09-21, Abschnitt 1) ----------------------------------------------------------------------

def _zoomreihe(*stuecke: tuple[float, float, float], fps: float = 25.0) -> list[float]:
    """KB-Brennweite je Sample aus Stücken (Dauer s, mm von, mm bis), log-linear, auf 0,1 mm gerundet wie die Kamera."""
    werte: list[float] = []
    for dauer, von, bis in stuecke:
        n = int(round(dauer * fps))
        werte += np.exp(np.linspace(math.log(von), math.log(bis), n, endpoint=False)).tolist()
    werte.append(stuecke[-1][2])
    return [round(w, 1) for w in werte]


def _fahrten(kb: list[float], fps: float = 25.0) -> list[dict]:
    return T.zoomfahrten(T.kb_je_frame(kb, None, fps, len(kb)), CFG)


def test_defaults_haben_zoom_schluessel():
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    for k in ("zoom_min_proz", "zoom_rausch_proz_s", "zoom_schnell_proz_s", "zoom_ruck_max", "zoom_stocken_anteil",
              "zoom_verlauf_hz"):
        assert k in cfg


def test_kb_je_frame_median_raster_und_luecken():
    ausreisser = [50.0] * 10 + [80.0] + [50.0] * 10
    assert np.allclose(T.kb_je_frame(ausreisser, None, 25.0, 21), 50.0)         # Median über 0,2 s (5 Samples)
    reihe50 = _zoomreihe((1.0, 24, 24), (4.0, 24, 36), (1.0, 36, 36), fps=50.0)  # 301 Samples bei 50p
    k50 = T.kb_je_frame(reihe50, None, 50.0, len(reihe50))
    assert len(k50) == 150 and k50[0] == 24.0 and k50[-1] == 36.0              # 25-fps-Raster
    idx = [i for i in range(len(reihe50)) if i % 3]                             # jedes dritte Sample ohne Brennweite
    luecken = T.kb_je_frame([reihe50[i] for i in idx], idx, 50.0, len(reihe50))
    assert len(luecken) == 150 and float(np.abs(luecken - k50).max()) < 0.5
    assert len(T.kb_je_frame([], [], 25.0, 100)) == 0
    assert np.allclose(T.kb_je_frame([50.0, 50.0], [0, 1, 2], 25.0, 2), 50.0)   # unpassender Index: lückenlos


def test_zoomfahrten_festbrennweite_und_rauschen():
    assert _fahrten([50.0] * 100) == []
    rng = np.random.default_rng(1)
    assert _fahrten((50.0 + 0.1 * rng.integers(0, 2, 200)).round(1).tolist()) == []     # Quantisierung 0,1 mm
    atmen = [round(50.0 * (1 + 0.01 * math.sin(math.pi * k / 25.0)), 1) for k in range(200)]
    assert _fahrten(atmen) == []                                                 # Fokus-Atmen ±1 % < zoom_min_proz


def test_zoomfahrt_langsam_gleichmaessig():
    z = _fahrten(_zoomreihe((1.0, 24, 24), (4.0, 24, 36), (1.0, 36, 36)))
    assert len(z) == 1 and z[0]["urteil"] == "langsam" and z[0]["ruckartig"] is False
    # ln(36/24) / 4 s = 10,1 % pro s; 0,1-mm-Stufen und Glättung heben die Spitze etwas an
    assert 9.0 < z[0]["tempo_max"] < 13.0 and z[0]["tempo_mittel"] < z[0]["tempo_max"] and z[0]["ruck"] < 0.1
    assert abs(z[0]["von_s"] - 1.0) <= 0.15 and abs(z[0]["bis_s"] - 5.0) <= 0.15
    assert (z[0]["von_mm"], z[0]["bis_mm"]) == (24.0, 36.0)


def test_zoomfahrt_schnell():
    z = _fahrten(_zoomreihe((1.0, 24, 24), (0.8, 24, 70), (1.0, 70, 70)))
    # ln(70/24) / 0,8 s = 134 % pro s
    assert len(z) == 1 and z[0]["urteil"] == "schnell" and 120.0 < z[0]["tempo_max"] < 145.0
    assert (z[0]["von_mm"], z[0]["bis_mm"]) == (24.0, 70.0) and z[0]["ruckartig"] is False


def test_zoom_ruck_variationskoeffizient_und_stocken():
    # 20 Frames, Kern ohne je 2 Frames: Mittel der 5er-Schritte 6,4 / 4,6 / 10,0 → CV 2,245 / 7,0 = 0,32;
    # |v| fällt im Kern unter 20 % der Spitze (1 < 2) und steigt wieder → Stocken
    ruck, stockt = T.zoom_ruck(np.array([10.0] * 5 + [1.0] * 5 + [10.0] * 10), 0.2)
    assert ruck == pytest.approx(0.32, abs=0.005) and stockt is True
    assert T.zoom_ruck(np.full(20, 10.0), 0.2) == (0.0, False)
    assert T.zoom_ruck(np.linspace(0.0, 10.0, 20), 0.2)[1] is False            # Anlauf ist kein Stocken
    assert T.zoom_ruck(np.array([]), 0.2) == (0.0, False)


def test_zoomfahrt_mit_stocken_ist_ruckartig():
    # 15 % pro s (unter zoom_schnell_proz_s 20), dazwischen 0,2 s Halt: eine Fahrt, Stocken → ruckartig → schnell
    z = _fahrten(_zoomreihe((1.0, 24, 24), (1.0, 24, 27.9), (0.2, 27.9, 27.9), (1.0, 27.9, 32.4), (1.0, 32.4, 32.4)))
    assert len(z) == 1 and z[0]["tempo_max"] < 20.0
    assert z[0]["ruckartig"] is True and z[0]["urteil"] == "schnell"


def test_stop_and_go_unter_0_3_s_ist_eine_fahrt():
    def halt(s: float) -> list[float]:
        return _zoomreihe((1.0, 24, 24), (0.5, 24, 32.4), (s, 32.4, 32.4), (0.5, 32.4, 43.7), (1.0, 43.7, 43.7))
    eine = _fahrten(halt(0.2))
    assert len(eine) == 1 and (eine[0]["von_mm"], eine[0]["bis_mm"]) == (24.0, 43.7) and eine[0]["ruckartig"] is True
    zwei = _fahrten(halt(0.6))
    assert [(z["von_mm"], z["bis_mm"]) for z in zwei] == [(24.0, 32.4), (32.4, 43.7)]


def test_stufiger_sprung_ist_schnell():
    # Klarbild-Zoom der a7 IV schaltet stufig: 50 → 60 mm in zwei Frames (+20 %)
    z = _fahrten(_zoomreihe((1.0, 50, 50), (0.08, 50, 60), (1.0, 60, 60)))
    assert len(z) == 1 and z[0]["urteil"] == "schnell" and z[0]["tempo_max"] > 20.0
    assert (z[0]["von_mm"], z[0]["bis_mm"]) == (50.0, 60.0)


def test_kb_verlauf_kompakt_und_5_hz():
    assert T.kb_verlauf(np.full(100, 50.0), CFG) == [[0.0, 50.0]]
    assert T.kb_verlauf(np.array([50.0, 51.0, 50.4]), CFG) == [[0.0, 50.4]]    # 2 % < zoom_min_proz: Median
    k = T.kb_je_frame(_zoomreihe((1.0, 24, 24), (4.0, 24, 36), (1.0, 36, 36)), None, 25.0, 151)
    v = T.kb_verlauf(k, CFG)
    assert len(v) == 31 and v[:2] == [[0.0, 24.0], [0.2, 24.0]] and v[-1] == [6.0, 36.0]
    assert all(round(b[0] - a[0], 2) == 0.2 for a, b in zip(v, v[1:]))
    assert T.kb_verlauf(np.zeros(0), CFG) == []


def test_zoom_messen():
    assert T.zoom_messen([], [], 25.0, 100, CFG) == {"kb_verlauf": [], "zooms": []}
    assert T.zoom_messen([71.6] * 100, list(range(100)), 25.0, 100, CFG) == {"kb_verlauf": [[0.0, 71.6]], "zooms": []}
    kb = _zoomreihe((1.0, 24, 24), (0.8, 24, 70), (1.0, 70, 70))
    m = T.zoom_messen(kb, list(range(len(kb))), 25.0, len(kb), CFG)
    assert len(m["zooms"]) == 1 and m["zooms"][0]["urteil"] == "schnell" and m["kb_verlauf"][-1][1] == 70.0
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py -q`
Expected: `11 failed, 55 passed` — die neuen Tests mit `AttributeError: module 'niro_autocut.telemetrie' has no attribute
'kb_je_frame'` (bzw. `zoomfahrten`, `zoom_ruck`, `kb_verlauf`, `zoom_messen`), `test_defaults_haben_zoom_schluessel` mit
`AssertionError`; alle alten Tests bestehen.

- [ ] **Step 3: Implementierung**

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
oder aus der optischen Verschiebungsreihe, Clip-Messung mit Cache, Charge-Lauf, Abschnittswerte für Stufe 2b und der
Stabilisierungs-Vorschlag für 6d.
```

**durch:**

```python
oder aus der optischen Verschiebungsreihe, Clip-Messung mit Cache, Charge-Lauf, Abschnittswerte für Stufe 2b und der
Stabilisierungs-Vorschlag für 6d; Zoomfahrten aus der KB-Brennweite und die Brennweitenregel für 3a/6d (Spec 2026-09-21).
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
# --- Clip-Messung ---------------------------------------------------------------------------------------------------------
```

**durch:**

```python
# --- Zoomfahrten (Spec 2026-09-21) ---------------------------------------------------------------------------------------

ZOOM_MEDIAN_S = 0.2           # gleitender Median der Brennweite je Sample (Ausreißer, Quantisierung)
ZOOM_GLAETTUNG_S = 0.2        # gleitendes Mittel des Tempos
ZOOM_LUECKE_S = 0.3           # Bereiche mit kürzerem Abstand sind eine Fahrt (Stop-and-go)
ZOOM_KERN_RAND = 0.10         # Anteil je am Anfang und Ende einer Fahrt, der für ruck nicht zählt
ZOOM_RUCK_SCHRITT_S = 0.2     # Schrittweite der Mittelwerte von |v| für ruck
URTEILE_ZOOM = ["langsam", "schnell"]


def _median_gleitend(x: np.ndarray, breite: int) -> np.ndarray:
    """Gleitender Median über ``breite`` Werte (auf ungerade aufgerundet), Ränder mit dem Randwert aufgefüllt."""
    x = np.asarray(x, np.float64)
    h = max(0, int(breite) // 2)
    if h == 0 or len(x) < 2:
        return x
    fenster_ = np.lib.stride_tricks.sliding_window_view(np.pad(x, (h, h), mode="edge"), 2 * h + 1)
    return np.median(fenster_, axis=1)


def kb_je_frame(kb_mm: list[float], kb_index: list[int] | None, fps: float, samples: int,
                ziel_fps: float = ZIEL_FPS) -> np.ndarray:
    """KB-Brennweite je rtmd-Sample → je Zielframe (25 fps): gleitender Median über ``ZOOM_MEDIAN_S``, dann linear auf
    die Zeiten k / ziel_fps interpoliert (Ränder gehalten). ``kb_index`` = Sample-Nummer je Wert (Lücken, wo der Tag
    fehlt oder 0xFFFF ist); leer oder unpassend = lückenlos ab 0. Leer ohne Werte."""
    kb = np.asarray(kb_mm, np.float64)
    if len(kb) == 0 or fps <= 0:
        return np.zeros(0, np.float64)
    idx = np.asarray(kb_index if kb_index and len(kb_index) == len(kb) else range(len(kb)), np.float64)
    glatt = _median_gleitend(kb, int(round(ZOOM_MEDIAN_S * fps)))
    n = max(1, int(round(max(int(samples), int(idx[-1]) + 1) * ziel_fps / fps)))
    return np.interp(np.arange(n) / ziel_fps, idx / fps, glatt)


def zoom_tempo(kb25: np.ndarray, ziel_fps: float = ZIEL_FPS) -> np.ndarray:
    """Tempo der Brennweite je Zielframe in % pro s: Änderung von ln(KB) je Sekunde, gemittelt über ZOOM_GLAETTUNG_S."""
    kb25 = np.asarray(kb25, np.float64)
    if len(kb25) < 2:
        return np.zeros(len(kb25), np.float64)
    v = np.gradient(np.log(np.maximum(kb25, 0.1))) * ziel_fps * 100.0
    return _tiefpass(v[:, None], int(round(ZOOM_GLAETTUNG_S * ziel_fps)))[:, 0]


def zoom_bereiche(v: np.ndarray, cfg: dict, ziel_fps: float = ZIEL_FPS) -> list[tuple[int, int]]:
    """Frame-Bereiche [a, b) mit |v| über ``zoom_rausch_proz_s``; Bereiche mit weniger als ZOOM_LUECKE_S Abstand werden
    zusammengefasst (Stop-and-go = eine Fahrt)."""
    ueber = (np.abs(np.asarray(v, np.float64)) > float(cfg["zoom_rausch_proz_s"])).astype(np.int8)
    kanten = np.diff(np.concatenate([[0], ueber, [0]]))
    out: list[list[int]] = []
    for a, b in zip(np.flatnonzero(kanten == 1).tolist(), np.flatnonzero(kanten == -1).tolist()):
        if out and (a - out[-1][1]) / ziel_fps < ZOOM_LUECKE_S:
            out[-1][1] = b
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def zoom_ruck(betrag: np.ndarray, stocken_anteil: float, ziel_fps: float = ZIEL_FPS) -> tuple[float, bool]:
    """(ruck, stockt) einer Zoomfahrt aus |v| je Frame. ruck = Variationskoeffizient der Mittel über
    ZOOM_RUCK_SCHRITT_S-Schritte im Kern (ohne je ZOOM_KERN_RAND am Anfang/Ende; unter zwei Schritten 0,0);
    stockt = |v| fällt im Kern unter ``stocken_anteil`` × Spitze und steigt danach wieder darüber."""
    av = np.asarray(betrag, np.float64)
    if len(av) == 0:
        return 0.0, False
    rand = int(round(len(av) * ZOOM_KERN_RAND))
    kern = av[rand:len(av) - rand] if len(av) - 2 * rand >= 1 else av
    s = max(1, int(round(ZOOM_RUCK_SCHRITT_S * ziel_fps)))
    mittel = np.array([kern[i:i + s].mean() for i in range(0, len(kern) - s + 1, s)])
    ruck = float(mittel.std() / mittel.mean()) if len(mittel) >= 2 and mittel.mean() > 0 else 0.0
    ueber = np.flatnonzero(kern >= stocken_anteil * float(av.max()))
    stockt = len(ueber) > 0 and int(ueber[-1] - ueber[0] + 1) > len(ueber)
    return ruck, bool(stockt)


def zoomfahrten(kb25: np.ndarray, cfg: dict, ziel_fps: float = ZIEL_FPS) -> list[dict]:
    """Zoomfahrten einer Brennweitenreihe je Zielframe: Bereiche aus ``zoom_bereiche`` mit mindestens ``zoom_min_proz``
    Änderung (größte / kleinste Brennweite im Bereich − 1). Je Fahrt Zeiten (s), Brennweiten am Anfang/Ende (mm), Tempo
    (% pro s), ruck, ruckartig (ruck > ``zoom_ruck_max`` oder Stocken) und Urteil: schnell, wenn tempo_max >
    ``zoom_schnell_proz_s`` oder ruckartig, sonst langsam."""
    kb25 = np.asarray(kb25, np.float64)
    v = zoom_tempo(kb25, ziel_fps)
    out = []
    for a, b in zoom_bereiche(v, cfg, ziel_fps):
        teil = kb25[a:b]
        if (float(teil.max()) / max(float(teil.min()), 0.1) - 1.0) * 100.0 < float(cfg["zoom_min_proz"]):
            continue
        betrag = np.abs(v[a:b])
        ruck, stockt = zoom_ruck(betrag, float(cfg["zoom_stocken_anteil"]), ziel_fps)
        ruckartig = ruck > float(cfg["zoom_ruck_max"]) or stockt
        tempo_max = float(betrag.max())
        schnell = tempo_max > float(cfg["zoom_schnell_proz_s"]) or ruckartig
        out.append({"von_s": round(a / ziel_fps, 2), "bis_s": round(b / ziel_fps, 2),
                    "von_mm": round(float(kb25[a]), 1), "bis_mm": round(float(kb25[b - 1]), 1),
                    "tempo_max": round(tempo_max, 1), "tempo_mittel": round(float(betrag.mean()), 1),
                    "ruck": round(ruck, 2), "ruckartig": ruckartig, "urteil": "schnell" if schnell else "langsam"})
    return out


def kb_verlauf(kb25: np.ndarray, cfg: dict, ziel_fps: float = ZIEL_FPS) -> list[list[float]]:
    """[[t_s, kb_mm], …] mit ``zoom_verlauf_hz`` Werten je Sekunde (letzter Frame immer dabei); ändert sich die
    Brennweite um weniger als ``zoom_min_proz``, genau ein Eintrag [0.0, Median]. Leer ohne Werte."""
    kb25 = np.asarray(kb25, np.float64)
    if len(kb25) == 0:
        return []
    if (float(kb25.max()) / max(float(kb25.min()), 0.1) - 1.0) * 100.0 < float(cfg["zoom_min_proz"]):
        return [[0.0, round(float(np.median(kb25)), 1)]]
    schritt = max(1, int(round(ziel_fps / float(cfg["zoom_verlauf_hz"]))))
    idx = list(range(0, len(kb25), schritt))
    if idx[-1] != len(kb25) - 1:
        idx.append(len(kb25) - 1)
    return [[round(i / ziel_fps, 2), round(float(kb25[i]), 1)] for i in idx]


def zoom_messen(kb_mm: list[float], kb_index: list[int] | None, fps: float, samples: int, cfg: dict) -> dict:
    """``kb_verlauf`` und ``zooms`` eines Clips aus der KB-Brennweite je rtmd-Sample; beide leer ohne Brennweite."""
    kb25 = kb_je_frame(kb_mm, kb_index, fps, samples)
    if len(kb25) == 0:
        return {"kb_verlauf": [], "zooms": []}
    return {"kb_verlauf": kb_verlauf(kb25, cfg), "zooms": zoomfahrten(kb25, cfg)}


# --- Clip-Messung ---------------------------------------------------------------------------------------------------------
```

**Anhängen an `tools/autocut/defaults.yaml`** (direkt nach der letzten Zeile `  parallel: 2 …` des Blocks `telemetrie:`):

```yaml
  # Zoomfahrten (Spec 2026-09-21): KB-Brennweite je Frame aus der rtmd-Spur, Tempo = Änderung von ln(KB) in % pro s
  zoom_min_proz: 3.0        # Mindeständerung der Brennweite für eine Zoomfahrt (%); Fokus-Atmen bleibt darunter
  zoom_rausch_proz_s: 1.0   # Rauschgrenze des Tempos: Frames mit |v| darüber gehören zu einer Fahrt
  zoom_schnell_proz_s: 20.0 # Spitzentempo, ab dem eine Zoomfahrt schnell ist (% pro s) — Startwert bis zur Kalibrierung
  zoom_ruck_max: 0.6        # Ungleichmäßigkeit (Variationskoeffizient von |v|), ab der eine Fahrt ruckartig = schnell ist
  zoom_stocken_anteil: 0.2  # Stocken: |v| fällt mitten in der Fahrt unter diesen Anteil der Spitze und steigt wieder
  zoom_verlauf_hz: 5        # Auflösung von kb_verlauf (Werte je Sekunde)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py -q && venv/bin/python -m pytest -q`
Expected: `66 passed`; Gesamtlauf grün (nur `1 skipped`).

- [ ] **Step 5: Commit**

```bash
git add tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/defaults.yaml tools/autocut/tests/test_telemetrie.py
git commit -q -m "feat(autocut): Zoomfahrten aus der KB-Brennweite erkennen (Tempo, ruck, Stocken, kb_verlauf)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Zoomfahrten je Clip — `rtmd.kb_index`, `clip_messen`, `ruhige_fenster`

**Files:**
- Modify: `tools/autocut/src/niro_autocut/rtmd.py` (`RtmdDaten.kb_index`, `auswerten`)
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (`_leer`, `clip_messen`, neu `ruhige_ohne_schnelle_zooms`)
- Modify: `tools/autocut/WORKFLOW-AutoCut.md` (Abschnitt Telemetrie: Absatz „Zoomfahrten"), `tools/autocut/README.md` (Modulzeile)
- Test: `tools/autocut/tests/test_rtmd.py`, `tools/autocut/tests/test_telemetrie.py` (`_kb`, `_rtmd_puffer` mit Brennweite je Frame)

**Interfaces:**
- Consumes: Task 1 (`zoom_messen`, `_zoomreihe` im Test)
- Produces:
  - `RtmdDaten.kb_index: list[int]` (Sample-Nummer je `kb_mm`-Wert)
  - `ruhige_ohne_schnelle_zooms(ruhige: list[float], zooms: list[dict], fenster_s: float | None) -> list[float]`
  - Datensatz je Clip: `kb_verlauf`, `zooms`, `zoomfahrt = bool(zooms)`; `ruhige_fenster` ohne Fenster mit schneller Fahrt
  - Test-Helfer `_kb(mm: float) -> bytes`, `_rtmd_puffer(…, kb: bytes | list[bytes] = …)`

- [ ] **Step 1: Failing Tests schreiben**

**Anhängen an `tools/autocut/tests/test_rtmd.py`:**

```python
def test_auswerten_kb_index_mit_luecken():
    """Samples ohne KB-Tag oder mit 0xFFFF fehlen in kb_mm — kb_index hält je Wert die Sample-Nummer (Zeitachse)."""
    pakete = [R.paket_bauen({R.TAG_KB_MM: bytes.fromhex("c2cc")}), R.paket_bauen({R.TAG_FOKUS_M: bytes.fromhex("e62e")}),
              R.paket_bauen({R.TAG_KB_MM: b"\xff\xff"}), R.paket_bauen({R.TAG_KB_MM: bytes.fromhex("c2a5")})]
    d = R.auswerten(R.samples(b"".join(pakete)))
    assert d.samples == 4 and d.kb_mm == [71.6, 67.7] and d.kb_index == [0, 3]
```

**Ersetzen in `tools/autocut/tests/test_telemetrie.py`:**

```python
def _rtmd_puffer(frames: int = 100, proben: int = 80, gyro_y: float = 0.0, acc=(0.0, 1.15, 0.0),
                 kb: bytes = bytes.fromhex("c2cc")) -> bytes:
    """Synthetische Datenspur: je Frame ein Sample mit konstantem Gyro (°/s um y) und Schwerkraftvektor."""
```

**durch:**

```python
def _kb(mm: float) -> bytes:
    """KB-Brennweite in mm als RDD-18-Wert (Exponent −4: 0,1 mm Auflösung bis 409,5 mm), z. B. 71,6 → c2cc."""
    return struct.pack(">H", 0xC000 | int(round(mm * 10)))


def _rtmd_puffer(frames: int = 100, proben: int = 80, gyro_y: float = 0.0, acc=(0.0, 1.15, 0.0),
                 kb: bytes | list[bytes] = bytes.fromhex("c2cc")) -> bytes:
    """Synthetische Datenspur: je Frame ein Sample mit konstantem Gyro (°/s um y) und Schwerkraftvektor; ``kb`` als
    Liste = KB-Brennweite je Frame (``_kb``)."""
```

**Ersetzen in `tools/autocut/tests/test_telemetrie.py`:**

```python
            R.TAG_IMU_HZ: struct.pack(">I", 2000), R.TAG_KB_MM: kb, R.TAG_BRENNWEITE_MM: bytes.fromhex("c2a5"),
            R.TAG_FOKUS_M: bytes.fromhex("e62e")}
    return R.paket_bauen(tags) * frames
```

**durch:**

```python
            R.TAG_IMU_HZ: struct.pack(">I", 2000), R.TAG_KB_MM: kb if isinstance(kb, bytes) else kb[0],
            R.TAG_BRENNWEITE_MM: bytes.fromhex("c2a5"), R.TAG_FOKUS_M: bytes.fromhex("e62e")}
    if isinstance(kb, bytes):
        return R.paket_bauen(tags) * frames
    return b"".join(R.paket_bauen({**tags, R.TAG_KB_MM: k}) for k in kb[:frames])
```

**Anhängen an `tools/autocut/tests/test_telemetrie.py`:**

```python
def test_ruhige_fenster_ohne_schnelle_zooms():
    zooms = [{"von_s": 2.4, "bis_s": 3.4, "urteil": "schnell"}, {"von_s": 6.0, "bis_s": 9.0, "urteil": "langsam"}]
    # Fenster [t, t + 2): 1, 2 und 3 schneiden den schnellen Zoom, 6 nur den langsamen
    assert T.ruhige_ohne_schnelle_zooms([0.0, 1.0, 2.0, 3.0, 4.0, 6.0], zooms, 2.0) == [0.0, 4.0, 6.0]
    assert T.ruhige_ohne_schnelle_zooms([0.0, 1.0], [], 2.0) == [0.0, 1.0]
    assert T.ruhige_ohne_schnelle_zooms([], zooms, None) == []


def test_clip_messen_zoomfahrt_und_ruhige_fenster(monkeypatch, tmp_path):
    clip = tmp_path / "FX3_0070.MP4"
    clip.write_bytes(b"x")
    kb = _zoomreihe((2.5, 24, 24), (0.8, 24, 70), (1.7, 70, 70))                 # 125 Frames, schneller Zoom ab 2,5 s
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p), dauer=5.0))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: _rtmd_puffer(frames=len(kb), kb=[_kb(x) for x in kb]))
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "rtmd" and rec["zoomfahrt"] is True and len(rec["zooms"]) == 1
    z = rec["zooms"][0]
    assert z["urteil"] == "schnell" and (z["von_mm"], z["bis_mm"]) == (24.0, 70.0) and 2.3 < z["von_s"] < 2.5
    # 5 Hz über 125 Frames: 0,0 … 4,8 s plus der letzte Frame (4,96 s)
    assert len(rec["kb_verlauf"]) == 26 and rec["kb_verlauf"][0] == [0.0, 24.0] and rec["kb_verlauf"][-1] == [4.96, 70.0]
    # Stativ (Gyro 0): alle Fenster ruhig — bis auf die drei, die den schnellen Zoom schneiden (ab 1, 2 und 3 s)
    assert [f[0] for f in rec["fenster"]] == [0.0, 1.0, 2.0, 3.0, 4.0] and rec["ruhige_fenster"] == [0.0, 4.0]


def test_clip_messen_ohne_rtmd_brennweite_ohne_zooms(monkeypatch, tmp_path):
    clip = tmp_path / "DJI_0071.MOV"
    clip.write_bytes(b"x")
    _optisch_fakes(monkeypatch, seed=21)
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "optisch" and rec["kb_verlauf"] == [] and rec["zooms"] == [] and rec["zoomfahrt"] is False
    fest = tmp_path / "FX3_0072.MP4"
    fest.write_bytes(b"x")
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: _rtmd_puffer(frames=100))
    rec2 = T.clip_messen(fest, CFG)
    assert rec2["kb_verlauf"] == [[0.0, 71.6]] and rec2["zooms"] == [] and rec2["zoomfahrt"] is False
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_rtmd.py tests/test_telemetrie.py -q`
Expected: `4 failed, 77 passed` — `test_auswerten_kb_index_mit_luecken` (`AttributeError: 'RtmdDaten' object has no
attribute 'kb_index'`), `test_ruhige_fenster_ohne_schnelle_zooms` (`AttributeError … ruhige_ohne_schnelle_zooms`),
`test_clip_messen_zoomfahrt_und_ruhige_fenster` (`KeyError: 'zooms'`) und `test_clip_messen_ohne_rtmd_brennweite_ohne_zooms`
(`KeyError: 'kb_verlauf'`); alle übrigen bestehen (die umgebauten Helfer ändern nichts am Verhalten).

- [ ] **Step 3: Implementierung**

**Ersetzen in `tools/autocut/src/niro_autocut/rtmd.py`:**

```python
    fokus_m: list[float] = field(default_factory=list)
```

**durch:**

```python
    fokus_m: list[float] = field(default_factory=list)
    kb_index: list[int] = field(default_factory=list)         # Sample-Nummer je kb_mm-Wert (Lücken: Tag fehlt/0xFFFF)
```

**Ersetzen in `tools/autocut/src/niro_autocut/rtmd.py`:**

```python
    """Samples → RtmdDaten (Gyro/Acc aneinandergehängt, Distanzen je Sample; 0xFFFF und fehlende Tags übersprungen)."""
    gyro, acc, f_ist, f_kb, fokus = [], [], [], [], []
    hz = None
    for s in sample_list:
```

**durch:**

```python
    """Samples → RtmdDaten (Gyro/Acc aneinandergehängt, Distanzen je Sample; 0xFFFF und fehlende Tags übersprungen —
    ``kb_index`` hält je KB-Wert die Sample-Nummer, damit die Zeitachse der Brennweite auch mit Lücken stimmt)."""
    gyro, acc, f_ist, f_kb, fokus, kb_idx = [], [], [], [], [], []
    hz = None
    for i, s in enumerate(sample_list):
```

**Ersetzen in `tools/autocut/src/niro_autocut/rtmd.py`:**

```python
                if v != 0xFFFF:
                    ziel.append(round(distanz(v) * faktor, stellen))
```

**durch:**

```python
                if v != 0xFFFF:
                    ziel.append(round(distanz(v) * faktor, stellen))
                    if tag == TAG_KB_MM:
                        kb_idx.append(i)
```

**Ersetzen in `tools/autocut/src/niro_autocut/rtmd.py`:**

```python
                     brennweite_mm=f_ist, kb_mm=f_kb, fokus_m=fokus)
```

**durch:**

```python
                     brennweite_mm=f_ist, kb_mm=f_kb, fokus_m=fokus, kb_index=kb_idx)
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
            "kb_max": None, "zoomfahrt": False, "fokus_m": None, "brennweitenklasse": None, "pitch_grad": None,
```

**durch:**

```python
            "kb_max": None, "kb_verlauf": [], "zooms": [], "zoomfahrt": False, "fokus_m": None,
            "brennweitenklasse": None, "pitch_grad": None,
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
                out["zoomfahrt"] = bool(out["kb_max"] / max(out["kb_min"], 0.1) > 1.3)
```

**durch:**

```python
                out.update(zoom_messen(daten.kb_mm, daten.kb_index, float(info.fps), daten.samples, cfg))
                out["zoomfahrt"] = bool(out["zooms"])
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
            out.update(quelle="optisch", **kennzahlen(verschiebungen(frames), cfg, kb, schaerfe_frames(frames)))
    except AutoCutError as e:
```

**durch:**

```python
            out.update(quelle="optisch", **kennzahlen(verschiebungen(frames), cfg, kb, schaerfe_frames(frames)))
        out["ruhige_fenster"] = ruhige_ohne_schnelle_zooms(out["ruhige_fenster"], out["zooms"], out["fenster_s"])
    except AutoCutError as e:
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
def zoom_messen(kb_mm: list[float], kb_index: list[int] | None, fps: float, samples: int, cfg: dict) -> dict:
```

**durch:**

```python
def ruhige_ohne_schnelle_zooms(ruhige: list[float], zooms: list[dict], fenster_s: float | None) -> list[float]:
    """Ruhige Fenster (Startzeiten) ohne die, deren Fenster [t, t + fenster_s) eine schnelle Zoomfahrt schneidet."""
    schnell = [z for z in zooms or [] if z.get("urteil") == "schnell"]
    lang = float(fenster_s or 0.0)
    return [t for t in ruhige or [] if not any(t < z["bis_s"] and t + lang > z["von_s"] for z in schnell)]


def zoom_messen(kb_mm: list[float], kb_index: list[int] | None, fps: float, samples: int, cfg: dict) -> dict:
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_rtmd.py tests/test_telemetrie.py -q && venv/bin/python -m pytest -q`
Expected: alle bestehen (Fixture-Tests aus `test_rtmd.py` laufen mit); Gesamtlauf grün.

- [ ] **Step 5: Doku**

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
Spec: `docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md`.
```

**durch:**

```text
Spec: `docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md`.

**Zoomfahrten (seit 21.09.2026, Spec `docs/superpowers/specs/2026-09-21-autocut-zoom-brennweite-design.md`):** aus der
KB-Brennweite je rtmd-Sample (0x8004, mit Crop und Klarbild-Zoom): Median über 0,2 s, 25-fps-Raster, Tempo = Änderung von
ln(KB) in % pro s. Je Clip `kb_verlauf` ([t_s, kb_mm] mit 5 Hz; bei gleichbleibender Brennweite ein Eintrag) und `zooms`
(`von_s`/`bis_s`, `von_mm`/`bis_mm`, `tempo_max`/`tempo_mittel`, `ruck`, `ruckartig`, `urteil` langsam/schnell);
`zoomfahrt` = mindestens eine Fahrt. Eine Fahrt ändert die Brennweite um mindestens `zoom_min_proz` (3 %), Pausen unter
0,3 s gehören dazu (Stop-and-go). Schnell = Spitze über `zoom_schnell_proz_s` oder ruckartig (`ruck` über `zoom_ruck_max`
oder Stocken unter `zoom_stocken_anteil` der Spitze). Fenster, die eine schnelle Fahrt schneiden, zählen nicht zu den
`ruhige_fenster`. Ohne rtmd-Brennweite (Mavic, Avata) bleiben `kb_verlauf` und `zooms` leer (Brennweite unbekannt).
Startwerte bis zur Kalibrierung: 20 %/s, `ruck` 0,6, Stocken 0,2.
```

**Ersetzen in `tools/autocut/README.md`:**

```text
Bewegungsart, Lage), Clip-Messung
```

**durch:**

```text
Bewegungsart, Lage, Zoomfahrten), Clip-Messung
```

- [ ] **Step 6: Tests (Doku) und Commit**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_docs.py -q`
Expected: grün (nur `1 skipped`).

```bash
git add tools/autocut/src/niro_autocut/rtmd.py tools/autocut/src/niro_autocut/telemetrie.py \
  tools/autocut/tests/test_rtmd.py tools/autocut/tests/test_telemetrie.py tools/autocut/WORKFLOW-AutoCut.md \
  tools/autocut/README.md
git commit -q -m "feat(autocut): Zoomfahrten je Clip (kb_verlauf, zooms), ruhige Fenster ohne schnelle Zooms

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Brennweite im Bereich — `kb_am`, `kb_im_bereich`, `zooms_im_bereich`, 2b-Werte, Texte

**Files:**
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (neuer Abschnitt am Dateiende)
- Test: `tools/autocut/tests/test_telemetrie.py`

**Interfaces:**
- Consumes: Datensatz-Felder `kb_mm`, `kb_verlauf`, `zooms` (Task 2)
- Produces:
  - `OHNE_TELEMETRIE = "keine Telemetrie — Brennweitenregel nicht geprüft"`
  - `_zahl(x: float, stellen: int = 1) -> str` (Dezimalkomma, `:g`), `_kb_median(verlauf, von_s, bis_s) -> float`
  - `kb_am(rec: dict | None, t_s: float, spanne_s: float = 0.5, seite: str = "mitte") -> float | None`
  - `kb_im_bereich(rec: dict | None, von_s: float, bis_s: float) -> float | None`
  - `zooms_im_bereich(rec: dict | None, von_s: float, bis_s: float, nur_schnelle: bool = True) -> list[dict]`
  - `abschnitt_brennweite(rec: dict | None, von_s: float, bis_s: float) -> dict` (`brennweite_mm`, `zoom`)
  - `brennweite_text(rec: dict | None) -> str | None` („KB 71,6 mm" / „KB 24–70 mm, langsamer Zoom")
  - `zoom_hinweise(sid: str, rec: dict | None, von_s: float, bis_s: float, tempo_faktor: float = 1.0,
    cfg: dict | None = None) -> list[str]` — bei Zeitlupe (6d, `tempo_faktor=0.5`) zählt das sichtbare Tempo
    (Controller-Entscheidung 21.09., folgt aus der User-Regel „so, wie es im Schnitt aussieht")

- [ ] **Step 1: Failing Tests schreiben**

**Anhängen an `tools/autocut/tests/test_telemetrie.py`:**

```python
# --- Brennweite im Bereich: kb_am, kb_im_bereich, zooms_im_bereich, 2b-Werte, Texte (Spec 2026-09-21) -------------------

_ZOOM_REC = {"kb_mm": 48.0, "kb_verlauf": [[0.0, 24.0], [1.0, 24.0], [2.0, 48.0], [3.0, 48.0]],
             "zooms": [{"von_s": 1.0, "bis_s": 2.0, "von_mm": 24.0, "bis_mm": 48.0, "tempo_max": 85.2, "tempo_mittel": 69.3,
                        "ruck": 0.1, "ruckartig": False, "urteil": "schnell"},
                       {"von_s": 5.0, "bis_s": 6.0, "von_mm": 48.0, "bis_mm": 50.0, "tempo_max": 4.0, "tempo_mittel": 3.0,
                        "ruck": 0.1, "ruckartig": False, "urteil": "langsam"}]}


def test_kb_am_seiten_raender_und_ohne_verlauf():
    # Spanne 0,5 s auf dem 0,1-s-Raster, linear zwischen den Verlaufspunkten (1 s: 24 mm, 2 s: 48 mm)
    assert T.kb_am(_ZOOM_REC, 2.0, seite="ende") == 42.0           # 1,5–2,0 s: 36 … 48 → Median (40,8 + 43,2) / 2
    assert T.kb_am(_ZOOM_REC, 2.0, seite="anfang") == 48.0         # 2,0–2,5 s
    assert T.kb_am(_ZOOM_REC, 1.0, seite="ende") == 24.0
    assert T.kb_am(_ZOOM_REC, 1.0) == 24.6                         # mittig 0,75–1,25 s: 24, 24, 24, 25,2, 27,6, 30
    assert T.kb_am(_ZOOM_REC, 0.0, seite="ende") == 24.0 and T.kb_am(_ZOOM_REC, 10.0, seite="anfang") == 48.0
    assert T.kb_am({"kb_verlauf": [[0.0, 71.6]]}, 3.0, seite="ende") == 71.6    # Festbrennweite: ein Eintrag
    assert T.kb_am(None, 1.0) is None and T.kb_am({"kb_verlauf": []}, 1.0) is None
    assert T.kb_am({"kb_mm": 50.0}, 1.0) is None                   # Datensatz von vor der Umstellung: unbekannt


def test_kb_im_bereich_und_zooms_im_bereich():
    assert T.kb_im_bereich(_ZOOM_REC, 0.0, 3.0) == 36.0            # 11 × 24, 26,4 … 45,6, 11 × 48 → Mitte 36
    assert T.kb_im_bereich(_ZOOM_REC, 2.0, 3.0) == 48.0 and T.kb_im_bereich({}, 0.0, 1.0) is None
    schnell, langsam = _ZOOM_REC["zooms"]
    assert T.zooms_im_bereich(_ZOOM_REC, 0.0, 1.5) == [schnell]
    assert T.zooms_im_bereich(_ZOOM_REC, 2.0, 5.0) == []           # Berühren zählt nicht
    assert T.zooms_im_bereich(_ZOOM_REC, 0.0, 10.0) == [schnell]
    assert T.zooms_im_bereich(_ZOOM_REC, 0.0, 10.0, nur_schnelle=False) == [schnell, langsam]
    assert T.zooms_im_bereich({"kb_mm": 50.0}, 0.0, 10.0) == [] and T.zooms_im_bereich(None, 0.0, 1.0) == []


def test_abschnitt_brennweite_und_brennweite_text():
    assert T.abschnitt_brennweite(_ZOOM_REC, 0.0, 1.5) == {"brennweite_mm": 24.0, "zoom": "schnell"}
    assert T.abschnitt_brennweite(_ZOOM_REC, 5.5, 6.0) == {"brennweite_mm": 48.0, "zoom": "langsam"}
    assert T.abschnitt_brennweite(_ZOOM_REC, 3.0, 4.0) == {"brennweite_mm": 48.0, "zoom": "keiner"}
    assert T.abschnitt_brennweite({"kb_mm": 50.0}, 0.0, 1.0) == {"brennweite_mm": None, "zoom": None}
    assert T.brennweite_text(_ZOOM_REC) == "KB 24–48 mm, schneller Zoom"
    langsam = {**_ZOOM_REC, "zooms": _ZOOM_REC["zooms"][1:]}
    assert T.brennweite_text(langsam) == "KB 24–48 mm, langsamer Zoom"
    assert T.brennweite_text({"kb_mm": 71.6, "kb_verlauf": [[0.0, 71.6]], "zooms": []}) == "KB 71,6 mm"
    assert T.brennweite_text({"kb_mm": 50.0}) == "KB 50 mm"         # Altdatensatz ohne Verlauf
    assert T.brennweite_text({"kb_mm": None}) is None and T.brennweite_text(None) is None


def test_zoom_hinweise():
    rec = {"zooms": [{"von_s": 2.4, "bis_s": 3.1, "von_mm": 24.0, "bis_mm": 70.0, "tempo_max": 85.2, "tempo_mittel": 60.0,
                      "ruck": 0.2, "ruckartig": False, "urteil": "schnell"}]}
    assert T.zoom_hinweise("S07", rec, 2.0, 4.0) == ["S07: schneller Zoom 2,4–3,1 s (24 → 70 mm, 85 %/s)"]
    ruck = {"zooms": [{**rec["zooms"][0], "tempo_max": 14.6, "ruckartig": True}]}
    assert T.zoom_hinweise("S08", ruck, 0.0, 10.0) == ["S08: schneller Zoom 2,4–3,1 s (24 → 70 mm, 15 %/s, ruckartig)"]
    assert T.zoom_hinweise("S07", rec, 3.1, 5.0) == [] and T.zoom_hinweise("S07", None, 0.0, 1.0) == []
    # 6d-Zeitlupe (50 %): sichtbares Tempo halb so hoch — 85 → 43 %/s bleibt schnell (CFG: 20 %/s), 30 → 15 %/s nicht
    assert T.zoom_hinweise("S07", rec, 2.0, 4.0, tempo_faktor=0.5, cfg=CFG) == [
        "S07: schneller Zoom 2,4–3,1 s (24 → 70 mm, 43 %/s sichtbar bei 50 %)"]
    maessig = {"zooms": [{**rec["zooms"][0], "tempo_max": 30.0}]}
    assert T.zoom_hinweise("S09", maessig, 2.0, 4.0, tempo_faktor=0.5, cfg=CFG) == []
    # ruckartig bleibt schnell, egal wie langsam
    assert T.zoom_hinweise("S08", ruck, 0.0, 10.0, tempo_faktor=0.5, cfg=CFG) == [
        "S08: schneller Zoom 2,4–3,1 s (24 → 70 mm, 7 %/s sichtbar bei 50 %, ruckartig)"]
    # ohne cfg bleibt der Hinweis (Schwelle unbekannt → lieber melden)
    assert len(T.zoom_hinweise("S09", maessig, 2.0, 4.0, tempo_faktor=0.5)) == 1
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py -q`
Expected: `4 failed` mit `AttributeError: module 'niro_autocut.telemetrie' has no attribute 'kb_am'` (bzw. `kb_im_bereich`,
`abschnitt_brennweite`, `zoom_hinweise`); alle übrigen bestehen.

- [ ] **Step 3: Implementierung**

**Anhängen an `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
# --- Brennweite im Bereich (Stufe 2b, Vorlagen 3a/6d; Spec 2026-09-21) --------------------------------------------------

OHNE_TELEMETRIE = "keine Telemetrie — Brennweitenregel nicht geprüft"


def _zahl(x: float, stellen: int = 1) -> str:
    """Zahl mit Dezimalkomma ohne überflüssige Nullen: 71,6 · 50 · 1,25."""
    return f"{round(float(x), stellen):g}".replace(".", ",")


def _kb_median(verlauf: list[list[float]], von_s: float, bis_s: float) -> float:
    """Median der linear interpolierten Brennweite auf einem 0,1-s-Raster über [von_s, bis_s] (Ränder gehalten)."""
    t = np.array([p[0] for p in verlauf], np.float64)
    k = np.array([p[1] for p in verlauf], np.float64)
    n = max(2, int(round((bis_s - von_s) * 10)) + 1)
    return round(float(np.median(np.interp(np.linspace(von_s, bis_s, n), t, k))), 1)


def kb_am(rec: dict | None, t_s: float, spanne_s: float = 0.5, seite: str = "mitte") -> float | None:
    """Median der KB-Brennweite über ``spanne_s`` an ``t_s`` (s im Clip) aus ``kb_verlauf``: ``seite="ende"`` = die
    Spanne bis t_s (Quell-Out), ``"anfang"`` = ab t_s (Quell-In), sonst mittig; außerhalb des Verlaufs gilt der Randwert.
    None ohne Verlauf (Drohne, Datensatz von vor der Umstellung)."""
    verlauf = (rec or {}).get("kb_verlauf") or []
    if not verlauf:
        return None
    von = {"ende": t_s - spanne_s, "anfang": t_s}.get(seite, t_s - spanne_s / 2)
    return _kb_median(verlauf, von, von + spanne_s)


def kb_im_bereich(rec: dict | None, von_s: float, bis_s: float) -> float | None:
    """Median der KB-Brennweite im Bereich [von_s, bis_s] (s im Clip); None ohne Verlauf."""
    verlauf = (rec or {}).get("kb_verlauf") or []
    if not verlauf:
        return None
    return _kb_median(verlauf, von_s, max(von_s, bis_s))


def zooms_im_bereich(rec: dict | None, von_s: float, bis_s: float, nur_schnelle: bool = True) -> list[dict]:
    """Zoomfahrten, die den Bereich (von_s, bis_s) schneiden (Berühren zählt nicht); leer ohne ``zooms``."""
    return [z for z in (rec or {}).get("zooms") or []
            if z["von_s"] < bis_s and z["bis_s"] > von_s and (not nur_schnelle or z.get("urteil") == "schnell")]


def abschnitt_brennweite(rec: dict | None, von_s: float, bis_s: float) -> dict:
    """Stufe 2b: ``brennweite_mm`` (Median im Abschnitt) und ``zoom`` (keiner | langsam | schnell — die schnellste
    Zoomfahrt im Abschnitt); beide None ohne Brennweitenverlauf."""
    if not (rec or {}).get("kb_verlauf"):
        return {"brennweite_mm": None, "zoom": None}
    urteile = {z.get("urteil") for z in zooms_im_bereich(rec, von_s, bis_s, nur_schnelle=False)}
    zoom = "schnell" if "schnell" in urteile else "langsam" if "langsam" in urteile else "keiner"
    return {"brennweite_mm": kb_im_bereich(rec, von_s, bis_s), "zoom": zoom}


def brennweite_text(rec: dict | None) -> str | None:
    """Kurztext der gemessenen KB-Brennweite: „KB 71,6 mm", mit Zoomfahrten „KB 24–70 mm, langsamer Zoom" (schneller
    Zoom, sobald eine Fahrt schnell ist); None ohne Brennweite."""
    r = rec or {}
    if not r.get("kb_mm"):
        return None
    werte = [p[1] for p in r.get("kb_verlauf") or []]
    zooms = r.get("zooms") or []
    if not zooms or len(werte) < 2:
        return f"KB {_zahl(r['kb_mm'])} mm"
    art = "schneller" if any(z.get("urteil") == "schnell" for z in zooms) else "langsamer"
    return f"KB {_zahl(min(werte))}–{_zahl(max(werte))} mm, {art} Zoom"


def zoom_hinweise(sid: str, rec: dict | None, von_s: float, bis_s: float, tempo_faktor: float = 1.0,
                  cfg: dict | None = None) -> list[str]:
    """Probelauf-Hinweise (3a/6d) zu schnellen Zoomfahrten im genutzten Quellbereich (s im Clip), z. B.
    „S07: schneller Zoom 2,4–3,1 s (24 → 70 mm, 85 %/s)" — nur Hinweis, gebaut wird trotzdem. Bei Zeitlupe
    (``tempo_faktor`` < 1) zählt das sichtbare Tempo: ein Zoom, der nur wegen des Tempos schnell war, entfällt, wenn er
    sichtbar höchstens ``zoom_schnell_proz_s`` erreicht; ruckartige bleiben; ohne ``cfg`` bleibt jeder Hinweis."""
    schwelle = float((cfg or {}).get("zoom_schnell_proz_s", 0.0))
    out = []
    for z in zooms_im_bereich(rec, von_s, bis_s):
        tempo = float(z["tempo_max"]) * tempo_faktor
        if tempo_faktor < 1.0 and not z.get("ruckartig") and cfg is not None and tempo <= schwelle:
            continue
        sichtbar = f" sichtbar bei {tempo_faktor * 100:.0f} %" if tempo_faktor != 1.0 else ""
        ruck = ", ruckartig" if z.get("ruckartig") else ""
        out.append(f"{sid}: schneller Zoom {_zahl(z['von_s'])}–{_zahl(z['bis_s'])} s ({_zahl(z['von_mm'])} → "
                   f"{_zahl(z['bis_mm'])} mm, {tempo:.0f} %/s{sichtbar}{ruck})")
    return out
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py -q && venv/bin/python -m pytest -q`
Expected: alle bestehen; Gesamtlauf grün.

- [ ] **Step 5: Commit**

```bash
git add tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/tests/test_telemetrie.py
git commit -q -m "feat(autocut): Brennweite im Bereich (kb_am, kb_im_bereich, zooms_im_bereich), 2b-Werte und Hinweistexte

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Brennweitenfolge — gleiche Brennweite, digitaler Zoom

**Files:**
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (neuer Abschnitt am Dateiende)
- Modify: `tools/autocut/defaults.yaml` (drei Schlüssel am Ende des Blocks `telemetrie:`)
- Test: `tools/autocut/tests/test_telemetrie.py` (`CFG` ergänzen, Tests anhängen)

**Interfaces:**
- Consumes: `_zahl` (Task 3)
- Produces:
  - `brennweite_abstand(kb_a: float, kb_b: float) -> float` (größere / kleinere − 1, vier Stellen)
  - `gleiche_brennweite(kb_a: float, kb_b: float, abstand_max: float) -> bool` (Abstand < abstand_max)
  - `digitalzoom(kb_a: float, kb_b: float, zoom_a: float, zoom_b: float, cfg: dict, a_erlaubt: bool = True, b_erlaubt: bool = True) -> tuple[str, float] | None`
  - `brennweitenfolge(eintraege: list[dict], cfg: dict) -> list[dict]` — Eingabe je Shot
    `{id, rec_in, rec_out, kb_anfang, kb_ende, zoom_erzwungen}`, Ausgabe je Shot (Eingabe-Reihenfolge)
    `{id, zoom, hinweis, fehler}`
  - `defaults.yaml`: `brennweite_gleich_max 0.20`, `digitalzoom_faktor 1.25`, `digitalzoom_max 1.5`

- [ ] **Step 1: Failing Tests schreiben**

**Ersetzen in `tools/autocut/tests/test_telemetrie.py`:**

```python
       "zoom_stocken_anteil": 0.2, "zoom_verlauf_hz": 5}
```

**durch:**

```python
       "zoom_stocken_anteil": 0.2, "zoom_verlauf_hz": 5, "brennweite_gleich_max": 0.20, "digitalzoom_faktor": 1.25,
       "digitalzoom_max": 1.5}
```

**Anhängen an `tools/autocut/tests/test_telemetrie.py`:**

```python
# --- Brennweitenfolge: gleiche Brennweite, digitaler Zoom (Spec 2026-09-21, Abschnitt 2) ------------------------------

def test_defaults_haben_brennweitenregel():
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    assert cfg["brennweite_gleich_max"] == 0.20 and cfg["digitalzoom_faktor"] == 1.25 and cfg["digitalzoom_max"] == 1.5


@pytest.mark.parametrize("a,b,abstand,gleich", [
    (50, 55, 0.1, True), (24, 28, 0.1667, True), (35, 50, 0.4286, False), (70, 85, 0.2143, False),
    (50, 60, 0.2, False),                   # genau 20 %: nicht „unter 20 %"
    (50, 59.9, 0.198, True), (55, 50, 0.1, True),
])
def test_brennweite_abstand_und_gleich(a, b, abstand, gleich):
    assert T.brennweite_abstand(a, b) == abstand and T.gleiche_brennweite(a, b, 0.20) is gleich


@pytest.mark.parametrize("args,kw,erwartet", [
    ((50, 52, 1.0, 1.0), {}, ("b", 1.25)),                         # B länger: 1,25 reicht
    ((52, 50, 1.0, 1.0), {}, ("a", 1.25)),                         # A länger
    ((52, 50, 1.0, 1.0), {"a_erlaubt": False}, ("b", 1.3)),        # kürzerer mit Aufschlag: 1,25 × 52 / 50
    ((50, 52, 1.0, 1.0), {"b_erlaubt": False}, ("a", 1.3)),
    ((50, 50, 1.0, 1.0), {}, ("b", 1.25)),                         # Gleichstand → B
    ((50, 52, 1.0, 1.1), {}, ("b", 1.375)),                        # vorhandener Zoom: 1,1 × 1,25 (A bräuchte 1,43)
    ((50, 52, 1.0, 1.0), {"a_erlaubt": False, "b_erlaubt": False}, None),
])
def test_digitalzoom(args, kw, erwartet):
    assert T.digitalzoom(*args, CFG, **kw) == erwartet


def test_digitalzoom_grenze():
    assert T.digitalzoom(50, 52, 1.0, 1.1, {**CFG, "digitalzoom_max": 1.3}) is None     # 1,375 und 1,43 > 1,3
    assert T.digitalzoom(50, 52, 1.0, 1.0, {**CFG, "digitalzoom_max": 1.25}) == ("b", 1.25)   # Grenze zählt mit


def _shot(sid: str, rec_in: int, rec_out: int, kb_anfang: float | None, kb_ende: float | None,
          zoom: float | None = None) -> dict:
    return {"id": sid, "rec_in": rec_in, "rec_out": rec_out, "kb_anfang": kb_anfang, "kb_ende": kb_ende,
            "zoom_erzwungen": zoom}


def _zooms(folge: list[dict]) -> list[float]:
    return [e["zoom"] for e in folge]


def test_brennweitenfolge_automatik_verschieden_luecke_unbekannt():
    f = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 50, 100, 52.0, 52.0)], CFG)
    assert _zooms(f) == [1.0, 1.25] and f[0]["hinweis"] is None and f[1]["fehler"] is None
    assert f[1]["hinweis"] == "S02: 50 → 52 mm am Schnitt, Zoom 1,25× auf S02"
    verschieden = T.brennweitenfolge([_shot("S01", 0, 50, 24.0, 24.0), _shot("S02", 50, 100, 50.0, 50.0)], CFG)
    assert _zooms(verschieden) == [1.0, 1.0] and verschieden[1]["hinweis"] is None
    luecke = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 60, 110, 50.0, 50.0)], CFG)
    assert _zooms(luecke) == [1.0, 1.0] and luecke[1]["hinweis"] is None
    unbekannt = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 50, 100, None, None),
                                    _shot("S03", 100, 150, 50.0, 50.0)], CFG)
    assert _zooms(unbekannt) == [1.0, 1.0, 1.0] and all(e["hinweis"] is None for e in unbekannt)
    # Eingabe nicht in Record-Reihenfolge: geprüft wird nach rec_in, Ausgabe bleibt in Eingabe-Reihenfolge
    umgekehrt = T.brennweitenfolge([_shot("S02", 50, 100, 52.0, 52.0), _shot("S01", 0, 50, 50.0, 50.0)], CFG)
    assert [e["id"] for e in umgekehrt] == ["S02", "S01"] and _zooms(umgekehrt) == [1.25, 1.0]
    assert T.brennweitenfolge([], CFG) == []


def test_brennweitenfolge_spalte_zoom_erzwingt_und_verbietet():
    verbietet_b = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 50, 100, 52.0, 52.0, 1.0)], CFG)
    assert _zooms(verbietet_b) == [1.3, 1.0]                              # nur A: 1,25 × 52 / 50
    assert verbietet_b[1]["hinweis"] == "S02: 50 → 52 mm am Schnitt, Zoom 1,3× auf S01"
    beide = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0, 1.0), _shot("S02", 50, 100, 52.0, 52.0, 1.0)], CFG)
    assert _zooms(beide) == [1.0, 1.0]
    assert beide[1]["hinweis"] == "S02: gleiche Brennweite wie S01 (50/52 mm), Zoom nicht möglich (Spalte zoom)"
    erzwingt = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 50, 100, 52.0, 52.0, 1.4)], CFG)
    assert _zooms(erzwingt) == [1.0, 1.4] and erzwingt[1]["hinweis"] is None      # 50 / 72,8 mm: verschieden
    zu_gross = T.brennweitenfolge([_shot("S01", 0, 50, 24.0, 24.0, 1.6), _shot("S02", 60, 90, 50.0, 50.0, 0.9)], CFG)
    assert zu_gross[0]["fehler"] == "S01: Spalte zoom 1,6× außerhalb 1,0–1,5× (telemetrie.digitalzoom_max)"
    assert zu_gross[1]["fehler"] == "S02: Spalte zoom 0,9× außerhalb 1,0–1,5× (telemetrie.digitalzoom_max)"


def test_brennweitenfolge_kette_a_schon_gezoomt_nur_b():
    # Faktor 1,1: S02 bekommt 1,1 (Gleichstand → B); S02 → S03: 52,3 × 1,1 = 57,53 mm gegen 50 mm = gleich (15 %).
    # A (S02) hat schon einen Zoom → nur B: 1,1 × 57,53 / 50 = 1,266 (A allein bräuchte nur 1,1 × 1,1 = 1,21)
    cfg = {**CFG, "digitalzoom_faktor": 1.1}
    f = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 50, 100, 50.0, 52.3),
                            _shot("S03", 100, 150, 50.0, 50.0)], cfg)
    assert _zooms(f) == [1.0, 1.1, 1.266]
    assert f[2]["hinweis"] == "S03: 57,5 → 50 mm am Schnitt, Zoom 1,266× auf S03"


def test_brennweitenfolge_kein_rueckfall_zum_vorgaenger():
    # S01 → S02: 62,5 / 50 mm = 25 %, verschieden. S02 → S03: 52 / 50 = gleich; A (S02) wäre billiger (1,25 < 1,3),
    # 50 × 1,25 = 62,5 mm machte aber den Schnitt S01 → S02 wieder gleich → nur B: 1,25 × 52 / 50 = 1,3
    f = T.brennweitenfolge([_shot("S01", 0, 50, 62.5, 62.5), _shot("S02", 50, 100, 50.0, 52.0),
                            _shot("S03", 100, 150, 50.0, 50.0)], CFG)
    assert _zooms(f) == [1.0, 1.0, 1.3] and f[2]["hinweis"] == "S03: 52 → 50 mm am Schnitt, Zoom 1,3× auf S03"
    ohne_vorgaenger = T.brennweitenfolge([_shot("S02", 50, 100, 50.0, 52.0), _shot("S03", 100, 150, 50.0, 50.0)], CFG)
    assert _zooms(ohne_vorgaenger) == [1.25, 1.0]                          # ohne S01 darf A den Zoom tragen


def test_brennweitenfolge_zoom_nicht_moeglich():
    f = T.brennweitenfolge([_shot("S11", 0, 50, 50.0, 50.0), _shot("S12", 50, 100, 52.0, 52.0)],
                           {**CFG, "digitalzoom_max": 1.2})
    assert _zooms(f) == [1.0, 1.0]
    assert f[1]["hinweis"] == "S12: gleiche Brennweite wie S11 (50/52 mm), Zoom nicht möglich (1,2×-Grenze)"
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py -q`
Expected: `21 failed, 73 passed` — alle neuen Tests (7 + 7 parametrisierte, `test_digitalzoom_grenze`, fünf
`brennweitenfolge`-Tests mit `AttributeError … 'brennweite_abstand'` bzw. `'digitalzoom'`, `'brennweitenfolge'`;
`test_defaults_haben_brennweitenregel` mit `KeyError: 'brennweite_gleich_max'`); alle übrigen bestehen.

- [ ] **Step 3: Implementierung**

**Anhängen an `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
# --- Brennweitenfolge: nie zweimal dieselbe Brennweite direkt hintereinander (Spec 2026-09-21, Abschnitt 2) --------------

def brennweite_abstand(kb_a: float, kb_b: float) -> float:
    """Abstand zweier Brennweiten = größere / kleinere − 1 (auf vier Stellen, damit 60/50 genau 0,2 ist)."""
    return round(max(kb_a, kb_b) / min(kb_a, kb_b) - 1.0, 4)


def gleiche_brennweite(kb_a: float, kb_b: float, abstand_max: float) -> bool:
    """Gleich, wenn der Abstand unter ``abstand_max`` liegt (0,20: 50/55 und 24/28 gleich, 35/50 und 70/85 nicht)."""
    return brennweite_abstand(kb_a, kb_b) < abstand_max


def digitalzoom(kb_a: float, kb_b: float, zoom_a: float, zoom_b: float, cfg: dict, a_erlaubt: bool = True,
                b_erlaubt: bool = True) -> tuple[str, float] | None:
    """Digitaler Zoom für ein Paar A → B mit gleicher scheinbarer Brennweite am Schnitt (kb × vorhandener Zoom): der Shot
    mit der längeren scheinbaren Brennweite braucht ``digitalzoom_faktor``, der kürzere ``digitalzoom_faktor × längere /
    kürzere``. Zulässig ist ein erlaubter Kandidat, wenn vorhandener Zoom × Faktor ≤ ``digitalzoom_max``; gewählt wird
    der mit dem kleineren Gesamtzoom (mehr Reserve), bei Gleichstand B. Liefert ("a" | "b", Gesamtzoom auf drei Stellen)
    oder None, wenn kein Kandidat zulässig ist."""
    faktor, grenze = float(cfg["digitalzoom_faktor"]), float(cfg["digitalzoom_max"])
    schein_a, schein_b = kb_a * zoom_a, kb_b * zoom_b
    lang = max(schein_a, schein_b)
    kandidaten = []
    for seite, erlaubt, schein, zoom in (("b", b_erlaubt, schein_b, zoom_b), ("a", a_erlaubt, schein_a, zoom_a)):
        gesamt = zoom * faktor * lang / schein
        if erlaubt and gesamt <= grenze + 1e-9:
            kandidaten.append((round(gesamt, 3), seite))
    if not kandidaten:
        return None
    gesamt, seite = min(kandidaten, key=lambda k: k[0])      # min ist stabil: bei Gleichstand bleibt B (zuerst)
    return seite, gesamt


def brennweitenfolge(eintraege: list[dict], cfg: dict) -> list[dict]:
    """Regel „nie zweimal dieselbe Brennweite direkt hintereinander" für die B-Roll-Shots auf V3 als reine Funktion.

    Eingabe je Shot: ``id`` (Anzeige, z. B. „S07"), ``rec_in``/``rec_out`` (Timeline-Frames), ``kb_anfang``/``kb_ende``
    (KB-Brennweite am Quell-In bzw. -Out des genutzten Bereichs, ``kb_am``; None = unbekannt) und ``zoom_erzwungen``
    (Spalte ``zoom``; None = Automatik). Paare A → B werden in Record-Reihenfolge von links nach rechts geprüft, nur wenn
    B direkt an A anschließt (rec_out A = rec_in B) und beide Brennweiten bekannt sind. Gleich (Abstand der scheinbaren
    Brennweiten kb × Zoom unter ``brennweite_gleich_max``) → ``digitalzoom``; ein gesetzter Zoom zählt für das nächste
    Paar mit. A kommt nur in Frage, wenn er noch keinen Zoom hat, nicht per Spalte festliegt und der Zoom den Schnitt zu
    seinem Vorgänger nicht wieder gleich macht. Ein erzwungener Zoom liegt fest; unter 1,0 oder über ``digitalzoom_max``
    ist er ein Plan-Fehler.
    Ausgabe je Shot in Eingabe-Reihenfolge: ``id``, ``zoom`` (1.0 = kein digitaler Zoom), ``hinweis`` (am zweiten Shot
    des Paares, sonst None) und ``fehler`` (str | None)."""
    grenze, gleich_max = float(cfg["digitalzoom_max"]), float(cfg["brennweite_gleich_max"])
    out = [{"id": e["id"], "zoom": 1.0, "hinweis": None, "fehler": None} for e in eintraege]
    fest = [e.get("zoom_erzwungen") is not None for e in eintraege]
    for i, e in enumerate(eintraege):
        if fest[i]:
            z = float(e["zoom_erzwungen"])
            out[i]["zoom"] = z
            if z < 1.0 or z > grenze + 1e-9:
                out[i]["fehler"] = (f"{e['id']}: Spalte zoom {_zahl(z, 3)}× außerhalb 1,0–{_zahl(grenze, 3)}× "
                                    f"(telemetrie.digitalzoom_max)")
    reihe = sorted(range(len(eintraege)), key=lambda i: eintraege[i]["rec_in"])
    vorgaenger: dict[int, int] = {}
    for ia, ib in zip(reihe, reihe[1:]):
        a, b = eintraege[ia], eintraege[ib]
        if a["rec_out"] != b["rec_in"] or a.get("kb_ende") is None or b.get("kb_anfang") is None:
            continue
        vorgaenger[ib] = ia
        schein_a, schein_b = a["kb_ende"] * out[ia]["zoom"], b["kb_anfang"] * out[ib]["zoom"]
        if not gleiche_brennweite(schein_a, schein_b, gleich_max):
            continue
        args = (a["kb_ende"], b["kb_anfang"], out[ia]["zoom"], out[ib]["zoom"], cfg)
        wahl = digitalzoom(*args, a_erlaubt=not fest[ia] and out[ia]["zoom"] == 1.0, b_erlaubt=not fest[ib])
        ip = vorgaenger.get(ia)
        if wahl and wahl[0] == "a" and ip is not None and gleiche_brennweite(
                eintraege[ip]["kb_ende"] * out[ip]["zoom"], a["kb_anfang"] * wahl[1], gleich_max):
            wahl = digitalzoom(*args, a_erlaubt=False, b_erlaubt=not fest[ib])     # kein Rückfall zum Vorgänger
        if wahl is None:
            grund = "Spalte zoom" if fest[ib] else f"{_zahl(grenze, 3)}×-Grenze"
            out[ib]["hinweis"] = (f"{b['id']}: gleiche Brennweite wie {a['id']} ({_zahl(schein_a)}/{_zahl(schein_b)} mm), "
                                  f"Zoom nicht möglich ({grund})")
            continue
        ziel = ia if wahl[0] == "a" else ib
        out[ziel]["zoom"] = wahl[1]
        out[ib]["hinweis"] = (f"{b['id']}: {_zahl(schein_a)} → {_zahl(schein_b)} mm am Schnitt, Zoom "
                              f"{_zahl(wahl[1], 3)}× auf {eintraege[ziel]['id']}")
    return out
```

**Anhängen an `tools/autocut/defaults.yaml`** (nach `  zoom_verlauf_hz: 5 …`):

```yaml
  # Brennweitenfolge B-Roll (Spec 2026-09-21): nie zweimal dieselbe Brennweite direkt hintereinander, sonst digitaler Zoom
  brennweite_gleich_max: 0.20   # Abstand größere/kleinere KB-Brennweite − 1: darunter gilt die Brennweite als gleich
  digitalzoom_faktor: 1.25      # Zoom für den Shot mit der längeren scheinbaren Brennweite (der kürzere braucht mehr)
  digitalzoom_max: 1.5          # Obergrenze für das Produkt aller Zooms eines Shots (4K: bewusst leicht hochskaliert)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py -q && venv/bin/python -m pytest -q`
Expected: alle bestehen; Gesamtlauf grün.

- [ ] **Step 5: Commit**

```bash
git add tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/defaults.yaml tools/autocut/tests/test_telemetrie.py
git commit -q -m "feat(autocut): Brennweitenfolge — gleiche Brennweite, digitaler Zoom bis 1,5×, Kettenregeln

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Bericht — Brennweite in mm, „Schnelle Zoomfahrten", kein Brennweiten-Vergleich

**Files:**
- Modify: `tools/autocut/src/niro_autocut/telemetrie_bericht.py` (Docstring, `_verteilung`, neu `_brennweite_mm`/`_schnelle_zooms`, `vergleich_index`, `bericht_md`)
- Modify: `tools/autocut/WORKFLOW-AutoCut.md` (ein Satz im Absatz „Zoomfahrten")
- Test: `tools/autocut/tests/test_telemetrie_bericht.py` (Testdaten ohne `brennweitenklasse`, Vergleichs-Tests, zwei neue Tests)

**Interfaces:**
- Consumes: Datensatz-Felder `kb_mm`, `kb_min`, `kb_max`, `zooms` (Task 2)
- Produces: `_brennweite_mm(rs: list[dict]) -> str`, `_schnelle_zooms(tele: list[dict]) -> list[str]`;
  `vergleich_index(tele, index) -> dict` nur noch mit den Schlüsseln `perspektive_hoehe`, `haltung`

- [ ] **Step 1: Failing Tests schreiben**

**Ersetzen in `tools/autocut/tests/test_telemetrie_bericht.py`:**

```python
TELE = [
    {"path": "/nas/FX3/FX3_1.MP4", "clip": "FX3_1", "kamera": "FX3", "ordner": "FX3", "quelle": "rtmd",
     "haltung": "gimbal", "bewegungsart": "fahrt", "brennweitenklasse": "normal", "perspektive_hoehe": "Augenhöhe",
     "wackeln": 0.04, "bewegung": 0.5, "ruhige_fenster": [0.0, 1.0],
     "fenster": [[0.0, 0.04, 0.5, "fahrt"], [1.0, 0.04, 0.5, "fahrt"]], "fehler": None, "roll_grad": 0.4},
    {"path": "/nas/A7/a7_1.MP4", "clip": "a7_1", "kamera": "a7IV", "ordner": "A7iv", "quelle": "rtmd",
     "haltung": "hand", "bewegungsart": "schwenk_links", "brennweitenklasse": "tele", "perspektive_hoehe": "Aufsicht",
     "wackeln": 0.41, "bewegung": 2.0, "ruhige_fenster": [], "fenster": [[0.0, 0.41, 2.0, "schwenk_links"]],
     "fehler": None, "roll_grad": 2.6},
    {"path": "/nas/Mavic/DJI_1.MOV", "clip": "DJI_1", "kamera": "DJI", "ordner": "Mavic", "quelle": "optisch",
     "haltung": "gimbal", "bewegungsart": "fahrt", "brennweitenklasse": None, "perspektive_hoehe": None,
     "wackeln": 0.02, "bewegung": 0.3, "ruhige_fenster": [0.0], "fenster": [[0.0, 0.02, 0.3, "fahrt"]],
     "fehler": None, "roll_grad": None},
    {"path": "/nas/FX3/FX3_2.MP4", "clip": "FX3_2", "kamera": "FX3", "ordner": "FX3", "quelle": "keine",
     "haltung": None, "bewegungsart": None, "brennweitenklasse": None, "perspektive_hoehe": None, "wackeln": None,
     "bewegung": None, "ruhige_fenster": [], "fenster": [], "fehler": "Datei nicht gefunden: /nas/FX3/FX3_2.MP4",
     "roll_grad": None},
]
```

**durch:**

```python
ZOOM_SCHNELL = {"von_s": 2.4, "bis_s": 3.1, "von_mm": 24.0, "bis_mm": 70.0, "tempo_max": 85.2, "tempo_mittel": 60.3,
                "ruck": 0.2, "ruckartig": False, "urteil": "schnell"}
ZOOM_LANGSAM = {"von_s": 5.0, "bis_s": 9.0, "von_mm": 70.0, "bis_mm": 105.0, "tempo_max": 12.0, "tempo_mittel": 10.1,
                "ruck": 0.1, "ruckartig": False, "urteil": "langsam"}
TELE = [
    {"path": "/nas/FX3/FX3_1.MP4", "clip": "FX3_1", "kamera": "FX3", "ordner": "FX3", "quelle": "rtmd",
     "haltung": "gimbal", "bewegungsart": "fahrt", "kb_mm": 35.0, "kb_min": 35.0, "kb_max": 35.0, "zooms": [],
     "perspektive_hoehe": "Augenhöhe", "wackeln": 0.04, "bewegung": 0.5, "ruhige_fenster": [0.0, 1.0],
     "fenster": [[0.0, 0.04, 0.5, "fahrt"], [1.0, 0.04, 0.5, "fahrt"]], "fehler": None, "roll_grad": 0.4},
    {"path": "/nas/A7/a7_1.MP4", "clip": "a7_1", "kamera": "a7IV", "ordner": "A7iv", "quelle": "rtmd",
     "haltung": "hand", "bewegungsart": "schwenk_links", "kb_mm": 71.6, "kb_min": 24.0, "kb_max": 105.0,
     "zooms": [ZOOM_SCHNELL, ZOOM_LANGSAM], "zoomfahrt": True, "perspektive_hoehe": "Aufsicht",
     "wackeln": 0.41, "bewegung": 2.0, "ruhige_fenster": [], "fenster": [[0.0, 0.41, 2.0, "schwenk_links"]],
     "fehler": None, "roll_grad": 2.6},
    {"path": "/nas/Mavic/DJI_1.MOV", "clip": "DJI_1", "kamera": "DJI", "ordner": "Mavic", "quelle": "optisch",
     "haltung": "gimbal", "bewegungsart": "fahrt", "kb_mm": None, "zooms": [], "perspektive_hoehe": None,
     "wackeln": 0.02, "bewegung": 0.3, "ruhige_fenster": [0.0], "fenster": [[0.0, 0.02, 0.3, "fahrt"]],
     "fehler": None, "roll_grad": None},
    {"path": "/nas/FX3/FX3_2.MP4", "clip": "FX3_2", "kamera": "FX3", "ordner": "FX3", "quelle": "keine",
     "haltung": None, "bewegungsart": None, "kb_mm": None, "perspektive_hoehe": None, "wackeln": None,
     "bewegung": None, "ruhige_fenster": [], "fenster": [], "fehler": "Datei nicht gefunden: /nas/FX3/FX3_2.MP4",
     "roll_grad": None},
]
```

**Ersetzen in `tools/autocut/tests/test_telemetrie_bericht.py`:**

```python
def test_vergleich_index_zaehlt_uebereinstimmung():
    v = B.vergleich_index(TELE, INDEX)
    # FX3 normal=normal, a7 A1 tele≠normal, A2 tele=tele
    assert v["brennweite"]["n"] == 3 and v["brennweite"]["gleich"] == 2
    assert v["perspektive_hoehe"]["n"] == 3 and v["perspektive_hoehe"]["gleich"] == 2
    assert (v["haltung"]["n"] == 3 and v["haltung"]["kreuz"][("gimbal", "Gimbal")] == 1
            and v["haltung"]["kreuz"][("hand", "Handkamera")] == 1)
    md = B.bericht_md(TELE, "T", INDEX)
    assert "## Vergleich mit dem B-Roll-Index" in md and "Brennweite: 2 von 3" in md and "| gimbal | Gimbal | 1 |" in md
```

**durch:**

```python
def test_vergleich_index_zaehlt_uebereinstimmung():
    v = B.vergleich_index(TELE, INDEX)
    assert set(v) == {"perspektive_hoehe", "haltung"}                      # keine Brennweite mehr (Spec 2026-09-21)
    # FX3 Augenhöhe = Augenhöhe, a7 A1 Aufsicht = Aufsicht, A2 Aufsicht ≠ Augenhöhe
    assert v["perspektive_hoehe"]["n"] == 3 and v["perspektive_hoehe"]["gleich"] == 2
    assert (v["haltung"]["n"] == 3 and v["haltung"]["kreuz"][("gimbal", "Gimbal")] == 1
            and v["haltung"]["kreuz"][("hand", "Handkamera")] == 1)
    md = B.bericht_md(TELE, "T", INDEX)
    assert "## Vergleich mit dem B-Roll-Index" in md and "Perspektive Höhe: 2 von 3" in md
    assert "Brennweite: " not in md and "| gimbal | Gimbal | 1 |" in md
```

**Ersetzen in `tools/autocut/tests/test_telemetrie_bericht.py`:**

```python
    v = B.vergleich_index(TELE, index)
    assert v["brennweite"]["n"] == 1 and v["brennweite"]["gleich"] == 0
    assert v["brennweite"]["kreuz"][("tele", "normal")] == 1
    assert v["perspektive_hoehe"]["n"] == 1 and v["perspektive_hoehe"]["kreuz"][("Aufsicht", "Augenhöhe")] == 1
```

**durch:**

```python
    v = B.vergleich_index(TELE, index)
    assert "brennweite" not in v
    assert v["perspektive_hoehe"]["n"] == 1 and v["perspektive_hoehe"]["kreuz"][("Aufsicht", "Augenhöhe")] == 1
```

**Anhängen an `tools/autocut/tests/test_telemetrie_bericht.py`:**

```python
def test_verteilung_brennweite_in_mm():
    md = B.bericht_md(TELE, "T")
    assert "Brennweite KB mm: Median (Spanne)" in md and "weit/normal/tele" not in md
    zeilen = {z.split("|")[1].strip(): z for z in md.splitlines() if z.startswith("| ")}
    assert "| 35,0 (35–35) |" in zeilen["FX3"] and "| 71,6 (24–105) |" in zeilen["a7IV"] and "| – |" in zeilen["DJI"]


def test_bericht_schnelle_zoomfahrten():
    md = B.bericht_md(TELE, "T")
    assert "## Schnelle Zoomfahrten" in md and "| a7_1 | a7IV | 2,4–3,1 | 24,0 → 70,0 | 85/60 | nein |" in md
    assert "5,0–9,0" not in md                                             # langsame Fahrt steht nicht in der Liste
    assert md.index("## Unruhigste Clips") < md.index("## Schnelle Zoomfahrten") < md.index("## Clips ohne Daten")
    ohne = B.bericht_md([{**TELE[0]}], "T")
    assert "## Schnelle Zoomfahrten" in ohne and ohne.split("## Schnelle Zoomfahrten")[1].splitlines()[2] == "- keine"
    alt = [{k: v for k, v in TELE[1].items() if k != "zooms"}]                # Datensatz von vor der Umstellung
    assert "- keine" in B.bericht_md(alt, "T").split("## Schnelle Zoomfahrten")[1]
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie_bericht.py -q`
Expected: `4 failed` (`test_vergleich_index_zaehlt_uebereinstimmung`, `test_vergleich_index_nutzt_claudes_originalwerte`,
`test_verteilung_brennweite_in_mm`, `test_bericht_schnelle_zoomfahrten`); die übrigen bestehen.

- [ ] **Step 3: Implementierung**

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie_bericht.py`:**

```python
"""Bericht ``Ergebnisse/Rohschnitt/telemetrie.md``: Kopf, Verteilung je Kamera, unruhigste Clips, Clips ohne Daten,
optional Vergleich mit dem B-Roll-Index (Stufe 2b: Brennweite, Perspektive Höhe; Erst-Index: Kamerabewegung ↔ Haltung)."""
from __future__ import annotations

import datetime as _dt
from collections import Counter
```

**durch:**

```python
"""Bericht ``Ergebnisse/Rohschnitt/telemetrie.md``: Kopf, Verteilung je Kamera (Brennweite in mm), unruhigste Clips,
schnelle Zoomfahrten, Clips ohne Daten, optional Vergleich mit dem B-Roll-Index (Stufe 2b: Perspektive Höhe; Erst-Index:
Kamerabewegung ↔ Haltung). Die Brennweite wird seit 21.09.2026 nicht mehr verglichen (mm statt Klassen)."""
from __future__ import annotations

import datetime as _dt
from collections import Counter
from statistics import median
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie_bericht.py`:**

```python
def _verteilung(tele: list[dict]) -> list[str]:
    zeilen = ["| Kamera | Clips | Quelle rtmd/optisch/keine | Haltung " + "/".join(HALTUNGEN)
              + " | Bewegungsart " + "/".join(BEWEGUNGSARTEN)
              + " | Brennweite weit/normal/tele | Perspektive Augenhöhe/Aufsicht/Untersicht/Vogel |",
              "|---|---|---|---|---|---|---|"]
    for kam in sorted({r.get("kamera") or "unbekannt" for r in tele}):
        rs = [r for r in tele if (r.get("kamera") or "unbekannt") == kam]
        q = Counter(r.get("quelle") for r in rs)
        h = Counter(r.get("haltung") for r in rs)
        b = Counter(r.get("bewegungsart") for r in rs)
        f = Counter(r.get("brennweitenklasse") for r in rs)
        p = Counter(r.get("perspektive_hoehe") for r in rs)
        zeilen.append(f"| {kam} | {len(rs)} | {q['rtmd']}/{q['optisch']}/{q['keine']} | "
                      + "/".join(str(h[x]) for x in HALTUNGEN) + " | "
                      + "/".join(str(b[x]) for x in BEWEGUNGSARTEN)
                      + f" | {f['weit']}/{f['normal']}/{f['tele']} | "
                      f"{p['Augenhöhe']}/{p['Aufsicht']}/{p['Untersicht']}/{p['Vogelperspektive']} |")
    return zeilen
```

**durch:**

```python
def _brennweite_mm(rs: list[dict]) -> str:
    """Median der Clip-Brennweiten (KB, mm) und Spanne von der kleinsten bis zur größten gemessenen; – ohne Daten."""
    mit = [r for r in rs if r.get("kb_mm")]
    if not mit:
        return "–"
    lo = min(float(r.get("kb_min") or r["kb_mm"]) for r in mit)
    hi = max(float(r.get("kb_max") or r["kb_mm"]) for r in mit)
    return f"{_de(median(float(r['kb_mm']) for r in mit), 1)} ({_de(lo, 0)}–{_de(hi, 0)})"


def _verteilung(tele: list[dict]) -> list[str]:
    zeilen = ["| Kamera | Clips | Quelle rtmd/optisch/keine | Haltung " + "/".join(HALTUNGEN)
              + " | Bewegungsart " + "/".join(BEWEGUNGSARTEN)
              + " | Brennweite KB mm: Median (Spanne) | Perspektive Augenhöhe/Aufsicht/Untersicht/Vogel |",
              "|---|---|---|---|---|---|---|"]
    for kam in sorted({r.get("kamera") or "unbekannt" for r in tele}):
        rs = [r for r in tele if (r.get("kamera") or "unbekannt") == kam]
        q = Counter(r.get("quelle") for r in rs)
        h = Counter(r.get("haltung") for r in rs)
        b = Counter(r.get("bewegungsart") for r in rs)
        p = Counter(r.get("perspektive_hoehe") for r in rs)
        zeilen.append(f"| {kam} | {len(rs)} | {q['rtmd']}/{q['optisch']}/{q['keine']} | "
                      + "/".join(str(h[x]) for x in HALTUNGEN) + " | "
                      + "/".join(str(b[x]) for x in BEWEGUNGSARTEN)
                      + f" | {_brennweite_mm(rs)} | "
                      f"{p['Augenhöhe']}/{p['Aufsicht']}/{p['Untersicht']}/{p['Vogelperspektive']} |")
    return zeilen


def _schnelle_zooms(tele: list[dict]) -> list[str]:
    """Schnelle Zoomfahrten aller Clips, nach Spitzentempo absteigend (bis TOP); „ruckartig" = ruck oder Stocken."""
    fahrten = [(z, r) for r in tele for z in (r.get("zooms") or []) if z.get("urteil") == "schnell"]
    if not fahrten:
        return ["- keine", ""]
    zeilen = ["| Clip | Kamera | von–bis (s) | mm → mm | Tempo % pro s (Spitze/Mittel) | ruckartig |",
              "|---|---|---|---|---|---|"]
    for z, r in sorted(fahrten, key=lambda zr: -float(zr[0].get("tempo_max") or 0.0))[:TOP]:
        zeilen.append(f"| {_md(r.get('clip'))} | {_md(r.get('kamera'))} | {_de(z['von_s'], 1)}–{_de(z['bis_s'], 1)} | "
                      f"{_de(z['von_mm'], 1)} → {_de(z['bis_mm'], 1)} | "
                      f"{_de(z['tempo_max'], 0)}/{_de(z.get('tempo_mittel'), 0)} | "
                      f"{'ja' if z.get('ruckartig') else 'nein'} |")
    return zeilen + [""]
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie_bericht.py`:**

```python
    """Übereinstimmung Telemetrie ↔ Claude: je Abschnitt Brennweite und Perspektive Höhe (Stufe 2b),
    je Clip Haltung ↔ Kamerabewegung. Verglichen wird gegen Claudes Originalwert (``claude`` im Abschnitt, Stufe 2b hat
    das Feld mit der Telemetrie überschrieben), sonst gegen den Feldwert — aber nur, wenn das Feld laut ``felder_quelle``
    des Clips nicht aus der Telemetrie stammt (sonst Abschnitt für dieses Feld übersprungen: kein Selbstvergleich)."""
    out = {k: {"n": 0, "gleich": 0, "kreuz": Counter()} for k in ("brennweite", "perspektive_hoehe", "haltung")}
```

**durch:**

```python
    """Übereinstimmung Telemetrie ↔ Claude: je Abschnitt Perspektive Höhe (Stufe 2b), je Clip Haltung ↔ Kamerabewegung;
    keine Brennweite mehr (Spec 2026-09-21: mm statt Klassen, Claudes Klasse bleibt unangetastet). Verglichen wird gegen
    Claudes Originalwert (``claude`` im Abschnitt, Stufe 2b hat das Feld mit der Telemetrie überschrieben), sonst gegen
    den Feldwert — aber nur, wenn das Feld laut ``felder_quelle`` des Clips nicht aus der Telemetrie stammt (sonst
    Abschnitt übersprungen: kein Selbstvergleich)."""
    out = {k: {"n": 0, "gleich": 0, "kreuz": Counter()} for k in ("perspektive_hoehe", "haltung")}
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie_bericht.py`:**

```python
        paare = (("brennweite", r.get("brennweitenklasse")), ("perspektive_hoehe", r.get("perspektive_hoehe")))
```

**durch:**

```python
        paare = (("perspektive_hoehe", r.get("perspektive_hoehe")),)
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie_bericht.py`:**

```python
    zeilen += _verteilung(tele) + ["", f"## Unruhigste Clips (bis {TOP}, nach wackeln)", ""] + _unruhigste(tele) + [""]
```

**durch:**

```python
    zeilen += _verteilung(tele) + ["", f"## Unruhigste Clips (bis {TOP}, nach wackeln)", ""] + _unruhigste(tele) + [""]
    zeilen += [f"## Schnelle Zoomfahrten (bis {TOP}, nach Spitzentempo)", ""] + _schnelle_zooms(tele)
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie_bericht.py`:**

```python
        zeilen += _kreuz("Brennweite", v["brennweite"], "Telemetrie", "Claude (2b)")
        zeilen += _kreuz("Perspektive Höhe", v["perspektive_hoehe"], "Telemetrie", "Claude (2b)")
```

**durch:**

```python
        zeilen += _kreuz("Perspektive Höhe", v["perspektive_hoehe"], "Telemetrie", "Claude (2b)")
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie_bericht.py tests/test_telemetrie_script.py -q && venv/bin/python -m pytest -q`
Expected: alle bestehen; Gesamtlauf grün.

- [ ] **Step 5: Doku**

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
`ruhige_fenster`. Ohne rtmd-Brennweite (Mavic, Avata) bleiben `kb_verlauf` und `zooms` leer (Brennweite unbekannt).
```

**durch:**

```text
`ruhige_fenster`. Ohne rtmd-Brennweite (Mavic, Avata) bleiben `kb_verlauf` und `zooms` leer (Brennweite unbekannt).
Der Bericht `telemetrie.md` zeigt die KB-Brennweite je Kamera in mm und listet die schnellen Fahrten; der Vergleich mit
dem B-Roll-Index umfasst nur noch Perspektive Höhe und Haltung.
```

- [ ] **Step 6: Commit**

```bash
git add tools/autocut/src/niro_autocut/telemetrie_bericht.py tools/autocut/tests/test_telemetrie_bericht.py \
  tools/autocut/WORKFLOW-AutoCut.md
git commit -q -m "feat(autocut): Telemetrie-Bericht mit Brennweite in mm und schnellen Zoomfahrten, Vergleich ohne Brennweite

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Stufe 2b — `brennweite_mm`/`zoom` je Abschnitt, Claudes Klasse bleibt; Brennweitenklassen entfallen

**Files:**
- Modify: `tools/autocut/src/niro_autocut/index_sections.py` (Import, `telemetrie_text`, `_TELE_FELDER`, `_tele_felder`, `telemetrie_anwenden`, Kommentar in `index_sections_clip`)
- Modify: `tools/autocut/scripts/autocut_index_sections.py` (zwei Meldungen), `tools/autocut/prompts/index-sections.md` (Regel 4)
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (`brennweitenklasse()`, Feld und Aufruf entfernen), `tools/autocut/defaults.yaml` (`brennweite_klassen_kb` entfernen)
- Modify: `tools/autocut/WORKFLOW-AutoCut.md` (Stufe 2b, Kopf-Tabelle, Telemetrie-Felder, Abnehmer, Kalibrierwerte), `tools/autocut/README.md` (Tabellenzeile)
- Test: `tools/autocut/tests/test_index_sections.py` (bisherige Überschreib-Tests umstellen, ein neuer Test), `tools/autocut/tests/test_telemetrie.py` (`CFG`, drei Stellen mit `brennweitenklasse`)

**Interfaces:**
- Consumes: Task 3 (`abschnitt_brennweite`, `brennweite_text`), `abschnitt_werte`
- Produces:
  - `telemetrie_text(tele, abschnitte, fenster_s=2.0) -> str` mit „KB 71,6 mm" bzw. „KB 24–70 mm, langsamer Zoom"
  - `telemetrie_anwenden(rec, tele, fenster_s=2.0) -> tuple[dict, bool]` setzt je Abschnitt `brennweite_mm`, `zoom`
    (nur mit `kb_verlauf`), `bewegungsart`, `haltung` und überschreibt nur noch `perspektive_hoehe`
  - `_TELE_FELDER = (("perspektive_hoehe", "perspektive_hoehe"),)`; `felder_quelle`/`claude` nur noch für `perspektive_hoehe`
  - entfallen: `telemetrie.brennweitenklasse()`, Datensatz-Feld `brennweitenklasse`, Schlüssel `brennweite_klassen_kb`

- [ ] **Step 1: Failing Tests schreiben (bestehende Tests auf das neue Verhalten umstellen)**

**Ersetzen in `tools/autocut/tests/test_index_sections.py`:**

```python
TELE = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "clip": "FX3_1", "quelle": "rtmd", "kb_mm": 71.6, "brennweitenklasse": "tele",
        "pitch_grad": -12.0, "perspektive_hoehe": "Aufsicht", "haltung": "gimbal", "wackeln": 0.05, "fehler": None,
```

**durch:**

```python
TELE = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "clip": "FX3_1", "quelle": "rtmd", "kb_mm": 71.6,
        "kb_verlauf": [[0.0, 71.6]], "zooms": [],
        "pitch_grad": -12.0, "perspektive_hoehe": "Aufsicht", "haltung": "gimbal", "wackeln": 0.05, "fehler": None,
```

**Ersetzen in `tools/autocut/tests/test_index_sections.py`:**

```python
    text = S.telemetrie_text(TELE, rec["abschnitte"])
    assert "KB 71.6 mm = tele" in text and "Pitch -12° = Aufsicht" in text and "Haltung gimbal" in text
    assert "A1 schwenk_links, A2 statisch" in text
    assert S.telemetrie_text(None, rec["abschnitte"]) == "" and S.telemetrie_text({"quelle": "keine"}, []) == ""
    neu, geaendert = S.telemetrie_anwenden(rec, TELE)
    assert geaendert and neu["felder_quelle"] == {"brennweite": "rtmd", "perspektive_hoehe": "rtmd"}
    assert [a["brennweite"] for a in neu["abschnitte"]] == ["tele", "tele"]
    assert [a["perspektive_hoehe"] for a in neu["abschnitte"]] == ["Aufsicht", "Aufsicht"]
    assert [a["bewegungsart"] for a in neu["abschnitte"]] == ["schwenk_links", "statisch"]
    assert neu["abschnitte"][0]["haltung"] == "gimbal"
    assert S.telemetrie_anwenden(rec, None) == (rec, False)
    wieder, geaendert2 = S.telemetrie_anwenden(neu, TELE)
    assert not geaendert2 and wieder == neu
    assert "brennweite" not in S.telemetrie_anwenden({"abschnitte": [{"von_s": 0, "bis_s": 2}]}, TELE)[0]["abschnitte"][0]
```

**durch:**

```python
    text = S.telemetrie_text(TELE, rec["abschnitte"])
    assert "KB 71,6 mm" in text and "= tele" not in text and "Pitch -12° = Aufsicht" in text and "Haltung gimbal" in text
    assert "A1 schwenk_links, A2 statisch" in text and "brennweite und" not in text
    assert S.telemetrie_text(None, rec["abschnitte"]) == "" and S.telemetrie_text({"quelle": "keine"}, []) == ""
    neu, geaendert = S.telemetrie_anwenden(rec, TELE)
    assert geaendert and neu["felder_quelle"] == {"perspektive_hoehe": "rtmd"}
    assert [a["brennweite"] for a in neu["abschnitte"]] == ["normal", "tele"]              # Claudes Klasse bleibt
    assert [a["brennweite_mm"] for a in neu["abschnitte"]] == [71.6, 71.6]
    assert [a["zoom"] for a in neu["abschnitte"]] == ["keiner", "keiner"]
    assert [a["perspektive_hoehe"] for a in neu["abschnitte"]] == ["Aufsicht", "Aufsicht"]
    assert [a["bewegungsart"] for a in neu["abschnitte"]] == ["schwenk_links", "statisch"]
    assert neu["abschnitte"][0]["haltung"] == "gimbal"
    assert S.telemetrie_anwenden(rec, None) == (rec, False)
    wieder, geaendert2 = S.telemetrie_anwenden(neu, TELE)
    assert not geaendert2 and wieder == neu
    ohne_feld = S.telemetrie_anwenden({"abschnitte": [{"von_s": 0, "bis_s": 2}]}, TELE)[0]["abschnitte"][0]
    assert "brennweite" not in ohne_feld and "perspektive_hoehe" not in ohne_feld and ohne_feld["brennweite_mm"] == 71.6
```

**Ersetzen in `tools/autocut/tests/test_index_sections.py`:**

```python
    out = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", describe=kein_api, telemetrie=TELE)
    assert out["_cache"] is True and out["abschnitte"][0]["brennweite"] == "tele"
    assert out["felder_quelle"]["brennweite"] == "rtmd"
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["abschnitte"][0]["perspektive_hoehe"] == "Aufsicht"
    assert cached["abschnitte"][0]["claude"] == {"brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}   # I2
```

**durch:**

```python
    out = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", describe=kein_api, telemetrie=TELE)
    assert out["_cache"] is True and out["abschnitte"][0]["brennweite"] == "normal"         # Claudes Klasse bleibt
    assert out["felder_quelle"] == {"perspektive_hoehe": "rtmd"} and out["abschnitte"][0]["brennweite_mm"] == 71.6
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["abschnitte"][0]["perspektive_hoehe"] == "Aufsicht" and cached["abschnitte"][0]["zoom"] == "keiner"
    assert cached["abschnitte"][0]["claude"] == {"perspektive_hoehe": "Augenhöhe"}                          # I2
```

**Ersetzen in `tools/autocut/tests/test_index_sections.py`:**

```python
        assert "Kamera-Telemetrie" in meta_text and "KB 71.6 mm = tele" in meta_text
```

**durch:**

```python
        assert "Kamera-Telemetrie" in meta_text and "KB 71,6 mm" in meta_text
```

**Ersetzen in `tools/autocut/tests/test_index_sections.py`:**

```python
    a = out["abschnitte"][0]
    assert a["brennweite"] == "tele" and a["perspektive_hoehe"] == "Aufsicht"
    assert a["bewegungsart"] == "schwenk_links" and a["haltung"] == "gimbal"
    assert a["claude"] == {"brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}          # I2: Claudes Antwort
    assert out["felder_quelle"] == {"brennweite": "rtmd", "perspektive_hoehe": "rtmd"}
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["felder_quelle"]["brennweite"] == "rtmd" and "_cache" not in cached
```

**durch:**

```python
    a = out["abschnitte"][0]
    assert a["brennweite"] == "normal" and a["perspektive_hoehe"] == "Aufsicht" and a["brennweite_mm"] == 71.6
    assert a["bewegungsart"] == "schwenk_links" and a["haltung"] == "gimbal" and a["zoom"] == "keiner"
    assert a["claude"] == {"perspektive_hoehe": "Augenhöhe"}                                   # I2: Claudes Antwort
    assert out["felder_quelle"] == {"perspektive_hoehe": "rtmd"}
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["felder_quelle"] == {"perspektive_hoehe": "rtmd"} and "_cache" not in cached
```

**Ersetzen in `tools/autocut/tests/test_index_sections.py`:**

```python
_TELE_FENSTER = {"path": "/nas/B-Roll/Flur/FX3_9.MP4", "clip": "FX3_9", "quelle": "rtmd", "kb_mm": 50.0,
                 "brennweitenklasse": "normal", "pitch_grad": 0.0, "perspektive_hoehe": "Augenhöhe",
```

**durch:**

```python
_TELE_FENSTER = {"path": "/nas/B-Roll/Flur/FX3_9.MP4", "clip": "FX3_9", "quelle": "rtmd", "kb_mm": 50.0,
                 "pitch_grad": 0.0, "perspektive_hoehe": "Augenhöhe",
```

**Ersetzen in `tools/autocut/tests/test_index_sections.py`:**

```python
    neu, geaendert = S.telemetrie_anwenden(rec, TELE)
    assert geaendert and [a["claude"] for a in neu["abschnitte"]] == [
        {"brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}, {"brennweite": "tele", "perspektive_hoehe": "Aufsicht"}]
    wieder, geaendert2 = S.telemetrie_anwenden(neu, TELE)
    assert not geaendert2 and wieder == neu
    ohne_pitch, _ = S.telemetrie_anwenden(rec, {**TELE, "pitch_grad": None, "perspektive_hoehe": None})
    assert ohne_pitch["abschnitte"][0]["claude"] == {"brennweite": "normal"}         # nur überschriebene Felder
    assert ohne_pitch["abschnitte"][0]["perspektive_hoehe"] == "Augenhöhe"
    # Altbestand (vor dem Fix angewendet): felder_quelle gesetzt, kein claude → der Telemetrie-Wert ist nicht Claudes
    alt = {"felder_quelle": {"brennweite": "rtmd", "perspektive_hoehe": "rtmd"},
           "abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "tele", "perspektive_hoehe": "Aufsicht"}]}
```

**durch:**

```python
    neu, geaendert = S.telemetrie_anwenden(rec, TELE)
    assert geaendert and [a["claude"] for a in neu["abschnitte"]] == [
        {"perspektive_hoehe": "Augenhöhe"}, {"perspektive_hoehe": "Aufsicht"}]           # nur noch Perspektive
    wieder, geaendert2 = S.telemetrie_anwenden(neu, TELE)
    assert not geaendert2 and wieder == neu
    ohne_pitch, _ = S.telemetrie_anwenden(rec, {**TELE, "pitch_grad": None, "perspektive_hoehe": None})
    assert "claude" not in ohne_pitch["abschnitte"][0]                                   # nichts überschrieben
    assert ohne_pitch["abschnitte"][0]["perspektive_hoehe"] == "Augenhöhe"
    # Altbestand (vor dem Fix angewendet): felder_quelle gesetzt, kein claude → der Telemetrie-Wert ist nicht Claudes
    alt = {"felder_quelle": {"perspektive_hoehe": "rtmd"},
           "abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "tele", "perspektive_hoehe": "Aufsicht"}]}
```

**Ersetzen in `tools/autocut/tests/test_index_sections.py`:**

```python
    """M3: Brennweite und Pitch kommen immer aus den Metadaten, auch wenn die Bewegung optisch gemessen wurde."""
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}]}
    neu, _ = S.telemetrie_anwenden(rec, {**TELE, "quelle": "optisch"})
    assert neu["felder_quelle"] == {"brennweite": "rtmd", "perspektive_hoehe": "rtmd"}
```

**durch:**

```python
    """M3: Pitch und Brennweite in mm kommen immer aus den Metadaten, auch wenn die Bewegung optisch gemessen wurde."""
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}]}
    neu, _ = S.telemetrie_anwenden(rec, {**TELE, "quelle": "optisch"})
    assert neu["felder_quelle"] == {"perspektive_hoehe": "rtmd"} and neu["abschnitte"][0]["brennweite_mm"] == 71.6
```

**Ersetzen in `tools/autocut/tests/test_index_sections.py`:**

```python
    """I2: im API-Pfad kommen brennweite/perspektive_hoehe frisch aus der Modellantwort — claude wird daraus neu gesetzt,
    auch wenn der Datensatz schon felder_quelle und ein altes claude trägt (Neulauf mit --force)."""
```

**durch:**

```python
    """I2: im API-Pfad kommt perspektive_hoehe frisch aus der Modellantwort — claude wird daraus neu gesetzt, auch wenn
    der Datensatz schon felder_quelle und ein altes claude trägt (Neulauf mit --force; hier noch mit der Brennweite
    aus der Zeit vor der Umstellung: sie verschwindet aus claude und felder_quelle, Claudes frische Klasse bleibt)."""
```

**Ersetzen in `tools/autocut/tests/test_index_sections.py`:**

```python
    out = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", force=True, describe=fake_describe, telemetrie=TELE)
    a = out["abschnitte"][0]
    assert a["brennweite"] == "tele" and a["perspektive_hoehe"] == "Aufsicht"
    assert a["claude"] == {"brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["abschnitte"][0]["claude"] == {"brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}
    # Neulauf ohne Telemetrie, felder_quelle noch vom früheren Lauf: Claudes frische Werte bleiben in claude stehen
    ohne = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", force=True, describe=fake_describe)
    b = ohne["abschnitte"][0]
    assert b["brennweite"] == "normal" and b["claude"] == {"brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}
```

**durch:**

```python
    out = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", force=True, describe=fake_describe, telemetrie=TELE)
    a = out["abschnitte"][0]
    assert a["brennweite"] == "normal" and a["perspektive_hoehe"] == "Aufsicht"
    assert a["claude"] == {"perspektive_hoehe": "Augenhöhe"} and out["felder_quelle"] == {"perspektive_hoehe": "rtmd"}
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["abschnitte"][0]["claude"] == {"perspektive_hoehe": "Augenhöhe"}
    # Neulauf ohne Telemetrie, felder_quelle noch vom früheren Lauf: Claudes frische Werte bleiben in claude stehen
    ohne = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", force=True, describe=fake_describe)
    b = ohne["abschnitte"][0]
    assert b["brennweite"] == "normal" and b["claude"] == {"perspektive_hoehe": "Augenhöhe"}
```

**Anhängen an `tools/autocut/tests/test_index_sections.py`:**

```python
# --- Zoomfahrten und Brennweite in mm (Spec 2026-09-21, Abschnitt 3) ------------------------------------------------

def test_telemetrie_anwenden_brennweite_mm_und_zoom_je_abschnitt():
    tele = {**TELE, "kb_mm": 50.0, "kb_verlauf": [[0.0, 24.0], [2.0, 24.0], [3.0, 70.0], [8.0, 70.0]],
            "zooms": [{"von_s": 2.0, "bis_s": 3.0, "von_mm": 24.0, "bis_mm": 70.0, "tempo_max": 107.0,
                       "tempo_mittel": 90.0, "ruck": 0.1, "ruckartig": False, "urteil": "schnell"}]}
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 2}, {"von_s": 2, "bis_s": 4}, {"von_s": 4, "bis_s": 8}]}
    neu, _ = S.telemetrie_anwenden(rec, tele)
    # 2–4 s: 2,0 … 2,9 s steigend, 3,0 … 4,0 s = 70 mm → Median 70; der Zoom 2–3 s schneidet nur diesen Abschnitt
    assert [a["brennweite_mm"] for a in neu["abschnitte"]] == [24.0, 70.0, 70.0]
    assert [a["zoom"] for a in neu["abschnitte"]] == ["keiner", "schnell", "keiner"]
    assert "KB 24–70 mm, schneller Zoom" in S.telemetrie_text(tele, rec["abschnitte"])
    alt = {k: v for k, v in TELE.items() if k not in ("kb_verlauf", "zooms")}          # Datensatz von vor der Umstellung
    ohne, _ = S.telemetrie_anwenden(rec, alt)
    assert all("brennweite_mm" not in a and "zoom" not in a for a in ohne["abschnitte"])
    assert "KB 71,6 mm" in S.telemetrie_text(alt, rec["abschnitte"])
```

**Ersetzen in `tools/autocut/tests/test_telemetrie.py`:**

```python
       "hand_hf_anteil_min": 0.35, "brennweite_klassen_kb": [30, 60], "pitch_klassen_grad": [-60, -8, 8],
```

**durch:**

```python
       "hand_hf_anteil_min": 0.35, "pitch_klassen_grad": [-60, -8, 8],
```

**Ersetzen in `tools/autocut/tests/test_telemetrie.py`:**

```python
def test_klassen():
    brennweiten = [T.brennweitenklasse(k, [30, 60]) for k in (24, 30, 50, 60, 71.6, 283.8)]
    assert brennweiten == ["weit", "normal", "normal", "normal", "tele", "tele"]
```

**durch:**

```python
def test_klassen():
    assert not hasattr(T, "brennweitenklasse")                 # Brennweitenklassen entfallen (Spec 2026-09-21)
```

**Ersetzen in `tools/autocut/tests/test_telemetrie.py`:**

```python
    assert rec["brennweitenklasse"] == "tele" and rec["pitch_grad"] == 0.0 and rec["perspektive_hoehe"] == "Augenhöhe"
```

**durch:**

```python
    assert "brennweitenklasse" not in rec and rec["pitch_grad"] == 0.0 and rec["perspektive_hoehe"] == "Augenhöhe"
```

**Ersetzen in `tools/autocut/tests/test_telemetrie.py`:**

```python
    assert (rec["quelle"] == "optisch" and rec["kb_mm"] == 71.6 and rec["brennweitenklasse"] == "tele"
           and rec["haltung"] == "stativ")
```

**durch:**

```python
    assert (rec["quelle"] == "optisch" and rec["kb_mm"] == 71.6 and rec["kb_verlauf"] == [[0.0, 71.6]]
           and rec["haltung"] == "stativ")
```

**Ersetzen in `tools/autocut/tests/test_telemetrie.py`:**

```python
def test_defaults_haben_brennweitenregel():
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    assert cfg["brennweite_gleich_max"] == 0.20 and cfg["digitalzoom_faktor"] == 1.25 and cfg["digitalzoom_max"] == 1.5
```

**durch:**

```python
def test_defaults_haben_brennweitenregel():
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    assert cfg["brennweite_gleich_max"] == 0.20 and cfg["digitalzoom_faktor"] == 1.25 and cfg["digitalzoom_max"] == 1.5
    assert "brennweite_klassen_kb" not in cfg
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_index_sections.py tests/test_telemetrie.py -q`
Expected: `13 failed, 108 passed` — sechs in `test_index_sections.py` (`test_telemetrie_text_und_anwenden`,
`test_index_sections_clip_wendet_telemetrie_bei_cache_treffer_an`, `test_index_sections_clip_api_mit_telemetrie`,
`test_telemetrie_anwenden_felder_quelle_immer_metadaten`, `test_index_sections_clip_api_setzt_claude_aus_der_antwort`,
`test_telemetrie_anwenden_brennweite_mm_und_zoom_je_abschnitt`: alte Klasse überschrieben, „KB 71.6 mm = tele",
`felder_quelle` mit Brennweite, fehlendes `brennweite_mm`) und sieben in `test_telemetrie.py` (`test_klassen`,
`test_defaults_haben_brennweitenregel` und fünf `clip_messen`-Tests mit `KeyError: 'brennweite_klassen_kb'` — die Test-CFG
hat den Schlüssel schon nicht mehr, der alte Code liest ihn noch). `test_telemetrie_anwenden_sichert_claudes_originalwerte`
besteht schon vorher (ohne `brennweitenklasse` im Test-Datensatz überschreibt auch der alte Code nur die Perspektive).

- [ ] **Step 3: Implementierung**

**Ersetzen in `tools/autocut/src/niro_autocut/index_sections.py`:**

```python
from .telemetrie import abschnitt_werte, finden, laden as telemetrie_laden
```

**durch:**

```python
from .telemetrie import abschnitt_brennweite, abschnitt_werte, brennweite_text, finden, laden as telemetrie_laden
```

**Ersetzen in `tools/autocut/src/niro_autocut/index_sections.py`:**

```python
    teile = []
    if tele.get("kb_mm"):
        teile.append(f"KB {tele['kb_mm']:g} mm = {tele.get('brennweitenklasse')}")
```

**durch:**

```python
    teile = []
    kb = brennweite_text(tele)
    if kb:
        teile.append(kb)
```

**Ersetzen in `tools/autocut/src/niro_autocut/index_sections.py`:**

```python
    praefix = "Kamera-Telemetrie (gemessen; brennweite und perspektive_hoehe setzt das Schnittprogramm daraus fest): "
```

**durch:**

```python
    praefix = "Kamera-Telemetrie (gemessen; perspektive_hoehe setzt das Schnittprogramm daraus fest): "
```

**Ersetzen in `tools/autocut/src/niro_autocut/index_sections.py`:**

```python
_TELE_FELDER = (("brennweite", "brennweitenklasse"), ("perspektive_hoehe", "perspektive_hoehe"))


def _tele_felder(tele: dict | None) -> dict[str, str]:
    """Abschnittsfeld → Metadatenklasse, die ``telemetrie_anwenden`` setzt (Brennweite, Pitch); leer ohne Telemetrie."""
```

**durch:**

```python
_TELE_FELDER = (("perspektive_hoehe", "perspektive_hoehe"),)   # Claudes Klasse ``brennweite`` bleibt (Spec 2026-09-21)


def _tele_felder(tele: dict | None) -> dict[str, str]:
    """Abschnittsfeld → Metadatenklasse, die ``telemetrie_anwenden`` setzt (Pitch); leer ohne Telemetrie."""
```

**Ersetzen in `tools/autocut/src/niro_autocut/index_sections.py`:**

```python
    """Metadatenklassen in die Abschnitte: brennweite/perspektive_hoehe überschreiben (``felder_quelle`` je Feld „rtmd":
    Brennweite und Pitch stammen immer aus den Metadaten, auch wenn die Bewegung optisch gemessen wurde),
    bewegungsart/haltung ergänzen. Claudes Originalwert je überschriebenem Feld bleibt im Abschnitt unter ``claude``:
    stammt das Feld laut ``felder_quelle`` schon aus der Telemetrie, bleibt ein vorhandenes ``claude[feld]`` stehen
    (der aktuelle Wert ist dann der Telemetrie-Wert), sonst ist der aktuelle Wert Claudes und wird gesichert.
    Idempotent. Liefert (Datensatz, geändert?); ohne Telemetrie unverändert."""
```

**durch:**

```python
    """Metadaten in die Abschnitte: perspektive_hoehe überschreiben (``felder_quelle`` „rtmd": der Pitch stammt immer
    aus den Metadaten, auch wenn die Bewegung optisch gemessen wurde), ``brennweite_mm``/``zoom`` (Brennweite in mm und
    schnellste Zoomfahrt im Abschnitt, nur mit ``kb_verlauf``) sowie bewegungsart/haltung ergänzen. Claudes Klasse
    ``brennweite`` bleibt unangetastet (Spec 2026-09-21). Claudes Originalwert je überschriebenem Feld bleibt im
    Abschnitt unter ``claude``: stammt das Feld laut ``felder_quelle`` schon aus der Telemetrie, bleibt ein vorhandenes
    ``claude[feld]`` stehen (der aktuelle Wert ist dann der Telemetrie-Wert), sonst ist der aktuelle Wert Claudes und
    wird gesichert. Idempotent. Liefert (Datensatz, geändert?); ohne Telemetrie unverändert."""
```

**Ersetzen in `tools/autocut/src/niro_autocut/index_sections.py`:**

```python
        w = abschnitt_werte(tele, float(b.get("von_s", 0)), float(b.get("bis_s", 0)), fenster_s)
        for k in ("bewegungsart", "haltung"):
```

**durch:**

```python
        von, bis = float(b.get("von_s", 0)), float(b.get("bis_s", 0))
        w = {**abschnitt_werte(tele, von, bis, fenster_s), **abschnitt_brennweite(tele, von, bis)}
        for k in ("bewegungsart", "haltung", "brennweite_mm", "zoom"):
```

**Ersetzen in `tools/autocut/src/niro_autocut/index_sections.py`:**

```python
    # brennweite/perspektive_hoehe kommen hier frisch aus der Modellantwort: ``claude`` daraus neu setzen (ein altes gilt
    # nicht mehr) — für die Felder, die die Telemetrie jetzt überschreibt oder felder_quelle aus einem früheren Lauf führt
```

**durch:**

```python
    # perspektive_hoehe kommt hier frisch aus der Modellantwort: ``claude`` daraus neu setzen (ein altes gilt nicht
    # mehr) — für die Felder, die die Telemetrie jetzt überschreibt oder felder_quelle aus einem früheren Lauf führt
```

**Ersetzen in `tools/autocut/scripts/autocut_index_sections.py`:**

```python
        hinweis = ("" if mit_tele else " — erst scripts/autocut_telemetrie.py ausführen, dann kommen Brennweite "
                   "und Perspektive Höhe aus den Metadaten.")
```

**durch:**

```python
        hinweis = ("" if mit_tele else " — erst scripts/autocut_telemetrie.py ausführen, dann kommen Perspektive Höhe "
                   "sowie Brennweite in mm und Zoom je Abschnitt aus den Metadaten.")
```

**Ersetzen in `tools/autocut/scripts/autocut_index_sections.py`:**

```python
                  f"Telemetrie genutzt: {out['mit_telemetrie']} Clips (brennweite/perspektive_hoehe aus Metadaten, "
                  f"bewegungsart/haltung je Abschnitt)",
```

**durch:**

```python
                  f"Telemetrie genutzt: {out['mit_telemetrie']} Clips (perspektive_hoehe aus Metadaten, "
                  f"brennweite_mm/zoom/bewegungsart/haltung je Abschnitt)",
```

**Ersetzen in `tools/autocut/prompts/index-sections.md`:**

```text
brennweite und perspektive_hoehe trotzdem nach Schema ausfüllen
```

**durch:**

```text
perspektive_hoehe trotzdem nach Schema ausfüllen
```

**Ersetzen in `tools/autocut/prompts/index-sections.md`:**

```text
(das Schnittprogramm ersetzt sie durch die Messwerte);
```

**durch:**

```text
(das Schnittprogramm ersetzt sie durch den Messwert); brennweite bleibt deine Einschätzung, die gemessenen mm helfen dabei;
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
def brennweitenklasse(kb_mm: float, grenzen: list | tuple) -> str:
    """weit unter grenzen[0], tele über grenzen[1], dazwischen normal (Grenzen zählen zu normal)."""
    if kb_mm < grenzen[0]:
        return "weit"
    if kb_mm > grenzen[1]:
        return "tele"
    return "normal"


def perspektive_hoehe(pitch_grad: float | None, grenzen: list | tuple) -> str | None:
```

**durch:**

```python
def perspektive_hoehe(pitch_grad: float | None, grenzen: list | tuple) -> str | None:
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
            "kb_max": None, "kb_verlauf": [], "zooms": [], "zoomfahrt": False, "fokus_m": None,
            "brennweitenklasse": None, "pitch_grad": None,
```

**durch:**

```python
            "kb_max": None, "kb_verlauf": [], "zooms": [], "zoomfahrt": False, "fokus_m": None, "pitch_grad": None,
```

**Ersetzen in `tools/autocut/src/niro_autocut/telemetrie.py`:**

```python
                out["zoomfahrt"] = bool(out["zooms"])
                out["brennweitenklasse"] = brennweitenklasse(kb, cfg["brennweite_klassen_kb"])
```

**durch:**

```python
                out["zoomfahrt"] = bool(out["zooms"])
```

**Ersetzen in `tools/autocut/defaults.yaml`:**

```yaml
  brennweite_klassen_kb: [30, 60]    # KB-Brennweite: < 30 weit, > 60 tele, sonst normal
  pitch_klassen_grad: [-60, -8, 8]   # Pitch: ≤ −60 Vogelperspektive, ≤ −8 Aufsicht, ≥ 8 Untersicht, sonst Augenhöhe
```

**durch:**

```yaml
  pitch_klassen_grad: [-60, -8, 8]   # Pitch: ≤ −60 Vogelperspektive, ≤ −8 Aufsicht, ≥ 8 Untersicht, sonst Augenhöhe
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_index_sections.py tests/test_telemetrie.py tests/test_telemetrie_bericht.py tests/test_telemetrie_kalibrierung.py -q && venv/bin/python -m pytest -q`
Expected: alle bestehen; `grep -rn "brennweitenklasse\|brennweite_klassen_kb" tools/autocut/src tools/autocut/scripts tools/autocut/defaults.yaml`
findet nichts mehr; Gesamtlauf grün.

- [ ] **Step 5: Doku**

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
Liegt `telemetrie.json` vor (`autocut_telemetrie.py`), bekommt der Abschnittsbogen eine Kontextzeile mit
KB-Brennweite, Pitch, Haltung und Bewegungsart je Abschnitt; nach der Antwort setzt der Code `brennweite`
und `perspektive_hoehe` aus den Metadaten fest (`felder_quelle` im Datensatz) und ergänzt je Abschnitt
`bewegungsart` und `haltung`. `claude` je Abschnitt hält Claudes Originalwerte der überschriebenen Felder; der
Bericht `telemetrie.md` vergleicht dagegen. Cache-Treffer bekommen die Felder ohne API-Aufruf. Ohne Telemetrie bleibt
alles wie bisher; `--dry-run` zeigt die Zahl.
```

**durch:**

```text
Liegt `telemetrie.json` vor (`autocut_telemetrie.py`), bekommt der Abschnittsbogen eine Kontextzeile mit der
KB-Brennweite in mm („KB 71,6 mm", bei Zoomfahrten „KB 24–70 mm, langsamer Zoom"), Pitch, Haltung und Bewegungsart je
Abschnitt; nach der Antwort setzt der Code `perspektive_hoehe` aus den Metadaten fest (`felder_quelle` im Datensatz)
und ergänzt je Abschnitt `brennweite_mm` (Median im Abschnitt), `zoom` (keiner/langsam/schnell), `bewegungsart` und
`haltung`. Claudes Klasse `brennweite` bleibt unangetastet (seit 21.09.2026, Spec Zoomfahrten). `claude` je Abschnitt
hält Claudes Originalwert der überschriebenen Perspektive; der Bericht `telemetrie.md` vergleicht dagegen. Cache-Treffer
bekommen die Felder ohne API-Aufruf. Ohne Telemetrie bleibt alles wie bisher; `--dry-run` zeigt die Zahl.
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
Brennweiten-/Perspektivklasse; Grundlage
```

**durch:**

```text
Brennweite in mm, Zoomfahrten, Perspektivklasse; Grundlage
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
Felder je Clip: `quelle` (rtmd/optisch/keine), `kamera`, `kb_mm`/`brennweitenklasse` (weit < 30, tele > 60),
```

**durch:**

```text
Felder je Clip: `quelle` (rtmd/optisch/keine), `kamera`, `kb_mm` (Median; Verlauf und Zoomfahrten unten),
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
Stufe 2b (Brennweite/Perspektive aus Metadaten,
```

**durch:**

```text
Stufe 2b (Perspektive aus Metadaten, Brennweite in mm und Zoom je Abschnitt,
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
Clip-Medians; Grenzen [30, 60] vorerst unverändert (offen, Spec-Nachtrag „Kalibrierung").
```

**durch:**

```text
Clip-Medians. Die Klassen entfallen seit 21.09.2026 (Spec Zoomfahrten): Stufe 2b trägt `brennweite_mm` und `zoom`.
```

**Ersetzen in `tools/autocut/README.md`:**

```text
Brennweiten- und Perspektivklasse; Abnehmer
```

**durch:**

```text
Brennweite in mm und Zoomfahrten, Perspektivklasse; Abnehmer
```

- [ ] **Step 6: Doku-Test und Commit**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_docs.py -q`
Expected: grün (nur `1 skipped`).

```bash
git add tools/autocut/src/niro_autocut/index_sections.py tools/autocut/src/niro_autocut/telemetrie.py \
  tools/autocut/scripts/autocut_index_sections.py tools/autocut/prompts/index-sections.md tools/autocut/defaults.yaml \
  tools/autocut/tests/test_index_sections.py tools/autocut/tests/test_telemetrie.py tools/autocut/WORKFLOW-AutoCut.md \
  tools/autocut/README.md
git commit -q -m "feat(autocut): Stufe 2b mit brennweite_mm und zoom je Abschnitt, Brennweitenklassen entfallen

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Feinschnitt 6d — Brennweitenregel, digitaler Zoom, Spalte 8 `zoom`

**Files:**
- Modify: `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py` (`BROLL`-Kommentar, V3-Schleife in `plan()`, `bericht()`, `bauen()` Zoom + Readback)
- Modify: `tools/autocut/WORKFLOW-AutoCut.md` (6d, Telemetrie-Abnehmer), `tools/autocut/vorlagen/README.md`
- Test: `tools/autocut/tests/test_vorlagen_telemetrie.py` (Probelauf-Tests der Planfunktion mit Telemetrie, Textprüfung Bau)

**Interfaces:**
- Consumes: `TM.kb_am`, `TM.zoom_hinweise`, `TM.brennweitenfolge`, `TM.OHNE_TELEMETRIE`, `TM.genutzter_quellbereich_s`
- Produces: `BROLL`-Eintrag `(shot, versatz, n, rec, beat, langsam[, stabil[, zoom]])`; `v3_meta[*]` zusätzlich `zoom`,
  `zoom_hinweis`, `zoom_hinweise`, `kb_anfang`, `kb_ende`; `feinschnitt.json` zusätzlich `zoom_gesetzt`
  (`{"S07": True, …}`) und `zoom_abweichungen` (`[{"shot", "soll", "ist"}]`)

- [ ] **Step 1: Failing Tests schreiben**

**Anhängen an `tools/autocut/tests/test_vorlagen_telemetrie.py`:**

```python
# --- Brennweitenregel und Zoomfahrten (Spec 2026-09-21) ------------------------------------------------------------------

def _zoom(von: float, bis: float, von_mm: float, bis_mm: float, tempo: float) -> dict:
    return {"von_s": von, "bis_s": bis, "von_mm": von_mm, "bis_mm": bis_mm, "tempo_max": tempo, "tempo_mittel": tempo,
            "ruck": 0.1, "ruckartig": False, "urteil": "schnell"}


# Clip A: 35 → 50 mm bei 0,4–0,9 s, 50 mm bis 2 s, dann Zoom auf 100 mm. Clip B: 24 → 52 mm bei 2,0–2,5 s, 52 mm bis
# 3,7 s, dann Zoom auf 70 mm (4,2 s). Beide 50p, gimbal.
TELE_A = {"path": "/ssd/FX3/FX3_A.MP4", "quelle": "rtmd", "haltung": "gimbal", "wackeln": 0.02, "fehler": None,
          "fenster": [[0.0, 0.02, 0.1, "statisch"]],
          "kb_verlauf": [[0.0, 35.0], [0.4, 35.0], [0.9, 50.0], [2.0, 50.0], [3.0, 100.0], [10.0, 100.0]],
          "zooms": [_zoom(0.4, 0.9, 35.0, 50.0, 72.4), _zoom(2.0, 3.0, 50.0, 100.0, 69.3)]}
TELE_B = {**TELE_A, "path": "/ssd/FX3/FX3_B.MP4",
          "kb_verlauf": [[0.0, 24.0], [2.0, 24.0], [2.5, 52.0], [3.7, 52.0], [4.2, 70.0], [10.0, 70.0]],
          "zooms": [_zoom(2.0, 2.5, 24.0, 52.0, 150.0), _zoom(3.7, 4.2, 52.0, 70.0, 59.4)]}
SHOTS = {1: {"nr": 1, "clip": "FX3_A", "datei": "/ssd/FX3/FX3_A.MP4", "clip_fps": 50.0, "left_offset_f": 0,
             "dauer_f": 100},
         2: {"nr": 2, "clip": "FX3_B", "datei": "/ssd/FX3/FX3_B.MP4", "clip_fps": 50.0, "left_offset_f": 50,
             "dauer_f": 100}}


def _fb_plan(monkeypatch, broll: list[tuple], tele: list[dict]):
    fb = _vorlage_laden(monkeypatch)
    monkeypatch.setattr(fb, "anpassen_pruefen", lambda fuer_bau=False: None)
    monkeypatch.setattr(fb, "ENDE", 80)
    monkeypatch.setattr(fb, "alpha_min", lambda: [255] * 80)
    monkeypatch.setattr(fb, "v4_stuecke", lambda fehler: [])
    monkeypatch.setattr(fb, "TELE", tele)
    monkeypatch.setattr(fb, "TCFG", {**fb.TCFG, "brennweite_gleich_max": 0.2, "digitalzoom_faktor": 1.25,
                                     "digitalzoom_max": 1.5})
    monkeypatch.setattr(fb, "BROLL", broll)
    p, fehler = fb.plan({"items": []}, SHOTS)
    return fb, p, fehler


def test_6d_plan_brennweitenregel_mit_50_prozent(monkeypatch, capsys):
    """S01 (100 %) Record 0–40: Quelle 0–80 Frames = 0–1,6 s → am Out 50 mm. S02 (50 %) Record 40–80 direkt danach:
    Quell-In (50 + 20) · 2 = 140 Frames = 2,8 s, 40 Timeline-Frames bei 50 % = 0,8 s Quelle → 2,8–3,6 s → am In
    52 mm. 50/52 mm = gleich → Zoom 1,25× auf S02 (längere Brennweite). Schneller Zoom 0,4–0,9 s liegt in S01;
    der von B bei 3,7–4,2 s liegt nur bei 100 % im genutzten Bereich, bei 50 % nicht."""
    fb, p, fehler = _fb_plan(monkeypatch, [(1, 0, 40, 0, "1", False), (2, 20, 40, 40, "1", True)], [TELE_A, TELE_B])
    assert fehler == []
    m1, m2 = p["v3_meta"]
    assert (m1["kb_ende"], m2["kb_anfang"]) == (50.0, 52.0) and (m1["zoom"], m2["zoom"]) == (1.0, 1.25)
    assert m1["zoom_hinweise"] == ["S01: schneller Zoom 0,4–0,9 s (35 → 50 mm, 72 %/s)"] and m2["zoom_hinweise"] == []
    assert m2["zoom_hinweis"] == "S02: 50 → 52 mm am Schnitt, Zoom 1,25× auf S02" and m1["zoom_hinweis"] is None
    fb.bericht(p)
    out = capsys.readouterr().out
    assert "Hinweis: S01: schneller Zoom 0,4–0,9 s (35 → 50 mm, 72 %/s)" in out
    assert "Hinweis: S02: 50 → 52 mm am Schnitt, Zoom 1,25× auf S02" in out
    assert "KB 52 → 52 mm  Zoom 1,25×" in out and "keine Telemetrie" not in out


def test_6d_plan_spalte_zoom_und_ohne_telemetrie(monkeypatch, capsys):
    _, p, fehler = _fb_plan(monkeypatch, [(1, 0, 40, 0, "1", False), (2, 20, 40, 40, "1", True, None, 1.0)],
                            [TELE_A, TELE_B])
    assert fehler == [] and [m["zoom"] for m in p["v3_meta"]] == [1.3, 1.0]     # S02 fest → A: 1,25 × 52 / 50
    _, p2, fehler2 = _fb_plan(monkeypatch, [(1, 0, 40, 0, "1", False), (2, 20, 40, 40, "1", True, None, 1.6)],
                              [TELE_A, TELE_B])
    assert "S02: Spalte zoom 1,6× außerhalb 1,0–1,5× (telemetrie.digitalzoom_max)" in fehler2
    fb, p3, fehler3 = _fb_plan(monkeypatch, [(1, 0, 40, 0, "1", False), (2, 20, 40, 40, "1", True)], [])
    assert fehler3 == [] and [m["zoom"] for m in p3["v3_meta"]] == [1.0, 1.0]
    fb.bericht(p3)
    assert "Hinweis: keine Telemetrie — Brennweitenregel nicht geprüft" in capsys.readouterr().out


def test_6d_vorlage_setzt_zoom_beim_bau():
    text = VORLAGE.read_text(encoding="utf-8")
    assert "TM.brennweitenfolge(folge, TCFG)" in text and "TM.kb_am(" in text and "TM.zoom_hinweise(" in text
    assert "tempo_faktor=0.5 if langsam else 1.0" in text      # Zeitlupe: sichtbares Tempo zählt
    assert 'RA._safe(x.SetProperty, False, k, float(m["zoom"]))' in text and 'for k in ("ZoomX", "ZoomY")' in text
    assert 'RA._safe(x.GetProperty, None, "ZoomX")' in text and 'out["zoom_abweichungen"]' in text
    assert "8. Spalte optional" in text
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_vorlagen_telemetrie.py -q`
Expected: `3 failed` (`KeyError: 'kb_ende'` bzw. `'zoom'` in den Planfunktions-Tests, Text fehlt in der Vorlage); die
übrigen bestehen.

- [ ] **Step 3: Vorlage ändern**

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py`:**

```python
# 7. Spalte optional: True/False erzwingt Stabilize() bzw. lässt es aus; weggelassen = Vorschlag aus telemetrie.json
# (hand und wackeln > telemetrie.ruhig_max_px → stabilisieren; stativ/gimbal → nicht; ohne Telemetrie → stabilisieren).
# True bei einer _stabilized-Datei (Avata-Export) ist ein Plan-Fehler: Avata nie in Resolve stabilisieren.
BROLL: list[tuple] = [
    # (10, 27, 54, 345, "4", True),          # Shot 10 ab Frame 27 seiner Auswahl, 54 Frames lang, Record 345, Beat #4, 50 %
    # (11, 0, 40, 400, "5", False, False),   # … und ausdrücklich nicht stabilisieren
]
```

**durch:**

```python
# 7. Spalte optional: True/False erzwingt Stabilize() bzw. lässt es aus; weggelassen oder None = Vorschlag aus
# telemetrie.json (hand und wackeln > telemetrie.ruhig_max_px → stabilisieren; stativ/gimbal → nicht; ohne Telemetrie →
# stabilisieren). True bei einer _stabilized-Datei (Avata-Export) ist ein Plan-Fehler: Avata nie in Resolve stabilisieren.
# 8. Spalte optional (Spec 2026-09-21): Zahl = digitaler Zoom des Shots fest (1.0 = keiner); weggelassen = Automatik der
# Brennweitenregel aus telemetrie.json — nie zweimal dieselbe KB-Brennweite direkt hintereinander (Abstand unter
# telemetrie.brennweite_gleich_max), sonst Zoom auf einen der beiden Shots (1,25×, Grenze telemetrie.digitalzoom_max).
# Ein Wert über der Grenze ist ein Plan-Fehler. Schnelle Zooms im genutzten Quellbereich meldet der Probelauf als Hinweis.
BROLL: list[tuple] = [
    # (10, 27, 54, 345, "4", True),          # Shot 10 ab Frame 27 seiner Auswahl, 54 Frames lang, Record 345, Beat #4, 50 %
    # (11, 0, 40, 400, "5", False, False),   # … und ausdrücklich nicht stabilisieren
    # (12, 0, 40, 440, "5", False, None, 1.0),   # … Stabilisieren nach Vorschlag, aber kein digitaler Zoom
]
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py`:**

```python
    v3, v3_meta = [], []
    for eintrag in sorted(BROLL, key=lambda x: x[3]):
        nr, off, n, rec, beat, langsam, *rest = eintrag
        stabil_hand = rest[0] if rest else None
```

**durch:**

```python
    v3, v3_meta, folge = [], [], []  # folge: Eingabe der Brennweitenregel (TM.brennweitenfolge)
    for eintrag in sorted(BROLL, key=lambda x: x[3]):
        nr, off, n, rec, beat, langsam, *rest = eintrag
        stabil_hand = rest[0] if rest else None
        zoom_hand = rest[1] if len(rest) > 1 else None  # 8. Spalte: erzwungener Zoom, None = Automatik
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py`:**

```python
                        "roll_grad": (tele_rec or {}).get("roll_grad")})
    for a, b in zip(v3, v3[1:]):
```

**durch:**

```python
                        "roll_grad": (tele_rec or {}).get("roll_grad"),
                        "zoom_hinweise": TM.zoom_hinweise(f"S{nr:02d}", tele_rec, *bereich, cfg=TCFG,
                                                          tempo_faktor=0.5 if langsam else 1.0)})
        # Brennweite am Schnitt: Ende des genutzten Quellbereichs (bei 50 % halb so lang) bzw. sein Anfang
        folge.append({"id": f"S{nr:02d}", "rec_in": rec, "rec_out": rec + n, "zoom_erzwungen": zoom_hand,
                      "kb_anfang": TM.kb_am(tele_rec, bereich[0], seite="anfang"),
                      "kb_ende": TM.kb_am(tele_rec, bereich[1], seite="ende")})
    # Brennweitenregel (Spec 2026-09-21): nie zweimal dieselbe KB-Brennweite direkt hintereinander, sonst digitaler Zoom
    for m, f, z in zip(v3_meta, folge, TM.brennweitenfolge(folge, TCFG)):
        m.update(zoom=z["zoom"], zoom_hinweis=z["hinweis"], kb_anfang=f["kb_anfang"], kb_ende=f["kb_ende"])
        if z["fehler"]:
            fehler.append(z["fehler"])
    for a, b in zip(v3, v3[1:]):
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py`:**

```python
    print(f"Stabilisierung ({len(TELE)} Clips in telemetrie.json):")
    for m in p["v3_meta"]:
        roll = m.get("roll_grad")
        schief = f"  schief {abs(roll):.1f}°".replace(".", ",") if roll is not None and abs(roll) > 2.0 else ""
        print(f"  S{m['shot']:02d} {'stabilisieren' if m['stabil'] else 'lassen       '}  {m['stabil_grund']}{schief}")
```

**durch:**

```python
    print(f"Stabilisierung, Brennweite und Zoom ({len(TELE)} Clips in telemetrie.json):")
    for m in p["v3_meta"]:
        roll = m.get("roll_grad")
        schief = f"  schief {abs(roll):.1f}°".replace(".", ",") if roll is not None and abs(roll) > 2.0 else ""
        kb = "KB –" if m.get("kb_anfang") is None else f"KB {m['kb_anfang']:g} → {m['kb_ende']:g} mm".replace(".", ",")
        zoom = f"  Zoom {m['zoom']:g}×".replace(".", ",") if m.get("zoom", 1.0) != 1.0 else ""
        print(f"  S{m['shot']:02d} {'stabilisieren' if m['stabil'] else 'lassen       '}  {m['stabil_grund']}{schief}"
              f"  {kb}{zoom}")
    hinweise = [] if TELE else [TM.OHNE_TELEMETRIE]
    for m in p["v3_meta"]:
        hinweise += m.get("zoom_hinweise", []) + ([m["zoom_hinweis"]] if m.get("zoom_hinweis") else [])
    for h in hinweise:
        print(f"  Hinweis: {h}")
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py`:**

```python
        out["stabilisiert"] = stab
```

**durch:**

```python
        out["stabilisiert"] = stab
        # Digitaler Zoom der Brennweitenregel (Spec 2026-09-21): auf die Bildmitte, Pan/Tilt bleiben 0
        zoom_ok = {}
        for m in p["v3_meta"]:
            if m["zoom"] == 1.0:
                continue
            x = v3_items[m["rec_in_f"]]
            gesetzt = [bool(RA._safe(x.SetProperty, False, k, float(m["zoom"]))) for k in ("ZoomX", "ZoomY")]
            zoom_ok[f"S{m['shot']:02d}"] = all(gesetzt)
        out["zoom_gesetzt"] = zoom_ok
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py`:**

```python
    out["v3"] = v3_rb
    ausserhalb = []
```

**durch:**

```python
    out["v3"] = v3_rb
    # Readback Zoom (Spec 2026-09-21): ZoomX je V3-Item gegen den Plan (1.0 = kein digitaler Zoom)
    v3_zoom = [RA._safe(x.GetProperty, None, "ZoomX")
               for x in sorted(tl.GetItemListInTrack("video", 3) or [], key=lambda y: y.GetStart())]
    out["zoom_abweichungen"] = [{"shot": m["shot"], "soll": m["zoom"], "ist": z}
                                for m, z in zip(sorted(p["v3_meta"], key=lambda v: v["rec_in_f"]), v3_zoom)
                                if z is None or abs(float(z) - m["zoom"]) > 1e-3]
    ausserhalb = []
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_vorlagen_telemetrie.py -q && venv/bin/python -m pytest -q`
Expected: alle bestehen; Gesamtlauf grün.

- [ ] **Step 5: Doku**

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
- `BROLL` (aus `broll_einsatz.json`; 50 % nur bei Händen, Details und Kamerafahrten, nie bei Sprechenden, nur aus
  50p-Quellen)
```

**durch:**

```text
- `BROLL` (aus `broll_einsatz.json`; 50 % nur bei Händen, Details und Kamerafahrten, nie bei Sprechenden, nur aus
  50p-Quellen; optional Spalte 7 `stabil` und Spalte 8 `zoom`)
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
   - Ziel: **0 Frames ohne Bild und ohne deckende Grafik** (Taxodia vorher 51).
```

**durch:**

```text
   - Ziel: **0 Frames ohne Bild und ohne deckende Grafik** (Taxodia vorher 51).
   - Brennweite (Spec 2026-09-21, `telemetrie.json`): je Shot die KB-Brennweite am Quell-In/-Out des genutzten Bereichs
     (bei 50 % halb so lang) und der digitale Zoom der Brennweitenregel; Hinweise für schnelle Zooms im genutzten Bereich,
     gesetzte Zooms („S12: 50 → 52 mm am Schnitt, Zoom 1,25× auf S12") und nicht mögliche; ohne Telemetrie „keine
     Telemetrie — Brennweitenregel nicht geprüft". Spalte 8 über `digitalzoom_max` ist ein Fehler.
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
     Werkzeug) — `Stabilize()` allein nimmt Perspective.
```

**durch:**

```text
     Werkzeug) — `Stabilize()` allein nimmt Perspective. Danach der digitale Zoom der Brennweitenregel (`SetProperty`
     `ZoomX`/`ZoomY`, Bildmitte); Readback `zoom_gesetzt` und `zoom_abweichungen` in `feinschnitt.json`.
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
und 6d (Stabilisieren nur bei Bedarf).
```

**durch:**

```text
und 6d (Stabilisieren nur bei Bedarf, Brennweitenregel).
```

**Ersetzen in `tools/autocut/vorlagen/README.md`:**

```text
  stabilisiert. Der Probelauf druckt je Shot Vorschlag und Grund; `roll_grad` > 2° erscheint als „schief".
```

**durch:**

```text
  stabilisiert. Der Probelauf druckt je Shot Vorschlag und Grund; `roll_grad` > 2° erscheint als „schief".
  Die optionale 8. Spalte `zoom` legt den digitalen Zoom fest (1.0 = keiner); ohne sie setzt die Brennweitenregel aus
  `telemetrie.json` einen Zoom, wenn zwei direkt anschließende Shots dieselbe KB-Brennweite hätten (Spec 2026-09-21).
```

- [ ] **Step 6: Doku-Test und Commit**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_docs.py tests/test_vorlagen_telemetrie.py -q`
Expected: grün (nur `1 skipped`).

```bash
git add tools/autocut/vorlagen/feinschnitt/feinschnitt_bauen.py tools/autocut/tests/test_vorlagen_telemetrie.py \
  tools/autocut/WORKFLOW-AutoCut.md tools/autocut/vorlagen/README.md
git commit -q -m "feat(autocut): 6d-Vorlage mit Brennweitenregel — digitaler Zoom (BROLL-Spalte 8 zoom), Hinweise, Readback

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: B-Roll aus Auswahl 3a — Brennweitenregel, digitaler Zoom, Spalte 7 `zoom`

**Files:**
- Modify: `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py` (Docstring, Imports, `TELE`/`TCFG`, `PLAN`-Kommentar, `pruefen`, `bericht`, `bauen`)
- Modify: `tools/autocut/WORKFLOW-AutoCut.md` (3a, Kopf-Tabelle, Telemetrie-Abnehmer), `tools/autocut/vorlagen/README.md`, `tools/autocut/README.md`
- Test: `tools/autocut/tests/test_vorlagen_telemetrie.py` (Docstring, `VORLAGE_3A`, drei Tests)

**Interfaces:**
- Consumes: wie Task 7; Testdaten `TELE_A`, `TELE_B`, `SHOTS` aus Task 7
- Produces: `PLAN`-Eintrag `(shot, versatz, n, rec, beat, inhalt[, zoom])`; `zeilen[*]` zusätzlich `zoom`,
  `zoom_hinweis`, `zoom_hinweise`; Modulkonstanten `TELE`, `TCFG`; `broll_einsatz.json` zusätzlich `zoom_gesetzt`,
  `zoom_abweichungen` (Shot-Nummern)

- [ ] **Step 1: Failing Tests schreiben**

**Ersetzen in `tools/autocut/tests/test_vorlagen_telemetrie.py`:**

```python
"""6d-Vorlage: kompiliert, nutzt stabil_vorschlag, dokumentiert die 7. BROLL-Spalte, Stabilize nur für ausgewählte Shots."""
```

**durch:**

```python
"""Vorlagen 6d und 3a: kompilieren, nutzen die Telemetrie-Helfer (stabil_vorschlag, Brennweitenregel), Spalten stabil/zoom,
Stabilize und Zoom nur für ausgewählte Shots; Planfunktionen mit Telemetrie-Datensätzen ohne Resolve."""
```

**Ersetzen in `tools/autocut/tests/test_vorlagen_telemetrie.py`:**

```python
VORLAGE = Path(__file__).resolve().parents[1] / "vorlagen" / "feinschnitt" / "feinschnitt_bauen.py"
```

**durch:**

```python
VORLAGE = Path(__file__).resolve().parents[1] / "vorlagen" / "feinschnitt" / "feinschnitt_bauen.py"
VORLAGE_3A = VORLAGE.with_name("broll_einsetzen.py")
```

**Anhängen an `tools/autocut/tests/test_vorlagen_telemetrie.py`:**

```python
def _3a_pruefen(monkeypatch, plan: list[tuple], tele: list[dict]):
    spec = importlib.util.spec_from_file_location("broll_einsetzen_vorlage", VORLAGE_3A)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "TELE", tele)
    monkeypatch.setattr(mod, "TCFG", {**mod.TCFG, "brennweite_gleich_max": 0.2, "digitalzoom_faktor": 1.25,
                                      "digitalzoom_max": 1.5})
    monkeypatch.setattr(mod, "PLAN", plan)
    tl = {"items": [{"rec_out_f": 200}], "beats": [{"nr": "1"}]}
    zeilen, fehler = mod.pruefen(SHOTS, tl)
    return mod, tl, zeilen, fehler


def test_3a_pruefen_brennweitenregel_bei_100_prozent(monkeypatch, capsys):
    """Wie 6d, aber Tempo 100 %: S02 nutzt die Quelle 2,8–4,4 s (140 + 80 Frames bei 50p) — dort liegt der schnelle
    Zoom 3,7–4,2 s von B (Hinweis). Am Schnitt 50/52 mm → Zoom 1,25× auf S02."""
    mod, tl, zeilen, fehler = _3a_pruefen(monkeypatch, [(1, 0, 40, 0, "1", "A"), (2, 20, 40, 40, "1", "B")],
                                          [TELE_A, TELE_B])
    assert fehler == [] and [z["zoom"] for z in zeilen] == [1.0, 1.25]
    assert zeilen[0]["zoom_hinweise"] == ["S01: schneller Zoom 0,4–0,9 s (35 → 50 mm, 72 %/s)"]
    assert zeilen[1]["zoom_hinweise"] == ["S02: schneller Zoom 3,7–4,2 s (52 → 70 mm, 59 %/s)"]
    assert zeilen[1]["zoom_hinweis"] == "S02: 50 → 52 mm am Schnitt, Zoom 1,25× auf S02"
    mod.bericht(zeilen, tl)
    out = capsys.readouterr().out
    assert "Zoom 1,25×" in out and "Hinweis: S02: schneller Zoom 3,7–4,2 s (52 → 70 mm, 59 %/s)" in out


def test_3a_pruefen_spalte_zoom_und_ohne_telemetrie(monkeypatch, capsys):
    _, _, zeilen, fehler = _3a_pruefen(monkeypatch, [(1, 0, 40, 0, "1", "A"), (2, 20, 40, 40, "1", "B", 1.0)],
                                       [TELE_A, TELE_B])
    assert fehler == [] and [z["zoom"] for z in zeilen] == [1.3, 1.0]
    _, _, _, fehler2 = _3a_pruefen(monkeypatch, [(1, 0, 40, 0, "1", "A", 1.6), (2, 20, 40, 40, "1", "B")],
                                   [TELE_A, TELE_B])
    assert fehler2 == ["S01: Spalte zoom 1,6× außerhalb 1,0–1,5× (telemetrie.digitalzoom_max)"]
    mod, tl, zeilen3, fehler3 = _3a_pruefen(monkeypatch, [(1, 0, 40, 0, "1", "A"), (2, 20, 40, 40, "1", "B")], [])
    assert fehler3 == [] and [z["zoom"] for z in zeilen3] == [1.0, 1.0]
    mod.bericht(zeilen3, tl)
    assert "Hinweis: keine Telemetrie — Brennweitenregel nicht geprüft" in capsys.readouterr().out


def test_3a_vorlage_setzt_zoom_beim_bau():
    py_compile.compile(str(VORLAGE_3A), doraise=True)
    text = VORLAGE_3A.read_text(encoding="utf-8")
    assert "TM.brennweitenfolge(folge, TCFG)" in text and "TM.genutzter_quellbereich_s(" in text
    assert 'SetProperty, False, k, float(z["zoom"]))' in text and 'for k in ("ZoomX", "ZoomY")' in text
    assert 'RA._safe(it.GetProperty, None, "ZoomX")' in text and '"zoom_abweichungen": zoom_abweichungen' in text
```

- [ ] **Step 2: Tests laufen lassen — Fehlschlag erwartet**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_vorlagen_telemetrie.py -q`
Expected: `3 failed` (`AttributeError: module 'broll_einsetzen_vorlage' has no attribute 'TELE'` in den beiden
Planfunktions-Tests, fehlender Text im dritten); die 6d-Tests bestehen.

- [ ] **Step 3: Vorlage ändern**

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
Prüfung (Probelauf): Versatz + Länge innerhalb der Auswahl, keine Überlappung, nicht über das Timeline-Ende, Beat bekannt,
jeder Shot höchstens einmal — bei Fehlern Exit 1, nichts geschrieben.
```

**durch:**

```python
Prüfung (Probelauf): Versatz + Länge innerhalb der Auswahl, keine Überlappung, nicht über das Timeline-Ende, Beat bekannt,
jeder Shot höchstens einmal — bei Fehlern Exit 1, nichts geschrieben.
Brennweite (Spec 2026-09-21, _intern/autocut/telemetrie.json): nie zweimal dieselbe KB-Brennweite direkt hintereinander,
sonst digitaler Zoom auf einen der beiden Shots (gesetzt beim Bau); schnelle Zooms im genutzten Bereich = Hinweis.
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item, MarkerSpec  # noqa: E402

CH = Path(__file__).resolve().parent.parent
AC = CH / "_intern" / "autocut"
```

**durch:**

```python
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut import telemetrie as TM  # noqa: E402
from niro_autocut.charge import load_config  # noqa: E402
from niro_autocut.timeline_model import Item, MarkerSpec  # noqa: E402

CH = Path(__file__).resolve().parent.parent
AC = CH / "_intern" / "autocut"
TELE = TM.laden(AC)  # _intern/autocut/telemetrie.json (autocut_telemetrie.py); leer = Brennweitenregel nicht geprüft
TCFG = load_config(CH)["telemetrie"]
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
# (Shot-Nr aus der Auswahl, Versatz im Shot [Frames], Länge [Frames], Record-In [Frames], Beat, Inhalt)
PLAN = [  # Frames = Timeline-Frames; Versatz + Länge ≤ Dauer des Shots in der Auswahl; Beat = nr aus timeline.json
    # (10, 0, 54, 345, "4", "Person A geht zur Tür (Motiv laut Standbild)"),
]
```

**durch:**

```python
# (Shot-Nr aus der Auswahl, Versatz im Shot [Frames], Länge [Frames], Record-In [Frames], Beat, Inhalt[, zoom])
# 7. Spalte optional: Zahl = digitaler Zoom des Shots fest (1.0 = keiner); weggelassen = Automatik der Brennweitenregel
# (telemetrie.brennweite_gleich_max, digitalzoom_faktor, digitalzoom_max); über digitalzoom_max = Plan-Fehler.
PLAN = [  # Frames = Timeline-Frames; Versatz + Länge ≤ Dauer des Shots in der Auswahl; Beat = nr aus timeline.json
    # (10, 0, 54, 345, "4", "Person A geht zur Tür (Motiv laut Standbild)"),
    # (11, 0, 40, 399, "4", "Detail Hände", 1.0),   # … ohne digitalen Zoom, auch wenn die Brennweite gleich ist
]
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
    prev = None
    for nr, off, n, rec, beat, inhalt in sorted(PLAN, key=lambda p: p[3]):
        s = shots[nr]
```

**durch:**

```python
    prev, folge = None, []  # folge: Eingabe der Brennweitenregel (TM.brennweitenfolge)
    for nr, off, n, rec, beat, inhalt, *rest in sorted(PLAN, key=lambda p: p[3]):
        s = shots[nr]
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
                       "auswahl_f": [s["left_offset_f"], s["left_offset_f"] + s["dauer_f"]]})
        prev = rec + n
    return zeilen, fehler
```

**durch:**

```python
                       "auswahl_f": [s["left_offset_f"], s["left_offset_f"] + s["dauer_f"]]})
        # genutzter Quellbereich in s (Tempo 100 %) → Brennweite am Schnitt und schnelle Zooms
        tele_rec = TM.finden(TELE, s["datei"])
        bereich = TM.genutzter_quellbereich_s(zeilen[-1]["src_in_f"], n, s["clip_fps"], False, FPS)
        zeilen[-1]["zoom_hinweise"] = TM.zoom_hinweise(f"S{nr:02d}", tele_rec, *bereich)
        folge.append({"id": f"S{nr:02d}", "rec_in": rec, "rec_out": rec + n, "zoom_erzwungen": rest[0] if rest else None,
                      "kb_anfang": TM.kb_am(tele_rec, bereich[0], seite="anfang"),
                      "kb_ende": TM.kb_am(tele_rec, bereich[1], seite="ende")})
        prev = rec + n
    for z, e in zip(zeilen, TM.brennweitenfolge(folge, TCFG)):
        z["zoom"], z["zoom_hinweis"] = e["zoom"], e["hinweis"]
        if e["fehler"]:
            fehler.append(e["fehler"])
    return zeilen, fehler
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
              f"{z['left_offset_f'] / FPS:7.2f}–{(z['left_offset_f'] + z['dauer_f']) / FPS:7.2f}s  {z['inhalt']}")
```

**durch:**

```python
              f"{z['left_offset_f'] / FPS:7.2f}–{(z['left_offset_f'] + z['dauer_f']) / FPS:7.2f}s  {z['inhalt']}"
              + (f"  Zoom {z['zoom']:g}×".replace(".", ",") if z.get("zoom", 1.0) != 1.0 else ""))
    hinweise = [] if TELE else [TM.OHNE_TELEMETRIE]
    for z in zeilen:
        hinweise += z.get("zoom_hinweise", []) + ([z["zoom_hinweis"]] if z.get("zoom_hinweis") else [])
    for h in hinweise:
        print(f"  Hinweis: {h}")
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
    user_folder = mp.GetCurrentFolder()
    start = int(ziel.GetStartFrame())
    try:
```

**durch:**

```python
    user_folder = mp.GetCurrentFolder()
    start = int(ziel.GetStartFrame())
    zoom_gesetzt: dict[str, bool] = {}
    try:
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
        session.append_items(ziel, items, media, start)
        by_shot = {z["shot"]: z for z in zeilen}
```

**durch:**

```python
        session.append_items(ziel, items, media, start)
        # Digitaler Zoom der Brennweitenregel (Spec 2026-09-21): auf die Bildmitte, Pan/Tilt bleiben 0
        v3 = {int(x.GetStart()) - start: x for x in (ziel.GetItemListInTrack("video", 3) or [])}
        for z in zeilen:
            if z["zoom"] != 1.0 and z["rec_in_f"] in v3:
                gesetzt = [bool(RA._safe(v3[z["rec_in_f"]].SetProperty, False, k, float(z["zoom"])))
                           for k in ("ZoomX", "ZoomY")]
                zoom_gesetzt[f"S{z['shot']:02d}"] = all(gesetzt)
        by_shot = {z["shot"]: z for z in zeilen}
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
                    "left_offset_f": int(it.GetLeftOffset())})
```

**durch:**

```python
                    "left_offset_f": int(it.GetLeftOffset()), "zoom": RA._safe(it.GetProperty, None, "ZoomX")})
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
    ausserhalb = [z for z in zeilen if not (z["auswahl_f"][0] <= z["left_offset_f"]
```

**durch:**

```python
    zoom_ist = {i["rec_in_f"]: i["zoom"] for i in ist}
    zoom_abweichungen = [z["shot"] for z in zeilen if zoom_ist.get(z["rec_in_f"]) is None
                         or abs(float(zoom_ist[z["rec_in_f"]]) - z["zoom"]) > 1e-3]
    ausserhalb = [z for z in zeilen if not (z["auswahl_f"][0] <= z["left_offset_f"]
```

**Ersetzen in `tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py`:**

```python
        "gespeichert": gespeichert, "warnungen": session.warnings, "plan": zeilen, "readback": ist,
```

**durch:**

```python
        "gespeichert": gespeichert, "warnungen": session.warnings, "plan": zeilen, "readback": ist,
        "zoom_gesetzt": zoom_gesetzt, "zoom_abweichungen": zoom_abweichungen,
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_vorlagen_telemetrie.py -q && venv/bin/python -m pytest -q`
Expected: alle bestehen; Gesamtlauf grün.

- [ ] **Step 5: Doku**

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
   Versatz im Shot, Länge, Record-In (Frames), Beat, Inhalt. Regeln:
```

**durch:**

```text
   Versatz im Shot, Länge, Record-In (Frames), Beat, Inhalt, optional Zoom (7. Spalte). Regeln:
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
   - Kein Einstellungs-Doppel in Folge.
```

**durch:**

```text
   - Kein Einstellungs-Doppel in Folge und nie zweimal dieselbe KB-Brennweite direkt hintereinander (unter 20 %
     Abstand, `telemetrie.json`) — gibt das Material nichts anderes her, setzt der Bau einen digitalen Zoom (1,25×,
     höchstens 1,5×; Spalte 7 `zoom` legt ihn fest, 1.0 = keiner).
   - Schnelle Zoomfahrten meiden; langsame, gleichmäßige Zooms wie die Drehteller-Closeups (Wurst & Liebe) passen.
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
   gibt die Tabelle aus. Die Frame-Umrechnung ist für 50p-Clips in 25p gemessen; andere Bildraten vorher prüfen.
```

**durch:**

```text
   gibt die Tabelle aus. Die Frame-Umrechnung ist für 50p-Clips in 25p gemessen; andere Bildraten vorher prüfen.
   Mit `telemetrie.json` zeigt er je Shot den digitalen Zoom und Hinweise (schneller Zoom im genutzten Bereich,
   gesetzter Zoom, Zoom nicht möglich), ohne sie „keine Telemetrie — Brennweitenregel nicht geprüft".
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
   - V3 der roh-Timeline (muss leer sein) in einem Append, dazu Marker.
```

**durch:**

```text
   - V3 der roh-Timeline (muss leer sein) in einem Append, dazu Marker. Shots mit digitalem Zoom bekommen
     `ZoomX`/`ZoomY` (Readback `zoom_gesetzt`, `zoom_abweichungen` in `broll_einsatz.json`).
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
Grundlage für Sichtung, 2b, 6d |
```

**durch:**

```text
Grundlage für Sichtung, 2b, 3a, 6d |
```

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
je Abschnitt) und 6d (
```

**durch:**

```text
je Abschnitt), 3a (Brennweitenregel) und 6d (
```

**Ersetzen in `tools/autocut/vorlagen/README.md`:**

```text
Marker, Readback (3a) |
```

**durch:**

```text
Marker, Brennweitenregel mit digitalem Zoom (7. Spalte `zoom`), Readback (3a) |
```

**Ersetzen in `tools/autocut/README.md`:**

```text
Abnehmer Sichtung/Aftermovie, Stufe 2b, 6d |
```

**durch:**

```text
Abnehmer Sichtung/Aftermovie, Stufe 2b, 3a, 6d |
```

- [ ] **Step 6: Doku-Test und Commit**

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_docs.py tests/test_vorlagen_telemetrie.py -q`
Expected: grün (nur `1 skipped`).

```bash
git add tools/autocut/vorlagen/feinschnitt/broll_einsetzen.py tools/autocut/tests/test_vorlagen_telemetrie.py \
  tools/autocut/WORKFLOW-AutoCut.md tools/autocut/vorlagen/README.md tools/autocut/README.md
git commit -q -m "feat(autocut): 3a-Vorlage mit Brennweitenregel — digitaler Zoom (PLAN-Spalte 7 zoom), Hinweise, Readback

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Kalibrierung Teil 1 — Messläufe W&L und MEK, Beispielvideo in NIRO Review (Controller, NAS) — endet mit STOP

Diese Task führt der Controller selbst aus (kein Subagent): NAS gemountet, Code aus dem Worktree, Chargen im Hauptordner.
Rechenzeit ≈ 45 min (Lesen der Datenspur ≈ 300 MB/s übers NAS; Läufe im Hintergrund). Sie schreibt in drei Chargen
(`_intern/autocut/**`, `Ergebnisse/Rohschnitt/telemetrie.md`, `Protokoll.md`) und legt die Kalibrier-Charge an. Nichts in
Resolve, kein Commit (keine Werkzeug-Datei ändert sich). Vorab-Stichprobe aus der Planung (Prototyp dieses Codes auf
`Beef Burger`/`Kaiserschmarrn`): Drehteller-Zooms a7MK4_20260805_0085 7,2–11,0 s (110 → 284 mm) Spitze ≈ 35 %/s, ruck
0,13; 0098 42,0–46,3 s Spitze ≈ 32 %/s; die Rück-Zooms dazwischen 100–190 %/s. Der Startwert 20 %/s liegt also unter den
Drehteller-Zooms; die Kalibrierung hebt ihn voraussichtlich an. Der erste Zoom von 0085 (1,6–4,1 s) fällt mit |v| auf 19 %
der Spitze ab (Stocken) — deshalb ist `zoom_stocken_anteil` ein Schlüssel.

**Files:**
- Create (Charge, nicht im Repo): `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten/Protokoll.md`,
  `…/_intern/skripte/zoom_beispiele.py`; erzeugt `…/_intern/beispiele.json`, `…/_intern/work/zoom-beispiele.mp4`
  (+ `seg_*.mp4`, `nr_*.png`, `concat.txt`)
- Modify (durch die CLI): Wurst & Liebe `projects/Wurst & Liebe/Social-Reels/2026-08 Dreh 05.08/` und MEK
  `projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/`: `_intern/autocut/telemetrie.json`,
  `_intern/autocut/telemetrie/`, `Ergebnisse/Rohschnitt/telemetrie.md`, `Protokoll.md`

**Interfaces:**
- Consumes: Tasks 1–8 (Worktree-Code: `autocut_telemetrie.py`, Zoom-Datensätze), `tools/review/review.py hinzufuegen`
- Produces: `beispiele.json` = Liste je Beispiel (sortiert nach `nr`): alle Felder der Zoomfahrt plus `charge`, `path`,
  `clip`, `ordner`, `kamera`, `fps`, `dauer_s`, `zoom_nr`, `drehteller`, `grund`, `nr`, `quelle_start_s`,
  `video_von_s`, `video_bis_s`; Review „Zoom-Beispiele" V1 (`http://localhost:4711/#/NIRO/Werkzeug-Kalibrierung`)

- [ ] **Step 1: NAS prüfen, Chargen abgleichen**

```bash
MAIN="/Users/jansantos/NIRO Studio"
NAS_WL="/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/Wurst & Liebe GmbH/02_Projekte"
ls "$NAS_WL/01_Projekt-Reel Dreh 01/03_Medien/01_Footage/Sortiert/00 - B-Roll" | head -3
cd "$MAIN" && sh tools/studio_abgleich.sh --charge "projects/Wurst & Liebe/Social-Reels/2026-08 Dreh 05.08" \
  && sh tools/studio_abgleich.sh --charge "projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh"
```

Expected: drei Motiv-Ordner (z. B. `Antipastiplatte`, `Beef Burger`, `Bestellterminal`); Abgleich ohne Fehler.

- [ ] **Step 2: Telemetrie Wurst & Liebe (B-Roll, nur rtmd) — im Hintergrund**

```bash
MAIN="/Users/jansantos/NIRO Studio"; WT="$MAIN/.claude/worktrees/autocut-zoom-brennweite"
NAS_WL="/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/Wurst & Liebe GmbH/02_Projekte"
BROLL="$NAS_WL/01_Projekt-Reel Dreh 01/03_Medien/01_Footage/Sortiert/00 - B-Roll"
cd "$MAIN" && "$WT/tools/autocut/venv/bin/python" "$WT/tools/autocut/scripts/autocut_telemetrie.py" \
  "$MAIN/projects/Wurst & Liebe/Social-Reels/2026-08 Dreh 05.08" --ordner "$BROLL" --ohne-optisch --parallel 2 \
  < /dev/null 2>&1 | tail -4
```

Expected: `Telemetrie: … Clips (… gemessen, 0 Cache-Treffer, … Fehler …)`. `--ohne-optisch`: Zoomfahrten brauchen nur die
rtmd-Brennweite (FX3-Clips ohne Gyro erscheinen als `quelle: keine`, tragen aber `kb_verlauf`/`zooms`). Exit 1 = einzelne
Clips mit Fehler — Liste ansehen, der Lauf ist trotzdem vollständig.

- [ ] **Step 3: Telemetrie MEK (463 B-Roll-Clips aus `broll_index.json`) — im Hintergrund**

```bash
MAIN="/Users/jansantos/NIRO Studio"; WT="$MAIN/.claude/worktrees/autocut-zoom-brennweite"
cd "$MAIN" && "$WT/tools/autocut/venv/bin/python" "$WT/tools/autocut/scripts/autocut_telemetrie.py" \
  "$MAIN/projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh" --parallel 2 < /dev/null 2>&1 | tail -4
```

Expected: `Telemetrie: 463 Clips (463 gemessen, 0 Cache-Treffer, …)` — der Config-Hash hat sich geändert, jeder Clip wird
einmal neu gemessen.

- [ ] **Step 4: Kalibrier-Charge anlegen, Beispiel-Skript schreiben**

```bash
mkdir -p "/Users/jansantos/NIRO Studio/projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten/_intern/skripte"
```

**Neue Datei `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten/_intern/skripte/zoom_beispiele.py`** (im Hauptordner):

```python
"""Kalibrierung Zoomfahrten (Spec 2026-09-21, Abschnitt 4), Einmal-Skript der Kalibrier-Charge, nicht Teil des Werkzeugs.

Liest die Zoomfahrten aus den Telemetrie-Läufen von Wurst & Liebe und MEK (``telemetrie.json``), wählt 8–10 Grenzfälle
um die vorläufigen Schwellen plus zwei Drehteller-Zooms (Referenz „ok") und rendert sie als ein Beispielvideo
(1920×1080, 25 fps, H.264, Limited Range, Nummer oben links). Quellen nur lesend (NAS).

Aufruf aus der Studio-Wurzel mit dem AutoCut-venv (Pillow):
    tools/autocut/venv/bin/python "<Charge>/_intern/skripte/zoom_beispiele.py" --liste     → Übersicht, schreibt nichts
    tools/autocut/venv/bin/python "<Charge>/_intern/skripte/zoom_beispiele.py" --rendern   → _intern/beispiele.json,
                                                                                           _intern/work/zoom-beispiele.mp4
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HIER = Path(__file__).resolve()
CHARGE = HIER.parents[2]
PROJECTS = HIER.parents[5]
QUELLEN = {"W&L": PROJECTS / "Wurst & Liebe/Social-Reels/2026-08 Dreh 05.08/_intern/autocut/telemetrie.json",
           "MEK": (PROJECTS / "Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/autocut"
                   / "telemetrie.json")}
LUT = PROJECTS / "Wurst & Liebe/Social-Reels/2026-08 Dreh 05.08/_intern/reels/lut/slog3_lc709a.cube"
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
# Drehteller-Closeups von W&L (Reel-Pläne _intern/reels/specs*.py, montage_waehlen.py): (Ordner, Clip)
DREHTELLER = {("Beef Burger", "a7MK4_20260805_0085"), ("Beef Burger", "a7MK4_20260805_0087"),
              ("Kaiserschmarrn", "a7MK4_20260805_0697"), ("Kaiserschmarrn", "a7MK4_20260805_0698"),
              ("Kaiserschmarrn", "a7MK4_20260805_0699"), ("Kaiserschmarrn", "a7MK4_20260805_0700"),
              ("Kaiserschmarrn", "a7MK4_20260805_0098"), ("Falaffel", "a7MK4_20260805_0090"),
              ("Currywurst mit Pommes", "FX3_0754"), ("Pizza", "a7MK4_20260805_0080")}
ZIEL_TEMPO = [15, 20, 25, 30, 40, 55]   # % pro s: um den Startwert 20 und die Drehteller-Zooms (Stichprobe ≈ 35)
W, H, FPS = 1920, 1080, 25


def fahrten() -> list[dict]:
    """Alle Zoomfahrten beider Chargen mit Clip-Angaben; Drehteller markiert."""
    out = []
    for charge, pfad in QUELLEN.items():
        if not pfad.exists():
            raise SystemExit(f"{pfad} fehlt — erst autocut_telemetrie.py für {charge} laufen lassen.")
        for r in json.loads(pfad.read_text(encoding="utf-8")):
            for i, z in enumerate(r.get("zooms") or []):
                out.append({"charge": charge, "path": r["path"], "clip": r["clip"], "ordner": r.get("ordner") or "",
                            "kamera": r.get("kamera"), "fps": r.get("fps"), "dauer_s": r.get("dauer_s"), "zoom_nr": i, **z,
                            "drehteller": (Path(r.get("ordner") or "").name, r["clip"]) in DREHTELLER})
    return out


def auswahl(alle: list[dict]) -> list[dict]:
    """2 langsamste Drehteller-Zooms (≥ 1 s), 2 ruckartige unter 30 %/s, je Zieltempo die nächste gleichmäßige Fahrt;
    jeder Clip höchstens einmal. Reihenfolge gemischt (Seed 21), damit das Tempo nicht mit der Nummer steigt."""
    gewaehlt: list[dict] = []
    # nur Fahrten, die man beurteilen kann: mindestens 0,5 s und 10 % Brennweitenänderung zwischen Anfang und Ende
    alle = [f for f in alle if f["bis_s"] - f["von_s"] >= 0.5
            and max(f["von_mm"], f["bis_mm"]) / min(f["von_mm"], f["bis_mm"]) >= 1.10]

    def nimm(kandidaten: list[dict], grund: str, anzahl: int) -> None:
        for f in kandidaten:
            if anzahl and f["path"] not in {g["path"] for g in gewaehlt}:
                gewaehlt.append({**f, "grund": grund})
                anzahl -= 1

    dreh = [f for f in alle if f["drehteller"] and f["bis_s"] - f["von_s"] >= 1.0]
    nimm(sorted(dreh, key=lambda f: f["tempo_max"]), "Drehteller (Referenz ok)", 2)
    ruck = [f for f in alle if not f["drehteller"] and f["ruckartig"] and f["tempo_max"] <= 30.0]
    nimm(sorted(ruck, key=lambda f: -f["ruck"]), "ruckartig unter 30 %/s", 2)
    glatt = [f for f in alle if not f["drehteller"] and not f["ruckartig"]]
    for ziel in ZIEL_TEMPO:
        nimm(sorted(glatt, key=lambda f: abs(f["tempo_max"] - ziel)), f"Tempo um {ziel} %/s", 1)
    random.Random(21).shuffle(gewaehlt)
    return [{**f, "nr": i} for i, f in enumerate(gewaehlt, 1)]


def perzentile(werte: list[float]) -> str:
    if not werte:
        return "–"
    s = sorted(werte)
    return " / ".join(f"{s[min(len(s) - 1, int(q * len(s)))]:.0f}" for q in (0.1, 0.25, 0.5, 0.75, 0.9))


def liste(alle: list[dict], wahl: list[dict]) -> None:
    for charge in QUELLEN:
        fs = [f for f in alle if f["charge"] == charge]
        schnell = sum(f["urteil"] == "schnell" for f in fs)
        print(f"{charge}: {len(fs)} Zoomfahrten in {len({f['path'] for f in fs})} Clips, vorläufig {schnell} schnell; "
              f"tempo_max P10/25/50/75/90: {perzentile([f['tempo_max'] for f in fs])} %/s")
    print("\nDrehteller-Zooms:")
    for f in sorted((f for f in alle if f["drehteller"]), key=lambda f: (f["clip"], f["von_s"])):
        print(f"  {f['ordner']}/{f['clip']} {f['von_s']:.1f}–{f['bis_s']:.1f} s {f['von_mm']:g} → {f['bis_mm']:g} mm "
              f"Spitze {f['tempo_max']:.0f} Mittel {f['tempo_mittel']:.0f} %/s ruck {f['ruck']:.2f} "
              f"{'ruckartig ' if f['ruckartig'] else ''}{f['urteil']}")
    print("\nAuswahl:")
    for f in sorted(wahl, key=lambda f: f["nr"]):
        print(f"  {f['nr']:>2}. {f['charge']} {f['clip']} {f['von_s']:.1f}–{f['bis_s']:.1f} s {f['von_mm']:g} → "
              f"{f['bis_mm']:g} mm, {f['tempo_max']:.0f} %/s, ruck {f['ruck']:.2f} — {f['grund']}")


def plakette(nr: int, ziel: Path) -> Path:
    """Nummer als PNG (ffmpeg dieses Macs hat kein drawtext): weiße Ziffer auf halbtransparentem Schwarz."""
    bild = Image.new("RGBA", (260, 170), (0, 0, 0, 0))
    zeichnen = ImageDraw.Draw(bild)
    zeichnen.rounded_rectangle([0, 0, 259, 169], radius=24, fill=(0, 0, 0, 170))
    try:
        schrift = ImageFont.truetype(FONT, 120)
    except OSError:
        schrift = ImageFont.load_default(size=120)
    zeichnen.text((130, 85), str(nr), font=schrift, fill=(255, 255, 255, 255), anchor="mm")
    bild.save(ziel)
    return ziel


def slog3(path: str) -> bool:
    """S-Log3 laut Sony-Sidecar (<Clip>M01.XML) — dann LUT LC-709 Type A wie in den W&L-Vorschauen."""
    xml = Path(path).with_name(Path(path).stem + "M01.XML")
    return xml.is_file() and "s-log3" in xml.read_text(encoding="utf-8", errors="replace").lower()


def segment(f: dict, ziel: Path, arbeit: Path) -> tuple[float, float]:
    """3–5 s um die Fahrt (0,5 s davor), 100 % Tempo; liefert (Quell-Start, Dauer)."""
    dauer = min(5.0, max(3.0, f["bis_s"] - f["von_s"] + 1.0))
    start = max(0.0, f["von_s"] - 0.5)
    if f.get("dauer_s"):
        start = max(0.0, min(start, float(f["dauer_s"]) - dauer))
    lut = f"lut3d=file='{LUT}'," if LUT.exists() and slog3(f["path"]) else ""
    bild = (f"[0:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,{lut}"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,scale=w=iw:h=ih:out_range=tv:out_color_matrix=bt709,"
            f"format=yuv420p[b];[b][1:v]overlay=48:48:shortest=1,format=yuv420p[v]")
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", f["path"], "-loop", "1",
           "-i", str(plakette(f["nr"], arbeit / f"nr_{f['nr']:02d}.png")), "-filter_complex", bild, "-map", "[v]",
           "-an", "-t", f"{dauer:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "fast", "-crf", "18",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", str(ziel)]
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)
    return start, dauer


def rendern(wahl: list[dict]) -> Path:
    arbeit = CHARGE / "_intern" / "work"
    arbeit.mkdir(parents=True, exist_ok=True)
    stuecke, t = [], 0.0
    for f in sorted(wahl, key=lambda f: f["nr"]):
        seg = arbeit / f"seg_{f['nr']:02d}.mp4"
        start, dauer = segment(f, seg, arbeit)
        f.update(quelle_start_s=round(start, 2), video_von_s=round(t, 2), video_bis_s=round(t + dauer, 2))
        t += dauer
        stuecke.append(seg)
        print(f"  Nr. {f['nr']}: {f['clip']} ab {start:.1f} s, {dauer:.1f} s", flush=True)
    liste_txt = arbeit / "concat.txt"
    liste_txt.write_text("".join(f"file '{s}'\n" for s in stuecke), encoding="utf-8")
    ziel = arbeit / "zoom-beispiele.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(liste_txt), "-c", "copy",
                    str(ziel)], check=True, stdin=subprocess.DEVNULL)
    (CHARGE / "_intern" / "beispiele.json").write_text(json.dumps(sorted(wahl, key=lambda f: f["nr"]), indent=1,
                                                                  ensure_ascii=False), encoding="utf-8")
    return ziel


if __name__ == "__main__":
    alle = fahrten()
    wahl = auswahl(alle)
    liste(alle, wahl)
    if "--rendern" in sys.argv:
        print(f"\nBeispielvideo: {rendern(wahl)}")
```

(Das Skript lief in der Planung auf einer Probe-Charge mit 57 W&L-Clips: Auswahl, Render und `beispiele.json` wie
beschrieben; ffmpeg ohne drawtext → Nummer als Pillow-PNG per `overlay`.)

- [ ] **Step 5: Übersicht prüfen**

```bash
cd "/Users/jansantos/NIRO Studio" && tools/autocut/venv/bin/python \
  "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten/_intern/skripte/zoom_beispiele.py" --liste
```

Expected: je Charge Zahl der Zoomfahrten und Tempo-Perzentile, alle Drehteller-Zooms, eine Auswahl mit 8–10 Nummern.
Entscheidungsregeln:
- Die zwei „Drehteller (Referenz ok)"-Beispiele müssen gleichmäßige Fahrten ≥ 1 s sein (keine Rück-Zooms mit > 90 %/s).
  Sind die Drehteller-Zooms nicht eindeutig (z. B. nur schnelle), **STOP** und den User nach 2–3 Clipnamen fragen (Spec
  Abschnitt 4.2); dann `DREHTELLER` im Skript auf diese Clips setzen.
- Die Tempo-Beispiele sollen 15–55 %/s abdecken; fehlen Werte (zu wenige Kandidaten), reicht die Auswahl ab 8 Beispielen.

- [ ] **Step 6: Beispielvideo rendern und prüfen**

```bash
KAL="/Users/jansantos/NIRO Studio/projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten"
cd "/Users/jansantos/NIRO Studio" && tools/autocut/venv/bin/python "$KAL/_intern/skripte/zoom_beispiele.py" --rendern \
  | tail -12 && ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,color_range:format=duration \
  -of compact "$KAL/_intern/work/zoom-beispiele.mp4"
```

Expected: `stream|codec_name=h264|width=1920|height=1080|color_range=tv|r_frame_rate=25/1`, Dauer = Summe der Segmente
(≈ 30–45 s); `_intern/beispiele.json` mit `video_von_s`/`video_bis_s` je Nummer. Ein Standbild je Nummer ansehen
(`ffmpeg -ss <video_von_s + 1> -i … -frames:v 1 …jpg`): Nummer oben links, Farben normal (LUT), kein Farbkippen.

- [ ] **Step 7: In NIRO Review ablegen**

```bash
cd "/Users/jansantos/NIRO Studio" && python3 tools/review/review.py hinzufuegen \
  "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten" \
  --datei "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten/_intern/work/zoom-beispiele.mp4" \
  --video "Zoom-Beispiele" \
  --notiz "Kalibrierung Zoomfahrten: bitte je Nummer (oben links) „ok" oder „zu schnell" kommentieren"
```

Expected: Exit 0, Version V1, Link `http://localhost:4711/#/NIRO/Werkzeug-Kalibrierung/Zoom-Beispiele`.

- [ ] **Step 8: Protokolle und Abgleich**

**Neue Datei `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten/Protokoll.md`** (Datum des Laufs eintragen):

```markdown
# Protokoll — NIRO / Werkzeug-Kalibrierung / 2026-09 Zoomfahrten

## 2026-09-21 — Kalibrierung Zoomfahrten, Teil 1

- Gemacht: Telemetrie-Läufe mit Zoomfahrten über die B-Roll von Wurst & Liebe (2026-08 Dreh 05.08, `--ordner` 00 - B-Roll,
  nur rtmd) und MEK (2026-06 Ads und Imagefilm Dreh, 463 Clips); Auswahl der Grenzfälle mit
  `_intern/skripte/zoom_beispiele.py` (Plan `docs/superpowers/plans/2026-09-21-autocut-zoom-brennweite.md`, Task 9).
- Geliefert: `_intern/beispiele.json`, `_intern/work/zoom-beispiele.mp4`; NIRO Review „Zoom-Beispiele" V1
  (http://localhost:4711/#/NIRO/Werkzeug-Kalibrierung/Zoom-Beispiele).
- Offen: Urteil des Users je Nummer („ok"/„zu schnell"), danach Teil 2 (Schwellen setzen).
```

In den Protokollen von Wurst & Liebe und MEK steht nach den Läufen je ein Eintrag „AutoCut: Telemetrie" (von der CLI);
darunter je eine Zeile „Zweck: Kalibrierung Zoomfahrten (Charge NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten)" ergänzen.

```bash
cd "/Users/jansantos/NIRO Studio" \
  && sh tools/studio_abgleich.sh --charge "projects/Wurst & Liebe/Social-Reels/2026-08 Dreh 05.08" \
  && sh tools/studio_abgleich.sh --charge "projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh" \
  && sh tools/studio_abgleich.sh --charge "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten"
```

- [ ] **Step 9: STOP — Urteil des Users**

Dem User melden: Link, Zahl der Beispiele, Bitte: je Nummer „ok" oder „zu schnell" als Kommentar (am Beispiel oder als
„3: ok"), danach „fertig". Nicht verraten, welche Nummer welches Tempo hat. Auf die Rückmeldung warten; erst dann Task 10.

---

### Task 10: Kalibrierung Teil 2 — Schwellen aus den Urteilen, Gegenprobe, Regressionstest, Spec-Nachtrag

Controller-Task wie Task 9 (NAS, Code aus dem Worktree, Chargen im Hauptordner). Voraussetzung: der User hat „fertig" gesagt.

**Files:**
- Create (Charge): `…/2026-09 Zoomfahrten/_intern/urteile.json`, `…/_intern/skripte/zoom_kalibrieren.py`; erzeugt `…/_intern/kb_reihen.json`
- Create: `tools/autocut/tests/fixtures/kb_zoom_kalibrierung.json` (vom Skript geschrieben)
- Modify: `tools/autocut/defaults.yaml` (drei Werte), `tools/autocut/tests/test_telemetrie.py` (Regressionstest)
- Modify: `docs/superpowers/specs/2026-09-21-autocut-zoom-brennweite-design.md` (Status, Nachtrag), `tools/autocut/WORKFLOW-AutoCut.md` (Kalibrierwerte)

**Interfaces:**
- Consumes: `beispiele.json` (Task 9), Kommentare aus NIRO Review, `zoom_beispiele.fahrten()` (Import aus demselben Ordner)
- Produces: kalibrierte `zoom_schnell_proz_s`, `zoom_ruck_max`, `zoom_stocken_anteil`; Fixture `{"drehteller": {…},
  "mek": {…}}` je mit `clip`, `fps`, `samples`, `kb_mm`, `kb_index`, `von_s`, `bis_s`, `erwartet`

- [ ] **Step 1: Abgleich, Kommentare holen, Urteile festhalten**

```bash
KAL="projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten"
cd "/Users/jansantos/NIRO Studio" && sh tools/studio_abgleich.sh --charge "$KAL" \
  && python3 tools/review/review.py kommentare "$KAL" --video "Zoom-Beispiele"
```

Expected: Exit 0, Export unter `…/Material/Feedback/<Datum> Review Zoom-Beispiele V1/kommentare.md`. Je Kommentar die
Nummer zuordnen (Text „3: ok" / „Nr. 3 zu schnell", sonst über den Timecode: die Nummer, in deren
`video_von_s`–`video_bis_s` aus `beispiele.json` der TC liegt). Ergebnis als `_intern/urteile.json` schreiben, Werte nur
`ok` oder `zu schnell`, z. B. `{"1": "ok", "2": "zu schnell", "3": "ok"}`. Fehlen mehr als zwei Nummern oder ist ein
Kommentar mehrdeutig: **STOP**, beim User nachfragen.

- [ ] **Step 2: Kalibrier-Skript schreiben**

**Neue Datei `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten/_intern/skripte/zoom_kalibrieren.py`** (im Hauptordner):

```python
"""Kalibrierung Zoomfahrten, Teil 2 (Spec 2026-09-21, Abschnitt 4): Schwellen aus den Urteilen des Users ableiten.
Einmal-Skript der Kalibrier-Charge, nicht Teil des Werkzeugs.

Liest ``_intern/beispiele.json`` (zoom_beispiele.py) und ``_intern/urteile.json`` ({"1": "ok", "2": "zu schnell", …}),
liest die KB-Reihen der Beispiel-, Drehteller- und MEK-Gegenprobe-Clips einmal aus der rtmd-Spur (NAS, nur lesend;
Zwischenstand ``_intern/kb_reihen.json``) und rechnet die Zoomfahrten für ein Raster aus zoom_schnell_proz_s ×
zoom_ruck_max × zoom_stocken_anteil neu. Ausgabe: Fehler je Tempo-Schwelle, Empfehlung (Mitte des besten Bereichs, ruck
und Stocken nah an den Startwerten), Drehteller-Gegenprobe mit der Empfehlung; ``--fixture <Datei>`` schreibt die Reihen
des schnellsten „ok"-Drehteller-Beispiels und der MEK-Gegenprobe als Test-Fixture.

Aufruf aus der Studio-Wurzel mit dem venv und dem Code des Worktrees:
    "<WT>/tools/autocut/venv/bin/python" "<Charge>/_intern/skripte/zoom_kalibrieren.py" --autocut "<WT>/tools/autocut"
        [--fixture "<WT>/tools/autocut/tests/fixtures/kb_zoom_kalibrierung.json"]
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve()
CHARGE = HIER.parents[2]
sys.path.insert(0, str(HIER.parent))
from zoom_beispiele import fahrten  # noqa: E402

GEGENPROBE = ("a7MK4_20260624_9885", 160.0)   # MEK a7 IV 74 → 169 mm: die Fahrt, die über 160 mm endet, ist schnell
RASTER = {"zoom_schnell_proz_s": [float(x) for x in range(15, 105, 5)],
          "zoom_ruck_max": [0.4, 0.5, 0.6, 0.7, 0.8, 1.0], "zoom_stocken_anteil": [0.1, 0.15, 0.2]}


def reihen(pfade: dict[str, float], R) -> dict[str, dict]:
    """KB-Reihe je Clip aus der rtmd-Spur, zwischengespeichert in _intern/kb_reihen.json."""
    cache_datei = CHARGE / "_intern" / "kb_reihen.json"
    cache = json.loads(cache_datei.read_text(encoding="utf-8")) if cache_datei.exists() else {}
    for pfad, fps in pfade.items():
        if pfad not in cache:
            d = R.auswerten(R.samples(R.datenspur_lesen(pfad)))
            index = [] if d.kb_index == list(range(len(d.kb_mm))) else d.kb_index
            cache[pfad] = {"fps": fps, "samples": d.samples, "kb_mm": d.kb_mm, "kb_index": index}
            print(f"  gelesen: {Path(pfad).name} ({d.samples} Samples)", flush=True)
    cache_datei.write_text(json.dumps(cache), encoding="utf-8")
    return cache


def urteil_im_bereich(reihe: dict, von_s: float, bis_s: float, cfg: dict, T) -> str | None:
    """Urteil der Fahrt mit der größten Überdeckung von [von_s, bis_s]; None, wenn dort keine Fahrt erkannt wird."""
    kb25 = T.kb_je_frame(reihe["kb_mm"], reihe["kb_index"], reihe["fps"], reihe["samples"])
    treffer = [(min(bis_s, z["bis_s"]) - max(von_s, z["von_s"]), z) for z in T.zoomfahrten(kb25, cfg)]
    treffer = [(u, z) for u, z in treffer if u > 0]
    return max(treffer, key=lambda t: t[0])[1]["urteil"] if treffer else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--autocut", required=True, help="tools/autocut des Worktrees (Code mit Zoomfahrten)")
    ap.add_argument("--fixture", help="Test-Fixture schreiben (Drehteller-Referenz + MEK-Gegenprobe)")
    args = ap.parse_args()
    sys.path.insert(0, str(Path(args.autocut).resolve() / "src"))
    from niro_autocut import rtmd as R
    from niro_autocut import telemetrie as T
    from niro_autocut.charge import load_config
    basis = load_config(Path("/nirgendwo"))["telemetrie"]
    alle = fahrten()
    beispiele = json.loads((CHARGE / "_intern" / "beispiele.json").read_text(encoding="utf-8"))
    urteile = json.loads((CHARGE / "_intern" / "urteile.json").read_text(encoding="utf-8"))
    gegen = next(f for f in alle if f["clip"] == GEGENPROBE[0] and f["bis_mm"] >= GEGENPROBE[1])
    dreh = [f for f in alle if f["drehteller"]]
    daten = reihen({f["path"]: float(f["fps"]) for f in [*beispiele, gegen, *dreh]}, R)
    faelle = [(b["nr"], b["path"], b["von_s"], b["bis_s"], "langsam" if urteile[str(b["nr"])] == "ok" else "schnell")
              for b in beispiele if str(b["nr"]) in urteile]
    faelle.append(("MEK", gegen["path"], gegen["von_s"], gegen["bis_s"], "schnell"))
    ergebnis = {}
    for werte in itertools.product(*RASTER.values()):
        cfg = {**basis, **dict(zip(RASTER, werte))}
        ergebnis[werte] = [nr for nr, pfad, von, bis, soll in faelle
                           if urteil_im_bereich(daten[pfad], von, bis, cfg, T) != soll]
    tempi = RASTER["zoom_schnell_proz_s"]
    fehler_je_tempo = {s: min(len(f) for w, f in ergebnis.items() if w[0] == s) for s in tempi}
    print(f"\n{len(faelle)} Fälle (Urteile + MEK-Gegenprobe). Fehler je zoom_schnell_proz_s (bestes ruck/stocken):")
    print("  " + "  ".join(f"{s:g}: {n}" for s, n in fehler_je_tempo.items()))
    beste = [s for s in tempi if fehler_je_tempo[s] == min(fehler_je_tempo.values())]
    tempo = beste[(len(beste) - 1) // 2]            # Mitte des besten Bereichs (bei gerader Zahl die untere)
    kandidaten = [w for w, f in ergebnis.items() if w[0] == tempo and len(f) == fehler_je_tempo[tempo]]
    wahl = min(kandidaten, key=lambda w: (abs(w[1] - 0.6) + abs(w[2] - 0.2), w[1], -w[2]))   # nah an den Startwerten
    print(f"Bester Bereich: {', '.join(f'{s:g}' for s in beste)} %/s. Empfehlung: zoom_schnell_proz_s {wahl[0]:g}, "
          f"zoom_ruck_max {wahl[1]:g}, zoom_stocken_anteil {wahl[2]:g} — falsch: {ergebnis[wahl] or 'keine'}")
    cfg = {**basis, **dict(zip(RASTER, wahl))}
    print("\nDrehteller-Gegenprobe mit der Empfehlung (Spitze aus dem Telemetrie-Lauf):")
    for f in sorted(dreh, key=lambda f: (f["clip"], f["von_s"])):
        u = urteil_im_bereich(daten[f["path"]], f["von_s"], f["bis_s"], cfg, T)
        print(f"  {f['ordner']}/{f['clip']} {f['von_s']:.1f}–{f['bis_s']:.1f} s ({f['bis_s'] - f['von_s']:.1f} s) "
              f"{f['von_mm']:g} → {f['bis_mm']:g} mm, Spitze {f['tempo_max']:.0f} %/s: {u}")
    if args.fixture:
        ref = max((b for b in beispiele if b["drehteller"] and urteile.get(str(b["nr"])) == "ok"),
                  key=lambda b: b["tempo_max"])
        fixture = {"drehteller": {"clip": ref["clip"], **daten[ref["path"]], "von_s": ref["von_s"],
                                  "bis_s": ref["bis_s"], "erwartet": "langsam"},
                   "mek": {"clip": gegen["clip"], **daten[gegen["path"]], "von_s": gegen["von_s"],
                           "bis_s": gegen["bis_s"], "erwartet": "schnell"}}
        pruefung = [f["erwartet"] == urteil_im_bereich(f, f["von_s"], f["bis_s"], cfg, T) for f in fixture.values()]
        Path(args.fixture).write_text(json.dumps(fixture), encoding="utf-8")
        print(f"\nFixture {args.fixture}: Drehteller {ref['clip']}, MEK {gegen['clip']} — Prüfung mit der Empfehlung "
              f"{'ok' if all(pruefung) else 'FEHLER (Empfehlung prüfen)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

(In der Planung mit erfundenen Urteilen auf der Probe-Charge durchgelaufen: Raster, Empfehlung, Gegenprobe, Fixture.)

- [ ] **Step 3: Kalibrieren**

```bash
MAIN="/Users/jansantos/NIRO Studio"; WT="$MAIN/.claude/worktrees/autocut-zoom-brennweite"
KAL="projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten"
cd "$MAIN" && "$WT/tools/autocut/venv/bin/python" "$KAL/_intern/skripte/zoom_kalibrieren.py" \
  --autocut "$WT/tools/autocut" --fixture "$WT/tools/autocut/tests/fixtures/kb_zoom_kalibrierung.json" < /dev/null
```

Expected: Zeile „Fehler je zoom_schnell_proz_s …", Zeile „Empfehlung: …", Drehteller-Gegenprobe, Zeile „Fixture …
Prüfung mit der Empfehlung ok". Entscheidungsregeln:
- „falsch: keine" → Empfehlung übernehmen. Ein einziger Fehler ist zulässig, wenn er im Spec-Nachtrag begründet wird
  (Beispiel und Grund); mehr als ein Fehler → **STOP**: dem User die Fehlerzeile und die falsch beurteilten Nummern zeigen.
- Drehteller-Gegenprobe: gleichmäßige Drehteller-Fahrten ≥ 1 s mit Spitze unter 60 %/s müssen `langsam` sein. Liegt
  eine davon nur knapp (≤ 5 %/s) über der empfohlenen Schwelle, die nächsthöhere Rasterstufe nehmen, sofern sie in der
  Fehlerzeile dieselbe Fehlerzahl hat; sonst **STOP** und dem User die Liste zeigen. Rück-Zooms (> 90 %/s) sind `schnell`.
- Die MEK-Gegenprobe (a7 IV 109 → 169 mm) steht als Fall „MEK" in der Fehlerliste, wenn sie nicht `schnell` ist.

- [ ] **Step 4: `defaults.yaml` mit den Kalibrierwerten füllen**

**Ersetzen in `tools/autocut/defaults.yaml`** (im Worktree):

```yaml
  zoom_schnell_proz_s: 20.0 # Spitzentempo, ab dem eine Zoomfahrt schnell ist (% pro s) — Startwert bis zur Kalibrierung
  zoom_ruck_max: 0.6        # Ungleichmäßigkeit (Variationskoeffizient von |v|), ab der eine Fahrt ruckartig = schnell ist
  zoom_stocken_anteil: 0.2  # Stocken: |v| fällt mitten in der Fahrt unter diesen Anteil der Spitze und steigt wieder
```

**durch** die drei Werte aus Schritt 3 mit Kalibrier-Kommentar, z. B. bei der Empfehlung 45 / 0,6 / 0,15 (Zahlen aus
dem eigenen Lauf einsetzen, Zeilen ≤ 125 Zeichen):

```yaml
  zoom_schnell_proz_s: 45.0 # Spitzentempo, ab dem eine Zoomfahrt schnell ist (% pro s); Kalibrierung 2026-09-21: W&L + MEK,
                            # 10 Urteile des Users („Zoom-Beispiele" in NIRO Review), Drehteller-Zooms langsam
  zoom_ruck_max: 0.6        # Ungleichmäßigkeit (Variationskoeffizient von |v|), ab der eine Fahrt ruckartig = schnell ist
  zoom_stocken_anteil: 0.15 # Stocken: |v| fällt mitten in der Fahrt unter diesen Anteil der Spitze (Kalibrierung 2026-09-21)
```

- [ ] **Step 5: Regressionstest an echten Reihen**

**Anhängen an `tools/autocut/tests/test_telemetrie.py`:**

```python
# --- Kalibrierung Zoomfahrten (Task 10): echte KB-Reihen gegen die ausgelieferten Schwellen --------------------------------

def test_kalibrierung_zoom_an_echten_reihen():
    """W&L-Drehteller-Referenz (vom User „ok") bleibt langsam, der MEK-Zoom a7 IV 109 → 169 mm ist schnell — mit den
    Schwellen aus defaults.yaml. Fixture: KB-Reihen aus der rtmd-Spur (zoom_kalibrieren.py der Kalibrier-Charge)."""
    daten = json.loads((Path(__file__).parent / "fixtures" / "kb_zoom_kalibrierung.json").read_text(encoding="utf-8"))
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    for fall in daten.values():
        kb25 = T.kb_je_frame(fall["kb_mm"], fall["kb_index"], fall["fps"], fall["samples"])
        treffer = [z for z in T.zoomfahrten(kb25, cfg) if z["von_s"] < fall["bis_s"] and z["bis_s"] > fall["von_s"]]
        assert treffer and all(z["urteil"] == fall["erwartet"] for z in treffer), (fall["clip"], treffer)
```

Run: `cd tools/autocut && venv/bin/python -m pytest tests/test_telemetrie.py -q -k kalibrierung_zoom && venv/bin/python -m pytest -q`
Expected: der neue Test besteht (mit den Startwerten aus Task 1 schlüge er fehl: die Drehteller-Referenz wäre `schnell`);
Gesamtlauf grün.

- [ ] **Step 6: Telemetrie mit den Kalibrierwerten neu messen**

Die Kalibrierwerte ändern den Config-Hash — beide Chargen einmal neu messen (Befehle aus Task 9, Schritte 2 und 3, im
Hintergrund). Danach die schnellen Fahrten je Charge zählen:

```bash
cd "/Users/jansantos/NIRO Studio" && python3 - <<'PY'
import json
for name, pfad in (("W&L", "projects/Wurst & Liebe/Social-Reels/2026-08 Dreh 05.08"),
                   ("MEK", "projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh")):
    tele = json.load(open(f"{pfad}/_intern/autocut/telemetrie.json", encoding="utf-8"))
    zooms = [z for r in tele for z in r.get("zooms") or []]
    print(name, len(zooms), "Zoomfahrten,", sum(z["urteil"] == "schnell" for z in zooms), "schnell")
PY
```

Expected: je Charge eine Zeile; die Zahlen gehen in den Spec-Nachtrag.

- [ ] **Step 7: Spec-Nachtrag, Status und WORKFLOW**

**Ersetzen in `docs/superpowers/specs/2026-09-21-autocut-zoom-brennweite-design.md`:**

```markdown
Datum: 2026-09-21 · Status: Abschnitte 1–3 im Chat vom User freigegeben (21.09.). Folgeschritt der Kamera-Telemetrie
```

**durch:**

```markdown
Datum: 2026-09-21 · Status: umgesetzt (Plan `docs/superpowers/plans/2026-09-21-autocut-zoom-brennweite.md`), kalibriert
(Nachtrag unten). Folgeschritt der Kamera-Telemetrie
```

Am Dateiende einen Abschnitt `## Nachtrag <Datum> — Kalibrierung Zoom` anhängen mit: Datenbasis (Clips und Zoomfahrten je
Charge aus Schritt 6), Tabelle der Beispiele (Spalten: Nr, Charge, Clip, von–bis s, mm → mm, Spitze %/s, ruck,
Urteil User, Urteil mit den neuen Werten), die Fehlerzeile je Tempo aus Schritt 3, die gesetzten Werte mit Begründung
(Mitte des besten Bereichs, Abweichungen von der Empfehlung und warum), Drehteller-Gegenprobe und MEK-Gegenprobe
(a7MK4_20260624_9885, 109 → 169 mm).

**Ersetzen in `tools/autocut/WORKFLOW-AutoCut.md`:**

```text
Startwerte bis zur Kalibrierung: 20 %/s, `ruck` 0,6, Stocken 0,2.
```

**durch** einen Satz mit den gesetzten Werten, z. B. (eigene Zahlen einsetzen):

```text
Kalibriert 21.09.2026 (Wurst & Liebe, MEK, 10 Urteile des Users in NIRO Review „Zoom-Beispiele"): schnell ab 45 %/s
Spitze, `ruck` über 0,6 oder Stocken unter 15 % der Spitze; Drehteller-Zooms langsam, MEK a7 IV 109 → 169 mm schnell.
```

- [ ] **Step 8: Protokolle und Abgleich**

Im `Protokoll.md` der Kalibrier-Charge einen Eintrag „Kalibrierung Zoomfahrten, Teil 2" (Urteile, gesetzte Werte,
Fixture, Commit); in Wurst & Liebe und MEK unter dem neuen „AutoCut: Telemetrie"-Eintrag „Zweck: Neumessung mit den
kalibrierten Zoom-Schwellen". Danach alle drei Chargen abgleichen (Befehl aus Task 9, Schritt 8).

- [ ] **Step 9: Gesamtlauf und Commit**

Run: `cd tools/autocut && venv/bin/python -m pytest -q`
Expected: grün (nur `1 skipped`).

```bash
git add tools/autocut/defaults.yaml tools/autocut/tests/fixtures/kb_zoom_kalibrierung.json \
  tools/autocut/tests/test_telemetrie.py tools/autocut/WORKFLOW-AutoCut.md \
  docs/superpowers/specs/2026-09-21-autocut-zoom-brennweite-design.md
git commit -q -m "feat(autocut): Zoom-Schwellen kalibriert (W&L-Drehteller, MEK, Urteile des Users), Regressionstest

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
