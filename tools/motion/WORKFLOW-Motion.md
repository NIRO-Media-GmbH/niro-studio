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
- **Render-Performance/Disk (seit 2026-08-03):** Remotion kopiert bei JEDEM
  Render/Still den kompletten `public/`-Ordner ins Temp-Bundle — dort liegen
  GB-schwere Client-Videos (z. B. `clients/man/wz/`). Deshalb mit
  `--public-dir=public-hbl`-Muster arbeiten: schlanker Spiegel via
  `rsync -a --exclude='*.mov' --exclude='*.mp4' --exclude='*.wav' public/ public-<kunde>/`
  (Achtung: manche Clients laden Fonts aus `clients/<kunde>/fonts/` — deshalb
  ganzen public spiegeln, nicht nur den eigenen Client). Abgebrochene Renders
  hinterlassen 6–7-GB-Bundles: `rm -rf "$TMPDIR"remotion-webpack-bundle-*`.
- **Alpha-Falle:** CSS `border` + `overflow:hidden` + `borderRadius` erzeugt
  im ProRes-Alpha eine Haarlinie an der Border-Innenkante (Subpixel-Lücke).
  Rahmen mit „Loch" stattdessen aus 4 satt überlappenden Flächen bauen
  (Referenz: HBL `ScreenFrameVisual`).
- **Motion-Qualität:** Für jede Komposition gilt die Doktrin in
  `docs/motion-doctrine.md` (Easing, Szenen-Rhythmus, Video-Skalen,
  Transition-Rezepte, Technik-Fallen) — bei neuen Animationen vorher
  lesen.
- **Handwerk und Bausteine (seit 2026-09-19):** Zwei Projekt-Skills unter
  `.claude/skills/` (Repo-Root, beide Macs):
  - `remotion-craft` — Art Direction / Motion-Personality, Lower Thirds,
    Testimonial-Karten, Logo-Reveals, Style-System, Custom-Transitions,
    Beat-Sync, 3D, Ken-Burns-Shimmer, QA-Rubrik; Tabelle „Was zuerst lesen"
    im SKILL.md, Texte in `references/`. Vor dem Bauen die zur Aufgabe
    passende Referenz lesen.
  - `remocn` — Copy-Paste-Komponenten von remocn.dev (Text-Reveals,
    Signature-Transitions, Shader-Hintergründe, Odometer, Handschrift,
    Konfetti, Charts). Katalog live: `https://remocn.dev/llms-components.txt`.
    Installieren **nur** über `npm run remocn:add -- <name> [<name> …]`
    (die shadcn-CLI beschädigt String-Literale); Dateien landen in
    `src/components/remocn/`, Import `@/components/remocn/<name>`.
    Eigene Änderungen an Komponenten in `src/components/remocn/_NIRO-PATCHES.md`
    festhalten. Kundenschrift für alle Remocn-Textkomponenten per CSS-Variable
    am Root: `style={{ "--font-geist-sans": '"Meutas", sans-serif' }}`.
    Lebender Nachweis: `NiroDemo-RemocnShowcase` (Ordner NIRO-Demo im Studio).
  - Shader-Komponenten brauchen WebGL im Headless-Render — `remotion.config.ts`
    setzt deshalb `Config.setChromiumOpenGlRenderer("angle")` (ohne: schwarze
    Flächen, Log „WebGL is not supported"). Nicht-WebGL-Kompositionen rendern
    damit identisch (geprüft 2026-09-19).
  - SFX ohne Downloads: `npm run sfx` erzeugt `public/sfx/*.wav` (Whoosh, Pop,
    Bass, Tick, Pad; gitignored, jederzeit neu erzeugbar) → `<Audio
    src={staticFile("sfx/whoosh.wav")}>`; Hit 2–3 Frames vor dem visuellen Landen.
  - Alpha-Overlays: Shader/Backdrops sind opak — nur in Vollbild-Szenen oder
    hinter `!transparent`; vor jedem Komponenten-Einsatz `background:` am Root
    prüfen (Alpha-Falle oben).
- **Untertitel/Text-Overlays, Premium-Stufe:** Für gestaltete Captions
  (Hero-Wörter, Glass-Look, Platzierung um den Sprecher) gilt
  `docs/cinematic-captions.md` — vor dem Bauen lesen, Caption-Plan nach
  dessen Abschnitt 8 erstellen. Schnelle Recruiting-Formate behalten ihre
  bestehenden Kunden-Systeme.
- **Caption-Datenkette (seit 2026-08-31, Remotion 4.0.519):** Wort-Timings
  aus den Scribe-JSONs (`projects/.../_intern/cache/*.scribe.json`) nicht
  mehr von Hand gruppieren, sondern:
  `elevenLabsTranscriptToCaptions()` (`@remotion/elevenlabs`) →
  `Caption[]` → `createTikTokStyleCaptions({captions,
  combineTokensWithinMilliseconds})` (`@remotion/captions`) → Pages mit
  Token-Timings für Wort-Highlights; `serializeSrt()` liefert nebenbei
  SRT für Premiere. **Pflicht-Adapter:** unser Cache-Format hat kein
  `type`-Feld — vor dem Aufruf `words.map(w => ({text: w.text, start:
  w.start, end: w.end, type: "word", logprob: 0}))`, sonst überspringt
  die Funktion ALLE Einträge stumm (leeres Ergebnis, kein Fehler).
  Verifiziert am WTN-Imagefilm-Cache (230 Wörter → 61 Pages).

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
