# Workflow — Footage sortieren (pro Dreh, Claude in der Session)

Voraussetzung: `.env` (ELEVENLABS_API_KEY) geladen, ffmpeg im PATH, SSD gemountet.

Konvention: Rohmaterial auf der SSD unter `<Projekt>/01_Footage/<Kamera>/…`;
Ausgabe → `<Projekt>/sortiert/`. Arbeitsdateien (Cache, Plan, Manifest, Log,
Script-Kopie) im Repo unter `projects/<Name>/`.

1. **Finden.** `discover_clips(footage_root)` → Clip-Liste (Kamera + Sidecar).
2. **Transkribieren.** Pro Clip `transcribe_clip(...)` (Scribe + Diarisation,
   gecacht in `projects/<Name>/cache/`). Audio wird per ffmpeg extrahiert.
3. **Script lesen & zuordnen.** Nach `prompts/sort-footage.md`: Sprecher
   bestimmen (Kameramann raus), klassifizieren (gescriptet → Szene, frei →
   Person, Rest → B-Roll, unsicher → `_nicht_zugeordnet`).
4. **Plan + Manifest.** `zuordnungsplan.md` (Review) und `manifest.json`
   (`MovePlan`). `validate()` muss leer sein.
5. **Review.** David prüft `zuordnungsplan.md`. Bis hier nichts bewegt.
6. **Verschieben (nach „go").** `execute_plan(plan, log, discovered_srcs=[...])` → `_verschiebe_log.md`
   (JSONL). `execute_plan` prüft vor dem ersten Move selbständig die Vollständigkeit des Manifests
   (`validate()`); sind Probleme vorhanden, wird NICHTS verschoben. Bei einem Fehler mittendrin
   bricht die Funktion ab — bereits erfolgte Moves stehen im Log und können mit `undo(log)`
   rückgängig gemacht werden. Bilanz prüfen. Rückgängig via `undo(log)`.
