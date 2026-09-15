# Protokoll — REM / Gewerbedach / 2026-07 Erster Dreh

## 2026-07-07 — Animation aus Testimonial-Transkript

**Gemacht:**
- Chargen-Struktur angelegt, Transkript nach `Material/` verschoben
  (`Transcribe REM Gewerbedach Reinigung.srt`, Wort-Timings mit 1h-Timecode-Offset).
- Neue Remotion-Komposition **REM-Gewerbedach-Reinigung**
  (`tools/motion/src/clients/rem-maler/projects/gewerbedach-reinigung/`),
  Stil identisch zu Dachbeschichtung V2 Premium (Line-Art, dunkler Verlauf,
  REM-Rot, Rim Light, Slide-Texte). 4K landscape, 25 fps, 106 s
  (O-Ton endet bei 103,44 s; Frame 0 = Audio 0).
- 7 Szenen wortsynchron zum O-Ton: Ausgangslage (0–11 s), Reaktion/Angebot
  (12–31 s), Preis-Leistung (31–41 s), Kran/Beschichtung (42–58 s),
  Sprechpause mit Kamerafahrt (58–70 s), Gewährleistung (70–79 s),
  Ergebnis + PV-Module (80–98 s), Fazit/Weiterempfehlung (98–103 s).
  Bullets erscheinen auf den Wort-Timestamp der jeweiligen Aussage
  (`bulletFrames` in `constants.ts`).
- Neue Szenen-Komponenten: `CraneRig` (Spezialfahrzeug, Ausleger folgt der
  Beschichtungskante) und `PVPanels` (Module + Glanz-Sweep bei „gereinigt").
- Geometrie: Gewerbehalle (breit, flach geneigt) statt Einfamilienhaus.

**Geliefert:** noch kein Render — Vorschau in Remotion Studio geöffnet
(`http://localhost:3000/REM-Gewerbedach-Reinigung`), Still-Checks über alle
Szenen ok.

**Entscheidungen:**
- Slide-Texte ausschließlich aus O-Ton-Aussagen (keine erfundenen Claims);
  Garantie exakt wie gesprochen: 5 J. Arbeitsausführung / 20 J. Farbe (Hersteller).
- Dachfarbe verwittert-grau → REM-Rot per Coating-Wipe während der Kran-Szene.

**Offen:**
- ~~Feedback David zu Vorschau~~ → Richtungswechsel, siehe unten.

## 2026-07-08 — Richtungswechsel: Transparentes Overlay statt Fullscreen

**Gemacht:**
- Feedback David: keine Fullscreen-Haus-Animation — stattdessen transparentes
  Overlay über das Sprecher-Video, im Stil des Sauber-Entsorgen-Erklärvideos,
  aber in REM-CI (rem-maler.de: REM-Rot #D83C31, kantige Ecken, Inter).
- Neuer REM-Overlay-Baukasten `tools/motion/src/clients/rem-maler/components/overlay/`:
  KeywordLowerThird (weiße Karte, roter Kantenbalken + Badge + Unterstrich),
  ServiceChips, StackList (rotes Uppercase-Heading; tone pos=Rot / neg=Grau),
  18 eigene Line-Icons (Kran, Gerüst, Solar, Farbroller, …).
- Neue Komposition **REM-Gewerbedach-Overlay**
  (`projects/gewerbedach-overlay/`): 1920×1080, 25 fps, 105 s, transparent,
  `timeOffsetSec`-Prop zum Ausrichten im Schnitt. 19 Szenen wortsynchron zum
  O-Ton (`transcript.ts`), u. a. Vergleichsliste Angebotsdauer (REM 1 Woche
  vs. Andere 3–4 Wochen), Chips „Ohne Einrüstung / Arbeiten vom Kran aus",
  Gewährleistungs-Liste (Items erscheinen auf den Timestamp), Fazit +
  „Klare Weiterempfehlung". Sprechpause 57,8–69,7 s bewusst ohne Overlay.
- Alte Fullscreen-Komposition REM-Gewerbedach-Reinigung bleibt registriert
  (Referenz), wird aber nicht geliefert.

**Geliefert:**
- `Ergebnisse/Renders/rem-gewerbedach-overlay-4k.mov` — ProRes 4444 mit
  Alpha, 3840×2160, 25 fps, 105 s, ~980 MB (verifiziert per ffprobe).
  Pre-Delivery Review vor Render: Face Zone (rechte Hälfte) & Safe Zone
  per Guide-Stills geprüft, Guides im Export aus.

**Entscheidungen:**
- Annahme: Sprecher rechts im Bild → Grafiken links verankert, Face Zone =
  rechte Hälfte (per `review.faceZone` anpassbar).
- Texte weiterhin ausschließlich aus O-Ton-Aussagen.

**Offen:**
- ~~Feedback David~~ → Kundenfeedback siehe unten.

## 2026-07-08 — Kundenfeedback eingearbeitet (v2)

**Feedback:** Einblendungen teilweise nutzlos/„random"; Farblogik gewünscht:
negativ = Rot, positiv = Grün.

**Gemacht:**
- Farb-Töne: `tone` pro Element — pos = Grün (#2E9E5B), neg = REM-Rot;
  auch KeywordLowerThird hat jetzt einen tone (Badge, Kantenbalken,
  Unterstrich wechseln mit).
- Szenen von 19 auf 12 reduziert: generische Cues gestrichen (Zustand
  befriedigend, Höchste Zeit, Fazit-Liste, PV-Doppel-Cue u. a.);
  stattdessen zwei Rot/Grün-Gegenüberstellungen: „Angebot" (REM fix vs.
  Andere 3–4 Wochen) und „Einrüstung" (Andere Halle einrüsten vs. REM
  Arbeiten vom Kran) — Items weiterhin wortsynchron.
- v2-Render gestartet: `rem-gewerbedach-overlay-4k-v2.mov` (ProRes 4444
  Alpha, 4K, 25 fps). v1 bleibt als Referenz liegen.

**Offen:**
- ~~v2 an Kunden; bei Freigabe v1 löschen~~ → Kundenfeedback siehe unten.

## 2026-07-22 — Kundenfeedback eingearbeitet (v3): REM von Anfang an

**Feedback:** Am Videoanfang muss direkt erkennbar sein, dass es um REM geht
(der O-Ton nennt „die Firma REM" erst bei 42,8 s; im Overlay tauchte REM
bisher erst bei ~19 s auf).

**Gemacht:**
- Neue Absender-Karte **BrandIntro** (`components/overlay/BrandIntro.tsx`)
  bei 0,5–4,4 s, unten links wie die Cues: R-Monogramm + „REM
  Malerfachbetrieb" (REM in Rot) + Unterzeile „Kundenstimme · Gewerbedach";
  Exit endet, bevor der erste Cue (4,6 s) erscheint.
- R-Monogramm als Vektor (`RemMark.tsx`): Path + Original-Rotverlauf 1:1 aus
  dem Favicon von rem-maler.de übernommen — verlustfrei skalierbar; das
  Website-Logo-Bitmap (300 px) wäre für 4K zu klein gewesen. Logo-Assets
  jetzt unter `public/clients/rem-maler/` (logo.png/webp, favicon.svg),
  Logo-Pfad in `brand.json` nachgetragen.
- Szene 2 umformuliert: „**REM**-Chef meldete sich innerhalb 1 Woche" —
  Firma auch im ersten inhaltlichen Cue verankert (O-Ton: „hat sich dann
  der Chef bei mir gemeldet").
- Pre-Delivery Review: Stills Frame 40/118/360 geprüft — BrandIntro bleibt
  links außerhalb der Face Zone (rechte Hälfte) und innerhalb der Safe Zone,
  kein Overlap mit Cue 1; Guides in den Default-Props aus.

**Geliefert:**
- `Ergebnisse/Renders/rem-gewerbedach-overlay-4k-v3.mov` (ProRes 4444
  Alpha, 4K, 25 fps — Render dieser Session).

**Entscheidungen:**
- „REM Malerfachbetrieb" als Anzeigename (wie brand.json), nicht der volle
  Firmenname „Malerfachbetriebsgesellschaft mbH" — zu sperrig für eine Karte.
- Unterzeile „Kundenstimme · Gewerbedach" kennzeichnet das Format (kein
  O-Ton-Claim, daher zulässig neben der Nur-O-Ton-Regel für Aussagen).

**Offen:**
- v3 an Kunden; Renders-Ordner war zu Sessionbeginn leer (v1/v2 lokal nicht
  mehr vorhanden — vermutlich nach Übergabe ausgelagert).
