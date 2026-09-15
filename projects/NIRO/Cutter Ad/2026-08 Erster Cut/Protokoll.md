# Protokoll — NIRO / Cutter Ad / 2026-08 Erster Cut

## Session 2026-08-07

**Was gemacht:**
- Neuen Motion-Client `niro` angelegt (`tools/motion/src/clients/niro/`) mit
  korrekter CI aus dem Projektordner: Grün `#A1D334` (aus Logo-SVG — die
  Datei `Colors/Green/Green.txt` ist leer!), Blau `#7DD1FF`, Dunkel `#1A211C`,
  Meutas (Titles/CTA) + Roboto (Subtitles, Uppercase). Der alte `niro-demo`
  hatte leicht abweichende Farbwerte und blieb unangetastet.
- Komposition `Niro-CutterAd`: dynamische Word-Level-Untertitel über das
  ganze Video (~73 s O-Ton), Apple-clean: Meutas SemiBold weiß ohne Kasten,
  weicher Schatten, Wort-für-Wort-Reveal (Spring + Blur), stabiles Layout
  (kein Zeilen-Reflow). Beat-Stile: Flow / Punch („Verstärkung.",
  „verändert." groß in Grün) / Stack (Branchenliste mit grünen Dashes) /
  Name-Insert („Gründer & Geschäftsführer · NIRO Media", 13,3–17,2 s) /
  CTA-Finale ab 73,2 s (NIRO-Symbol + „CUTTER (M/W/D)" + „Trag dich unten
  ein." + Chevron-Bounce).
- Timing 1:1 aus `CUTTER Ad.srt` (word-level, Premiere-Offset 01:00:00
  rausgerechnet); Multi-Wort-Cues proportional gesplittet.
- Transkript-Korrekturen (von David bestätigt): „Freizeit abends und hast
  noch eigentlich ein Hauptjob" (0:07), „…fertig. Wir suchen eben Leute"
  (0:30). Stille Fixes: „Daran ist"→„Dann ist", „durch Gas"→„Gas",
  „trage ich dich"→„trag dich", „uns sich"→„uns, dich", „Niro"→„NIRO",
  Zusammenschreibungen (weiterzuentwickeln, dazuzulernen).
- Pre-Delivery Review: 11 Guide-Stills (Face Zone / Safe Zone) geprüft —
  alles im Untertitel-Band 45–57,5 % Höhe, nichts in Face Zone oder
  IG-Unsafe-Bereich. Stills unter `_intern/review/`.

**Geliefert (Ergebnisse/Renders/):**
- `Untertitel_CutterAd_v1.mov` — ProRes 4444 Alpha, 1080×1920, 25 fps, 77 s.
  In Premiere einfach über den Schnitt legen, hinten auf Videolänge kürzen.
- `Untertitel_CutterAd_v1_preview.mp4` — H264-Sichtkopie (schwarzer BG).

**Entscheidungen:**
- Akzentfarbe nur NIRO-Grün (eine Akzentfarbe = cleanster Look), Blau bewusst
  weggelassen. CTA-Jobtitel „Cutter (m/w/d)" gemäß m/w/d-Regel.
- Studio-Props zum Justieren: `timeOffsetSec` (Feinsync), `captionShiftY`
  (Band vertikal), `jobTitle`/`ctaText`/`nameInsertText`, Extras abschaltbar.

**Offen:**
- CTA-Stelle 1:09 gegenhören: Scribe transkribierte „trage ich dich gerne
  unten ein", gesetzt ist „trag dich gerne unten ein" — falls David wirklich
  „trage ich dich" sagt, 1 Wort in `transcript.ts` ändern + Re-Render.
- Face Zone = Standard (Gesicht oben-mittig) angenommen; Footage lag nicht
  vor. Falls Gesicht tiefer sitzt: `captionShiftY` nutzen.
- Render-Spiegel `tools/motion/public-niro/` angelegt (ohne Videodateien).

## Session 2026-08-07 (V2, Feedback David)

- „semi-professionell" → nur noch „professionell" im Untertitel
  (Kundenwunsch; Achtung: O-Ton sagt weiterhin „semi-professionell" —
  ggf. Audio entsprechend schneiden).
- CTA-Finale-Jobtitel: „Cutter & Videograf (m/w/d)".
- Mehr Abwechslung: neuer Kicker-Stil (Versalzeile + großes Hauptwort) bei
  „Verstärkung." und „sehr viel rumkommen."; „genau für dich." als eigener
  Mehrwort-Punch; tragende Grün-Wörter zusätzlich größer/fetter im Satz
  (Mixed-Size, Baseline-ausgerichtet): Videos, professionell, Hauptjob.,
  NIRO., Marketingagentur, glücklicher, Qualität, delivern.
- Review-Stills v2 geprüft (Band/Zonen ok), geliefert:
  `Untertitel_CutterAd_v2.mov` (ProRes 4444 Alpha) + `_v2_preview.mp4`.
  V1 bleibt zum Vergleich liegen.
