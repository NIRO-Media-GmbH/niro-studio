# NIRO Studio

Master-Werkzeug von NIRO Media: drei Funktionen, ein Projektsystem, eine Session.

## Projektstruktur

Alle Projektdaten liegen unter `projects/<Kunde>/<Projekt>/<Charge>/`.
Chargen-Name: `JJJJ-MM Beschreibung` (z. B. „2026-07 Erster Dreh") — die
Chargen-Ebene existiert immer, auch bei nur einer Charge.

    projects/<Kunde>/<Projekt>/<Charge>/
    ├── Material/           was reinkommt
    │   ├── Audio/             Interview-WAVs
    │   ├── Konzept/           Konzept-PDF
    │   └── Video/             Inputs für Animationen
    ├── Ergebnisse/         was fertig ist
    │   ├── O-Ton-Pläne/       Interview-Pipeline
    │   ├── Sortierung/        Zuordnungspläne Footage
    │   └── Renders/           fertige Animationen
    └── _intern/            was die Tools brauchen (cache, work, Logs, Manifeste)

Rohes Drehmaterial bleibt auf externen SSDs; hier liegen nur Arbeits- und
Ergebnisdateien. Unterordner nur anlegen, wenn die Funktion genutzt wird.

## Die drei Funktionen (Trigger)

| Trigger im Chat | Funktion | Anleitung |
|---|---|---|
| „Video-Auswahl: <Kunde>/<Projekt>[/<Charge>]" | Interviews → sortierte O-Ton-Pläne | `tools/transcribe/WORKFLOW.md` |
| „Footage sortieren: <Pfad>" + Konzept | Roh-MP4s nach Konzept-Script sortieren | `tools/transcribe/WORKFLOW-Footage.md` |
| „Animation: <Kunde>/<Projekt>[/<Charge>]" | Remotion Motion Graphics | `tools/motion/WORKFLOW-Motion.md` |

Beim Trigger die jeweilige Workflow-Datei lesen und ihr folgen.
Projektpfad-Konvention überall: `projects/<Kunde>/<Projekt>/<Charge>/` (relativ
zu dieser Studio-Wurzel). Bei nur einer Charge reicht Kunde/Projekt im Trigger —
die Charge wird dann automatisch gefunden.

## Umgebung

- **Python (transcribe):** `tools/transcribe/venv/bin/python`; `.env` mit
  API-Keys liegt in `tools/transcribe/.env`.
- **Remotion (motion):** `cd tools/motion && npm run studio`; Kompositionen
  und `brand.json` pro Kunde in `tools/motion/src/clients/<kunde>/`.
- **Neues Projekt:** Ordner nach Bedarf anlegen, z. B.
  `mkdir -p "projects/<Kunde>/<Projekt>/<Charge>/Material/Audio"`.
