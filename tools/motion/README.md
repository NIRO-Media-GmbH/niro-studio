# NIRO Motion Graphics

Remotion-basierte Motion-Graphics-Produktion von NIRO Media. Teil des
[NIRO Studio](../../CLAUDE.md) — Trigger im Chat:
**„Animation: <Kunde>/<Projekt>[/<Charge>]"** (Ablauf: [WORKFLOW-Motion.md](WORKFLOW-Motion.md)).

## Schnellstart

```bash
npm install
npm run studio        # Remotion Studio öffnen
```

## Struktur

```
src/
├── clients/<kunde>/          ein Ordner pro Kunde (kebab-case)
│   ├── brand.json               CI: Farben, Fonts, Logo-Pfad
│   ├── components/              kundenspezifische Bausteine
│   └── projects/<projekt>/      eine Komposition pro Projekt
├── components/               wiederverwendbare Bausteine (Barrel: index.ts)
├── core/                     Schemas, CI-Loader, Format-Utils
├── templates/                Demo-Vorlagen (nicht produktiv)
└── utils/                    geteilte Hooks/Helper (useExit, subtitles, …)

public/
├── clients/<kunde>/          Brand-Assets (Logo etc.) → staticFile("clients/<kunde>/…")
├── fonts/                    lokale Font-Dateien
└── projects/<kunde>-<projekt>  Symlinks auf Projekt-Videos (gitignored)
```

## Neuer Kunde / neues Projekt

```bash
npm run new:client  -- --name "Kundenname"
npm run new:project -- --client <kunde-slug> --name "projektname"
```

**CI zuerst:** Nach `new:client` sofort `brand.json` vollständig füllen
(Farben, Fonts) und das Logo nach `public/clients/<slug>/` legen — Pflicht
laut Workflow, bevor die erste Komposition entsteht. Neue Kompositionen
kommen mit eingebautem `<ReviewOverlay>` (Face-/Safe-Zone-Guides).

## Rendern

Renders gehen **immer in den Projektordner** des NIRO Studio, nie nach `out/`
(stillgelegt, bleibt leer):

```bash
npx remotion render src/index.ts <CompId> \
  "../../projects/<Kunde>/<Projekt>/<Charge>/Ergebnisse/Renders/<name>.mov" \
  --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444
```

Web-Varianten: `--codec=h264 --crf=18`.

## Pre-Delivery Review

Vor jeder Lieferung gilt die Checkliste in [CLAUDE.md](CLAUDE.md):
Face Zone frei, Safe Zone eingehalten, Guides vor dem Final-Render aus.
