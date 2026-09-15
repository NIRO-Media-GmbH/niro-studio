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

## 2026-09-01 — Migration ins Studio-Hauptsystem

**Gemacht:** Charge vom Zweit-MacBook übernommen und unter
`projects/Craiss/4 Ads/` eingegliedert — liegt jetzt neben der Charge
„2026-08 Dreh" (O-Ton-Pläne/Schnittanweisungen zu denselben 5 Videos).
Inhalte unverändert.
