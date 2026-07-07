# Footage-Workflow Anchoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Den bewährten Footage-Sortier-Workflow als wiederverwendbare Funktionen (`transcribe_all`, `build_move_plan`) im `footage/`-Paket verankern, sodass ein neuer Dreh nur Pfad + Konzept braucht und komplett durchläuft — ohne die Interview-Pipeline zu berühren.

**Architecture:** Zwei neue Module im bestehenden `src/niro_transcribe/footage/`-Subpaket: `pipeline.py` (Phase-1-Orchestrierung) und `planning.py` (Manifest + Zuordnungsplan). Sie generalisieren die projekt-spezifischen Ad-hoc-Skripte (`projects/LohiBW Recruiting/run_phase1.py`, `build_plan.py`). Verschieben (`mover.execute_plan`) existiert bereits. Klassifikation bleibt Claude-in-Session (kein Code). Docs beschreiben den Voll-Durchlauf.

**Tech Stack:** Python ≥3.11, `requests` (vorhanden), ffmpeg (System), pytest. Keine neuen Dependencies.

## Global Constraints

- **Nur ElevenLabs Scribe mit Diarisation**, kein Whisper.
- **Kein Footage geht verloren:** jeder Clip genau einmal im Manifest; `MovePlan.validate(discovered)` muss `[]` sein, bevor verschoben wird.
- **Dateinamen bleiben** (Struktur nur über Ordner). Multi-Cam-Trennung via `<Kamera>/`-Unterordner **nur bei Interviews**; gescriptete Takes liegen flach im Szenen-Ordner.
- **Interview-Pipeline unberührt:** KEINE Datei außerhalb `src/niro_transcribe/footage/`, `tests/footage/` und der genannten Docs ändern. `project.py`, `report.py`, `briefs.py`, `verify.py`, `models.py`, `config.py`, `cache.py`, `transcribe/*` NICHT modifizieren. Regressions-Gate: volle Suite (inkl. ~30 Interview-Tests) grün.
- Code-Stil: englische Bezeichner, knappe deutsche Fehler-/Doku-Texte. venv-Tests: `venv/bin/python -m pytest <pfad> -v`.

---

### Task 1: `pipeline.transcribe_all` (Phase-1-Orchestrierung)

**Files:**
- Create: `src/niro_transcribe/footage/pipeline.py`
- Test: `tests/footage/test_pipeline.py`

**Interfaces:**
- Consumes: `discover_clips`, `Clip` (`discover.py`); `clip_fingerprint`, `transcribe_clip` (`transcribe_clips.py`); `extract_audio` (`audio.py`); `transcribe_scribe` (`transcribe/elevenlabs.py`); `TranscriptCache` (`cache.py`); `Config` (`config.py`).
- Produces: `def transcribe_all(footage_root, project_dir, *, api_key=None, diarize=True, extractor=extract_audio, transcriber=transcribe_scribe, log=print) -> list[dict]` — findet Clips, transkribiert je Clip (gecacht in `project_dir/cache/`), räumt das temporäre WAV weg, schreibt `project_dir/transcripts_index.json` inkrementell und gibt die Record-Liste zurück. Resilient: ein Clip-Fehler bricht den Lauf nicht ab (Record bekommt `ok=False, error=...`). `api_key=None` → `Config.load()`.

- [ ] **Step 1: Write the failing test**

```python
# tests/footage/test_pipeline.py
import json
from pathlib import Path

from niro_transcribe.footage.pipeline import transcribe_all
from niro_transcribe.models import Transcript, Word


def _fake_extract(video, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{Path(video).stem}.wav"
    p.write_bytes(b"wav")
    return p


def _fake_transcribe(audio, api_key, *, diarize=True):
    if "BAD" in Path(audio).name:
        raise RuntimeError("boom")
    return Transcript(source_file=Path(audio).name, engine="scribe", text="hallo welt",
                      words=[Word("hallo", 0.0, 0.5, "speaker_0"), Word("welt", 0.5, 1.0, "speaker_1")])


def test_transcribe_all_resilient_and_writes_index(tmp_path):
    foot = tmp_path / "footage"
    (foot / "Kamera-A").mkdir(parents=True)
    (foot / "Kamera-A" / "GOOD.mp4").write_bytes(b"v")
    (foot / "Kamera-A" / "BAD.mp4").write_bytes(b"v")
    proj = tmp_path / "proj"

    recs = transcribe_all(foot, proj, api_key="k", extractor=_fake_extract,
                          transcriber=_fake_transcribe, log=lambda *_: None)

    by = {r["name"]: r for r in recs}
    assert by["GOOD.mp4"]["ok"] is True
    assert by["GOOD.mp4"]["speakers"] == ["speaker_0", "speaker_1"]
    assert by["GOOD.mp4"]["duration_s"] == 1.0
    assert by["BAD.mp4"]["ok"] is False and "boom" in by["BAD.mp4"]["error"]
    # Index-Datei geschrieben und vollständig
    idx = json.loads((proj / "transcripts_index.json").read_text(encoding="utf-8"))
    assert len(idx) == 2
    # WAV des erfolgreichen Clips wurde aufgeräumt
    assert not (proj / "work" / "GOOD.wav").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/jansantos/NIRO Transcribe" && venv/bin/python -m pytest tests/footage/test_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError` für `pipeline`

- [ ] **Step 3: Write minimal implementation**

```python
# src/niro_transcribe/footage/pipeline.py
from __future__ import annotations

import json
from pathlib import Path

from ..config import Config
from ..cache import TranscriptCache
from ..transcribe.elevenlabs import transcribe_scribe
from .audio import extract_audio
from .discover import discover_clips
from .transcribe_clips import clip_fingerprint, transcribe_clip


def transcribe_all(footage_root, project_dir, *, api_key=None, diarize=True,
                   extractor=extract_audio, transcriber=transcribe_scribe,
                   log=print) -> list[dict]:
    project_dir = Path(project_dir)
    cache = TranscriptCache(project_dir / "cache")
    work = project_dir / "work"
    index_path = project_dir / "transcripts_index.json"
    if api_key is None:
        api_key = Config.load().elevenlabs_api_key

    clips = discover_clips(footage_root)
    index: list[dict] = []
    for i, clip in enumerate(clips, 1):
        rec = {
            "path": str(clip.path), "camera": clip.camera, "name": clip.path.name,
            "sidecar": clip.sidecar.name if clip.sidecar else None,
            "fingerprint": clip_fingerprint(clip.path),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work,
                                diarize=diarize, extractor=extractor, transcriber=transcriber)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({"ok": True, "duration_s": round(t.duration(), 1),
                        "n_words": len(t.words), "speakers": speakers, "text": t.text})
            wav = work / f"{clip.path.stem}.wav"
            if wav.exists():
                wav.unlink()
            log(f"{i}/{len(clips)} OK [{clip.camera}] {clip.path.name}")
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            log(f"{i}/{len(clips)} FEHLER [{clip.camera}] {clip.path.name}: {rec['error']}")
        index.append(rec)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/jansantos/NIRO Transcribe" && venv/bin/python -m pytest tests/footage/test_pipeline.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/footage/pipeline.py tests/footage/test_pipeline.py
git commit -m "feat(footage): transcribe_all phase-1 orchestration (reusable, resilient)"
```

---

### Task 2: `planning.build_move_plan` (Manifest + Zuordnungsplan)

**Files:**
- Create: `src/niro_transcribe/footage/planning.py`
- Test: `tests/footage/test_planning.py`

**Interfaces:**
- Consumes: `Move`, `MovePlan` (`move_plan.py`); `Clip` (`discover.py`, nur zum Lesen von `.path`/`.camera`).
- Produces:
  - `class PlanResult` (dataclass): `plan: MovePlan`, `markdown: str`, `flags: list`, `balance: dict`.
  - `def slug(text: str, n: int = 32) -> str`, `def person_slug(name, aliases=None) -> str`.
  - `def build_move_plan(clips, classifications, script, sort_root, *, aliases=None) -> PlanResult`.
    - `classifications`: `dict[name -> {category, video_nr, row_id, person, confidence, note}]` (category ∈ scripted|interview|broll|unsure).
    - `script`: `{"videos":[{"nr","titel","rows":[{"id","typ","text"}]}]}`.
    - Routing: scripted+row → `<sort_root>/Video <nr> - <titel>/NN_<rowsuffix>_<slug>/<name>` (flach); scripted ohne row → `_nicht_zugeordnet`; interview → `Interviews/<person>/<camera>/<name>`; broll → `B-Roll/<name>`; sonst → `_nicht_zugeordnet`. `person_slug(None)` → `"_ohne_Namen"`; `aliases` führt Schreibvarianten zusammen.
    - `balance` enthält u. a. `validate_ok` (== leere `plan.validate(discovered)`).

- [ ] **Step 1: Write the failing test**

```python
# tests/footage/test_planning.py
from pathlib import Path

from niro_transcribe.footage.discover import Clip
from niro_transcribe.footage.planning import build_move_plan, person_slug


SCRIPT = {"videos": [
    {"nr": 1, "titel": "Der Weg", "rows": [
        {"id": "1_HookA", "typ": "scripted", "text": "In welcher Kanzlei wirst du Chef?"},
        {"id": "1_Szene1", "typ": "interview", "text": "Frage: Wie kamst du hierher?"},
    ]},
]}


def _clip(path, camera):
    return Clip(path=Path(path), camera=camera, sidecar=None)


def test_person_slug_alias_and_none():
    assert person_slug(None) == "_ohne_Namen"
    assert person_slug("Suzan Baözen", {"Suzan Baözen": "Suzan Baüsen"}) == "Suzan Baüsen"


def test_build_move_plan_routing_and_balance(tmp_path):
    clips = [
        _clip("/f/Kamera-C/C01.mp4", "Kamera-C"),          # scripted
        _clip("/f/Kamera-A/A01.mp4", "Kamera-A"),          # interview Suzan (A)
        _clip("/f/Kamera-B/B01.mp4", "Kamera-B"),          # interview Suzan (B, andere Schreibweise)
        _clip("/f/Kamera-C/C02.mp4", "Kamera-C"),          # broll
        _clip("/f/Kamera-C/C03.mp4", "Kamera-C"),          # unsure
    ]
    cls = {
        "C01.mp4": {"category": "scripted", "video_nr": 1, "row_id": "1_HookA", "confidence": "hoch"},
        "A01.mp4": {"category": "interview", "person": "Suzan Baüsen"},
        "B01.mp4": {"category": "interview", "person": "Suzan Baözen"},
        "C02.mp4": {"category": "broll"},
        "C03.mp4": {"category": "unsure", "note": "unklar"},
    }
    sort = tmp_path / "sortiert"
    res = build_move_plan(clips, cls, SCRIPT, sort, aliases={"Suzan Baözen": "Suzan Baüsen"})

    dst = {Path(m.src).name: m.dst for m in res.plan.moves}
    assert dst["C01.mp4"] == str(sort / "Video 1 - Der Weg" / "01_HookA_In-welcher-Kanzlei-wirst-du-Chef" / "C01.mp4")
    assert dst["A01.mp4"] == str(sort / "Interviews" / "Suzan Baüsen" / "Kamera-A" / "A01.mp4")
    assert dst["B01.mp4"] == str(sort / "Interviews" / "Suzan Baüsen" / "Kamera-B" / "B01.mp4")
    assert dst["C02.mp4"] == str(sort / "B-Roll" / "C02.mp4")
    assert dst["C03.mp4"] == str(sort / "_nicht_zugeordnet" / "C03.mp4")
    assert res.balance["validate_ok"] is True
    assert res.balance == {"clips": 5, "scripted": 1, "interview": 2, "broll": 1, "nicht": 1, "validate_ok": True}
    assert "Zuordnungsplan" in res.markdown
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/jansantos/NIRO Transcribe" && venv/bin/python -m pytest tests/footage/test_planning.py -v`
Expected: FAIL — `ModuleNotFoundError` für `planning`

- [ ] **Step 3: Write minimal implementation**

```python
# src/niro_transcribe/footage/planning.py
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .move_plan import Move, MovePlan


@dataclass
class PlanResult:
    plan: MovePlan
    markdown: str
    flags: list
    balance: dict


def slug(text: str, n: int = 32) -> str:
    text = re.sub(r"[^0-9A-Za-zÄÖÜäöüß ]", "", text)
    return "-".join(text.split())[:n].strip("-")


def person_slug(name, aliases=None) -> str:
    if not name:
        return "_ohne_Namen"
    name = (aliases or {}).get(name.strip(), name.strip())
    return re.sub(r"[^0-9A-Za-zÄÖÜäöüß ._-]", "", name).strip()


def build_move_plan(clips, classifications, script, sort_root, *, aliases=None) -> PlanResult:
    sort_root = Path(sort_root)
    rowmap = {}
    titel = {}
    for v in script["videos"]:
        titel[v["nr"]] = v["titel"]
        for i, row in enumerate(v["rows"], 1):
            rowmap[row["id"]] = {"video_nr": v["nr"], "order": i, "typ": row["typ"], "text": row["text"]}

    moves = []
    flags = []
    groups = {"scripted": {}, "interview": {}, "broll": [], "nicht": []}
    for c in clips:
        name = c.path.name
        o = classifications.get(name, {}) or {}
        cat = o.get("category")
        if cat == "scripted" and o.get("row_id") in rowmap:
            r = rowmap[o["row_id"]]
            vid = r["video_nr"]
            if o.get("confidence") == "niedrig":
                flags.append(f"Gescriptet unsicher: {name} -> {o['row_id']}")
            suffix = o["row_id"].split("_", 1)[1] if "_" in o["row_id"] else o["row_id"]
            folder = f"{r['order']:02d}_{suffix}_{slug(r['text'])}"
            dst = sort_root / f"Video {vid} - {titel[vid]}" / folder / name
            groups["scripted"].setdefault(f"V{vid}/{folder}", []).append(name)
        elif cat == "scripted":
            flags.append(f"Sprech-Take ohne Script-Zeile: {name}")
            dst = sort_root / "_nicht_zugeordnet" / name
            groups["nicht"].append((name, "kein Row-Match"))
        elif cat == "interview":
            person = person_slug(o.get("person"), aliases)
            dst = sort_root / "Interviews" / person / c.camera / name
            groups["interview"].setdefault(person, []).append((name, c.camera))
            if person == "_ohne_Namen":
                flags.append(f"Interview ohne Namen: {name}")
        elif cat == "broll":
            dst = sort_root / "B-Roll" / name
            groups["broll"].append(name)
        else:
            flags.append(f"Unsicher/unbekannt: {name} ({o.get('note', '')})")
            dst = sort_root / "_nicht_zugeordnet" / name
            groups["nicht"].append((name, o.get("note", "") or "unsure"))
        moves.append(Move(str(c.path), str(dst)))

    plan = MovePlan(moves=moves)
    discovered = [str(c.path) for c in clips]
    problems = plan.validate(discovered)
    balance = {
        "clips": len(clips),
        "scripted": sum(len(v) for v in groups["scripted"].values()),
        "interview": sum(len(v) for v in groups["interview"].values()),
        "broll": len(groups["broll"]),
        "nicht": len(groups["nicht"]),
        "validate_ok": not problems,
    }

    L = [
        "# Zuordnungsplan\n",
        f"**Bilanz:** {balance['clips']} Clips = {balance['scripted']} gescriptet + "
        f"{balance['interview']} interview + {balance['broll']} b-roll + {balance['nicht']} nicht-zugeordnet\n",
        f"**validate():** {'OK (leer)' if not problems else '; '.join(problems)}\n",
        "\n## Gescriptete Szenen\n",
    ]
    for f in sorted(groups["scripted"]):
        L.append(f"- **{f}** ({len(groups['scripted'][f])}): " + ", ".join(groups["scripted"][f]))
    L.append("\n## Interviews (nach Person)\n")
    for p in sorted(groups["interview"]):
        items = groups["interview"][p]
        L.append(f"- **{p}** ({len(items)}): " + ", ".join(f"{n}[{(cam or '?').split()[0]}]" for n, cam in items))
    L.append(f"\n## B-Roll ({len(groups['broll'])})\n" + ", ".join(sorted(groups["broll"])))
    L.append(f"\n\n## _nicht_zugeordnet ({len(groups['nicht'])})\n")
    for n, d in groups["nicht"]:
        L.append(f"- {n}: {d}")
    if flags:
        L.append(f"\n## ⚠️ Bitte prüfen ({len(flags)})\n")
        for fl in flags:
            L.append(f"- {fl}")

    return PlanResult(plan=plan, markdown="\n".join(L), flags=flags, balance=balance)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/jansantos/NIRO Transcribe" && venv/bin/python -m pytest tests/footage/test_planning.py -v`
Expected: PASS (2 Tests)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/footage/planning.py tests/footage/test_planning.py
git commit -m "feat(footage): build_move_plan reusable manifest + Zuordnungsplan builder"
```

---

### Task 3: Doku auf Voll-Durchlauf + Regressions-Gate

**Files:**
- Modify (überschreiben): `WORKFLOW-Footage.md`
- Modify (überschreiben): `prompts/sort-footage.md`
- Test: keiner (Doku) — Regressions-Nachweis über die volle Suite in Step 3.

**Interfaces:**
- Consumes: `transcribe_all` (Task 1), `build_move_plan` (Task 2), `execute_plan` (vorhanden).
- Produces: aktualisierte Betriebsdoku (Voll-Durchlauf, kein Review-Halt, zwei Auslöser-Sätze).

- [ ] **Step 1: `WORKFLOW-Footage.md` mit diesem Inhalt überschreiben**

```markdown
# Workflow — Footage sortieren (Voll-Durchlauf, Claude in der Session)

Auslöser: **„Footage sortieren: <Pfad>"** + Konzept-Dokument anhängen.
(Die andere Funktion — „Video-Auswahl / Videopläne" — ist die Interview-Pipeline
in `WORKFLOW.md` und bleibt davon unberührt.)

Voraussetzung: `.env` (ELEVENLABS_API_KEY) geladen, ffmpeg im PATH, SSD gemountet.

Konvention: Rohmaterial `<Projekt>/01_Footage/<Kamera>/…`; Ausgabe →
`<Projekt>/sortiert/`. Arbeitsdateien (cache, index, plan, manifest, log) im Repo
unter `projects/<Name>/`.

Ablauf (läuft ohne Halt durch; Sicherheit über Undo-Log):
1. **Konzept lesen.** Das angehängte PDF/Sheet in der Session lesen und in die
   Struktur `script_structured.json` bringen: `{"videos":[{"nr","titel",
   "rows":[{"id","typ","text"}]}]}`, typ ∈ scripted|interview|visual.
2. **Transkribieren.** `transcribe_all(footage_root, project_dir)` — Scribe +
   Diarisation, gecacht; schreibt `transcripts_index.json`.
3. **Klassifizieren.** Per Fan-out-Agenten (nach `prompts/sort-footage.md`) jeden
   Clip gegen die Struktur → `classifications` (category scripted|interview|broll|
   unsure, + video_nr/row_id/person). Kameramann via Diarisation ignorieren.
4. **Plan bauen.** `build_move_plan(clips, classifications, script, sort_root,
   aliases=...)` → `PlanResult` (Manifest + `zuordnungsplan.md`-Text). `validate()`
   muss leer sein, sonst STOPP und melden.
5. **Verschieben.** `execute_plan(plan, log, discovered_srcs=...)` → verschiebt
   sofort, schreibt `_verschiebe_log.jsonl` (Undo).
6. **Bilanz melden.** Quelle==Ziel bestätigen; Undo-Hinweis: `undo(log)`.

Rückgängig: `from niro_transcribe.footage.mover import undo; undo(log_path)`.
```

- [ ] **Step 2: `prompts/sort-footage.md` mit diesem Inhalt überschreiben**

```markdown
# Prompt — Footage sortieren (in der Session, Claude = Brain, Voll-Durchlauf)

Auslöser: „Footage sortieren: <Pfad>" + Konzept anhängen. Zuordnung über den
transkribierten **Ton**, nicht über Dateinamen. Kein Footage geht verloren
(alles Unklare → `_nicht_zugeordnet/`, nichts wird gelöscht). Läuft ohne
Review-Halt durch; Fehl-Zuordnungen sind per `undo(log)` umkehrbar.

## Ablauf
1. **Konzept → Struktur.** Angehängtes PDF/Sheet lesen, je Video geordnete rows
   mit typ ∈ {scripted, interview, visual} und Soll-Text bauen (script_structured.json).
2. **Transkribieren.** `transcribe_all(footage_root, project_dir)` (Scribe +
   Diarisation, gecacht).
3. **Sprecher bestimmen.** Kameramann/Interviewer (spricht auch, gibt Regie) zählt
   NIE; nur die Wörter des Befragten/Sprechers nutzen.
4. **Klassifizieren (Fan-out).** Clips in Batches an parallele Agenten; jeder Clip:
   - **scripted** — Ton matcht ~wörtlich eine `scripted`-row → video_nr + row_id.
     Multi-Cam desselben Satzes: alle in denselben Szenen-Ordner (flach). Takes → derselbe Ordner.
     Mehrere Sätze in einem Clip (selten): Primärsatz-Regel + im Plan vermerken.
   - **interview** — freie Antwort („Frage an … Sie erzählt …") → nach Person; Name
     aus Transkript, sonst `_ohne_Namen`. A/B-Winkel je Kamera getrennt.
   - **broll** — kein verwertbarer O-Ton / nur Ambiente/Regie / „Hook C ohne Text".
   - **unsure** — nicht sicher.
5. **Plan bauen.** `build_move_plan(clips, classifications, script, sort_root,
   aliases=...)`; `PlanResult.plan.validate(discovered)` MUSS `[]` sein.
6. **Verschieben.** `execute_plan(plan, log, discovered_srcs=[c.path for c in clips])`
   → sofort, mit Undo-Log. Danach Bilanz bestätigen.

## Regeln
- Original-Dateinamen NIE ändern. Im Zweifel `_nicht_zugeordnet/` statt raten.
- Nur ElevenLabs Scribe, kein Whisper.
```

- [ ] **Step 3: Volle Test-Suite als Regressions-Gate**

Run: `cd "/Users/jansantos/NIRO Transcribe" && venv/bin/python -m pytest -q`
Expected: PASS — alle Tests grün (footage + die ~30 Interview-Pipeline-Tests), Beweis dass die Interview-Funktion unverändert läuft.

- [ ] **Step 4: Commit**

```bash
git add WORKFLOW-Footage.md prompts/sort-footage.md
git commit -m "docs(footage): full run-through workflow + two-function triggers"
```

---

## Nach der Implementierung

Der Footage-Workflow ist damit reproduzierbar: neuer Dreh = „Footage sortieren: <Pfad>" + Konzept anhängen → Claude fährt Schritte 1–6. Die LohiBW-Ad-hoc-Skripte bleiben als Erstlauf-Beleg. Die Interview-Pipeline (`WORKFLOW.md`) ist unangetastet und durch die grüne Suite als unverändert nachgewiesen.
