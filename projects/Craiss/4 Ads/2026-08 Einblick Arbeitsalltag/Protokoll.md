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

## 2026-09-01 — Migration ins Studio-Hauptsystem

**Gemacht:** Charge vom Zweit-MacBook übernommen und unter
`projects/Craiss/4 Ads/` eingegliedert — liegt jetzt neben der Charge
„2026-08 Dreh" (O-Ton-Pläne/Schnittanweisungen zu denselben 5 Videos).
Inhalte unverändert.
