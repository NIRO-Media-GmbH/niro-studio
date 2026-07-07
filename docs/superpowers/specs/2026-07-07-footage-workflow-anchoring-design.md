# Footage-Workflow fest verankern — Design (Spec)

Datum: 2026-07-07
Status: Design bestätigt

## Zweck

Den beim Erstlauf (LohiBW) bewährten Footage-Sortier-Workflow aus projekt-
spezifischen Ad-hoc-Skripten in **wiederverwendbare Tool-Funktionen** heben, so
dass ein neuer Dreh nur noch **Pfad + Konzept** braucht und **komplett durchläuft**
(inkl. Verschieben; Sicherheit über Undo-Log). Die bestehende Interview-Pipeline
(„Interview → Videopläne mit Timestamps + Dramaturgie") bleibt **unverändert und
lauffähig**.

## Betriebsmodell (unverändert)

Läuft über die Claude-App; Claude = Orchestrator + „Brain". Mechanisch/Code: Audio
+ Scribe, Manifest bauen/prüfen, Verschieben. Semantisch/in-Session: Konzept lesen
→ Szenen-Struktur, und die Klassifikation (Fan-out-Agenten). Nur ElevenLabs Scribe.

## Wiederverwendbare Funktionen (neu, im `footage/`-Subpaket)

- `pipeline.transcribe_all(footage_root, project_dir, *, api_key=None) -> list[dict]`
  Phase 1: `discover_clips` → je Clip `transcribe_clip` (Audio via ffmpeg, Scribe,
  gecacht in `project_dir/cache/`), schreibt `project_dir/transcripts_index.json`
  (Records: name, camera, sidecar, speakers, duration_s, text, ok/error), resilient
  pro Clip (ein Fehler bricht den Lauf nicht ab). Gibt die Records zurück.

- `planning.build_move_plan(clips, classifications, script, sort_root, *, aliases=None) -> PlanResult`
  Phase 2: aus (Klassifikation + Konzept-Struktur) das Ziel je Clip bestimmen und
  ein `MovePlan` + menschenlesbaren `zuordnungsplan.md`-Text bauen.
  - `clips`: `list[Clip]` (aus `discover_clips`).
  - `classifications`: `dict[name -> {category, video_nr, row_id, person, confidence, note}]`,
    category ∈ {scripted, interview, broll, unsure}.
  - `script`: geparste Struktur `{"videos":[{"nr","titel","rows":[{"id","typ","text"}]}]}`.
  - `sort_root`: Zielwurzel (z. B. `<footage-Elternordner>/sortiert`).
  - `aliases`: optionale Namens-Normalisierung (ASR-Schreibvarianten → ein Name).
  - Routing: scripted→`<Video>/NN_<Szene>_<kurz>/…`; Multi-Cam getrennt via
    `<Kamera>/` NUR bei Interviews; interview→`Interviews/<Person>/<Kamera>/…`;
    broll→`B-Roll/…`; unsure/kein-Row→`_nicht_zugeordnet/…`. Dateinamen bleiben.
  - Rückgabe `PlanResult`: `.plan` (MovePlan), `.markdown` (str), `.flags` (list[str]),
    `.balance` (dict mit Zählwerten). `PlanResult.plan.validate(discovered)` MUSS `[]`
    sein.

- `mover.execute_plan(plan, log_path, *, discovered_srcs, dry_run=False)` — existiert
  bereits (geprüftes Verschieben, Undo-Log). Phase 3.

Die ad-hoc `projects/LohiBW Recruiting/*.py` bleiben als Erstlauf-Beleg liegen.

## Voll-Durchlauf (kein Review-Halt)

Eingabe: `footage_root` + Konzept-Dokument. Ablauf ohne Stopp:
1. Konzept in der Session lesen → `script_structured.json` (Claude).
2. `transcribe_all(footage_root, project_dir)`.
3. Klassifikation per Fan-out-Agenten gegen die Struktur → `classifications`.
4. `build_move_plan(...)` → Manifest + `zuordnungsplan.md`; `validate()` == [].
5. `execute_plan(plan, log, discovered_srcs=...)` → **verschiebt sofort**, Undo-Log.
6. Bilanz melden (Quelle==Ziel) + Undo-Hinweis.

Fehl-Zuordnungen sind über `undo(log)` vollständig umkehrbar (David-Entscheidung
gegen einen Review-Halt).

## Zwei Funktionen — getrennte Nutzung

Unterschieden durch Input und Auslöser-Satz; wird fest in die Docs geschrieben:

| | Interviews → Videopläne | Footage sortieren |
|---|---|---|
| Input | WAV-Interviews (`audio/`) + Konzept | Ordner-Pfad mit MP4s + Konzept |
| Auslöser | „**Video-Auswahl / Videopläne** für …" | „**Footage sortieren**: `<Pfad>`" |
| Ergebnis | Dokument mit von–bis-Timestamps + Dramaturgie (.md/.pdf) | MP4s verschoben (+ Undo-Log) |
| Dateien bewegt | nein (nur lesen) | ja (umkehrbar) |

Auslöser-Schlüsselwörter: „Video-Auswahl/Videopläne" → Interview-Pipeline;
„Footage sortieren" → Footage-Sortierer. Bei Unklarheit erkennt Claude die Funktion
am Input (WAV vs. MP4-Ordner); im Zweifel eine kurze Rückfrage.

## Die andere Funktion bleibt unberührt (harte Absicherung)

Alle Änderungen betreffen **ausschließlich** das `footage/`-Subpaket und Doku.
**Keine** Datei der Interview-Pipeline (`project.py`, `report.py`, `briefs.py`,
`verify.py`, `segment`/`select`-Prompts, …) wird geändert. Regressions-Gate: die
**komplette bestehende Test-Suite** (Interview-Tests inklusive) bleibt grün.

## Tests

- `tests/footage/test_pipeline.py`: `transcribe_all` mit injizierten
  extractor/transcriber → Cache-Nutzung, Resilienz bei einem Clip-Fehler, Index-Datei
  geschrieben.
- `tests/footage/test_planning.py`: `build_move_plan` → Routing je Kategorie,
  Multi-Cam-Trennung bei Interviews, Alias-Zusammenführung, `validate()`==[] bei
  Vollständigkeit, Flags bei unsure/kein-Row.
- Voll-Suite (inkl. der ~30 Interview-Tests) grün = Regressions-Nachweis.

## Doku

`WORKFLOW-Footage.md` + `prompts/sort-footage.md` auf **Voll-Durchlauf** aktualisieren
(kein Review-Halt), inkl. Konzept-Einlesen, Klassifikations-Fan-out und der beiden
Auslöser-Sätze. `WORKFLOW.md` (Interview) bleibt inhaltlich unangetastet.

## Bewusst außerhalb

- Kein Code für die Klassifikation selbst (bleibt Claude/Fan-out — semantisch).
- Kein automatischer Konzept-Parser (Claude liest das PDF in-Session).
- Kein Review-Halt (per David-Entscheidung).
