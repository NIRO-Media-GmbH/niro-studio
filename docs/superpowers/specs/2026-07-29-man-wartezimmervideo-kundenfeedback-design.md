# MAN Wartezimmervideo — Kundenfeedback Runde 1 (Design)

**Datum:** 2026-07-29
**Charge:** `projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/`
**Anlass:** Feedback MAN zur ausgelieferten Ton-Fassung (16:9-Master, 142 s)

MAN hat die erste Fassung freigegeben („gefällt uns schon sehr gut") und
13 Änderungswünsche geschickt. Fünf betreffen den Bildschnitt, sieben die
Grafikebene, einer ist eine zusätzliche Fassung.

## 1. Grundannahme: die Tonspur bleibt

David tauscht in Premiere nur Bilder, ohne Längen zu ändern. Damit bleibt
`_intern/final-16x9/timeline.json` (12 Blöcke, 134,0 s) unverändert gültig, und
sämtliche Animations-Timings im sync-plan behalten ihre Sekundenwerte. Es wird
weder neu transkribiert noch die Timeline neu abgeleitet.

**Prüfschritt vor der Umsetzung:** Die neue 9:16-Datei per ffprobe gegen die
alte vergleichen (Dauer, Framezahl, Audio-Stream). Weicht die Dauer um mehr als
±0,04 s (1 Frame) ab, ist die Annahme verletzt — dann Stopp und Rückfrage, statt
die Grafik auf eine verschobene Tonspur zu legen.

## 2. Schnitt (David, Premiere) — nicht Teil dieser Umsetzung

| TC | Wunsch | Kontext in der Timeline |
|---|---|---|
| 0:11 | Szene unterm Truck raus | Spotlight-Lücke 1 (9,5–22,3 s), kein O-Ton |
| 0:47 | Szene unterm Truck raus | Tobi-Block (44,3–50,2 s), Ton läuft weiter |
| 1:33 | Szene unterm Truck raus | Louis-Block (89,9–94,3 s) |
| 2:03 | andere Produktszene einbauen | Ciattei-Block (118,6–133,6 s) |
| 2:06 | Szene unterm Truck raus | Ciattei-Block |

## 3. Texte (Generator `build_sync_plan.py`)

Alle sichtbaren Texte entstehen im Generator und landen über `sync-plan.json` in
der Komposition. Es wird an keiner Stelle Text in `Composition.tsx` gepflegt.

| Element | Zeit | Ist | Soll |
|---|---|---|---|
| Takeaway Block 2 | 22,7 s | `MEHR ALS KOLLEGEN. EINE **FAMILIE**.` | `**FAMILIÄRES** UMFELD` |
| Takeaway Block 5 | 44,7 s | `GLEICHE **AUGENHÖHE**. KEINE HIERARCHIEN.` | `AUF **AUGENHÖHE**. FLACHE HIERARCHIESTUFEN.` |
| Plakette Block 7 | 59,0 s | Rolle `Azubi Teilelager & Teileverkauf` | `Teilelager & Teileverkauf` |
| Headline Kapitel 3 | 89,9 s | `FASZINATION **NUTZFAHRZEUG**` | `FASZINATION **NUTZFAHRZEUGE**` |
| Takeaway Block 10 | 104,3 s | `GROSSE MASCHINEN. GROSSER **EINDRUCK**.` | `GROSSE FAHRZEUGE. **GROSSES BEWEGEN**.` |

„Azubi" fällt ausschließlich bei Nico. Louis, Lara und Hannes behalten
`Azubi Nutzfahrzeugmechatronik` — MAN hat nur Nico genannt, und die
Azubi-Perspektive ist für einen Recruiting-Film ein Aktivposten.

Die Breitenprüfung des Generators (fontTools gegen 964 px nutzbare Spalte) muss
für die zwei neuen Takeaways erneut laufen. `AUF AUGENHÖHE. FLACHE
HIERARCHIESTUFEN.` ist der bislang längste Takeaway und der wahrscheinlichste
Kandidat für die Ausnahmestufe 46 px.

## 4. Löwe raus

MAN darf den Löwen nicht verwenden. Er muss an allen drei Stellen weg:

1. dauerhaft dunkel hinter dem Fenster (ganze Laufzeit, `Composition.tsx:1661`)
2. rot in beiden Spotlights (0:09,5–0:22,3 und 1:04,6–1:29,9, `:1406`)
3. weiß auf der Endcard (`:1467`)

Die Komponente `Loewe169` (`:1029`) und die PNGs `loewe-links-*.png` entfallen
ersatzlos, ebenso der Schlüssel `loewe` im sync-plan.

**Ersatz (Entscheidung David):** kein neues Motiv. Die Spotlights tragen allein
der Werkzeug-Regen plus die bestehende Licht-Choreografie (Abdunklung,
Vignette, roter Glow, Fenster-Glide zur Mitte).

Damit wird der Werkzeug-Regen vom Beiwerk zum einzigen Motiv und muss kräftiger
werden: Deckkraft von `0,04–0,09` auf `0,12–0,18`, Größenkorridor von
`70–180 px` auf `110–260 px`, Anzahl 9 → 12. Die Zone bleibt die Grafikfläche
links (x 0–1100). Die Werte sind ein Startpunkt, kein Dogma — sie werden am
Testframe kalibriert.

**Bekanntes Risiko:** Die sprechfreie Lücke bei 1:04,6–1:29,9 dauert 25,3 s und
lebte bisher wesentlich vom roten Löwen. Ob der verstärkte Werkzeug-Regen sie
allein trägt, entscheidet sich am Testframe — nicht im Endrender. Falls die
Fläche leer statt ruhig wirkt, ist die naheliegende Reserve der MAN-Halbbogen
aus `MANlogoWeiss.png` als großes angeschnittenes Artwork (freigabesicher, da
reiner Schriftzug ohne Löwen).

## 5. Endcard: Standort-Abbinder wird CTA

Bisher: `IHR **MAN SERVICE-TEAM**`, Logo links, weißer Löwe rechts, 135,0–140,0 s.

Neu (Variante A), Layout auf 1920×1080:

- **Links** (auf dem Versatz-Panel): MAN-Logo als Bilddatei, darunter der Claim
  `GROSSES BEWEGEN **MIT MAN**`, roter Trennstrich, darunter `JETZT BEWERBEN`.
- **Rechts** (der Platz, den der Löwe räumt): QR-Code als weiße Platte mit
  dunklen Modulen, Kantenlänge 480 px, darunter das Ziel als Klartext
  `JOBS.MAN.EU`.

**QR-Ziel:** `https://jobs.man.eu/` — die offizielle Jobbörse der MAN Truck &
Bus SE und Truck & Bus Deutschland GmbH. Kurze URLs ergeben grobe Raster; die
Scan-Distanz skaliert grob mit dem Zehnfachen der Kantenlänge, also braucht ein
Wartezimmer mit ~3 m Sitzabstand rund 30 cm auf dem Schirm — auf einem
55-Zoll-Gerät entspricht das den 480 px im 1920er Bild. Die lange
Karriereseiten-URL (`man.eu/de/de/…/grosses-bewegen-mit-man.html`) verlinkt
ohnehin auf dieselbe Jobbörse und würde das Raster nur verdichten.

Der Pfad dieser Karriereseite bestätigt nebenbei den Wortlaut: „Großes bewegen
mit MAN" ist MANs eigener Employer-Claim. Zusammen mit dem neuen Takeaway bei
1:45 klammert er das Video.

**Standzeit:** Der Hero steht künftig 8,0 s statt 5,0 s (135,0–143,0 s), damit
ein QR im Wartezimmer tatsächlich gescannt und nicht nur gesehen wird. Der
Ausklang in die Dunkelfläche verschiebt sich auf 143,0–145,0 s, die
Master-Dauer von 142,0 s auf 145,0 s (3550 → 3625 Frames). Die Loop-Naht bleibt
das Konstruktionsprinzip: Frame 3624 entspricht Frame 0.

**Kein Berufstitel auf der Endcard**, damit greift die m/w/d-Pflicht hier nicht.
Sobald ein Titel dazukommt, muss `(m/w/d)` daran.

**QR-Erzeugung:** einmalig als Asset nach `tools/motion/public/clients/man/wz/`
gerendert, nicht zur Laufzeit. Fehlerkorrektur-Level M, Quiet Zone 4 Module.
Der erzeugte Code wird vor dem Einbau mit einem echten Handy gegen die Ziel-URL
geprüft — ein QR, der im Wartezimmer ins Leere führt, ist schlimmer als keiner.

## 6. Stumme Fassung mit Untertiteln

Der Flag `fassung: "stumm"` existiert bereits und schaltet das Video stumm
(`Composition.tsx:1774`), bewirkt bei den Texten aber nichts — `endeStumm` und
`endeTon` sind im aktuellen Plan überall identisch. Die stumme Fassung ist bis
heute nie gerendert worden.

MAN will eine Fassung für stumme Wiedergabe. Untertitel laufen deshalb
**klassisch unten im Videofenster** (Entscheidung David), nicht auf der
Grafikfläche:

- **Zone:** unteres Fensterdrittel, Fenster HD x 1200–1740 / y 60–1020,
  40 px Innenabstand → 460 px Textbreite.
- **Typo:** MAN Global Regular ~30 px, Zeilenhöhe 1,25, weiß, zentriert,
  Gemischtschreibung (keine Versalien — Fließtext, nicht Headline).
- **Umbruch:** maximal 2 Zeilen, ~32 Zeichen je Zeile, minimale Standzeit 1,2 s,
  Segmentgrenzen an Satzzeichen und Sprechpausen.
- **Lesbarkeit:** dezenter dunkler Verlauf unter dem Band, damit heller Footage
  den Text nicht frisst. Bewusst zurückhaltend — Davids Linie ist „sehr clean";
  die Stärke wird am Testframe festgelegt.
- **Quelle:** Wort-Timings aus `_intern/final-16x9/transcript.scribe.json`, die
  Wortlaute aus `timeline.json`. Die Segmentierung erzeugt der Generator, damit
  Untertitel und Takeaways aus derselben Wahrheit stammen.

**Die Lara-Textsperre entfällt.** Der Satz „Da habe ich direkt gesagt: muss ich
mich hier bewerben" (101,0–103,8 s) war gesperrt, weil das Video ausdrücklich
ohne Recruiting-Botschaft geplant war. Mit dem CTA ist das Video ein
Recruiting-Film; die Sperre wäre jetzt eine sinnentstellende Lücke mitten im
Satz. `endeStumm` für Takeaway 9 zieht entsprechend auf das Blockende nach.

**Bekanntes Risiko:** In der stummen Fassung stehen künftig Headline, Takeaway,
Plakette und Untertitel gleichzeitig im Bild. Das ist deutlich mehr Text als in
der Ton-Fassung. Wird am Testframe geprüft; falls es zu dicht wird, ist die
Takeaway-Ebene der Kandidat zum Ausdünnen, nicht der Untertitel — den hat MAN
bestellt.

## 7. Nicht Teil dieser Runde

- **Musik** legt David in Premiere unter die Ton-Fassung (Akt-Wechsel 0:17 und
  1:16), Shortlist liegt in `Ergebnisse/Musik-Empfehlungen.md`.
- **MAN-Freigabe 2023er Material (Ciattei):** gilt als erteilt. MAN hat den
  Block bei 2:03 und 2:06 kommentiert und dabei nur Szenen beanstandet, nicht
  die Person. Der Fallback-Flag `ohneCiattei` bleibt vorhanden.

## 8. Lieferung

Je Fassung vier Dateien nach `Ergebnisse/Renders/`, wie bei der ersten Runde:
ProRes 422 HQ in 1920×1080 und 3840×2160, dazu je ein H.264-Preview (CRF 18).
Die 4K-Fassung entsteht über `--scale=2`; das Videofenster misst dann exakt
1080×1920 und trifft die ProRes-Arbeitskopie pixelgenau.

Acht Dateien sind zusammen rund 12 GB. Falls die stumme Fassung nur auf einem
Wartezimmer-Schirm läuft, reicht dort HD — das entscheidet David vor dem
Rendern.

## 9. Reihenfolge

1. David schneidet, liefert die neue 9:16-Datei.
2. ffprobe-Abgleich gegen die alte Datei (Gate: Dauer identisch).
3. Generator-Änderungen (Texte, Untertitel-Segmente, Werkzeug-Werte, Endcard).
4. Komposition (Löwe raus, Endcard neu, Untertitel-Ebene, Master 145 s).
5. Testframes — Look-Review mit David, insbesondere Spotlight-2 ohne Löwe,
   neue Endcard, Untertitel-Dichte in der stummen Fassung.
6. Erst nach Freigabe rendern.
