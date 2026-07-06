# Prompt — Footage sortieren (in der Session, Claude = Brain)

Ziel: Roh-MP4s anhand des Konzept-Scripts sortieren. Zuordnung über den
transkribierten **Ton**, nicht über Dateinamen. Kein Footage geht verloren.

## Eingaben
- `footage_root` (SSD): enthält Kamera-Ordner mit MP4/MOV (+ XML-Sidecars).
- Konzept-Script (PDF/Sheet): Spalten u. a. Video-Nr, Videotitel, Szenen-Nr,
  `Sprechtext/Inhalt`. Script in strukturierte Szenen parsen:
  je Video eine geordnete Liste (Hook A/B/C, Szene 1..N) mit Soll-Sprechtext.

## Ablauf
1. `discover_clips(footage_root)` → alle Clips (mit Kamera + Sidecar).
2. Pro Clip `transcribe_clip(...)` (Scribe, Diarisation, gecacht). Ergebnis:
   Wörter mit `speaker`-Label und Zeiten.
3. **Sprecher bestimmen:** der Kameramann/Interviewer spricht auch — er zählt
   NIE. Interviewten-Sprecher pro Clip identifizieren (größter Redeanteil bzw.
   der, der die Konzept-/Antwortinhalte spricht). Nur dessen Wörter nutzen.
4. **Klassifizieren** (pro Clip):
   - **Gescripteter Satz:** Ton matcht ~wörtlich eine `Sprechtext`-Zeile, die
     als echter Sprech-Satz gedreht wurde → Ziel
     `sortiert/<Videotitel>/NN_<Szene>_<Kurztext>/<Kamera>/<Originaldatei>`.
     NN = Script-Reihenfolge (Hook A/B/C zuerst, dann Szene 1..N). Multi-Cam:
     mehrere Kameras desselben Satzes → alle in denselben Szenen-Ordner,
     nach `<Kamera>/` getrennt. Takes (Wiederholungen) → derselbe Ordner.
     Enthält ein Clip ausnahmsweise MEHRERE Sätze: Primärsatz-Regel — Clip in
     den Ordner des ersten Satzes; die weiteren Sätze mit von–bis im Plan
     vermerken. Keine Datei duplizieren.
   - **Freies Interview:** Script-Zeile ist „Frage an … Sie erzählt, dass …"
     (Antwort frei) → NICHT einer Szene zuordnen, sondern nach Person:
     `sortiert/Interviews/<Name>/<Originaldatei>`. Name aus dem Transkript
     (Selbstvorstellung / im Clip genannter Name). Kein Name → `Interviews/_ohne_Namen/`
     und im Plan markieren.
   - **B-Roll / kein O-Ton:** kein verwertbarer Interviewten-Sprech, nur
     Ambiente/Kameramann, oder „Hook C – bildlicher Einstieg ohne Text" →
     `sortiert/B-Roll/<Originaldatei>`.
   - **Unsicher:** nicht sicher zuordenbar → `sortiert/_nicht_zugeordnet/<Originaldatei>`.
5. **Zuordnungsplan** schreiben (`zuordnungsplan.md`, menschenlesbar): pro
   Video/Szene die Clips (Kamera, Take, von–bis, Match-Sicherheit), dann
   Interviews-nach-Person, B-Roll, `_nicht_zugeordnet`. Ganz oben die
   **Bilanz**: Anzahl gefundener Clips == Summe aller Ziele.
6. **Manifest** schreiben (`manifest.json`, `MovePlan`): je Clip genau ein
   `{src, dst}`. `MovePlan.validate(discovered_srcs)` MUSS `[]` liefern, bevor
   irgendetwas bewegt wird.
7. **Review-Gate:** David prüft `zuordnungsplan.md` im Chat. NICHTS wurde bewegt.
8. **Erst nach „go":** `execute_plan(plan, log_path, discovered_srcs=[...])` (same-fs → atomarer
   rename). `execute_plan` verweigert das Verschieben, solange `validate()` nicht leer ist —
   `discovered_srcs` muss die vollständige Liste aller gefundenen Clips enthalten. Danach Bilanz
   aus dem Log bestätigen. Bei Bedarf `undo(log_path)`.

## Regeln
- Original-Dateinamen NIE ändern. Struktur entsteht nur über Ordner.
- Im Zweifel `_nicht_zugeordnet/` statt raten. Lieber melden als verlieren.
- Nur ElevenLabs Scribe, kein Whisper.
