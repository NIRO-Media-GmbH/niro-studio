# SFX-Plan Grafikebene — Taxodia-Erklärvideo „Der Taxodia-Weg“

Stand 15.09.2026 · nur offline geplant und gemessen, nichts in Resolve geschrieben · Daten: `sfx_plan.json`

## Kurzfassung

- **39 Platzierungen** auf 19 der 20 V4-Elemente (ohne eigenes SFX: `bauchbinde-flammann`, siehe unten) · A4 „SFX 1“: 35 · A5 „SFX 2“: 4 (nur Überlappungen) · keine Überlappung je Spur.
- **17 Dateien** aus Whoosh/Fast, Whoosh/Slow, UI, Click, Riser (keine Intro-, Drone-, Glitch-, Impact-Dateien).
- **Pegel:** Clip-Gain −26,4 … −2,9 dB → SFX-Peaks −28,1 … −17,1 dBFS; während Sprache höchstens −26,0 dBFS.
- **Prüfmischung:** −19,1 LUFS mit und ohne SFX (Beitrag 0,0 LU), True Peak −2,5 dBTP unverändert, 0 übersteuerte Samples.

## Klangfamilie: „Luft statt Effekt“

Rauschbasierte, luftige Bewegungsgeräusche für alles, was sich bewegt, dazu drei sehr kurze, leise Klick-Typen für Dinge, die erscheinen. Keine tonalen Jingles, keine Booms, keine Riser. Die Auswahl ist gemessen (`analyse/sfx_metriken.json`, 205 Dateien) und per Spektrogramm geprüft (`analyse/spektren/`), nicht nach Namen getroffen.

| Rolle | Datei(en) | Messbefund |
|---|---|---|
| Vollbild-Wipes (Flashes, Karten, Blenden, Taxodia-Weg, Endcard) | Whoosh 2-1 … 2-5 | eine Serie, 5 Varianten: Swell ab 0,25 s → harter Stopp bei 0,48 s → Luft-Ausklang bis 0,8 s; Rauschen (Flachheit 0,16–0,27), Tonanteil ≤ 0,05 |
| Iris öffnet in den Take | Woosh_AI004 / Riser Woosh_AI005, abwechselnd | linearer Luft-Swell mit hartem Stopp, passt zur beschleunigenden Iris (EASE_IN); kaum Bass; MP3 ohne Priming-Versatz |
| Bauchbinden und Faktenkarten | Ninja Jump 5 / 1 / 6 | reine Luft-Swishes (~0,3 s), ohne Tonhöhenverlauf und ohne Bass |
| Pins, Stationen des Taxodia-Wegs | Pop Notification, Menu Select, Smartphone UI Click Single | 0,1–0,15 s; drei Varianten, damit sich gleiche Ereignisse nicht maschinell wiederholen |
| „online“-Chip und URL-Pille | Digital Interface Notification | gleicher kurzer Blip für beide grünen Pillen (gleiches Design, gleicher Klang) |
| Titel und Endcard-Logos | Shimmer and fast airy whoosh | der einzige Shimmer, weich (Swell 0,43 s, Ausklang 1 s): Klammer von Anfang und Ende |
| Karten-Zoom Ilshofen | Cinematic Whoosh (19) | langer, glatter Whoosh (Peak 0,92 s, Ausklang 1,8 s) zum 1,8-s-Zoom |
| 50-km-Kreis; Iris + Bauchbinde Flammann | Whoosh Airy Motion Soft Transition | weiches Anschwellen (Peak 0,65 s), ruhiger Ausklang |

**Verworfen:**
- Impacts: 83–100 % der Energie unter 150 Hz, reine Booms.
- Tonale UI-Akkorde und Chimes: UI Approval Swipe, Task Completed, Light Button, Bubbly Bells.
- 8-Bit-, Game- und Error-Sounds.
- Noise-Uplifter (Riser 1–5, Riser_AI001, Sweeping Riser) sowie Stutter-, Glitch-, Horror- und Braam-Riser.
- Metallische Reverse-Cymbals.
- Einzeldateien:
  - Fabric Whoosh Swift: Peak kommt von einem 50-Hz-Plopp, dadurch Crest 19 dB – bei −26 dBFS nur −45 LUFS.
  - Ninja Jump 3: steigende Tonlinie.
  - UI Maximize: tonaler Chirp.
  - The Title Reveal: Tremolo-Rumpeln.

## Timing

- **Ereignis-Frame** = Element-Start aus `Grafikebene.tsx` + lokaler Animations-Frame aus `vollbild.tsx`/`grafik-basis.tsx`; Wipe-in/Iris gegen `alpha_v2.json` geprüft.
- **Whoosh/Swell:** Hüllkurven-Maximum bzw. harter Stopp liegt auf
  - Vollbild-Wipe: ~64 % Deckung (lokal 1,5), Flash: Mitte des 3-Frame-Aufblendens;
  - Karten: schnellster Teil des Wipes (lokal 1,5), Titel: lokal 1,7 = Zählzeit der Musik;
  - Iris: zwischen letztem sichtbarem Frame und klarem Bild (dauer − 0,5), Zoom: höchste Geschwindigkeit (lokal 40).
- **Klicks:** Attack (−3 dB) exakt auf dem Frame, ab dem Pin/Station/Chip/Pille sichtbar ist.
- **Quell-In** ganzzahlig in Frames. Landung −0,25 … +0,75 Frames (Ton eher minimal spät als früh), gemessen −0,06 … +0,69.

## Pegel

- **Unter Sprache:** Ziel −26 dBFS Sample-Peak. Ausnahmen: Iris-Öffnungen −28, Iris+Bauchbinde Flammann und Pin 2 −27.
  - Harte Grenze: SFX-Peak ≤ −26 dBFS in jedem Frame mit hörbarer Sprache. Die Sprachmaske kommt aus dem Audio (Frame > −40 LUFS), nicht aus den Wortgrenzen.
  - Zusätzlich liegt in Frames mit deutlicher Sprache (> −32 LUFS) der SFX-Peak immer unter dem Sprach-Peak. Wortfugen dürfen die SFX tragen.
- **Sprachfrei:**
  - Kapitel- und CTA-Blenden −18 dBFS, Endcard-Wipe −19, Flash 2 −20, Iris Ilshofen −22, Flash 1 (Pause ohne Musik) −24.
  - Titel-Shimmer −17, Endcard-Shimmer und URL-Blip −18.
- **Gain** = Ziel − Peak des tatsächlich genutzten Abschnitts inkl. Fades. Einmal durch die Sprachgrenze begrenzt: Iris Karte Taxodia (−26,1 statt −24, wegen „Wir“).

## Platzierungen

Ereignis-TC = Timeline ab 0 (in Resolve 01:MM:SS:FF). `rec` = Frame, an dem die SFX-Datei beginnt. Peak = SFX-Sample-Peak nach Gain. M = lautestes 400-ms-Fenster der SFX (LUFS).

| # | Ereignis-TC | rec | Spur | Element | Ereignis | SFX | In s | Dauer f | Gain dB | Peak dBFS | Fade in/out | Klasse | M |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00:02:11 | 54 | A4 | flash-fachkraeftemangel | Flash rein (Aufblenden 3 Frames) | Whoosh 2-4 | 0,16 | 20 | −19,4 | −24,0 | 2/1 | frei | −38,2 |
| 2 | 00:09:09 | 227 | A4 | flash-quereinsteiger | Flash rein (Aufblenden 3 Frames) | Whoosh 2-2 | 0,16 | 21 | −19,0 | −20,0 | 2/1 | frei | −33,8 |
| 3 | 00:14:23 | 362 | A4 | titel | Titelkarte Wipe + Rise | Shimmer and fast airy whoosh | 0,12 | 36 | −11,2 | −17,1 | 2/1 | frei | −26,1 |
| 4 | 00:19:06 | 480 | A4 | bauchbinde-ludwig | Bauchbinde Wipe + Rise | Ninja Jump 5 | 0,0 | 9 | −21,3 | −26,0 | 1/1 | Sprache | −40,0 |
| 5 | 00:22:03 | 548 | A4 | karte-ilshofen | Vollbild Wipe rein (weißer Grund) | Whoosh 2-3 | 0,24 | 19 | −25,6 | −26,0 | 2/1 | Sprache | −41,2 |
| 6 | 00:22:12 | 562 | A5 | karte-ilshofen | Pin Ilshofen erscheint | Pop Notification | 0,04 | 3 | −20,8 | −26,0 | 0/1 | Sprache | −36,7 |
| 7 | 00:23:17 | 579 | A4 | karte-ilshofen | Karten-Zoom 1→2,7 (lokal 18–62) | Cinematic Whoosh (19) | 0,4 | 36 | −23,1 | −26,1 | 2/1 | Sprache | −37,4 |
| 8 | 00:25:03 | 620 | A4 | karte-ilshofen | 50-km-Kreis zeichnet sich | Whoosh Airy Motion Soft Trans. | 0,32 | 24 | −24,4 | −26,0 | 2/6 | Sprache | −39,1 |
| 9 | 00:27:17 | 681 | A4 | karte-ilshofen | Iris öffnet in den Take | Woosh_AI004.mp3 | 0,36 | 16 | −2,9 | −22,1 | 2/3 | frei | −35,8 |
| 10 | 00:41:02 | 1025 | A4 | bauchbinde-hein | Bauchbinde Wipe + Rise | Ninja Jump 1 | 0,0 | 8 | −21,1 | −26,0 | 1/1 | Sprache | −41,9 |
| 11 | 01:06:15 | 1663 | A4 | blende-taxodia | Vollbild Wipe rein (Kapitel „Die Online-Steuerfachschule“) | Whoosh 2-1 | 0,36 | 16 | −17,9 | −18,1 | 2/1 | frei | −32,7 |
| 12 | 01:08:11 | 1704 | A4 | blende-taxodia | Iris öffnet + Bauchbinde Flammann 4 Frames später | Whoosh Airy Motion Soft Trans. | 0,32 | 24 | −25,4 | −27,0 | 2/6 | Sprache | −40,1 |
| 13 | 01:14:13 | 1858 | A4 | karte-taxodia | Vollbild Wipe rein (Karte Visselhövede–Ilshofen) | Whoosh 2-5 | 0,24 | 17 | −23,0 | −26,1 | 2/1 | Sprache | −41,1 |
| 14 | 01:14:20 | 1870 | A5 | karte-taxodia | Pin Visselhövede erscheint | Pop Notification | 0,04 | 3 | −20,8 | −26,0 | 0/1 | Sprache | −36,7 |
| 15 | 01:15:05 | 1880 | A4 | karte-taxodia | Pin Ilshofen erscheint | Menu Select | 0,04 | 3 | −21,8 | −27,1 | 0/1 | Sprache | −41,1 |
| 16 | 01:16:18 | 1918 | A4 | karte-taxodia | Chip „online“ poppt auf | Digital Interface Notification | 0,04 | 6 | −21,4 | −26,0 | 0/1 | Sprache | −38,3 |
| 17 | 01:19:06 | 1970 | A4 | karte-taxodia | Iris öffnet in den Take | Riser Woosh_AI005.mp3 | 1,44 | 15 | −24,4 | −26,1 | 2/3 | frei | −38,0 |
| 18 | 01:40:12 | 2511 | A4 | software | Faktenkarte Wipe + Rise (unten rechts) | Ninja Jump 6 | 0,0 | 9 | −22,1 | −26,0 | 1/1 | Sprache | −41,8 |
| 19 | 01:55:07 | 2881 | A4 | bachelor-professional | Faktenkarte Wipe + Rise | Ninja Jump 5 | 0,0 | 9 | −21,3 | −26,0 | 1/1 | Sprache | −40,0 |
| 20 | 02:08:23 | 3218 | A4 | taxodia-weg | Vollbild Wipe rein (Der Taxodia-Weg) | Whoosh 2-2 | 0,24 | 19 | −25,0 | −26,0 | 2/1 | Sprache | −39,8 |
| 21 | 02:09:07 | 3232 | A5 | taxodia-weg | Station 1 Einstiegskurs setzt | Smartphone UI Click Single | 0,04 | 4 | −20,3 | −26,0 | 0/1 | Sprache | −41,2 |
| 22 | 02:13:02 | 3327 | A4 | taxodia-weg | Station 2 Teil I setzt | Menu Select | 0,04 | 3 | −20,8 | −26,1 | 0/1 | Sprache | −40,1 |
| 23 | 02:14:22 | 3372 | A4 | taxodia-weg | Station 3 Teil II setzt | Smartphone UI Click Single | 0,04 | 4 | −20,3 | −26,0 | 0/1 | Sprache | −41,2 |
| 24 | 02:16:19 | 3419 | A4 | taxodia-weg | Station 4 Prüfung setzt | Pop Notification | 0,04 | 3 | −20,8 | −26,0 | 0/1 | Sprache | −36,7 |
| 25 | 02:23:14 | 3578 | A4 | taxodia-weg | Iris öffnet in den Take | Woosh_AI004.mp3 | 0,36 | 16 | −8,9 | −28,1 | 2/3 | Sprache | −41,8 |
| 26 | 02:26:03 | 3651 | A4 | kosten | Faktenkarte Wipe + Rise | Ninja Jump 1 | 0,0 | 8 | −21,1 | −26,0 | 1/1 | Sprache | −41,9 |
| 27 | 02:33:07 | 3829 | A4 | blende-online | Vollbild Wipe rein (Kapitel „Online lernen“) | Whoosh 2-4 | 0,32 | 16 | −13,4 | −18,0 | 2/1 | frei | −32,5 |
| 28 | 02:35:14 | 3878 | A4 | blende-online | Iris öffnet in den Take | Riser Woosh_AI005.mp3 | 1,44 | 15 | −26,4 | −28,1 | 2/3 | Sprache | −40,0 |
| 29 | 03:13:16 | 4840 | A4 | monitoring | Faktenkarte Wipe + Rise | Ninja Jump 6 | 0,0 | 9 | −22,1 | −26,0 | 1/1 | Sprache | −41,8 |
| 30 | 03:18:17 | 4966 | A4 | abrechnung | Faktenkarte Wipe + Rise | Ninja Jump 5 | 0,0 | 9 | −21,3 | −26,0 | 1/1 | Sprache | −40,0 |
| 31 | 03:38:05 | 5452 | A4 | blende-ergebnis | Vollbild Wipe rein (Kapitel „Das Ergebnis“) | Whoosh 2-3 | 0,32 | 17 | −17,6 | −18,0 | 2/1 | frei | −33,3 |
| 32 | 03:39:24 | 5488 | A4 | blende-ergebnis | Iris öffnet in den Take | Woosh_AI004.mp3 | 0,36 | 16 | −8,9 | −28,1 | 2/3 | Sprache | −41,8 |
| 33 | 04:00:08 | 6005 | A4 | blende-kanzleien | Vollbild Wipe rein (CTA „Für Kanzleien“) | Whoosh 2-5 | 0,32 | 15 | −15,0 | −18,1 | 2/1 | frei | −33,3 |
| 34 | 04:02:06 | 6045 | A4 | blende-kanzleien | Iris öffnet in den Take | Riser Woosh_AI005.mp3 | 1,44 | 15 | −26,4 | −28,1 | 2/3 | Sprache | −40,0 |
| 35 | 04:14:00 | 6348 | A4 | blende-quereinsteiger | Vollbild Wipe rein (CTA „Für Quereinsteiger“) | Whoosh 2-1 | 0,36 | 16 | −17,9 | −18,1 | 2/1 | frei | −32,7 |
| 36 | 04:15:09 | 6373 | A4 | blende-quereinsteiger | Iris öffnet in den Take | Woosh_AI004.mp3 | 0,36 | 16 | −8,9 | −28,1 | 2/3 | Sprache | −41,8 |
| 37 | 04:25:13 | 6635 | A4 | endcard | Endcard Wipe rein | Whoosh 2-3 | 0,32 | 17 | −18,6 | −19,0 | 2/1 | frei | −34,3 |
| 38 | 04:26:05 | 6645 | A5 | endcard | Logos Taxodia + Ludwig erscheinen | Shimmer and fast airy whoosh | 0,16 | 36 | −12,2 | −18,1 | 2/1 | frei | −27,1 |
| 39 | 04:27:14 | 6689 | A4 | endcard | URL-Pille taxodia.de poppt auf | Digital Interface Notification | 0,04 | 6 | −13,4 | −18,0 | 0/1 | frei | −30,3 |

## Bewusst ohne SFX

- **Mikro-Ereignisse:** Ortsschilder, Kicker und Wortkaskaden, Radius-Label „50 km“, Pin-Pulse.
- **Dichte O-Ton-Stellen:** Bogen der Karte Taxodia (der „online“-Chip schließt ihn ab), Linienfüllung, Fortschrittspunkt und Fußzeile des Taxodia-Wegs.
- **Alle Abgänge** von Karten, Bauchbinden, Titel und Flashes (Abgang schnell und leise).
- **Bauchbinde Flammann:** Sie beginnt 4 Frames nach der Iris der Blende „Die Online-Steuerfachschule“. Ein gemeinsamer weicher Whoosh trägt beide Bewegungen, statt zwei SFX in 0,25 s.
- **Kein Riser:**
  - Titel: Die Musik hebt schon auf der Eins bei 345 an.
  - Endcard: Heins CTA läuft bis 6637, ein Riser würde unter dem CTA liegen.

## Prüfmischung

`sfx_mischung_pruefen.py` baut die Mischung wie `musik/mischung_pruefen.py` nach:
- A1 mit den Normalisierungs-Gains aus Resolve,
- Musik aus `MUSIK_PLAN`,
- SFX aus diesem Plan, jeweils mit linearen Fades.

Ergebnis: `vorschau_mischung.wav` (48 kHz / 24 Bit, 4:33,8) und `analyse/mischung_sfx.json`. Voice Isolation ist nicht simuliert.

| Messung | Wert |
|---|---|
| Integriert mit / ohne SFX | −19,1 / −19,1 LUFS (Sprache −19,2, Musik −30,5) |
| Lautheitsbeitrag SFX | 0,0 LU · K-gewichteter Energieanteil −27,7 dB |
| True Peak Mischung mit / ohne SFX | −2,5 / −2,5 dBTP · SFX-Stem −17,1 dBTP · übersteuerte Samples 0 |
| SFX-Peak während hörbarer Sprache | max. −26,0 dBFS (Grenze −26) |
| Sprach-Peak minus SFX-Peak je Frame (deutliche Sprache) | min. 5,2 dB, Median 14,2 dB |
| SFX unter Sprache (26 Platzierungen) | Peak −28,1 … −26,0 dBFS · M −41,9 … −36,7 LUFS · Mischung ohne SFX im selben Fenster 12,1 … 26,3 LU lauter (Median 20,9) |
| Blenden-Wipes in Sprechpausen | Kapitel-/CTA-Blenden M −33,3 … −32,5 LUFS = Musik −2,2 … +2,9 LU; „Online lernen“ +7,0 LU (Musik-Crossfade-Tal); Endcard-Wipe −34,3 LUFS (Musik −1,7 LU) |
| Titel / Endcard (Musik-Anhebungen) | Shimmer −26,1 / −27,1 LUFS, URL-Blip −30,3 LUFS · Musik dort −18,4 / −18,7 LUFS · lauteste SFX −26,1 LUFS < Musik-Anhebung max. −17,0 LUFS |
| Automatische Prüfungen | Plan: ok · Mischung: ok |

## Offen / Hinweise

- **Nicht abgehört:** nur gemessen und per Spektrogramm geprüft. Vor der Abnahme `vorschau_mischung.wav` oder die Timeline anhören.
- **Unter Sprache sehr dezent:** im Median 20,9 LU unter der Mischung ohne SFX. Die Iris-Swells unter Sprache (−28 dBFS) sind praktisch nur in Wortfugen hörbar.
  - Falls zu leise: A4/A5 pauschal +3 dB. Dann liegen die Peaks unter Sprache bei ≈ −23 dBFS, also über der Vorgabe −26.
- **Grafik-Timing geändert (neuer Render)?** `sfx_plan_bauen.py` erneut laufen lassen – die Anker werden aus `Grafikebene.tsx` gelesen. Danach `sfx_mischung_pruefen.py`.
- **Inventar:** Das Feld `pfad` in `inventar.json` ist veraltet; der Plan nutzt `pfad_nas` (alle 39 Pfade erreichbar).
- **Formate:** Die Dateien liegen in 44,1/48/96 kHz vor, Resolve rechnet sie um. Die zwei MP3s ohne Priming-Versatz: Sync im Resolve-Viewer trotzdem kurz gegenprüfen.
- **Kompatibilität:** Das Format entspricht dem, was `sfx_einsetzen.py` erwartet (Liste; element/rec_frame/src_in_s/dauer_frames/gain_db/fade_in_f/fade_out_f/spur). Das Skript wurde nicht ausgeführt.

## Dateien

- `sfx_analyse.py` → `analyse/sfx_metriken.json` (Messung Bestand).
- `sfx_spektren.py` → `analyse/spektren/*.png` (Sichtprüfung).
- `sfx_plan_bauen.py` → `sfx_plan.json` und `analyse/sfx_plan_details.json` (Ereignis-Frame, Anker, Abweichung, Wörter, Pegelbegrenzung).
- `sfx_mischung_pruefen.py` → `vorschau_mischung.wav` und `analyse/mischung_sfx.json`.
- Aufruf jeweils mit `PYTHONDONTWRITEBYTECODE=1 tools/autocut/venv/bin/python …`.
