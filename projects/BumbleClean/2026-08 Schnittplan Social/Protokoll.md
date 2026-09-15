# Protokoll — BumbleClean · 2026-08 Schnittplan Social

## 2026-08-09 — V1 „Lack-Edit": Animations-Overlay (Ansatz „Silent Luxury")

**Input:** `Videos Ohne Animation/Bumbleclean Video 1 Lack-Edit.mov` (2160×3840, 25 fps, HEVC 10-bit, 22,64 s = 566 Frames). Analyse: Drei-Akt-Struktur — Arbeit (0–10,1 s), Bass-Drop exakt bei 10,12 s → Glanz-Phase auf ~94-BPM-Beat, ab 17,8 s Gold-Flare in 4,6 s statischen Hero-Endshot.

**Komposition:** `tools/motion/src/clients/bumble-clean/projects/schnittplan-social/V1LackEdit.tsx`, Comp-ID `bumble-clean-v1-lack-edit` (portrait-4k, 25 fps, 566 F, transparent). Symlink `public/projects/bumble-clean-schnittplan` → `Videos Ohne Animation/` (Preview-Unterlage via Prop `zeigeVideo`). Public-Spiegel `public-bumble-clean/` angelegt (rsync ohne mov/mp4/wav, 169 MB).

**Animierte Elemente** (Frames @25fps):
- f010–058 Hook „19 JAHRE ALTER LACK." (Letter-Spacing-Einflug; 19 Jahre = MJ 2007)
- f065–115 Mini-Chip „⬡ POLITUR · STUFE 1" unten links
- f250–266 Hexagon-Puls + Echo exakt auf dem Drop (10,12 s) — bewusst kein Fullscreen-Wipe
- f317–442 Glass-Chip „EINSTUFIGE POLITUR", Gold-Badge „AB 199 €" dockt auf Beat 7 an (14,60 s)
- f444–456 Waben-Silhouette im Gold-Flare des Schnitts
- f461–560 Endcard: 7 Logo-Waben als Stroke-Draw (3-F-Stagger), Wortmarke, „CAR DETAILING", Gold-Linie, „TERMIN PER DM", „bumble-clean.de · Bad Rappenau"; globaler Fade-out f548–560

**Design-Entscheidungen:**
- Stil-Freigabe David: Ansatz A „Silent Luxury" (statt Kinetic Captions / HUD), Preis-Chip JA.
- CI identisch Messevideo (Gold #FFD700/#C9A227, Inter, Radius 24, Glass-Chips), aber Glass dunkler (rgba(10,10,10,0.38)) — liegt auf Video statt auf Schwarz.
- **Preis „ab 199 €" website-belegt** (bumble-clean.de am 2026-08-09 geprüft: „Einstufige Politur ab 199 €"). Achtung: Messevideo-Slides zeigen noch ALTE Pakete (Quick Fix/Basic/Premium Care) — Website wurde zwischenzeitlich umgestellt; separates To-do angelegt.
- Alpha-Falle (WORKFLOW-Motion.md): kein overflow:hidden in den Chips → auf Gold-Shimmer verzichtet.
- Musik-Raster: Beat ≈ 0,64 s ab Drop 10,12 s; Chip-Timings liegen auf Beat 4 und 7, Flare = Beat 12. Timings nicht verschieben, ohne den Schnitt zu prüfen.

**Pre-Delivery-Review (CLAUDE.md):** 6 Stills (f30/f90/f256/f380/f500/f545) mit Video-Unterlage + Safe-Zone-Guides geprüft: alle Elemente in der Safe Zone, keine Gesichts-Überdeckung, Endcard lässt die Front frei. Fix nach Review: Web-Zeile der Endcard auf Weight 600 + Textschatten (lag auf heller Stoßfänger-Reflexkante). Final-Render mit `showGuides:false` (Defaults).

**Renders** (`Ergebnisse/Renders/`):
- `V1 Lack-Edit Animation-Overlay ProRes4444.mov` — 2160×3840, ProRes 4444 + Alpha, 25 fps. In Resolve als oberste Spur über den Schnitt legen (Position 0/0, 100 %).
- `V1 Lack-Edit PREVIEW mit Animation.mp4` — 1080×1920 H.264, Animation auf Video gebrannt (nur zur Ansicht, NICHT posten — Grade fehlt).

**Hinweis Re-Render:** Default `zeigeVideo` steht seit 2026-08-09 auf `true` (Studio-Preview mit Video-Unterlage). Beim Alpha-Render zwingend `--props='{"zeigeVideo":false}'` anhängen, sonst wird das Video eingebrannt.

**Revision 2 (2026-08-09, Feedback David in Studio-Preview):**
- Preis aus dem Mittelteil-Chip entfernt — Chip zeigt nur noch „⬡ EINSTUFIGE POLITUR"; Preis erscheint erst in der Endcard als Gold-Zeile „EINSTUFIGE POLITUR · AB 199 €" (f494 ff., POP-Spring).
- Endcard-Lesbarkeit: radialer Scrim (rgba-schwarz 0,55 → 0, randlos, alpha-sicher) hinter dem Textblock; „CAR DETAILING" auf helles Gold, CTA auf Weight 800/46, stärkere Textschatten; Block rückt bis y1068 (Web-Zeile).
- Beide Renders neu erzeugt (gleiche Dateinamen, --overwrite).

## 2026-08-09 — V2 „Interior-Deep-Clean": Overlay + finale Composites

**Input:** `Videos Ohne Animation/Bumbleclean Video 2 Interior-Deep-Clean.mov` (2160×3840, 25 fps, 50,48 s = 1262 F). Struktur: Cockpit-Arbeit 0–18 s, Matten-Block 18–36,6 s, Drop-Cut bei 36,64 s → Result-Beauty-Cuts, ab 47,6 s ruhiger Lenkrad-Schluss.

**Komposition:** `V2InteriorDeepClean.tsx`, Comp-ID `bumble-clean-v2-interior-deep-clean`. Gemeinsame Bausteine nach `shared/motion-kit.tsx` extrahiert (Hexagons, HexPuls, GlassChip, Stage, CI-Konstanten) — V1 nutzt noch lokale Kopien (gerendert/abgenommen, bei nächster Änderung umziehen). Elemente: Hook „WAIT FOR THE RESULT…" mit Punkte-Loop (Davids Vorgabe) f12–88, Chips „INTERIOR DEEP CLEAN" f113–163 + „MATTEN · TIEFENREINIGUNG" f455–515, HexPuls auf Drop f913–929, „THE RESULT."-Gold-Pop f918–950 (Payoff, endet vor Leuchtkasten-Shot ~38 s), Endcard kompakt f1184–1254 mit „INNENAUFBEREITUNG · AB 119 €" (website-belegt). Stills-Review (f40/130/480/924/1230): Safe Zones ✓, keine Kollision mit Kontakt-Element oben rechts im Schluss-Shot.

**Finale Composites (Davids Auftrag: „beide mit Animation und Audio, nicht größer als Quelle, gleiche Auflösung"):**
ffmpeg-Overlay (ProRes-4444-Alpha auf Quelle), hevc_videotoolbox Main 10 (wie Quellen), AAC 256k aus dem Original-PCM, faststart.
- `V1 Lack-Edit FINAL.mp4` — 25,2 MB (Quelle 27,7) ✓, 2160×3840, 22,64 s
- `V2 Interior-Deep-Clean FINAL.mp4` — 59,7 MB (Quelle 63,9) ✓, 2160×3840, 50,48 s
- dazu `V2 Interior-Deep-Clean Animation-Overlay ProRes4444.mov` als Archiv/Resolve-Overlay

## 2026-08-29 — ⚠️ Website-Preisänderung betrifft V1

Website-Check (bumble-clean.de, 29.08.2026): **„Einstufige Politur ab 199 €" wurde von der Website entfernt** — Lackkorrektur gibt es nur noch als „Komplett + Politur ab 349 €". Neuer Claim: „Showroom-Finish. Ohne Kompromisse."
**Folge:** `V1 Lack-Edit FINAL.mp4` und das V1-Overlay zeigen „EINSTUFIGE POLITUR · AB 199 €" — nicht mehr website-belegt. Vor Veröffentlichung: Preis-Chip + Endcard-Preiszeile in `V1LackEdit.tsx` anpassen (Davids Entscheidung: „ab 349 €" nennen oder Preis ganz raus) und neu rendern/komponieren. V2 („Innenaufbereitung ab 119 €") ist weiterhin korrekt. Schnittplan V6 wurde aktualisiert.

**Offen:**
- Davids finale Abnahme V1-Overlay (Revision 2) und V2 (Erstfassung) — Finals ggf. neu komponieren.
- **V1: Preis-Fix wegen Website-Änderung (siehe 29.08.) — vor dem Posten!**
- V3–V7 bei Anlieferung: Muster V2 + motion-kit.
- V2–V7: gleiche Comp-Struktur wiederverwendbar (Datei pro Video unter `projects/schnittplan-social/`).
- Messevideo-Preisstand aktualisieren (separater Task, Chip erstellt).
