# Workflow — Footage sortieren (Voll-Durchlauf, Claude in der Session)

Auslöser: **„Footage sortieren: <Pfad>"** + Konzept-Dokument anhängen.
(Die andere Funktion — „Video-Auswahl / Videopläne" — ist die Interview-Pipeline
in `WORKFLOW.md` und bleibt davon unberührt.)

Voraussetzung: `.env` (ELEVENLABS_API_KEY) geladen, ffmpeg im PATH, SSD gemountet.

Konvention: Rohmaterial `<Projekt-SSD>/01_Footage/<Kamera>/…`; Ausgabe →
`<Projekt-SSD>/sortiert/`. Arbeitsdateien (cache, index, manifest, log) in der
NIRO-Studio-Wurzel unter `projects/<Kunde>/<Projekt>/<Charge>/_intern/`; der
fertige Zuordnungsplan → `…/<Charge>/Ergebnisse/Sortierung/zuordnungsplan.md`.

Ablauf (läuft ohne Halt durch; Sicherheit über Undo-Log):
1. **Konzept lesen.** Das angehängte PDF/Sheet in der Session lesen und in die
   Struktur `script_structured.json` bringen: `{"videos":[{"nr","titel",
   "rows":[{"id","typ","text"}]}]}`, typ ∈ scripted|interview|visual.
2. **Transkribieren.** `transcribe_all(footage_root, project_dir)` — Scribe +
   Diarisation, gecacht; schreibt `_intern/transcripts_index.json`.
3. **Klassifizieren.** Per Fan-out-Agenten (nach `prompts/sort-footage.md`) jeden
   Clip gegen die Struktur → `classifications` (category scripted|interview|broll|
   unsure, + video_nr/row_id/person). Kameramann via Diarisation ignorieren.
4. **Plan bauen.** `clips = discover_clips(footage_root)` — liefert die Clip-Liste
   für `build_move_plan` und `execute_plan`.
   `build_move_plan(clips, classifications, script, sort_root,
   aliases=...)` → `PlanResult` (Manifest + `zuordnungsplan.md`-Text, ablegen
   unter `Ergebnisse/Sortierung/`). `validate()` muss leer sein, sonst STOPP
   und melden.
5. **Verschieben.** `execute_plan(plan, log, discovered_srcs=[str(c.path) for c in clips])`
   → verschiebt sofort, schreibt `_verschiebe_log.jsonl` (Undo).
6. **Bilanz melden.** Quelle==Ziel bestätigen; Undo-Hinweis: `undo(log)`.
7. **Protokoll.** `Protokoll.md` im Chargen-Ordner fortschreiben (bei erster
   Session anlegen): Datum, sortierte Clips (Bilanz), Sonderfälle/Offenes.

Rückgängig: `from niro_transcribe.footage.mover import undo; undo(log_path)`.
