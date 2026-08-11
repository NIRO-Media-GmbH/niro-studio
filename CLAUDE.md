# NIRO Studio

Master-Werkzeug von NIRO Media: fünf Funktionen, ein Projektsystem, eine Session.

## Projektstruktur

Alle Projektdaten liegen unter `projects/<Kunde>/<Projekt>/<Charge>/`.
Chargen-Name: `JJJJ-MM Beschreibung` (z. B. „2026-07 Erster Dreh") — die
Chargen-Ebene existiert immer, auch bei nur einer Charge.

    projects/<Kunde>/<Projekt>/<Charge>/
    ├── Protokoll.md        Kurzprotokoll pro Session
    ├── Material/           was reinkommt
    │   ├── Audio/             Interview-WAVs
    │   ├── Konzept/           Konzept-PDF
    │   └── Video/             Inputs für Animationen
    ├── Ergebnisse/         was fertig ist
    │   ├── O-Ton-Pläne/       Interview-Pipeline
    │   ├── Sortierung/        Zuordnungspläne Footage
    │   ├── Renders/           fertige Animationen
    │   └── Fotos/             entwickelte RAW-Fotos (+ web/)
    └── _intern/            was die Tools brauchen (cache, work, Logs, Manifeste)

Rohes Drehmaterial bleibt auf externen SSDs; hier liegen nur Arbeits- und
Ergebnisdateien. Unterordner nur anlegen, wenn die Funktion genutzt wird.

**Protokoll-Pflicht:** Bei jeder Arbeit an einer Charge (egal welche Funktion)
`Protokoll.md` im Chargen-Ordner fortschreiben — pro Session ein kurzer
Eintrag: Datum, was gemacht, was geliefert (Dateien), Entscheidungen/Offenes.
Datei bei der ersten Session anlegen.

## Die fünf Funktionen (Trigger)

| Trigger im Chat | Funktion | Anleitung |
|---|---|---|
| „Video-Auswahl: <Kunde>/<Projekt>[/<Charge>]" | Interviews → sortierte O-Ton-Pläne | `tools/transcribe/WORKFLOW.md` |
| „Footage sortieren: <Pfad>" + Konzept | Roh-MP4s nach Konzept-Script sortieren | `tools/transcribe/WORKFLOW-Footage.md` |
| „Schnittplan: <Kunde>/<Projekt>[/<Charge>]" | Roh-Footage → Cutter-Schnittanweisungen (PDF, max 2 Seiten/Video) | `tools/transcribe/WORKFLOW-Schnittplan.md` |
| „Animation: <Kunde>/<Projekt>[/<Charge>]" | Remotion Motion Graphics | `tools/motion/WORKFLOW-Motion.md` |
| „Foto: <Kunde>/<Projekt>[/<Charge>]" | ARW-RAWs → Culling, Look, fertige Bilder | `tools/photo/WORKFLOW-Foto.md` |

Beim Trigger die jeweilige Workflow-Datei lesen und ihr folgen.
Projektpfad-Konvention überall: `projects/<Kunde>/<Projekt>/<Charge>/` (relativ
zu dieser Studio-Wurzel). Bei nur einer Charge reicht Kunde/Projekt im Trigger —
die Charge wird dann automatisch gefunden.

## Umgebung

- **Python (transcribe):** `tools/transcribe/venv/bin/python`; `.env` mit
  API-Keys liegt in `tools/transcribe/.env`.
- **Remotion (motion):** `cd tools/motion && npm run studio`; Kompositionen
  und `brand.json` pro Kunde in `tools/motion/src/clients/<kunde>/`.
- **Foto (photo):** RAW-Stufe `dcraw_emu` (libraw, Homebrew) + ImageMagick;
  Kunden-Looks als HALD-LUT in `tools/photo/looks/<kunde>/`; RawTherapee liegt
  quarantäne-blockiert in `/Applications` (GUI einmal öffnen würde ihn freischalten).
- **Neues Projekt:** Ordner nach Bedarf anlegen, z. B.
  `mkdir -p "projects/<Kunde>/<Projekt>/<Charge>/Material/Audio"`.
