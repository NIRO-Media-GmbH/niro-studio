# NIRO Studio — Master-Tool-Design

Datum: 2026-07-07 · Status: vom User freigegeben

## Ziel

Drei bestehende Funktionen unter einem Dach vereinen, mit projektbasiertem
Arbeiten (alle Daten eines Projekts in einem Ordner) und einer Session für
alle Abfragen:

1. **Interview-Pipeline** (NIRO Transcribe, `WORKFLOW.md`)
2. **Footage-Sortierer** (NIRO Transcribe, `WORKFLOW-Footage.md`)
3. **Motion Graphics** (NIROmotiongraphics, Remotion)

Alles muss danach genauso gut funktionieren wie bisher.

## Entscheidungen (mit User abgestimmt)

| Frage | Entscheidung |
|---|---|
| Projektbegriff | Zweistufig: `projects/<Kunde>/<Projekt>/` — Branding beim Kunden, Daten beim Projekt |
| Physische Struktur | Master-Ordner **„NIRO Studio"** mit 2 eigenständigen Sub-Repos unter `tools/` |
| Motion-Daten | Nur **Medien** (Inputs + Renders) wandern in Projektordner; TSX-Code bleibt in `tools/motion/src/clients/` |
| Name | **NIRO Studio** |
| Migration | Nur **aktive** Projekte umziehen; Abgeschlossenes bleibt liegen |

## Zielstruktur

```
/Users/jansantos/NIRO Studio/
├── CLAUDE.md                  # Master-Einstieg: routet auf alle 3 Workflows
├── docs/                      # Specs, Pläne
├── .gitignore                 # tools/ und projects/ ignoriert (leichtes Repo)
├── projects/
│   └── <Kunde>/<Projekt>/
│       ├── audio/  script/  cache/  output/  work/   # Interview-Pipeline
│       ├── footage/                                   # Sortierer-Arbeitsdateien
│       └── motion/inputs/  motion/renders/            # Motion Graphics
└── tools/
    ├── transcribe/            # ehem. „NIRO Transcribe" (git zieht mit um)
    └── motion/                # ehem. „NIROmotiongraphics" (bekommt git)
```

- Master-Ordner ist ein leichtes git-Repo (nur CLAUDE.md + docs).
- Rohmaterial (Footage) bleibt weiterhin auf externen SSDs; im Projektordner
  liegen nur Pläne/Manifeste/Logs.

## Master-CLAUDE.md — Trigger

| Trigger | Funktion | Workflow-Datei |
|---|---|---|
| „Video-Auswahl: <Kunde>/<Projekt>" | Interview → O-Ton-Pläne | `tools/transcribe/WORKFLOW.md` |
| „Footage sortieren: <Pfad>" | Roh-MP4s sortieren | `tools/transcribe/WORKFLOW-Footage.md` |
| „Animation: <Kunde>/<Projekt>" | Remotion Motion Graphics | `tools/motion/WORKFLOW-Motion.md` |

Workflows bleiben inhaltlich unverändert; nur die Pfad-Konvention wird
`projects/<Kunde>/<Projekt>/` (relativ zur NIRO-Studio-Wurzel). Der Python-Code
braucht keine Änderung (`Project.open()` nimmt beliebige Pfade).

## Remotion-Anbindung (Medien beim Projekt)

- **Inputs:** Symlink `tools/motion/public/projects/<kunde>-<projekt>` →
  `projects/<Kunde>/<Projekt>/motion/inputs/`. Remotion lädt via
  `staticFile("projects/<kunde>-<projekt>/…")`.
- **Renders:** Render-Scripts schreiben nach
  `../../projects/<Kunde>/<Projekt>/motion/renders/` statt `out/`.
- `brand.json` und TSX-Kompositionen bleiben in `tools/motion/src/clients/`.

## Migration

1. `NIRO Studio/` anlegen (CLAUDE.md, docs/, projects/, tools/), git init.
2. `NIROmotiongraphics` → `tools/motion`; dort `git init` + Erst-Commit
   (.gitignore: node_modules, out, Videos, Video inputs, public-Medien).
3. Aktive Projekte: `LohiBW Recruiting` → `projects/LohiBW/Recruiting/`,
   `REM 1x Website-Dienstleistungsfilm` → `projects/REM/Website-Dienstleistungsfilm/`.
   `WTN 5x Ads` bleibt (abgeschlossen).
4. Docs anpassen (Pfad-Konventionen in WORKFLOW*.md, SETUP.md, README),
   Master-CLAUDE.md + WORKFLOW-Motion.md schreiben.
5. **Zuletzt:** `NIRO Transcribe` → `tools/transcribe` verschieben (Session
   läuft im alten Pfad), venv neu erstellen (`python3 -m venv venv` +
   `pip install -e .`), pytest als Smoke-Test; Remotion Studio einmal starten.
6. Claude-Memory auf neuen Projektpfad übertragen
   (`~/.claude/projects/-Users-jansantos-NIRO-Studio/memory/`).

## Risiken / Verifikation

- venv enthält absolute Pfade → wird neu erstellt, danach `pytest`.
- Symlinks in Remotion `public/` → Smoke-Test: Studio starten, Assets sichtbar.
- git-Repo übersteht Ordner-Umzug verlustfrei (Standardverhalten).
- Undo-Logs/Manifeste des Footage-Sortierers enthalten absolute Pfade —
  migrierte Projekte behalten ihre Logs; alte Pfade gelten nur für bereits
  ausgeführte Läufe (kein Re-Run nötig).
