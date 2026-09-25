# AutoCut — Schnittkanten frame-genau — Implementierungsplan

> **Für agentische Ausführung:** PFLICHT-SKILL: superpowers:subagent-driven-development (empfohlen) oder
> superpowers:executing-plans, Task für Task. Schritte mit Checkbox (`- [ ]`).

**Goal:** B-Roll-Shots schneiden nie in Kamerabewegung hinein oder aus ihr heraus: stabile Läufe und die Prüfung
rechnen frame-genau aus dem Gyro statt aus 2-s-Fenstern.

**Architecture:** Die Telemetrie speichert je Clip die Bildverschiebung je 25-fps-Frame (`verschiebung`), mit der
Brennweite je Frame umgerechnet. Reine Funktionen in `telemetrie.py` leiten daraus ruhige Frames, stabile Läufe und
Kantenbefunde ab. Stufe 2b schreibt die Läufe in den Index, `verify_layout()` prüft die genutzten Frames jedes Shots
(Kanten hart, Mitte Hinweis) und schlägt eine ruhige Lage vor. `bewegung_max` kalibriert eine Review-Runde mit dem User.

**Tech Stack:** Python 3 (venv `tools/autocut/venv`), numpy, pytest; ffmpeg, Pillow und NIRO Review für die Kalibrierung.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-25-autocut-schnittkanten-framegenau-design.md` — bei Widerspruch gilt die Spec.
- Arbeitsort: Worktree `/Users/jansantos/NIRO Studio/.claude/worktrees/autocut-schnittkanten`, Branch
  `worktree-autocut-schnittkanten`. Befehle aus der Worktree-Wurzel; `tools/autocut/venv` ist dort ein Symlink auf die
  venv des Hauptordners (nicht committen, steht in `.git/info/exclude`).
- Tests: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests -q -p no:cacheprovider`
  (Stand vor Task 1: 851 passed, 1 skipped). Einzelne Datei: Pfad statt `tools/autocut/tests`.
- `projects/` gibt es nur im Hauptordner `/Users/jansantos/NIRO Studio/projects/` — nur mit absolutem Pfad lesen.
  In der Klebl-Charge (`projects/Klebl/Recruiting-Videos/2026-09 Dreh Edeka Baustelle 22.09/`) **nichts schreiben**:
  dort arbeitet parallel eine Feinschnitt-Session.
- Nichts in Resolve schreiben. Medien auf dem NAS nur lesen.
- Schwellen (`defaults.yaml`, Block `telemetrie:`): `ruhig_max_px` 0,15 · `bewegung_max` 2,0 (UNKALIBRIERT bis Task 6) ·
  `glatt_s` 0,4 · `kante_s` 0,3 · `stabil_min_s` 2,0.
- Meldungen deutsch mit Dezimalkomma (`_z()` in `broll_layout.py`, `_de()` im Bericht); Kommentare deutsch wie im Bestand.
- Commits: `feat(autocut): …` / `test(autocut): …` / `docs(autocut): …`; letzte Zeile
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Kein Merge nach main ohne OK des Users.

## Dateien

| Datei | Verantwortung | Task |
|---|---|---|
| `tools/autocut/src/niro_autocut/telemetrie.py` | Reihe je Frame, Brennweite je Frame, `MESS_VERSION`; ruhige Frames, Läufe, Kantenbefunde, Vorschlag | 1, 2, 3 |
| `tools/autocut/defaults.yaml` | `glatt_s`, `kante_s`, `bewegung_max` neu gedeutet, zwei Schlüssel entfallen | 2, 3, 6 |
| `tools/autocut/src/niro_autocut/index_sections.py` | `stabil_quelle.glatt_s` | 2 |
| `tools/autocut/src/niro_autocut/broll_layout.py` | Kantenprüfung in `verify_layout()`, alte Bewegungs-Warnungen raus | 2, 3 |
| `tools/autocut/src/niro_autocut/telemetrie_bericht.py`, `scripts/autocut_telemetrie.py` | Spalte „ruhige Läufe (s)“ | 4 |
| `tools/autocut/tests/reihen.py` (neu) | synthetische Frame-Reihen für Tests | 2 |
| `tools/autocut/tests/fixtures/gen_bereiche_fixture.py` + `bereiche-*.json` | Fixtures neu vom NAS, mit Reihe | 2, 6 |
| `tools/autocut/tests/test_bereiche_abnahme.py` | Abnahme frame-genau | 2, 3, 6 |
| `tools/autocut/prompts/place-broll.md`, `WORKFLOW-AutoCut.md`, `README.md`, Spec 23.09. | Doku | 4, 6 |
| `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten/` (Hauptordner) | Review-Runde | 6 |

---

## Task 1: Messung — Reihe je Frame, Brennweite je Frame, Messversion

**Files:**
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (`verschiebung_aus_rate` Z. 56–63, `config_hash` Z. 393–398,
  `_leer` Z. 401–408, `clip_messen` Z. 416–463)
- Test: `tools/autocut/tests/test_telemetrie.py`

**Interfaces:**
- Produces: `verschiebung_aus_rate(rate, kb_mm: float | np.ndarray, cfg, ziel_fps=25.0) -> np.ndarray (m, 2)`;
  `_auf_laenge(x: np.ndarray, n: int) -> np.ndarray`; `verschiebung_reihe(dxy, t0_s=0.0) -> dict`
  `{"fps": 25.0, "t0_s": float, "dx": list[float], "dy": list[float]}`; `MESS_VERSION = 2`; Datensatzfeld
  `rec["verschiebung"]` (dict wie oben oder `None`).

- [ ] **Step 1: Failing Tests schreiben** — ans Ende von `tests/test_telemetrie.py`:

```python
# --------------------------------------------------------------------------- #
# Schnittkanten frame-genau (Spec 2026-09-25): Reihe je Frame, Brennweite je Frame, Messversion
# --------------------------------------------------------------------------- #

def test_verschiebung_aus_rate_mit_brennweite_je_frame():
    rate = np.zeros((4, 3))
    rate[:, 1] = 10.0
    fest = T.verschiebung_aus_rate(rate, 36.0, CFG)
    je_frame = T.verschiebung_aus_rate(rate, np.array([36.0, 36.0, 72.0, 72.0]), CFG)
    assert np.allclose(je_frame[:2], fest[:2]) and np.allclose(je_frame[2:], 2 * fest[2:])


def test_auf_laenge_kuerzt_oder_haelt_den_letzten_wert():
    assert T._auf_laenge(np.array([1.0, 2.0, 3.0]), 2).tolist() == [1.0, 2.0]
    assert T._auf_laenge(np.array([1.0, 2.0]), 4).tolist() == [1.0, 2.0, 2.0, 2.0]


def test_verschiebung_reihe_rundet_auf_zwei_stellen():
    r = T.verschiebung_reihe(np.array([[0.123, -1.0], [2.0049, 0.006], [-0.001, 0.0]]))
    assert r == {"fps": 25.0, "t0_s": 0.0, "dx": [0.12, 2.0, 0.0], "dy": [-1.0, 0.01, 0.0]}
    assert str(r["dx"][2]) == "0.0"                       # keine −0,0 in telemetrie.json


def test_clip_messen_schreibt_die_reihe_je_frame(monkeypatch, tmp_path):
    clip = tmp_path / "FX3_0003.MP4"
    clip.write_bytes(b"x")
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: _rtmd_puffer(frames=100, gyro_y=10.0))
    rec = T.clip_messen(clip, CFG)
    v = rec["verschiebung"]
    assert v["fps"] == 25.0 and v["t0_s"] == 0.0 and len(v["dx"]) == len(v["dy"]) == 100
    # Test-CFG (Vorzeichen Schwenk −1): 10 °/s bei 71,6 mm KB ≈ −6,66 px je Frame
    assert v["dx"][0] == pytest.approx(-6.66, abs=0.01) and v["dy"][0] == 0.0
    assert T._leer(clip, "FX3", None)["verschiebung"] is None


def test_clip_messen_optisch_schreibt_die_reihe(monkeypatch, tmp_path):
    clip = tmp_path / "DJI_0073.MOV"
    clip.write_bytes(b"x")
    _optisch_fakes(monkeypatch, seed=22)
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "optisch" and len(rec["verschiebung"]["dx"]) == 29      # 30 Bilder → 29 Verschiebungen
    assert set(rec["verschiebung"]["dx"]) == {0.0}                                    # gleiche Bilder: keine Bewegung


def test_clip_messen_rechnet_den_gyro_mit_der_brennweite_je_frame(monkeypatch, tmp_path):
    clip = tmp_path / "FX3_0074.MP4"
    clip.write_bytes(b"x")
    kb = _zoomreihe((2.0, 24, 24), (0.4, 24, 72), (2.0, 72, 72))             # 111 Samples, Zoom 24 → 72 mm
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p), dauer=4.44))
    monkeypatch.setattr(T, "datenspur_lesen",
                        lambda p: _rtmd_puffer(frames=len(kb), gyro_y=10.0, kb=[_kb(x) for x in kb]))
    rec = T.clip_messen(clip, CFG)
    dx = rec["verschiebung"]["dx"]
    assert len(dx) == 111
    # gleiche Drehung, dreifache Brennweite → dreifache Bildverschiebung (vorher überall der Median)
    assert dx[-1] == pytest.approx(3 * dx[0], rel=0.02) and dx[0] == pytest.approx(-2.23, abs=0.01)


def test_config_hash_traegt_die_messversion(monkeypatch):
    h = T.config_hash(CFG)
    monkeypatch.setattr(T, "MESS_VERSION", T.MESS_VERSION + 1)
    assert T.config_hash(CFG) != h
```

- [ ] **Step 2: Tests laufen lassen, sie schlagen fehl**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests/test_telemetrie.py -q -p no:cacheprovider -k "reihe or auf_laenge or brennweite_je_frame or messversion"`
Expected: FAIL (`AttributeError: … has no attribute '_auf_laenge'` / `'verschiebung_reihe'` / `'MESS_VERSION'`, KeyError `verschiebung`).

- [ ] **Step 3: `verschiebung_aus_rate` für Brennweite je Frame** — ersetze die Funktion (Z. 56–63):

```python
def verschiebung_aus_rate(rate: np.ndarray, kb_mm, cfg: dict,
                          ziel_fps: float = ZIEL_FPS) -> np.ndarray:
    """(m, 3) °/s je Frame → (m, 2) px: dx aus der Schwenk-Achse, dy aus der Tilt-Achse (Achsen/Vorzeichen aus cfg).
    ``kb_mm`` ist eine Zahl oder die KB-Brennweite je Frame (Länge m): seit Spec 2026-09-25 rechnet ``clip_messen``
    jeden Frame mit seiner eigenen Brennweite — mit dem Median waren Zoom-Clips abschnittsweise falsch skaliert."""
    kb = np.asarray(kb_mm, np.float64)
    k = math.pi / 180.0 * float(cfg["optisch_breite"]) * kb / 36.0 / ziel_fps
    a, v = cfg["achsen"], cfg["vorzeichen"]
    dx = float(v["schwenk"]) * rate[:, int(a["schwenk"])] * k
    dy = float(v["tilt"]) * rate[:, int(a["tilt"])] * k
    return np.stack([dx, dy], axis=1)


def _auf_laenge(x: np.ndarray, n: int) -> np.ndarray:
    """Reihe auf ``n`` Werte bringen: kürzen oder mit dem letzten Wert verlängern (KB je Frame ↔ Gyro-Frames)."""
    x = np.asarray(x, np.float64)
    if len(x) >= n:
        return x[:n]
    return np.concatenate([x, np.full(n - len(x), x[-1])])


def verschiebung_reihe(dxy: np.ndarray, t0_s: float = 0.0) -> dict:
    """Reihe ``verschiebung`` für ``telemetrie.json`` (Spec 2026-09-25): dx/dy je 25-fps-Frame in px @480, auf 2 Stellen
    gerundet (+ 0,0 macht aus −0,0 eine 0,0); Frame ``i`` liegt bei ``t0_s + i / fps``."""
    d = np.asarray(dxy, np.float64).reshape(-1, 2)
    return {"fps": ZIEL_FPS, "t0_s": float(t0_s), "dx": (np.round(d[:, 0], 2) + 0.0).tolist(),
            "dy": (np.round(d[:, 1], 2) + 0.0).tolist()}
```

- [ ] **Step 4: Messversion im Config-Hash** — ersetze `config_hash` (Z. 393–398) durch:

```python
# Messversion, geht in den Config-Hash ein. 2 = Brennweite je Frame und Reihe ``verschiebung`` (Spec 2026-09-25):
# jeder ältere Datensatz gilt damit als veraltet und wird beim nächsten ``autocut_telemetrie.py`` neu gemessen.
MESS_VERSION = 2


def config_hash(cfg: dict) -> str:
    """Kurzer Hash (12 Hex-Zeichen, sha1) der ``telemetrie:``-Config ohne ``OHNE_MESSWIRKUNG``, zusammen mit
    ``MESS_VERSION`` — Haltung, Bewegungsart, Klassen, wackeln × px_faktor, ruhige Fenster, Fensterlänge, Zoomfahrten
    und die Reihe je Frame hängen an ihr; ein Cache-Datensatz mit anderem Hash ist veraltet."""
    text = json.dumps({"mess_version": MESS_VERSION, **{k: v for k, v in cfg.items() if k not in OHNE_MESSWIRKUNG}},
                      sort_keys=True, default=str)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
```

- [ ] **Step 5: `_leer` und `clip_messen`** — in `_leer` hinter `"ruhige_fenster": [],` die Zeile
`"verschiebung": None,` ergänzen. In `clip_messen`:
  - vor `if daten is not None:` die Zeile `kb25 = np.zeros(0, np.float64)` einfügen;
  - im Zweig `if daten.kb_mm:` direkt vor `out.update(zoom_messen(...))` einfügen:
    `kb25 = kb_je_frame(daten.kb_mm, daten.kb_index, float(info.fps), daten.samples)`;
  - im Gyro-Zweig die Zeile `dxy = verschiebung_aus_rate(rate, kb, cfg) * faktor` ersetzen durch

```python
            # Brennweite je Frame (Spec 2026-09-25); ohne Brennweitenverlauf der Median wie bisher
            kb_frames = _auf_laenge(kb25, len(rate)) if len(kb25) else kb
            dxy = verschiebung_aus_rate(rate, kb_frames, cfg) * faktor
```
  - `out.update(quelle="rtmd", **kennzahlen(dxy, cfg, kb, s))` wird
    `out.update(quelle="rtmd", verschiebung=verschiebung_reihe(dxy), **kennzahlen(dxy, cfg, kb, s))`;
  - der optische Zweig wird

```python
        elif not ohne_optisch:
            frames = _frames(p, cfg)
            dxy = verschiebungen(frames)
            out.update(quelle="optisch", verschiebung=verschiebung_reihe(dxy),
                       **kennzahlen(dxy, cfg, kb, schaerfe_frames(frames)))
```
  - im Modul-Docstring (Z. 1–10) ans Ende des ersten Absatzes: „Seit Spec 2026-09-25 zusätzlich die Reihe
    ``verschiebung`` je Frame (Gyro mit der Brennweite je Frame).“

- [ ] **Step 6: Tests grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests -q -p no:cacheprovider`
Expected: alle PASS (858 passed, 1 skipped).

- [ ] **Step 7: Commit**

```bash
git add tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/tests/test_telemetrie.py
git commit -m "feat(autocut): Telemetrie speichert die Bewegung je Frame, Gyro mit der Brennweite je Frame

MESS_VERSION 2 im Config-Hash: alte Datensätze gelten als veraltet und werden neu gemessen.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 2: Stabile Läufe frame-genau (mit Fixtures vom NAS und Abnahme)

**Files:**
- Create: `tools/autocut/tests/reihen.py`
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (Import `NamedTuple`; `OHNE_MESSWIRKUNG` Z. 387–390; neuer
  Abschnitt statt `stabile_bereiche` Z. 705–745)
- Modify: `tools/autocut/defaults.yaml` (Block „Stabile Bereiche“, Z. 146–152)
- Modify: `tools/autocut/src/niro_autocut/index_sections.py` (`telemetrie_anwenden`, Z. 199–252)
- Modify: `tools/autocut/src/niro_autocut/broll_layout.py` (Hinweis „andere Stabil-Schwellen“, Z. 922–924)
- Modify: `tools/autocut/tests/fixtures/gen_bereiche_fixture.py`; regenerate `bereiche-urteile.json`, `bereiche-wlc.json`;
  create `bereiche-klebl.json`
- Test: `tests/test_telemetrie.py`, `tests/test_index_sections.py`, `tests/test_broll_layout.py`,
  `tests/test_bereiche_abnahme.py`

**Interfaces:**
- Consumes (Task 1): `rec["verschiebung"]`.
- Produces: `bewegung_je_frame(rec, glatt_s) -> tuple[float, float, np.ndarray, np.ndarray] | None` = (t0_s, fps,
  wackeln, bewegung); `class Ruhe(NamedTuple)` mit `t0_s, fps, ruhig, wackeln, bewegung`, Methoden
  `frames(von_s, bis_s) -> slice`, `zeit(i) -> float`; `ruhe_je_frame(rec, cfg, faktor=1.0) -> Ruhe | None`;
  `stabile_bereiche(rec, cfg) -> list[[von_s, bis_s, wackeln_max, bewegung_max]]` (Format unverändert);
  Config-Schlüssel `glatt_s`; `stabil_quelle["glatt_s"]`; Testhelfer `reihen.reihe(*stuecke, t0_s=0.0, fps=25.0)`,
  `reihen.rec(*stuecke, t0_s=0.0, zooms=None, dauer_s=None)`.

- [ ] **Step 1: Testhelfer anlegen** — `tools/autocut/tests/reihen.py`:

```python
"""Synthetische Frame-Reihen (``verschiebung``) für die Tests der Spec 2026-09-25 (Schnittkanten frame-genau).
Wie ``fake_resolve.py`` ein Helfer-Modul, kein Test."""
from __future__ import annotations


def reihe(*stuecke, t0_s: float = 0.0, fps: float = 25.0) -> dict:
    """``verschiebung`` aus Stücken ``(dauer_s, dx, dy[, zitter])``: je Frame konstante Verschiebung in px @480;
    ``zitter`` wechselt dx von Frame zu Frame um ± zitter (Mittel aus |Δdx| und |Δdy| = zitter)."""
    dx: list[float] = []
    dy: list[float] = []
    for st in stuecke:
        dauer, x, y = st[:3]
        zitter = st[3] if len(st) > 3 else 0.0
        for i in range(int(round(dauer * fps))):
            dx.append(round(x + (zitter if i % 2 else -zitter), 2))
            dy.append(round(y, 2))
    return {"fps": fps, "t0_s": t0_s, "dx": dx, "dy": dy}


def rec(*stuecke, t0_s: float = 0.0, zooms: list | None = None, dauer_s: float | None = None) -> dict:
    """Telemetrie-Datensatz mit Reihe, für stabile_bereiche/ruhe_je_frame/kanten_befunde."""
    return {"verschiebung": reihe(*stuecke, t0_s=t0_s), "zooms": list(zooms or []), "dauer_s": dauer_s}
```

- [ ] **Step 2: Failing Unit-Tests** — in `tests/test_telemetrie.py` die Imports um
`from reihen import rec as _rec_reihe` ergänzen; die vier alten Tests
`test_stabile_bereiche_fasst_benachbarte_ruhige_fenster_zusammen`, `test_stabile_bereiche_deckelt_bewegung_und_kappt_an_der_clipdauer`,
`test_stabile_bereiche_folgt_ruhige_fenster_und_verwirft_zu_kurze_laeufe`, `test_stabile_bereiche_ohne_daten_leer`
löschen (`_rec_fenster`/`CFG_STABIL` bleiben bis Task 3, `test_bewegung_max_im_bereich` braucht sie noch);
`test_config_hash_ignoriert_die_stabil_schwellen` und `test_defaults_haben_die_stabil_schwellen` ersetzen; ans Ende:

```python
CFG_FRAME = {**CFG, "bewegung_max": 2.0, "stabil_min_s": 2.0, "glatt_s": 0.4, "kante_s": 0.3}


def test_bewegung_je_frame_betrag_und_wackeln():
    t0, fps, wk, bw = T.bewegung_je_frame(_rec_reihe((2.0, 3.0, 4.0)), 0.4)
    assert (t0, fps, len(bw)) == (0.0, 25.0, 50)
    assert np.allclose(bw, 5.0) and np.allclose(wk, 0.0)            # Betrag √(3² + 4²), keine Änderung je Frame
    _, _, wk2, bw2 = T.bewegung_je_frame(_rec_reihe((2.0, 0.0, 0.0, 0.5)), 0.4)
    assert np.allclose(wk2, 0.5) and np.allclose(bw2, 0.5)         # dx ±0,5 im Wechsel: |Δdx| 1,0, Achsmittel 0,5
    assert T.bewegung_je_frame(_rec_reihe((1.0, 0.0, 0.0), t0_s=3.0), 0.4)[0] == 3.0
    _, _, wk3, bw3 = T.bewegung_je_frame(_rec_reihe((0.12, 1.0, 0.0)), 0.4)   # 3 Frames, kürzer als die Glättung
    assert len(wk3) == len(bw3) == 3 and np.allclose(bw3, 1.0)


def test_bewegung_je_frame_ohne_reihe():
    assert T.bewegung_je_frame(None, 0.4) is None
    assert T.bewegung_je_frame({"verschiebung": None}, 0.4) is None
    assert T.bewegung_je_frame({"verschiebung": {"fps": 25.0, "t0_s": 0.0, "dx": [], "dy": []}}, 0.4) is None


def test_ruhe_je_frame_schwellen_zeitlupe_und_zoom():
    rec = _rec_reihe((2.0, 0.0, 0.0), (2.0, 5.0, 0.0))                   # ab 2,0 s Bewegung 5 px je Frame
    r = T.ruhe_je_frame(rec, CFG_FRAME)
    # 0,4 s Glättung: der Sprung bei Frame 50 (wackeln 2,5) wirkt auf die Frames 46–55, die Bewegung ab Frame 50
    assert np.flatnonzero(r.ruhig).tolist() == list(range(46))
    assert T.ruhe_je_frame(rec, CFG_FRAME, faktor=0.25).ruhig.all()      # tempo 4: sichtbar 1,25 px je Frame
    zoom = _rec_reihe((4.0, 0.0, 0.0), zooms=[{"von_s": 0.4, "bis_s": 0.8, "urteil": "schnell"},
                                             {"von_s": 2.0, "bis_s": 3.0, "urteil": "langsam"}])
    assert np.flatnonzero(~T.ruhe_je_frame(zoom, CFG_FRAME).ruhig).tolist() == list(range(10, 20))
    assert T.ruhe_je_frame({"zooms": []}, CFG_FRAME) is None


def test_ruhe_frames_und_zeit():
    r = T.ruhe_je_frame(_rec_reihe((2.0, 0.0, 0.0), (2.0, 5.0, 0.0)), CFG_FRAME)
    assert r.frames(0.5, 1.0) == slice(13, 25) and r.frames(-1.0, 0.1) == slice(0, 3)
    assert r.frames(3.9, 9.0) == slice(98, 100) and r.zeit(10) == 0.4


def test_stabile_bereiche_frame_genau():
    rec = _rec_reihe((2.4, 0.0, 0.0), (0.8, 5.0, 0.0), (4.8, 0.0, 0.0), dauer_s=8.0)
    # Schwenk 2,4–3,2 s: die Läufe enden 0,16 s davor und beginnen 0,24 s danach (Glättung 0,4 s, Sprung im wackeln)
    assert T.stabile_bereiche(rec, CFG_FRAME) == [[0.0, 2.24, 0.0, 0.0], [3.44, 8.0, 0.0, 0.0]]
    assert T.stabile_bereiche(rec, {**CFG_FRAME, "stabil_min_s": 2.5}) == [[3.44, 8.0, 0.0, 0.0]]
    assert T.stabile_bereiche({**rec, "dauer_s": 7.9}, CFG_FRAME) == [[0.0, 2.24, 0.0, 0.0], [3.44, 7.9, 0.0, 0.0]]
    versetzt = _rec_reihe((2.4, 0.0, 0.0), (0.8, 5.0, 0.0), (4.8, 0.0, 0.0), t0_s=10.0, dauer_s=18.0)
    assert T.stabile_bereiche(versetzt, CFG_FRAME) == [[10.0, 12.24, 0.0, 0.0], [13.44, 18.0, 0.0, 0.0]]


def test_stabile_bereiche_deckel_und_zoom():
    langsam = _rec_reihe((2.4, 0.0, 0.0), (0.8, 1.2, 0.0), (4.8, 0.0, 0.0), dauer_s=8.0)   # Schwenk 1,2 px je Frame
    assert T.stabile_bereiche(langsam, CFG_FRAME) == [[0.0, 8.0, 0.06, 1.2]]
    assert T.stabile_bereiche(langsam, {**CFG_FRAME, "bewegung_max": 1.0}) == [[0.0, 2.56, 0.06, 0.96],
                                                                                 [3.08, 8.0, 0.06, 0.96]]
    zoom = _rec_reihe((6.0, 0.0, 0.0), zooms=[{"von_s": 2.0, "bis_s": 2.6, "urteil": "schnell"}], dauer_s=6.0)
    assert T.stabile_bereiche(zoom, CFG_FRAME) == [[0.0, 2.0, 0.0, 0.0], [2.6, 6.0, 0.0, 0.0]]


def test_stabile_bereiche_ohne_reihe_leer():
    assert T.stabile_bereiche(None, CFG_FRAME) == []
    # alter Datensatz: Fenster ja, Reihe nein → keine Läufe (er ist nach MESS_VERSION ohnehin veraltet)
    assert T.stabile_bereiche({"fenster": [[0.0, 0.05, 0.1, "statisch", None]], "ruhige_fenster": [0.0],
                               "dauer_s": 3.0, "fenster_s": 2.0}, CFG_FRAME) == []


def test_config_hash_ignoriert_die_stabil_schwellen():
    # die Schlüssel ändern keine Messung, nur die Ableitung aus der Reihe → kein neuer Hash, kein Neumessen
    h = T.config_hash(CFG)
    for k, wert in (("bewegung_max", 5.0), ("stabil_min_s", 3.0), ("glatt_s", 0.8)):
        assert T.config_hash({**CFG, k: wert}) == h, k


def test_defaults_haben_die_stabil_schwellen():
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    assert cfg["bewegung_max"] == 2.0 and cfg["stabil_min_s"] == 2.0 and cfg["glatt_s"] == 0.4
    assert cfg["ruhig_max_px"] == 0.15
```

- [ ] **Step 3: Tests schlagen fehl**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests/test_telemetrie.py -q -p no:cacheprovider`
Expected: FAIL (`bewegung_je_frame`/`ruhe_je_frame` fehlen, `glatt_s` fehlt in defaults.yaml).

- [ ] **Step 4: Implementierung in `telemetrie.py`** — Import `from typing import NamedTuple` zu den Imports;
`OHNE_MESSWIRKUNG` um `"glatt_s"` ergänzen (Kommentar darüber: „… und die Ableitung der stabilen Läufe (Spec
2026-09-23/-25; sie rechnet auf der gemessenen Reihe)“); die Funktion `stabile_bereiche` (Z. 705–745) ersetzen durch:

```python
# --- Bewegung je Frame, ruhige Frames, stabile Läufe (Spec 2026-09-25) ----------------------------------------------

def _glatt(x: np.ndarray, breite: int) -> np.ndarray:
    """Gleitendes Mittel einer 1-D-Reihe über ``breite`` Frames, Ränder normiert (wie ``_tiefpass``)."""
    return _tiefpass(np.asarray(x, np.float64)[:, None], breite)[:, 0]


def bewegung_je_frame(rec: dict | None, glatt_s: float) -> tuple[float, float, np.ndarray, np.ndarray] | None:
    """(t0_s, fps, wackeln, bewegung) je Frame aus ``verschiebung``, beide über ``glatt_s`` gemittelt; None ohne Reihe.
    ``wackeln`` = Mittel aus |Δdx| und |Δdy| zum Vorframe (dieselbe Größe wie in den Fenstern; Frame 0 übernimmt den Wert
    von Frame 1), ``bewegung`` = Betrag √(dx² + dy²) — ein reiner Schwenk zählt voll (die Fenster mitteln die Achsen)."""
    v = (rec or {}).get("verschiebung")
    if not v or not v.get("dx") or not v.get("dy"):
        return None
    fps = float(v.get("fps") or ZIEL_FPS)
    n = min(len(v["dx"]), len(v["dy"]))
    dxy = np.stack([np.asarray(v["dx"][:n], np.float64), np.asarray(v["dy"][:n], np.float64)], axis=1)
    wk = np.abs(np.diff(dxy, axis=0)).mean(axis=1)
    wk = np.r_[wk[:1], wk] if len(wk) else np.zeros(n)
    k = max(1, min(n, int(round(float(glatt_s) * fps))))
    return float(v.get("t0_s") or 0.0), fps, _glatt(wk, k), _glatt(np.hypot(dxy[:, 0], dxy[:, 1]), k)


class Ruhe(NamedTuple):
    """Ruhige Frames eines Clips (Spec 2026-09-25); ``wackeln``/``bewegung`` geglättet und mit dem Zeitlupen-Faktor
    skaliert. Frame ``i`` liegt bei ``t0_s + i / fps``."""
    t0_s: float
    fps: float
    ruhig: np.ndarray
    wackeln: np.ndarray
    bewegung: np.ndarray

    def frames(self, von_s: float, bis_s: float) -> slice:
        """Frames mit ``von_s <= t < bis_s``, auf die Reihe gekappt (leer, wenn der Bereich außerhalb liegt)."""
        n = len(self.ruhig)
        a = min(n, max(0, math.ceil((von_s - self.t0_s) * self.fps - 1e-6)))
        b = min(n, max(a, math.ceil((bis_s - self.t0_s) * self.fps - 1e-6)))
        return slice(a, b)

    def zeit(self, i: int) -> float:
        return self.t0_s + i / self.fps


def ruhe_je_frame(rec: dict | None, cfg: dict, faktor: float = 1.0) -> Ruhe | None:
    """Ruhig = ``wackeln·faktor <= ruhig_max_px`` und ``bewegung·faktor <= bewegung_max`` und außerhalb jeder schnellen
    Zoomfahrt ``[von_s, bis_s)``; ``faktor`` = 1 / tempo (Zeitlupe: sichtbare Bewegung). None ohne Reihe."""
    b = bewegung_je_frame(rec, float(cfg["glatt_s"]))
    if b is None:
        return None
    t0, fps, wk, bw = b
    wk, bw = wk * float(faktor), bw * float(faktor)
    ruhig = (wk <= float(cfg["ruhig_max_px"]) + 1e-9) & (bw <= float(cfg["bewegung_max"]) + 1e-9)
    t = t0 + np.arange(len(ruhig)) / fps
    for z in (rec or {}).get("zooms") or []:
        if z.get("urteil") == "schnell":
            ruhig &= ~((t >= float(z["von_s"])) & (t < float(z["bis_s"])))
    return Ruhe(t0, fps, ruhig, wk, bw)


def stabile_bereiche(rec: dict | None, cfg: dict) -> list[list[float]]:
    """Bereiche, die ruhig genug zum Schneiden sind, als ``[von_s, bis_s, wackeln_max, bewegung_max]`` (Spec 2026-09-25,
    löst die Ableitung aus 2-s-Fenstern der Spec 2026-09-23 ab): maximale Folgen ruhiger Frames (``ruhe_je_frame``),
    mindestens ``stabil_min_s`` lang, Grenzen auf den Frame genau, ``bis_s`` auf ``dauer_s`` gekappt; die Höchstwerte
    sind die der geglätteten Reihen im Lauf. Reine Ableitung aus dem Datensatz — keine Messung. Ohne Reihe leer.
    Die Liste ist ein Vorschlag, nie eine Sperre: was davon geschnitten wird, entscheidet der Bildinhalt."""
    r = ruhe_je_frame(rec, cfg)
    if r is None:
        return []
    kanten = np.diff(np.concatenate([[0], r.ruhig.astype(np.int8), [0]]))
    dauer = (rec or {}).get("dauer_s")
    out = []
    for a, b in zip(np.flatnonzero(kanten == 1).tolist(), np.flatnonzero(kanten == -1).tolist()):
        von, bis = r.zeit(a), r.zeit(b)
        if dauer is not None:
            bis = min(bis, float(dauer))
        if bis - von < float(cfg["stabil_min_s"]) - 1e-6:
            continue
        out.append([round(von, 2), round(bis, 2), round(float(r.wackeln[a:b].max()), 3),
                    round(float(r.bewegung[a:b].max()), 3)])
    return out
```

- [ ] **Step 5: `defaults.yaml`** — die Zeilen ab `# Stabile Bereiche für die B-Roll-Auswahl (Spec 2026-09-23)` bis
einschließlich `stabil_min_s: 2.0 …` ersetzen durch:

```yaml
  # Stabile Läufe und Schnittkanten (Spec 2026-09-25, löst die 2-s-Fenster der Spec 2026-09-23 ab): ruhige Frames
  # aus der Reihe ``verschiebung``. Die Schlüssel ändern keine Messung, nur die Ableitung → OHNE_MESSWIRKUNG,
  # ein Neusetzen erzwingt kein Neumessen (danach autocut_index_sections.py, kostenlos aus dem Cache).
  bewegung_max: 2.0         # Obergrenze der Bewegung je Frame (Betrag √(dx²+dy²), px @480, über glatt_s geglättet)
                            # für ruhige Frames — UNKALIBRIERT bis zur Review-Runde Schnittkanten (Klebl 25.09.:
                            # die vier Wackler fallen bei 1,0–2,0 raus; WLC FX3_8660, vom User „gut“, hat 2,9)
  stabil_min_s: 2.0         # kürzester stabiler Lauf = kürzester Shot aus broll.shot_len_s
  glatt_s: 0.4              # Glättung der Reihen je Frame (wackeln, Bewegung) für Läufe und Kantenprüfung
```

- [ ] **Step 6: Unit-Tests grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests/test_telemetrie.py -q -p no:cacheprovider`
Expected: PASS.

- [ ] **Step 7: Stufe 2b und Prüfer kennen `glatt_s`** — in `index_sections.py` (`telemetrie_anwenden`) wird
`sq = {...}` zu

```python
        sq = {"ruhig_max_px": float(tcfg["ruhig_max_px"]), "bewegung_max": float(tcfg["bewegung_max"]),
              "stabil_min_s": float(tcfg["stabil_min_s"]), "glatt_s": float(tcfg["glatt_s"]),
              "config_hash": tele.get("config_hash"), "laeufe": laeufe}
```
und im Docstring „mit den drei Schwellen“ → „mit den vier Schwellen (samt ``glatt_s``)“. In `broll_layout.py`
(Z. 922–924) wird die Bedingung

```python
        elif (float(sq.get("bewegung_max", tcfg["bewegung_max"])) != float(tcfg["bewegung_max"])
              or float(sq.get("stabil_min_s", tcfg["stabil_min_s"])) != float(tcfg["stabil_min_s"])
              or float(sq.get("glatt_s", tcfg["glatt_s"])) != float(tcfg["glatt_s"])):
```
und der Kommentar darüber nennt `bewegung_max/stabil_min_s/glatt_s`.

- [ ] **Step 8: Tests von Stufe 2b auf Reihen umstellen** — in `tests/test_index_sections.py`:
  - Import `from reihen import reihe as _reihe`;
  - `_CFG_T["telemetrie"]` und `_TCFG` bekommen `"glatt_s": 0.4`;
  - `_TELE_STABIL` bekommt `"verschiebung": _reihe((4.6, 0.0, 0.0), (0.8, 5.0, 0.0), (2.6, 0.0, 0.0)), "zooms": []`
    (Kommentar darüber: „Reihe je Frame: 0–4,6 s ruhig, 4,6–5,4 s Schwenk 5 px je Frame, 5,4–8 s ruhig → Läufe
    0–4,44 s und 5,64–8,0 s (Glättung 0,4 s, Spec 2026-09-25)“);
  - `_TELE_LAUF` bekommt `"verschiebung": _reihe((12.0, 5.0, 0.0), (6.0, 0.0, 0.0), (2.0, 5.0, 0.0)), "zooms": []`
    (Kommentar: „EIN gemessener Lauf 12,24–17,84 s“);
  - die Erwartungen werden:

```python
def test_telemetrie_anwenden_schreibt_stabil_je_abschnitt():
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 4, "verwendbar": True},
                          {"von_s": 4, "bis_s": 8, "verwendbar": False}]}
    neu, geaendert = S.telemetrie_anwenden(rec, _TELE_STABIL, 2.0, _TCFG)
    assert geaendert is True
    # Clip-Läufe 0–4,44 s und 5,64–8,0 s (der Schwenk 4,6–5,4 s trennt sie), auf die Abschnitte geschnitten
    assert neu["abschnitte"][0]["stabil"] == [[0.0, 4.0, 0.0, 0.0]]
    # 4,0–4,44 s ist nur 0,44 s lang, bleibt aber: der Lauf 0–4,44 s beginnt im Nachbarabschnitt (Schluss-Review I3)
    assert neu["abschnitte"][1]["stabil"] == [[4.0, 4.44, 0.0, 0.0], [5.64, 8.0, 0.0, 0.0]]
    assert neu["stabil_quelle"] == {"ruhig_max_px": 0.15, "bewegung_max": 2.0, "stabil_min_s": 2.0, "glatt_s": 0.4,
                                    "config_hash": "abc123abc123",
                                    "laeufe": [[0.0, 4.44, 0.0, 0.0], [5.64, 8.0, 0.0, 0.0]]}


def test_telemetrie_anwenden_laesst_nur_stuecke_ohne_laenge_weg():
    """Schluss-Review I3 (Task 8): ein kurzes Stück bleibt — Abschnitt 3,5–4,44 s trifft den Lauf 0–4,44 s nur 0,94 s
    lang, die Mindestlänge gilt aber für den Lauf, nicht für das Stück. Weg fällt nur ein Stück ohne Länge: der
    Abschnitt 4,44–7 s berührt den Lauf 0–4,44 s nur im Punkt 4,44."""
    rec = {"abschnitte": [{"von_s": 3.5, "bis_s": 4.44, "verwendbar": False},
                          {"von_s": 4.44, "bis_s": 7.0, "verwendbar": False}]}
    neu, _ = S.telemetrie_anwenden(rec, _TELE_STABIL, 2.0, _TCFG)
    assert neu["abschnitte"][0]["stabil"] == [[3.5, 4.44, 0.0, 0.0]]
    assert neu["abschnitte"][1]["stabil"] == [[5.64, 7.0, 0.0, 0.0]]
```
    In `test_telemetrie_anwenden_randstueck_bleibt_und_laeufe_ungeschnitten` werden die Erwartungen
    `[[12.24, 13.0, 0.0, 0.0]]`, `[[13.0, 17.84, 0.0, 0.0]]` und `laeufe == [[12.24, 17.84, 0.0, 0.0]]` (Docstring:
    „EIN Lauf 12,24–17,84 s“). In `test_index_sections_clip_traegt_stabil_bei_cache_treffer_nach`: `stabil` beide Male
    `[[0.0, 4.0, 0.0, 0.0]]`, `laeufe == [[0.0, 4.44, 0.0, 0.0], [5.64, 8.0, 0.0, 0.0]]`. In
    `test_index_sections_clip_traegt_laeufe_bei_altem_datensatz_nach`: `out["abschnitte"][0]["stabil"] ==
    [[4.0, 4.44, 0.0, 0.0], [5.64, 8.0, 0.0, 0.0]]`, `laeufe == [[0.0, 4.44, 0.0, 0.0], [5.64, 8.0, 0.0, 0.0]]`.

- [ ] **Step 9: Test für die geänderte Glättung** — in `tests/test_broll_layout.py` `CFG_TELEMETRIE` um
`"glatt_s": 0.4` ergänzen und hinter `test_verify_layout_warnt_bei_anderen_stabil_schwellen` einfügen:

```python
def test_verify_layout_warnt_bei_anderer_glaettung():
    """glatt_s steht wie bewegung_max in OHNE_MESSWIRKUNG: der Hash bleibt, die Läufe sind trotzdem veraltet."""
    idx = _idx_abschnitts_maengel([], [])
    idx["clips"][0]["stabil_quelle"]["glatt_s"] = 0.4
    cfg = {**CFG, "telemetrie": {**CFG_TELEMETRIE, "glatt_s": 0.8}}
    plan = _plan({1: [("Flur/FX3_1.MP4", 1.0, 4.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    res = L.verify_layout(plan, TP, idx, CL, cfg, 25, [_tele("FX3_1.MP4", 25.0)])
    assert any("anderen Stabil-Schwellen abgeleitet" in w for w in res.warnings)
```

- [ ] **Step 10: Fixture-Generator umbauen** — `tools/autocut/tests/fixtures/gen_bereiche_fixture.py` komplett ersetzen:

```python
"""Erzeugt die Fixtures bereiche-urteile.json, bereiche-wlc.json und bereiche-klebl.json (Spec 2026-09-25).

Einmalig von Hand laufen lassen, NICHT im Testlauf: die Clips liegen auf dem NAS (nur lesen), Auswahl und Urteile in
projects/ (NAS-Spiegel, nicht im Repo). Jeder Clip wird mit ``clip_messen()`` und der ausgelieferten Konfiguration
(defaults.yaml) neu gemessen — die Chargen bleiben unberührt. Gelesen wird aus dem HAUPTORDNER des Repos (Worktrees
haben kein projects/), geschrieben wird neben diese Datei.

    tools/autocut/venv/bin/python tools/autocut/tests/fixtures/gen_bereiche_fixture.py

Quellen:
  projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/autocut/telemetrie.json  (Pfade)
  projects/WLC/Recruiting/2026-07 Erster Dreh/_intern/autocut/telemetrie.json                                  (Pfade)
  projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schwenks/_intern/{beispiele,urteile}{,2}.json
  projects/Klebl/Recruiting-Videos/2026-09 Dreh Edeka Baustelle 22.09/_intern/autocut/video-*/broll_build.json

Reihe und Fenster der 30 Urteile und der 32 Klebl-Shots werden auf den Bereich ± 3 s beschnitten (``t0_s``; die
Läufe im Bereich bleiben dieselben, solange der Rand über ``stabil_min_s`` liegt), die vier WLC-Clips bleiben
vollständig. Die MEK- und WLC-Aufnahmen lagen beim ersten Messen auf der SSD NIRO-SSD-03 — ohne sie gilt dieselbe
Datei auf dem NAS.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parents[1] / "src"))

from niro_autocut.charge import load_config  # noqa: E402
from niro_autocut.telemetrie import clip_messen  # noqa: E402


def studio_wurzel() -> Path:
    """Hauptordner des Repos. NICHT relativ zu dieser Datei bestimmen: in einem Worktree gibt es kein
    projects/ (CLAUDE.md, „Chargen-Daten nur im Hauptordner des Repos lesen und schreiben"). Die erste
    Zeile von `git worktree list --porcelain` nennt den Hauptordner, auch aus einem Worktree heraus."""
    aus = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=HIER,
                         capture_output=True, text=True, check=True).stdout
    return Path(aus.splitlines()[0].removeprefix("worktree "))


STUDIO = studio_wurzel()
MEK = STUDIO / "projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/autocut/telemetrie.json"
WLC = STUDIO / "projects/WLC/Recruiting/2026-07 Erster Dreh/_intern/autocut/telemetrie.json"
KAL = STUDIO / "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schwenks/_intern"
KLEBL = STUDIO / "projects/Klebl/Recruiting-Videos/2026-09 Dreh Edeka Baustelle 22.09/_intern/autocut"
KLEBL_VIDEOS = ("video-1-tiefbau", "video-2-hoch-und-fertigteilbau")
RAND_S = 3.0
FELDER = ("clip", "dauer_s", "fenster_s", "fenster", "ruhige_fenster", "config_hash", "haltung", "wackeln", "zooms",
          "verschiebung")
CFG = load_config(Path("/nirgendwo"))["telemetrie"]
NAS_KUNDEN = "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
UMLEITUNG = {"/Volumes/NIRO-SSD-03/01_Projekt-2xAds1xImagefilm_24.06.26/":
             NAS_KUNDEN + "Marien-Elisabeth-Kliniken Kassel gGmbH/02_Projekte/01_Projekt-2xAds1xImagefilm_24.06.26/",
             "/Volumes/NIRO-SSD-03/WLC Würth Logistik GmbH & CO KG/": NAS_KUNDEN + "WLC Würth Logistik GmbH & CO KG/"}

# Die Bereiche, die der User am 23.09. im Review genannt hat (Protokoll der WLC-Charge)
WLC_BEREICHE = {"FX3_8636": [[4.5, 7.5]], "FX3_8641": [[1.5, 4.0]], "FX3_8660": [[12.5, 15.5]],
                "FX3_8663": [[9.0, 12.0], [63.5, 66.5]]}


def _laden(p: Path) -> dict:
    if not p.is_file():
        raise SystemExit(f"{p} fehlt — Charge vom NAS holen (sh tools/studio_abgleich.sh --charge ...).")
    return {r["clip"]: r for r in json.loads(p.read_text(encoding="utf-8"))}


def _medienpfad(p: str) -> Path:
    if Path(p).exists():
        return Path(p)
    for von, nach in UMLEITUNG.items():
        if p.startswith(von) and Path(nach + p[len(von):]).exists():
            return Path(nach + p[len(von):])
    raise SystemExit(f"{p} nicht erreichbar — NAS gemountet?")


def _messen(p: str) -> dict:
    rec = clip_messen(_medienpfad(p), CFG)
    if rec.get("fehler") or not rec.get("verschiebung"):
        raise SystemExit(f"{p}: Messung ohne Reihe ({rec.get('fehler') or rec.get('quelle')})")
    print(f"  gemessen {Path(p).name}", flush=True)
    return rec


def _schlank(rec: dict, von_s: float | None = None, bis_s: float | None = None) -> dict:
    out = {k: rec.get(k) for k in FELDER}
    if von_s is not None:
        a, z = max(0.0, von_s - RAND_S), bis_s + RAND_S
        out["fenster"] = [f for f in out["fenster"] if a <= f[0] <= z]
        out["ruhige_fenster"] = [t for t in out["ruhige_fenster"] if a <= t <= z]
        v = out["verschiebung"]
        i, j = int(round(a * v["fps"])), int(round(z * v["fps"]))
        out["verschiebung"] = {**v, "t0_s": round(i / v["fps"], 2), "dx": v["dx"][i:j], "dy": v["dy"][i:j]}
    return out


def urteile() -> list[dict]:
    mek = _laden(MEK)
    raus = []
    for runde, suffix in ((1, ""), (2, "2")):
        beispiele = json.loads((KAL / f"beispiele{suffix}.json").read_text(encoding="utf-8"))
        urteil = json.loads((KAL / f"urteile{suffix}.json").read_text(encoding="utf-8"))
        for b in beispiele:
            u = urteil[str(b["nr"])]
            von_s = float(b["quelle_start_s"])
            raus.append({"nr": f"R{runde}#{b['nr']}",
                         "urteil": u if isinstance(u, str) else u["urteil"],
                         "anmerkung": "" if isinstance(u, str) else u.get("anmerkung", ""),
                         "von_s": von_s, "bis_s": von_s + 5.0,
                         "telemetrie": _schlank(_messen(mek[b["clip"]]["path"]), von_s, von_s + 5.0)})
    return raus


def wlc() -> list[dict]:
    tel = _laden(WLC)
    return [{"clip": c, "bereiche_user": b, "telemetrie": _schlank(_messen(tel[c]["path"]))}
            for c, b in WLC_BEREICHE.items()]


def klebl() -> list[dict]:
    """Die 32 gebauten B-Roll-Shots des Klebl-Nachtlaufs 24./25.09. (Anlass der Spec), Quellbereich wie gebaut."""
    raus, gemessen = [], {}
    for video in KLEBL_VIDEOS:
        bau = json.loads((KLEBL / video / "broll_build.json").read_text(encoding="utf-8"))
        for p in bau["placed"]:
            if p["clip"] not in gemessen:
                gemessen[p["clip"]] = _messen(p["clip"])
            von_s, bis_s = p["src_in_f"] / p["clip_fps"], p["src_out_f"] / p["clip_fps"]
            raus.append({"video": video, "rec_s": round(p["rec_in_f"] / 25.0, 2), "clip": p["name"],
                         "von_s": round(von_s, 3), "bis_s": round(bis_s, 3), "tempo": int(p["tempo"]),
                         "telemetrie": _schlank(gemessen[p["clip"]], von_s, bis_s)})
    return raus


def _schreiben(p: Path, daten: list[dict]) -> None:
    """JSON mit Einrückung, Zahlenlisten (Reihen, Bereiche) aber je in einer Zeile — sonst eine Zahl je Zeile."""
    text = json.dumps(daten, ensure_ascii=False, indent=1)
    text = re.sub(r"\[\s+([-0-9.,\s]+?)\s+\]", lambda m: "[" + re.sub(r"\s+", "", m.group(1)) + "]", text)
    p.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    for name, erzeugen in (("bereiche-urteile.json", urteile), ("bereiche-wlc.json", wlc),
                           ("bereiche-klebl.json", klebl)):
        print(name, flush=True)
        daten = erzeugen()
        p = HIER / name
        _schreiben(p, daten)
        print(f"{p.name}: {len(daten)} Einträge, {p.stat().st_size // 1024} KB")
```

- [ ] **Step 11: Fixtures erzeugen** (liest vom NAS, ca. 3–5 min; NAS muss gemountet sein)

Run: `tools/autocut/venv/bin/python tools/autocut/tests/fixtures/gen_bereiche_fixture.py`
Expected: `bereiche-urteile.json: 30 Einträge`, `bereiche-wlc.json: 4 Einträge`, `bereiche-klebl.json: 32 Einträge`,
zusammen unter 400 KB.

- [ ] **Step 12: Abnahme frame-genau** — `tests/test_bereiche_abnahme.py` komplett ersetzen:

```python
"""Abnahme der stabilen Läufe (frame-genau, Spec 2026-09-25) gegen die 30 Urteile vom 22.09., die vier WLC-Clips vom
23.09. und die 32 Klebl-Shots vom 25.09.

Die Tests lesen die Schwellen aus defaults.yaml — jede Änderung an ruhig_max_px, bewegung_max, glatt_s oder
stabil_min_s muss hier wieder antreten. Exakte Läufe und Mengen sind Änderungsmelder (gemessene Werte), keine Urteile;
bewegung_max ist bis zur Review-Runde Schnittkanten UNKALIBRIERT (2,0).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from niro_autocut import telemetrie as T
from niro_autocut.charge import load_config

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CFG = load_config(Path("/nirgendwo"))["telemetrie"]
KLEBL_IM_LAUF = {"FX3_0232.MP4", "FX3_0235.MP4", "FX3_0241.MP4", "FX3_0244.MP4", "FX3_0257.MP4", "FX3_0261.MP4",
                 "FX3_0265.MP4", "FX3_0274.MP4", "FX3_0282.MP4", "FX3_0648.MP4", "FX3_0662.MP4", "FX3_0668.MP4",
                 "FX3_0671.MP4", "FX3_0673.MP4", "FX3_0677.MP4", "FX3_0678.MP4", "FX3_0680.MP4", "FX3_0690.MP4",
                 "FX3_0699.MP4", "FX3_0701.MP4", "FX3_0713.MP4"}


def _json(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _im_lauf(tele: dict, von: float, bis: float) -> bool:
    return any(a - 1e-6 <= von and bis <= z + 1e-6 for a, z, _wk, _bw in T.stabile_bereiche(tele, CFG))


def _kandidaten(e: dict) -> list[tuple[float, float]]:
    """Läufe im 5-s-Beispiel, auf das Beispiel geschnitten; zu kurze Schnitte zählen nicht."""
    out = []
    for a, z, _wk, _bw in T.stabile_bereiche(e["telemetrie"], CFG):
        x, y = max(a, e["von_s"]), min(z, e["bis_s"])
        if y - x >= float(CFG["stabil_min_s"]) - 1e-6:
            out.append((round(x, 2), round(y, 2)))
    return out


def test_fixtures_tragen_reihen_je_frame():
    for name in ("bereiche-urteile.json", "bereiche-wlc.json", "bereiche-klebl.json"):
        for e in _json(name):
            v = e["telemetrie"]["verschiebung"]
            assert v["fps"] == 25.0 and len(v["dx"]) == len(v["dy"]) > 0, (name, e.get("nr") or e["clip"])


def test_fixture_traegt_die_dreissig_urteile():
    alle = _json("bereiche-urteile.json")
    assert len(alle) == 30
    assert sum(1 for e in alle if e["urteil"] == "ungewollt") == 24
    assert sum(1 for e in alle if e["urteil"].startswith("gewollt")) == 6


def test_abnahme_kein_lauf_im_komplett_ungewollten_beispiel():
    """Hartes Kriterium 1: R2#12 hat der User ausdrücklich „komplett ungewollt" genannt."""
    e = next(x for x in _json("bereiche-urteile.json") if x["nr"] == "R2#12")
    assert e["anmerkung"] == "komplett ungewollt"
    assert _kandidaten(e) == []


def test_abnahme_hoechstens_zwei_laeufe_in_ungewolltem_material():
    """Hartes Kriterium 2: höchstens 2 der 24 „ungewollt"-Beispiele dürfen einen Lauf bekommen."""
    treffer = [e["nr"] for e in _json("bereiche-urteile.json") if e["urteil"] == "ungewollt" and _kandidaten(e)]
    assert len(treffer) <= 2, f"zu viele Läufe in „ungewollt“-Material: {treffer}"
    assert treffer == ["R2#14"]                     # Änderungsmelder (bewegung_max 2,0)


def test_abnahme_wlc_laeufe_unveraendert():
    """Gegen gemessene Werte, damit eine Schwellenänderung sichtbar wird statt still durchzugehen."""
    erwartet = {"FX3_8636": [[0.0, 11.52]], "FX3_8641": [[0.0, 4.56]], "FX3_8660": [[7.16, 10.24], [13.76, 18.36]],
                "FX3_8663": [[8.36, 15.92], [35.8, 40.44], [41.64, 45.84], [54.04, 59.0], [62.4, 71.12],
                             [71.72, 78.72]]}
    for e in _json("bereiche-wlc.json"):
        assert [[a, z] for a, z, _wk, _bw in T.stabile_bereiche(e["telemetrie"], CFG)] == erwartet[e["clip"]], e["clip"]


@pytest.mark.parametrize("clip,von,bis", [("FX3_8636", 4.5, 7.5), ("FX3_8641", 1.5, 4.0), ("FX3_8663", 9.0, 12.0),
                                          ("FX3_8663", 63.5, 66.5)])
def test_abnahme_wlc_bereiche_des_users_liegen_in_einem_lauf(clip, von, bis):
    e = next(x for x in _json("bereiche-wlc.json") if x["clip"] == clip)
    assert _im_lauf(e["telemetrie"], von, bis)


@pytest.mark.xfail(strict=True, reason="FX3_8660 beginnt bei 12,5 s im Auslauf eines Schwenks (2,9 px/Frame) — ob "
                                       "das an der Kante reicht, entscheidet die Review-Runde Schnittkanten")
def test_abnahme_wlc_fx3_8660_liegt_in_einem_lauf():
    e = next(x for x in _json("bereiche-wlc.json") if x["clip"] == "FX3_8660")
    assert _im_lauf(e["telemetrie"], 12.5, 15.5)


def test_abnahme_klebl_die_vier_wackler_liegen_in_keinem_lauf():
    """Anlass der Spec: diese vier lagen in Läufen aus 2-s-Fenstern und wackelten doch."""
    shots = {s["clip"]: s for s in _json("bereiche-klebl.json")}
    for clip in ("FX3_0260.MP4", "FX3_0700.MP4", "FX3_0653.MP4", "FX3_0267.MP4"):
        s = shots[clip]
        assert not _im_lauf(s["telemetrie"], s["von_s"], s["bis_s"]), clip


def test_abnahme_klebl_shots_in_einem_lauf_unveraendert():
    shots = _json("bereiche-klebl.json")
    assert len(shots) == 32
    drin = {s["clip"] for s in shots if _im_lauf(s["telemetrie"], s["von_s"], s["bis_s"])}
    assert drin == KLEBL_IM_LAUF                   # Änderungsmelder (bewegung_max 2,0)
```

- [ ] **Step 13: FX3_8660-Ende-zu-Ende-Test auf die neuen Läufe** — in `tests/test_broll_layout.py`
`test_verify_layout_i3_ende_zu_ende_an_fx3_8660` ersetzen durch:

```python
def test_verify_layout_i3_ende_zu_ende_an_fx3_8660():
    """Schluss-Review I3 an echten Werten, seit Spec 2026-09-25 frame-genau: FX3_8660 (WLC,
    tests/fixtures/bereiche-wlc.json) hat bei bewegung_max 2,0 die Läufe 7,16–10,24 s und 13,76–18,36 s. Mit
    verworfenen Abschnitten 8–15 und 15–18,72 s (Grenze mitten im zweiten Lauf) schreibt Stufe 2b die Stücke, und der
    Prüfer lässt den Shot 14,0–17,0 s über die Abschnittsgrenze durch — er liegt in EINEM gemessenen Lauf."""
    e = next(x for x in json.loads(WLC_FIXTURE.read_text(encoding="utf-8")) if x["clip"] == "FX3_8660")
    idx = _idx()
    c = idx["clips"][0]
    tele = {**e["telemetrie"], "path": c["path"], "quelle": "rtmd", "fehler": None,
            "config_hash": TM.config_hash(CFG_TELEMETRIE)}
    vorlage = dict(c["abschnitte"][0])
    c.update(dauer_s=18.72, maengel=["Wackler"],
             abschnitte=[{**vorlage, "von_s": 8.0, "bis_s": 15.0, "verwendbar": False, "maengel": ["Wackler"]},
                         {**vorlage, "von_s": 15.0, "bis_s": 18.72, "verwendbar": False, "maengel": ["Wackler"]}])
    idx["clips"][0], _ = S.telemetrie_anwenden(c, tele, 2.0, CFG_TELEMETRIE)
    assert idx["clips"][0]["stabil_quelle"]["laeufe"] == [[7.16, 10.24, 0.125, 1.892], [13.76, 18.36, 0.142, 1.985]]
    plan = _plan({1: [("Flur/FX3_1.MP4", 14.0, 17.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    res = L.verify_layout(plan, TP, idx, CL, WACKLER_GESPERRT, 25, [tele])
    assert _fehler_fx3_1(res, "verwendbaren Abschnitt", "Mangel") == [], res.errors
```

Hinweis: Die erwarteten Läufe (Step 12, 13) und Mengen stammen aus der Referenzrechnung vom 25.09. an denselben
Clips. Weicht eine Grenze im neu erzeugten Fixture um höchstens einen Frame (0,04 s) oder ein Höchstwert in der
dritten Stelle ab (Rundung der Reihe), gilt der Wert aus dem Fixture — die Abweichung im Commit nennen. Größere
Abweichungen: stoppen und melden.

- [ ] **Step 14: Alles grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests -q -p no:cacheprovider`
Expected: alle PASS, 1 skipped, 1 xfailed.

- [ ] **Step 15: Commit**

```bash
git add tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/src/niro_autocut/index_sections.py \
        tools/autocut/src/niro_autocut/broll_layout.py tools/autocut/defaults.yaml tools/autocut/tests/reihen.py \
        tools/autocut/tests/test_telemetrie.py tools/autocut/tests/test_index_sections.py \
        tools/autocut/tests/test_broll_layout.py tools/autocut/tests/test_bereiche_abnahme.py \
        tools/autocut/tests/fixtures/gen_bereiche_fixture.py tools/autocut/tests/fixtures/bereiche-*.json
git commit -m "feat(autocut): stabile Läufe frame-genau aus der Reihe je Frame

Ruhig = wackeln und Bewegungsbetrag unter der Schwelle, über glatt_s geglättet, ohne schnelle Zoomfahrt;
Läufe auf den Frame genau. Fixtures vom NAS neu gemessen, Abnahme gegen Urteile, WLC und Klebl.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 3: Kantenprüfung in `verify_layout()`

**Files:**
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (neu: `Kante`, `_kanten`, `kanten_befunde`, `ruhige_lage`;
  entfernt: `bewegung_grundniveau`, `bewegung_max_im_bereich`; `OHNE_MESSWIRKUNG`)
- Modify: `tools/autocut/defaults.yaml` (`bewegung_rand_s`, `bewegung_spitze_faktor` raus, `kante_s` rein)
- Modify: `tools/autocut/src/niro_autocut/broll_layout.py` (Pflichtschlüssel Z. 676; Block Z. 792–827; neue Helfer
  `_vorschlag`, `_kanten_pruefen`)
- Test: `tests/test_telemetrie.py`, `tests/test_broll_layout.py`, `tests/test_bereiche_abnahme.py`

**Interfaces:**
- Consumes (Task 2): `ruhe_je_frame`, `Ruhe.frames/zeit`, `reihen.reihe/rec`.
- Produces: `class Kante(NamedTuple)`: `seite: str` („in“|„out“|„mitte“), `von_s`, `bis_s`, `wackeln`, `bewegung`
  (je 2 Stellen), `gemessen: bool = True`; `kanten_befunde(rec, cfg, von_s, bis_s, faktor=1.0) -> list[Kante] | None`;
  `ruhige_lage(rec, cfg, von_s, bis_s, faktor, grenzen: tuple[float, float]) -> float | None` (Verschiebung in s);
  Config `kante_s`; Meldungen „In-/Out-Punkt liegt in Bewegung (…) — …“, „Bewegung im Shot bei …“,
  „In-/Out-Punkt ohne Messung …“.

- [ ] **Step 1: Failing Tests für die Funktionen** — in `tests/test_telemetrie.py` löschen:
`test_neue_schluessel_aendern_den_config_hash_nicht`, `test_bewegung_grundniveau_nimmt_nur_entfernte_fenster`,
`test_bewegung_max_im_bereich`, den Helfer `_rec_fenster` und `CFG_STABIL` (samt Kommentarblock „Stabile Bereiche
(Spec 2026-09-23)“ darüber, falls danach leer); in `test_config_hash_ignoriert_die_stabil_schwellen` das Tupel um
`("kante_s", 0.5)` ergänzen; `test_defaults_haben_die_stabil_schwellen` bekommt zusätzlich
`assert cfg["kante_s"] == 0.3 and "bewegung_rand_s" not in cfg and "bewegung_spitze_faktor" not in cfg`. Ans Ende:

```python
def test_kanten_befunde_kante_mitte_und_ruhig():
    rec = _rec_reihe((2.0, 0.0, 0.0), (2.0, 5.0, 0.0), (4.0, 0.0, 0.0))        # Schwenk 2,0–4,0 s
    assert T.kanten_befunde(rec, CFG_FRAME, 5.0, 7.5) == []
    assert T.kanten_befunde(rec, CFG_FRAME, 3.0, 6.0) == [
        T.Kante("in", 3.0, 3.32, 0.0, 5.0), T.Kante("mitte", 3.32, 4.24, 0.25, 5.0)]
    assert T.kanten_befunde(rec, CFG_FRAME, 0.5, 2.5) == [
        T.Kante("out", 2.2, 2.52, 0.25, 5.0), T.Kante("mitte", 1.84, 2.2, 0.25, 4.5)]
    assert T.kanten_befunde(rec, CFG_FRAME, 3.0, 6.0, faktor=0.25) == []          # tempo 4: sichtbar 1,25 px je Frame
    assert T.kanten_befunde({"zooms": []}, CFG_FRAME, 0.0, 1.0) is None


def test_kanten_befunde_kurzer_shot_und_kante_ohne_messung():
    rec = _rec_reihe((2.0, 0.0, 0.0), (2.0, 5.0, 0.0), (4.0, 0.0, 0.0))
    # 0,5 s: die Kanten sind je 0,25 s lang und stoßen aneinander, eine Mitte gibt es nicht
    assert T.kanten_befunde(rec, CFG_FRAME, 3.6, 4.1) == [
        T.Kante("in", 3.6, 3.88, 0.25, 5.0), T.Kante("out", 3.88, 4.12, 0.25, 4.0)]
    kurz = _rec_reihe((2.0, 0.0, 0.0))                                           # Reihe endet bei 2,0 s
    assert T.kanten_befunde(kurz, CFG_FRAME, 1.9, 2.4) == [T.Kante("out", 2.15, 2.4, 0.0, 0.0, gemessen=False)]


def test_ruhige_lage_spaeter_frueher_zoom_und_keine():
    spaeter = _rec_reihe((2.0, 5.0, 0.0), (6.0, 0.0, 0.0))                       # Schwenk am Anfang
    assert T.ruhige_lage(spaeter, CFG_FRAME, 1.5, 3.5, 1.0, (0.0, 8.0)) == 0.72
    assert T.ruhige_lage(spaeter, CFG_FRAME, 1.5, 3.5, 1.0, (0.0, 3.6)) is None     # erlaubter Bereich zu knapp
    frueher = _rec_reihe((6.0, 0.0, 0.0), (2.0, 5.0, 0.0))                       # Schwenk am Ende
    assert T.ruhige_lage(frueher, CFG_FRAME, 4.5, 6.5, 1.0, (0.0, 8.0)) == -0.68
    zoom = _rec_reihe((8.0, 0.0, 0.0), zooms=[{"von_s": 3.0, "bis_s": 4.0, "urteil": "schnell"}])
    assert T.ruhige_lage(zoom, CFG_FRAME, 3.2, 5.2, 1.0, (0.0, 8.0)) == 0.8        # hinter die schnelle Zoomfahrt
    assert T.ruhige_lage({"zooms": []}, CFG_FRAME, 0.0, 2.0, 1.0, (0.0, 8.0)) is None
```

- [ ] **Step 2: Tests schlagen fehl**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests/test_telemetrie.py -q -p no:cacheprovider -k "kanten or ruhige_lage or stabil_schwellen"`
Expected: FAIL (`Kante`/`kanten_befunde`/`ruhige_lage` fehlen, `kante_s` fehlt).

- [ ] **Step 3: Funktionen in `telemetrie.py`** — hinter `stabile_bereiche` einfügen:

```python
class Kante(NamedTuple):
    """Nicht ruhige Frames an einer Schnittkante (``in``/``out``) oder in der Mitte eines Shots (Spec 2026-09-25):
    vom ersten bis nach dem letzten solchen Frame (Quellsekunden), Höchstwerte sichtbar (× Faktor), je 2 Stellen.
    ``gemessen`` False = die Reihe reicht nicht bis an die Kante."""
    seite: str
    von_s: float
    bis_s: float
    wackeln: float
    bewegung: float
    gemessen: bool = True


def _kanten(r: Ruhe, kante_s: float, von_s: float, bis_s: float) -> list[Kante]:
    """Befunde in [von_s, bis_s]: Kanten je ``kante_s`` Quelle (bei kurzen Shots die Hälfte), dazwischen die Mitte."""
    kante = min(kante_s, (bis_s - von_s) / 2)
    out: list[Kante] = []
    for seite, a, b in (("in", von_s, von_s + kante), ("out", bis_s - kante, bis_s),
                        ("mitte", von_s + kante, bis_s - kante)):
        if b - a <= 1e-9:
            continue
        s = r.frames(a, b)
        if s.stop <= s.start:
            if seite != "mitte":
                out.append(Kante(seite, round(a, 2), round(b, 2), 0.0, 0.0, gemessen=False))
            continue
        unruhig = np.flatnonzero(~r.ruhig[s]) + s.start
        if len(unruhig):
            i, j = int(unruhig[0]), int(unruhig[-1]) + 1
            out.append(Kante(seite, round(r.zeit(i), 2), round(r.zeit(j), 2),
                             round(float(r.wackeln[i:j].max()), 2), round(float(r.bewegung[i:j].max()), 2)))
    return out


def kanten_befunde(rec: dict | None, cfg: dict, von_s: float, bis_s: float,
                   faktor: float = 1.0) -> list[Kante] | None:
    """Nicht ruhige Frames eines genutzten Quellbereichs [von_s, bis_s]: je Schnittkante (``kante_s``·faktor Quelle,
    ``kante_s`` in Timeline-Sekunden) und in der Mitte (Spec 2026-09-25). ``faktor`` = 1 / tempo. Leer = alles ruhig;
    None ohne Reihe."""
    r = ruhe_je_frame(rec, cfg, faktor)
    if r is None:
        return None
    return _kanten(r, float(cfg["kante_s"]) * float(faktor), von_s, bis_s)


def ruhige_lage(rec: dict | None, cfg: dict, von_s: float, bis_s: float, faktor: float,
                grenzen: tuple[float, float]) -> float | None:
    """Kleinste Verschiebung (Frame-Schritte der Reihe, bei gleichem Abstand die spätere) des Bereichs [von_s, bis_s],
    nach der beide Schnittkanten gemessen ruhig sind, keine schnelle Zoomfahrt darin liegt und der Bereich in
    ``grenzen`` bleibt; None, wenn es keine gibt oder die Reihe fehlt (Spec 2026-09-25: Vorschlag, keine Automatik)."""
    r = ruhe_je_frame(rec, cfg, faktor)
    if r is None:
        return None
    a, z = grenzen
    kante = float(cfg["kante_s"]) * float(faktor)
    schritt = 1.0 / r.fps
    for k in range(1, int(math.ceil((z - a) / schritt)) + 2):
        for d in (k * schritt, -k * schritt):
            x, y = von_s + d, bis_s + d
            if x < a - 1e-6 or y > z + 1e-6 or zooms_im_bereich(rec, x, y):
                continue
            if not any(b.seite != "mitte" for b in _kanten(r, kante, x, y)):
                return round(d, 2)
    return None
```

Dann `bewegung_grundniveau` und `bewegung_max_im_bereich` löschen und `OHNE_MESSWIRKUNG` setzen auf

```python
OHNE_MESSWIRKUNG = ("parallel", "brennweite_gleich_max", "digitalzoom_faktor", "digitalzoom_max",
                    "bewegung_max", "stabil_min_s", "glatt_s", "kante_s")
```
(Kommentar darüber: „Schlüssel ohne Einfluss auf die Messung: Parallelität, die Brennweitenfolge der Vorlagen 3a/6d und
die Ableitung der Läufe und Kanten aus der Reihe (Spec 2026-09-23/-25)“).

- [ ] **Step 4: `defaults.yaml`** — die beiden Zeilen `bewegung_rand_s: 0.5 …` und `bewegung_spitze_faktor: 3.0 …`
löschen; hinter `glatt_s: 0.4 …` einfügen:

```yaml
  kante_s: 0.3              # Schnittkante in Timeline-Sekunden: die ersten/letzten kante_s jedes B-Roll-Shots müssen
                            # ruhig sein (Fehler), Bewegung dazwischen ist ein Hinweis (Spec 2026-09-25)
```

- [ ] **Step 5: Funktionstests grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests/test_telemetrie.py -q -p no:cacheprovider`
Expected: PASS.

- [ ] **Step 6: Failing Prüfer-Tests** — in `tests/test_broll_layout.py`:
  - Import `from reihen import reihe as _reihe`; in `CFG_TELEMETRIE` `"bewegung_rand_s": 0.5, "bewegung_spitze_faktor":
    3.0,` durch `"kante_s": 0.3,` ersetzen;
  - in `test_verify_layout_meldet_fehlenden_telemetrie_configblock` `bewegung_rand_s` (zweimal) durch `kante_s` ersetzen;
  - löschen: `test_verify_layout_bewegungsspitze_an_der_schnittgrenze_warnt_nur`,
    `test_verify_layout_bewegungsspitze_nennt_schnittgrenze_und_messfenster_getrennt`,
    `test_verify_layout_bewegungsspitze_unter_ruhig_max_px_warnt_nicht`,
    `test_verify_layout_bewegungsspitze_grundniveau_null_warnt_trotzdem`,
    `test_verify_layout_keine_bewegungs_warnung_in_verworfenem_abschnitt`;
  - Assertions mit „nicht als stabil gemessen“ entfernen in `test_verify_layout_erlaubt_shot_im_stabilen_bereich_eines_verworfenen_abschnitts`,
    `test_verify_layout_shot_ueber_gerettete_abschnittsgrenze_ohne_warnung`,
    `test_verify_layout_wackler_bleibt_gesperrt_bei_luecke_innerhalb_des_abschnitts`,
    `test_verify_layout_i3_shot_ueber_die_grenze_in_einem_lauf`, `test_verify_layout_m1_zwei_laeufe_an_der_abschnittsgrenze_bleiben_zwei`,
    `test_verify_layout_fx3_8641_mit_laeufen` (die übrigen Assertions bleiben);
  - in `test_verify_layout_alte_schwellen_ueberspringt_zoom_und_bewegung_nicht_die_brennweite` bekommt `frisch[0]`
    zusätzlich eine Reihe — `frisch = [{**_tele("FX3_1.MP4", 25.0, schnell, fen), "verschiebung": _reihe((12.0, 5.0, 0.0))},
    _tele("FX3_2.MP4", 25.0), _tele("FX3_3.MP4", 70.0)]` — und die beiden „Bewegungsspitze“-Assertions werden
    `assert any("Punkt liegt in Bewegung" in e and "FX3_1" in e for e in r.errors), r.errors` bzw.
    `assert not any("Punkt liegt in Bewegung" in e for e in r.errors), r.errors     # Kantenregel übersprungen`;
  - `test_verify_layout_warnt_bei_shot_ausserhalb_jedes_stabilen_bereichs` ersetzen, und neue Tests anfügen:

```python
def _tele_reihe(datei, *stuecke, dauer_s=12.0, fps=25.0):
    """_tele() mit Reihe je Frame (Spec 2026-09-25)."""
    return {**_tele(datei, 25.0, dauer_s=dauer_s), "fps": fps, "verschiebung": _reihe(*stuecke)}


def test_verify_layout_verwendbarer_abschnitt_in_bewegung_ist_an_der_kante_ein_fehler():
    """FX3_8663-Fall (Spec 2026-09-23: nur Warnung) nach der Spec 2026-09-25: der Abschnitt ist verwendbar, die Kamera
    bewegt sich dort aber durchgehend (8 px je Frame) — beide Schnittkanten liegen in Bewegung, das ist ein Fehler."""
    idx = _idx_abschnitts_maengel([], [], stabil_a=[])
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    res = L.verify_layout(plan, TP, idx, CL, CFG, 25, [_tele_reihe("FX3_1.MP4", (12.0, 8.0, 0.0))])
    assert any("FX3_1.MP4" in e and "In-Punkt liegt in Bewegung" in e for e in res.errors), res.errors
    assert any("FX3_1.MP4" in e and "Out-Punkt liegt in Bewegung" in e for e in res.errors), res.errors


def test_verify_layout_kante_in_bewegung_ist_fehler_mit_vorschlag():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    tele = [_tele_reihe("FX3_1.MP4", (2.0, 5.0, 0.0), (10.0, 0.0, 0.0))]      # Schwenk bis 2,0 s
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    fehler = [e for e in r.errors if "FX3_1.MP4" in e and "Punkt liegt in Bewegung" in e]
    assert len(fehler) == 1 and fehler[0].startswith(
        "Strecke 1 Szene 1 Shot 1 (FX3_1.MP4 0–3s): In-Punkt liegt in Bewegung (0–0,32 s: wackeln 0, "
        "Bewegung 5 px/Frame) — gleich lang passend ab 2,24 s."), fehler
    assert any("FX3_1.MP4" in w and "Bewegung im Shot bei 0,32–2,24 s" in w for w in r.warnings), r.warnings


def test_verify_layout_kante_mit_abweichung_ohne_fehler():
    idx = _idx()
    plan = L.LayoutPlan("v.md", [], [L.Strecke(1, [L.Szene("Standort 1/Flur", [
        L.Shot("Flur/FX3_1.MP4", 0.0, 3.0, abweichung=True, abweichung_grund="gewollter Reißschwenk"),
        L.Shot("Flur/FX3_2.MP4", 1.0, 4.0), L.Shot("Flur/FX3_3.MP4", 0.0, 2.0)])])])
    tele = [_tele_reihe("FX3_1.MP4", (2.0, 5.0, 0.0), (10.0, 0.0, 0.0))]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert not any("Punkt liegt in Bewegung" in e for e in r.errors), r.errors
    assert not any("Bewegung im Shot" in w for w in r.warnings), r.warnings


def test_verify_layout_zeitlupe_zaehlt_die_sichtbare_bewegung():
    idx = _idx()
    tele = [_tele_reihe("FX3_5.MP4", (12.0, 3.0, 0.0), fps=50.0)]           # gleichmäßig 3 px je 25-fps-Frame
    langsam = _plan({1: [("Flur/FX3_5.MP4", 0.0, 2.0, 2), ("Flur/FX3_1.MP4", 0.0, 2.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    r = L.verify_layout(langsam, TP, idx, CL, CFG, 25, tele)
    assert not any("FX3_5" in e and "Punkt liegt in Bewegung" in e for e in r.errors), r.errors   # sichtbar 1,5
    normal = _plan({1: [("Flur/FX3_5.MP4", 0.0, 2.0), ("Flur/FX3_1.MP4", 0.0, 2.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    r2 = L.verify_layout(normal, TP, idx, CL, CFG, 25, tele)
    fehler = [e for e in r2.errors if "FX3_5" in e and "Punkt liegt in Bewegung" in e]
    assert len(fehler) == 2 and all("keine ruhige Lage gleicher Länge" in e for e in fehler), fehler


def test_verify_layout_kante_ohne_messung_warnt_nur():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, [_tele_reihe("FX3_1.MP4", (2.0, 0.0, 0.0))])  # Reihe bis 2,0 s
    assert not any("FX3_1" in e and "Punkt liegt in Bewegung" in e for e in r.errors), r.errors
    assert any("FX3_1.MP4" in w and "Out-Punkt ohne Messung" in w for w in r.warnings), r.warnings


def test_verify_layout_ohne_reihe_keine_kantenpruefung():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, [_tele("FX3_1.MP4", 25.0)])
    for x in r.errors + r.warnings:
        assert "Punkt liegt in Bewegung" not in x and "Bewegung im Shot" not in x and "ohne Messung" not in x, x
```

- [ ] **Step 7: Tests schlagen fehl**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests/test_broll_layout.py -q -p no:cacheprovider`
Expected: FAIL (keine Kantenmeldungen; Config-Fehler „telemetrie.bewegung_rand_s fehlt“).

- [ ] **Step 8: Prüfer umbauen** — in `broll_layout.py`:
  - Pflichtschlüssel (Z. 676): `for key in ("brennweite_gleich_max", "ruhig_max_px", "bewegung_max", "glatt_s",
    "kante_s", "fenster_s"):`
  - im Block `if rec is not None and not veraltet:` alles ab `rand = float(tcfg["bewegung_rand_s"])` bis einschließlich
    der Warnung „Bereich nicht als stabil gemessen“ löschen und im Zweig `if not p["abweichung"]:` hinter der
    Zoom-Schleife ergänzen: `_kanten_pruefen(r, tag, rec, tcfg, p, von, bis, spans)`;
  - den Kommentar „außerhalb der abweichung-Bedingung: Regel 3c rechnet auf denselben Grenzen weiter“ löschen;
  - vor `def verify_layout(` einfügen:

```python
def _vorschlag(rec: dict, tcfg: dict, p: dict, von: float, bis: float, faktor: float,
               spans: list[tuple[float, float]]) -> str:
    """Text für die Kanten-Meldung: die nächste Lage gleicher Länge mit ruhigen Kanten im erlaubten Bereich des Shots,
    als In-Punkt des Plans (``in_s``) — ein Vorschlag, keine Automatik (Spec 2026-09-25)."""
    grenzen = next(((a, z) for a, z in spans if a - EPS <= p["in_s"] and p["out_s"] <= z + EPS), None)
    if grenzen is None:
        return "kein Vorschlag, der Shot liegt in keinem erlaubten Bereich"
    d = TM.ruhige_lage(rec, tcfg, von, bis, faktor, grenzen)
    if d is None:
        return "im erlaubten Bereich keine ruhige Lage gleicher Länge — kürzer schneiden oder anderen Bereich"
    return f"gleich lang passend ab {_z(round(p['in_s'] + d, 2))} s"


def _kanten_pruefen(r: VerifyResult, tag: str, rec: dict, tcfg: dict, p: dict, von: float, bis: float,
                    spans: list[tuple[float, float]]) -> None:
    """Schnittkanten frame-genau (Spec 2026-09-25): nicht ruhige Frames in den ersten/letzten ``kante_s`` des Shots sind
    ein Fehler mit Vorschlag, in der Mitte ein Hinweis, eine Kante ohne Messung ebenfalls. Ohne Reihe keine Prüfung
    (alter Datensatz — die Hash-Prüfung meldet ihn). Bei Zeitlupe zählt die sichtbare Bewegung (Faktor 1 / tempo).
    Ersetzt die Warnungen „Bewegungsspitze" und „Bereich nicht als stabil gemessen" der Spec 2026-09-23."""
    faktor = 1.0 / float(p["tempo"] or 1)
    vorschlag = None
    for k in TM.kanten_befunde(rec, tcfg, von, bis, faktor) or []:
        seite = "In" if k.seite == "in" else "Out"
        if not k.gemessen:
            r.warnings.append(f"{tag}: {seite}-Punkt ohne Messung (Telemetrie-Reihe zu kurz) — Kante nicht geprüft.")
        elif k.seite == "mitte":
            r.warnings.append(f"{tag}: Bewegung im Shot bei {_z(k.von_s)}–{_z(k.bis_s)} s (wackeln {_z(k.wackeln)}, "
                              f"Bewegung {_z(k.bewegung)} px/Frame) — Hinweis.")
        else:
            if vorschlag is None:
                vorschlag = _vorschlag(rec, tcfg, p, von, bis, faktor, spans)
            r.errors.append(f"{tag}: {seite}-Punkt liegt in Bewegung ({_z(k.von_s)}–{_z(k.bis_s)} s: wackeln "
                            f"{_z(k.wackeln)}, Bewegung {_z(k.bewegung)} px/Frame) — {vorschlag}. Shot verschieben, "
                            f"anderen Bereich wählen oder `abweichung` mit Grund.")
```

- [ ] **Step 9: Klebl-Abnahme an den Kanten** — in `tests/test_bereiche_abnahme.py` ergänzen:

```python
KLEBL_KANTENFEHLER = {"FX3_0260.MP4", "FX3_0252.MP4", "a7MK4_20260922_0317.MP4", "FX3_0675.MP4", "FX3_0710.MP4",
                      "FX3_0700.MP4", "FX3_0267.MP4", "FX3_0705.MP4", "FX3_0653.MP4"}


def test_abnahme_klebl_kantenpruefung_unveraendert():
    """Die vier Wackler des Nachtlaufs und fünf weitere fallen an einer Schnittkante durch (Änderungsmelder,
    bewegung_max 2,0); die übrigen 23 Shots bestehen."""
    fehler = set()
    for s in _json("bereiche-klebl.json"):
        befunde = T.kanten_befunde(s["telemetrie"], CFG, s["von_s"], s["bis_s"], 1.0 / s["tempo"])
        if any(k.seite != "mitte" and k.gemessen for k in befunde):
            fehler.add(s["clip"])
    assert fehler == KLEBL_KANTENFEHLER
```

- [ ] **Step 10: Alles grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests -q -p no:cacheprovider`
Expected: alle PASS, 1 skipped, 1 xfailed. Außerdem: `grep -rn "bewegung_rand_s\|bewegung_spitze_faktor\|bewegung_grundniveau\|bewegung_max_im_bereich" tools/autocut/src tools/autocut/scripts tools/autocut/tests tools/autocut/defaults.yaml`
→ keine Treffer.

- [ ] **Step 11: Commit**

```bash
git add tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/src/niro_autocut/broll_layout.py \
        tools/autocut/defaults.yaml tools/autocut/tests/test_telemetrie.py tools/autocut/tests/test_broll_layout.py \
        tools/autocut/tests/test_bereiche_abnahme.py
git commit -m "feat(autocut): Schnittkanten frame-genau geprüft — Kante in Bewegung ist ein Fehler mit Vorschlag

Erste/letzte kante_s jedes B-Roll-Shots müssen ruhig sein, Bewegung dazwischen ist ein Hinweis; ersetzt die
Warnungen Bewegungsspitze und „Bereich nicht als stabil gemessen“ samt bewegung_rand_s/bewegung_spitze_faktor.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 4: Bericht, Planer-Prompt, Doku

**Files:**
- Modify: `tools/autocut/src/niro_autocut/telemetrie_bericht.py` (`_unruhigste`, `bericht_md`),
  `tools/autocut/scripts/autocut_telemetrie.py` (Aufruf von `bericht_md`)
- Modify: `tools/autocut/prompts/place-broll.md`, `tools/autocut/WORKFLOW-AutoCut.md`, `tools/autocut/README.md`,
  `docs/superpowers/specs/2026-09-23-autocut-broll-bereichsauswahl-design.md`
- Test: `tests/test_telemetrie_bericht.py`, `tests/test_docs.py`

**Interfaces:**
- Consumes: `stabile_bereiche(rec, tcfg)`.
- Produces: `bericht_md(tele, titel, index=None, px_faktor=None, tcfg=None) -> str`.

- [ ] **Step 1: Failing Tests** — in `tests/test_telemetrie_bericht.py` Import `from reihen import reihe` und:

```python
def test_bericht_nennt_ruhige_laeufe_frame_genau():
    tele = [{**TELE[0], "verschiebung": reihe((2.4, 0.0, 0.0), (0.8, 5.0, 0.0), (4.8, 0.0, 0.0)), "dauer_s": 8.0}]
    tcfg = {"ruhig_max_px": 0.15, "bewegung_max": 2.0, "glatt_s": 0.4, "stabil_min_s": 2.0}
    md = B.bericht_md(tele, "T", tcfg=tcfg)
    assert "ruhige Läufe (s)" in md and "0,00–2,24; 3,44–8,00" in md
    assert "ruhige Fenster" not in B.bericht_md(TELE, "T")
```
In `tests/test_docs.py` in `test_workflow_erklaert_die_bereichsauswahl` den Eintrag `"nicht als stabil gemessen"` durch
`"Punkt liegt in Bewegung"` ersetzen und anfügen:

```python
def test_doku_erklaert_die_kantenregel():
    """Spec 2026-09-25: Workflow, Prompt und README nennen die frame-genaue Kantenregel."""
    wf = _flach(_text(WORKFLOW))
    for needle in ("kante_s", "glatt_s", "verschiebung", "frame-genau", "Punkt liegt in Bewegung", "gleich lang passend ab"):
        assert needle in wf, f"WORKFLOW-AutoCut.md: „{needle}“ fehlt"
    for alt in ("bewegung_rand_s", "bewegung_spitze_faktor", "nicht als stabil gemessen"):
        assert alt not in wf, f"WORKFLOW-AutoCut.md nennt noch „{alt}“"
    prompt = _flach(_text(PLACE_PROMPT))
    for needle in ("Punkt liegt in Bewegung", "0,3 s", "frame-genau"):
        assert needle in prompt, f"place-broll.md: „{needle}“ fehlt"
    assert "nicht als stabil gemessen" not in prompt
    assert "Schnittkanten" in _flach(_text(README))
```

- [ ] **Step 2: Tests schlagen fehl**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests/test_telemetrie_bericht.py tools/autocut/tests/test_docs.py -q -p no:cacheprovider`
Expected: FAIL.

- [ ] **Step 3: Bericht** — in `telemetrie_bericht.py` den Import zu `from .telemetrie import BEWEGUNGSARTEN, HALTUNGEN,
finden, stabile_bereiche` erweitern; `_unruhigste(tele)` wird `_unruhigste(tele, tcfg=None)`, Kopfzeile
`| Clip | Kamera | Ordner | wackeln | bewegung | Haltung | Bewegungsart | ruhige Läufe (s) | Hinweis |`, und statt
`ruhig = r.get("ruhige_fenster") or []` samt Ausgabe:

```python
        laeufe = stabile_bereiche(r, tcfg) if tcfg else []
        lauf_text = "; ".join(f"{_de(a)}–{_de(z)}" for a, z, *_ in laeufe[:4]) + (" …" if len(laeufe) > 4 else "")
        zeilen.append(f"| {_md(r.get('clip'))} | {_md(r.get('kamera'))} | {_md(r.get('ordner'))} | {_de(r['wackeln'])} | "
                      f"{_de(r.get('bewegung'))} | {_md(r.get('haltung'))} | {_md(r.get('bewegungsart'))} | "
                      f"{lauf_text or '–'} | {', '.join(hinweis) or '–'} |")
```
`bericht_md` bekommt den Parameter `tcfg: dict | None = None` (Docstring: „``tcfg`` (``telemetrie:``) → ruhige Läufe
frame-genau je Clip“) und ruft `_unruhigste(tele, tcfg)`. In `scripts/autocut_telemetrie.py` den Aufruf um
`tcfg=cfg` ergänzen: `bericht_md(laden(ch.autocut), …, px_faktor=cfg.get("px_faktor") or {}, tcfg=cfg)`.

- [ ] **Step 4: `prompts/place-broll.md`** —
  - im Absatz zu `stabil_laeufe` hinter „die **ungeschnittenen** gemessenen ruhigen Läufe `[von_s, bis_s, wackeln_max,
    bewegung_max]`“ ergänzen: „, **frame-genau** (seit 25.09.2026, Grenzen auf 0,04 s; Bewegung = Betrag je Frame)“;
  - hinter dem Absatz „Bei verwendbaren Abschnitten ist `stabil` ein Hinweis, kein Zwang …“ als neuer Absatz:
    „- **Schnittkanten (Pflicht, jeder Shot):** die ersten und letzten 0,3 s jedes Shots (Timeline, `kante_s`) müssen
    ruhig sein — am sichersten liegt der ganze Shot in einem Lauf aus `stabil_laeufe`. Bewegung zwischen den Kanten
    ist erlaubt (nur Hinweis); ein Shot, der in einen Schwenk hinein oder aus ihm heraus schneidet, nicht. Nicht um
    Zehntelsekunden schieben, bis die Prüfung schweigt — die Meldung nennt die nächste ruhige Lage gleicher Länge.“
  - in der Fehlertabelle die Zeile
    `| \`liegt in keinem verwendbaren Abschnitt\` / \`Abschnitt … hat den Mangel\` / \`Bereich nicht als stabil gemessen\` | … |`
    ersetzen durch

```markdown
| `liegt in keinem verwendbaren Abschnitt` / `Abschnitt … hat den Mangel` | Shot vollständig in einen Lauf aus `stabil_laeufe` legen oder anderen Abschnitt wählen |
| `In-/Out-Punkt liegt in Bewegung` | Shot auf die vorgeschlagene Lage schieben („gleich lang passend ab … s“), kürzer schneiden oder anderen Bereich; gewollter Schwenk: `abweichung` + Grund |
| `Bewegung im Shot bei …` / `… ohne Messung` (Hinweis) | Bild ansehen; gewollte Bewegung zwischen ruhigen Kanten darf bleiben |
```

- [ ] **Step 5: `WORKFLOW-AutoCut.md`** —
  - Stufe 2b, Absatz „Zusätzlich trägt der Nachlauf die gemessenen **stabilen Bereiche** ein …“: „Läufe benachbarter
    ruhiger Fenster (`wackeln ≤ ruhig_max_px`, ohne schnelle Zoomfahrten, `bewegung ≤ bewegung_max`), je Lauf mindestens
    `stabil_min_s` lang.“ ersetzen durch „Läufe ruhiger **Frames**, seit 25.09.2026 frame-genau aus der Reihe
    `verschiebung` (je Frame `wackeln ≤ ruhig_max_px` und Bewegung als Betrag `≤ bewegung_max`, beide über `glatt_s`
    0,4 s geglättet, ohne schnelle Zoomfahrten), je Lauf mindestens `stabil_min_s` lang, Grenzen auf den Frame
    (0,04 s) genau.“; „die drei Schwellen“ → „die Schwellen samt `glatt_s`“; „Wer `bewegung_max` oder `stabil_min_s`
    ändert“ → „Wer `bewegung_max`, `stabil_min_s` oder `glatt_s` ändert“; „(beide Schlüssel stehen in
    `OHNE_MESSWIRKUNG`)“ → „(alle drei stehen in `OHNE_MESSWIRKUNG`)“.
  - Stufe 3, Schritt 4: den Text ab „**Schnittgrenze in einer Bewegungsspitze** (nur Warnung)“ bis einschließlich
    „die Regel blockiert deshalb nie.“ ersetzen durch: „**Schnittkanten in Bewegung** (Fehler, seit 25.09.2026, Spec
    `docs/superpowers/specs/2026-09-25-autocut-schnittkanten-framegenau-design.md`) — die ersten und letzten `kante_s`
    (0,3 s Timeline) jedes Shots müssen frame-genau ruhig sein (`wackeln ≤ ruhig_max_px`, Bewegung ≤ `bewegung_max`,
    geglättet über `glatt_s`; bei Zeitlupe zählt die sichtbare Bewegung, Faktor 1/tempo). Die Meldung „In-/Out-Punkt
    liegt in Bewegung (…)“ nennt Stelle, Werte und die nächste ruhige Lage gleicher Länge im erlaubten Bereich
    („gleich lang passend ab … s“) — ein Vorschlag, keine Automatik. Ausweg für einen gewollten Schwenk: `abweichung`
    mit Grund. **Bewegung in der Mitte** des Shots ist nur ein Hinweis („Bewegung im Shot bei …“), ebenso eine Kante,
    an die die Telemetrie-Reihe nicht reicht („ohne Messung“).“
  - Stufe 3, Liste unter „`--verify-only` prüft dazu“: den Punkt „**Warnung `Bereich nicht als stabil gemessen`** …“
    ersetzen durch „**Fehler `In-/Out-Punkt liegt in Bewegung`**: auch in verwendbaren Abschnitten müssen die
    Schnittkanten ruhig sein (Schritt 4); Bewegung in der Mitte bleibt ein Hinweis — ein gewollter Schwenk zwischen zwei
    ruhigen Kanten ist erlaubt.“; „(dazwischen lag ein unruhiges Fenster)“ → „(dazwischen lagen unruhige Frames)“;
    im Absatz „**Andere Schwellen**“: „keine Rettung, keine Bewegungs-Warnung“ → „keine Rettung“ und „Wurden nur
    `bewegung_max` oder `stabil_min_s` geändert“ → „Wurden nur `bewegung_max`, `stabil_min_s` oder `glatt_s` geändert“.
  - Telemetrie-Abschnitt: „und ohne die unkalibrierten Bewegungsspitzen-Schwellen `bewegung_rand_s`,
    `bewegung_spitze_faktor` — keine dieser Schwellen ändert die Messung, nur die Regel darauf)“ ersetzen durch „und ohne
    die Ableitungs-Schwellen `bewegung_max`, `stabil_min_s`, `glatt_s`, `kante_s` — keine dieser Schwellen ändert die
    Messung, nur die Regel darauf; dazu eine Messversion: seit 25.09.2026 Version 2 mit Brennweite je Frame und Reihe
    `verschiebung`, ältere Datensätze gelten als veraltet und werden neu gemessen)“; in „Felder je Clip“ hinter
    „`ruhige_fenster` (wackeln ≤ `telemetrie.ruhig_max_px`)“ ergänzen: „, `verschiebung` (seit 25.09.2026: dx/dy je
    25-fps-Frame in px @480, 2 Stellen, `t0_s` = Zeit des ersten Frames; der Gyro wird mit der KB-Brennweite **je
    Frame** umgerechnet, vorher mit dem Median des Clips)“; „Stufe 3 (Brennweitenfolge, Zoom, Bewegungsspitzen)“ →
    „Stufe 3 (Brennweitenfolge, Zoom, Schnittkanten)“.
  - Absatz „`bewegung_max` (2,0) und `stabil_min_s` (2,0) sind **unkalibrierte Startwerte** vom 23.09.2026 …“ ersetzen
    durch: „`bewegung_max` ist seit 25.09.2026 die Bewegung **je Frame** als Betrag (px @480, über `glatt_s` 0,4 s
    geglättet) — die Ableitung aus 2-s-Fenstern (Achsmittel, Grenzen ±1 s; Klebl-Nachtlauf: vier Shots schnitten in
    Schwenk-Ausläufe und Nachwackeln) ist abgelöst. Startwert 2,0, **unkalibriert**; die Review-Runde Schnittkanten
    (`projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten/`) läuft. Abnahme `tests/test_bereiche_abnahme.py`:
    kein Lauf im Beispiel „komplett ungewollt“, höchstens zwei der 24 „ungewollt“-Beispiele mit Lauf, die vier
    Klebl-Wackler liegen in keinem Lauf. Wer eine Schwelle ändert, muss dort wieder antreten.“
- [ ] **Step 6: `README.md`** — Zeile „Nachlauf“: „**stabile Bereiche**:“ → „**stabile Bereiche** (frame-genau):“;
Zeile „B-Roll“: „mit Telemetrie geprüft auf Brennweitenfolge/Zoom (Fehler) und Bewegungsspitzen am Schnitt (Warnung)“ →
„mit Telemetrie geprüft auf Brennweitenfolge/Zoom und Schnittkanten in Bewegung (Fehler, frame-genau) sowie Bewegung im
Shot (Hinweis)“; Zeile „Telemetrie“: „wackeln, ruhige Fenster,“ → „wackeln, ruhige Fenster, `verschiebung` je Frame,“ und
„(Brennweitenfolge, Zoom, Bewegungsspitzen, stabile Bereiche)“ → „(Brennweitenfolge, Zoom, Schnittkanten, stabile Bereiche)“.
- [ ] **Step 7: Spec vom 23.09.** — in `docs/superpowers/specs/2026-09-23-autocut-broll-bereichsauswahl-design.md` hinter
den Absatz „**Berichtigt 24.09.2026** …“ einfügen: „**Abgelöst 25.09.2026** (Klebl-Praxislauf): Abschnitt 2 (Läufe aus
2-s-Fenstern, „±1 s reicht“) und die Bewegungs-Warnungen in Abschnitt 5 sind durch
`2026-09-25-autocut-schnittkanten-framegenau-design.md` ersetzt — Läufe und Prüfung rechnen frame-genau aus dem Gyro.“
- [ ] **Step 8: Alles grün**

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests -q -p no:cacheprovider`
Expected: alle PASS, 1 skipped, 1 xfailed.

- [ ] **Step 9: Commit**

```bash
git add tools/autocut/src/niro_autocut/telemetrie_bericht.py tools/autocut/scripts/autocut_telemetrie.py \
        tools/autocut/prompts/place-broll.md tools/autocut/WORKFLOW-AutoCut.md tools/autocut/README.md \
        docs/superpowers/specs/2026-09-23-autocut-broll-bereichsauswahl-design.md \
        tools/autocut/tests/test_telemetrie_bericht.py tools/autocut/tests/test_docs.py
git commit -m "docs(autocut): Kantenregel frame-genau in Workflow, Prompt, README und Bericht

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 5: Optischer Weg prüfen (Analyse, kein Code im Repo)

**Ausführung:** Controller (nicht Subagent). Ergebnis geht in Task 6 (Beispiele) und in den Abschlussbericht.

**Files:**
- Create (Scratchpad, nicht committen): `optisch_pruefung.py`

- [ ] **Step 1: Skript** — im Scratchpad der Session:

```python
"""Task 5 (Plan 2026-09-25): optischer Weg — frame-genaue Ruhe an Drohnen-Clips, die laut Fenstern ruhig sind.
Nur lesen: misst mit clip_messen() aus dem Worktree, schreibt nichts in die Chargen."""
import json
import sys
from pathlib import Path

import numpy as np

WT = Path("/Users/jansantos/NIRO Studio/.claude/worktrees/autocut-schnittkanten")
sys.path.insert(0, str(WT / "tools/autocut/src"))
from niro_autocut import telemetrie as T  # noqa: E402
from niro_autocut.charge import load_config  # noqa: E402

CFG = load_config(Path("/nirgendwo"))["telemetrie"]
KUNDEN = [Path("/Users/jansantos/NIRO Studio/projects/MN Deko und Verleih"),
          Path("/Users/jansantos/NIRO Studio/projects/Autohaus Rappold"),
          Path("/Users/jansantos/NIRO Studio/projects/WLC")]
kandidaten = []
for kunde in KUNDEN:
    for tj in kunde.glob("*/*/_intern/autocut/telemetrie.json"):
        for r in json.loads(tj.read_text(encoding="utf-8")):
            f = r.get("fenster") or []
            if r.get("quelle") == "optisch" and r.get("kamera") == "DJI" and f and Path(r["path"]).exists():
                anteil = len(r.get("ruhige_fenster") or []) / len(f)
                if anteil >= 0.8:
                    kandidaten.append((anteil, r["path"]))
kandidaten.sort(reverse=True)
print(len(kandidaten), "laut Fenstern ruhige DJI-Clips erreichbar")
for anteil, pfad in kandidaten[:8]:
    rec = T.clip_messen(Path(pfad), CFG)
    r = T.ruhe_je_frame(rec, CFG)
    if r is None:
        print(Path(pfad).name, "ohne Reihe:", rec.get("fehler"))
        continue
    laeufe = T.stabile_bereiche(rec, CFG)
    flag = "  ← prüfen" if r.ruhig.mean() < 0.6 else ""
    print(f"{Path(pfad).name:26} Fenster ruhig {anteil:4.0%} | Frames ruhig {r.ruhig.mean():4.0%} | "
          f"{len(laeufe)} Läufe über {rec['dauer_s']} s | wackeln p90 {np.percentile(r.wackeln, 90):.3f} | "
          f"Bewegung p90 {np.percentile(r.bewegung, 90):.2f}{flag}")
```

- [ ] **Step 2: Laufen lassen und bewerten**

Run: `tools/autocut/venv/bin/python <Scratchpad>/optisch_pruefung.py`
Expected: mindestens 5 Clips gemessen. Unauffällig = Frames ruhig ≥ 60 % bei allen. Clips mit „← prüfen“ (bis zu
zwei) kommen als zusätzliche Beispiele in die Review-Runde (Task 6, Liste `BEISPIELE`, Zweck „DJI laut Fenstern ruhig,
Bildmessung je Frame unruhig“). Sind weniger als 5 Clips erreichbar: dem User melden, nicht raten.

---

## Task 6: Review-Runde Schnittkanten und Kalibrierung von `bewegung_max`

**Ausführung:** Controller mit dem User (Urteile). Charge im **Hauptordner** (`/Users/jansantos/NIRO Studio/projects/…`),
Kalibrier-Werkzeug aus dem Worktree (`--src`).

**Files:**
- Create: `/Users/jansantos/NIRO Studio/projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten/Protokoll.md`,
  `…/_intern/skripte/kanten_beispiele.py`
- Modify (Worktree): `tools/autocut/defaults.yaml`, `tests/fixtures/gen_bereiche_fixture.py`, `tests/test_bereiche_abnahme.py`,
  `tests/test_broll_layout.py` (nur falls sich Läufe ändern), `WORKFLOW-AutoCut.md`; Create: `tests/fixtures/bereiche-kanten.json`

- [ ] **Step 1: Skript `kanten_beispiele.py`** anlegen:

```python
"""Kalibrierung Schnittkanten (Spec docs/superpowers/specs/2026-09-25-autocut-schnittkanten-framegenau-design.md).

Einmal-Skript der Kalibrier-Charge, nicht Teil des Werkzeugs. Zeigt B-Roll-Einsetzer genau so, wie AutoCut sie setzen
würde (Quellbereich von–bis, 100 % Tempo), damit der User je Nummer urteilt: „so schneiden: ja/nein“ und wo es stört.
Daraus kommt ``telemetrie.bewegung_max`` (Bewegung je Frame an der Schnittkante).

Aufruf aus dem Hauptordner des Repos mit dem AutoCut-venv:
  tools/autocut/venv/bin/python "<Charge>/_intern/skripte/kanten_beispiele.py" --src <tools/autocut/src> --rendern
      → _intern/beispiele.json, _intern/vorhersagen.json, _intern/work/schnittkanten-beispiele.mp4
  tools/autocut/venv/bin/python "<Charge>/_intern/skripte/kanten_beispiele.py" --src <tools/autocut/src> --auswerten
      → liest _intern/urteile.json ({"<nr>": {"urteil": "ja"|"nein", "stoert": "Anfang"|"Ende"|"Anfang und Ende"|
        "Mitte"|""}}), schreibt _intern/auswertung.json und druckt die Grenzen
Quellen nur lesend (NAS).
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HIER = Path(__file__).resolve()
CHARGE = HIER.parents[2]
PROJECTS = HIER.parents[5]
NAS = "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
KLEBL = NAS + "Klebl GmbH/02_Projekte/03_Projek-Edeka Baustelle/03_Medien/01_Footage/"
WLC = NAS + "WLC Würth Logistik GmbH & CO KG/02_Projekte/01_Projekt-Dreh18.05 & 20.05/03_Medien/01_Footage/"
LUT = PROJECTS / "Wurst & Liebe/Social-Reels/2026-08 Dreh 05.08/_intern/reels/lut/slog3_lc709a.cube"
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
W, H, FPS, SEED, TAFEL_S = 1080, 1920, 25, 25, 1.0

# (Bezeichnung, Datei, von_s, bis_s, Zweck) — Klebl wie gebaut bzw. korrigiert (Klebl-Protokoll 25.09.2026)
BEISPIELE = [
    ("Klebl FX3_0260 wie gebaut", KLEBL + "Kamera-B/FX3_0260.MP4", 1.50, 3.50, "Einschwingen am In-Punkt"),
    ("Klebl FX3_0260 korrigiert", KLEBL + "Kamera-B/FX3_0260.MP4", 2.20, 4.20, "In-Punkt nach dem Einschwingen"),
    ("Klebl FX3_0700 wie gebaut", KLEBL + "Kamera-B/FX3_0700.MP4", 7.00, 9.64, "Nachwackeln nach schnellem Zoom"),
    ("Klebl FX3_0700 korrigiert", KLEBL + "Kamera-B/FX3_0700.MP4", 7.32, 9.96, "In-Punkt nach dem Nachwackeln"),
    ("Klebl FX3_0653 wie gebaut", KLEBL + "Kamera-B/FX3_0653.MP4", 4.00, 6.68, "Schwenk-Auslauf bis 3,9 px/Frame"),
    ("Klebl FX3_0267 wie gebaut", KLEBL + "Kamera-B/FX3_0267.MP4", 6.20, 8.52, "Schwenk bis 5,0 px/Frame am In-Punkt"),
    ("Klebl FX3_0705 wie gebaut", KLEBL + "Kamera-B/FX3_0705.MP4", 4.00, 6.08, "Schwenk-Auslauf 2,8 px/Frame"),
    ("Klebl FX3_0675 wie gebaut", KLEBL + "Kamera-B/FX3_0675.MP4", 5.20, 7.48, "In-Punkt kurz nach einem Ruck"),
    ("Klebl FX3_0252 wie gebaut", KLEBL + "Kamera-B/FX3_0252.MP4", 3.50, 5.82, "Mitzieh-Schwenk bis 3,5 am Out"),
    ("Klebl FX3_0710 wie gebaut", KLEBL + "Kamera-B/FX3_0710.MP4", 6.30, 8.38, "Mitzieh-Schwenk 2,5 am Out"),
    ("Klebl FX3_0674 wie gebaut", KLEBL + "Kamera-B/FX3_0674.MP4", 6.50, 8.86, "Mitzieh-Schwenk um 2,0 px/Frame"),
    ("Klebl a7 0317 wie gebaut", KLEBL + "Kamera-A/a7MK4_20260922_0317.MP4", 20.00, 22.24, "Handkamera wacklig"),
    ("WLC FX3_8660 12,5–15,5 s", WLC + "Adelsheim/B-Roll/Ameise/FX3_8660.MP4", 12.50, 15.50,
     "vom User am 23.09. als gut benannt, Schwenk-Auslauf 2,9 am In"),
]


def werkzeug(src: str):
    sys.path.insert(0, src)
    from niro_autocut import telemetrie as T
    from niro_autocut.charge import load_config
    return T, load_config(Path("/nirgendwo"))["telemetrie"]


def slog3(path: str) -> bool:
    """S-Log3 laut Sony-Sidecar (<Clip>M01.XML) — dann LUT LC-709 Type A wie in den Schwenk-Beispielen."""
    xml = Path(path).with_name(Path(path).stem + "M01.XML")
    return xml.is_file() and "s-log3" in xml.read_text(encoding="utf-8", errors="replace").lower()


def plakette(nr: int, ziel: Path, gross: bool) -> Path:
    groesse = (W, H) if gross else (260, 170)
    bild = Image.new("RGBA", groesse, (0, 0, 0, 255 if gross else 170))
    zeichnen = ImageDraw.Draw(bild)
    try:
        schrift = ImageFont.truetype(FONT, 360 if gross else 120)
    except OSError:
        schrift = ImageFont.load_default(size=360 if gross else 120)
    zeichnen.text((groesse[0] // 2, groesse[1] // 2), str(nr), font=schrift, fill=(255, 255, 255, 255), anchor="mm")
    bild.save(ziel)
    return ziel


def tafel(nr: int, ziel: Path, arbeit: Path) -> None:
    """1 s Schwarz mit der großen Nummer — so beginnt jedes Beispiel mit einem echten Schnitt in den Shot."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(plakette(nr, arbeit / f"tafel_{nr:02d}.png", True)),
                    "-t", f"{TAFEL_S:.3f}", "-r", str(FPS), "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "fast",
                    "-crf", "18", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-color_range", "tv", str(ziel)], check=True, stdin=subprocess.DEVNULL)


def segment(b: dict, ziel: Path, arbeit: Path) -> None:
    """Der Einsetzer genau von–bis, 100 % Tempo, Nummer oben links."""
    lut = f"lut3d=file='{LUT}'," if LUT.exists() and slog3(b["pfad"]) else ""
    bild = (f"[0:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,{lut}"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,scale=w=iw:h=ih:out_range=tv:out_color_matrix=bt709,"
            f"format=yuv420p[b];[b][1:v]overlay=40:40:shortest=1,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{b['von_s']:.3f}", "-i", b["pfad"], "-loop", "1",
                    "-i", str(plakette(b["nr"], arbeit / f"nr_{b['nr']:02d}.png", False)), "-filter_complex", bild,
                    "-map", "[v]", "-an", "-t", f"{b['bis_s'] - b['von_s']:.3f}", "-r", str(FPS), "-c:v", "libx264",
                    "-preset", "fast", "-crf", "18", "-colorspace", "bt709", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-color_range", "tv", str(ziel)], check=True, stdin=subprocess.DEVNULL)


def kantenwerte(T, cfg: dict, rec: dict, von: float, bis: float) -> dict:
    """Höchstwerte (geglättet) an beiden Kanten und in der Mitte — die Vorhersage vor den Urteilen."""
    r = T.ruhe_je_frame(rec, cfg)
    kante = float(cfg["kante_s"])
    out = {}
    for name, a, b in (("in", von, von + kante), ("out", bis - kante, bis), ("mitte", von + kante, bis - kante)):
        s = r.frames(a, b)
        out[name] = {"wackeln": round(float(r.wackeln[s].max()), 3) if s.stop > s.start else None,
                     "bewegung": round(float(r.bewegung[s].max()), 3) if s.stop > s.start else None}
    befunde = T.kanten_befunde(rec, cfg, von, bis)
    out["besteht_bei_2_0"] = not any(k.seite != "mitte" for k in befunde)
    return out


def rendern(T, cfg: dict) -> None:
    arbeit = CHARGE / "_intern" / "work"
    arbeit.mkdir(parents=True, exist_ok=True)
    liste = [{"bezeichnung": n, "pfad": p, "von_s": v, "bis_s": b, "zweck": z} for n, p, v, b, z in BEISPIELE]
    random.Random(SEED).shuffle(liste)
    gemessen, stuecke = {}, []
    for nr, b in enumerate(liste, 1):
        b["nr"] = nr
        if b["pfad"] not in gemessen:
            gemessen[b["pfad"]] = T.clip_messen(Path(b["pfad"]), cfg)
        b["vorhersage"] = kantenwerte(T, cfg, gemessen[b["pfad"]], b["von_s"], b["bis_s"])
        t, s = arbeit / f"tafel_{nr:02d}.mp4", arbeit / f"seg_{nr:02d}.mp4"
        tafel(nr, t, arbeit)
        segment(b, s, arbeit)
        stuecke += [t, s]
        print(f"  Nr. {nr:>2}: {b['bezeichnung']} ({b['von_s']:.2f}–{b['bis_s']:.2f} s) — {b['zweck']}", flush=True)
    (CHARGE / "_intern" / "beispiele.json").write_text(json.dumps(liste, indent=1, ensure_ascii=False), encoding="utf-8")
    (CHARGE / "_intern" / "vorhersagen.json").write_text(json.dumps({str(b["nr"]): b["vorhersage"] for b in liste},
                                                                    indent=1, ensure_ascii=False), encoding="utf-8")
    concat = arbeit / "concat.txt"
    concat.write_text("".join(f"file '{s}'\n" for s in stuecke), encoding="utf-8")
    ziel = arbeit / "schnittkanten-beispiele.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy",
                    str(ziel)], check=True, stdin=subprocess.DEVNULL)
    print(f"→ {ziel}")


def auswerten(cfg: dict) -> None:
    beispiele = json.loads((CHARGE / "_intern" / "beispiele.json").read_text(encoding="utf-8"))
    urteile = json.loads((CHARGE / "_intern" / "urteile.json").read_text(encoding="utf-8"))
    ruhig_max = float(cfg["ruhig_max_px"])
    ja_max, nein_min, widersprueche = 0.0, None, []
    for b in beispiele:
        u = urteile[str(b["nr"])]
        v = b["vorhersage"]
        kante_bw = max(v["in"]["bewegung"] or 0.0, v["out"]["bewegung"] or 0.0)
        kante_wk = max(v["in"]["wackeln"] or 0.0, v["out"]["wackeln"] or 0.0)
        b["urteil"], b["stoert"] = u["urteil"], u.get("stoert", "")
        if u["urteil"] == "ja":
            ja_max = max(ja_max, kante_bw)
            if kante_wk > ruhig_max:
                widersprueche.append(f"Nr. {b['nr']} ja, aber wackeln {kante_wk} > {ruhig_max} an der Kante")
        elif u.get("stoert") in ("Anfang", "Ende", "Anfang und Ende") and kante_wk <= ruhig_max:
            nein_min = kante_bw if nein_min is None else min(nein_min, kante_bw)
        print(f"Nr. {b['nr']:>2} {u['urteil']:<4} {b.get('stoert') or '':<16} Kante Bewegung {kante_bw:5.2f} "
              f"wackeln {kante_wk:5.3f} — {b['bezeichnung']}")
    grenze = None
    if nein_min is not None and ja_max < nein_min:
        grenze = round((ja_max + nein_min) / 2, 1)
    elif nein_min is not None:
        widersprueche.append(f"schnellstes „ja“ {ja_max} ≥ langsamstes „nein“ {nein_min} — eine Grenze trennt nicht")
    erg = {"ja_max": ja_max, "nein_min": nein_min, "vorschlag_bewegung_max": grenze, "widersprueche": widersprueche}
    (CHARGE / "_intern" / "auswertung.json").write_text(json.dumps(erg, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(erg, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="tools/autocut/src des Werkzeugstands (Worktree bis zum Merge)")
    ap.add_argument("--rendern", action="store_true")
    ap.add_argument("--auswerten", action="store_true")
    args = ap.parse_args()
    T, CFG = werkzeug(args.src)
    if args.rendern:
        rendern(T, CFG)
    if args.auswerten:
        auswerten(CFG)
```
Beispiele aus Task 5 (bis zu zwei DJI-Clips mit „← prüfen“) vor dem Rendern an `BEISPIELE` anhängen (Pfad, 2,5 s aus
dem Clip, Zweck „DJI laut Fenstern ruhig, je Frame unruhig“).

- [ ] **Step 2: Rendern und Vorhersage festschreiben** (aus `/Users/jansantos/NIRO Studio`)

Run: `tools/autocut/venv/bin/python "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten/_intern/skripte/kanten_beispiele.py" --src "/Users/jansantos/NIRO Studio/.claude/worktrees/autocut-schnittkanten/tools/autocut/src" --rendern`
Expected: 13–15 Nummern, `_intern/vorhersagen.json` geschrieben, `schnittkanten-beispiele.mp4` ≈ 45–60 s.
Das Video einmal ansehen (Frames an zwei Nummern ziehen): Hochkant, LUT sichtbar, Nummer lesbar.

- [ ] **Step 3: Protokoll anlegen und ins Review** — `Protokoll.md` der Kalibrier-Charge (Ziel, Beispiele mit Zweck,
Vorhersage bei 2,0 je Nummer, Hinweis: die vier Klebl-Wackler sind Messbefund, nicht Urteil des Users); dann

Run: `python3 tools/review/review.py hinzufuegen "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten" --datei "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten/_intern/work/schnittkanten-beispiele.mp4" --video "Schnittkanten-Beispiele" --notiz "Je Nummer: so schneiden ja/nein, und wo es stört (Anfang/Mitte/Ende)"`
Expected: Link `http://localhost:4711/#/NIRO/Werkzeug-Kalibrierung/Schnittkanten-Beispiele`; im Chat melden, dazu die
Frage an den User: je Nummer „ja/nein“ und „stört am Anfang / in der Mitte / am Ende“. Danach
`sh tools/studio_abgleich.sh --charge "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten"`.

- [ ] **Step 4: Warten auf die Urteile.** Tasks 1–4 dürfen weiterlaufen; hier weiter erst mit den Urteilen. Urteile als
`_intern/urteile.json` festhalten (`stoert` auf „Anfang“, „Ende“, „Anfang und Ende“, „Mitte“ oder „“ normiert).

- [ ] **Step 5: Auswerten**

Run: `tools/autocut/venv/bin/python "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten/_intern/skripte/kanten_beispiele.py" --src "/Users/jansantos/NIRO Studio/.claude/worktrees/autocut-schnittkanten/tools/autocut/src" --auswerten`
Expected: `vorschlag_bewegung_max` gesetzt und `widersprueche` leer. Sonst **stoppen**: dem User die Tabelle zeigen und
die Grenze gemeinsam festlegen (Spec: „nicht passend machen“).

- [ ] **Step 6: Grenze übernehmen (Worktree)** — `defaults.yaml`: `bewegung_max: <vorschlag>` und den Kommentar auf
„kalibriert <Datum>, Review-Runde Schnittkanten (<n> Urteile, schnellstes „ja“ <ja_max>, langsamstes „nein“ <nein_min>)“.
Im Generator eine Funktion ergänzen und in die Liste in `__main__` aufnehmen:

```python
KANTEN = STUDIO / "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten/_intern"


def kanten() -> list[dict]:
    """Die Einsetzer der Review-Runde Schnittkanten mit den Urteilen des Users (Kalibrierung von bewegung_max)."""
    beispiele = json.loads((KANTEN / "beispiele.json").read_text(encoding="utf-8"))
    urteile = json.loads((KANTEN / "urteile.json").read_text(encoding="utf-8"))
    raus, gemessen = [], {}
    for b in beispiele:
        u = urteile[str(b["nr"])]
        if b["pfad"] not in gemessen:
            gemessen[b["pfad"]] = _messen(b["pfad"])
        raus.append({"nr": b["nr"], "bezeichnung": b["bezeichnung"], "von_s": b["von_s"], "bis_s": b["bis_s"],
                     "urteil": u["urteil"], "stoert": u.get("stoert", ""),
                     "telemetrie": _schlank(gemessen[b["pfad"]], b["von_s"], b["bis_s"])})
    return raus
```
Generator laufen lassen (`bereiche-kanten.json` entsteht, die übrigen Fixtures bleiben gleich) und in
`test_bereiche_abnahme.py` ergänzen:

```python
def test_abnahme_review_runde_schnittkanten():
    """Kalibrierung (Spec 2026-09-25): jede Nummer mit „ja“ besteht die Kantenprüfung, jede mit „nein“, die am Anfang
    oder Ende stört, fällt durch."""
    for e in _json("bereiche-kanten.json"):
        befunde = T.kanten_befunde(e["telemetrie"], CFG, e["von_s"], e["bis_s"])
        faellt = any(k.seite != "mitte" and k.gemessen for k in befunde)
        if e["urteil"] == "ja":
            assert not faellt, (e["nr"], e["bezeichnung"], befunde)
        elif e["stoert"] in ("Anfang", "Ende", "Anfang und Ende"):
            assert faellt, (e["nr"], e["bezeichnung"], befunde)
```

- [ ] **Step 7: Änderungsmelder nachziehen** — volle Suite laufen lassen. Mit der neuen Grenze ändern sich die
exakten Werte in `test_abnahme_hoechstens_zwei_laeufe_in_ungewolltem_material` (Liste), `test_abnahme_wlc_laeufe_unveraendert`,
`KLEBL_IM_LAUF`, `KLEBL_KANTENFEHLER` und ggf. `test_verify_layout_i3_ende_zu_ende_an_fx3_8660`: je die gemessenen Werte
eintragen (die harten Kriterien — R2#12 ohne Lauf, höchstens zwei „ungewollt“ mit Lauf, die vier Klebl-Wackler in keinem
Lauf — dürfen NICHT fallen; fällt eins, stoppen und mit dem User klären). Besteht FX3_8660 jetzt, das `xfail` entfernen.

Run: `tools/autocut/venv/bin/python -m pytest tools/autocut/tests -q -p no:cacheprovider`
Expected: alle PASS.

- [ ] **Step 8: Doku** — in `WORKFLOW-AutoCut.md` den Kalibrier-Absatz (aus Task 4) auf den Stand bringen: Wert, Datum,
Zahl der Urteile, Grenzen `ja_max`/`nein_min`, Abnahme um „jede Review-Nummer „ja“ besteht, jede „nein“ an einer Kante
fällt durch“ ergänzt. Protokoll der Kalibrier-Charge fortschreiben und abgleichen
(`sh tools/studio_abgleich.sh --charge "projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten"`).

- [ ] **Step 9: Commit (Worktree)**

```bash
git add tools/autocut/defaults.yaml tools/autocut/WORKFLOW-AutoCut.md tools/autocut/tests/fixtures/gen_bereiche_fixture.py \
        tools/autocut/tests/fixtures/bereiche-kanten.json tools/autocut/tests/test_bereiche_abnahme.py \
        tools/autocut/tests/test_broll_layout.py
git commit -m "feat(autocut): bewegung_max aus der Review-Runde Schnittkanten kalibriert

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 7: Abnahme am echten Klebl-Plan (nur lesen) und Abschluss

**Ausführung:** Controller.

- [ ] **Step 1: Prüfer am echten Plan** — Scratchpad-Skript (schreibt nichts in die Charge):

```python
"""Task 7 (Plan 2026-09-25): verify_layout mit frame-genauer Telemetrie an den echten Klebl-Plänen — nur lesen."""
import json
import sys
from pathlib import Path

import yaml

WT = Path("/Users/jansantos/NIRO Studio/.claude/worktrees/autocut-schnittkanten")
sys.path.insert(0, str(WT / "tools/autocut/src"))
from niro_autocut import broll_layout as L  # noqa: E402
from niro_autocut import index_sections as S  # noqa: E402
from niro_autocut import telemetrie as T  # noqa: E402
from niro_autocut.broll_plan import load_profile  # noqa: E402
from niro_autocut.charge import load_config  # noqa: E402
from niro_autocut.cutlist import Cutlist  # noqa: E402

CH = Path("/Users/jansantos/NIRO Studio/projects/Klebl/Recruiting-Videos/2026-09 Dreh Edeka Baustelle 22.09")
AC = CH / "_intern" / "autocut"
cfg = load_config(CH)
tcfg = cfg["telemetrie"]
_, prof = load_profile("default")
lokal = (yaml.safe_load((AC / "config.yaml").read_text(encoding="utf-8")) or {}).get("broll") or {}
cfg_broll = {**(cfg.get("broll") or {}), **prof, **lokal}
index = json.loads((AC / "broll_index.json").read_text(encoding="utf-8"))
for video in ("video-1-tiefbau", "video-2-hoch-und-fertigteilbau"):
    vd = AC / video
    cl = Cutlist.load(vd / "cutlist.json")
    tp = json.loads((vd / "timeline.json").read_text(encoding="utf-8"))
    plan = L.LayoutPlan.load(vd / "broll_plan.json")
    genutzt = {p["clip"] for p in json.loads((vd / "broll_build.json").read_text(encoding="utf-8"))["placed"]}
    tele = [T.clip_messen(Path(p), tcfg) for p in sorted(genutzt)]
    by = {t["path"]: t for t in tele}
    idx = {**index, "clips": [S.telemetrie_anwenden(c, by[c["path"]], float(tcfg["fenster_s"]), tcfg)[0]
                              if c["path"] in by else c for c in index["clips"]]}
    res = L.verify_layout(plan, tp, idx, cl, {**cfg_broll, "telemetrie": tcfg}, float(tp.get("fps") or 25), tele)
    print(f"\n== {video}: {len(res.errors)} Fehler, {len(res.warnings)} Warnungen")
    for e in res.errors:
        if "Punkt" in e:
            print("FEHLER:", e)
    for w in res.warnings:
        if "Bewegung im Shot" in w or "ohne Messung" in w:
            print("HINWEIS:", w)
```

Run: `tools/autocut/venv/bin/python <Scratchpad>/klebl_abnahme.py`
Expected: die Shots aus `KLEBL_KANTENFEHLER` (Stand nach Task 6) bekommen „In-/Out-Punkt liegt in Bewegung“ mit
Vorschlag; die übrigen keinen Kantenfehler. Ergebnis in den Abschlussbericht.

- [ ] **Step 2: Volle Suite und Review** — Suite grün; dann superpowers:requesting-code-review über den Branch
(Spec + Plan als Maßstab), Befunde abarbeiten.
- [ ] **Step 3: Abschluss** — superpowers:finishing-a-development-branch: dem User Stand, Kalibrierwert und die
Folgen nennen (jede Charge misst beim nächsten AutoCut-Lauf einmal neu, dann `autocut_index_sections.py`); Merge nach
main nur mit OK. Gedächtnis (`autocut-bereichsauswahl.md`, `autocut-telemetrie.md`) und Klebl-Protokoll nicht
vergessen (Klebl-Protokoll nur anhängen).
