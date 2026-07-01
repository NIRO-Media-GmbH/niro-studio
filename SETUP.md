# Setup (einmalig)

## 1. Python-Umgebung
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 2. ElevenLabs-Key
- Key unter https://elevenlabs.io → Profile → API Keys erstellen.
- `.env.example` nach `.env` kopieren und `ELEVENLABS_API_KEY` eintragen.

## 3. Lokales Whisper (faster-whisper)
- Wird über `pip install` (Schritt 1) mitinstalliert.
- Erstes Ausführen lädt das Modell (`large-v3`) automatisch herunter.
- Bei wenig RAM/Zeit: in `.env` `NIRO_WHISPER_MODEL=medium` setzen.

## 4. Prüfen
```bash
python -m pytest -q
```
Alle Tests müssen grün sein.
