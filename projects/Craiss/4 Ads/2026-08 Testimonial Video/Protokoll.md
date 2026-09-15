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

## 2026-09-01 — Migration ins Studio-Hauptsystem

**Gemacht:** Charge vom Zweit-MacBook übernommen und unter
`projects/Craiss/4 Ads/` eingegliedert — liegt jetzt neben der Charge
„2026-08 Dreh" (O-Ton-Pläne/Schnittanweisungen zu denselben 5 Videos).
Inhalte unverändert.
