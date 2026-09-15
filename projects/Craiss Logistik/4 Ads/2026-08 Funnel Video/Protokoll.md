# Protokoll — Craiss Logistik / 4 Ads / 2026-08 Funnel Video

## 2026-08-26 — Hook, Logo-Transition, Schritte, End-Logo (Video 04)

**Gemacht:**
- Lose Dateien aus `4 Ads/` einsortiert; H.264-Proxy erstellt (Quelle 10-bit-HEVC).
- Komposition `Craiss-Funnel` (+ `-Preview`), 60,72 s:
  - **Hook** „WIR SIND DIE KÜMMERER" + roter Balken (kein Chip — kein
    zweiter Text vorhanden), Lower-Third, **1,44–4,44 s**: startet auf dem
    Schnitt in den weiten Chef-Shot, weil Shot 1 zu eng gerahmt ist
    (Kinn ~52 %); die Phrase fällt 0,08–1,08 s.
  - **Logo-Transition** 22,76–23,56 s: Die „Lücke" zwischen Chef und Eva
    ist im Schnitt **schwarz** (22,68–23,64 s) — weiße Logo-Karte poppt
    mittig ins Schwarz (Spring-in, leichter Drift, Fade-out), komplett
    innerhalb des schwarzen Fensters.
  - **Bewerbungs-Schritte** als rote Nummern-Kacheln + Text, rein/raus wie
    die Flaggen in Video 03 (Wortanfänge aus SRT):
    1 „TRAG DICH EIN" 36,8–38,16 · 2 „TELEFONAT" 38,16–40,6 ·
    3 „PERSÖNLICHES KENNENLERNEN" 47,96–50,4 (raus vor Schnitt 50,6).
  - **KEIN CTA** (Video liegt auf der Landing Page). Stattdessen
    **End-Logo** (weiße Karte, mittig) ab **55,8 s** — nur auf dem LETZTEN
    Shot (unscharfe Drohne ab 55,68 s), nicht auf dem vorletzten (54,2–55,68).

**v2 nach Davids Feedback (6 Punkte):**
1. Hook sofort (0,24 s) — dafür nach OBEN verlegt (y 200, über Kopf in
   beiden Chef-Shots), da Shot 1 unten keinen Platz lässt (Kinn ~52 %).
2. Standort-Chip „📍 MÜHLACKER" 6,84–9,6 s (Wortanfang; liegt auf dem
   Stadt-Drohnenshot).
3. Transition jetzt Vollbild-SWIPE statt Logo-auf-Schwarz: Panel
   [rot|weiß|rot] fährt 22,36 s von links ein (rote Kante führt), deckt ab
   Lücken-Beginn 22,68 s voll, Logo-Lockup mittig, Ausfahrt gibt Eva exakt
   auf ihrem Shot-Beginn 23,64 s frei. Schwarz nie sichtbar.
4. Mehr Eva-Animationen: Namens-Karte „EVA / DEINE ANSPRECHPARTNERIN"
   (24,84–28,4), „✕ KEIN LEBENSLAUF / ✕ KEIN ANSCHREIBEN" (33,56 + 35,32,
   Wellenform-basiert), Phone-Chip „SEI ERREICHBAR" mit Klingel-Wackeln
   (40,64–44,6), Outro „WORAUF WARTEST DU?" (51,4–54,0).
5. Schritt-Zahlen in den roten Kacheln optisch zentriert (Cap-Höhen-
   Ausgleich translateY −3 px).
6. End-Logo größer, vertikal mittig, als Lockup mit „GENERATION LOGISTIK".
   Dafür `CraissWordmark`/`CraissLogoLockup` in der lib: Wordmark als
   Inline-SVG mit freier Farbe (rot/weiß/anthrazit), Unterzeile optional.

**v3 (Feedback):** Hook mittig, Mühlacker 6,6–8,0 s (minimale Überschneidung
in den Truck-Shot), Step-Zahlen per Pixel-Crop zentriert (−6,5 px).

**v4 (Feedback, nur Studio — David will keine Preview-MP4s mehr):**
- Hook war in Bildmitte im Gesicht des Chefs (Shot 1) → jetzt kompakter
  roter Chip im schmalen Band zwischen Kinnfalte (~1030) und Safe-Zone-
  Kante (1104); Kinn per Frame-Crops vermessen. Nur noch 0,24–2,0 s
  (halbe Länge).
- Neu: Chef-Namenskarte „MICHAEL CRAISS / GESCHÄFTSFÜHRER" 2,0–6,4 s
  (Wortanfang „Michael"), Übergabe an Standort-Chip 6,6 s.
- Ziffer „3" hing tiefer als „1" → eigener Versatz (−10,5 px statt −6,5).
- NameCard kompaktiert (Unterkante ≤ Safe Zone).

**v5 (Feedback):** Kümmerer-Chip weiter runter auf die Brust (top 1110 —
bewusst unter der strengen Safe-Zone-Kante, Davids Entscheidung);
Chef-Namenskarte endet vor dem Schnitt bei 4,52 (raus 4,44).

**Geliefert:**
- `Ergebnisse/Renders/04_Funnel_HookTransitionSteps_Preview_v1–v3.mp4`
  (Abnahme-Previews; ab v4 Abnahme direkt im Studio).
- `Ergebnisse/Renders/04_Funnel_Overlays_v1.mov` — **Final**, ProRes 4444
  mit Alpha (yuva444p12le), 2160×3840, 25 fps, 1518 Frames (60,72 s).
  `flicker-check.sh`: 19 Kandidaten, alle 19 exakt auf Ein-/Ausblende-
  rampen der 10 Elemente gemappt, keine Ausfälle in Haltephasen.
  Alpha frameweise: Rampen monoton; Transition deckt voll ab Frame 565
  (vor Schwarz-Beginn 567) bis 593 und ist bei 599 exakt 0; vorletzter
  Shot (F1370) und alle Leerbereiche exakt transparent; Chef-Karte bei
  F120 (nach Schnitt) weg; letzter Frame steht (End-Logo).

**Serie komplett:** Alle 4 Craiss-Ads final geliefert (01–04).

**Offen:**
- Abnahme durch David (Studio: `Craiss-Funnel-Preview`, Port 3112).
- Nach Go: Final-Render ProRes 4444 (`Craiss-Funnel`) + flicker-check.

## 2026-09-07 — v2-Final: Kunden-CTA (CI-Handbuch) (Transition + End-Logo)
- Geteilte Bausteine umgestellt: CTA/Endcard = „WERDE TEIL DER" +
  offizielles Logo-Lockup (Wortmarke + GENERATION/LOGISTIK in
  Craiss-Blau #002F5F, CD-Handbuch S. 13/21), nach Davids Größen-Review
  um 20 % vergrößert (Wortmarke 480 px, bleibt in der Safe Zone).
- **Geliefert:** `Ergebnisse/Renders/04_Funnel_Overlays_v2.mov` (ProRes 4444 Alpha, ersetzt v1).
  flicker-check: nur bekannte Ein-/Ausblenderampen, keine Ausfälle.

## 2026-09-07 — v3-Final: Kundenfeedback-Runde 2
- **Ruhigere Animationen** (wichtigster Punkt): weiche Feder `SOFT`
  (Dämpfung 34/Steifigkeit 75, clamped) für alle 04-Elemente und den
  geteilten Serien-CTA; Wege reduziert (Slides 340→120, Scale 0,85→0,95,
  Phone-Wackler 1× mit halber Amplitude).
- Hook „Wir sind die Kümmerer" entfernt (wird gecuttet).
- Michael Craiss: „GESCHÄFTSFÜHRENDER GESELLSCHAFTER".
- Transition-Panel zeigt jetzt CTA-Inhalt (WERDE TEIL DER + Logo +
  JETZT BEWERBEN), Swipe-Mechanik unverändert.
- Eva-Einblendungen +60 px tiefer (Hals frei, Kundenwunsch).
- Ende: voller Serien-CTA statt End-Logo (nur letzter Shot, ab 55,8 s).
- **Geliefert:** `Ergebnisse/Renders/04_Funnel_Overlays_v3.mov` (427 MB,
  ProRes 4444 Alpha). flicker-check: 15 Kandidaten, alle bekannte
  Ein-/Ausblenderampen; Alpha-Spots: Anfang jetzt leer (F20=0),
  Transition deckt voll, vorletzter Shot frei, letzter Frame steht.
- Hinweis: SOFT-CTA erbt die Serie — Re-Render 01/02/03/05 auf Zuruf.

## 2026-09-07 — Untertitel für V4-Schnitt (Teil der Craiss-01–05-Serie)

Gleiches Vorgehen wie 01–03: `Material/Video/04_Funnel_Video_V4.mp4` ist der
fertig komponierte Schnitt (alle Chips/Transition/Schritte/End-Logo
eingebrannt). H.264-Proxy gebaut, Scribe-Transkript neu gezogen (ASR-Fehler
„Kreis"→Craiss, 3×), 39 Caption-Seiten generiert, neue Komposition
`Craiss-Funnel-Untertitel`.

**Video ist durchgehend dicht mit Grafiken belegt** (Chef-Karte, Standort-
Chip, Swipe-Transition, Eva-Namenskarte, „Kein Lebenslauf/Anschreiben",
3 Schritte, Phone-Chip, Outro, End-Logo) — die Untertitel-Spur zeigt
entsprechend nur in den echten Lücken (v. a. 8–21 s und vereinzelte
kürzere Fenster). Root.tsx-Defaults trafen den V4-Schnitt an mehreren
Stellen nicht (z. B. „KEIN LEBENSLAUF"-Chip real ~1 s früher als
dokumentiert) — erste Fassung mit gepolsterten Default-Werten kollidierte
sichtbar mit dem Untertitel; **komplett neu vermessen per lückenlosem
1-Sekunden-Kontaktbogen (0–59 s)** statt der Doku-Werte zu vertrauen.
Alle 10 Sperrfenster jetzt gegen echte Frames verifiziert.

Gleiche Untertitel-Höhe/-Stil wie 01–03. Eva-Nahaufnahmen: Text sitzt am
oberen Rand von Schulter/Kragen, nie am Hals (Kontaktbogen geprüft).

**Geliefert:** `Ergebnisse/Renders/04_Funnel_Untertitel_v1.mp4` (H.264,
1080×1920, 25 fps, aus dem V4-Proxy).

**Offen:** `Material/Video/04_Funnel_Video_V4.mp4` gehört eigentlich nach
`Ergebnisse/Renders/` (kein Rohmaterial) — nicht verschoben, außerhalb des
Auftrags.

## 2026-09-11 — Code-Migration, Untertitel-Vorschau, Kundenfeedback-Check

- Craiss-Code vom Zweit-MacBook übernommen (Details im Protokoll 01).
  `Craiss-Funnel-Untertitel`: Studio mit V4-Schnitt, Render = Alpha.
- **Sperrfenster korrigiert:** Chip „MÜHLACKER“ blendet ab Frame 132 (5,28 s)
  ein, nicht 6,0 s — Untertitel „mit Sitz in Mühlacker.“ lief parallel und
  doppelte ihn; Sperre jetzt ab 5,2 s.
- Export ohne Animation (NAS, `04_Funnel_Video_V3.mp4`) nach
  `Material/Video/ohne-Animation/` (+ Proxy): gleicher Schnitt wie V4 animiert;
  unter dem Wisch-Übergang liegen zwei Schnitte (21,32 / 22,44 s), kein
  Schwarzbild mehr. Alle 11 Grafik-Segmente per Differenz frame-genau gemessen.
- Kundenfeedback-Check: „Kümmerer“ raus ✓, Bauchbinde „GESCHÄFTSFÜHRENDER
  GESELLSCHAFTER“ ✓, Trenner = CTA-Inhalt auf Weiß ✓, Eva-Einblendungen tiefer
  und ruhig (Ausstieg frameweise geprüft) ✓, Abspann ✓.
- QC Export: −16,5 LUFS, True Peak 0,0 dBFS, keine Schwarzbilder.

- **Abnahme-Vorschau** `Craiss-Vorschau-04-Funnel` (Craiss → Vorschau-Neu).
  `Craiss-Funnel`-Defaults auf den Kunden-Schnitt V4 umgestellt (59,12 s):
  Render mit alten V2-Zeiten gegen die gemessenen Grafik-Segmente
  ausgerichtet — Chef-Teil (Karte 0,64, Mühlacker 5,24, Transition 21,0)
  −34 Frames, Eva-Teil (Karte 23,76 … Outro 50,32, CTA 54,72) −27 Frames,
  Positionen unverändert. Kontroll-Render gegen den animierten V4: nur
  Rest-Rauschen, keine Zeit- oder Lageabweichung.

**Offen:** Untertitel-Render nach Freigabe; Satzteil-Reste (4,0–5,0 s
„Logistikunternehmens Craiss“, 44,5–46,5 s) mit Jan/David klären.

## 2026-09-11 — Untertitel-Look „Mix" (nach Abnahme von 01 übertragen)

- Sperrfenster = Sequenzen von `Craiss-Funnel` (11 Grafiken, Dauern als
  Literale). Satzteil-Reste damit erledigt: der Mix-Look zeigt nur ganze Sätze.
- Plan `captions/funnel-v4.plan.json`; zwei lange Sätze an Sinngrenzen geteilt
  (`--split=cc-08:10,cc-11:6`): „… ist das ganz einfach:" steht vor „KEIN
  LEBENSLAUF", „Wenn bei diesem Telefonat alles passt" übergibt an
  „3 PERSÖNLICHES KENNENLERNEN". „Wir sind ein Familienunternehmen." startet
  erst nach dem Mühlacker-Chip (6,64 s). ANKOMMEN (weiß), UND DAFÜR STEHEN WIR
  (Wort-Kasten), GANZ EINFACH (rot); 5 Sätze sichtbar — der Rest wiederholt
  Namenskarten, Schritte und Chips.
- Sichtprüfung Kontaktbogen: Hals/Gesichter frei (Chef-Nahaufnahme: Text
  ≥ 110 px unter dem Kinn).
- Vorschau `Craiss-Vorschau-04-Funnel`.

- **Nachtrag (Feedback „sieht aus wie der alte Stil"):** Dichte wie Video 01 —
  Chef-Satz in drei Sinneinheiten geteilt (`--split=cc-04:9`, dann `cc-04b:12`):
  RIESENVORTEIL (rot), UNTERSCHIED (blau), ANKOMMEN (weiß); dazu
  FAMILIENUNTERNEHMEN (blau). „Wenn bei diesem Telefonat" war als Wort-Kasten
  dreizeilig und ragte unter 78 % → Grundzeile + TELEFONAT (blau), per Still
  geprüft. Planprüfung schätzt jetzt Wort-Kasten-Zeilen (`wordboxLines`, Tests).

- **UT-Korrektur (Kunde/Jan):** bei 16 s „0815-Arbeitsverhältnis" als Ziffern,
  per Still geprüft.

## 2026-09-11 — Lieferung: eine Alpha-Datei (Animationen + Untertitel)

- User-Wunsch „für jedes Video nur eine lange Datei": Remotion `Craiss →
  Alpha-Komplett` / `Craiss-Alpha-04-Funnel`.
- **Geliefert:** `Ergebnisse/Renders/04_Funnel_Alpha_Komplett_v1.mov` — ProRes
  4444 Alpha (yuva444p12le), 2160×3840, 25 fps, 1478 Frames. Alle Grafiken
  (Karten, Chips, Transition, Schritte, Outro, CTA) + Untertitel-Mix in einer
  Datei; ersetzt `04_Funnel_Overlays_v3.mov`.
- flicker-check: Kandidaten nur an Ein-/Ausblendungen und Satzwechseln; 4
  isolierte Einbrüche (Frames 244, 318, 327, 761) = geplante Seiten-/Hero-
  Wechsel (neue Zeile bzw. UNTERSCHIED blendet ein), per Einzelbild geprüft.
  Kontaktbogen geprüft.

- **NAS + Resolve:** NAS `03_Medien/02_Assets/07_Animation/04_Funnel_Video/` (ohne
  Tonspur); Resolve `01_Projekt_4_Ads` → Timeline `04_Funnel_Video_V3`, neue oberste
  Spur V9 „NIRO Alpha Komplett", ab Start, 1478 Frames, nur Video (Details
  Protokoll 01). Hinweis: Timeline-Clips reichen bis Frame 1504 (Drohne), der
  Export ohne Animation hat 1478 — Alpha-Datei deckt den Export-Bereich.

**Offen:** Alte Overlay-Spur V6 (`04_Funnel_Overlays_v3.mov`, zwei Teile) noch drin —
deaktivieren, sonst doppelt; Kunden-Abnahme.
