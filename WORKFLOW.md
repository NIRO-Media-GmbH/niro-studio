# Workflow — pro Dreh (von Claude in der Session ausgeführt)

Voraussetzung: Setup abgeschlossen (siehe SETUP.md), `.env` gefüllt.

1. **Projekt anlegen.** `Project.open(<projektordner>)` erstellt `audio/`,
   `cache/`, `output/`. Der Nutzer legt die WAVs per Finder in `audio/` und sagt
   im Chat Bescheid; `skript.pdf` und Briefs kommen über den Chat (Claude
   speichert PDF nach `skript.pdf` und schreibt `briefs.yaml`).
2. **Einlesen.** `audio_files()` listen; `guess_meta()` je Datei →
   Interpretationen (Claude prüft/korrigiert sie im Chat, wenn nötig).
   `extract_text(skript.pdf)` → Rahmendaten. `load_briefs(briefs.yaml)`.
3. **Transkribieren.** Für jede WAV `transcribe_file()` (Scribe + Whisper,
   gecacht).
4. **Abgleichen.** Pro Datei nach `prompts/reconcile.md` → saubere Fassung.
5. **Zerlegen.** Pro Datei nach `prompts/segment.md` → Aussagen; jede mit
   `verify_statement()` prüfen; Probleme beheben. Ergebnis: Aussagen-Pool.
6. **Auswählen & ordnen.** Nach `prompts/select-and-order.md` → `VideoPlan` je
   Video (+ ungenutzte Aussagen). `exklusiv`/`mehrfach` aus `GlobalConfig`.
7. **Kritischer Zweit-Durchgang.** Nach `prompts/critical-review.md` überarbeiten.
8. **Ausgeben.** `render_video_plan()` je Video → `output/<video>.md`;
   `render_overview()` → `output/uebersicht.md`. Optional PDF-Export.
9. **Zusammenfassen** im Chat: was wurde erzeugt, worauf achten
   (z. B. unsichere Datei-Interpretationen, ungenutzte starke Aussagen).
