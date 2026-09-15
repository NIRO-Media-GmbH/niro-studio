# Protokoll — Craiss Logistik / 4 Ads / 2026-08 Einblick Arbeitsalltag

## 2026-08-26 — Hook- & CTA-Animation (Video 02)

**Gemacht:**
- Lose Dateien aus `4 Ads/` in die Chargen-Struktur einsortiert
  (`Material/Video/`, `Material/Transcription/`).
- Gemeinsame Craiss-Bausteine nach `tools/motion/src/clients/craiss/lib.tsx`
  extrahiert (Hook mit Layout-Varianten, CTA, FootageCompare, Fonts, CI) —
  Video 01 nutzt sie jetzt auch, Regressions-Stills identisch.
- Komposition `Craiss-Arbeitsalltag` (+ `-Preview`):
  - **Hook** 0,24–3,12 s als **Lower-Third** (Talking-Head-Opener, Gesicht
    bis ~47 % Höhe; Kompaktvariante 76/38 px, Block ~50–57 % Höhe, unter der
    Gesichts-Zone, innerhalb der Safe Zone): „MEIN ARBEITSALLTAG" + Chip
    „BEI CRAISS". Ende exakt auf dem Schnitt bei 3,12 s.
  - **CTA** ab 70,4 s (3 Frames nach letztem Schnitt 70,28 s), Design/Texte
    1:1 aus Video 01, steht bis zum Ende (82,68 s, langer Drohnen-Endshot,
    wird von David unscharf gestellt).
- H.264-Proxy in `Material/Video/proxy/` (Quelle wieder 10-bit-HEVC).

**Geliefert:**
- `Ergebnisse/Renders/02_Arbeitsalltag_HookCTA_Preview_v1.mp4` (Abnahme-Preview).
- `Ergebnisse/Renders/02_Arbeitsalltag_HookCTA_v1.mov` — **Final**, ProRes 4444
  mit Alpha (yuva444p12le), 2160×3840, 25 fps, 2067 Frames. Nach Davids
  „passt!" gerendert. `flicker-check.sh`: 3 Kandidaten (Frames 9/74/1763),
  alle in Fade-Rampen; Alpha pro Frame nachgemessen — monoton, Ausblendung
  endet auf exakt 0, Leerbereich (z. B. Frame 500) komplett transparent.

**Entscheidungen:**
- Hook-Position unten statt oben (Serie bleibt im Look konsistent, Layout
  weicht wegen Gesichtern im Opener ab); Copy nach Videotitel.
- Sprache endet 67,9 s („Das ist kein Stress."), CTA-Fenster sprachfrei.

**Offen:**
- Videos 03–04 der Serie noch unbearbeitet.

## 2026-09-07 — v2-Final: Kunden-CTA (CI-Handbuch) 
- Geteilte Bausteine umgestellt: CTA/Endcard = „WERDE TEIL DER" +
  offizielles Logo-Lockup (Wortmarke + GENERATION/LOGISTIK in
  Craiss-Blau #002F5F, CD-Handbuch S. 13/21), nach Davids Größen-Review
  um 20 % vergrößert (Wortmarke 480 px, bleibt in der Safe Zone).
- **Geliefert:** `Ergebnisse/Renders/02_Arbeitsalltag_HookCTA_v2.mov` (ProRes 4444 Alpha, ersetzt v1).
  flicker-check: nur bekannte Ein-/Ausblenderampen, keine Ausfälle.

## 2026-09-07 — Untertitel für V3-Schnitt (Teil der Craiss-01–05-Serie)

Gleiches Vorgehen wie bei Video 01 (dort ausführlich dokumentiert):
`Material/Video/02_Einblick_in_meinen_Arbeitsalltag_V3.mp4` ist bereits der
fertig komponierte Schnitt (Hook+CTA eingebrannt), kein Rohmaterial — H.264-
Proxy gebaut, Wort-Transkript per ElevenLabs Scribe neu gezogen (ASR-Fehler
„Kreis"→Craiss, „Family."→Familie korrigiert), 30 Caption-Seiten generiert
(`scripts/craiss-captions.ts`), neue Komposition `Craiss-Arbeitsalltag-
Untertitel` (nur Untertitel-Layer, Hook/CTA/Composition-02 unangetastet).

Hook/CTA-Timing im V3-Schnitt weicht stark vom `craissArbeitsalltagDefaults`-
Stand ab (Video ist ~9,5 s kürzer als dokumentiert) — Sperrzeiten per
Frame-Kontaktbogen neu vermessen statt aus Root.tsx übernommen: Hook
0–3,0 s, CTA ab 61,6 s (Schnitt auf Drohnen-Endshot ~61,65 s).

Untertitel-Höhe/-Stil identisch zu Video 01 (knapp unter Bildmitte, für
alle Cues gleich, Highlight-Rot `#E5484F`). Footage hier durchgehend
Halbtotale/Totale (Fahrer/Büro-Szenen) — keine Kinn-Kollisionen im
Kontaktbogen gefunden.

**Geliefert:** `Ergebnisse/Renders/02_Arbeitsalltag_HookCTA_Untertitel_v1.mp4`
(H.264, 1080×1920, 25 fps, aus dem V3-Proxy).

**Offen:** `Material/Video/02_Einblick_in_meinen_Arbeitsalltag_V3.mp4` gehört
eigentlich nach `Ergebnisse/Renders/` (kein Rohmaterial) — nicht verschoben,
außerhalb des Auftrags.

## 2026-09-11 — Code-Migration, Untertitel-Vorschau, Kundenfeedback-Check

- Craiss-Code vom Zweit-MacBook übernommen (Details im Protokoll 01).
  `Craiss-Arbeitsalltag-Untertitel`: Studio mit V3-Schnitt, Render = Alpha.
- **„Kein Stress.“ aus den Untertiteln gestrichen** (Kundenwunsch: Fokus
  reduzieren) — `craiss-captions.ts` drop-Liste, Captions neu generiert
  (29 Seiten, „Hinterachse Lkw.“ → „Ich melde den Chef Werkstatt“).
- Export ohne Animation vom NAS nach `Material/Video/ohne-Animation/`
  (+ Proxy): identischer Schnitt zu V3 animiert; Grafiken per Differenz
  gemessen (Hook 0,32–3,0 s, CTA ab 62,4 s).
- Kundenfeedback-Check: „zu viele Stunden“ raus ✓, Kennzeichen Golf verpixelt
  ✓ (V2 noch lesbar), Fahrer weißes Polo raus ✓, zweites „Stress“ beim rosa
  Hemd raus ✓, Abspann ✓. **Nicht umgesetzt:** Abwechslung — Aussagen
  „Jeden Tag ist gute Tag“, „Nahverkehr … Familie“, „Chef Werkstatt … zehn
  Minuten“ sowie mehrere Einstellungen (LKW-Front, rosa Hemd, Handschlag,
  Werkstatt, Golf) stecken auch in 04/05; Drohne nur hinter dem CTA.
- QC Export: −17,5 LUFS, True Peak −0,2 dBFS, keine Schwarzbilder.

- **Abnahme-Vorschau** `Craiss-Vorschau-02-Arbeitsalltag` (Craiss →
  Vorschau-Neu). `Craiss-Arbeitsalltag`-Defaults auf den Kunden-Schnitt
  umgestellt: 73,12 s, CTA 62,28 s (vorher 70,4 für V2), Footage = Export
  ohne Animation; per Kontroll-Render gegen den animierten V3 frame-genau
  bestätigt.

**Offen:** Untertitel-Render nach Freigabe; Abwechslung ist Cutter-Sache.

## 2026-09-11 — Untertitel-Look „Mix" (nach Abnahme von 01 übertragen)

- Plan `tools/motion/src/clients/craiss/captions/arbeitsalltag-v3.plan.json`
  (System siehe Protokoll 01): FAMILIE (weiß), LKW IST NEU (Wort-Kasten),
  ZEHN MINUTEN (rot), 24/7 (weiß; ASR-Token „vierundzwanzig/7" → „24/7"),
  BEWIRB DICH (blau); 11 von 12 Sätzen sichtbar (Satz 1 liegt unter dem Hook).
- Sichtprüfung Kontaktbogen mit Guides: Hals/Gesichter frei. Glas „SCHÖN"
  wieder entfernt — auf dem weißen LKW-Dach kaum lesbar.
- Vorschau `Craiss-Vorschau-02-Arbeitsalltag` (Standard: neuer Look).

- **Nachtrag (Feedback „sieht aus wie der alte Stil"):** Dichte wie Video 01 —
  jeder sichtbare Satz hervorgehoben: + FERNVERKEHR (rot), JEDEN TAG ZU HAUSE
  (blau), TABLET (weiß), SCHÖN LKW (Wort-Kasten), NEUE GUMMI (blau), ICH FREUE
  MICH AUF DICH (Wort-Kasten). Kontaktbogen neu geprüft, Hals/Gesichter frei.

- **UT-Korrektur (Kunde/Jan):** NAH- UND FERNVERKEHR zusammen (blau, statt nur
  FERNVERKEHR), „Schöner" (SCHÖNER LKW), „melden"; ZU HAUSE jetzt rot.
- **Neuexport 18:42 vom NAS** (alter Export → `ohne-Animation/_vorher-1436/`):
  Bild frame-genau identisch bis 73,12 s, Drohnen-Endshot +1 s (1853 Frames =
  74,12 s). Ton: nur „Kein Stress." bei 39,98–40,54 s herausgenommen (−10 dB,
  liegt zwischen zwei Sätzen, Untertitel unberührt). Längen in Overlay,
  Untertitel-Comp und Vorschau auf 74,12 s; Kontaktbogen (540×960) geprüft.

## 2026-09-11 — Lieferung: eine Alpha-Datei (Animationen + Untertitel)

- User-Wunsch „für jedes Video nur eine lange Datei": Remotion `Craiss →
  Alpha-Komplett` / `Craiss-Alpha-02-Arbeitsalltag` (Vorschau-Komposition,
  transparent, Schnitt nur im Studio).
- **Geliefert:** `Ergebnisse/Renders/02_Arbeitsalltag_Alpha_Komplett_v1.mov` —
  ProRes 4444 Alpha (yuva444p12le), 2160×3840, 25 fps, 1853 Frames (= Neuexport
  18:42). Hook, CTA und Untertitel-Mix in einer Datei; ersetzt `…_HookCTA_v2.mov`.
- flicker-check: Kandidaten nur an Ein-/Ausblendungen und Satzwechseln; Suche
  nach isolierten Ein-Frame-Einbrüchen: 0. Kontaktbogen (alle 3 s, über Grau)
  geprüft.

- **NAS + Resolve:** NAS `03_Medien/02_Assets/07_Animation/02_Blick_in_meinen_Arbeitsalltag/`
  (ohne Tonspur); Resolve `01_Projekt_4_Ads` → Timeline
  `02_Einblick_in_meinen_Arbeitsalltag_V3`, neue oberste Spur V9 „NIRO Alpha
  Komplett", ab Start, 1853 Frames, nur Video (Details Protokoll 01).

**Offen:** Alte Overlay-Spur V5 (`02_Arbeitsalltag_HookCTA_v2.mov`) noch drin —
deaktivieren, sonst doppelt; Kunden-Abnahme.
