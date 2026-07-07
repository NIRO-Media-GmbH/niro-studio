# Workflow — Animation (Motion Graphics, Claude in der Session)

Auslöser: **„Animation: <Kunde>/<Projekt>[/<Charge>]"** (+ Beschreibung, was
animiert werden soll; bei nur einer Charge reicht Kunde/Projekt).

Voraussetzung: `npm install` gelaufen (node_modules vorhanden).

Konventionen:
- Kompositionen + `brand.json` pro Kunde: `src/clients/<kunde>/`
  (kebab-case). Neuer Kunde: `npm run new:client`; neues Projekt:
  `npm run new:project`.
- **CI zuerst:** Existiert `src/clients/<kunde>/brand.json` noch nicht, vor
  allem anderen den Kunden anlegen und die CI vollständig einpflegen —
  Markenfarben, Fonts, Logo. Quellen: vom Nutzer erfragen bzw. von der
  Kunden-Website/Logo-Dateien ableiten (Werte im Chat kurz bestätigen lassen).
  Logo-Assets nach `public/clients/<kunde>/`.
- **Inputs** liegen beim Projekt: `../../projects/<Kunde>/<Projekt>/<Charge>/Material/Video/`.
  Für Remotion per Symlink erreichbar machen:
  `ln -s "../../../../projects/<Kunde>/<Projekt>/<Charge>/Material/Video" "public/projects/<kunde>-<projekt>"`
  → im Code: `staticFile("projects/<kunde>-<projekt>/<datei>")`.
- **Renders** gehen direkt ins Projekt (nicht nach `out/`):
  `npx remotion render src/index.ts <CompId> "../../projects/<Kunde>/<Projekt>/<Charge>/Ergebnisse/Renders/<name>.mov" --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444`
  (Web-Varianten: `--codec=h264 --crf=18`.)
- `out/` ist stillgelegt und bleibt leer; es gibt keine projektspezifischen
  package.json-Render-Scripts mehr. Alle Renders laufen als direkte
  render-Kommandos mit Projektpfad (auch bei Bestandskunden).

Ablauf:
1. Projektordner prüfen/anlegen (`<Charge>/Material/Video/`, `<Charge>/Ergebnisse/Renders/`),
   Symlink setzen falls Inputs genutzt werden.
2. Komposition bauen/ändern in `src/clients/<kunde>/projects/<projekt>/`.
3. **Pre-Delivery Review nach CLAUDE.md** (Face Zone, Safe Zone, Guides aus
   vor Final-Render) — Pflicht.
4. Rendern in `projects/<Kunde>/<Projekt>/<Charge>/Ergebnisse/Renders/`.
5. Im Chat bilanzieren: was gerendert wurde, wohin, Auffälligkeiten.
6. `Protokoll.md` im Chargen-Ordner fortschreiben (bei erster Session anlegen):
   Datum, was animiert, gelieferte Renders, CI-/Design-Entscheidungen, Offenes.
