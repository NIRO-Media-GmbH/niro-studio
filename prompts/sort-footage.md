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
