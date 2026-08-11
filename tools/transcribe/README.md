# NIRO Transcribe

Teil von **NIRO Studio** (`~/NIRO Studio/`): Master-Einstieg und Projektordner
(`projects/<Kunde>/<Projekt>/`) liegen dort, siehe `../../CLAUDE.md`. Dieses
Tool liefert die Interview-Pipeline und den Footage-Sortierer.

Chat-gesteuertes Werkzeug: aus WAV-Interviews + PDF-Skript + Briefs pro Ziel-Video
entstehen dramaturgisch/marketingpsychologisch sortierte O-Ton-Übersichten mit
von–bis-Timestamps für DaVinci.

- **Setup:** siehe [SETUP.md](SETUP.md)
- **Ablauf pro Dreh:** siehe [WORKFLOW.md](WORKFLOW.md)
- **Design/Spec:** siehe [docs/superpowers/specs/2026-07-01-niro-transcribe-design.md](docs/superpowers/specs/2026-07-01-niro-transcribe-design.md)

Transkription: ElevenLabs Scribe + lokales Whisper (faster-whisper).
Gehirn: Claude Opus 4.8 (in der Session).
