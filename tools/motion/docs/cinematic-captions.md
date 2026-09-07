# Cinematic Captions — Design-System für Remotion-Untertitel

Premium-Stilstufe für Untertitel/Text-Overlays: statt fester Untertitel-Leiste
werden Sinneinheiten als gestaltete „Momente" im Bild gesetzt — Hero-Wörter
groß, halbtransparent, räumlich um den Sprecher platziert. Gedacht für
Image-/Premium-Projekte; die schnellen Recruiting-Formate behalten ihre
bestehenden Systeme (Keyword-Kästen, Kicker/Punch/Stack).

Quelle: adaptiert aus `audrey-560/hyperframes-cinematic-caption` (MIT) und
den `embedded-captions`-Referenzen aus `heygen-com/hyperframes` (MIT); auf
Remotion und NIRO-Konventionen übersetzt. Alle px-Angaben beziehen sich auf
1080×1920 (Hochformat); für 16:9 sinngemäß skalieren.

Zwei Ausbaustufen: **Rail + Embed** (Abschnitt 11 — schlichte
Untertitel-Leiste plus einzelne Peak-Wörter, der leichtere Modus) und
**volle Cinematic Captions** (Abschnitte 2–6 — alles räumlich gesetzt).
Timing (Abschnitt 1) und Verifikation (Abschnitt 10) gelten für beide.
Allgemeine Bewegungs-/Easing-Regeln: `docs/motion-doctrine.md`.

## 1. Transkript in Cues schneiden

- Wort-Timings kommen aus den Scribe-JSONs (`_intern/`), nie schätzen;
  angezeigtes Timing max. ±80 ms vom Transkript-Wort.
- Pro Cue 2–5 angezeigte Wörter (min. 2, max. 6), ca. 0,65–1,8 s, hart
  max. 2,5 s. An Sinn, Kontrast, Atmung und rhetorischen Wendungen
  brechen — nicht an fester Wortzahl. Mechanische Bruchstellen: Pause
  ≥ 500 ms, Satzende, Komma + Pause ≥ 250 ms.
- Cue öffnet bei `erstes Wort − 0,08 s`, schließt bei
  `letztes Wort + 0,6 s` (aber ≤ 0,05 s vor dem nächsten Cue). Jeder Cue
  ≥ 0,5 s sichtbar. **Nie während laufender Sprache ausfaden** — nur in
  der Pause danach.
- Nur 70–85 % des Gesagten anzeigen: Füllwörter, Selbstkorrekturen und
  Schluss-Interpunktion raus. Wichtige Phrasen dürfen länger stehen.
- **Ganze Sinneinheiten, nie Satzteile** (David-Regel). Adjektiv nicht vom
  Nomen trennen, Aktion nicht vom zugehörigen Keyword.
- **Keine Dopplung:** Was ein Keyword-Kasten/Hook inhaltlich schon sagt,
  fliegt aus dem Untertitel (David-Regel).
- Mixed Case ist Standard. ALL-CAPS nur für Akronyme, kurze Proof-Labels
  oder ein bewusst gesetztes CTA-Keyword.

Jedem Cue eine Rolle geben: `setup` (Kontext), `anchor` (Kernbegriff),
`contrast` (Umkehrung), `proof` (Zahl/Ort/Beleg), `aside` (Brücke),
`payoff` (Schlussfolgerung), `cta` (Handlungsaufforderung).

Cues zu **semantischen Gruppen** bündeln (eine Gruppe = ein Satz/Kontrast/
Beweis/CTA) mit `orderIndex` in Sprechreihenfolge. Stack-Grammatiken:

- `support → hero`: Kontext zuerst, entscheidendes Wort danach
- `eyebrow → hero → qualifier`: kompakter Aufbau, dominante Idee, Einordnung
- `proof-label → Zahl/Ort`: kleines Label vor dem großen Beweiswert
- `cta-setup → Aktion → Keyword → Schluss`: komplette Anweisung chronologisch
- `parallel hero sequence`: Listen-Items ersetzen einander in derselben Zone

## 2. Emphasis vergeben (Scoring statt Bauchgefühl)

Drei Stufen (Hochformat-Richtwerte):

| Stufe | Größe | Gewicht | Anteil |
|---|---|---|---|
| `support` | 52–80 px | Regular/Medium, Weiß | 60–75 % |
| `anchor` | 76–112 px | Semibold/Bold, 1 Akzent | 20–35 % |
| `hero` | 150–240 px (Zahl/Ort bis 280) | Extra-Bold/Condensed Display | 5–15 % |

Hero-Kandidaten vor dem Stylen scoren:

- +3 wenn das Wort fehlt → Aussage bricht zusammen
- +2 konkreter Beweis (Zahl, Ort, Feature, Ergebnis)
- +2 gesprochene Betonung, Umkehrung, Punchline, CTA-Keyword
- +1 kurz genug, um in Hero-Größe lesbar zu bleiben
- −3 Füllwort, Bindewort, generisches Nomen ohne Argumentgewicht
- −2 benachbarter Cue trägt dieselbe Betonung schon
- −2 sichere Platzierung würde Buchstaben oder Szeneninhalt verdecken

**Hero ab Score 4**, normalerweise nur der höchste Kandidat pro
Argument-Beat. Ein Wort wird nicht Hero, nur weil es ein Nomen ist. Eine
Passage ganz ohne Hero ist gültig. Parallel-Listen dürfen mehrere Heroes
als eine dokumentierte `heroSequence` tragen.

Feinere Budget-Sicht über ein ganzes Video: ~70 % plain, ~20 % leichter
Lift (Farbe ODER Gewicht, nie beides), ~8 % volle Emphase, ~2 % Climax —
ein Climax-Moment hält 1,5 s und bekommt eine Atempause davor und danach.
Höchstens ~30 % aller Cues tragen überhaupt eine Emphase.

**Proof-Pflichtprüfung:** Zahlen/Claims in Proof-Cues nur, wenn
Website-belegt (David-Regel „nur Website-Infos"). CTA-Endcards mit
Berufstitel brauchen „(m/w/d)".

## 3. Typografie

Dreiteilige Hierarchie, Fonts aus `brand.json` / `font-loader.ts`:

- Support: sauberer Sans in echtem Regular/Medium
- Hero: echter Extra-Bold-/Black-/Condensed-Schnitt — die Datei muss das
  Gewicht wirklich enthalten
- Editorial-Akzent: gelegentlicher Serif/Italic für Asides/CTA — nicht überall

Nie synthetisch fetten (kein 700-File als 800 deklarieren, kein
Browser-Bolding, keine dicken Strokes als Fake-Gewicht), kein exzessives
negatives Tracking. Hero-Wörter in voller Auflösung auf verschmolzene
Striche und mehrdeutige Buchstaben prüfen.

Farbe: Support standardmäßig Weiß; auf hellen Frames Weiß mit dezentem
Stroke/Schatten/lokalem Scrim halten, bevor auf Schwarz gewechselt wird.
Pro 8–12-s-Passage: Weiß + eine Glass-Familie + max. ein Akzentton (mehr
nur mit CI-/Sinn-Begründung).

## 4. Platzierung um den Sprecher

Basis bleiben unsere Review-Werkzeuge: Safe Zone + FaceZone aus
`src/core/format-utils.ts`, geprüft mit `ReviewOverlay`
(`review.showGuides`). Zusätzlich:

- Pro Cue Anfang/Mitte/Ende sichten: Gesicht, Mund, Haare, Schultern,
  Hände, Produkte, UI, vorhandener Text → daraus die Bewegungs-Envelope
  bilden, damit eine Platzierung über die ganze Cue-Dauer sicher ist.
- Vordergrund-Support hält **mind. 40 px Abstand** zu Gesicht/Mund.
- Anker-Zonen: upper-left/right, shoulder-left/right, center-gap,
  lower-left/right. Untere Plattform-UI-Zone meiden (deckt unser
  Safe-Zone-Check ab).
- Pro semantischer Gruppe eine `flowDirection` festlegen (z. B. oben-links
  → unten-rechts). Spätere Fragmente laufen weiter oder bleiben — **nie
  die Richtung umkehren** (kein Auf-Ab-Auf innerhalb eines Satzes).
- Fragmente derselben Gruppe behalten ihre Anker-Zone; Layout wechselt an
  Satz-/Shot-/Argument-Grenzen, nicht pro Wort.
- Pro 8–12 s ca. **3–5 Layout-Zustände**; zwischen fremden Gruppen nur
  **1–2 Eigenschaften** ändern (Zone, Ausrichtung, Größenverhältnis,
  Tiefe, Füllung ODER Motion — nicht alles auf einmal).
- Zeilenabstände: Support-zu-Support line-height 0,96–1,10;
  Support-zu-Hero ca. 0,15–0,45 × Support-Größe; CTA-Aktion und Keyword
  visuell direkt benachbart.
- Innerhalb einer Gruppe liest sich alles in Sprechreihenfolge, auch im
  Standbild. Text bleibt gerade — Rotation nur mit CI-Begründung.
- **Seitenwahl** (bei zwei möglichen Zonen): 1. eingebrannte Grafiken/
  Bauchbinden meiden → 2. größere Clean-Zone gewinnt (Differenz < 10 %
  Framebreite = gleichwertig) → 3. Text auf die Gegenseite der
  Blickrichtung (Looking Room erhalten).
- Augen-Bounding-Box + 20 px Rand ist absolut tabu; das Gesicht nie
  dauerhaft > 70 % verdecken (pro 0,3-s-Fenster ≥ 30 % frei).
- Fester Caption-Platz wird monoton — nach Shot variieren: Close-up →
  oben/seitlich, Mid → Rückwand/Schulterzone, Wide → versetztes
  Lower-Third. Letterbox-Balken sind legitimer Caption-Platz.
- Kontrast auf Footage nach den Luminanz-Gates aus
  `docs/motion-doctrine.md` (Scrim nur textbox-groß, nie framebreit).

## 5. Treatments

- **Clean editorial** (Standard): präziser Sans, kein Kasten, weicher
  Schatten nur bei Kontrastbedarf.
- **Weight-/Scale-Shift:** dünne Support-Wörter + ein fetter Anchor.
- **Hero-Wort:** kurzes Überschießen und Setzen; darf neben/hinter dem
  Subjekt sitzen, solange Maske und Kontrast lesbar bleiben.
- **Proof-Größe:** wichtige Zahl/Ort als visueller Beweis, 170–280 px,
  darf fast die Framebreite spannen; kleines weißes Label dazu.
- **Tinted-Glass-Hero** (Default für transluzente Heroes): silber-weißes
  Glas, Glyphen-Füllung **32–55 % Opacity** (Footage bleibt durchs Wort
  sichtbar), feiner Rim 0,75–1,25 px, dezentes inneres Highlight,
  optionaler Licht-Sweep 0,4–0,8 s bei stehender Letterform. Farbton nur
  mit Marken-/Sinn-Begründung; keine Scanlines/Streifen ohne explizite
  Anforderung, kein Pastell-Regenbogen, kein schwerer Bevel.
- **Behind-Subject-Tiefe:** nur mit echter Matte/Cutout — nie faken.
  Ebenen-Stack in Remotion: Footage unten → Hero-Text Mitte →
  Subjekt-Cutout (Alpha-Video) darüber → Support-Copy ganz oben.
  Cutout muss framegenau zum Footage passen (Start, FPS, Dauer, Crop,
  Scale); bei Doppelkontur/Halo: Original-RGB mit Matte-Alpha neu
  kombinieren, nicht mit Blur/Schatten kaschieren.
- **Occlusion-Budget** pro Hintergrund-Hero: 0,10–0,20 leicht (Haar/
  Schulter), 0,20–0,30 stark aber sofort lesbar, 0,30–0,35 Maximum für
  sehr kurze bekannte Wörter, darüber → umplatzieren. Gesicht/Mund zählen
  nie als akzeptable Überdeckung. Bevorzugt kreuzt das untere
  Buchstaben-Drittel Haar/Schulter/Arm; identitätsstiftende Innenbuchstaben
  schützen (Wort darf nie falsch geschrieben wirken). Mit sauberer Matte
  sind **10–22 % Haarlinien-Überlappung** der Sweet Spot — ein großes Wort
  über ungenutztem Leerraum wirkt schwächer als eines, dessen Unterkante
  hinter dem Subjekt liegt.
- **Soft Bloom:** nur für leuchtende/aspirationale/Premium-Momente;
  0,20–0,40 s Bloom am Entry, dann scharf. Nie dauerhafter Neon-Halo.
- **Evidence-Grafiken:** Karten/Icons/Zahlen als Beleg am `proof`-Cue,
  ein Cluster mit klarer Hierarchie. Screenshots/Ordner/Dateien nativ
  zeigen (leichter Schatten), Panels nur für echte UI-Flächen. Bei
  Schritt-für-Schritt-Inhalten erledigte Belege stehen lassen, solange
  der nächste Schritt davon abhängt (`persistenceGroup`).

## 6. Motion-Vokabular (Remotion: `interpolate`/`spring`, nur transform+opacity)

Entries schnell und entschlossen: **0,18–0,45 s**. Frame-basiert ist bei
uns automatisch seek-safe — keine wallclock-Animationen.

Stagger/Hold nach Ton des Videos (Wort-Stagger / Standzeit-Basis):

| Ton | Stagger | Hold | Default-Move |
|---|---|---|---|
| dokumentarisch | 150 ms | 600 ms | Burn-in 70 % Opacity + Fade-up |
| conversational | 80 ms | 400 ms | word-fade-up |
| energetisch | 50 ms | 300 ms | word-pop |
| poetisch | 250 ms | 1200 ms | langsamer Fade |
| Keynote/Statement | ganze Phrase | — | Swipe/clip-path 400 ms |

- `support-cascade`: 10–22 px Rise + Opacity, 30–55 ms Wort-Stagger
  (bei progressiven Gruppen 80–180 ms semantischer Stagger)
- `firm-settle`: Scale 0,88 → 1,04 → 1 für Anchor-/Hero-Landung
  (0,26–0,36 s beim Hero-Handoff)
- `editorial-wipe`: overflow-hidden-Reveal für saubere Phrase/Ort
- `directional-snap`: 18–36 px von der nächsten Framekante
  (Foreground-Payoff: 14–28 px von der offenen Seite, ohne Bounce)
- `rule-draw`: kurze Unterstreichung/Divider zeichnet nach dem Anchor
- `bloom-settle`: Glow/Blur-Peak am Entry, Glyphe bleibt scharf
- `fill-drift`: Wort landet zuerst, dann bewegt sich nur die transluzente
  Füllung/das Footage im Glyphen
- `depth-reveal`: großes Wort auf Mittelebene, real vom Cutout überdeckt
- `card-orbit`: Evidence-Karten aus nahen Vektoren in ein Cluster

Progressive Builds: Fragmente erscheinen an ihren echten Wort-Starts und
akkumulieren zum Lockup — **nie die fertige Phrase zeigen, bevor sie
gesprochen ist**. Build-Modi: `replace`, `progressive`,
`foreground-background-handoff`, `proof-reveal`, `cta-build`. Blur nur als
kurzer Übergang, innerhalb 0,4 s scharf. Nicht Bounce+Blur+Rotation+Glow
auf denselben Cue stapeln.

## 7. Sound (optional — meist Premiere-Sache)

Akzente ans **visuelle Landing** koppeln, nicht an den Animationsstart.
Support meist still; Wipe → kurzes Whoosh; Anchor → gedämpfter Pop; Hero →
kontrollierter tiefer Impact; Bloom → ein einziges Shimmer pro Passage.
Max. ein hörbarer Akzent pro Beat, benachbarte Beats nie mit demselben
Chime. Da unsere Overlays i. d. R. in Premiere vertont werden: SFX-Empfehlung
pro Hero-Beat als Notiz in Protokoll/Übergabe statt eingebrannt.

## 8. Caption-Plan vor Implementierung

Vor dem Bauen einen Plan als JSON in `_intern/` der Charge ablegen
(`cinematic-caption-plan.json`): pro Cue `id` (stabil, `cc-…`),
`semanticGroupId`, `orderIndex`, `start`/`end` (exakte Sekunden aus
Scribe), `text`, `role`, `emphasis`, `heroReason` (Score nennen),
`placement`/`anchorZone`, `flowDirection`, `buildMode`, `treatment`,
`occlusionBudget`, `motion`, ggf. `foregroundText`/`heroText`,
`persistenceGroup`, `audioAccent`-Empfehlung. Der Plan ist die
Review-Grundlage im Chat, bevor Komposition gebaut wird.

## 9. Betriebsarten in unserer Pipeline

- **Voll-Komposition** (Footage in Remotion): alle Treatments möglich,
  inkl. Behind-Subject und Video-through-Type.
- **Alpha-Overlay für Premiere** (ProRes 4444): Tinted-Glass funktioniert
  — 32–55 %-Weiß mit Alpha legt sich in Premiere wie Glas übers Footage.
  Behind-Subject nur, wenn der Cutout mit in die Komposition kommt oder
  der Cutter den Cutout in Premiere ÜBER unser Overlay legt (dann im
  Schnittplan/Übergabe dokumentieren).

## 10. Verifikation (ergänzt die Pflicht-Checkliste aus CLAUDE.md)

Kontaktbogen bauen: `npx remotion still` an jeder Cue-Mitte (+ früh/spät
bei Depth-Cues), chronologisch nebeneinander sichten. Ablehnen wenn:

- drei fremde Gruppen dieselbe Mittelachse + dasselbe Layout-Rezept teilen
- zwei fremde Hero-Wörter Palette, Größe, Platz UND Motion wiederholen
- jede Phrase schon im ersten sichtbaren Frame komplett ist
- das Subjekt identitätsstiftende Buchstaben eines Heroes verdeckt
- der Cutout Halo/Doppelkontur/Farbversatz zeigt
- eine Gruppe ihre Leserichtung umkehrt oder pausiert nicht in
  Sprechreihenfolge lesbar ist
- CTA-Aktion und Keyword in konkurrierenden Zonen liegen
- ein Hero synthetisch gefettet ist oder Striche verschmelzen
- Hero-Treatments zahlreicher sind als saubere Support-Cues
- Ort-/Flaggen-/Map-Texturen ohne inhaltlichen Anlass auftauchen

Zusätzliche QA-Tests aus der embedded-captions-Schule:

- **Poster-Test:** Der Climax-Frame muss allein als Posting funktionieren.
- **Scene-Handshake:** Die Typo muss auf ≥ 2 Arten anerkennen, dass sie
  auf DIESEM Footage sitzt (gesampelter Akzentton, echte Occlusion,
  Schattenrichtung, Tiefen-Blur, Farbtemperatur) — sonst wirkt sie wie
  ein Sticker.
- **Timid-Test:** Wirkt die Passage zaghaft (alles gleich klein, keine
  Hierarchie), Emphasis-Verteilung prüfen.
- **Dead-Air-Audit:** längere stumme Strecken ohne bewussten Grund?
- **Fresh-Eyes:** Review idealerweise durch einen Subagenten, der NUR den
  Kontaktbogen + diese Checkliste bekommt (kein Baukontext).

Danach wie immer: FaceZone-/SafeZone-Scrub mit `ReviewOverlay`, Guides
aus vor dem Final-Render.

## 11. Stilstufe Rail + Embed (leichter Modus)

Das Zwei-Spur-Modell für Projekte zwischen Standard-Untertiteln und voller
Cinematic-Inszenierung:

- **Rail:** schlichte Untertitel-Leiste trägt 80 %+ des Texts. Höhe
  ~4,5 % der Framehöhe (≈ 86 px @1080×1920, ≈ 48 px @1080p), Weight
  500–600, max. 2 Zeilen à 32–42 Zeichen, immer vor dem Subjekt. Position
  nach Shot variieren (s. Abschnitt 4), im Hochformat y ∈ 12–78 %
  (untere 22 % = Plattform-UI).
- **Embed:** höchstens EIN Peak-Wort pro Sinnabschnitt wird groß und
  wandert hinter den Sprecher (echte Matte, Occlusion-Budget aus
  Abschnitt 5). Auswahl über das Hero-Scoring aus Abschnitt 2.
- **Crown-Regel** (großes Wort quer über den Körper): nur wenn das
  Subjekt mittig steht (±10 % Framebreite), beidseitig ≥ 15 % Clean-Zone
  bleibt und das Wort breiter ist als der Körper + 400 px — sonst in die
  Clean-Zone schrumpfen oder als Emphase in die Spalte setzen.
  **Max. 1 Crown pro Video.**
- Rail-Wörter nie per `letter-spacing`/`blur` einfliegen (Reflow-Sprung)
  — transform + opacity, wie überall.
