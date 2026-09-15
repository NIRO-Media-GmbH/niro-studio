# Protokoll — SW Projektentwicklung / Solar-Wissen / 2026-08 Reels

## Charge
Reels-Serie „Solar-Wissen". Erstes bearbeitetes Video: **02 — Bifaziale Solarmodule**.

## Struktur
```
Material/Transkript/02_Bifaziale_Solarmodule_V1.srt   Transkript (Input)
Material/Video/                                        Rohmaterial (noch leer)
Ergebnisse/Renders/                                    Finale Renders
_intern/review/                                        Review-Artefakte
```
Symlink für Remotion:
`tools/motion/public/projects/sw-projektentwicklung-solar-wissen` → `Material/Video`

## Kunden-CI (erfasst von sw-projektentwicklung.com)
Quelle: Computed Styles der Live-Seite, nicht aus dem Marketing-Text abgeleitet.

| Rolle | Wert |
|---|---|
| Primär | `#FF8022` (Orange) |
| Sekundär / Text | `#2E2D2C` (Anthrazit) |
| Akzent | `#FF9A4D` |
| Hintergrund | `#FFFFFF` |
| Schrift | Montserrat (Headline + Body) |
| Border-Radius | 10 px |

Logo: `tools/motion/public/clients/sw-projektentwicklung/logo-stack-white.png`
(Quelle: `Material/Logo/SW Projektentwicklung_Logo_Final-04.png`, vom Kunden geliefert,
16000×9001 mit viel weißem Rand → getrimmt auf 15285×5826 und auf Höhe 600 skaliert.
`logo-stack.png` ist die Positiv-Fassung derselben Datei, aktuell ungenutzt.)
Das frühere `logo.svg` (von der Website, quer 5,69:1) liegt weiter im Ordner,
wird in dieser Komposition aber nicht mehr verwendet.
Füllfarben beider Dateien `#ff8022` / `#2e2d2c` — bestätigt die Palette.

Hinweis: Ein WebFetch-Durchlauf meldete zusätzlich ein Blau `#4e94e8`. Bei Prüfung der
Computed Styles taucht dieses praktisch nicht auf → **nicht** in `brand.json` übernommen.

## Komposition
`tools/motion/src/clients/sw-projektentwicklung/projects/bifaziale-module/Composition.tsx`
Registriert in `Root.tsx` als `SW-BifazialeModule` (Ordner `SW-Projektentwicklung`).

- Format: Portrait 1080×1920, 30 fps, 36,0 s (1080 Frames)
- Hintergrund: `footageFile` (leer ⇒ Anthrazit-Platzhalter). Sobald O-Ton-Footage in
  `Material/Video/` liegt, Dateiname in `footageFile` eintragen.
- Alle Texte/Positionen über das Zod-Schema im Studio editierbar.

### Szenen (auf den Wortzeitstempeln des SRT)
Grundsatz: Eine Grafik setzt erst ein, **nachdem** das zugehörige Wort gefallen
ist — nicht in gleichmäßigen Blöcken. Zwischen den Szenen stehen bewusst Lücken,
in denen nur der Sprecher läuft.

| # | Sek | Auslösendes Wort (SRT) | Visual |
|---|---|---|---|
| 1 | 0–2,4 | „streiten … Solarmarkt" (0,3–2,2) | „STREIT." schlägt ein, Schockwellen-Ring |
| 2 | 3,4–6,6 | „gar nichts" (3,5) / „bringt was" (5,2) | ✕-Karte bei 3,5 s, ✓-Karte erst bei 4,87 s |
| 3 | 8,0–13,0 | „bifazial" (8,2–8,8) | „BIFAZIAL" mit Buchstaben-Bounce + Unterstrich |
| 4 | 14,0–16,4 | „von beiden Seiten" (14,4–15,2) | Modul mit Strahlen, „Sonne" ↔ „Reflexion" |
| 5 | 18,6–24,0 | „Garten stellen als Zaun" (19,8–21,5) | 4 stehende Module, Sonne wandert links→rechts |
| 6 | 25,0–31,3 | „zwischen 5 und 20 Prozent" (25,2–26,9) | Zähler 5–20 %, „Mehrertrag" |
| 7 | 32,8–36,0 | „immer bifazial" (33,3–34,0) | Pill „IMMER BIFAZIAL" + ✓ + Logo-Karte |

Durchgehend: Energie-Partikel (nur im unteren Band).

## Pre-Delivery Review (nach tools/motion/CLAUDE.md)
Durchgeführt in Remotion Studio mit `review.showGuides: true`, geprüfte Frames:
1, 3, 11, 50, 96, 173, 198, 255, 315, 435, 540, 660, 790, 990, 1040.

Gefunden und behoben:
1. **Hook, Frame 0–3:** Start-Skalierung 3,4 ließ „STREIT" über die Safe Zone hinaus
   und in die Gesichts-Zone ragen → auf 1,32 reduziert, Impact stattdessen über
   Motion-Blur (16 px → 0).
2. **Hook, Schockwellen-Ring:** expandierte bis in die Gesichts-Zone → wird jetzt
   unterhalb 0,45 · Höhe abgeschnitten (`overflow: hidden`).
3. **Wasserzeichen:** kollidierte in Szene 7 mit dem Untertitel; oben links hätte es
   in die Gesichts-Zone geragt → durch eine 3 px hohe Fortschrittslinie an der
   Safe-Zone-Unterkante ersetzt.
4. **Szene 4 (Flip):** Label „Rückseite" lag hinter dem Modul → Label auf Bühnen-
   oberkante, Modulhöhe 0,50 → 0,42, Caption 0,82 → 0,78.
5. **Szene 6 (Zaun):** Sonne überlagerte den Titel, Caption ragte aus der Safe Zone →
   Boden 0,86 → 0,80, Zaunhöhe 0,44 → 0,30, Sonne höher, Caption 0,90 → 0,82.
6. **Szene 8 (Empfehlung):** Logo-Karte ragte ~10 px unter die Safe Zone → Pill,
   Check und Logo verkleinert, Zeilen neu gestapelt.

Ergebnis: keine Elemente in der Gesichts-Zone, alle Texte in der Safe Zone.
`review.showGuides` steht wieder auf `false`.

**Vorbehalt:** Die Gesichts-Zone ist der Default (0,08–0,45 / 0,20–0,80). Sobald die
echte Footage vorliegt, muss geprüft werden, ob das Gesicht tatsächlich dort sitzt;
ggf. `review.faceZone` projektspezifisch anpassen.

## Footage eingebunden (2026-08-12, zweite Session)
`02_Bifaziale_Solarmodule_V1.mp4` lag lose in `projects/SW Projektentwicklung/`;
nach `Material/Video/` verschoben. Eigenschaften: 2160×3840, 25 fps, HEVC, 36,07 s,
34 MB. In `Root.tsx` als `footageFile` gesetzt, lädt über den bestehenden Symlink.
HEVC dekodiert im Studio problemlos.

### Gesichts-Zone verifiziert
Der Vorbehalt aus der ersten Session ist erledigt: Der Sprecher steht über alle
geprüften Frames (96, 435, 600, 820, 1010) bei ca. 0,13–0,42 der Höhe. Die
Default-Gesichts-Zone (0,08–0,45) passt, alle Grafiken liegen ab 0,455 darunter.
`review.faceZone` muss **nicht** projektspezifisch angepasst werden.

### Neuer Befund: Kontrast auf echter Footage
Die Szenen wurden gegen den Anthrazit-Platzhalter gebaut. Auf echtem Material:
- **Szene 5 + 6:** Modul- und Zaun-Grafiken sind dunkle Outlines und gehen vor
  dunkler Jacke bzw. unruhigem Kies/Dach fast unter.
- **Szene 6:** Die orange Sonne sitzt direkt auf der Headline „Modul als Gartenzaun".
- **Szene 6:** Orange Caption über hellem Kies zu kontrastarm.
- Unauffällig und gut lesbar: Szene 2 (Karten) und Szene 8 (Pill + Logo-Karte) —
  beide haben eine eigene deckende Fläche. Szene 7 (Zähler) trägt ebenfalls.

Offen: Kontrast-Pass für die Modul-/Zaun-Szenen (Scrim hinter der Bühne, gefüllte
statt umrandeter Module, Sonne versetzen). Noch nicht umgesetzt.

## Timing- und Layout-Korrektur (Kundenfeedback, 2026-08-12)
Rückmeldung: Grafiken kommen durchweg zu früh und laufen dem Sprecher davon.
Konsequenz — alle Einsätze neu auf die SRT-Wortzeitstempel gelegt (Tabelle oben):

1. **Szene 2 zu schnell / nicht am O-Ton.** Beide Karten kamen fast gleichzeitig
   (Frame 2 und 16) direkt bei 2,4 s. Jetzt startet die Szene bei 3,4 s, die
   ✕-Karte bei 3,5 s („gar nichts") und die ✓-Karte bei 4,87 s („bringt was") —
   1,37 s Abstand, dadurch liest sich die Gegenüberstellung als Dialog.
2. **„BIFAZIAL" zu früh.** Lief ab 5,9 s, das Wort fällt aber erst bei 8,2 s.
   Jetzt 8,0–13,0 s, also 5,0 statt 3,3 s Standzeit.
3. **Flip-Szene („Vorder-/Rückseite") komplett entfernt** — Komponente,
   Zod-Schema und Sequence. Die frei gewordene Zeit geht an Szene 3.
4. **Fortschrittslinie entfernt** (lenkte ab, `BrandProgress` gelöscht).
5. **Logo in der Endkarte von 0,30 auf 0,47 Bildbreite** (+57 %), damit die
   Wortmarke auf dem Handy lesbar ist. Pill und Unterzeile dafür gestrafft und
   der Stapel neu gesetzt. Die Karte wird jetzt von **oben** eingeblendet — der
   frühere Versatz nach unten schob sie beim Eintritt unter die Safe-Zone-Kante.
6. Gesamtlänge 35,5 → 36,0 s, damit die Endkarte ausreichend steht
   (Footage ist 36,07 s lang).

Geprüfte Frames nach der Änderung: 118, 158, 262, 600, 1012, 1040 —
Guides wieder auf `false`, `tsc --noEmit` sauber.

## Logo-Tausch (Kundenfeedback, 2026-08-12)
Kunde hat die offizielle Logodatei nach `Material/Logo/` gelegt. Sie ist die
**gestapelte** Variante (Icon über Wortmarke), Seitenverhältnis **2,62:1** —
das bisherige Website-SVG war quer mit **5,69:1**.

**Warum das die Endkarte verändert hat:** Die Wortmarke macht im gestapelten Logo
nur 12,9 % der Gesamthöhe aus (quer: 24,4 %). Für dieselbe Schriftgröße braucht
die Datei also rund die doppelte Logohöhe. Zwischen Gesichts-Zone (endet bei
0,45 · H = 864 px) und Safe-Zone-Unterkante (0,575 · H = 1104 px) liegen aber nur
240 px. Pill + Unterzeile + lesbares Logo passen dort nicht gleichzeitig hinein —
gemessen wären es 14 px Versalhöhe gewesen, gegenüber 22 px vorher, also
schlechter als der ursprünglich bemängelte Zustand.

**Lösung:** Endkarte in zwei Phasen statt Elemente zu streichen.
- Frame 0–44: Pill „IMMER BIFAZIAL" + Unterzeile wie bisher.
- Frame 44–52: beide blenden aus.
- Ab Frame 52: Logo-Lockup allein, mittig auf der Bühne, Logohöhe 0,80 · Bühne
  ≈ 184 px → Versalhöhe der Wortmarke **≈ 24 px** (vorher 22 px) und ein rund
  100 px hohes Icon statt vorher ~40 px.

Damit bleiben alle Texte erhalten, das Logo steht die letzten ~1,5 s allein.
Innenabstand der weißen Karte: 0,065 · Bühnenhöhe vertikal, 0,03 · Breite
horizontal. Größe wird über die **Höhe** gesetzt, nicht über die Breite —
davon hängt die Lesbarkeit der Wortmarke ab.

Geprüft an Frames 1018 (Pill-Phase), 1042 und 1070 (Lockup) sowie 1075 mit
Guides: Karte vollständig in der Safe Zone, unterhalb der Gesichts-Zone.

### Nachtrag: weiße Karte entfernt, Logo freigestellt
Auf Kundenwunsch steht das Logo jetzt ohne weiße Fläche direkt auf der Footage.

**Asset:** `logo-stack-white.png` — Negativ-Version, erzeugt aus der Kundendatei:
Deckkraft aus dem invertierten Minimum der RGB-Kanäle, Wortmarke und Dach auf
Weiß gesetzt, Sonnen-Icon über eine Sättigungsmaske (Schwellwert 35 %) auf
`#FF8022` gehalten. Nur ~4,2 % der Pixel sind orange — die Maske trennt also
sauber zwischen Icon und Typo.

**Schlagschatten ist Pflicht, keine Deko.** Die Endkarte liegt teils vor hellem
Himmel; dort hätte weiße Schrift ohne Abdunklung zu wenig Kontrast. Gesetzt sind
zwei `drop-shadow` (0/2/3 px bei 55 % und ein weicher 14-px-Schein bei 50 %).
Der bestehende 15-%-Abdunkler über der Footage hilft zusätzlich.

Gegenprobe in echter Auflösung (Frame per ffmpeg extrahiert, Logo mit exakt
184 px Höhe einkopiert): Wortmarke bleibt auf dunkler Jacke wie auf Himmel
lesbar. Prüf-Frames 1042 und 1076 (Exit-Fade).

### Nachtrag: Überblendung Pill → Logo entkoppelt (2026-08-12)
Die Pill blendete bis Frame 54 aus, das Logo setzte aber schon bei 50 ein.
In den vier Überlappungs-Frames schaute ihr orangefarbener Rand hinter dem Logo
hervor und wirkte wie ein Rendering-Fehler. Beide Phasen sind jetzt strikt
getrennt: `HANDOVER = 44`, Text-Fade 8 Frames, Logo-Spring startet exakt bei
`HANDOVER + TEXT_FADE` (Frame 52). Der Logo-Einsatz ist an die Fade-Dauer
gekoppelt, nicht mehr als eigene Zahl gepflegt — sonst driftet das wieder
auseinander. Prüf-Frames 1034 / 1036 / 1039.

### Nachtrag: Pill hart abgeschaltet statt ausgeblendet (2026-08-12)
Kundenrückmeldung mit Screenshot: Die Pill war hinter dem Logo weiterhin schwach
sichtbar. Ursache war ein Denkfehler auf meiner Seite — die Entkopplung oben
regelte nur den *Zeitpunkt*, die Pill blieb aber als Element mit Rest-Alpha im
Baum stehen und lag unter dem teiltransparenten Logo-PNG. Opazität 0 ist bei
großen Farbflächen nicht dasselbe wie „nicht vorhanden".

Konsequenz: harte Umschaltung. `SWITCH = HANDOVER + TEXT_FADE` (Frame 52);
Pill und Unterzeile werden ab da nicht mehr gerendert (`showText`), das Logo
erst ab da (`showLogo`). Beide Zustände schließen sich gegenseitig aus, eine
Überlappung ist damit strukturell unmöglich statt nur zeitlich unwahrscheinlich.

**Merksatz für künftige Übergaben:** wenn zwei Elemente an derselben Stelle
liegen, aus- und einblenden **nicht** über Opazität lösen, sondern unmounten.

Logo zugleich von `stage.height * 0.8` auf `* 0.9` vergrößert (184 → 207 px,
Versalhöhe der Wortmarke ~24 → ~27 px), damit „SW PROJEKTENTWICKLUNG" auf dem
Handy sicher lesbar bleibt.

Pre-Delivery Review mit Guides (Frame 1044): Logo liegt von 885 px bis 1092 px.
Gesichts-Zone endet bei 864 px, Safe-Zone-Unterkante bei 1104 px → 21 px Luft
oben, 12 px unten. Die Einblend-Feder (SMOOTH, Dämpfungsgrad 0,64) überschwingt
auf Skalierung 1,007, das sind rund 1 px — bleibt innerhalb. Danach Guides
wieder auf `REVIEW_DEFAULTS` zurückgesetzt und Frames 1034 / 1036 / 1044 ohne
Guides gegengeprüft: keine Pill mehr sichtbar.

### Nachtrag: schwarzer Frame am Ende entfernt (2026-08-12)
Beim Prüfen des letzten Frames fiel auf, dass Frame 1079 komplett schwarz war.
Der Videostream ist exakt 36,000 s lang (900 Frames bei 25 fps), die Komposition
lief mit `Math.ceil(36,0 × 30)` = 1080 Frames bis 35,967 s — auf dem letzten
Compositing-Frame hatte `OffthreadVideo` kein Quellbild mehr. Kompositionsdauer
auf **35,96 s** (1079 Frames) gekürzt; damit ist der schwarze Blitz weg und der
Ton verliert nur 33 ms Nachlauf. Frame 1078 gegengeprüft: Footage vorhanden.

## Overlay-Export (2026-08-12)
Geliefert: `Ergebnisse/Renders/02_Bifaziale_Solarmodule_Overlay_ProRes4444.mov`

Nur die Animationsebene, ohne Hintergrundvideo — das diente lediglich dazu,
Lesbarkeit und Gesichtsfreiheit gegen echtes Material zu prüfen. Über den
Schalter `transparent: true` entfallen Footage, der 15-%-Abdunkler und der
Verlaufshintergrund; alles andere bleibt unverändert.

| | |
|---|---|
| Codec | ProRes 4444, `yuva444p12le` (Alpha erhalten) |
| Auflösung | 1080 × 1920, 30 fps |
| Länge | 35,967 s / 1079 Frames |
| Größe | 292 MB |

Der Alphakanal wurde nicht nur am Containerformat abgelesen, sondern an neun
Zeitpunkten (0,5 / 1 / 4 / 9,5 / 15 / 20,5 / 27 / 34 / 35,5 s) gemessen: die
mittlere Deckkraft liegt je nach Szene zwischen 0,9 % und 3,9 %, der Hintergrund
ist also durchgehend leer und nur die Grafik trägt Deckung.

Zwei Dinge, die für die Weiterverarbeitung wichtig sind:
- Die Komposition nutzt **keine** `mixBlendMode`- oder `backdropFilter`-Effekte.
  Das Overlay ist damit selbsttragend und rechnet im Schnittprogramm identisch,
  egal was darunter liegt — sonst hätte es zwingend mit der Footage gerendert
  werden müssen.
- Die Schlagschatten am weißen Logo bleiben drin. Sie sind kein Dekor, sondern
  der Kontrastgeber gegen den hellen Himmel im Originalclip.

Overlay bei Frame 0 auf den Clip legen, dann liegt alles lippensynchron. Es ist
einen Frame kürzer als das Video (siehe Nachtrag zum schwarzen Schlussframe).

### Render war blockiert — Ursache behoben
`remotion render` scheiterte bislang daran, dass Remotions eigener Chrome Headless
Shell sich nicht entpacken lässt (nur `ABOUT` und eine abgeschnittene Lizenz landen
im Zielordner, und jeder Aufruf lädt neu herunter, sodass manuelles Entpacken nicht
hält). Statt den Download zu reparieren, zeigt `tools/motion/remotion.config.ts` jetzt
per `Config.setBrowserExecutable()` auf das installierte Google Chrome (151.0.7922.76),
abgesichert mit `existsSync`, damit die Konfiguration auf Rechnern ohne Chrome weiter
den Standardweg nimmt. `remotion still` und `remotion render` laufen seitdem ohne
zusätzliche Flags durch.

## Video 01 — Projekt Gottwollshausen (2026-08-14)
Eigene Komposition `SW-Gottwollshausen`, Datei
`tools/motion/src/clients/sw-projektentwicklung/projects/gottwollshausen/Composition.tsx`.
Video 02 wurde dafür nicht angefasst — gleicher Stil, gleiche CI, gleiche
Bausteine, aber getrennte Datei und getrennte Vorschau.

**Ein wichtiger Unterschied zur Bifazial-Folge:** dieses Transkript liefert nur
**Segment-Timecodes**, kein Wort-SRT. Innerhalb eines Segments ist die genaue
Wortposition also unbekannt. Deshalb sitzt jede Grafik bewusst 0,3–0,6 s **nach**
dem Segmentbeginn — zu früh eingeblendet nähme sie dem Sprecher die Pointe vorweg,
und genau das war beim ersten Video die Hauptkritik. Nullpunkt des Transkripts ist
`00:59:59:24` bei 25 fps; das letzte gesprochene Wort fällt bei 53,4 s.

| Szene | Start | Dauer | Inhalt |
|---|---|---|---|
| Hook | 1,8 s | 3,6 s | „GEDROSSELT" / auch dein Eigenverbrauch |
| Projekt | 6,2 s | 4,0 s | Bauvorhaben Gottwollshausen |
| Anlage | 10,9 s | 2,9 s | 460 Wp pro Modul |
| Speicher | 14,2 s | 2,8 s | 18 kWh Stromspeicher |
| Ertrag | 18,9 s | 3,3 s | 24.000 kWh pro Jahr (Zähler) |
| Grenze | 22,9 s | 2,6 s | 25 kWp — bewusst darunter geplant |
| Folgen | 25,6 s | 15,9 s | drei Konsequenzen ab 25 kWp |
| CTA-Frage | 41,8 s | 4,4 s | „Frisst dir die Stromrechnung die Haare vom Kopf?" |
| Endkarte | 46,8 s | 6,7 s | Analyse → Autarkie-Pill → Logo |

Die Folgen-Szene liegt nicht gleichmäßig verteilt, sondern auf den Sprechzeiten:
Rundsteuergerät 25,7 s, Drosselung 31,9 s, Montagekosten 39,8 s. Ein erster
Entwurf setzte sie 2,6 s zu spät an; das wurde gegen die Segment-Timecodes
gegengeprüft und korrigiert.

**Warum die drei Folgen nacheinander statt gestapelt erscheinen:** Eine Karte ist
mit Text, Unterzeile und Innenabstand rund 74 px hoch. Zwischen Gesichts-Zone
(864 px) und Safe-Zone-Unterkante (1104 px) liegen nur 240 px, davon gehen ~40 px
für die Überschrift ab. Drei gestapelte Karten überlappten sich und die dritte
lief unten aus der Safe Zone heraus. Jetzt ist immer genau eine Karte sichtbar,
die beim Wechsel neu einfedert.

Aus demselben Grund wanderte der Balken der Grenze-Szene von 0,42 auf 0,52 der
Bühnenhöhe — die Beschriftung „25 kWp" kollidierte sonst mit der Überschrift. Die
Bildunterschrift wurde von „25 kWp" auf „Anlagenleistung im Projekt" geändert,
weil Titel, Label und Unterzeile sonst dreimal dasselbe sagten.

Die Endkarte übernimmt das harte Umschalten aus Video 02: Text wird **entfernt**,
nicht ausgeblendet, bevor das Logo kommt. Bei Frame 1562 (Umschaltpunkt) ist die
Bühne messbar komplett leer — es kann also keine Pill durch das Logo-PNG
durchscheinen.

### Pre-Delivery Review
Alle Szenenanfänge, -mitten und -übergänge als Einzelbilder gerendert und die
Grafik-Bounding-Box gemessen (Alpha extrahiert, Schwelle 45 %, Partikel per
Morphologie weggefiltert). Ergebnis: oberste Kante **884 px** (Gesichts-Zone endet
bei 864), unterste **1088 px** (Safe Zone endet bei 1104), horizontal 100–978 px
(Safe Zone 54–1026). Der Logo-Federweg wurde beim Überschwingpeak (Frame 1573)
separat nachgemessen: 884–1059 px, ebenfalls innerhalb. Guides sind in den
Standard-Props aus. `npx tsc --noEmit` läuft sauber durch.

### Offene Punkte Video 01
- **Modulanzahl fehlt.** Der Sprecher sagt „wo wir insgesamt … Solarmodule
  installieren" — die Zahl ist im Transkript nicht mitgeschrieben. Der Prop
  `anlage.moduleCount` ist deshalb bewusst **leer**; der Block wird erst
  gerendert, wenn der Wert gesetzt ist. Geraten wurde nichts.
- **Preis unvollständig.** „Kostet pauschal je nach Netzbetreiber irgendwas
  zwischen 600 Euro" — der zweite Wert fehlt. In der Grafik steht deshalb
  „pauschal ab ca. 600 €".
- **Transkriptionsfehler der Spracherkennung**, die sinngemäß korrigiert wurden:
  Rieschwaldgerät → Rundsteuer-Empfänger, Stromspeichel → Stromspeicher,
  Bauverhaben → Bauvorhaben, Bevoranlage → PV-Anlage, Autarkigrad → Autarkiegrad.
- **Schreibweise geklärt (2026-08-17).** Der Ort heißt **Gottwollshausen**.
  Komposition, Ordner und Grafik wurden umbenannt; die vom Kunden gelieferten
  Material- und Transkriptdateien tragen weiter die alte Schreibweise mit „f"
  und wurden bewusst nicht umbenannt.

## Footage eingebunden (2026-08-17)
`01_Projekt-Gottwolfshausen_V1.mp4` liegt jetzt als Hintergrund unter der
Komposition. Der Clip ist 2160 × 3840 bei 25 fps und 53,56 s lang (1339 Frames).

**Länge:** 53,56 s × 30 fps sind 1606,8 Frames. Aufgerundet ragte der letzte
Frame über das Videoende hinaus und wäre schwarz — derselbe Fehler wie bei
Video 02. Die Komposition steht deshalb auf **53,53 s** = 1606 Frames; der
letzte liegt bei 53,50 s und hat noch Bild (gegengeprüft). Die Endkarte wurde
von 7,7 s auf 6,7 s gekürzt, damit sie hineinpasst.

**Endkarten-Umbau — Gesichtsabdeckung in der Beratungsszene.** Der Clip hat
dreizehn Schnitte; bei 46,52–48,92 s liegt B-Roll vom Beratungsgespräch am
Tisch. Dort sitzen drei Gesichter deutlich tiefer im Bild als beim Dachsprecher
und reichen bis rund 911 px herunter. Die Zeile „Komplette Analyse — kostenlos"
saß auf 910 px und lag damit rund zwei Sekunden lang direkt auf Mund und Kinn
von zwei Personen. Weil zwischen Gesichts-Zone und Safe-Zone-Unterkante nur
240 px liegen, ließ sich das nicht durch ein leichtes Verschieben lösen:
Zeile und Pill wurden getauscht. Die Pill steht jetzt oben (Bühnenanteil 0,32,
Mitte 947 px), die Analyse-Zeile darunter (0,78, 1053 px) und damit unter allen
Gesichtern. Nebeneffekt: Pill als Schlagzeile über der Unterzeile liest sich
besser als vorher.

Auch der Umschaltpunkt der Endkarte wurde angepasst — 138 statt 150 Frames,
sonst wäre das Logo in der verkürzten Szene nur noch gut eine Sekunde stehen
geblieben.

**Zweite Review-Runde gegen das echte Material.** Diesmal wurde nicht nur der
Hauptsprecher geprüft: Die Schnittgrenzen wurden per Szenenerkennung ermittelt
(5,9 / 8,4 / 10,6 / 12,7 / 14,0 / 17,2 / 19,0 / 31,6 / 38,9 / 41,5 / 46,5 /
48,9 s) und aus jedem Shot ein Frame mit eingeblendeter Grafik kontrolliert.
Außer der Beratungsszene liegt kein Gesicht im Grafikband. Der letzte Frame
zeigt Bild, kein Schwarz.

## Kundenfeedback Video 01 (2026-08-17)
Fünf Punkte, alle umgesetzt:

1. **„GEDROSSELT" kam zu spät** — Hook von 1,8 s auf 1,3 s vorgezogen.
2. **Ertragszeile gekürzt** — „24.000 kWh / pro Jahr" reicht, die Erklärzeile
   „prognostizierter Ertrag der Anlage" ist raus. Der Prop bleibt bestehen, ist
   aber leer; leere Werte werden nicht mehr gerendert.
3. **Grenze-Szene auf 36 Frames (1,2 s)** gekürzt und die Bildunterschrift
   entfernt. Das machte einen Umbau der Szenen-Animation nötig: Der Balken füllte
   sich mit `damping 20 / stiffness 55` ab Frame 6 so langsam, dass die Szene noch
   mitten in der Animation war, als die Ausblende schon lief — lesbar war fast
   nichts. Jetzt steht alles ab Frame 12, hält bis 31 und blendet in 5 statt
   8 Frames aus.
4. **„kostenlos" gestrichen** — unklar, ob die Analyse tatsächlich kostenlos ist.
   Steht jetzt nur noch „Komplette Analyse".
5. **Endkarte neu aufgeteilt.** Die Autarkie-Pill stand 1,6 s und war nicht zu
   lesen, das Logo dagegen länger als nötig. Umschaltpunkt von Frame 138 auf 158,
   Pill-Einsatz von 104 auf 88. Jetzt: Pill 2,6 s, Logo 1,2 s. Die Pill startet
   damit rund eine halbe Sekunde vor dem Wort „Autarkiegrad" — eine bewusste
   Ausnahme von der Regel „nie vor dem Sprecher", weil sie die Kernaussage des
   Videos trägt und Lesezeit braucht.

**Eine Rückfrage:** Zur Grenze-Szene hieß es, sie sei „ab dem 36. Frame fertig,
da danach der nächste Shot kommt". Die Kürzung auf 36 Frames ist umgesetzt — im
Material liegt an dieser Stelle aber kein Schnitt: Der Shot läuft durchgehend von
22,0 s bis 31,6 s (per Szenenerkennung und Einzelbildern geprüft). Falls mit
„nächster Shot" etwas anderes gemeint war, ist die Länge eine Zahl im Prop.

## Overlay-Export Video 01 (2026-08-17)
Geliefert: `Ergebnisse/Renders/01_Projekt-Gottwollshausen_Overlay_ProRes4444.mov`

| | |
|---|---|
| Codec | ProRes 4444, `yuva444p12le` (Alpha erhalten) |
| Auflösung | 1080 × 1920, 30 fps |
| Länge | 53,533 s / 1606 Frames |
| Größe | 432 MB |

Nur die Animationsebene; das Hintergrundvideo diente ausschließlich der Prüfung
von Lesbarkeit und Gesichtsfreiheit. Alpha an zwölf Zeitpunkten gemessen: mittlere
Deckkraft 0,6–3,1 %, der Hintergrund ist also durchgehend leer. Guides sind nicht
mitgerendert. Wie bei Video 02 nutzt die Komposition keine Blend-Modi, das Overlay
ist damit selbsttragend. Bei Frame 0 auf den Clip legen; es ist einen Frame kürzer
als das Video.

## Zweites Kundenfeedback Video 01 (2026-08-18)
1. **Hook wortgleich zum O-Ton.** Statt „GEDROSSELT." steht jetzt der gesprochene
   Satz „Der Netzbetreiber kann deine Anlage drosseln!". Die Unterzeile „auch dein
   Eigenverbrauch" ist ersatzlos raus — gewünscht war nur dieser eine Text.

   Der Umbau war nötig, weil sich ein ganzer Satz nicht wie ein Einzelwort
   einschlagen lässt: Bei der alten Schriftgröße (100 px) wäre er weit über die
   Safe Zone hinausgelaufen. Jetzt zwei Zeilen à 64 px, Zeile 1 weiß, Zeile 2
   orange, versetzt einschlagend (Zeile 2 sechs Frames später). Der
   Schockwellenring geht unter Zeile 2 auf, der Wackler hängt am zweiten
   Einschlag statt am Szenenstart. Dauer von 3,6 s auf 4,0 s, weil mehr Text
   auch mehr Lesezeit braucht; der Satz wird im O-Ton bis 5,6 s gesprochen,
   die Szene endet bei 5,3 s.
2. **„460 Wp" → „460 Watt"** auf Wunsch der Geschäftsführung.

Zonen neu gemessen, inklusive Einschlag- und Wackel-Spitzen: oberste Kante
908 px, unterste 1066 px, horizontal 97–975 px. Alles innerhalb.

## Nachtrag Video 02 (2026-08-18)
Der Füllbalken zwischen „5–20 %" und „MEHRERTRAG" ist entfernt. Er saß auf
993 px, die Zahl reichte bis rund 1000 px herunter — dadurch wirkte er wie eine
Unterstreichung der Zahl statt wie ein Trenner. Statt ihn zu zentrieren, ist er
ganz raus: Er zeigte nur dasselbe wie der Zähler, der ohnehin von 5 auf 20
hochläuft. Übrige Szene unverändert, Zonen nachgemessen (873–1092 px).
Overlay neu exportiert, 292 MB, sonst identische Spezifikation.

## Video 04 — Flachdach-Erklärung (2026-08-18)
Eigene Komposition `SW-Flachdach`, Datei
`tools/motion/src/clients/sw-projektentwicklung/projects/flachdach/Composition.tsx`.
Videos 01 und 02 wurden nicht angefasst — gleicher Stil, gleiche CI, gleiche
Bausteine, getrennte Datei und getrennte Vorschau.

**Erstmals ein Wort-SRT.** `04_Flachdach-Erklaerung_V1.srt` liefert 231 Cues auf
Wortebene (01:00:00,079 – 01:01:18,639). Anders als bei Video 01 muss also nicht
geschätzt werden, wo im Segment ein Stichwort fällt — jede Grafik hängt am
exakten Wortende plus 0,1–0,6 s Nachlauf.

| Szene | Start | Dauer | Auslösendes Wort (Wortende) | Inhalt |
|---|---|---|---|---|
| Dichtigkeit | 1,9 s | 5,2 s | „Dichtigkeitsproblem" 1,72 | Kein Dichtigkeitsproblem |
| Ost-West | 11,9 s | 5,6 s | „Aufständerung" 11,80 | Zelt-Form, OST / WEST |
| Winkel | 20,4 s | 3,2 s | „aufgewinkelt" 20,28 | 10° |
| Schiene | 25,6 s | 3,6 s | „Schiene gespannt" 25,44 | Schiene + Ballaststeine |
| Durchstoßen | 29,7 s | 2,4 s | „durchstoßen" 30,84 | Keine Dachdurchdringung |
| Unterkonstruktion | 32,9 s | 5,0 s | „Unterkonstruktion" 32,76 | Modul wird aufgelegt |
| Klemmen | 39,9 s | 6,4 s | „Mittelklemme" 39,76 / „Endklemme" 44,16 | zwei Karten nacheinander |
| Fertig | 47,6 s | 4,6 s | „verkabelt" 47,48 | Anlage fertig |
| Süd | 54,2 s | 5,6 s | „Südaufständerung" 54,08 | eine Reihe, nach Süden |
| Unterschied | 61,4 s | 4,4 s | „Angriffsfläche" 64,60 | Wind fährt unter das Modul |
| Windfangblech | 67,6 s | 4,2 s | „Windfangblech" 67,48 | Blech schließt die Rückseite |
| Endkarte | 76,3 s | 4,5 s | „relativ simpel" 77,00 | Fazit → Pill → Logo |

Keine Szene überlappt; zwischen den Blöcken läuft nur der Sprecher.

**Eine gemeinsame Geometrie für drei Szenen.** Unterkonstruktion, Angriffsfläche
und Windfangblech zeigen dasselbe Gestell aus verschiedenen Blickwinkeln der
Erklärung. Es steckt deshalb in einer Komponente (`TiltRig`), deren Maße
gerechnet statt geschätzt sind: `panelW = span / cos(Neigung)`,
`rise = panelW · sin(Neigung)`, hintere Stütze = vordere + rise. Nur so landen
beide Modulenden exakt auf den Stützenköpfen. Einheitliche Ausrichtung im
gesamten Video: **hohe Stütze links, Modulfläche nach rechts**, der SÜD-Pfeil
zeigt in dieselbe Richtung. Ohne diese Festlegung hätten die Süd-Szene und die
beiden Wind-Szenen einander widersprochen.

Windrichtung ist die Pointe der beiden letzten Szenen: In „Der einzige
Unterschied" laufen die Pfeile von links **durch** den offenen Spalt — das ist
die Angriffsfläche. In „Windfangblech" endet derselbe Weg vor dem orangen Blech,
das genau bis zur Höhe der hinteren Stütze wächst.

### Pre-Delivery Review
Komplette Sequenz transparent gerendert (2424 PNGs, halbe Auflösung) und für
jeden Frame mit Inhalt die Bounding-Box der Grafik gemessen (Alpha extrahiert,
Schwelle 45 %, Partikel per Morphologie weggefiltert). 1540 Frames tragen Grafik.
Ergebnis in voller Auflösung: oberste Kante **884 px** (Gesichts-Zone endet bei
864), unterste **1098 px** (Safe Zone endet bei 1104), horizontal 64–1016 px
(Safe Zone 54–1026). **Null Verstöße.**

Zwei Befunde davor, beide behoben:
1. **Endkarten-Pill 2 px über der rechten Safe-Zone-Kante** (1028 statt 1026) →
   horizontaler Innenabstand von 0,045 auf 0,038 der Breite.
2. **Fünf Bildunterschriften saßen exakt auf 1104 px**, also millimetergenau auf
   der Unterkante ohne jeden Puffer → von 0,90 auf 0,87 der Bühnenhöhe.

**Wichtiger als die Zahlen: die Zahlen allein reichen nicht.** Drei Fehler haben
den Bounding-Box-Test anstandslos bestanden und wären trotzdem ausgeliefert
worden. Gefunden erst durch vergrößerte Ausschnitte des Grafikbands:
- Die Dachkante war ein Verlauf von `#6E6A65` nach `#4C4945` und vor dunklem
  Hintergrund praktisch unsichtbar. Ohne sichtbares Dach verpufft aber genau die
  Aussage „es liegt nur drauf, nichts geht hindurch". Jetzt mit hellem Oberrand.
- In der Unterkonstruktions-Szene lagen zwei gleich hohe Stützen vollständig
  hinter dem Modul — die Unterkonstruktion war unter ihrer eigenen Überschrift
  unsichtbar. Ersetzt durch die gerechnete Geometrie mit unterschiedlich hohen
  Stützen.
- Der SÜD-Pfeil war ein nach unten zeigendes Dreieck über dem Label und las sich
  als Kartenmarkierung, nicht als Himmelsrichtung. Jetzt Balken plus Spitze nach
  rechts.

Seitdem Sichtprüfung an den Szenen 6, 9, 10, 11 in 3-facher Vergrößerung sowie
in der Vorschau (Frame 2076). `npx tsc --noEmit` sauber, Guides in den
Standard-Props aus.

## Video 04 — Footage, Timing-Feedback und Export (2026-08-19)

**Footage eingebunden.** `04_Flachdach-Erklaerung_V1.mp4`, 2160 × 3840, 25 fps,
79,509 s. Komposition steht auf **79,47 s** (2385 Frames) — der letzte liegt bei
79,467 s und hat noch Bild. Der Vorbehalt „Gesichts-Zone unverifiziert" ist damit
erledigt: der Sprecher steht in allen geprüften Shots deutlich über dem
Grafikband.

**Timing-Feedback des Kunden — alles eine Richtung: zu spät.** Elf von zwölf
Szenen mussten nach vorn. Das Muster ist dasselbe wie bei Video 01, aber die
Ursache eine andere: Nicht die Szenenstarts saßen falsch (die hingen ja am
Wort-SRT), sondern der Nachlauf war zu großzügig bemessen. Wo ich 0,5–0,6 s
Sicherheitsabstand hinter das Stichwort gelegt hatte, empfindet der Kunde bereits
0,1–0,2 s als richtig. **Merksatz: das Wort muss angefangen haben, nicht zu Ende
gesprochen sein.**

| Szene | alt → neu | Anmerkung |
|---|---|---|
| Dichtigkeit | 1,9 → **0,9 s** | setzt jetzt mit dem Wort ein, Dauer 5,2 → 6,2 s |
| Ost-West | 11,9 → **10,9 s** | endet 1 s früher (16,5 s), damit der Sprecher nicht in die Grafik läuft |
| 10 Grad | 20,4 → **18,8 s** | Unterzeile von 19,5 auf 20,4 s (nach „aufgewinkelt") |
| Schiene | unverändert | vom Kunden bestätigt |
| Durchstoßen | 29,7 → **29,2 s** | schließt bündig an die Schiene an |
| Unterkonstruktion | 32,9 → **32,4 s** | „Module werden aufgelegt" 36,4 → 34,6 s (−1,8 s) |
| Klemmen | 39,9 → **39,3 s** | Endklemme 44,3 → 43,8 s |
| Verkabeln | 47,6 → **46,9 s** | „ANLAGE FERTIG" bleibt bei 48,5 s (bestätigt) |
| Süd | 54,2 → **53,6 s** | „eine Reihe" bleibt bei 57,2 s (bestätigt) |
| Unterschied | 61,4 → **60,9 s** | „Angriffsfläche" bleibt bei 64,7 s (bestätigt) |
| Windfangblech | unverändert | |

Bemerkenswert: Die **Unterzeilen** wurden fast durchweg bestätigt, nur die
Überschriften kamen zu spät. Beim Vorziehen einer Szene mussten die internen
Offsets also gegenläufig erhöht werden, damit die Unterzeile absolut stehen
bleibt. Wer hier nur `startSec` verschiebt, zieht die Unterzeile mit und macht
den bestätigten Teil kaputt.

Die Durchstoßen-Szene wanderte zusätzlich von 0,44 auf 0,58 der Bühnenhöhe
(rund 32 px tiefer) — im folgenden B-Roll stehen Arbeiter höher im Bild als der
Hauptsprecher.

### Endkarte komplett umgebaut
Das bisherige Muster aus Video 01/02 — erst Text, dann Logo — ist hier
**mathematisch nicht möglich**. Die Endkarte hat ab 76,3 s nur 95 Frames; jede
Staffel-Phase bekäme unter einer Sekunde. Genau das war die Rückmeldung: „relativ
simpel und Fragen sieht man fast gar nicht".

Jetzt stehen **Logo und Pill gemeinsam 2,4 s**, Logo oben, Pill darunter.
Drei Konsequenzen:
1. **„Relativ simpel" ist entfallen.** Drei Elemente passen nicht in die 240 px
   zwischen Gesichts-Zone und Safe Zone. Der Prop `fazitText` existiert weiter
   und ist leer — ein Wort hineinschreiben und die Zeile ist zurück.
2. **Das doppelte Fragezeichen ist raus.** In der Pill stand ein dekoratives „?"
   vor dem Text „FRAGEN? GERNE MELDEN".
3. **Das Logo ragt bewusst über die Bühnenoberkante hinaus** — rund 55 px in den
   unteren Rand der Default-Gesichts-Zone, Oberkante bei 830 px statt 864.
   Das ist eine dokumentierte Ausnahme, keine Nachlässigkeit: In diesem Clip
   endet der Sprecher bei ca. 680 px. Ohne die Ausnahme klebte das Logo an der
   Pill (8 px Abstand), und größer ging es im regulären Band nicht.
   (Nachgemessen im Vollsequenz-Review: die Logo-Oberkante liegt bei **790 px**,
   nicht bei den zuvor gerechneten 830 — der Abstand zum Sprecher bleibt
   trotzdem über 100 px.) Die
   Begründung steht im Code direkt am `top`-Wert, damit sie beim nächsten
   Review nicht als Fehler zurückgebaut wird.
   Logo 173 px hoch (Wortmarke ~22 px Versalhöhe), Pill-Schrift 0,021 → 0,0225.

Zonen nachgemessen: Durchstoßen 968–1046 px, Endkarten-Block 790–1100 px
(Logo 830–985, Pill 1033–1089), horizontal 178–902 px.

## Overlay-Export Video 04 (2026-08-19)
Geliefert: `Ergebnisse/Renders/04_Flachdach-Erklaerung_Overlay_ProRes4444.mov`

| | |
|---|---|
| Codec | ProRes 4444, `yuva444p12le` (Alpha erhalten) |
| Auflösung | 1080 × 1920, 30 fps |
| Länge | 79,50 s / 2385 Frames |
| Größe | 515 MB |

Alpha an sechs Zeitpunkten gemessen (3 / 15 / 30 / 45 / 63 / 78,5 s): mittlere
Deckkraft 1,2–3,4 %, der Hintergrund ist durchgehend leer. Keine Blend-Modi, das
Overlay ist selbsttragend. Bei Frame 0 auf den Clip legen.

**Render-Flags, die beim ersten Versuch gescheitert sind:** `yuva444p12le` ist
kein gültiger Eingabewert (ffprobe meldet ihn zwar so am fertigen File, gesetzt
wird aber `yuva444p10le`), und ohne `--image-format=png` bricht der Transparenz-
Render ab. Vollständig:
`--props='{"transparent":true}' --codec=prores --prores-profile=4444
--pixel-format=yuva444p10le --image-format=png`

## Video 03 — Bauer Solar Modul (2026-08-20)
Eigene Komposition `SW-BauerSolar`, Datei
`tools/motion/src/clients/sw-projektentwicklung/projects/bauer-solar/Composition.tsx`.
Videos 01, 02 und 04 wurden nicht angefasst.

**Schreibweise des Herstellers: „Bauer Solar".** Die gelieferte Videodatei heißt
`03_BauSolar-Modul_V1.mp4` — das ist falsch, „BauSolar" gibt es nicht. Die Datei
wurde bewusst **nicht** umbenannt (Kundenmaterial bleibt wie geliefert, wie schon
bei Gottwolfshausen/Gottwollshausen); im Bild und im Transkriptnamen steht
ausschließlich die korrekte Fassung. Im Wort-SRT ist der Name richtig
geschrieben, nur der Dateiname weicht ab.

**Footage:** 2160 × 3840, 25 fps, HEVC, 56,043 s. Komposition **56,0 s**
(1680 Frames) — der letzte liegt bei 55,967 s und hat noch Bild.
Wort-SRT mit 149 Cues, letztes Wort bei 55,96 s.

**Timing nach der neuen Regel.** Die Rückmeldung zu Video 04 („alles zu spät")
ist hier von Anfang an eingearbeitet: Jede Szene startet **0,05–0,15 s hinter
dem Wortanfang** ihres Stichworts, nicht hinter dem Wortende.

| # | Szene | Start | Dauer | Stichwort (Wortanfang) |
|---|---|---|---|---|
| 1 | Bauer Solar / German Brand | 3,1 s | 3,3 s | „Bauer" 3,04 |
| 2 | 460 Watt | 7,4 s | 3,0 s | „460" 7,36 |
| 3 | Glas-Glas-Bifazial | 10,9 s | 3,6 s | „Glas-Glas-…" 10,88 |
| 4 | Zellen direkt sichtbar | 15,2 s | 2,9 s | „Zellen" 15,12 |
| 5 | Solar-Zaun → beide Seiten | 18,6 s | 5,0 s | „Solar-Zaun" 18,56 |
| 6 | Stäubli statt MC4 | 25,1 s | 4,5 s | „Stäubli-Stecker" 25,04 |
| 7 | 2 mm → Hagelklasse 3 | 29,7 s | 5,4 s | „2 mm" 29,68 |
| 8 | Vergleich 2,0 / 1,6 mm | 36,3 s | 3,4 s | „1,6" 36,20 |
| 9 | Brandschutzklasse A | 40,0 s | 3,6 s | „Brandschutzklasse" 39,92 |
| 10 | Schon bewiesen | 46,1 s | 3,3 s | „vorherige" 46,00 |
| 11 | Härte / Feuer / Schlag | 49,9 s | 3,6 s | „Härtetest" 49,88 |
| 12 | Endkarte | 54,0 s | 2,0 s | „Link" 53,84 |

Drei Szenen tragen zwei Aussagen nacheinander, weil im 240-px-Band nur eine
Karte Deckung tragen kann (Muster aus Video 01/04):
Solar-Zaun → „Ertrag von beiden Seiten" (Frame 42),
Stäubli ✓ → „Kein Standard-MC4" ✕ (Frame 45),
„2 mm" → Hagelwiderstandsklasse 3 (Frame 87, hartes Umschalten statt Überblenden).

Die Test-Szene macht es **anders**: Härte, Feuer und Schlag lösen einander nicht
ab, sondern bleiben stehen und sammeln sich an. Der dritte Test fällt erst 2,8 s
nach dem ersten — als Wechselkarte hätte er 0,8 s Standzeit gehabt.

**ASR-Korrekturen:** „Solar-Zaun-Verwender" → als Solar-Zaun verwenden,
„vorherrige" → vorherige.

### Pre-Delivery Review
Alle 1680 Frames transparent gerendert und die Grafik-Bounding-Box gemessen
(Alpha, Schwelle 45 %, Partikel per Morphologie gefiltert; 1233 Frames tragen
Grafik). Szenen 1–11: oberste Kante **884 px**, unterste **1094 px**, horizontal
176–904 px. Gesichts-Zone endet bei 864, Safe Zone 54–1026 / 1104.
**Null Verstöße.**

Die Endkarte liegt bei 786–1098 px. Die 786 sind die aus Video 04 übernommene,
dokumentierte Ausnahme: Das Logo steht über der Bühnenoberkante, damit es nicht
an der Pill klebt. Gegengeprüft — im Schlussshot sitzt der Sprecherkopf bei rund
300 px, also über 480 px darüber.

**Gesichts-Zone gegen jeden Shot geprüft.** Szenenerkennung ergab 14 Schnitte
(5,3 / 7,7 / 12,8 / 16,1 / 23,8 / 26,2 / 29,6 / 31,4 / 37,3 / 39,1 / 49,8 /
51,0 / 52,3 / 54,0 s). Aus jedem Shot ein Frame mit eingeblendeter Grafik
kontrolliert: kein Gesicht im Grafikband. Die B-Roll der Tests (49,8–54,0 s)
zeigt Füße und Modul, keine Gesichter.

### Vier Befunde, die der Zonen-Test nicht gefunden hat
Wieder der Punkt aus Video 04: Die Bounding-Box war von Anfang an sauber, die
Bilder waren es nicht. Gefunden erst an vergrößerten Ausschnitten über echter
Footage:
1. **„BAUER SOLAR" war zu „BAUER SOL" abgeschnitten.** Das Label der
   Vergleichs-Grafik lief in einer festen 150-px-Spalte und verschwand unter dem
   Balken. Spalte auf 210 px, Balken von 300 auf 240 px.
2. **Der Glas-Glas-Schnitt war vor hellem Modul praktisch unsichtbar.** Die
   Scheiben sind hell und lagen vor hellem Hintergrund. Diagramm vergrößert
   (260 → 300 px breit, Zellschicht 16 → 22 px) und auf eine dunkle Trägerplatte
   gesetzt.
3. **Dasselbe beim Zellraster** — Zellen von 30 auf 34 px, ebenfalls mit dunkler
   Platte hinterlegt.
4. **Die erste Test-Pille stand sichtbar links neben der Bildmitte**, weil die
   beiden noch unsichtbaren Pillen ihren Platz schon hielten. Jetzt werden nur
   gestartete Tests gerendert, die Reihe bleibt mittig.

### Ein Fund, der auch Video 04 betraf
Die Endkarten-Pill „atmet" (Sinus-Skalierung) und federt beim Einflug über. Im
**Vollsequenz**-Review lag ihre Unterkante dadurch auf 1114 px — 10 px unter der
Safe Zone. Bei den Stichproben in Video 04 war der Spitzenwert nicht in den
geprüften Frames und daher unentdeckt geblieben. Die Pill steht jetzt in
**beiden** Kompositionen auf 0,75 statt 0,814 der Bühnenhöhe.
**Lehre: Stichproben reichen bei Federn mit Überschwung nicht — der Spitzenwert
liegt oft in zwei, drei Frames.**

### Kundenfeedback Video 03 (2026-08-20)
Fünf Punkte, alle umgesetzt:

1. **Solar-Zaun zu kurz lesbar.** Die zweite Karte hing auf „von beiden Seiten"
   (19,96 s) — damit stand die erste nur 1,4 s. Jetzt auf „Produktion"
   (Frame 75 = 21,1 s), Szene von 5,0 auf 5,8 s. Beide Karten über 2,5 s.
2. **Stäubli-Stecker zu kurz.** Gegenkarte von Frame 45 auf 66 (27,3 s),
   Szene 4,5 → 4,6 s. Beide Karten jetzt über 2 s.
3. **Klasse auf der falschen Seite.** Das „A" stand links vom Begriff. Jetzt
   rechts — so, wie man es liest: „Brandschutzklasse A".
4. **„Schon bewiesen" gestrichen.** Der Verweis auf ältere Videos trug nichts.
   An seiner Stelle steht jetzt **„Wirklich so robust?"** ab 43,8 s (der O-Ton
   sagt an der Stelle „dass die Module wirklich so robust sind"), Unterzeile
   „Wir haben es getestet" ab 46,8 s. Die Frage leitet direkt in die Test-Szene
   über, statt den Zuschauer wegzuschicken.
5. **Schlagtest zu kurz.** Test-Szene von 3,6 auf 4,1 s — läuft jetzt bündig bis
   zur Endkarte (49,9–54,0 s).

Zonen nach den Änderungen neu über alle 1680 Frames gemessen: Szenen 1–11
884–1094 px, horizontal 176–904 px. Null Verstöße.

### Inhaltliche Entscheidung
Der Sprecher sagt „2 mm Stärke" ohne zu sagen, worauf sie sich bezieht. Aus dem
Kontext (Glas-Glas-Modul, Vergleich mit 1,6 mm, Hagelwiderstandsklasse) ist die
**Glasstärke** gemeint; die Unterzeile sagt das, ohne dem O-Ton zu widersprechen.
Falls der Chef das anders sieht, ist es ein Prop (`staerke.valueCaption`).

## Overlay-Export Video 03 + Neu-Export Video 04 (2026-08-20)

**Geliefert:** `Ergebnisse/Renders/03_BauerSolar-Modul_Overlay_ProRes4444.mov`

| | |
|---|---|
| Codec | ProRes 4444, `yuva444p12le` (Alpha erhalten) |
| Auflösung | 1080 × 1920, 30 fps |
| Länge | 56,00 s / 1680 Frames |
| Größe | 294 MB |

Alpha an sieben Zeitpunkten gemessen (4 / 12 / 20 / 30 / 42 / 51 / 55 s):
mittlere Deckkraft 0,35–2,4 %, Hintergrund durchgehend leer. Keine Blend-Modi,
das Overlay ist selbsttragend. Bei Frame 0 auflegen.

Der Dateiname der Lieferung trägt die **korrekte** Schreibweise „BauerSolar",
obwohl die Quelldatei `03_BauSolar-Modul_V1.mp4` heißt.

**Video 04 neu exportiert**, gleiche Spezifikation wie am 19.08. (79,50 s /
2385 Frames / 515 MB) — Grund ist allein die korrigierte Endkarten-Pill
(0,814 → 0,75). Die alte Fassung ist damit überholt.

Gegenprobe der Endkarte mit der Review-Pipeline (Alpha, Schwelle 45 %,
Morphologie-Filter): Unterkante **1084 px**, also 20 px Luft zur Safe Zone.

**Eine Falle beim Nachmessen am fertigen Film:** Misst man die Bounding-Box ohne
den Morphologie-Filter, zählen die Energie-Partikel mit und die Box wird viel
größer als die eigentliche Grafik (im ersten Anlauf 184–895 px statt 194–886 px,
Unterkante scheinbar 1106 statt 1084). Der Filter gehört zur Messung dazu.

## Flackern im Export — Ursache und Konsequenz (2026-08-20)
Der Kunde meldete, dass „Hagelwiderstandsklasse 3" im exportierten Video
flackert. Der Befund war real: **21 von 162 Frames** dieser Szene zeigten nur
das Badge, die Textzeile fehlte.

### Ursache
Ein Element mit Deckkraft < 1 bekommt in Chrome eine eigene Render-Surface.
Remotion-Federn konvergieren gegen 1, erreichen es aber **nie exakt**
(0,99999…). Die Surface bleibt damit für immer bestehen — und beim
Einzelframe-Rendern zeichnet sie den Textknoten sporadisch nicht mit.

Warum ausgerechnet diese Szene: Es war die **einzige Stelle im ganzen Video**,
an der die Deckkraft auf dem Gruppen-Element saß statt auf den Kindern. Überall
sonst tragen Text und Grafik ihre Deckkraft selbst.

Der Fix ist eine Zeile:
```ts
const settle = (v: number) => (v > 0.999 ? 1 : v);
```
Angewandt auf jede Feder-gesteuerte Deckkraft in beiden Kompositionen. Damit
schnappt die Deckkraft auf glatte 1 und die Render-Surface löst sich auf.

### Drei Sackgassen davor — und warum sie Sackgassen waren
- **Schrift-Ladefehler vermutet** (`delayRender` bis Montserrat da ist).
  Eingebaut und behalten, weil korrekt — hat das Flackern aber nicht behoben.
- **GPU-Rasterisierung vermutet** (`--gl=swangle`). Machte es *schlimmer*
  (8 statt 4 gemeldete Frames), also kein GPU-Problem.
- **`transform` auf dem Textknoten vermutet.** Auf `position: relative` +
  `left`/`top` umgestellt. Ebenfalls behalten (die Regel ist sinnvoll), war
  aber nicht die Ursache.

### Der eigentliche Fehler war ein Messfehler
Die ersten drei Testrunden meldeten „keine Ausfälle" und waren wertlos: Im
Prüfskript stand `%w` (Breite des **Bildes**, immer 1080) statt `%@`
(Bounding-Box). Damit war jeder Frame unauffällig. Erst mit `%@` zeigte sich das
wahre Ausmaß — 21 statt der vermuteten 5 Frames.

**Merksatz: Wenn eine Messung durchweg „alles in Ordnung" sagt, zuerst die
Messung prüfen, nicht die Hypothese.**

### Konsequenz für die Auslieferung
Die mittlere Deckkraft ist ein **schlechter** Detektor: Fällt eine Textzeile
weg, sinkt sie nur von 0,89 % auf 0,13 % — im Rauschen der Szenenwechsel. Die
**Breite der Bounding-Box** dagegen bricht schlagartig ein (706 → 59 px).

Neu: `tools/motion/scripts/flicker-check.sh <datei.mov>` prüft jeden Frame des
fertigen Films auf diesen Einbruch. Treffer an Szenengrenzen sind normal, alles
dazwischen ist ein Fehler. Gehört ab jetzt vor jede Abgabe.

Zusätzlich wird Video 03 nicht mehr direkt als Video gerendert, sondern:
PNG-Sequenz → Sequenz prüfen → mit ffmpeg zu ProRes kodieren. So ist die
ausgelieferte Datei nachweislich identisch mit den geprüften Frames.

```bash
ffmpeg -framerate 30 -start_number 0 -i element-%04d.png \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le \
  -alpha_bits 16 -vendor apl0 out.mov
```

### Stand der Dateien
- **Video 03 neu ausgeliefert**, 271 MB (statt 293 MB — ffmpeg packt die
  Alpha-Ebene enger als Remotions Encoder). Klasse-Block über die gesamte
  Szene konstant, kein Ausfall.
- **Video 04 bleibt, wie es ist.** Der Frame-für-Frame-Test des ausgelieferten
  Films meldet 21 Kandidaten — alle 21 sind Szenengrenzen, keiner ein Ausfall.
  Der `settle()`-Schutz ist im Code trotzdem eingebaut, für den Fall, dass die
  Komposition später noch einmal gerendert wird.

### Ebenfalls in dieser Runde
Die Unterzeilen von „460 Watt" und „2 mm" standen an der Bühnenunterkante und
damit weit von ihrer Zahl entfernt — sie lasen sich als zwei getrennte
Elemente. Beide sitzen jetzt direkt unter der Zahl (0,70 bzw. 0,67 statt 0,87
der Bühnenhöhe). Die Caption-Komponente hat dafür eine optionale Höhe bekommen.

## Video 07 — Recruiting Elektromeister (2026-08-20)
Eigene Komposition `SW-Recruiting`, Datei
`tools/motion/src/clients/sw-projektentwicklung/projects/recruiting/Composition.tsx`.

**Footage:** 2160 × 3840, 25 fps, 25,664 s. **Ab 22,8 s ist das Bild schwarz** —
dort sitzt die Bewerbungs-Endkarte. Komposition **25,63 s** (769 Frames).

| # | Szene | Start | Dauer | Stichwort (Wortanfang) |
|---|---|---|---|---|
| 1 | „Elektromeister?" | 0,3 s | 2,3 s | 0,24 |
| 2 | Was nervt (2 ✕-Karten) | 2,6 s | 5,7 s | „Photovoltaik" 2,48 / „Überspannungsschutz" 5,64 |
| 3 | „Dann bist du bei uns richtig" | 8,45 s | 2,9 s | „dann" 8,36 / „genau richtig" 9,08 |
| 4 | Was du hier machst (2 ✓-Karten) | 11,6 s | 4,7 s | „Gewerbe" 11,52 / „Tarifschaltgeräte" 14,04 |
| 5 | „Wir suchen dich" + Teamleiter-Pill | 16,55 s | 2,9 s | 16,44 / „Teamleiter" 17,20 |
| 6 | CTA „Meld dich gern" | 19,6 s | 3,2 s | 19,52 / 20,80 |
| 7 | **Bewerbungs-Endkarte** | 22,9 s | 2,73 s | auf dem Schwarzbild |

### Die Endkarte ist die einzige Szene außerhalb des 240-px-Bandes
Ab 22,8 s gibt es kein Bild und keinen Sprecher — also auch keine Gesichts-Zone,
die freizuhalten wäre. Die Endkarte nutzt deshalb die **volle Reels-Safe-Zone**
(134–1104 px) statt der sonst üblichen 230 px zwischen Gesichts-Zone und
Safe-Zone-Unterkante. Anders wäre eine Bewerbungskarte mit Logo, Stelle und CTA
nicht unterzubringen.

Aufbau von oben nach unten: Logo → „KOMM INS TEAM" → „ELEKTROMEISTER" →
„als Teamleiter (m/w/d)" → Pill „JETZT BEWERBEN" → Kontaktzeile.
Gemessen: 205–1072 px, horizontal 90–989 px.

Die Überschrift heißt bewusst **nicht** noch einmal „Wir suchen dich" wie in
Szene 5, sondern greift das Schlusswort des O-Tons auf („ob du zu uns ins Team
passt").

### Endkarte entschlackt (Kundenfeedback)
Rückmeldung: „mehr sichtbare Zeit in den 2,8 Sekunden, weniger Animation".
Der erste Aufbau lief gestaffelt bis Frame 46 plus Federweg — vollständig
lesbar war die Karte damit nur **1,2 s** von 2,8.

Umgebaut:
- Einsätze von 0/10/18/24/34/46 auf **0/4/7/9/11/14** zusammengezogen.
- Neue Feder `ENTER` (Dämpfung 18, Steifigkeit 220): fährt zügig an und
  schwingt **nicht** über. Überschwingen kostet an dieser Stelle nur Standzeit.
- Bewegungswege verkleinert: Logo 0,86 → 0,94 Startskalierung, Überschrift
  1,15 → 1,06, Pill 0,3 → 0,85, Stelle 14 → 8 px Versatz.
- Endkarte beginnt jetzt mit dem Schwarzbild bei 22,8 s statt 22,9 s
  (CTA-Szene entsprechend 0,05 s kürzer).
- Die Stelle „ELEKTROMEISTER" ist die eigentliche Information und etwas größer
  (0,0235 → 0,026).

Ergebnis: Die Karte steht ab Frame 702 vollständig, also **2,1 s statt 1,2 s** —
fast doppelt so lange.

### Pre-Delivery Review
Alle 769 Frames gemessen. Szenen 1–6: **882–1097 px**, horizontal 135–957 px
(Gesichts-Zone endet 864, Safe Zone 54–1026 / 1104). Endkarte: 205–1072 px.
**Null Verstöße.** Flacker-Prüfung (Breiten-Ausreißer): keine.

Gesichts-Zone gegen alle acht Shots geprüft (Schnitte bei 5,3 / 8,6 / 12,6 /
14,1 / 16,0 / 17,9 / 20,6 / 22,8 s): kein Gesicht im Grafikband. Vier der acht
Shots sind ohnehin B-Roll von Verteilerkästen.

### ASR-Korrekturen — hier besonders viele
Der Sprecher redet stark Dialekt:
„Elektromaster" → Elektromeister · „Fotoverteilkeinlage" → Photovoltaikanlagen ·
„das komplizierte Stär" → das Komplizierteste · „Tarishaltgeräte" →
Tarifschaltgeräte · „pascht" → passt.

**Eine Lesart, die der Kunde bestätigen muss:** Das ASR schreibt
„Arschchutzanschließer". Aus dem Kontext — Gewerbeanlagen, direkt gefolgt von
„Tarifschaltgeräte anschließen" — ist **NA-Schutz** (Netz- und Anlagenschutz)
die einzige sinnvolle Lesart; die beiden gehören beim gewerblichen Netzanschluss
zusammen. Steht so im Bild, ist aber ein Prop (`gewerbe.row2`).

**Und eine offene Angabe:** Die Kontaktzeile der Endkarte steht auf
`sw-projektentwicklung.com` — das ist die Website aus der CI-Erfassung, **nicht**
eine bestätigte Bewerbungsadresse. Falls es eine eigene Mail oder ein
Bewerbungsformular gibt, gehört die dorthin (`endkarte.contact`).

## Overlay-Export Video 07 (2026-08-20)
Geliefert: `Ergebnisse/Renders/07_Recruiting-Elektromeister_Overlay_ProRes4444.mov`

| | |
|---|---|
| Codec | ProRes 4444, `yuva444p12le` (Alpha erhalten) |
| Auflösung | 1080 × 1920, 30 fps |
| Länge | 25,63 s / 769 Frames |
| Größe | 192 MB |

Weg wie bei Video 03: PNG-Sequenz rendern → Sequenz prüfen → mit ffmpeg zu
ProRes kodieren. Die ausgelieferte Datei besteht damit nachweislich aus den
geprüften Frames.

Prüfung der Sequenz vor dem Kodieren: 0 Zonen-Verstöße, 0 Breiten-Ausreißer.
Prüfung der fertigen Datei mit `flicker-check.sh`: 17 Kandidaten, alle mit
Breite 0 und alle an Szenengrenzen (Frames 11 / 75–80 / 246 / 255 / 337 / 350 /
486 / 498 / 580 / 590 / 679 / 686) — kein Textausfall.

Alpha an sieben Zeitpunkten gemessen: 0,64–3,3 % in den Szenen, 7,3 % auf der
Endkarte (die trägt deutlich mehr Fläche). Hintergrund durchgehend leer.

Bei Frame 0 auflegen. Die Endkarte liegt komplett auf dem Schwarzbild des
Originalclips — dort trägt allein das Overlay das Bild.

## Video 05 — Hotel Smartino (2026-08-20)
Eigene Komposition `SW-Smartino`, Datei
`tools/motion/src/clients/sw-projektentwicklung/projects/smartino/Composition.tsx`.

**Nummerierung:** Im Auftrag hieß es „04 Projekt Smartino"; die gelieferten
Dateien sind aber **05**_Hotel-Smartino. 04 ist die Flachdach-Erklärung. Ich
halte mich an die Dateinummer.

**Footage:** 2160 × 3840, 25 fps, 49,28 s. Komposition **49,25 s** (1478 Frames).
Kein Schwarzbild am Ende — die Endkarte liegt über dem Sprecher.

### Die Kernzahl fehlte im Transkript
Zwischen „tatsächlich" (endet 2,16 s) und „Autarkiegrad" (beginnt 3,12 s) klafft
im SRT eine Lücke von knapp einer Sekunde. Gesprochen wird dort **„60 Prozent"**
— vom Kunden nachgereicht. Das ist die wichtigste Zahl des Videos und trägt jetzt
den Hook bei 2,3 s.

| # | Szene | Start | Dauer | Stichwort (Wortanfang) |
|---|---|---|---|---|
| 1 | **60 % Autarkie** (Hook) | 2,3 s | 2,9 s | „60 Prozent" ≈ 2,2 (SRT-Lücke) |
| 2 | 65–70 % Prognose | 6,3 s | 3,0 s | „65" 6,24 |
| 3 | Hotel Smartino, Schwäbisch Hall | 10,5 s | 5,4 s | „Hotel" 10,48 / „Schwäbisch Hall" 11,36 |
| 4 | 144 Module · 63 kWp | 16,15 s | 3,7 s | „144" 16,68 / „63" 18,12 |
| 5 | 70.000 kWh Verbrauch | 21,4 s | 3,4 s | „Stromverbrauch" 21,28 |
| 6 | **Netzbezug 70.000 → 25.000** | 27,2 s | 4,3 s | „25.000" 27,12 |
| 7 | „Perfekt ausgelegt" | 35,3 s | 3,1 s | 35,24 / „perfekt" 37,08 |
| 8 | CTA Gewerbedach-Analyse | 39,4 s | 5,1 s | „Gewerbeobjekt" 39,36 |
| 9 | Endkarte Logo + Pill | 45,0 s | 4,2 s | „melde dich" ≈ 45,0 |

Szene 6 ist die Pointe: zwei Balken im echten Verhältnis (25.000 zu 70.000 sind
0,36), grau gegen orange. Szene 4 zeigt beide Anlagenwerte **nebeneinander** und
lässt sie stehen — im O-Ton kommen sie in einem Atemzug.

Der Sprecher setzt bei 32,8 s neu an (Abbruch „Also das ist wirklich ein …",
Neuansatz ab 34,7 s). Im Material liegt dort ein Schnitt bei 33,9 s; die
Fazit-Szene beginnt deshalb erst um 35,3 s.

### Pre-Delivery Review
Alle 1478 Frames gemessen. Szenen 1–8: **882–1097 px**, horizontal 168–909 px
(Gesichts-Zone endet 864, Safe Zone 54–1026 / 1104). **Null Verstöße.**
Endkarte 773–1098 px — die aus Video 03/04 bekannte, dokumentierte Ausnahme:
Das Logo steht über der Bühnenoberkante. Gegengeprüft am Schlussshot: der
Sprecherkopf endet deutlich darüber, kein Gesicht verdeckt.

Ein Breiten-Ausreißer bei Frame 823 geprüft: dort wächst der erste Balken der
Netzbezug-Szene gerade an — kein Textausfall.

**Gesichts-Zone gegen alle Shots geprüft** (Schnitte 12,1 / 14,2 / 16,8 / 19,9 /
31,6 / 33,9 / 36,4 / 38,5 / 49,2 s). Kritisch war nur die Beratungs-B-Roll ab
36,4 s — dieselbe Situation wie in Video 01: drei Gesichter, tiefer im Bild als
der Dachsprecher. Sie enden hier bei rund 850 px, die Fazit-Überschrift sitzt
auf 933 px. Passt, aber knapp.

### Zwei Befunde aus der Sichtprüfung
1. **„VORHER" wurde vom Balken überdeckt** — exakt derselbe Fehler wie
   „BAUER SOL" in Video 03: feste Label-Spalte zu schmal (90 px, das Wort misst
   rund 110). Spalte auf 130 px, Balken von 250 auf 210 px.
   **Muster erkannt: Label-Spalten fester Breite immer gegen das längste Wort
   prüfen, nicht gegen das erste.**
2. **Der graue Vorher-Wert war vor hellem Dach zu kontrastarm** (#8A8681 auf
   Ziegel/Blech). Auf #C9C4BD aufgehellt — gedämpft gegenüber Orange bleibt er
   trotzdem.

### Kundenfeedback Video 05 (2026-08-20)
1. **„Richtig gelungenes Projekt" war langweilig.** Zu Recht — an der Stelle
   stand nur eine Behauptung im Bild. Die Szene trägt jetzt den **Beweis**: die
   drei Kennzahlen des Videos laufen als Chips nacheinander ein
   (63 kWp · 144 Module · 60 % Autarkie), „perfekt ausgelegt" wurde zur
   Unterzeile und sitzt damit auf dem Wort statt davor. Das ist das Muster aus
   Video 03 (Härte/Feuer/Schlag), das der Kunde ausdrücklich gelobt hat.
   Erfunden wird nichts — alle drei Zahlen sind vorher im O-Ton gefallen.
2. **„Wie viel Autarkie geht?" zu kurz.** Die Karte stand 1,0 s. Sie kann nicht
   früher kommen (das Wort „Autarkie" fällt erst 43,44 s), also läuft die
   CTA-Szene jetzt bis 45,9 statt 44,5 s → **2,4 s**. Die Endkarte rückt
   entsprechend auf 46,0 s; der letzte SRT-Eintrag hat keine Wortzeiten mehr,
   nach Sprechtempo fällt „dann melde dich doch bei uns" dort.

Nach der Änderung nachgemessen: Die Chip-Reihe reichte mit den ersten Werten bis
**1025 px** — die Safe Zone endet bei 1026, also kein Puffer. Innenabstand,
Lücke und Schrift verkleinert, jetzt 148–957 px.

### Messgrundlage geklärt: weiche Kante ≠ feste Grafik
Beim Nachmessen fiel die Endkarten-Pill mit Unterkante **1128 px** auf, also
24 px unter der Safe Zone. Gegenprobe mit zwei Schwellwerten:

| Schwelle | Endkarte Unterkante |
|---|---|
| 45 % (weiche Kante, Glow zählt mit) | 1128 px |
| 75 % (feste Grafik) | **1092 px** |

Die 1128 sind ausschließlich der orange Schein der Pill, nicht ihr Körper. Bei
Video 03/04 wurde in halber Auflösung gemessen, wo der Morphologie-Filter den
Schein wegräumt — daher standen dort 1084/1098 im Protokoll. Gleiche Geometrie,
andere Messung.

**Regel ab jetzt: Für das Urteil zählt die feste Grafik (Schwelle 75 %).**
Ein weicher Schein, der die Kante überschreitet, ist kein Lesbarkeitsproblem —
die Safe Zone schützt vor der App-Oberfläche, und ein halb verdeckter Schein
fällt niemandem auf. Die 45-%-Messung bleibt für die Flacker-Erkennung.

Endstand: feste Grafik Szenen 1–8 **886–1094 px**, horizontal 148–957 px.
Endkarte 773–1092 px. **Null Verstöße.**

### ASR-Korrekturen
„Schwäbischhal" → Schwäbisch Hall · „Photovoltaik-Entlage" → Photovoltaikanlage ·
„Gewerbio-Objekt" → Gewerbeobjekt.

**Bewusst nicht geschrieben:** „kostenlose Analyse". Er sagt nur „eine Analyse
haben möchtest" — ob sie kostenlos ist, ist nicht gesagt. Gleiche Entscheidung
wie in Video 01, wo „kostenlos" auf Kundenwunsch gestrichen wurde.

## Overlay-Export Video 05 (2026-08-20)
Geliefert: `Ergebnisse/Renders/05_Hotel-Smartino_Overlay_ProRes4444.mov`

| | |
|---|---|
| Codec | ProRes 4444, `yuva444p12le` (Alpha erhalten) |
| Auflösung | 1080 × 1920, 30 fps |
| Länge | 49,27 s / 1478 Frames |
| Größe | 243 MB |

Weg wie bei Video 03 und 07: PNG-Sequenz rendern → Sequenz prüfen → mit ffmpeg
kodieren. Prüfung vor dem Kodieren: 0 Zonen-Verstöße (feste Grafik, Schwelle
75 %), keine Breiten-Ausreißer außer Frame 823 — dort wächst der erste Balken
der Netzbezug-Szene gerade an.

Prüfung der fertigen Datei mit `flicker-check.sh`: 11 Kandidaten, alle mit
Breite 0 und alle an Szenengrenzen (153 / 317 / 474 / 741 / 942 / 1061 / 1149 /
1184 / 1374 / 1386 / 1474) — kein Textausfall.

Alpha an neun Zeitpunkten: 0,5–2,4 %. Der Wert bei 22 s (0,002 %) ist korrekt —
dort läuft die Verbrauchs-Szene bereits, die Zahl setzt aber erst bei 22,13 s
ein („70.000"), im Bild sind nur die Partikel.

Bei Frame 0 auflegen.

## Nachtrag Video 03 — Flagge bei „German Brand" (2026-08-20)
Kundenwunsch: „German Brand" braucht eine deutsche Flagge.

Umgesetzt als **CSS-Verlauf**, nicht als Bilddatei — bei 25 px Höhe trägt ein
PNG keine Details mehr, und ein Asset wäre eine weitere Datei, die mitgepflegt
werden müsste. Seitenverhältnis 5:3 wie die echte Flagge, Farben
#000000 / #DD0000 / #FFCE00.

**Der helle Rahmen ist Pflicht, keine Deko:** Der schwarze Streifen liegt in
dieser Szene vor einem dunklen Modul und verschwindet ohne Abgrenzung — die
Flagge sähe dann nach Rot-Gold aus statt Schwarz-Rot-Gold.

Die Unterzeile ist dafür von der Standard-`Caption` auf eine eigene Zeile
umgestellt (Flagge + Text in einer Flex-Reihe), damit beide gemeinsam einlaufen
und die Zeile mittig bleibt. Höhe unverändert bei CAP_Y.

Zonen nachgemessen (feste Grafik, Schwelle 75 %): Szene 1 liegt bei 936–1090 px,
horizontal 287–789 px. Die Zeile ist weiterhin schmaler als die Überschrift
„BAUER SOLAR", der Maximalwert der Szene ändert sich also nicht.

### Video 03 neu exportiert
`03_BauerSolar-Modul_Overlay_ProRes4444.mov`, 271 MB, sonst identische
Spezifikation (ProRes 4444, `yuva444p12le`, 1080 × 1920, 30 fps, 56,00 s /
1680 Frames). Weg wie gehabt: PNG-Sequenz → Sequenz prüfen → ffmpeg.

Prüfung vor dem Kodieren: 0 Zonen-Verstöße (feste Grafik, Schwelle 75 %),
Szenen 1–11 bei 886–1094 px, Endkarte 773–1092 px. Breiten-Ausreißer bei
819–821 (Stecker-Kartenwechsel) und 1207 (Einflug Brandschutz) — beide bekannt
und geprüft.

Prüfung der fertigen Datei: 26 Kandidaten, identisch mit der Liste des vorigen
Exports, alle an Szenengrenzen oder Kartenwechseln. Die Flagge im fertigen Film
gegengeprüft — im Alphakanal vorhanden und farbrichtig.

## Offene Punkte
- Kontrast in Szene „beide Seiten" und „Gartenzaun" über der echten Footage:
  dunkle Modulkonturen vor dunkler Jacke. Für das Overlay unkritisch, weil der
  Kunde selbst komponiert — bei einer gebrannten Fassung aber nachzuschärfen.
- Studio-Port: auf diesem Rechner ist `127.0.0.1:3000` bereits von einem anderen
  Benutzerkonto belegt. Studio läuft deshalb auf **3111**
  (`tools/motion/.claude/launch.json`).

## Zeitleiste
- 2026-08-12 — Projektstruktur angelegt, CI erfasst, Komposition gebaut,
  Pre-Delivery Review durchgeführt.
- 2026-08-12 — O-Ton-Footage einsortiert und als Hintergrund eingebunden,
  Gesichts-Zone gegen echtes Material bestätigt, Kontrast-Schwächen in
  Szene 5/6 dokumentiert.
- 2026-08-12 — Timing auf SRT-Wortzeitstempel umgestellt, Flip-Szene und
  Fortschrittslinie entfernt, Endkarten-Logo vergrößert (Kundenfeedback).
- 2026-08-12 — Offizielle Logodatei des Kunden eingesetzt, Endkarte dafür in
  Pill-Phase und Logo-Lockup geteilt.
- 2026-08-12 — Logo freigestellt in Weiß (Negativ-Version mit orangem Icon),
  weiße Karte entfernt, Schlagschatten für Kontrast auf hellem Himmel.
- 2026-08-12 — Pill/Logo-Übergabe auf hartes Umschalten umgestellt (Kunden-
  rückmeldung), Logo auf 207 px vergrößert, schwarzer Schlussframe entfernt,
  Pre-Delivery Review mit und ohne Guides bestanden.
- 2026-08-12 — Render-Blockade behoben (System-Chrome statt Headless Shell),
  Overlay ohne Hintergrundvideo als ProRes 4444 mit Alpha ausgeliefert.
- 2026-08-14 — Video 01 (Gottwollshausen) als eigene Komposition gebaut,
  Timing aus den Segment-Timecodes abgeleitet und bewusst nach hinten versetzt,
  Folgen-Szene auf Einzelkarten umgestellt, Pre-Delivery Review bestanden.
- 2026-08-17 — Schreibweise auf Gottwollshausen korrigiert, Footage eingebunden,
  Länge auf 53,53 s gesetzt, Endkarte wegen Gesichtsabdeckung in der
  Beratungsszene umgebaut (Pill oben, Analyse-Zeile unten), alle dreizehn Shots
  einzeln gegen die Gesichts-Zone geprüft.
- 2026-08-17 — Kundenfeedback umgesetzt: Hook früher, Ertrags- und Grenze-Szene
  entschlackt, „kostenlos" gestrichen, Endkarte zugunsten der Autarkie-Pill
  neu aufgeteilt.
- 2026-08-17 — Grenze-Szene bündig an das Ertrags-Ende gezogen (22,2–24,2 s),
  Overlay Video 01 als ProRes 4444 mit Alpha ausgeliefert.
- 2026-08-18 — Hook auf den wortgleichen O-Ton-Satz umgebaut (zweizeilig),
  „460 Wp" auf „460 Watt" geändert, Overlay neu exportiert.
- 2026-08-18 — Video 02: Füllbalken in der Mehrertrag-Szene entfernt,
  Overlay neu exportiert.
- 2026-08-18 — Video 04 (Flachdach-Erklärung) als eigene Komposition gebaut,
  zwölf Szenen auf den Wortzeitstempeln des SRT, gemeinsame gerechnete
  Gestell-Geometrie für die drei Aufständerungs-Szenen, Pre-Delivery Review
  über alle Frames ohne Verstoß.
- 2026-08-19 — Video 04: Footage eingebunden (79,47 s), elf Szenen auf
  Kundenwunsch vorgezogen, Endkarte auf gleichzeitiges Logo + Pill umgebaut,
  Overlay als ProRes 4444 mit Alpha ausgeliefert.
- 2026-08-20 — Video 03 (Bauer Solar Modul) als eigene Komposition gebaut,
  zwölf Szenen direkt auf den Wortanfängen, Footage eingebunden (56,0 s),
  Gesichts-Zone gegen alle 14 Shots geprüft, Vollsequenz-Review ohne Verstoß.
  Dabei ein Überschwing-Fehler der Endkarten-Pill gefunden und auch in
  Video 04 korrigiert.
- 2026-08-20 — Kundenfeedback Video 03 umgesetzt (Karten-Standzeiten, Klasse
  rechts, „Schon bewiesen" durch „Wirklich so robust?" ersetzt, Schlagtest bis
  zur Endkarte), Overlay 03 als ProRes 4444 ausgeliefert und Overlay 04 wegen
  der Pill-Korrektur neu exportiert.
- 2026-08-20 — Flackern im Export von Video 03 auf eine Gruppen-Deckkraft von
  0,9999 zurückgeführt (eigene Chrome-Render-Surface), mit settle() behoben,
  Prüfskript flicker-check.sh angelegt, Video 03 aus geprüfter PNG-Sequenz neu
  kodiert. Unterzeilen von „460 Watt" und „2 mm" enger an die Zahl gerückt.
- 2026-08-20 — Video 07 (Recruiting Elektromeister) gebaut, sieben Szenen,
  Bewerbungs-Endkarte auf dem Schwarzbild ab 22,8 s über die volle Safe Zone.
  Review ohne Verstoß. Endkarte nach Kundenfeedback entschlackt (2,1 s statt
  1,2 s vollständig sichtbar) und als ProRes 4444 mit Alpha ausgeliefert.
- 2026-08-20 — Video 05 (Hotel Smartino) gebaut, neun Szenen. Die Kernzahl
  „60 % Autarkie" fehlte im SRT und kam vom Kunden; sie trägt jetzt den Hook.
  Review ohne Verstoß. Fazit-Szene nach Kundenfeedback zum Kennzahlen-Rückblick
  umgebaut, CTA-Karte auf 2,4 s verlängert, als ProRes 4444 mit Alpha
  ausgeliefert.
- 2026-08-20 — Video 03: Deutschlandflagge bei „German Brand" ergänzt,
  Overlay neu exportiert.

## 2026-09-01 — Migration ins Studio-Hauptsystem

**Gemacht:** Charge vom Zweit-MacBook übernommen; „Solar-Wissen" ist jetzt
drittes Projekt unter `projects/SW-Projektentwicklung/` (neben
Einfamilienhaus-und-Smartino und Solar-Verkaeufer). Inhalte unverändert.

## 2026-09-03 — Untertitel in den Animationslücken (alle sechs Videos)

**Auftrag (Jan):** Für die sechs Videos mit fertigen Animationen zusätzlich
Untertitel einbauen, die **nur dann** erscheinen, wenn gerade keine der
bestehenden Animationen läuft. Die Animationen selbst bleiben unverändert.

### Umsetzung
- Neue Spur `tools/motion/src/clients/sw-projektentwicklung/Subtitles.tsx`
  (`SubtitleTrack`), in alle sechs Kompositionen eingehängt. Die Szenen sind
  nicht angefasst; ihre `startSec`/`durationSec` gehen als **Sperrzeiten** in die
  Spur, die daraus die freien Fenster rechnet (gleiche Frame-Rundung wie die
  `<Sequence>`-Elemente, damit sich Grafik und Untertitel nie um einen Frame
  überlappen). Fenster unter **0,5 s** bleiben leer, sichtbare Seiten-Reste
  unter 10 Frames fallen weg — sonst blitzt Text auf.
- Darstellung: Montserrat 600, 46 px, Weiß, gesprochenes Wort in Orange,
  Textschatten statt Kasten (Alpha-Overlay bleibt selbsttragend, kein
  backdropFilter/Blend). Sitzt in derselben Bühne wie die Grafiken
  (0,455–0,575 · H, also unter der Gesichts-Zone, über der Safe-Zone-Unterkante).
  Deckkraft mit `settle()` auf glatte 1 — Flacker-Lehre aus Video 03.
- Studio-Props pro Komposition: `subtitles.enabled / fontSize / highlight /
  minGapSec / pos`.

### Wort-Timings
| Video | Quelle | Anmerkung |
|---|---|---|
| 01 Gottwollshausen | **Scribe** (`_intern/cache/01_…scribe.json`) | Kundentranskript hat nur Segment-Zeiten |
| 02 Bifazial | Kunden-SRT | wortgenau |
| 03 Bauer Solar | Kunden-SRT | wortgenau |
| 04 Flachdach | Kunden-SRT | wortgenau |
| 05 Smartino | **Scribe** (`_intern/cache/05_…scribe.json`) | SRT-Schluss ab 43,8 s ohne Wortzeiten |
| 07 Recruiting | Kunden-SRT | wortgenau |

Generator: `tools/motion/scripts/sw-captions.ts` → `src/clients/sw-projektentwicklung/captions/<id>.json`
(Kopie + lesbare Kontrollfassung mit Sichtbarkeits-Spalte in `_intern/captions/`).
Seiten mit 2–5 Wörtern, Bruch an Pause ≥ 0,45 s / Satzende / Komma+Pause, keine
hängenden Artikel am Zeilenende, Zahlen als Ziffern, Füllwörter raus.
Verhörer-Korrekturen stehen als Liste im Skript (u. a. Gebüte→Gemüter,
Pfauenlage→PV-Anlage, Fotoverteilkeinlage→Photovoltaikanlagen, pascht→passt,
Solar-Zaun-Verwender→Solar-Zaun verwenden).

**Zwei Befunde aus Video 01, die der Kunde bestätigen muss** (Scribe und Whisper
hören übereinstimmend dasselbe, Whisper-Gegenprobe in `_intern/cache/01_…whisper.json`):
1. **„insgesamt 54 Solarmodule“** — die Zahl fehlte im Kundentranskript; der Prop
   `anlage.moduleCount` der Animation ist weiterhin leer. Im Untertitel steht die
   54, die Stelle liegt aber unter der Projekt-Szene (6,2–10,2 s) und ist damit
   im Bild **nicht** sichtbar. Wenn der Kunde die 54 bestätigt, kann sie in die
   Anlage-Szene.
2. **„Das Tarifschaltgerät wird immer benötigt ab 25 kWp“** — beide ASR lesen
   „Tarifschaltgerät“, die Folgen-Karte der Animation sagt „Rundsteuer-Empfänger“
   (Interpretation vom 14.08.). Der Untertitel „Das Tarifschaltgerät wird“ ist
   bei 24,2–25,6 s kurz sichtbar, direkt bevor die Folgen-Szene startet.
   Kunde fragen, welcher Begriff ins Bild soll.

### Sichtbarkeit — der wichtigste Befund
Die Animationen decken den Großteil der Sprechzeit ab. Nach der Regel „nur ohne
Animation“ werden sichtbar:

| Video | Seiten sichtbar (ganz/teils) | freie Fenster |
|---|---|---|
| 01 | 10 von 43 | 6 (0–1,3 · 5,3–6,2 · 10,2–10,9 · 17,0–18,9 · 24,2–25,6 · 46,2–46,8) |
| 02 | 7 von 25 | 6 |
| 03 | 11 von 41 | 7 |
| 04 | 28 von 63 | 11 |
| 05 | 12 von 37 | 7 |
| 07 | **0 von 18** | keine Lücke ≥ 0,5 s |

**Video 07 zeigt damit keinen einzigen Untertitel.** Die Spur ist eingebaut und
greift sofort, falls eine Ausnahme gewünscht ist (z. B. `minGapSec` senken oder
einzelne Szenen als nicht-sperrend markieren) — das ist eine Entscheidung für
David/Kunde, keine technische. Für 07 wurde deshalb **kein neues Overlay**
gerendert; die Lieferung vom 20.08. bleibt gültig.

Teilweise sichtbare Seiten zeigen Satzfragmente („speziell vor uns“, „Ost-West
und wenn ich“): Der Untertitel öffnet, sobald die Animation endet, und
verschwindet, sobald die nächste startet. Das ist die Konsequenz der Regel;
wer geschlossene Sätze will, muss Animationen kürzen oder die Regel lockern.

### Fehlendes Asset nachgebaut
`public/clients/sw-projektentwicklung/logo-stack-white.png` (und `logo-stack.png`)
lagen nur auf dem Zweit-MacBook; der erste Render brach an jeder Endkarte mit
404 ab. Beide aus der Kundendatei `Material/Logo/SW Projektentwicklung_Logo_Final-04.png`
nach dem Rezept vom 12.08. neu erzeugt (Trim, Höhe 600 → 1574 × 600 = 2,62:1,
Alpha = invertiertes RGB-Minimum, Sättigungsmaske 35 % → Sonne #FF8022, Rest
Weiß). Endkarten 01 und 04 als Still gegengeprüft: Logo steht wie zuvor.

### Pre-Delivery Review
Stills mit Guides an 17 Untertitel-Momenten über echter Footage
(`_intern/review/2026-09-03-untertitel/`): Text vollständig in der Bühne,
unter der Gesichts-Zone, lesbar auf Himmel wie auf dunkler Jacke. Frame 537 in
Video 01 (B-Roll, zwei Monteure) geprüft: Kopf des Monteurs rechts neben dem
Text, keine Überdeckung. Vollsequenz-Messung siehe Render-Bilanz unten.

### Render-Bilanz (2026-09-03)
Weg wie bei 03/05/07: PNG-Sequenz aus dem vorgebauten Bundle (`build-sw`,
`--public-dir=public-sw`, Props `transparent:true, footageFile:""`) → Sequenz
geprüft → ffmpeg ProRes 4444 (`yuva444p10le`, 16-bit-Alpha). Die bisherigen
Lieferungen `*_Overlay_ProRes4444.mov` bleiben unverändert liegen; die neuen
Fassungen heißen `*_Overlay-Untertitel_ProRes4444.mov`.

| Datei | Frames | Größe | Untertitel sichtbar |
|---|---|---|---|
| `01_Projekt-Gottwollshausen_Overlay-Untertitel_ProRes4444.mov` | 1606 | 406 MB | 144 Frames (4,8 s) |
| `02_Bifaziale_Solarmodule_Overlay-Untertitel_ProRes4444.mov` | 1080 | 289 MB | 195 Frames (6,5 s) |
| `03_BauerSolar-Modul_Overlay-Untertitel_ProRes4444.mov` | 1680 | 273 MB | 179 Frames (6,0 s) |
| `04_Flachdach-Erklaerung_Overlay-Untertitel_ProRes4444.mov` | 2385 | 513 MB | 610 Frames (20,3 s) |
| `05_Hotel-Smartino_Overlay-Untertitel_ProRes4444.mov` | 1478 | 273 MB | 326 Frames (10,9 s) |
| 07 Recruiting | — | — | 0 Frames → nicht neu gerendert |

Alle 1080 × 1920, 30 fps, ProRes 4444 mit Alpha. Bei Frame 0 auflegen.

**Vollsequenz-Messung (feste Grafik, Alpha ≥ 75 %), nur Untertitel-Frames:**
Box in allen fünf Videos **y 969–1015 px** (eine Zeile, Gesichts-Zone endet 864,
Safe Zone 1104), horizontal max. 78–1002 px (Safe Zone 54–1026). **Null
Verstöße, null Flacker-Kandidaten.** Keine Seite brach auf zwei Zeilen um.

Nebenbefund, nicht Teil dieses Auftrags: In den Szenen-Frames misst dieselbe
Pipeline Verstöße in 02 (72 Frames, Karten-Einflug von links über die
Safe-Zone-Kante bei 3,9 s), 03/04/05 (Endkarten-Logo über der Bühnenoberkante —
die dokumentierte Ausnahme). Bestand vom August, unverändert übernommen.

Hinweis 02: Root steht auf 35,967 s → 1080 Frames; die August-Lieferung hatte
1079 (Kürzung wegen schwarzem Schlussframe im *gebrannten* Bild). Für das
Alpha-Overlay ist der zusätzliche leere Frame ohne Belang.

### Offen
- Kunde: **54 Solarmodule** (Video 01) bestätigen → dann `anlage.moduleCount`.
- Kunde: **Tarifschaltgerät vs. Rundsteuer-Empfänger** (Video 01, Folgen-Karte).
- David/Kunde: Video 07 ohne jeden Untertitel akzeptieren oder Regel lockern?
- Satzfragmente an Szenengrenzen (siehe Sichtbarkeit) — gewollt oder Regel lockern?
- 2026-09-03 — Untertitel-Spur in allen sechs Kompositionen (nur in Animationslücken), Scribe-Timings für 01/05, Logo-Assets nachgebaut, fünf Overlays neu als *_Overlay-Untertitel_* geliefert; 07 hat keine Lücke.
