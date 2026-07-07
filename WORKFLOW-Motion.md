# Workflow — Animation (Motion Graphics, Claude in der Session)

Auslöser: **„Animation: <Kunde>/<Projekt>"** (+ Beschreibung, was animiert
werden soll).

Voraussetzung: `npm install` gelaufen (node_modules vorhanden).

Konventionen:
- Kompositionen + `brand.json` pro Kunde: `src/clients/<kunde>/`
  (kebab-case). Neuer Kunde: `npm run new:client`; neues Projekt:
  `npm run new:project`.
- **Inputs** liegen beim Projekt: `../../projects/<Kunde>/<Projekt>/motion/inputs/`.
  Für Remotion per Symlink erreichbar machen:
  `ln -s "../../../../projects/<Kunde>/<Projekt>/motion/inputs" "public/projects/<kunde>-<projekt>"`
  → im Code: `staticFile("projects/<kunde>-<projekt>/<datei>")`.
- **Renders** gehen direkt ins Projekt (nicht nach `out/`):
  `npx remotion render src/index.ts <CompId> "../../projects/<Kunde>/<Projekt>/motion/renders/<name>.mov" --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444`
  (Web-Varianten: `--codec=h264 --crf=18`.)
- Alte `render:*`-Scripts in package.json gelten für Bestandsprojekte
  (Ausgabe nach `out/`); neue Projekte bekommen KEINE neuen package.json-
  Scripts mehr, sondern direkte render-Kommandos mit Projektpfad.

Ablauf:
1. Projektordner prüfen/anlegen (`motion/inputs/`, `motion/renders/`),
   Symlink setzen falls Inputs genutzt werden.
2. Komposition bauen/ändern in `src/clients/<kunde>/projects/<projekt>/`.
3. **Pre-Delivery Review nach CLAUDE.md** (Face Zone, Safe Zone, Guides aus
   vor Final-Render) — Pflicht.
4. Rendern in `projects/<Kunde>/<Projekt>/motion/renders/`.
5. Im Chat bilanzieren: was gerendert wurde, wohin, Auffälligkeiten.
