# SETUP: NIRO AutoCut einrichten

Einmalig pro Rechner. Alles liegt unter `tools/autocut/`; nichts wird systemweit installiert.

## 1. Python-Umgebung

Python 3.12 (python.org-Framework, `/usr/local/bin/python3.12`):

    cd "/Users/jansantos/NIRO Studio/tools/autocut"
    /usr/local/bin/python3.12 -m venv venv
    venv/bin/python -m pip install --upgrade pip
    venv/bin/python -m pip install numpy scipy pillow anthropic requests rapidfuzz pytest python-dotenv pyyaml

`anthropic` muss ≥ 1.3 sein (Structured Outputs über `output_config`). Stand 03.09.2026: anthropic 1.3.0,
numpy 2.5, scipy 1.18, Pillow 12.3, RapidFuzz 3.14, pytest 9.1.

## 2. Zugriff auf `niro_transcribe` (nur Import, keine Installation)

AutoCut nutzt den Clip-Fingerprint der Interview-Pipeline. Der Quellordner wird per `.pth` sichtbar
gemacht — **nicht** per `pip install`, damit `tools/transcribe` unverändert bleibt:

    echo "/Users/jansantos/NIRO Studio/tools/transcribe/src" > venv/lib/python3.12/site-packages/niro_transcribe.pth
    venv/bin/python -c "from niro_transcribe.footage.transcribe_clips import clip_fingerprint; print('ok')"

## 3. API-Schlüssel (`.env`, nur für Stufe 2 B-Roll-Index)

    venv/bin/python scripts/setup_env.py

liest den Anthropic-Key aus dem macOS-Schlüsselbund (Dienst `niro_autocut`, Konto `anthropic`) und schreibt
`tools/autocut/.env` (Rechte 600). Fehlt der Eintrag, den Key von Hand eintragen:

    ANTHROPIC_API_KEY=sk-ant-...

`.env` ist über `.gitignore` von der Versionierung ausgeschlossen. Standardmodell für die Vision-Indexierung:
`index.model` in `defaults.yaml` (`claude-opus-5`, `effort: medium`).

## 4. ffmpeg / ffprobe

Homebrew-ffmpeg 8 (`/opt/homebrew/bin/ffmpeg`, `ffprobe`) muss im PATH liegen:

    brew install ffmpeg
    ffmpeg -version | head -1

Genutzt für ffprobe (Format, Rotation, Frames), Audio-Extraktion (16-kHz-Mono-WAV der Originale, nur lesend
vom NAS), Szenenwechsel (`select='gt(scene,T)'`) und Einzelbilder aus den Proxies. Der `drawtext`-Filter
fehlt in dieser Installation — Zeitstempel werden mit Pillow eingebrannt.

## 5. DaVinci Resolve Studio (für build, probe, place, export, read)

- Resolve Studio 21.1 (verifiziert: 21.1.0.14) installiert unter `/Applications/DaVinci Resolve/`.
- Externes Scripting freischalten: DaVinci Resolve → Preferences → System → General →
  „External scripting using" = **Local**. Resolve muss laufen und das Zielprojekt geöffnet sein.
- Die Scripting-Pfade setzt `resolve_api.connect()` selbst:
  `RESOLVE_SCRIPT_API=/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting`,
  `RESOLVE_SCRIPT_LIB=/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so`,
  Modul `…/Scripting/Modules/DaVinciResolveScript.py`. Keine Wrapper-Bibliothek (pydavinci ist verwaist).
- Doku der API seit 21.1 im selben Ordner: `README.md`, `CHANGELOG.md` und die Stubs `DaVinciResolveScript.pyi`
  (`README.txt`/`CHANGELOG.txt` gibt es nicht mehr). Resolve bringt ein eigenes Python 3.14 mit
  (`…/DaVinci Resolve.app/Contents/Applications/ResolvePython`, ohne pip) — AutoCut bleibt bei der venv mit
  Python 3.12 und den Umgebungsvariablen oben.
- Erreichbarkeit prüfen: `venv/bin/python scripts/autocut_prepare.py "<Charge>" --check-resolve`.
- Vor dem ersten Bau in einer neuen Resolve-Umgebung einmal `scripts/resolve_probe.py "<Charge>"`
  laufen lassen: legt eine Probe-Timeline an, misst die `endFrame`-Semantik und die Record-Positionen,
  löscht nur diese Probe wieder und schreibt `<Charge>/_intern/autocut/probe.json`.
- Einmal je Resolve-Umgebung zusätzlich `scripts/resolve_probe_api.py "<Charge>" --project "<offenes Projekt>"`:
  misst das Verhalten der 21.1-Funktionen (AudioVolume, Normalize, SetSpeed, Fades, Transition, AutoAlign,
  QuickExport, Alpha-Import) mit synthetischem Material — `--project` muss exakt dem geöffneten Projekt entsprechen
  (Freigabe des Users), sonst passiert nichts. Ergebnis `<Charge>/_intern/autocut/probe_api.json`.
- Proxies: Resolve-Proxies der Clips liegen als `<Clip-Ordner>/Proxy/<stem>.mov` (1920×1080) neben den
  Originalen auf dem NAS; AutoCut verknüpft sie per `LinkProxyMedia` und liest sie für Frames/Kontaktbögen.

## 6. NAS

Die Clip-Pfade stammen aus `<Charge>/_intern/transcripts_index.json` (`/Volumes/NIRO NAS/...`). Das NAS
muss beim Lauf gemountet sein; AutoCut liest dort nur (Original-Audio, Proxies) und schreibt nie.

## 7. Prüfen

    cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q

Alle Tests laufen ohne Resolve, NAS und API-Key. Danach ein lesender Live-Check auf einer echten Charge:

    venv/bin/python -c "from niro_autocut.media import ffprobe, proxy_for; import sys; i=ffprobe(sys.argv[1]); print(i, proxy_for(sys.argv[1]))" "<FX3-Pfad aus transcripts_index.json>"

## Werte anpassen

`defaults.yaml` enthält alle Standardwerte (Pause 1,0 s, Handles 6/8 Frames, Alignment-Schwelle 0,80,
Sync-Konfidenz 4,0, Index-Modell/Kacheln, B-Roll-Regeln, Resolve-Bin/Timeline-Namen). Pro Charge
überschreibbar in `<Charge>/_intern/autocut/config.yaml` (rekursiv gemergt: nur die dort genannten Schlüssel
ersetzen die Standardwerte, verschachtelte Blöcke bleiben sonst erhalten) — die Datei
selbst nicht ändern, solange andere Chargen sie nutzen.
