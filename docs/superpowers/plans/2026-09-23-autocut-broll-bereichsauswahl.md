# B-Roll-Auswahl auf Bereichsebene — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die B-Roll-Auswahl urteilt je Abschnitt und je gemessenem Bereich statt je Clip, damit Clips mit einer schlechten Sekunde nicht komplett ausfallen.

**Architecture:** Stufe 2 nennt Mängel je Abschnitt statt nur je Clip. Die Telemetrie leitet aus den vorhandenen Sekunden-Fenstern „stabile Bereiche" ab (reine Rechnung, keine Messung, keine API); Stufe 2b schreibt sie je Abschnitt in den Index. Der kompakte Index nimmt daraufhin auch Abschnitte auf, die das Modell verworfen hat, solange kein gesperrter Mangel bleibt — beschränkt auf ihre stabilen Bereiche. Der Prüfer sperrt je Abschnitt statt je Clip, lässt den Mangel „Wackler" innerhalb eines stabilen Bereichs fallen und warnt bei Shots außerhalb jedes stabilen Bereichs.

**Tech Stack:** Python 3 (`tools/autocut/venv`), numpy, pytest. Keine neuen Abhängigkeiten.

## Global Constraints

- **Spec:** `docs/superpowers/specs/2026-09-23-autocut-broll-bereichsauswahl-design.md`. Bei Widersprüchen gilt die Spec; Abweichungen zuerst melden, nicht still umsetzen.
- **Sprache:** Code-Kommentare, Docstrings, Meldungstexte und Commit-Botschaften auf Deutsch, wie im ganzen Modul. Zahlen in Meldungen mit Dezimalkomma (`f"{x:.2f}".replace(".", ",")`), wie in `telemetrie.py` üblich.
- **Tests laufen mit dem venv des Hauptordners** (Worktrees haben keinen eigenen): `cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest -q`. Alle Befehle in diesem Plan sind aus `tools/autocut/` heraus gedacht.
- **Keine Medien, kein NAS, keine API in Tests.** Fixtures tragen gemessene Werte, keine erfundenen.
- **Rückwärtskompatibel:** Ein Index oder eine Telemetrie ohne die neuen Felder muss sich exakt wie heute verhalten. Kein Zwangs-Neuindex, kein Zwangs-Neumessen.
- **Unkalibrierte Werte werden gekennzeichnet.** `bewegung_max` steht auf zwei Datenpunkten und bekommt in `defaults.yaml` das Wort `UNKALIBRIERT`, wie `bewegung_rand_s`.
- **Exakte neue Schlüssel:** `telemetrie.bewegung_max: 2.0`, `telemetrie.stabil_min_s: 2.0`. `telemetrie.ruhig_max_px` bleibt bei `0.15`.

## File Structure

| Datei | Verantwortung | Task |
|---|---|---|
| `src/niro_autocut/telemetrie.py` | `stabile_bereiche()`, `bewegung_max_im_bereich()`, beide Schlüssel in `OHNE_MESSWIRKUNG` | 1 |
| `defaults.yaml` | die zwei neuen Schwellen | 1 |
| `tests/fixtures/gen_bereiche_fixture.py` | erzeugt die zwei Fixtures aus den Chargen (einmalig, nicht im Testlauf) | 2 |
| `tests/fixtures/bereiche-urteile.json` | 30 Urteile vom 22.09. mit Fenster-Reihen | 2 |
| `tests/fixtures/bereiche-wlc.json` | 4 WLC-Clips mit den Bereichen des Users | 2 |
| `tests/test_bereiche_abnahme.py` | die Abnahme-Kriterien der Spec | 2 |
| `src/niro_autocut/index_sections.py` | `stabil` je Abschnitt, `stabil_quelle` je Clip | 3 |
| `src/niro_autocut/broll_index.py`, `prompts/index-clip.md` | `abschnitte[].maengel` | 4 |
| `src/niro_autocut/broll_layout.py` (`compact_index_v2`), `scripts/autocut_place_broll.py`, `prompts/place-broll.md` | gerettete Abschnitte im kompakten Index | 5 |
| `src/niro_autocut/broll_plan.py` (`_usable_spans`), `src/niro_autocut/broll_layout.py` (`verify_layout`) | Sperre je Abschnitt, Lage, Warnung | 6 |
| `WORKFLOW-AutoCut.md`, `README.md` | Doku | 7 |

Die Reihenfolge ist bindend: Task 3 braucht Task 1, Task 5 braucht Task 3 und 4, Task 6 braucht Task 5.

---

### Task 1: `stabile_bereiche()` in der Telemetrie

**Files:**
- Modify: `tools/autocut/src/niro_autocut/telemetrie.py` (`OHNE_MESSWIRKUNG` bei Zeile 387; neue Funktionen hinter `bewegung_grundniveau`, Zeile ~702)
- Modify: `tools/autocut/defaults.yaml` (`telemetrie:`-Block, hinter `bewegung_spitze_faktor`)
- Test: `tools/autocut/tests/test_telemetrie.py`

**Interfaces:**
- Produces: `stabile_bereiche(rec: dict | None, cfg: dict) -> list[list[float]]` — je Eintrag `[von_s, bis_s, wackeln_max, bewegung_max]`, aufsteigend nach `von_s`. `cfg` ist der `telemetrie:`-Block und muss `bewegung_max`, `stabil_min_s`, `schritt_s`, `fenster_s` enthalten.
- Produces: `bewegung_max_im_bereich(rec: dict | None, von_s: float, bis_s: float, fenster_s: float = 2.0) -> float | None`

- [ ] **Step 1: Write the failing tests**

Ans Ende von `tools/autocut/tests/test_telemetrie.py` anhängen:

```python
# --------------------------------------------------------------------------- #
# Stabile Bereiche (Spec 2026-09-23)
# --------------------------------------------------------------------------- #

CFG_STABIL = {**CFG, "bewegung_max": 2.0, "stabil_min_s": 2.0}


def _rec_fenster(fenster, ruhige=None, dauer_s=None, fenster_s=2.0):
    """Datensatz mit Fenster-Reihe; ruhige_fenster sonst aus wackeln <= ruhig_max_px wie clip_messen()."""
    if ruhige is None:
        ruhige = [f[0] for f in fenster if f[1] <= CFG_STABIL["ruhig_max_px"]]
    return {"clip": "FX3_1", "dauer_s": dauer_s, "fenster_s": fenster_s,
            "fenster": fenster, "ruhige_fenster": ruhige}


def test_stabile_bereiche_fasst_benachbarte_ruhige_fenster_zusammen():
    rec = _rec_fenster([[0.0, 0.05, 0.1, "statisch", None], [1.0, 0.06, 0.2, "statisch", None],
                        [2.0, 0.40, 3.0, "schwenk_links", None], [3.0, 0.05, 0.3, "statisch", None],
                        [4.0, 0.05, 0.3, "statisch", None]], dauer_s=6.0)
    assert T.stabile_bereiche(rec, CFG_STABIL) == [[0.0, 3.0, 0.06, 0.2], [3.0, 6.0, 0.05, 0.3]]


def test_stabile_bereiche_deckelt_bewegung_und_kappt_an_der_clipdauer():
    # t=1 ist nach wackeln ruhig, die Bewegung (3,5) liegt über bewegung_max → der Lauf beginnt erst bei t=2;
    # das Ende 3,0 + fenster_s = 5,0 wird auf die Clipdauer 4,6 gekappt
    rec = _rec_fenster([[0.0, 0.30, 0.4, "fahrt", None], [1.0, 0.05, 3.5, "schwenk_rechts", None],
                        [2.0, 0.05, 0.4, "fahrt", None], [3.0, 0.05, 0.4, "fahrt", None]], dauer_s=4.6)
    assert T.stabile_bereiche(rec, CFG_STABIL) == [[2.0, 4.6, 0.05, 0.4]]


def test_stabile_bereiche_folgt_ruhige_fenster_und_verwirft_zu_kurze_laeufe():
    # ruhige_fenster ist die Quelle: t=2 fehlt dort (schnelle Zoomfahrt im Fenster), obwohl wackeln klein ist
    rec = _rec_fenster([[0.0, 0.05, 0.1, "statisch", None], [1.0, 0.40, 0.1, "gemischt", None],
                        [2.0, 0.05, 0.1, "statisch", None]], ruhige=[0.0], dauer_s=4.0)
    assert T.stabile_bereiche(rec, CFG_STABIL) == [[0.0, 2.0, 0.05, 0.1]]
    assert T.stabile_bereiche(rec, {**CFG_STABIL, "stabil_min_s": 2.5}) == []


def test_stabile_bereiche_ohne_daten_leer():
    assert T.stabile_bereiche(None, CFG_STABIL) == []
    assert T.stabile_bereiche({"fenster": [], "ruhige_fenster": []}, CFG_STABIL) == []
    # Fenster vorhanden, aber keins ruhig (Datensatz einer verwackelten Handkamera)
    assert T.stabile_bereiche({"fenster": [[0.0, 2.0, 5.0, "gemischt", None]], "ruhige_fenster": [],
                               "dauer_s": 3.0, "fenster_s": 2.0}, CFG_STABIL) == []


def test_bewegung_max_im_bereich():
    rec = _rec_fenster([[0.0, 0.05, 0.1, "statisch", None], [1.0, 0.05, 2.4, "fahrt", None],
                        [2.0, 0.05, 0.3, "statisch", None]], dauer_s=4.0)
    assert T.bewegung_max_im_bereich(rec, 0.0, 4.0) == 2.4
    assert T.bewegung_max_im_bereich(None, 0.0, 4.0) is None
    assert T.bewegung_max_im_bereich({"fenster": []}, 0.0, 4.0) is None


def test_config_hash_ignoriert_die_stabil_schwellen():
    # beide Schlüssel ändern keine Messung, nur die Ableitung aus fenster → kein neuer Hash, kein Neumessen
    h = T.config_hash(CFG)
    assert T.config_hash({**CFG, "bewegung_max": 5.0}) == h
    assert T.config_hash({**CFG, "stabil_min_s": 3.0}) == h


def test_defaults_haben_die_stabil_schwellen():
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    assert cfg["bewegung_max"] == 2.0 and cfg["stabil_min_s"] == 2.0
    assert cfg["ruhig_max_px"] == 0.15
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_telemetrie.py -q -k "stabil or bewegung_max_im_bereich"
```

Erwartet: FAIL mit `AttributeError: module 'niro_autocut.telemetrie' has no attribute 'stabile_bereiche'` und `KeyError: 'bewegung_max'` beim Defaults-Test.

- [ ] **Step 3: Schwellen in `defaults.yaml` ergänzen**

In `tools/autocut/defaults.yaml` im `telemetrie:`-Block direkt hinter der Zeile `bewegung_spitze_faktor: 3.0   # ...` einfügen:

```yaml
  # Stabile Bereiche für die B-Roll-Auswahl (Spec 2026-09-23): Läufe benachbarter ruhiger Fenster, in denen ein
  # Shot liegen darf, auch wenn der Index den Abschnitt verworfen hat. Beide Schlüssel ändern keine Messung,
  # nur die Ableitung aus fenster → OHNE_MESSWIRKUNG, ein Neusetzen erzwingt kein Neumessen.
  bewegung_max: 2.0         # Obergrenze der Bewegung je Fenster eines stabilen Bereichs (UNKALIBRIERT, Startwert
                            # 23.09.2026: die vier vom User zurückgeholten Bereiche liegen bei max. 1,64, der
                            # einzige Fehlalarm im 30er-Testsatz bei 3,1–5,3 — je ein Datenpunkt pro Seite)
  stabil_min_s: 2.0         # kürzester stabiler Bereich = kürzester Shot aus broll.shot_len_s
```

- [ ] **Step 4: `OHNE_MESSWIRKUNG` erweitern**

In `tools/autocut/src/niro_autocut/telemetrie.py` (Zeile ~387):

```python
# Schlüssel ohne Einfluss auf die Messung: Parallelität, die Brennweitenfolge der Vorlagen 3a/6d und die
# Ableitung der stabilen Bereiche (Spec 2026-09-23; sie rechnet auf fenster, das die Messung schon enthält)
OHNE_MESSWIRKUNG = ("parallel", "brennweite_gleich_max", "digitalzoom_faktor", "digitalzoom_max",
                    "bewegung_rand_s", "bewegung_spitze_faktor", "bewegung_max", "stabil_min_s")
```

- [ ] **Step 5: Die zwei Funktionen implementieren**

In `tools/autocut/src/niro_autocut/telemetrie.py` direkt hinter `bewegung_grundniveau` (Zeile ~702) einfügen:

```python
def stabile_bereiche(rec: dict | None, cfg: dict) -> list[list[float]]:
    """Bereiche, die ruhig genug zum Schneiden sind, als ``[von_s, bis_s, wackeln_max, bewegung_max]``
    (Spec 2026-09-23). Reine Ableitung aus einem vorhandenen Datensatz — keine Messung, keine Mediendatei.

    Grundlage sind die Fenster, deren Startzeit in ``ruhige_fenster`` steht: damit gilt ``wackeln <= ruhig_max_px``
    **und** der Ausschluss schneller Zoomfahrten aus ``ruhige_ohne_schnelle_zooms`` ohne zweite Rechnung.
    Zusätzlich muss ``bewegung`` des Fensters unter ``bewegung_max`` liegen — ``wackeln`` misst Zittern, nicht
    Tempo, und ein glatter schneller Schwenk taugt als kurzer Einsetzer nicht. Benachbarte Fenster (Abstand
    höchstens ``schritt_s``) bilden einen Lauf; er reicht bis zum Ende seines letzten Fensters, gekappt an
    ``dauer_s``. Läufe unter ``stabil_min_s`` fallen weg. Ohne ``fenster`` oder ohne ruhige Fenster leer.

    Die Bereichsgrenzen sind auf die Fensterauflösung genau (``fenster_s`` 2,0 / ``schritt_s`` 1,0 ⇒ ±1 s).
    Die Liste ist ein Vorschlag, nie eine Sperre: was davon geschnitten wird, entscheidet der Bildinhalt."""
    fen = (rec or {}).get("fenster") or []
    if not fen:
        return []
    ruhig = {float(t) for t in (rec.get("ruhige_fenster") or [])}
    bew_max = float(cfg["bewegung_max"])
    schritt = float(cfg["schritt_s"])
    w = float(rec.get("fenster_s") or cfg["fenster_s"])
    dauer = rec.get("dauer_s")
    laeufe: list[list[tuple[float, float, float]]] = []
    for f in fen:
        t, wk, bw = float(f[0]), float(f[1]), float(f[2])
        if t not in ruhig or bw > bew_max:
            continue
        if laeufe and t - laeufe[-1][-1][0] <= schritt + 1e-6:
            laeufe[-1].append((t, wk, bw))
        else:
            laeufe.append([(t, wk, bw)])
    out = []
    for lauf in laeufe:
        von = lauf[0][0]
        bis = lauf[-1][0] + w
        if dauer is not None:
            bis = min(bis, float(dauer))
        if bis - von < float(cfg["stabil_min_s"]) - 1e-6:
            continue
        out.append([round(von, 2), round(bis, 2),
                    round(max(x[1] for x in lauf), 3), round(max(x[2] for x in lauf), 3)])
    return out


def bewegung_max_im_bereich(rec: dict | None, von_s: float, bis_s: float, fenster_s: float = 2.0) -> float | None:
    """Höchste ``bewegung`` der Fenster im Bereich; None ohne Fenster. Für die Meldung des Prüfers, wenn ein
    Shot außerhalb jedes stabilen Bereichs liegt (Spec 2026-09-23)."""
    fen = _fenster_im_bereich(rec, von_s, bis_s, fenster_s) if rec and rec.get("fenster") else []
    return max((float(f[2]) for f in fen), default=None)
```

- [ ] **Step 6: Run the tests to verify they pass**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_telemetrie.py -q
```

Erwartet: PASS, 120 Tests (113 bisher + 7 neue).

- [ ] **Step 7: Gesamtlauf, damit die neuen Config-Schlüssel nirgends anecken**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest -q
```

Erwartet: PASS ohne neue Fehler.

- [ ] **Step 8: Commit**

```bash
git add tools/autocut/src/niro_autocut/telemetrie.py tools/autocut/defaults.yaml tools/autocut/tests/test_telemetrie.py
git commit -m "feat(autocut): stabile Bereiche aus den Sekunden-Fenstern ableiten

stabile_bereiche() fasst benachbarte ruhige Fenster zu Bereichen zusammen,
in denen ein Shot liegen darf: Grundlage ist ruhige_fenster (wackeln unter
ruhig_max_px, ohne schnelle Zoomfahrten), dazu ein Deckel auf bewegung.
Reine Ableitung, keine Messung. Beide neuen Schwellen stehen in
OHNE_MESSWIRKUNG und erzwingen deshalb kein Neumessen.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Fixtures und Abnahme gegen die 30 Urteile

**Files:**
- Create: `tools/autocut/tests/fixtures/gen_bereiche_fixture.py`
- Create: `tools/autocut/tests/fixtures/bereiche-urteile.json` (erzeugt, ~52 KB)
- Create: `tools/autocut/tests/fixtures/bereiche-wlc.json` (erzeugt, ~9 KB)
- Create: `tools/autocut/tests/test_bereiche_abnahme.py`

**Interfaces:**
- Consumes: `telemetrie.stabile_bereiche(rec, cfg)` aus Task 1.
- Produces: nichts für spätere Tasks — dieser Task ist das Abnahmetor. Schlägt er fehl, ist der Mechanismus nicht abgenommen und Task 3 startet nicht.

**Hintergrund:** Die 30 Urteile beantworten „gewollt vs. ungewollt" (Absicht), der Mechanismus beantwortet „ruhig genug zum Schneiden". Übertragbar ist nur die Fehlalarm-Richtung: in Material, das der User als unbrauchbar bezeichnet hat, darf kein Bereich behauptet werden. Die erwarteten Werte unten sind an den echten Daten nachgerechnet, nicht geschätzt.

- [ ] **Step 1: Generator schreiben**

`tools/autocut/tests/fixtures/gen_bereiche_fixture.py`:

```python
"""Erzeugt die Fixtures bereiche-urteile.json und bereiche-wlc.json aus den Chargen-Daten.

Einmalig von Hand laufen lassen, NICHT im Testlauf: die Quellen liegen in projects/ und damit nicht im Repo
(NAS-Spiegel). Die erzeugten Dateien werden committet — sie sind die Testgrundlage. Gelesen wird aus dem
HAUPTORDNER des Repos (Worktrees haben kein projects/), geschrieben wird neben diese Datei.

    python3 tools/autocut/tests/fixtures/gen_bereiche_fixture.py

Quellen:
  projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/autocut/telemetrie.json
  projects/WLC/Recruiting/2026-07 Erster Dreh/_intern/autocut/telemetrie.json
  projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schwenks/_intern/{beispiele,urteile}{,2}.json

Die Fenster-Reihen der 30 Urteile werden auf den Bereich ± 10 s beschnitten (halbiert die Dateigröße;
an allen 30 Beispielen geprüft: identische Kandidaten wie mit der vollen Reihe). Die vier WLC-Clips
bleiben vollständig — dort werden Kandidaten über den ganzen Clip geprüft.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HIER = Path(__file__).resolve().parent


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
RAND_S = 10.0
FELDER = ("clip", "dauer_s", "fenster_s", "fenster", "ruhige_fenster", "config_hash", "haltung", "wackeln")

# Die Bereiche, die der User am 23.09. im Review genannt hat (Protokoll der WLC-Charge)
WLC_BEREICHE = {"FX3_8636": [[4.5, 7.5]], "FX3_8641": [[1.5, 4.0]], "FX3_8660": [[12.5, 15.5]],
                "FX3_8663": [[9.0, 12.0], [63.5, 66.5]]}


def _laden(p: Path) -> dict:
    if not p.is_file():
        raise SystemExit(f"{p} fehlt — Charge vom NAS holen (sh tools/studio_abgleich.sh --charge ...).")
    return {r["clip"]: r for r in json.loads(p.read_text(encoding="utf-8"))}


def _schlank(rec: dict, von_s: float | None = None, bis_s: float | None = None) -> dict:
    out = {k: rec.get(k) for k in FELDER}
    if von_s is not None:
        a, z = von_s - RAND_S, bis_s + RAND_S
        out["fenster"] = [f for f in out["fenster"] if a <= f[0] <= z]
        out["ruhige_fenster"] = [t for t in out["ruhige_fenster"] if a <= t <= z]
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
                         "telemetrie": _schlank(mek[b["clip"]], von_s, von_s + 5.0)})
    return raus


def wlc() -> list[dict]:
    tel = _laden(WLC)
    return [{"clip": c, "bereiche_user": b, "telemetrie": _schlank(tel[c])} for c, b in WLC_BEREICHE.items()]


if __name__ == "__main__":
    for name, daten in (("bereiche-urteile.json", urteile()), ("bereiche-wlc.json", wlc())):
        p = HIER / name
        p.write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{p.name}: {len(daten)} Einträge, {p.stat().st_size // 1024} KB")
```

- [ ] **Step 2: Fixtures erzeugen**

```bash
cd "/Users/jansantos/NIRO Studio/.claude/worktrees/youthful-boyd-a787a3" && python3 tools/autocut/tests/fixtures/gen_bereiche_fixture.py
```

Erwartet:
```
bereiche-urteile.json: 30 Einträge, 52 KB
bereiche-wlc.json: 4 Einträge, 9 KB
```

Wenn eine Quelle fehlt: `sh tools/studio_abgleich.sh --charge "projects/<...>"` **im Hauptordner** `/Users/jansantos/NIRO Studio` holt die Charge vom NAS. Die Telemetrie-Dateien liegen unter 20 MB und werden vom Abgleich getragen. Der Worktree bekommt kein `projects/` — das ist richtig so, der Generator liest über `git worktree list --porcelain` im Hauptordner.

- [ ] **Step 3: Write the failing test**

`tools/autocut/tests/test_bereiche_abnahme.py`:

```python
"""Abnahme der stabilen Bereiche gegen die 30 Urteile vom 22.09. und die vier WLC-Clips vom 23.09.

Spec: docs/superpowers/specs/2026-09-23-autocut-broll-bereichsauswahl-design.md, Abschnitt „Tests".

Die 30 Urteile messen „gewollt vs. ungewollt" (Absicht), dieser Mechanismus misst „ruhig genug zum Schneiden".
Übertragbar ist nur die Fehlalarm-Richtung: in Material, das der User als unbrauchbar bezeichnet hat, darf kein
Bereich behauptet werden. Die Tests lesen die Schwellen aus defaults.yaml — jede Änderung an ruhig_max_px oder
bewegung_max muss hier wieder antreten.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from niro_autocut import telemetrie as T
from niro_autocut.charge import load_config

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CFG = load_config(Path("/nirgendwo"))["telemetrie"]


def _urteile() -> list[dict]:
    return json.loads((FIXTURES / "bereiche-urteile.json").read_text(encoding="utf-8"))


def _beispiel(nr: str) -> dict:
    return next(e for e in _urteile() if e["nr"] == nr)


def _kandidaten_mit(e: dict, cfg: dict) -> list[tuple[float, float]]:
    """Stabile Bereiche des Clips, auf das 5-s-Beispiel geschnitten; zu kurze Schnitte zählen nicht."""
    min_s = float(cfg["stabil_min_s"])
    out = []
    for a, z, _wk, _bw in T.stabile_bereiche(e["telemetrie"], cfg):
        x, y = max(a, e["von_s"]), min(z, e["bis_s"])
        if y - x >= min_s - 1e-6:
            out.append((round(x, 2), round(y, 2)))
    return out


def _kandidaten(e: dict) -> list[tuple[float, float]]:
    return _kandidaten_mit(e, CFG)


def test_fixture_traegt_die_dreissig_urteile():
    alle = _urteile()
    assert len(alle) == 30
    assert sum(1 for e in alle if e["urteil"] == "ungewollt") == 24
    assert sum(1 for e in alle if e["urteil"].startswith("gewollt")) == 6


def test_abnahme_kein_kandidat_im_komplett_ungewollten_beispiel():
    """Hartes Kriterium 1: R2#12 hat der User ausdrücklich „komplett ungewollt" genannt."""
    e = _beispiel("R2#12")
    assert e["anmerkung"] == "komplett ungewollt"
    assert _kandidaten(e) == []


def test_abnahme_hoechstens_zwei_kandidaten_in_ungewolltem_material():
    """Hartes Kriterium 2: höchstens 2 der 24 „ungewollt"-Beispiele dürfen einen Kandidaten bekommen."""
    treffer = [e["nr"] for e in _urteile() if e["urteil"] == "ungewollt" and _kandidaten(e)]
    assert len(treffer) <= 2, f"zu viele Kandidaten in „ungewollt“-Material: {treffer}"
    # R2#10 ist durch die Anmerkung gedeckt; R1#2 stammt aus Runde 1, die ohne Anmerkungen lief, und ist offen
    assert treffer == ["R1#2", "R2#10"]


def test_abnahme_r2_10_trifft_die_vom_user_genannte_stelle():
    e = _beispiel("R2#10")
    assert e["anmerkung"] == "brauchbar am Anfang und ganz kurz am Ende"
    assert _kandidaten(e) == [(2.5, 5.0)]          # genau der Anfang des Beispiels


def test_abnahme_bewegungsdeckel_haelt_den_glatten_schnellen_schwenk_draussen():
    """R2#9: wackeln 0,03–0,18 (ruhig), bewegung bis 5,3 — ohne Deckel käme hier ein Kandidat."""
    e = _beispiel("R2#9")
    assert _kandidaten(e) == []
    assert _kandidaten_mit(e, {**CFG, "bewegung_max": 99.0}) != []


@pytest.mark.parametrize("clip", ["FX3_8636", "FX3_8641", "FX3_8660", "FX3_8663"])
def test_abnahme_wlc_bereiche_des_users_liegen_in_kandidaten(clip):
    """Die vier Clips aus dem Review vom 23.09.: jeder genannte Bereich muss in einem Kandidaten liegen."""
    e = next(x for x in json.loads((FIXTURES / "bereiche-wlc.json").read_text(encoding="utf-8")) if x["clip"] == clip)
    br = T.stabile_bereiche(e["telemetrie"], CFG)
    for a, z in e["bereiche_user"]:
        assert any(x - 1e-6 <= a and z <= y + 1e-6 for x, y, _wk, _bw in br), \
            f"{clip}: {a}–{z} s liegt in keinem Kandidaten {br}"


def test_abnahme_wlc_kandidaten_unveraendert():
    """Gegen gemessene Werte, damit eine Schwellenänderung sichtbar wird statt still durchzugehen."""
    erwartet = {"FX3_8636": [[0.0, 11.52]], "FX3_8641": [[0.0, 4.8]], "FX3_8660": [[0.0, 11.0], [12.0, 18.72]],
                "FX3_8663": [[8.0, 15.0], [22.0, 27.0], [32.0, 34.0], [35.0, 40.0], [42.0, 47.0], [54.0, 59.0],
                             [63.0, 71.0], [72.0, 77.0]]}
    for e in json.loads((FIXTURES / "bereiche-wlc.json").read_text(encoding="utf-8")):
        grenzen = [[a, z] for a, z, _wk, _bw in T.stabile_bereiche(e["telemetrie"], CFG)]
        assert grenzen == erwartet[e["clip"]], e["clip"]
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_bereiche_abnahme.py -q -v
```

Erwartet: PASS. Sieben Testfunktionen, davon eine viermal parametrisiert — `pytest` sammelt zehn Fälle.

Dies ist der erste Test, der nach der Implementierung geschrieben wird statt davor — bewusst: er prüft nicht neues Verhalten, sondern nimmt das aus Task 1 gegen echte Urteile ab. Schlägt eine Abnahme fehl, **nicht den Test anpassen**, sondern melden: dann stimmt die Schwelle nicht.

- [ ] **Step 5: Commit**

```bash
git add tools/autocut/tests/fixtures/gen_bereiche_fixture.py tools/autocut/tests/fixtures/bereiche-urteile.json tools/autocut/tests/fixtures/bereiche-wlc.json tools/autocut/tests/test_bereiche_abnahme.py
git commit -m "test(autocut): Abnahme der stabilen Bereiche gegen 30 Urteile und 4 WLC-Clips

Die 30 Urteile vom 22.09. und die vier Clips aus dem Review vom 23.09.
liegen als Fixture im Repo (Fenster-Reihen, keine Medien). Hart geprueft:
kein Kandidat in R2#12 (komplett ungewollt), hoechstens 2 der 24
ungewollt-Beispiele mit Kandidat, und jeder vom User genannte WLC-Bereich
liegt in einem Kandidaten. Die Tests lesen die Schwellen aus defaults.yaml.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Stufe 2b schreibt `stabil` je Abschnitt

**Files:**
- Modify: `tools/autocut/src/niro_autocut/index_sections.py` (`telemetrie_anwenden`, Zeile ~188; beide Aufrufe in `index_sections_clip`, Zeile ~367 und ~424)
- Test: `tools/autocut/tests/test_index_sections.py`

**Interfaces:**
- Consumes: `telemetrie.stabile_bereiche(rec, cfg)` aus Task 1.
- Produces: `telemetrie_anwenden(rec, tele, fenster_s=2.0, tcfg=None) -> tuple[dict, bool]`. Mit `tcfg` (dem `telemetrie:`-Config-Block) trägt jeder Abschnitt `stabil: list[list[float]]` und der Datensatz `stabil_quelle: {"ruhig_max_px", "bewegung_max", "stabil_min_s", "config_hash"}`. Ohne `tcfg` unverändert wie heute.

- [ ] **Step 1: Write the failing tests**

In `tools/autocut/tests/test_index_sections.py`: `_CFG_T` erweitern (Zeile ~330) und Tests anhängen.

```python
# ersetzt den bisherigen telemetrie-Block in _CFG_T
_CFG_T = {"index": {"model": "claude-opus-5"},
          "index_sections": {"tile_px": 480, "per_section": 2, "max_sections": 5, "effort": "medium", "max_tokens": 2500},
          "telemetrie": {"fenster_s": 2.0, "schritt_s": 1.0, "ruhig_max_px": 0.15,
                         "bewegung_max": 2.0, "stabil_min_s": 2.0}}
```

Neue Tests ans Ende der Datei:

```python
# --------------------------------------------------------------------------- #
# Stabile Bereiche je Abschnitt (Spec 2026-09-23)
# --------------------------------------------------------------------------- #

_TCFG = {"fenster_s": 2.0, "schritt_s": 1.0, "ruhig_max_px": 0.15, "bewegung_max": 2.0, "stabil_min_s": 2.0}
# Telemetrie mit ruhigen Fenstern: 0–3 s ruhig, 4 s Ausreißer, 5–6 s wieder ruhig
_TELE_STABIL = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "clip": "FX3_1", "quelle": "rtmd", "fehler": None,
                "dauer_s": 8.0, "fenster_s": 2.0, "haltung": "gimbal", "wackeln": 0.05,
                "pitch_grad": -12.0, "perspektive_hoehe": "Aufsicht",
                "fenster": [[0.0, 0.05, 0.2, "statisch", None], [1.0, 0.05, 0.2, "statisch", None],
                            [2.0, 0.05, 0.2, "statisch", None], [3.0, 0.05, 0.2, "statisch", None],
                            [4.0, 0.40, 4.0, "schwenk_links", None], [5.0, 0.05, 0.3, "statisch", None],
                            [6.0, 0.05, 0.3, "statisch", None]],
                "ruhige_fenster": [0.0, 1.0, 2.0, 3.0, 5.0, 6.0],
                "config_hash": "abc123abc123"}


def test_telemetrie_anwenden_schreibt_stabil_je_abschnitt():
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 4, "verwendbar": True},
                          {"von_s": 4, "bis_s": 8, "verwendbar": False}]}
    neu, geaendert = S.telemetrie_anwenden(rec, _TELE_STABIL, 2.0, _TCFG)
    assert geaendert is True
    # Clip-Bereiche sind 0–5 s und 5–8 s, auf die Abschnitte geschnitten
    assert neu["abschnitte"][0]["stabil"] == [[0.0, 4.0, 0.05, 0.2]]
    # 4,0–5,0 s wäre nur 1,0 s lang und fällt unter stabil_min_s weg
    assert neu["abschnitte"][1]["stabil"] == [[5.0, 8.0, 0.05, 0.3]]
    assert neu["stabil_quelle"] == {"ruhig_max_px": 0.15, "bewegung_max": 2.0, "stabil_min_s": 2.0,
                                    "config_hash": "abc123abc123"}


def test_telemetrie_anwenden_schneidet_zu_kurze_stabile_stuecke_weg():
    # Abschnitt 3,5–4,5 s trifft den Bereich 0–5 s nur 1,0 s lang → unter stabil_min_s, fällt weg
    rec = {"abschnitte": [{"von_s": 3.5, "bis_s": 4.5, "verwendbar": False}]}
    neu, _ = S.telemetrie_anwenden(rec, _TELE_STABIL, 2.0, _TCFG)
    assert neu["abschnitte"][0]["stabil"] == []


def test_telemetrie_anwenden_ohne_tcfg_schreibt_kein_stabil():
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 4, "verwendbar": True}]}
    neu, _ = S.telemetrie_anwenden(rec, _TELE_STABIL, 2.0)
    assert "stabil" not in neu["abschnitte"][0] and "stabil_quelle" not in neu


def test_telemetrie_anwenden_ist_mit_stabil_idempotent():
    rec = {"abschnitte": [{"von_s": 0, "bis_s": 4, "verwendbar": True}]}
    einmal, _ = S.telemetrie_anwenden(rec, _TELE_STABIL, 2.0, _TCFG)
    zweimal, geaendert = S.telemetrie_anwenden(einmal, _TELE_STABIL, 2.0, _TCFG)
    assert geaendert is False and zweimal == einmal


def test_index_sections_clip_traegt_stabil_bei_cache_treffer_nach(tmp_path):
    ch = _Ch(tmp_path)
    (ch.autocut / "broll_index").mkdir()
    rec = {"path": "/nas/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "fingerprint": "abcdefabcdef0000",
           "orientierung": "16:9",
           "abschnitte": [{"von_s": 0, "bis_s": 4, "beschreibung": "Flur", "qualitaet": 4, "verwendbar": False,
                           "einstellung": "Halbtotale", "perspektive_hoehe": "Augenhöhe",
                           "perspektive_ansicht": "seitlich", "brennweite": "normal",
                           "bewegungsrichtung": "keine", "hauptmotiv": "Flur", "setup_hash": "0123456789abcdef"}]}
    (ch.autocut / "broll_index" / "abcdefabcdef0000.json").write_text(json.dumps(rec), encoding="utf-8")

    def kein_api(*a, **k):
        raise AssertionError("kein API-Aufruf bei Cache-Treffer")

    out = S.index_sections_clip(ch, rec, None, _CFG_T, "prompt", describe=kein_api, telemetrie=_TELE_STABIL)
    assert out["_cache"] is True and out["abschnitte"][0]["stabil"] == [[0.0, 4.0, 0.05, 0.2]]
    cached = json.loads((ch.autocut / "broll_index" / "abcdefabcdef0000.json").read_text())
    assert cached["abschnitte"][0]["stabil"] == [[0.0, 4.0, 0.05, 0.2]]
    assert cached["stabil_quelle"]["config_hash"] == "abc123abc123"
```

Nachrechnen der Erwartungswerte: `stabile_bereiche(_TELE_STABIL, _TCFG)` liefert `[[0.0, 5.0, 0.05, 0.2], [5.0, 8.0, 0.05, 0.3]]` — Lauf 1 aus t=0…3 endet bei 3+2=5, Lauf 2 aus t=5,6 endet bei 6+2=8 (Clipdauer 8,0). Abschnitt 0–4 schneidet nur Lauf 1 zu `[0.0, 4.0]` (4,0 s, bleibt). Abschnitt 4–8 schneidet Lauf 1 zu `[4.0, 5.0]` — 1,0 s, fällt unter `stabil_min_s` weg — und Lauf 2 zu `[5.0, 8.0]` (3,0 s, bleibt).

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_index_sections.py -q -k stabil
```

Erwartet: FAIL mit `TypeError: telemetrie_anwenden() takes from 2 to 3 positional arguments but 4 were given`.

- [ ] **Step 3: `telemetrie_anwenden` erweitern**

In `tools/autocut/src/niro_autocut/index_sections.py` den Import ergänzen (Zeile 22):

```python
from .telemetrie import (abschnitt_brennweite, abschnitt_werte, bewegung_spitzen, brennweite_text, finden,
                         laden as telemetrie_laden, stabile_bereiche)
```

Signatur und Docstring von `telemetrie_anwenden` (Zeile ~188):

```python
def telemetrie_anwenden(rec: dict, tele: dict | None, fenster_s: float = 2.0,
                        tcfg: dict | None = None) -> tuple[dict, bool]:
    """Metadaten in die Abschnitte: perspektive_hoehe überschreiben (``felder_quelle`` „rtmd": der Pitch stammt immer
    aus den Metadaten, auch wenn die Bewegung optisch gemessen wurde), ``brennweite_mm``/``zoom`` (Brennweite in mm und
    schnellste Zoomfahrt im Abschnitt, nur mit ``kb_verlauf``) sowie bewegungsart/haltung ergänzen. Claudes Klasse
    ``brennweite`` bleibt unangetastet (Spec 2026-09-21). Claudes Originalwert je überschriebenem Feld bleibt im
    Abschnitt unter ``claude``: stammt das Feld laut ``felder_quelle`` schon aus der Telemetrie, bleibt ein vorhandenes
    ``claude[feld]`` stehen (der aktuelle Wert ist dann der Telemetrie-Wert), sonst ist der aktuelle Wert Claudes und
    wird gesichert. Idempotent. Liefert (Datensatz, geändert?); ohne Telemetrie unverändert.

    ``tcfg`` = der ``telemetrie:``-Config-Block (Spec 2026-09-23). Mit ihm bekommt jeder Abschnitt zusätzlich
    ``stabil`` — die auf ihn geschnittenen stabilen Bereiche des Clips, Stücke unter ``stabil_min_s`` fallen weg —
    und der Datensatz ``stabil_quelle`` mit den drei Schwellen und dem Config-Hash der Messung, aus der sie stammen.
    Ohne ``tcfg`` schreibt die Funktion beides nicht (Aufrufer, die nur die Metadaten brauchen)."""
```

Im Rumpf hinter der Zeile `spitzen = bewegung_spitzen(tele, von, bis)` den `stabil`-Block ergänzen. Der vollständige geänderte Schleifenteil:

```python
    bereiche = stabile_bereiche(tele, tcfg) if tcfg else None
    min_s = float(tcfg["stabil_min_s"]) if tcfg else 0.0
    for a in rec.get("abschnitte") or []:
        b = dict(a)
        claude = dict(b.get("claude") or {})
        for feld, wert in felder.items():
            if feld not in b:
                continue
            quelle[feld] = "rtmd"
            if feld not in schon:
                claude[feld] = b[feld]
            geaendert |= b.get(feld) != wert
            b[feld] = wert
        if claude:
            geaendert |= b.get("claude") != claude
            b["claude"] = claude
        von, bis = float(b.get("von_s", 0)), float(b.get("bis_s", 0))
        w = {**abschnitt_werte(tele, von, bis, fenster_s), **abschnitt_brennweite(tele, von, bis)}
        spitzen = bewegung_spitzen(tele, von, bis)
        if spitzen:
            w["bewegung_spitzen"] = spitzen
        for k in ("bewegungsart", "haltung", "brennweite_mm", "zoom", "bewegung_spitzen"):
            if w.get(k) is not None:
                geaendert |= b.get(k) != w[k]
                b[k] = w[k]
        if bereiche is not None:
            # auf den Abschnitt schneiden; was dabei unter stabil_min_s fällt, ist kein Shot mehr
            geschnitten = [[max(x, von), min(z, bis), wk, bw] for x, z, wk, bw in bereiche
                           if min(z, bis) - max(x, von) >= min_s - 1e-6]
            geaendert |= b.get("stabil") != geschnitten
            b["stabil"] = geschnitten
        neu.append(b)
```

Und am Ende der Funktion, vor `return out, geaendert`:

```python
    out = {**rec, "abschnitte": neu}
    if quelle:
        geaendert |= rec.get("felder_quelle") != quelle
        out["felder_quelle"] = quelle
    if tcfg:
        sq = {"ruhig_max_px": float(tcfg["ruhig_max_px"]), "bewegung_max": float(tcfg["bewegung_max"]),
              "stabil_min_s": float(tcfg["stabil_min_s"]), "config_hash": tele.get("config_hash")}
        geaendert |= rec.get("stabil_quelle") != sq
        out["stabil_quelle"] = sq
    return out, geaendert
```

- [ ] **Step 4: Beide Aufrufe in `index_sections_clip` umstellen**

In `tools/autocut/src/niro_autocut/index_sections.py`, Zeile ~362 (`fenster_s`-Zeile) den Config-Block mitnehmen:

```python
    scfg = cfg["index_sections"]
    icfg = cfg["index"]
    tcfg = cfg.get("telemetrie") or None
    fenster_s = float((cfg.get("telemetrie") or {}).get("fenster_s", 2.0))
```

Cache-Zweig (Zeile ~367):

```python
        neu, geaendert = telemetrie_anwenden(rec, telemetrie, fenster_s, tcfg)
```

API-Zweig (Zeile ~424):

```python
    out, _ = telemetrie_anwenden(out, telemetrie, fenster_s, tcfg)
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_index_sections.py -q
```

Erwartet: PASS. Die bestehenden Tests, die `telemetrie_anwenden(rec, TELE)` ohne `tcfg` aufrufen, bleiben unverändert grün — `TELE` hat kein `ruhige_fenster`, und ohne `tcfg` wird `stabil` gar nicht geschrieben.

- [ ] **Step 6: Gesamtlauf**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest -q
```

Erwartet: PASS.

- [ ] **Step 7: Commit**

```bash
git add tools/autocut/src/niro_autocut/index_sections.py tools/autocut/tests/test_index_sections.py
git commit -m "feat(autocut): Stufe 2b schreibt stabile Bereiche je Abschnitt

telemetrie_anwenden bekommt den telemetrie:-Config-Block und traegt je
Abschnitt stabil ein (die auf ihn geschnittenen stabilen Bereiche) sowie
je Clip stabil_quelle mit den drei Schwellen und dem Config-Hash der
Messung. Wie bewegung_spitzen laeuft das auch bei Cache-Treffern ohne
API-Aufruf. Ohne den Config-Block bleibt das Verhalten unveraendert.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Stufe 2 nennt Mängel je Abschnitt

**Files:**
- Modify: `tools/autocut/src/niro_autocut/broll_index.py` (`CLIP_SCHEMA`, Zeile ~74–82)
- Modify: `tools/autocut/prompts/index-clip.md` (Feldliste bei Zeile 28–31, Beispiel 2 bei Zeile 47, Hinweis bei Zeile 49)
- Test: `tools/autocut/tests/test_broll_index.py`

**Interfaces:**
- Produces: Abschnitte aus Stufe 2 tragen `maengel: list[str]` (Werte aus `MAENGEL`, darf leer sein). Der clip-weite `maengel`-Eintrag bleibt die Vereinigung. Task 5 und 6 unterscheiden **fehlender Schlüssel** (alter Cache → clip-weites Verhalten) von **leerer Liste** (Aussage „hier ist nichts").

- [ ] **Step 1: Write the failing tests**

In `tools/autocut/tests/test_broll_index.py` anhängen:

```python
def test_clip_schema_kennt_maengel_je_abschnitt():
    """Spec 2026-09-23: die Verortung eines Mangels gehört in den Abschnitt, nicht nur in den Clip."""
    absch = B.CLIP_SCHEMA["properties"]["abschnitte"]["items"]
    assert absch["properties"]["maengel"] == {"type": "array", "items": {"type": "string", "enum": B.MAENGEL}}
    assert "maengel" in absch["required"]          # Structured Outputs: alle Felder required
    assert absch["additionalProperties"] is False


def test_prompt_verlangt_maengel_je_abschnitt():
    text = (B.TOOL_ROOT / "prompts" / "index-clip.md").read_text(encoding="utf-8")
    assert "maengel je Abschnitt" in text
    # Beispiel 2 (Kapelle) zeigt den Fall: Mangel nur im zweiten Abschnitt
    assert '"maengel": ["Blick in Kamera"]}], "maengel": ["Blick in Kamera"]' in text
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_broll_index.py -q -k "maengel_je_abschnitt"
```

Erwartet: FAIL mit `KeyError: 'maengel'`.

- [ ] **Step 3: Schema erweitern**

In `tools/autocut/src/niro_autocut/broll_index.py`, `CLIP_SCHEMA`, den `abschnitte`-Eintrag (Zeile ~76):

```python
        "abschnitte": {"type": "array", "items": {"type": "object", "properties": {
            "von_s": {"type": "number"}, "bis_s": {"type": "number"},
            "beschreibung": {"type": "string"},
            "qualitaet": {"type": "integer", "enum": SCORE},
            # Mängel je Abschnitt (Spec 2026-09-23): die clip-weite Liste bleibt die Vereinigung, die Sperre
            # in verify_layout() liest aber diese hier — ein Mangel in einer Sekunde darf keinen Clip kosten.
            "maengel": {"type": "array", "items": {"type": "string", "enum": MAENGEL}},
            "verwendbar": {"type": "boolean"}},
            "required": ["von_s", "bis_s", "beschreibung", "qualitaet", "maengel", "verwendbar"],
            "additionalProperties": False}},
```

- [ ] **Step 4: Prompt erweitern**

In `tools/autocut/prompts/index-clip.md`:

Zeile 28 (`- abschnitte: …`) am Satzende ergänzen:

```
Jeder Abschnitt hat von_s, bis_s, beschreibung (ein Satz), qualitaet (1 bis 5), maengel und verwendbar.
```

Direkt hinter Zeile 30 (`- verwendbar: …`) einen neuen Punkt einfügen:

```
- maengel je Abschnitt: dieselbe Liste wie unten, aber nur, was in DIESEM Abschnitt zu sehen ist. Leer lassen, wenn der Abschnitt sauber ist. Das Schnittprogramm sperrt anhand dieser Liste, nicht anhand der clip-weiten — ein Blick in die Kamera in Sekunde 2 darf die Sekunden 5 bis 12 nicht mitkosten.
```

Zeile 31 (`- maengel: …`) am Ende ersetzen: statt „Ein Mangel steht auch dann in der Liste, wenn er nur in einem Abschnitt auftritt; welcher Abschnitt betroffen ist, steht in dessen beschreibung und verwendbar." schreiben:

```
Diese Liste ist die Vereinigung aller Abschnitte: ein Mangel steht auch dann darin, wenn er nur in einem Abschnitt auftritt. Wo genau er sitzt, steht in maengel des betroffenen Abschnitts.
```

In Beispiel 1 (Zeile 43) den Abschnitt um `"maengel": []` ergänzen, in Beispiel 2 (Zeile 47) den ersten Abschnitt um `"maengel": []` und den zweiten um `"maengel": ["Blick in Kamera"]`.

Zeile 49 („Beachte an Beispiel 2: …") ergänzen um:

```
… der Mangel steht in der clip-weiten Liste UND in maengel des zweiten Abschnitts, der erste Abschnitt hat eine leere Liste.
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_broll_index.py -q
```

Erwartet: PASS. Falls `test_broll_index.py:341` (Prompt nennt alle Schema-Begriffe) anschlägt, ist der Prompt-Text noch nicht vollständig — nachziehen, nicht den Test lockern.

- [ ] **Step 6: Gesamtlauf**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest -q
```

Erwartet: PASS.

- [ ] **Step 7: Commit**

```bash
git add tools/autocut/src/niro_autocut/broll_index.py tools/autocut/prompts/index-clip.md tools/autocut/tests/test_broll_index.py
git commit -m "feat(autocut): Stufe 2 nennt Maengel je Abschnitt

CLIP_SCHEMA bekommt abschnitte[].maengel aus derselben Enum-Liste; die
clip-weite Liste bleibt die Vereinigung. Der Prompt sagte bisher schon,
dass die Verortung in beschreibung und verwendbar steckt - jetzt steht sie
strukturiert da, damit der Pruefer je Abschnitt sperren kann statt je Clip.
Cache-Eintraege ohne das Feld bleiben gueltig.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Gerettete Abschnitte im kompakten Index

**Files:**
- Modify: `tools/autocut/src/niro_autocut/broll_layout.py` (`compact_index_v2`, Zeile ~862)
- Modify: `tools/autocut/scripts/autocut_place_broll.py` (`--compact`-Zweig, Zeile ~239–241)
- Modify: `tools/autocut/prompts/place-broll.md` (Feldliste Zeile 21–22, Regeltabelle Zeile 53)
- Test: `tools/autocut/tests/test_broll_layout.py`

**Interfaces:**
- Consumes: `abschnitte[].maengel` aus Task 4, `abschnitte[].stabil` und `stabil_quelle` aus Task 3.
- Produces: `compact_index_v2(index: dict, cfg: dict) -> list[dict]` — **zweiter Parameter ist neu**. `cfg` braucht `forbidden_maengel` und `telemetrie`. Je Abschnitt zusätzlich `maengel: list[str]`, `stabil: list[list[float]]`; gerettete Abschnitte zusätzlich `gerettet: True` und `trotz: list[str]`.

- [ ] **Step 1: Write the failing tests**

In `tools/autocut/tests/test_broll_layout.py`: `CFG_TELEMETRIE` um die zwei Schlüssel ergänzen (Zeile ~13) …

```python
                  "bewegung_rand_s": 0.5, "bewegung_spitze_faktor": 3.0,
                  "bewegung_max": 2.0, "stabil_min_s": 2.0}
```

… die beiden bestehenden Aufrufe `L.compact_index_v2(idx)` auf `L.compact_index_v2(idx, CFG)` umstellen (Zeile ~230, ~367, ~376) und neue Tests anhängen:

```python
# --------------------------------------------------------------------------- #
# Gerettete Abschnitte im kompakten Index (Spec 2026-09-23)
# --------------------------------------------------------------------------- #

def _idx_gerettet(maengel, stabil=None, hash_=None):
    """Ein Clip, dessen einziger Abschnitt verworfen ist, mit Mängeln und gemessenen stabilen Bereichen."""
    idx = _idx(1)
    c = idx["clips"][0]
    c["maengel"] = list(maengel)
    c["stabil_quelle"] = {"ruhig_max_px": 0.15, "bewegung_max": 2.0, "stabil_min_s": 2.0,
                          "config_hash": hash_ if hash_ is not None else TM.config_hash(CFG_TELEMETRIE)}
    a = c["abschnitte"][0]
    a["verwendbar"] = False
    a["maengel"] = list(maengel)
    a["stabil"] = [[2.0, 8.0, 0.05, 0.4]] if stabil is None else stabil
    return idx


def test_compact_index_v2_rettet_verworfenen_abschnitt_mit_stabilem_bereich():
    cx = L.compact_index_v2(_idx_gerettet(["Wackler", "Unschärfe"]), CFG)
    ab = cx[0]["abschnitte"][0]
    assert ab["gerettet"] is True and ab["stabil"] == [[2.0, 8.0, 0.05, 0.4]]
    assert ab["trotz"] == ["Unschärfe"]            # Wackler fällt weg: im stabilen Bereich widerlegt
    assert ab["maengel"] == ["Wackler", "Unschärfe"]
    assert cx[0]["verwendbar"] is True             # Clip ist wieder sichtbar


def test_compact_index_v2_rettet_nicht_bei_gesperrtem_mangel():
    cx = L.compact_index_v2(_idx_gerettet(["Wackler", "Blick in Kamera"]), CFG)
    assert cx[0]["abschnitte"] == [] and cx[0]["verwendbar"] is False


def test_compact_index_v2_rettet_nicht_ohne_stabilen_bereich():
    cx = L.compact_index_v2(_idx_gerettet(["Wackler"], stabil=[]), CFG)
    assert cx[0]["abschnitte"] == [] and cx[0]["verwendbar"] is False


def test_compact_index_v2_rettet_nicht_bei_anderem_config_hash():
    """Mit anderen Schwellen gemessen: der Bereich sagt nichts über die heutige Konfiguration."""
    cx = L.compact_index_v2(_idx_gerettet(["Wackler"], hash_="000000000000"), CFG)
    assert cx[0]["abschnitte"] == []


def test_compact_index_v2_reicht_maengel_und_stabil_bei_verwendbaren_abschnitten_durch():
    idx = _idx(1)
    a = idx["clips"][0]["abschnitte"][0]
    a["maengel"] = ["Unschärfe"]
    a["stabil"] = [[0.0, 6.0, 0.05, 0.4]]
    idx["clips"][0]["stabil_quelle"] = {"ruhig_max_px": 0.15, "bewegung_max": 2.0, "stabil_min_s": 2.0,
                                        "config_hash": TM.config_hash(CFG_TELEMETRIE)}
    ab = L.compact_index_v2(idx, CFG)[0]["abschnitte"][0]
    assert ab["maengel"] == ["Unschärfe"] and ab["stabil"] == [[0.0, 6.0, 0.05, 0.4]]
    assert "gerettet" not in ab and "trotz" not in ab


def test_compact_index_v2_ohne_neue_felder_wie_bisher():
    ab = L.compact_index_v2(_idx(1), CFG)[0]["abschnitte"][0]
    assert ab["maengel"] == [] and ab["stabil"] == [] and "gerettet" not in ab
```

`_idx(1)` liefert einen Clip mit einem Abschnitt 0–12 s, `verwendbar=True`, `maengel: []` auf Clip-Ebene — die vorhandene Hilfsfunktion in dieser Datei.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_broll_layout.py -q -k "compact_index"
```

Erwartet: FAIL mit `TypeError: compact_index_v2() takes 1 positional argument but 2 were given`.

- [ ] **Step 3: `compact_index_v2` umschreiben**

In `tools/autocut/src/niro_autocut/broll_layout.py` (Zeile ~862) ersetzen:

```python
def _stabil_frisch(c: dict, hash_heute: str) -> bool:
    """Stammen die stabilen Bereiche des Clips aus einer Messung mit den heutigen Schwellen? Sonst zählen sie
    nicht — dieselbe Regel, die 3b und 3c seit dem 22.09. für veraltete Datensätze anwenden (Spec 2026-09-23)."""
    return bool(hash_heute) and (c.get("stabil_quelle") or {}).get("config_hash") == hash_heute


def _abschnitt_kompakt(a: dict) -> dict:
    return {"von_s": a["von_s"], "bis_s": a["bis_s"], "kurz": a.get("beschreibung", ""), "q": a.get("qualitaet"),
            "einstellung": a.get("einstellung"), "perspektive": _perspektive(a), "brennweite": a.get("brennweite"),
            "richtung": a.get("bewegungsrichtung"), "motiv": a.get("hauptmotiv"),
            # gemessen (Spec 2026-09-22): die Auswahl plant auf diesen Werten, nicht auf den Klassen
            "brennweite_mm": a.get("brennweite_mm"), "zoom": a.get("zoom"),
            "bewegungsart": a.get("bewegungsart"), "haltung": a.get("haltung"),
            "bewegung_spitzen": a.get("bewegung_spitzen") or [],
            # Spec 2026-09-23: Mängel dieses Abschnitts und die gemessenen ruhigen Bereiche darin
            "maengel": list(a.get("maengel") or []), "stabil": [list(s) for s in (a.get("stabil") or [])]}


def compact_index_v2(index: dict, cfg: dict) -> list[dict]:
    """Kompakter Index für die Planung. Neben den verwendbaren Abschnitten enthält er die vom Modell verworfenen,
    für die die Messung einen stabilen Bereich ausweist und kein gesperrter Mangel bleibt (Spec 2026-09-23) —
    markiert mit ``gerettet`` und ``trotz`` (die übrigen, nicht sperrenden Mängel). „Wackler" zählt bei geretteten
    Abschnitten nicht als Mangel: sie werden ausschließlich über ihre stabilen Bereiche angeboten, und die sind
    per Definition unter ``ruhig_max_px`` gemessen. Ein Abschnitt ohne ``maengel``-Schlüssel (Index vor der
    Umstellung) wird nie gerettet — dort ist der Grund des Verwerfens nicht bekannt."""
    forbidden = set(cfg["forbidden_maengel"])
    hash_heute = TM.config_hash(cfg["telemetrie"])
    out = []
    for c in index.get("clips") or []:
        frisch = _stabil_frisch(c, hash_heute)
        abschnitte = []
        for a in c.get("abschnitte") or []:
            if a.get("verwendbar"):
                abschnitte.append(_abschnitt_kompakt(a))
                continue
            if not frisch or "maengel" not in a or not (a.get("stabil") or []):
                continue
            uebrig = [m for m in (a.get("maengel") or []) if m != "Wackler"]
            if set(uebrig) & forbidden:
                continue
            abschnitte.append({**_abschnitt_kompakt(a), "gerettet": True, "trotz": uebrig})
        out.append({"ref": clip_ref(c), "datei": c.get("datei"), "ordner": c.get("ordner") or "", "standort": c.get("standort"),
                    "dauer_s": c.get("dauer_s"), "fps": c.get("fps"), "kurz": c.get("beschreibung_kurz", ""),
                    "bewegung": c.get("kamerabewegung"), "tempo": c.get("tempo"), "verwendbar": bool(abschnitte), "abschnitte": abschnitte,
                    "tags": list(c.get("tags") or []), "maengel": list(c.get("maengel") or []), "eignung": list(c.get("eignung") or []),
                    "qualitaet": c.get("qualitaet_gesamt")})
    out.sort(key=lambda x: (str(x["standort"] or ""), x["ordner"], str(x["datei"])))
    return out
```

- [ ] **Step 4: Skript umstellen**

In `tools/autocut/scripts/autocut_place_broll.py` den `--compact`-Zweig (Zeile ~239). Die Config muss **vor** dem Zweig geladen werden, weil `compact_index_v2` sie jetzt braucht:

```python
        _, cfg_broll = effective_broll_cfg(ch, args.profile)
        if args.compact:
            clips = compact_index_v2(index, {**cfg_broll, "telemetrie": ch.config["telemetrie"]})
            gerettet = sum(1 for c in clips for a in c["abschnitte"] if a.get("gerettet"))
            p = ch.write_json(COMPACT_FILE, {"erstellt_am": _dt.datetime.now().isoformat(timespec="seconds"),
                                             "anzahl": len(clips), "clips": clips})
            print(f"Kompakter Index: {p} ({len(clips)} Clips, {sum(1 for c in clips if c['verwendbar'])} mit verwendbaren "
                  f"Abschnitten, davon {gerettet} über die Messung gerettet, {p.stat().st_size // 1024} KB)\n"
                  f"Profil: {Path(__file__).resolve().parents[1] / 'profile' / (args.profile + '.md')}")
            return 0
```

Die bisherige Zeile `_, cfg_broll = effective_broll_cfg(ch, args.profile)` weiter unten (nach `fps = …`) ersatzlos streichen — sie steht jetzt oben.

- [ ] **Step 5: Prompt ergänzen**

In `tools/autocut/prompts/place-broll.md` die Feldliste (Zeile ~22) erweitern:

```
  `abschnitte[{von_s,bis_s,kurz,q,einstellung,perspektive,brennweite,richtung,motiv,brennweite_mm,zoom,bewegungsart,haltung,bewegung_spitzen,maengel,stabil,gerettet,trotz}]`
```

Und darunter erklären:

```
  `stabil` = gemessene ruhige Bereiche `[von_s, bis_s, wackeln_max, bewegung_max]` im Abschnitt; dort ist das Bild
  ruhig genug für einen kurzen Einsetzer. `gerettet: true` heißt: diesen Abschnitt hat der Bild-Index verworfen, die
  Messung widerspricht — **Shots dort müssen vollständig in einem `stabil`-Bereich liegen**, und `trotz` nennt, was
  der Index sonst noch bemängelt hat (meist Unschärfe). Bei normalen Abschnitten ist `stabil` ein Hinweis, kein Zwang:
  ein gewollter Schwenk ist nicht ruhig und bleibt erlaubt. `maengel` gilt je Abschnitt, die clip-weite Liste darunter
  ist nur die Vereinigung.
```

In der Fehlertabelle (Zeile ~95) eine Zeile ergänzen:

```
| `liegt in keinem verwendbaren Abschnitt` / `Abschnitt … hat den Mangel` / `Bereich nicht als stabil gemessen` | Shot in einen `stabil`-Bereich legen oder anderen Abschnitt wählen |
```

- [ ] **Step 6: Run the tests to verify they pass**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_broll_layout.py tests/test_resolve_scripts.py -q
```

Erwartet: PASS.

- [ ] **Step 7: Gesamtlauf**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest -q
```

Erwartet: PASS.

- [ ] **Step 8: Commit**

```bash
git add tools/autocut/src/niro_autocut/broll_layout.py tools/autocut/scripts/autocut_place_broll.py tools/autocut/prompts/place-broll.md tools/autocut/tests/test_broll_layout.py
git commit -m "feat(autocut): geretete Abschnitte im kompakten Index

compact_index_v2 bekommt die Charge-Config und nimmt Abschnitte auf, die
das Modell verworfen hat, sofern die Messung einen stabilen Bereich
ausweist und kein gesperrter Mangel bleibt - markiert mit gerettet und
trotz. Wackler zaehlt dort nicht, weil der Abschnitt nur ueber seine
stabilen Bereiche angeboten wird. Ohne die neuen Felder oder mit einem
anderen Config-Hash bleibt alles wie bisher.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Prüfer sperrt je Abschnitt und warnt bei unruhigem Bereich

**Files:**
- Modify: `tools/autocut/src/niro_autocut/broll_plan.py` (`_usable_spans`, Zeile 225–235)
- Modify: `tools/autocut/src/niro_autocut/broll_layout.py` (Hilfsfunktionen vor `verify_layout`; Mangel- und Lageprüfung Zeile ~653–660; Telemetrie-Block Zeile ~700–730; Schlussbericht Zeile ~797–815)
- Test: `tools/autocut/tests/test_broll_layout.py`, `tools/autocut/tests/test_broll_plan.py`

**Interfaces:**
- Consumes: `abschnitte[].maengel`, `abschnitte[].stabil`, `stabil_quelle` aus Task 3–5; `telemetrie.bewegung_max_im_bereich` aus Task 1.
- Produces: `_usable_spans(c: dict, stabil: bool = False) -> list[tuple[float, float]]` — mit `stabil=True` zusätzlich die `stabil`-Bereiche verworfener Abschnitte, vor dem Zusammenlegen. Der Plan-v1-Pfad (`broll_plan.py:339`) ruft weiter ohne den Parameter auf und bleibt unverändert.

- [ ] **Step 1: Write the failing tests**

In `tools/autocut/tests/test_broll_plan.py` anhängen:

```python
def test_usable_spans_nimmt_stabile_bereiche_nur_auf_wunsch_auf():
    """Plan v1 ruft ohne den Parameter auf und darf sich nicht ändern (Spec 2026-09-23)."""
    c = {"abschnitte": [{"von_s": 0, "bis_s": 2, "verwendbar": False, "stabil": [[0.0, 2.0, 0.05, 0.3]]},
                        {"von_s": 2, "bis_s": 5, "verwendbar": False, "stabil": [[2.0, 4.8, 0.07, 0.3]]},
                        {"von_s": 5, "bis_s": 9, "verwendbar": True}]}
    assert _usable_spans(c) == [(5.0, 9.0)]
    # angrenzende gerettete Bereiche werden zusammengelegt — ein Shot darf über die Abschnittsgrenze laufen
    assert _usable_spans(c, stabil=True) == [(0.0, 4.8), (5.0, 9.0)]
```

`test_broll_plan.py` importiert heute einzelne Namen, keinen Modul-Alias. Für diesen Test die Importzeile (Zeile 8) um `_usable_spans` ergänzen und im Test `_usable_spans(...)` statt `P._usable_spans(...)` schreiben.

In `tools/autocut/tests/test_broll_layout.py` anhängen:

```python
# --------------------------------------------------------------------------- #
# Prüfer je Abschnitt (Spec 2026-09-23)
# --------------------------------------------------------------------------- #

def _idx_abschnitts_maengel(maengel_a, maengel_b, stabil_a=None, stabil_b=None):
    """Clip 1 mit zwei Abschnitten 0–6 s und 6–12 s, je eigene Mängel und stabile Bereiche."""
    idx = _idx()
    c = idx["clips"][0]
    c["maengel"] = sorted(set(maengel_a) | set(maengel_b))
    c["stabil_quelle"] = {"ruhig_max_px": 0.15, "bewegung_max": 2.0, "stabil_min_s": 2.0,
                          "config_hash": TM.config_hash(CFG_TELEMETRIE)}
    vorlage = dict(c["abschnitte"][0])
    c["abschnitte"] = [{**vorlage, "von_s": 0, "bis_s": 6, "maengel": list(maengel_a),
                        "stabil": stabil_a if stabil_a is not None else [[0.0, 6.0, 0.05, 0.4]]},
                       {**vorlage, "von_s": 6, "bis_s": 12, "maengel": list(maengel_b),
                        "stabil": stabil_b if stabil_b is not None else [[6.0, 12.0, 0.05, 0.4]]}]
    return idx


def test_verify_layout_sperrt_nur_den_betroffenen_abschnitt():
    """FX3_8636-Fall: „Blick in Kamera" nur im ersten Abschnitt — der zweite bleibt nutzbar."""
    idx = _idx_abschnitts_maengel(["Blick in Kamera"], [])
    plan = _plan({1: [("Flur/FX3_1.MP4", 7.0, 10.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    res = L.verify_layout(plan, TP, idx, CL, CFG, 25, [_tele("FX3_1.MP4", 25.0)])
    assert not any("Blick in Kamera" in e for e in res.errors)


def test_verify_layout_meldet_den_mangel_des_benutzten_abschnitts():
    idx = _idx_abschnitts_maengel(["Blick in Kamera"], [])
    plan = _plan({1: [("Flur/FX3_1.MP4", 1.0, 4.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    res = L.verify_layout(plan, TP, idx, CL, CFG, 25, [_tele("FX3_1.MP4", 25.0)])
    assert any("Blick in Kamera" in e and "0–6s" in e for e in res.errors)


def test_verify_layout_laesst_wackler_im_stabilen_bereich_fallen():
    """Frage (b) der Spec: die Messung überstimmt den Mangel, Schwelle ist ruhig_max_px."""
    cfg = {**CFG, "forbidden_maengel": ["Blick in Kamera", "Crew im Bild", "Wackler"]}
    idx = _idx_abschnitts_maengel(["Wackler"], [])
    plan = _plan({1: [("Flur/FX3_1.MP4", 1.0, 4.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    res = L.verify_layout(plan, TP, idx, CL, cfg, 25, [_tele("FX3_1.MP4", 25.0)])
    assert not any("Wackler" in e for e in res.errors)
    # ohne stabilen Bereich greift die Sperre wieder
    ohne = _idx_abschnitts_maengel(["Wackler"], [], stabil_a=[])
    res2 = L.verify_layout(plan, TP, ohne, CL, cfg, 25, [_tele("FX3_1.MP4", 25.0)])
    assert any("Wackler" in e for e in res2.errors)


def test_verify_layout_erlaubt_shot_im_stabilen_bereich_eines_verworfenen_abschnitts():
    idx = _idx_abschnitts_maengel([], [])
    for a in idx["clips"][0]["abschnitte"]:
        a["verwendbar"] = False
    plan = _plan({1: [("Flur/FX3_1.MP4", 4.0, 7.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    res = L.verify_layout(plan, TP, idx, CL, CFG, 25, [_tele("FX3_1.MP4", 25.0)])
    # 4–7 s läuft über die Abschnittsgrenze bei 6 s: nur durch das Zusammenlegen erlaubt (FX3_8641-Fall)
    assert not any("verwendbaren Abschnitt" in e for e in res.errors)


def test_verify_layout_warnt_bei_shot_ausserhalb_jedes_stabilen_bereichs():
    """FX3_8663-Fall: der Abschnitt ist verwendbar, die gemessene Bewegung dort aber hoch — nur Warnung."""
    idx = _idx_abschnitts_maengel([], [], stabil_a=[])
    fenster = [[0.0, 0.5, 10.3, "tilt_auf", None], [1.0, 0.5, 8.8, "tilt_auf", None],
               [2.0, 0.5, 9.1, "tilt_auf", None], [3.0, 0.5, 7.4, "tilt_auf", None]]
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    res = L.verify_layout(plan, TP, idx, CL, CFG, 25, [_tele("FX3_1.MP4", 25.0, fenster=fenster)])
    assert not any("stabil" in e for e in res.errors)
    assert any("nicht als stabil gemessen" in w and "10,3" in w for w in res.warnings)


def test_verify_layout_ohne_abschnitts_maengel_sperrt_weiter_clip_weit():
    """Alter Index: kein Abschnitt trägt den Schlüssel maengel — Verhalten wie vor der Umstellung."""
    idx = _idx()
    idx["clips"][0]["maengel"] = ["Blick in Kamera"]
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    res = L.verify_layout(plan, TP, idx, CL, CFG, 25, None)
    assert any("Blick in Kamera" in e for e in res.errors)
    assert any("Abschnitts-Mängel fehlen" in w for w in res.warnings)
```

Die Hilfsfunktion `_tele` in dieser Datei bekommt dafür den bereits vorhandenen `fenster`-Parameter; zusätzlich muss sie `ruhige_fenster` und `dauer_s` liefern, damit die Bewegungsrechnung greift. Falls sie das noch nicht tut, ergänzen:

```python
def _tele(datei, kb_mm, zooms=None, fenster=None, ruhige=None, dauer_s=12.0):
    return {"path": f"/nas/Standort 1/Sortiert/B-Roll/Flur/{datei}", "clip": datei.split(".")[0],
            "quelle": "rtmd", "fps": 25.0, "dauer_s": dauer_s, "fenster_s": 2.0,
            "config_hash": TM.config_hash(CFG_TELEMETRIE),
            "kb_verlauf": [[0.0, kb_mm]], "zooms": zooms or [], "fenster": fenster or [],
            "ruhige_fenster": ruhige if ruhige is not None else [f[0] for f in (fenster or []) if f[1] <= 0.15]}
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_broll_layout.py tests/test_broll_plan.py -q -k "abschnitt or stabil or usable_spans"
```

Erwartet: FAIL — `_usable_spans() got an unexpected keyword argument 'stabil'` und fehlende Meldungstexte.

- [ ] **Step 3: `_usable_spans` erweitern**

In `tools/autocut/src/niro_autocut/broll_plan.py` (Zeile 225) ersetzen:

```python
def _usable_spans(c: dict, stabil: bool = False) -> list[tuple[float, float]]:
    """Verwendbare Abschnitte, direkt angrenzende zusammengelegt (ein Item darf über eine Inhaltsgrenze laufen,
    solange kein unbrauchbarer Abschnitt dazwischen liegt).

    ``stabil=True`` (nur Plan v2, Spec 2026-09-23) nimmt zusätzlich die gemessenen ``stabil``-Bereiche der
    Abschnitte auf, die das Modell verworfen hat. Ob dort ein gesperrter Mangel liegt, prüft ``verify_layout()``
    getrennt je Abschnitt — hier geht es nur um die Frage, wo überhaupt brauchbares Material liegt. Ohne den
    Parameter (Plan v1) ist das Ergebnis unverändert."""
    spans = [(float(a["von_s"]), float(a["bis_s"])) for a in (c.get("abschnitte") or []) if a.get("verwendbar")]
    if stabil:
        spans += [(float(x), float(z)) for a in (c.get("abschnitte") or []) if not a.get("verwendbar")
                  for x, z, *_ in (a.get("stabil") or [])]
    merged: list[list[float]] = []
    for a, z in sorted(spans):
        if merged and a <= merged[-1][1] + EPS:
            merged[-1][1] = max(merged[-1][1], z)
        else:
            merged.append([a, z])
    return [(a, z) for a, z in merged]
```

- [ ] **Step 4: Hilfsfunktionen in `broll_layout.py`**

Direkt vor `def verify_layout(` einfügen:

```python
def _hat_abschnitts_maengel(c: dict) -> bool:
    """True, wenn mindestens ein Abschnitt den Schlüssel ``maengel`` trägt (Index ab Spec 2026-09-23).
    Eine leere Liste ist eine Aussage („hier ist nichts"), ein fehlender Schlüssel ist keine."""
    return any("maengel" in a for a in (c.get("abschnitte") or []))


def _abschnitte_im_bereich(c: dict, von_s: float, bis_s: float) -> list[dict]:
    """Abschnitte, die das Intervall berühren — ein Shot über eine Abschnittsgrenze muss beide erfüllen."""
    return [a for a in (c.get("abschnitte") or [])
            if float(a["von_s"]) - EPS < bis_s and von_s < float(a["bis_s"]) + EPS]


def _stabil_bereiche(c: dict) -> list[tuple[float, float]]:
    return [(float(x), float(z)) for a in (c.get("abschnitte") or []) for x, z, *_ in (a.get("stabil") or [])]


def _in_stabil(c: dict, von_s: float, bis_s: float) -> bool:
    """Liegt der genutzte Quellbereich ganz in einem gemessenen stabilen Bereich?"""
    return any(x - EPS <= von_s and bis_s <= z + EPS for x, z in _stabil_bereiche(c))
```

- [ ] **Step 5: Mangel- und Lageprüfung umstellen**

In `verify_layout` den Block bei Zeile ~652 ersetzen. `ohne_abschnitts_maengel` vor der Schleife bei den anderen Zählern (Zeile ~639) anlegen:

```python
    ohne_abschnitts_maengel = 0     # Clips aus einem Index vor Spec 2026-09-23 (Sperre bleibt clip-weit)
```

Und im Schleifenrumpf:

```python
        # Stabile Bereiche aus einer Messung mit anderen Schwellen zählen nicht — dann verhält sich der Clip
        # wie ohne Telemetrie (Spec 2026-09-23, Randfälle).
        frisch = _stabil_frisch(c, hash_heute)
        spans = _usable_spans(c, stabil=frisch)
        if not any(a - EPS <= p["in_s"] and p["out_s"] <= z + EPS for a, z in spans):
            r.errors.append(f"{tag}: liegt in keinem verwendbaren Abschnitt und in keinem gemessenen stabilen Bereich "
                            f"(erlaubt: {', '.join(f'{a:g}–{z:g}s' for a, z in spans) or 'nichts'}).")
        q_von, q_bis = _quellbereich_s(p, fps)
        stabil_ok = frisch and _in_stabil(c, q_von, q_bis)
        if _hat_abschnitts_maengel(c):
            # Sperre je Abschnitt: der Index verortet den Mangel, der Prüfer darf ihn nicht auf den Clip weiten.
            # „Wackler" entfällt im gemessenen stabilen Bereich — das ist das Überstimmen aus Spec 2026-09-23.
            for a in _abschnitte_im_bereich(c, p["in_s"], p["out_s"]):
                sperrend = set(a.get("maengel") or []) & forbidden
                if stabil_ok:
                    sperrend -= {"Wackler"}
                for m in sorted(sperrend):
                    r.errors.append(f"{tag}: Abschnitt {float(a['von_s']):g}–{float(a['bis_s']):g}s hat den Mangel "
                                    f"„{m}“ — gesperrt.")
        else:
            ohne_abschnitts_maengel += 1
            maengel = set(c.get("maengel") or [])
            if (c.get("personen") or {}).get("blick_in_kamera"):
                maengel.add("Blick in Kamera")
            for m in sorted(maengel & forbidden):
                r.errors.append(f"{tag}: Clip hat den Mangel „{m}“ — gesperrt.")
```

- [ ] **Step 6: Warnung für Shots außerhalb jedes stabilen Bereichs**

Im Telemetrie-Block von `verify_layout`, innerhalb von `if rec is not None and not veraltet:` und hinter der 3c-Schleife:

```python
            # Spec 2026-09-23: der Abschnitt ist verwendbar, der genutzte Bereich aber nicht als ruhig gemessen.
            # Bewusst nur eine Warnung — ein gewollter Schwenk ist nicht ruhig und bleibt erlaubt.
            if frisch and any("stabil" in a for a in (c.get("abschnitte") or [])) and not stabil_ok:
                bw = TM.bewegung_max_im_bereich(rec, von, bis, fen_s)
                bw_txt = "–" if bw is None else f"{bw:.1f}".replace(".", ",")
                r.warnings.append(f"{tag}: Bereich nicht als stabil gemessen (Bewegung max {bw_txt}) — "
                                  f"für einen ruhigen Einsetzer einen `stabil`-Bereich wählen.")
```

`frisch` und `stabil_ok` stammen aus Step 5 und stehen in derselben Schleifeniteration; `von`/`bis`/`fen_s` sind im Block bereits gesetzt. `hash_heute` berechnet `verify_layout` schon heute (Zeile ~641).

Ein neuer Test dazu, ans Ende von `test_broll_layout.py`:

```python
def test_verify_layout_ignoriert_stabile_bereiche_aus_alter_messung():
    """Mit anderen Schwellen abgeleitet: der Bereich sagt nichts über die heutige Konfiguration."""
    idx = _idx_abschnitts_maengel([], [])
    for a in idx["clips"][0]["abschnitte"]:
        a["verwendbar"] = False
    idx["clips"][0]["stabil_quelle"]["config_hash"] = "000000000000"
    plan = _plan({1: [("Flur/FX3_1.MP4", 4.0, 7.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    res = L.verify_layout(plan, TP, idx, CL, CFG, 25, [_tele("FX3_1.MP4", 25.0)])
    assert any("verwendbaren Abschnitt" in e for e in res.errors)
```

- [ ] **Step 7: Schlussbericht ergänzen**

Am Ende von `verify_layout`, **vor** der Zeile `if not tele:` (Zeile ~797) — der Hinweis gilt unabhängig davon, ob Telemetrie vorliegt, weil er den Index betrifft und nicht die Messung:

```python
    if ohne_abschnitts_maengel:
        r.warnings.append(f"{ohne_abschnitts_maengel} von {len(placed)} Shots aus Clips ohne Abschnitts-Mängel — "
                          f"die Sperre greift dort clip-weit wie vor der Umstellung; "
                          f"autocut_index_broll.py --force holt die Verortung nach.")
```

- [ ] **Step 8: Run the tests to verify they pass**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_broll_layout.py tests/test_broll_plan.py -q
```

Erwartet: PASS. Bestehende Tests, die die alte Meldung `„liegt in keinem verwendbaren Abschnitt (verwendbar: …)"` wörtlich prüfen, tragen jetzt den neuen Text — die Erwartung dort auf `"verwendbaren Abschnitt"` kürzen, nicht die Meldung zurückdrehen.

- [ ] **Step 9: Gesamtlauf**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest -q
```

Erwartet: PASS.

- [ ] **Step 10: Commit**

```bash
git add tools/autocut/src/niro_autocut/broll_plan.py tools/autocut/src/niro_autocut/broll_layout.py tools/autocut/tests/test_broll_layout.py tools/autocut/tests/test_broll_plan.py
git commit -m "feat(autocut): Pruefer sperrt je Abschnitt statt je Clip

verify_layout liest die Maengel des Abschnitts, in dem der Shot liegt, und
laesst Wackler fallen, wenn der genutzte Quellbereich in einem gemessenen
stabilen Bereich liegt. _usable_spans nimmt auf Wunsch die stabilen
Bereiche verworfener Abschnitte auf, vor dem Zusammenlegen - sonst fiele
ein Shot ueber eine Abschnittsgrenze durch. Neu als Warnung: Shot in einem
verwendbaren Abschnitt, aber ausserhalb jedes stabilen Bereichs. Ein Index
ohne Abschnitts-Maengel verhaelt sich wie bisher und wird gezaehlt.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Doku

**Files:**
- Modify: `tools/autocut/WORKFLOW-AutoCut.md` (Stufe 2, Stufe 2b, Stufe 3, Telemetrie-Abschnitt)
- Modify: `tools/autocut/README.md` (Tabellenzeile)
- Test: `tools/autocut/tests/test_docs.py`

**Interfaces:**
- Consumes: die Feld- und Meldungsnamen aus Task 1–6. Keine Produktion für spätere Tasks.

- [ ] **Step 1: Write the failing test**

In `tools/autocut/tests/test_docs.py` anhängen:

```python
def test_workflow_erklaert_die_bereichsauswahl():
    text = _text(WORKFLOW)
    for needle in ("stabile Bereiche", "abschnitte[].maengel", "stabil_quelle", "gerettet",
                   "bewegung_max", "stabil_min_s", "nicht als stabil gemessen"):
        assert needle in text, f"WORKFLOW-AutoCut.md: „{needle}“ fehlt"


def test_readme_nennt_die_bereichsauswahl():
    assert "stabile Bereiche" in _text(README)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_docs.py -q -k "bereichsauswahl"
```

Erwartet: FAIL mit `WORKFLOW-AutoCut.md: „stabile Bereiche“ fehlt`.

- [ ] **Step 3: `WORKFLOW-AutoCut.md` ergänzen**

Unter `## Ablauf Stufe 2 — „B-Roll-Index"` (Zeile 249) hinter der Beschreibung der Abschnitte:

```markdown
Je Abschnitt steht seit dem 23.09.2026 auch `maengel` — dieselbe Liste wie clip-weit, aber nur, was in diesem
Abschnitt zu sehen ist. Der Prüfer sperrt anhand dieser Liste; die clip-weite bleibt die Vereinigung und dient
nur der Übersicht. Ein Index aus der Zeit davor trägt das Feld nicht: dann sperrt der Prüfer wie früher
clip-weit und sagt es im Bericht. `autocut_index_broll.py --force` holt die Verortung nach (kostet die Stufe-2-
Token erneut, bei 51 Clips rund 2,50 €).
```

Unter `## Ablauf Stufe 2b — „Nachlauf" (Pflicht vor Stufe 3 v2)` (Zeile 265):

```markdown
Zusätzlich trägt der Nachlauf je Abschnitt `stabil` ein: die gemessenen **stabilen Bereiche**
`[von_s, bis_s, wackeln_max, bewegung_max]` — Läufe benachbarter ruhiger Fenster (`wackeln ≤ ruhig_max_px`,
ohne schnelle Zoomfahrten, `bewegung ≤ bewegung_max`), mindestens `stabil_min_s` lang, auf den Abschnitt
geschnitten. Je Clip kommt `stabil_quelle` dazu (die drei Schwellen und der Config-Hash der Messung, aus der
die Bereiche stammen). Das ist reine Rechnung auf vorhandenen Daten: Cache-Treffer bekommen die Felder ohne
API-Aufruf. Wer `bewegung_max` oder `stabil_min_s` ändert, lässt `autocut_index_sections.py` erneut laufen —
kostenlos, die Telemetrie selbst bleibt gültig (beide Schlüssel stehen in `OHNE_MESSWIRKUNG`).
```

Unter `## Ablauf Stufe 3 — „B-Roll" (v2)` (Zeile 289):

```markdown
Der kompakte Index enthält neben den verwendbaren Abschnitten die **geretteten**: solche, die der Bild-Index
verworfen hat, für die die Messung aber einen stabilen Bereich ausweist und kein gesperrter Mangel bleibt.
Sie tragen `gerettet: true` und `trotz` (was der Index sonst noch bemängelt hat, meist Unschärfe). Shots dort
müssen vollständig in einem `stabil`-Bereich liegen.

`--verify-only` prüft dazu:
- **Mangel je Abschnitt** statt je Clip. `Wackler` entfällt, wenn der genutzte Quellbereich in einem stabilen
  Bereich liegt — die Messung überstimmt das Bildurteil, Schwelle ist `ruhig_max_px`.
- **Lage**: der Shot muss in einem verwendbaren Abschnitt **oder** in einem stabilen Bereich liegen;
  angrenzende Bereiche werden zusammengelegt, ein Shot darf also über eine Abschnittsgrenze laufen.
- **Warnung `Bereich nicht als stabil gemessen`**: der Abschnitt ist verwendbar, die gemessene Bewegung dort
  aber hoch. Bewusst keine Sperre — ein gewollter Schwenk ist nicht ruhig und bleibt erlaubt.
```

Unter `## Telemetrie — „Telemetrie" (seit 21.09.2026)` (Zeile 785), bei den Kalibrierwerten:

```markdown
`bewegung_max` (2,0) und `stabil_min_s` (2,0) sind **unkalibrierte Startwerte** vom 23.09.2026. Die Abnahme
läuft gegen die 30 Urteile vom 22.09. und die vier WLC-Clips aus dem Review
(`tests/test_bereiche_abnahme.py`): kein Kandidat im Beispiel „komplett ungewollt", höchstens zwei der
24 „ungewollt"-Beispiele mit Kandidat, und jeder vom User genannte Bereich liegt in einem Kandidaten.
Wer eine Schwelle ändert, muss dort wieder antreten.
```

- [ ] **Step 4: `README.md` ergänzen**

In der Unterbefehl-Tabelle (Zeile 24–38) drei Zeilen ergänzen:

- Zeile 27 („B-Roll-Index", Stufe 2): „… , Mängel je Abschnitt"
- Zeile 28 („Nachlauf", Stufe 2b): „… , **stabile Bereiche** je Abschnitt (`stabil`, `stabil_quelle`)"
- Zeile 35 („Telemetrie"): bei den Abnehmern „Stufe 3 (…)" um „stabile Bereiche" erweitern

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest tests/test_docs.py -q
```

Erwartet: PASS.

- [ ] **Step 6: Gesamtlauf**

```bash
cd tools/autocut && "/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python3" -m pytest -q
```

Erwartet: PASS, keine Fehler.

- [ ] **Step 7: Commit**

```bash
git add tools/autocut/WORKFLOW-AutoCut.md tools/autocut/README.md tools/autocut/tests/test_docs.py
git commit -m "docs(autocut): Bereichsauswahl in Workflow und README

Stufe 2 (Maengel je Abschnitt), Stufe 2b (stabil, stabil_quelle), Stufe 3
(gerettete Abschnitte, Sperre je Abschnitt, neue Warnung) und der
Telemetrie-Abschnitt nennen die unkalibrierten Startwerte samt Abnahme.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Nach dem Plan: erste Probe an WLC

Kein Task — das ist der Lauf mit dem User zusammen, nach Abschluss aller sieben Tasks. Die Charge liegt unter `projects/WLC/Recruiting/2026-07 Erster Dreh` **im Hauptordner des Repos**, nicht im Worktree.

1. `sh tools/studio_abgleich.sh --charge "projects/WLC/Recruiting/2026-07 Erster Dreh"`
2. `broll.forbidden_maengel: ["Blick in Kamera", "Crew im Bild"]` in `_intern/autocut/config.yaml` (offener Punkt im Protokoll vom 23.09.: „Logo/Marke" ist bei WLC gewollt, betrifft 27 der 51 Clips)
3. `venv/bin/python scripts/autocut_index_broll.py "<Charge>" --force` (51 Clips, ~2,50 €)
4. `venv/bin/python scripts/autocut_index_sections.py "<Charge>"` (Cache, keine API-Kosten)
5. `venv/bin/python scripts/autocut_place_broll.py "<Charge>" --compact`
6. Auswahl für Video 1 neu; Ergebnis als Sichtungs-Video gegen `Ergebnisse/Rohschnitt/video-1-broll-sichtung.mp4` und `video-1-broll-nachtrag.mp4` halten.
7. Protokoll-Eintrag, dann `sh tools/studio_abgleich.sh --charge "<Charge>"`

Maßgeblich ist Schritt 6: kommen die vier vom User genannten Bereiche in der neuen Auswahl vor, und wird nichts hereingeholt, was er verworfen hat.

Offen bleibt **R1#2** aus dem Testsatz — der eine Kandidaten-Vorschlag in „ungewollt"-Material ohne Anmerkung. Der 5-s-Ausschnitt liegt in `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schwenks/_intern/work/schwenk-beispiele.mp4` bei 5–10 s. Fällt das Urteil „da ist nichts Brauchbares", muss die Zahl in `test_abnahme_hoechstens_zwei_kandidaten_in_ungewolltem_material` auf 1 sinken und die Schwelle nachgezogen werden.
