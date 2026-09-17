# Einrichtung NIRO Studio

Einmalig pro Rechner. Danach steht das komplette Werkzeug — die fünf Funktionen
aus [CLAUDE.md](CLAUDE.md) laufen dann per Trigger im Chat.

Getestet auf macOS (Apple Silicon). Erwartet wird [Homebrew](https://brew.sh).

## 1. Repo klonen

```bash
cd ~
git clone https://github.com/<org>/niro-studio.git "NIRO Studio"
cd "NIRO Studio"
```

Der Ordnername `NIRO Studio` ist Konvention, kein Zwang — alle Pfade im Repo
sind relativ.

## 2. Größensperre aktivieren

```bash
git config core.hooksPath .githooks
```

Blockt Commits mit Dateien über 5 MB. Hier gehört das Werkzeug hinein, nicht
das Kundenmaterial — der Hook fängt Versehen ab, bevor sie in der Historie
landen. Details in [.githooks/pre-commit](.githooks/pre-commit).

Dieselbe Einstellung aktiviert den **Studio-Abgleich mit dem NAS**: Nach jedem `git pull` holt
`tools/studio_abgleich.sh` Chargen-Daten, Claude-Gedächtnis und NIRO-Grading-LUTs vom NAS, legt eigene Stände dort ab
und zieht geänderte Abhängigkeiten nach (Spec: `docs/superpowers/specs/2026-09-17-studio-nas-abgleich-design.md`).

**Einmalig je Mac, der noch `projects/` aus GitHub hat** (statt des ersten Pulls, NAS verbunden):

```bash
git fetch && git show origin/main:tools/studio_abgleich.sh | sh -s -- --umstieg
```

Meldet der LUT-Abgleich fehlendes Schreibrecht, einmalig
`sudo chmod a+w "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"`.

**Mac-Name für die Tagesberichte** (einmal je Mac; Studio-Rechner „Studio-Mac", Zweit-MacBook „MacBook"):

```bash
git config niro.mac "MacBook"
```

Beim Start jeder Claude-Session schreibt der Hook aus `.claude/settings.json` den Tagesstand dieses Macs nach
`berichte/<Datum>/<Mac>.md` (`tools/tagesbericht/sammler.py`) und spiegelt `berichte/` aufs NAS; die Funktion
„Tagesbericht" fasst beide Macs zusammen (`tools/tagesbericht/README.md`). Ohne `niro.mac` heißt die Datei nach dem
Computernamen.

## 3. Systemwerkzeuge

```bash
brew install ffmpeg imagemagick libraw exiftool node python@3.13
```

| Paket | wofür |
|---|---|
| `ffmpeg` | Audio aus Footage ziehen (Transkription, Sortierer, Schnittplan) |
| `imagemagick` | Foto-Pipeline: Look, Clarity, Vignette, Kontaktbögen |
| `libraw` | Foto-Pipeline: `dcraw_emu` entwickelt die ARW-RAWs |
| `exiftool` | Foto-Pipeline: Previews fürs Culling, EXIF beim Export |
| `node` | Remotion (Motion Graphics) |
| `python@3.13` | Transkriptions-Pipeline (mindestens 3.11) |

## 4. Transcribe (Interviews, Footage, Schnittpläne)

```bash
cd tools/transcribe
python3 -m venv venv
./venv/bin/pip install -e ".[dev]"
cp .env.example .env          # ELEVENLABS_API_KEY eintragen
./venv/bin/python -m pytest -q
```

Den ElevenLabs-Key gibt es unter elevenlabs.io → Profile → API Keys. Jeder
arbeitet mit dem **eigenen** Key; `.env` ist ignoriert und wandert nie ins Repo.

Beim ersten Lauf lädt sich das Whisper-Modell `large-v3` selbst herunter
(mehrere GB). Bei wenig RAM in `.env` auf `NIRO_WHISPER_MODEL=medium` stellen.
Mehr Details: [tools/transcribe/SETUP.md](tools/transcribe/SETUP.md).

## 5. Motion (Remotion)

```bash
cd tools/motion
npm install
npm run studio
```

Marken-Definitionen, Fonts und Logos aller Kunden sind im Repo — die
Kompositionen laufen sofort. Was fehlt, ist das Rohmaterial: Kompositionen mit
Video-Unterlage brauchen einen Symlink nach `projects/`, siehe
[tools/motion/WORKFLOW-Motion.md](tools/motion/WORKFLOW-Motion.md).

## 6. Foto

Außer den Systemwerkzeugen aus Schritt 3 nichts zu tun. Die Kunden-Looks
(HALD-LUTs) sind bewusst **nicht** im Repo — sie sind je ~10 MB groß und aus
dem Rezept reproduzierbar:

```bash
cd tools/photo
./scripts/make_look_lut.sh looks/bumbleclean/ultraclean_v5.png
```

Die Parameter des aktiven Looks stehen im Kopf von `make_look_lut.sh`, die
Entwicklungsgeschichte in der jeweiligen `NOTES.md`.

## 7. Projektordner

`projects/` ist nicht Teil des Repos und existiert nach dem Klonen nicht.
Beim ersten Auftrag nach Bedarf anlegen:

```bash
mkdir -p "projects/<Kunde>/<Projekt>/<Charge>/Material/Audio"
```

Struktur und Chargen-Konvention stehen in [CLAUDE.md](CLAUDE.md). Rohes
Drehmaterial bleibt auf NAS/SSD.

## Arbeiten mit dem Repo

**Updates holen:** `git pull` — regelmäßig, damit Workflows und Kompositionen
aktuell sind.

**Schreibrechte** hat aktuell nur David. Wenn dir etwas am Werkzeug fehlt oder
fehlerhaft ist: melden statt selbst pushen.

**Was nie ins Repo gehört:** Kundenmaterial, Renders, Fotos, Schnittpläne,
Protokolle, API-Keys. Alles davon liegt entweder unter `projects/` (ignoriert)
oder auf NAS/SSD. Im Zweifel vor dem Commit `git status` lesen.
