# Protokoll — MAN / Lagervideos / 2026-08 CTA Lagerlogistik

## 2026-08-13 — CTA-Endcard „Fachkraft für Lagerlogistik" im Wartezimmer-Web-Look

**Anlass (Kundenwunsch via David):** CTA für die Lagervideos mit dem Beruf
„Fachkraft für Lagerlogistik", Claim „Großes Bewegen mit MAN" wie im
Wartezimmervideo, Stil ähnlich dazu.

**Gemacht:** Neue Komposition `ManLagerCtaWeb` (ID `MAN-LagerCTA-Web`,
`tools/motion/src/clients/man/projects/lager-ausbildung-cta/CompositionWeb.tsx`)
— ersetzt für diesen Zweck den alten „KRANK"-Still-Ads-Look (`MAN-LagerCTA`
bleibt unangetastet daneben bestehen). Design = 1:1 die Tokens der
freigegebenen Wartezimmer-CTA-Endcard (v9): Anthrazit #2E3A46, Radius 0
überall, Rot #E30045 nur als Akzent, MAN Global Cond Versalien, Logo als
Bilddatei, dunkler Löwe Ton-in-Ton links mit Blick nach rechts
(MAN-Auflage 2026-07-29), Claim-Zweizeiler „GROSSES BEWEGEN / MIT MAN"
(MIT MAN rot) + roter Balken + „JETZT BEWERBEN", QR jobs.man.eu mit Label
JOBS.MAN.EU. Aufbau 9:16: Logo → Kicker „STARTE DEINE AUSBILDUNG" →
Berufstitel „FACHKRAFT FÜR LAGERLOGISTIK" + „(m/w/d)" (Pflicht-Regel) →
Benefits-Liste mit rotem Vertikal-Balken (man.eu-Listen-Token), QR rechts
daneben → Claim-Block. Eintritt gestaffelt über ~4 s, Text nur Fade + Y
(keine X-Bewegung, WZ-Regel v6), nichts pulsiert; Löwe driftet minimal
(nie ganz statisch). Start transparent (0,4 s Aufblende) → übers Videoende
legbar. Alle Texte als Props editierbar (inkl. `zeigeQr`).

**Review:** Safe-Zone-Still mit Guides geprüft (Inhalt endet bei ~79 % Höhe,
unteres IG/TikTok-UI-Feld frei — gleiche Praxis wie beim alten Lager-CTA);
keine Gesichter (reine Grafik, Face-Zone n. a.); Guides in den Final-Renders
aus. Verifiziert am gerenderten File: ProRes 4444 mit Alpha (yuva444p12le),
Frame 0 voll transparent, 300 Frames/30 fps, Steady-Frame inhaltlich korrekt.
QR-Asset identisch mit dem am 2026-07-29 real dekodierten
`qr-jobs-man-eu.png` (→ https://jobs.man.eu/).

**Geliefert (`Ergebnisse/Renders/`):**
- `MAN-Lager-CTA-Lagerlogistik-4K.mov` — ProRes 4444 Alpha, 2160×3840/30p, 10,0 s, 320 MB
- `MAN-Lager-CTA-Lagerlogistik-Preview.mp4` — H.264 CRF 18, 1080×1920/30p, 1,1 MB

**Entscheidungen:**
- Kicker, Benefits (Vergütung/30 Tage Urlaub/iPad/36h) und Berufstitel aus dem
  bestehenden Lager-CTA übernommen; CTA-Wording auf das MAN-freigegebene
  „JETZT BEWERBEN" der Wartezimmer-Endcard gesetzt (statt „in unter 1 Min. /
  ohne Lebenslauf" — Funnel nicht verifizierbar, Website-Regel 2026-08-01).
- 30 fps wie der alte Lager-CTA; fps ist Prop, Wechsel auf 25p = Re-Render.

**Offen (David):**
1. Kundenmail sprach von „folgenden Beruf … aufnehmen" — umgesetzt als
   Endcard FÜR „Fachkraft für Lagerlogistik". Falls MAN einen WEITEREN,
   im Chat nicht genannten Beruf meinte: Titel nachreichen → zweite
   Variante ist ein Props-Wechsel + Re-Render.
2. ~~Benefits-Zeilen gegenchecken~~ → verifiziert, siehe 13.08. unten.
3. ~~QR in 9:16-Ads gewünscht?~~ → David 13.08.: kein QR.
4. Standzeit 10 s — David kürzt bei Bedarf in Premiere.

## 2026-08-13 — QR raus (Davids Vorgabe), Benefits-Herkunft verifiziert

**Gemacht:** (1) QR-Code auf Davids Ansage entfernt — Default `zeigeQr:false`
in CompositionWeb.tsx, beide Renders + Still neu (gleiche Pfade/Specs,
ProRes 4444 Alpha verifiziert, 300 F). Rechte Spalte trägt jetzt der
Ton-in-Ton-Löwe. (2) Herkunft der Benefits geklärt: Sie standen wörtlich so
als Defaults im alten `MAN-LagerCTA` (KRANK-Look), der mit dem
Squash-Erst-Commit des Motion-Repos (2026-07-07, vor der Studio-Struktur)
reinkam — im Repo KEINE dokumentierte Quelle. Deshalb gegen MAN-Quellen
web-verifiziert; alle vier Zeilen gedeckt:
- „Attraktive Vergütung", „30 Tage Urlaub", „36h Woche" → MAN-eigene
  Ausbildungs-Stellenanzeigen Fachkraft für Lagerlogistik auf jobs.man.eu
  (MAN Truck & Bus Deutschland GmbH, z. B. Flensburg 2026: tarifliche
  Vergütung mit übertariflichen Zulagen, 36-Stunden-Woche, 30 Urlaubstage,
  Urlaubs-/Weihnachtsgeld).
- „Kostenloses iPad" → man.eu-Karriereseite („Das iPad, das du während der
  Ausbildung erhältst, darfst du auch privat nutzen") + Anzeigen (iPad
  geschenkt zum Ausbildungsstart).

**Nuance (dokumentiert):** Die zentrale man.eu-Konzern-Karriereseite nennt
35-Stunden-Woche (SE/Werke, bayerischer Tarif); für die Lagerlogistik-
Ausbildung in den Servicebetrieben (Deutschland GmbH) nennen deren eigene
Anzeigen 36 h — die CTA-Zeile „36h Woche" stützt sich auf die konkret
passende Anzeige. Falls MAN intern anders zählt, einfach Props ändern.

## 2026-08-13 — Wording an die laufenden Kampagnen-Ads angeglichen

**David zeigt die Still-Ads der Lager-Kampagne** (Screens: „1 PLATZ / 1 CHANCE /
1 KLICK" und „EINE AUSBILDUNG DIE RICHTIG KNALLT", beide Karlsruhe).
Damit ist die Benefits-Herkunft endgültig geklärt: Die Defaults des alten
KRANK-CTAs sind die kondensierten Kampagnen-Benefits — deckungsgleich mit den
Ads (36-Stunden-Woche, 30 Urlaubstage, iPad zum Start, Vergütung; dort
zusätzlich Trainings/Betreuung/VL). Web-Verifikation von heute passt dazu.

**Gemacht:** CTA-Wording der Endcard von „JETZT BEWERBEN" auf die
Kampagnensprache umgestellt — „JETZT IN UNTER 1 MIN. BEWERBEN" + neue
Sub-Zeile „IN KARLSRUHE – OHNE LEBENSLAUF!" (neuer Prop `ctaSub`, leer =
entfällt). Der Quick-Apply-Funnel ist durch die laufenden, MAN-freigegebenen
Ads belegt (Website-Regel erfüllt); Look bleibt bewusst Wartezimmer-Web-Look
(explizite Kundenvorgabe), NICHT der Foto-Look der Still-Ads.
Beide Renders + Still neu (gleiche Pfade; ProRes 4444 Alpha, 300 F,
verifiziert am File). Benefits-Zeilen unverändert (alle vier in den Ads
enthalten); Option: „Enge Betreuung" als 5. Zeile passt noch ins Layout.

**Offen (David):** Karlsruhe-Zeile korrekt für alle Lagervideos? (Ads sagen
Karlsruhe; falls ein Video woanders läuft: `ctaSub` anpassen/leeren.)

## 2026-08-13 — Auflösung: Kundenänderung betrifft den KRANK-CTA (MAN-LagerCTA)

**Klarstellung David (mit Screenshot):** Die Kundenmail meint den BESTEHENDEN
Lager-CTA im KRANK-Look (`MAN-LagerCTA`), nicht eine neue Endcard. Die
Web-Look-Endcard von heute Vormittag war ein Missverständnis — Renders nach
`Ergebnisse/Renders/_alt-web-look/` archiviert (Komposition `MAN-LagerCTA-Web`
bleibt im Studio verfügbar).

**Kundenänderung (nach mehreren Rückfragen komplett):**
1. Zweiter Beruf unter „Fachkraft für Lagerlogistik": **„Kaufmann/frau im
   Einzelhandel"** (Davids Zwischenantworten „Ausbildung"/„Lager" waren
   Kontext, kein Berufsname — mein Fachlagerist-Tipp war falsch und ist
   NICHT enthalten).
2. **Benefits ganz raus** (die 4 Chips entfallen).
3. **Standort raus** (kein „In Karlsruhe" — Sub-Text nur „Ohne Lebenslauf!").

**Umbau `Composition.tsx` (KRANK):** Neuer Prop `beruf2` (62 px Cond Bold,
gleicher Smash-in wie die Headline-Zeilen, „(m/w/d)"-Suffix rückt darunter und
blendet verzögert — gilt für beide Titel, m/w/d-Pflicht erfüllt); Benefits-
Schema von min 1 auf min 0, Chips-Block konditional; ohne Chips rücken
CTA-Button auf 56 % und Sub auf 64 % und kommen ~1 s früher. Suchlauf nach
Davids Hinweis „NIROremotion": Ordner enthält KEINEN MAN-Code (alte Pipeline
März–Juni) — der CTA-Code liegt seit jeher in
`tools/motion/src/clients/man/projects/lager-ausbildung-cta/` (Spec
2026-06-18, Assets in `tools/motion/Videos/Man Lagerausbildung/`; die vier
Kampagnen-Stills dort zeigen alle nur einen Beruf).

**Geliefert (`Ergebnisse/Renders/`):**
- `MAN-LagerCTA-2-Berufe-4K.mov` — ProRes 4444 Alpha, 2160×3840/30p, 10,0 s, 739 MB
- `MAN-LagerCTA-2-Berufe-Preview.mp4` — H.264 CRF 18, 1080×1920/30p, 3,5 MB
- `MAN-LagerCTA-2-Berufe-Still.png` — 4K-Standbild
Verifiziert am File: 300 F/30 fps, Frame 0 voll transparent (Iris-Intro,
über Videoende legbar), F120 Einlauf korrekt, F280 Steady komplett;
Safe-Zone eingehalten (Inhalt endet ~66 %), keine Gesichter (reine Grafik).

**Offen:** Falls die Kundenmail noch weitere Berufe/Änderungen nennt, die im
Chat nicht ankamen: Wortlaut nachreichen → Props-Wechsel + Re-Render.

## 2026-08-13 — Beide Ausbildungen visuell gleichwertig (David)

**Gemacht:** Titel-Block auf einheitliches Zeilen-Modell umgebaut: beide
Berufe in 96 px Cond Bold (vorher 118/62), JEDER Beruf mit rotem
Highlight-Sweep auf seiner Schlusszeile („LAGERLOGISTIK" / „IM EINZELHANDEL"),
dazwischen weißer „+"-Trenner (54 px — erst rot probiert, auf dem dunkelroten
Grund zwischen den zwei Balken unsichtbar), darunter EIN gemeinsames
„(M/W/D)". `beruf2` unterstützt jetzt \n-Umbruch („Kaufmann/frau\nim
Einzelhandel"); Highlight-Sweeps je Zeile eigenständig getimt, Suffix und CTA
hängen an der letzten Titel-Zeile (CTA startet ~5,2 s, hält ~4,8 s).

**Geliefert:** Alle drei Dateien ersetzt (gleiche Namen/Specs):
MAN-LagerCTA-2-Berufe-{4K.mov 744 MB, Preview.mp4, Still.png}.
Verifiziert: ProRes 4444 Alpha, 300 F, F0 transparent, F280 Steady korrekt,
Titel-Block endet ~48 % (Safe-Zone), „+" im Voll-Res-Crop klar lesbar.
