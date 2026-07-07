# Workflow — pro Dreh (von Claude in der Session ausgeführt)

Voraussetzung: Setup abgeschlossen (siehe SETUP.md), `.env` gefüllt.

   Ordnerkonvention pro Charge (NIRO-Studio-Wurzel):
   `projects/<Kunde>/<Projekt>/<Charge>/Material/Audio/` (WAVs) und
   `…/<Charge>/Material/Konzept/` (Konzept-PDF mit echtem Namen).
   Ausgabe → `…/<Charge>/Ergebnisse/O-Ton-Pläne/`, Cache → `…/<Charge>/_intern/cache/`.

1. **Projekt öffnen.** Mit den Ordnerpfaden aus der Konvention arbeiten
   (`_intern/cache/` und `Ergebnisse/O-Ton-Pläne/` bei Bedarf anlegen). WAVs
   liegen bereits in `Material/Audio/`; Briefs kommen über den Chat.
2. **Einlesen.** Audiodateien in `Material/Audio/` listen; `guess_meta()` je Datei →
   Interpretationen (Claude prüft/korrigiert sie im Chat, wenn nötig).
   `extract_text(<Material/Konzept>/*.pdf)` → Rahmendaten. Briefs aus dem Chat (bzw.
   `load_briefs`, falls `briefs.yaml` vorliegt).
3. **Transkribieren.** Für jede WAV `transcribe_file()` (Scribe **mit
   Diarisation** + Whisper, gecacht). Scribe liefert `speaker` pro Wort.
4. **Abgleichen.** Pro Datei nach `prompts/reconcile.md` → saubere Fassung
   (Wort-Timestamps und `speaker` bleiben erhalten).
5. **Zerlegen.** Pro Datei nach `prompts/segment.md`: zuerst den **Interviewten**
   (Sprecher-ID) bestimmen, dann Aussagen NUR aus dessen Wörtern; jede mit
   `verify_statement()` prüfen und auf Sprecher-Reinheit von `[von, bis]`
   (kein Fremdsprecher im Bereich). Ergebnis: Aussagen-Pool.
6. **Auswählen & ordnen.** Nach `prompts/select-and-order.md` → `VideoPlan` je
   Video (+ ungenutzte Aussagen). `exklusiv`/`mehrfach` aus `GlobalConfig`.
7. **Kritischer Zweit-Durchgang.** Nach `prompts/critical-review.md` überarbeiten.
8. **Ausgeben.** `render_video_plan()` je Video → `Ergebnisse/O-Ton-Pläne/<video>.md`;
   `render_overview()` → `Ergebnisse/O-Ton-Pläne/uebersicht.md`. Optional PDF-Export.
9. **Zusammenfassen** im Chat: was wurde erzeugt, worauf achten
   (z. B. unsichere Datei-Interpretationen, ungenutzte starke Aussagen).
