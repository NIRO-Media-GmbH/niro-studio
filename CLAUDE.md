# NIRO Studio

Master-Werkzeug von NIRO Media: drei Funktionen, ein Projektsystem, eine Session.

## Projektstruktur

Alle Projektdaten liegen unter `projects/<Kunde>/<Projekt>/`:

    projects/<Kunde>/<Projekt>/
    ├── audio/            Interview-WAVs
    ├── script/           Konzept-PDF
    ├── cache/ output/ work/   Interview-Pipeline (Transkripte, O-Ton-Pläne)
    ├── footage/          Sortierer-Arbeitsdateien (Pläne, Manifeste, Undo-Logs)
    └── motion/
        ├── inputs/       Video-Inputs für Remotion
        └── renders/      fertige Animationen

Rohes Drehmaterial bleibt auf externen SSDs; hier liegen nur Arbeits- und
Ergebnisdateien. Unterordner nur anlegen, wenn die Funktion genutzt wird.

## Die drei Funktionen (Trigger)

| Trigger im Chat | Funktion | Anleitung |
|---|---|---|
| „Video-Auswahl: <Kunde>/<Projekt>" | Interviews → sortierte O-Ton-Pläne | `tools/transcribe/WORKFLOW.md` |
| „Footage sortieren: <Pfad>" + Konzept | Roh-MP4s nach Konzept-Script sortieren | `tools/transcribe/WORKFLOW-Footage.md` |
| „Animation: <Kunde>/<Projekt>" | Remotion Motion Graphics | `tools/motion/WORKFLOW-Motion.md` |

Beim Trigger die jeweilige Workflow-Datei lesen und ihr folgen.
Projektpfad-Konvention überall: `projects/<Kunde>/<Projekt>/` (relativ zu
dieser Studio-Wurzel).

## Umgebung

- **Python (transcribe):** `tools/transcribe/venv/bin/python`; `.env` mit
  API-Keys liegt in `tools/transcribe/.env`.
- **Remotion (motion):** `cd tools/motion && npm run studio`; Kompositionen
  und `brand.json` pro Kunde in `tools/motion/src/clients/<kunde>/`.
- **Neues Projekt:** Ordner nach Bedarf anlegen, z. B.
  `mkdir -p "projects/<Kunde>/<Projekt>/audio"`.
