# Protokoll — Craiss Logistik / 4 Ads / 2026-08 Testimonial Video

## 2026-08-26 — Hook, Zitat-Chip, Flaggen, Endcard (Video 05)

**Gemacht:**
- Dateien aus `4 Ads/` einsortiert; H.264-Proxy (Quelle 10-bit-HEVC).
- Komposition `Craiss-Testimonial` (+ `-Preview`), 54 s (Video 50,92 s):
  - **Hook-Chip** „ICH MAG MEINE ARBEIT." 0,24–2,28 s (gesprochener
    Opener; roter Chip wie Video 04, Lower-Third, raus vor Schnitt 2,36).
  - **Zitat-Chip** „KEIN STRESS." 16,84–19,12 s (Wortanfang; raus vor
    Schnitt 19,2).
  - **Flaggen-Staffel** (gleiche Audio-Passage wie Video 03): Ungarn 42,04 /
    Tschechien 42,84 / Rumänien 43,48 / **Litauen 44,44** — SRT (43,96) war
    wie in Video 03 zu früh, Wortanfang per Wellenform (Sprechpause bis
    44,44). LT hält über den Schnitt 44,88 durch „Alles.", raus 45,86.
  - **Endcard ab 48,52 s** auf dem schwarzen End-Shot (ab 48,4):
    **Preview-Comp zeigt die opake weiße Endcard** (Davids Wunsch: er
    graded parallel und will sie sehen), **der Alpha-Export nutzt den
    transparenten Serien-CTA** (`ctaOpaque`-Prop). Komposition läuft bis
    54 s — Schwarz/Endcard kann im Schnitt beliebig gehalten werden.

**v2 (Feedback „zu wenig Animationen, Hook gefällt nicht"):**
- Hook jetzt Serien-Look wie Video 02: Headline „ICH MAG MEINE ARBEIT."
  + roter Chip „LKW-FAHRER BEI CRAISS" (offsetY +32, unter dem Kinn).
- Sechs wortgetreue Zitat-Chips (alle am Wortanfang, raus vor dem
  jeweils nächsten Schnitt; Gesichter in allen Fenstern oben,
  per Kontaktbogen geprüft):
  „JEDEN TAG IST EIN GUTER TAG." 3,32 · „DIE FREIHEIT. DIE RUHE." 6,88 ·
  „ICH MACHE LKW-FAHRER." 13,12 · „KEIN STRESS." 16,84 ·
  „JEDEN TAG ZU HAUSE." 30,84 · „BEI CRAISS PASST OPTIMAL." 37,28.

**v3 (Feedback):** „JEDER TAG IST EIN GUTER TAG." (mit R);
„ICH MACHE LKW-FAHRER." gestrichen; alle Elemente auf gemeinsame
Oberkante 990 (Referenz „JEDEN TAG ZU HAUSE."); „BEI CRAISS PASST'S."
mit Punkt (Apostroph ergänzt — Davids Schreibweise war „passts").

**Geliefert:**
- `Ergebnisse/Renders/05_Testimonial_Overlays_v1.mov` — **Final**, ProRes
  4444 mit Alpha (yuva444p12le), 2160×3840, 25 fps, 1350 Frames (54 s;
  Video endet 50,92 s, Endcard transparent ab 48,52 s bis 54 s).
  Nach Davids „go" gerendert (2. Versuch, bekannter Serverstart-Fehler).
  `flicker-check.sh`: 13 Kandidaten, alle 13 auf Ein-/Ausblenderampen
  der 8 Elemente gemappt; Alpha frameweise: Rampen monoton, Flaggen-
  Übergaben sauber, Leerbereiche (F250/600/1000/1180) exakt 0,
  letzter Frame steht (CTA).

**Offen:** — (Video 05 komplett; Serie 01–05 final geliefert.)

## 2026-09-07 — v2-Final: Kunden-CTA (CI-Handbuch) 
- Geteilte Bausteine umgestellt: CTA/Endcard = „WERDE TEIL DER" +
  offizielles Logo-Lockup (Wortmarke + GENERATION/LOGISTIK in
  Craiss-Blau #002F5F, CD-Handbuch S. 13/21), nach Davids Größen-Review
  um 20 % vergrößert (Wortmarke 480 px, bleibt in der Safe Zone).
- **Geliefert:** `Ergebnisse/Renders/05_Testimonial_Overlays_v2.mov` (ProRes 4444 Alpha, ersetzt v1).
  flicker-check: nur bekannte Ein-/Ausblenderampen, keine Ausfälle.

## 2026-09-07 — Untertitel für V2-Schnitt (Teil der Craiss-01–05-Serie)

Gleiches Vorgehen wie 01–04: `Material/Video/05_Testimonial_Video_V2.mp4`
ist der fertig komponierte Schnitt (Hook+Zitat-Chips+Flaggen+CTA
eingebrannt). H.264-Proxy gebaut, Scribe-Transkript neu gezogen (ASR-Fehler
„Kreis"→Craiss, 2×), 24 Caption-Seiten generiert, neue Komposition
`Craiss-Testimonial-Untertitel`.

Root.tsx-Defaults trafen den V2-Schnitt nicht durchgehend — der Zitat-Chip
„JEDEN TAG ZU HAUSE." z. B. blendet real ~1,8 s früher ein als dokumentiert
und kollidierte im ersten Durchlauf sichtbar mit dem Untertitel; „BEI CRAISS
PASST'S." und die Länder-Flaggen ebenfalls einige Zehntel bis über 1 s
verschoben. **Komplett neu vermessen per lückenlosem 1-Sekunden-Kontaktbogen
(0–52 s)**, alle 8 Sperrfenster (Hook, 5 Zitat-Chips, Flaggen, CTA) gegen
echte Frames verifiziert.

Gleiche Untertitel-Höhe/-Stil wie 01–04.

**Geliefert:** `Ergebnisse/Renders/05_Testimonial_Untertitel_v1.mp4` (H.264,
1080×1920, 25 fps, aus dem V2-Proxy).

**Damit hat die ganze Craiss-01–05-Serie eine Untertitel-Fassung.**

**Offen:** `Material/Video/05_Testimonial_Video_V2.mp4` gehört eigentlich
nach `Ergebnisse/Renders/` (kein Rohmaterial) — nicht verschoben, außerhalb
des Auftrags. Alle 5 „V-Original"-Dateien in Material/Video tragen dasselbe
Muster; bei Gelegenheit als Serie aufräumen/umbenennen.

## 2026-09-11 — Overlay v3 nach Kundenfeedback (Studio, noch nicht gerendert)

- Craiss-Code vom Zweit-MacBook übernommen (Details im Protokoll 01).
- Export ohne Animation vom NAS nach `Material/Video/ohne-Animation/`
  (+ Proxy): gleicher Schnitt wie V2 animiert, 1324 Frames. Grafiken per
  Differenz animiert − ohne Animation frame-genau gemessen. Befund: der
  Cutter hat „JEDER TAG…“ +120 px und „DIE FREIHEIT…“ +84 px tiefer gesetzt
  und ab ~20 s alles 47 Frames nach vorn gezogen; CTA liegt auf der Drohne.
- **`Craiss-Testimonial` v3** (Timing/Höhen des Kunden-Schnitts übernommen):
  - „KEIN STRESS.“ entfernt (Kunde: Fokus reduzieren, nicht einblenden).
  - Hook +60 px tiefer (Kunde: Texteinblendungen zu hoch; wie Eva in 04).
  - Ruhige Bewegung: SOFT-Feder, Skalierung 0,95, Flaggen-Weg 120 statt
    340 px (neue `calm`-Option an `Hook`/`FlagsRow` in der lib — 01–03
    unverändert).
  - Chips 3,32 / 6,88 / 28,96 / 35,40 s, Flaggen 40,16–44,04 s, CTA 46,64 s.
  - Kontroll-Render 540×960 gegen den Kunden-Schnitt differenziert: Abweichung
    nur bei Hook, entferntem Chip und den weicheren Ein-/Ausflügen.
- Untertitel: „Kein Stress.“ gestrichen; Sperre „DIE FREIHEIT“ ab 6,86 s
  korrigiert (Chip ab 6,92 s). `Craiss-Testimonial-Untertitel` zeigt jetzt
  Export ohne Animation + Overlay v3 + Untertitel.
- Kundenfeedback-Check: Kennzeichen Golf verpixelt ✓, zweites „keine Stress“
  (V1) raus ✓, Einblendungen tiefer ✓. **Nicht umgesetzt:** Abwechslung — 05
  besteht fast nur aus Aussagen, die auch in 02/03 laufen.
- QC Export: −16,9 LUFS, **True Peak +2,1 dBFS** (Cutter), keine Schwarzbilder.

- **Abnahme-Vorschau** `Craiss-Vorschau-05-Testimonial` (Studio: Craiss →
  Vorschau-Neu): Export ohne Animation + Overlay v3 + Untertitel.

- **Untertitel-Look „Mix"** (nach Abnahme von 01 übertragen): Sperrfenster =
  Sequenzen von Overlay v3; Plan `captions/testimonial-v2.plan.json` mit
  LIEBE JOB (rot) und GERN FAHREN (blau); 4 von 10 Sätzen sichtbar (die übrigen
  liegen unter Hook, Chips, Flaggen oder wiederholen deren Inhalt).
  Kontaktbogen geprüft: Hals/Gesichter frei.
- **Nachtrag (Feedback „sieht aus wie der alte Stil"):** Dichte wie Video 01 —
  Fahrer-Satz geteilt (`--split=cc-04:7`): IMMER LKW (weiß) → LIEBE JOB (rot);
  dazu ZEHN MINUTEN (blau), MERCEDES (weiß). Kontaktbogen neu geprüft.

- **UT-Korrektur (Kunde/Jan):** 16,1 s „und für mich ist, ich liebe meinen Job."
  (ASR hatte „ist Liebe Job") → ICH LIEBE MEINEN JOB (blau), Wortzeiten per
  Hüllkurve geprüft; ZEHN MINUTEN jetzt rot.
- **Neuexport 18:46 vom NAS** (alter Export → `ohne-Animation/_vorher-1436/`):
  1315 Frames = 52,6 s. Bild-Abgleich Frame für Frame: bei 16,96 s 13 Frames
  („Kein Stress.") herausgeschnitten, danach alles −0,52 s. Plan per Frame-Map
  umgerechnet; Overlay v3 neu getaktet: Chips JEDEN TAG ZU HAUSE 28,44 /
  PASST'S 34,88, Flaggen 39,64–43,52, CTA 46,12; Sperrfenster und Längen
  (Overlay, Untertitel-Comp, Vorschau) nachgezogen. Ton ab 17,5 s leicht
  anders gemischt (gleiche Lage ±16 ms). Kontaktbogen (540×960): Untertitel,
  Chips, Flaggen und CTA sitzen auf den neuen Schnitten.

## 2026-09-11 — Lieferung: eine Alpha-Datei (Animationen + Untertitel)

- User-Wunsch „für jedes Video nur eine lange Datei": statt getrenntem
  Overlay v3 + Untertitel-Spur eine Datei. Remotion `Craiss → Alpha-Komplett` /
  `Craiss-Alpha-05-Testimonial`.
- **Geliefert:** `Ergebnisse/Renders/05_Testimonial_Alpha_Komplett_v1.mov` —
  ProRes 4444 Alpha (yuva444p12le), 2160×3840, 25 fps, 1315 Frames (= Neuexport
  18:46). Overlay v3 (Hook, Chips, Flaggen, CTA) + Untertitel-Mix; ersetzt
  `05_Testimonial_Overlays_v2.mov`.
- flicker-check: Kandidaten nur an Ein-/Ausblendungen und Satzwechseln; Suche
  nach isolierten Ein-Frame-Einbrüchen: 0. Kontaktbogen geprüft.

- **NAS + Resolve:** NAS `03_Medien/02_Assets/07_Animation/05_Testimonial_Video/`
  (ohne Tonspur); Resolve `01_Projekt_4_Ads` → Timeline `05_Testimonial_Video_V2`,
  neue oberste Spur V9 „NIRO Alpha Komplett", ab Start, 1315 Frames (bis zum
  Mark-Out), nur Video (Details Protokoll 01).

**Offen:** Alte Overlay-Spur V5 (`05_Testimonial_Overlays_v2.mov`) ist bereits
deaktiviert, kann raus; Kunden-Abnahme.
