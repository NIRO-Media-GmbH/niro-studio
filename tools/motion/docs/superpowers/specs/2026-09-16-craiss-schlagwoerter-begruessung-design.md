# Craiss 4 Ads — Schlagwort-Chips + Begrüßungs-Intro 03 (Design)

Stand 2026-09-16, im Chat freigegeben. Anlass: Kundenfeedback Craiss vom 16.09.
(Untertitel raus, nur Schlagwörter; Headline „Viele Jahre, viele Geschichten“ passt
nicht; Begrüßungen am Anfang von 03 nicht als „Hallo“ erkennbar). Ersetzt für die
Lieferung den Untertitel-Look „Mix“ (Spec 2026-09-11); Mix und alter Look bleiben als
Umschalter in der Vorschau.

## Ziel

- Alle 5 Videos: keine Satz-Untertitel mehr, stattdessen wenige Schlagwort-Chips in
  korrektem Deutsch.
- Video 03: neues Intro — groß „HALLO“, darunter die Begrüßung in der jeweiligen
  Sprache, Flaggen-Wischer über das ganze Bild als Übergang zwischen den Sprachen, Titel-
  Chip „VIELE SPRACHEN. EIN TEAM.“. „VIELE JAHRE / VIELE GESCHICHTEN“ entfällt.
- Lieferung weiter als eine Alpha-Datei pro Video (`…_Alpha_Komplett_v2.mov`).

## Teil A — Schlagwort-Chips (01–05)

### Aussehen

Genau der rote Zitat-Chip aus Video 05 (`RedChip`): Laski Slab Bold 42 px, Laufweite 2,
weiß auf Craiss-Rot `#CD202C`, Radius 6, Innenabstand 14/34 px, Schatten, Versalien,
einzeilig. Einblendung: SOFT-Feder auf Skalierung 0,95 → 1, Deckkraft linear über
8 Frames; Ausblendung linear über 0,32 s. Horizontal mittig.

### Regeln

- **Inhalt:** kurz, korrektes Deutsch, höchstens 32 Zeichen und Chip-Breite ≤ 972 px
  (mit den Laski-Slab-Metriken gemessen: längster Chip 867 px); nur Gesagtes, keine neuen
  Fakten oder Zahlen; keine Dopplung mit Hook, Zitat-Chips, Flaggen, Schritten oder CTA
  (David-Regel 12.08.).
- **Timing:** Start = Beginn des ersten Worts, auf das sich der Chip bezieht
  (Scribe-Wortzeit aus dem Mix-Plan). Standzeit 1,5–3,5 s: Ende = Satzende, bei kurzen
  Sätzen bis 1,0 s nachhalten, bei langen nach 3,5 s kappen. Kein Überlapp mit den
  Sperrfenstern (`BLOCKED`), mindestens 0,3 s Abstand zum nächsten Chip.
- **Position:** Oberkante = größtes `y` der überdeckten Sätze im Mix-Plan (dort gegen Kinn
  und Hals geprüft), also `offsetY = y − 990`. Läuft ein Chip über einen Schnitt, wird die
  Folgeeinstellung mit geprüft.

### Liste (freigegeben 16.09.)

Zeiten = Start in Sekunden im jeweils aktuellen Schnitt; exakte Werte kommen aus der
Wortzeit des Ankerworts.

| Video | Start | Chip | Ankerwort · O-Ton |
|---|---|---|---|
| 01 | 8,50 | KINDERLEICHT – FÜR JUNG UND ALT | „kinderleicht“ · „Das ist kinderleicht gebaut. Keiner hat Probleme, egal ob jung oder alt.“ (steht bis Satzende 11,73) |
| 01 | 14,02 | WIR WEISEN DICH EIN | „eingewiesen“ · „Die Fahrer werden ja auch von uns eingewiesen …“ |
| 01 | 16,90 | FRAGEN? EINFACH ANRUFEN. | „Fragen“ · „Und bei Fragen können sie sich immer übers Telefon melden.“ |
| 02 | 6,74 | JEDEN TAG ZU HAUSE | „jeden“ · „… Arbeit Nahverkehr, jeden Tag zu Hause und ist besser für mich …“ |
| 02 | 11,54 | NAH- UND FERNVERKEHR | „Nah-“ · „Wir suchen Fahrer in Nah- und Fernverkehr.“ |
| 02 | 21,18 | ALLE INFOS PER TABLET | „Tablet“ · „Bei Dispo, bei Tablet geben alle, was machen …“ |
| 02 | ~31,2 | NEUER, SCHÖNER LKW | „neu“ · „Lkw ist neu. Schöner Lkw.“ |
| 02 | 44,06 | WERKSTATT: NUR 10 MINUTEN | „zehn“ · „… Chef Werkstatt sagen: ‚Muss warten zehn Minuten …‘“ |
| 02 | 48,12 | 24/7 ERREICHBAR | „24/7“ · „Wir sind 24/7 erreichbar für die Fahrer …“ |
| 03 | 12,86 + D | FRÜHER SELBST KEIN DEUTSCH | „früher“ · „Ich konnte früher selber kein Deutsch …“ |
| 03 | 25,24 + D | KOMMUNIKATION? KEIN PROBLEM. | „kein“ · „… von daher ist überhaupt kein Problem mit der Kommunikation.“ |
| 03 | 28,52 + D | RESPEKTVOLL UND LERNBEREIT | „respektvoll“ · „… freundlich und respektvoll ist und … lernbereit ist.“ |
| 03 | 32,50 + D | ÜBER 50 JAHRE BEI CRAISS | „Fünfzig“ · „Fünfzig Jahr hier in der Firma, über fünfzig Jahr.“ |
| 03 | 36,24 + D | TROTZ RENTE AM STEUER | „Rente“ · „Trotzdem, dass ich in Rente bin, möchte ich noch gern fahren …“ |
| 03 | 44,24 + D | DU BIST KEINE ZAHL. | „Du“ · „Du bist keine Zahl.“ (Ende vor CTA) |
| 04 | 6,68 | FAMILIENUNTERNEHMEN | „Familienunternehmen“ · „Wir sind ein Familienunternehmen.“ (nach Mühlacker-Chip) |
| 04 | 14,70 | KEIN 08/15-JOB | „0815“ · „… den Unterschied zum 0815-Arbeitsverhältnis“ |
| 04 | ~17,6 | BEI UNS ANKOMMEN | „schauen“ · „… wir schauen, dass die Leute auch bei uns ankommen.“ |
| 04 | ~30,3 | SO EINFACH STARTEST DU | „starten“ · „Wenn du bei uns starten möchtest, ist das ganz einfach:“ (Ende vor „KEIN LEBENSLAUF“) |
| 05 | 10,94 | KINDHEITSTRAUM LKW | „Bei“ · „Bei Kleine habe ich gesehen immer Lkw“ (Adrian, gemeint: seit der Kindheit) |
| 05 | 20,52 | WERKSTATT: NUR 10 MINUTEN | „zehn“ · „… muss warten zehn Minuten.“ |
| 05 | 32,68 | TROTZ RENTE AM STEUER | „Rente“ · „Trotzdem, dass ich in Rente bin …“ (Ende vor „BEI CRAISS PASST'S.“) |

`D` = Verlängerung der Begrüßungs-Montage in 03 (Teil B, gemessen nach dem Umbau).
Bewusst ohne Chip: „Ich liebe meinen Job“ (05, Hook sagt „ICH MAG MEINE ARBEIT.“),
„bewirb dich“ (02, CTA), „Arabisch, Polnisch“ (03, Titel deckt Sprachen ab),
„Telefonat“ (04, Schritt 2).

### Technik

- `RedChip` aus `projects/testimonial/Composition.tsx` nach `lib.tsx` verschieben;
  Video 05 nutzt ihn unverändert weiter.
- `captionMix/keywords.ts`: Schema `{ text, startSec, endSec, offsetY }` und
  `validateKeywords(list, blocked)` (Länge ≤ 32, Dauer 1,5–3,5 s, sortiert, Abstand
  ≥ 0,3 s, kein Überlapp mit Sperrfenstern). Tests `keywords.test.ts` (node:test wie
  `plan.test.ts`), dazu ein Test, der die echten `KEYWORDS` aller 5 Videos gegen ihre
  `BLOCKED` prüft.
- Pro Video `KEYWORDS` neben `BLOCKED` in `projects/<video>/CompositionSubtitled.tsx`
  und eine Ebene `<Video>KeywordLayer` (je Chip eine `Sequence`).
- Vorschau: `subtitleStyle: "schlagwort" | "neu" | "alt"`, Standard `schlagwort`;
  `VIDEOS[id].KeywordSubs`. `Craiss-Alpha-0X` erbt das.

## Teil B — Intro Video 03

### Ablauf

1. Start: Flaggen-Wischer Polen gibt Jakub frei — „DZIEŃ DOBRY“.
2. Wischer Ungarn → Victor — „SZIASZTOK“.
3. Wischer Rumänien → Adrian — „BUNĂ ZIUA“.
4. Wischer Tschechien → Jan — „ZDRAVÍM“.
5. Wischer Craiss-Rot → Thomas („Wir haben hier in der Dispo die verschiedensten
   Sprachen.“) — Titel-Chip „VIELE SPRACHEN. EIN TEAM.“.

Danach unverändert: Flaggen-Passage (Staffellauf HU/CZ/RO/LT), Schlagwort-Chips, CTA —
alle Zeiten + D.

### Elemente

- **HALLO:** Laski Slab Black, weiß, Schatten wie die Hook-Headline, deutlich größer
  (Richtwert 150 px), horizontal mittig. Steht vom ersten Frame bis zum Ende des roten
  Wischers und liegt über den Wischern.
- **Begrüßungs-Chip:** `RedChip`-Look direkt unter HALLO; der Text wechselt, während eine
  Flagge das Bild komplett deckt. Keine kleine Flagge im Chip.
- **Position:** HALLO + Chip im Bereich der alten Headline (Basis-y ≈ 940, Rumpfhöhe in
  den Ganzkörper-Shots); Gesicht und Hals in allen vier Shots frei (Still-Prüfung).
- **Titel-Chip:** `RedChip` über Thomas in der Höhe des Mix-Plans (cc-05: y 1150 →
  `offsetY` 160); erscheint mit dem Freigeben durch den roten Wischer, ist vor dem
  Kamerawechsel (alt 5,24 s, neu 5,24 + D) ausgeblendet. Für diesen Satz gibt es keinen
  weiteren Chip.

### Flaggen-Wischer

- Vollbild-Fläche in Flaggenfarben (Farbwerte wie `FLAG_RECTS` in `lib.tsx`): Polen
  weiß/rot, Ungarn rot/weiß/grün (waagrecht), Rumänien blau/gelb/rot (senkrecht),
  Tschechien weiß/rot mit blauem Dreieck von links, letzter Wischer einfarbig Craiss-Rot.
- Bewegung von rechts nach links (Richtung wie die Flaggen-Passage), weiches Easing ohne
  Überschwingen. Rund 0,4 s je Wischer: etwa 4 Frames Einlauf, mindestens 2 Frames voll
  deckend mit dem Schnitt dazwischen, etwa 4 Frames Auslauf. Der erste Wischer (Polen)
  startet voll deckend auf Frame 0 und läuft nur aus.
- Voll deckende Flächen ohne CSS-Border (Alpha-Haarlinien-Falle); Flaggen aus
  überlappenden Rechtecken.
- Synchron zu den Schnittframes des neuen Exports (per Szenenerkennung gemessen).
- **Harte Regel:** Während eine Person spricht, deckt kein Wischer ihr Bild (Wortzeiten
  aus der Quelle, per Pegel gegengeprüft; Scribe-Wortenden hängen nach). Ein- und Auslauf
  richten sich nach der verfügbaren Stille (mindestens 2 Frames). Beim roten Wischer
  bleibt Thomas' Clip unverändert: Er spricht 3 Frames nach dem Schnitt, also läuft der
  rote Wischer lang über Jans stilles Ende ein und höchstens 2 Frames aus.

### Umbau in Resolve (nur Kopie)

- Projekt `01_Projekt_4_Ads`. Freigabe 16.09.: **Schreiben nur in Kopien.** Vor jedem
  schreibenden Skript `project.GetName()` lesen und nennen; nie abspielen lassen, während
  geschrieben wird; am Ende Timeline und Media-Pool-Bin des Users zurücksetzen.
- Kopie: `DuplicateTimeline("Claude 03 Begrüßung 2026-09-16 <HHMM>")` von
  `03_Viele_Jahre_Viele_Geschichten_V3`. Das Original bleibt unberührt.
- Quell-Stellen: FCPXML-Export der V3-Timeline nach
  `<Charge 03>/_intern/resolve/` — der Compound Clip „Compound Clip 1“ ist per API nicht
  lesbar, das XML nennt Quelle und Quell-In/Out der vier Shots.
- Neue Shots: vorne und hinten so viel Luft, wie Ein- und Auslauf der Wischer brauchen,
  plus 1 Frame Puffer zur Sprache; die Luft muss im Quellmaterial ruhig sein (Standbild-
  Prüfung, kein Blickwechsel oder Gang aus dem Bild). Richtwert D ≈ 23 Frames (0,92 s).
- Platz vorn schaffen, ohne einen Clip hinter der Montage zu verändern: zuerst auf der
  Kopie testen, ob ein früherer Start-Timecode die Clip-Positionen hält. Wenn nicht: der
  User verschiebt in der Kopie alles geschlossen um D Frames nach rechts (ein Handgriff).
- In der Kopie:
  - Compound Clip (V1/A1) nur deaktivieren.
  - Neue Bild-Clips auf V3 (dort vorne frei, unter der Adjustment-Ebene V5).
  - Ton nur über die gesprochenen Wörter auf A2 „Stimme B“ (leer), damit der Interviewer
    in der Luft nicht zu hören ist.
  - Musik A3 vorne um D aus demselben Song ergänzen (Quelle direkt vor dem bisherigen
    Einstieg, nahtlos).
  - Swoosh je Wischer (`florianreichelt__swishes-and-swooshes.mp3` wie in der Flaggen-
    Passage) auf einer leeren SFX-Spur.
  - Alte Overlay-Spur V6 und `…_Alpha_Komplett_v1` (V9) aus; Alpha v2 auf eine neue
    oberste Spur.
- Grading: Ort des Gradings klären (Compound-Knoten, Adjustment V5 ab 0 s, Clip-Knoten),
  neue Shots per `CopyGrades` bzw. Still-Vergleich an die alte Montage angleichen; der
  Vorlauf vor der alten Position 0 muss mit abgedeckt sein.
- Readback nach jedem Schritt (Items, Offsets, Enabled-Status).
- Danach: Export „ohne Animation“ der Kopie (Quick Export) nach
  `Material/Video/ohne-Animation/` + H.264-Proxy; Remotion-Längen und alle 03-Zeiten nach
  der Montage um D verschieben (Flaggen-Passage, Sperrfenster, Chips, CTA).

### Technik Remotion

- `src/clients/craiss/intro/`: `wipeTiming.ts` (Schema der Layout-Datei, Panel-Versatz je
  Frame), `FlagWipe.tsx` (Vollbild-Fläche je Land + Craiss-Rot), `GreetingIntro.tsx`
  (HALLO, Begrüßungs-Chip, Wischer-Folge). Zeiten aus
  `projects/viele-jahre/intro-layout.json`, das der Resolve-Umbau erzeugt.
- `viele-jahre/Composition.tsx`: `hook` durch `intro` (Schema mit Schnittframes, Texten,
  Titel-Chip) ersetzen; Footage-Quelle und `VIDEO_SECONDS` auf den neuen Export.
- Vorschau 03: neue Quelle und Länge.

## Teil C — Prüfung und Lieferung

- `npx tsc --noEmit`; Tests (`keywords.test.ts`, bestehende `captionMix`-Tests).
- Vorschau `Craiss → Vorschau-Neu` für 01–05 → Abnahme durch den User.
- Pre-Delivery-Review: Kontaktbogen je Chip (Start/Mitte/Ende) mit Face- und Safe-Zone;
  Intro 03 frameweise um jeden Schnitt (Sprecher beim Sprechen frei, Schnitt verdeckt).
- Renders `0X_<Name>_Alpha_Komplett_v2.mov`: ProRes 4444 mit Alpha, 2160×3840, 25 fps,
  nach `Ergebnisse/Renders/`, mit `--public-dir=public-craiss` und freiem `--port`;
  flicker-check und Alpha-Stills.
- Einsetzen in Resolve nur in Kopien (03: die Umbau-Kopie; 01/02/04/05: nach Rückfrage
  eigene Kopien oder durch den Cutter). NAS-Ablage nur nach Rückfrage.
- `Protokoll.md` je Charge.

## Nachtrag Umsetzung (16.09.)

- **Resolve-Kopie:** „Claude 03 Begrüßung 2026-09-16 1259". Platz vorn per Handgriff des Users (Cmd+A, +N) — der
  Start-Timecode-Weg verschiebt die Clips mit. Der Handgriff lieferte 33 statt 35 Frames → **D = 33 Frames (1,32 s)**,
  roter Wischer mit 4 statt 6 Frames Einlauf; Montage 101 Frames, Video 1324 Frames (52,96 s).
- **Shots im Compound Clip des Originals** hatten Zoom 1,05 plus kleine Pan/Tilt-Werte und Clip-Lautstärken
  (+9,1 / +3,8 / +9,7 / +4,5 dB) — aus dem OTIO-Export gelesen und auf die neuen Clips übertragen.
- **Look:** kam aus der Color-Gruppe „sony3" (nicht aus dem Clip-Knoten) → neue Shots in „sony3" gehängt.
- **Ausschnitt:** Das Original hatte Dynamic Zoom (Standard, 1,25× → 1,0×) auf dem Compound Clip → neue Shots
  ebenfalls zu einem Compound Clip („Claude Begrüßung Montage", ohne Gruppe) mit Dynamic Zoom; Abweichung zum Original
  per Bildvergleich 0–2,5 %.
- Prüfskripte und Messungen: `projects/…/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/` (r1–r8, r7b–r7d,
  `zoom_messung.json`), Kontaktbögen in `_intern/review/`.

## Nicht Teil davon

Änderungen am Schnitt außer der Begrüßungs-Montage in 03; Tonmischung und Pegel;
Abwechslung zwischen den Videos (Cutter); Schreiben in bestehende Timelines.
