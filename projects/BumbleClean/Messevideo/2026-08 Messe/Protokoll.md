# Protokoll — BumbleClean / Messevideo / 2026-08 Messe

## Session 2026-08-01 (erste Session)

**Was gemacht:**
- Neuer Kunde BumbleClean (Henor Brahimi, Premium-Autoaufbereitung, Bad Rappenau)
  im Studio angelegt: Projektstruktur, Motion-Client `bumble-clean`, CI von
  bumble-clean.de abgeleitet.
- 16:9-Messe-Master gebaut (`bumble-clean-messe-master`, 1920×1080 @ 25fps,
  4607 Frames = 03:04:07): 9:16-Fenster 540×960 fest rechts (Geometrie nach
  MAN-WZ-Master), links Grafikfläche mit Logo + rotierenden Info-Slides
  (6 Slides × 2 Runden = ~15,3 s je Slot), konstanter Footer, Waben-Ambient,
  loop-nahtlos (sin-Drifts mit ganzen Perioden, Slide-Zyklus).
- David-Vorgabe eingearbeitet: Das Video zeigt nur „nice shots" ohne
  Reihenfolge — die Grafik-Ebene steht komplett für sich (kein Video-Sync,
  jede Slide selbsterklärend, Marke konstant). Dazu Davids 5-s-Regel
  umgesetzt: doppelter Slide-Durchlauf, Gold-Shimmer über die Chips
  (~7,6-s-Zyklus, je Chip versetzt, Opazität 0,16), pulsierende Gold-Linie
  (5-s-Zyklus), atmende Sterne (4-s-Zyklus).
- Slides (Stand v2): 1 Claim „Showroom-Finish" · 2 Pakete (149/249/349 €) ·
  3 Einzelleistungen (49/59/99/199 €) · 4 „5,0 auf Google" + Zitat ·
  5 Kontakt/Öffnungszeiten. Alle Inhalte/Preise von bumble-clean.de.
  (Ursprüngliche Steinschlag-Slide stammte aus dem Dreh-Briefing, nicht
  von der Website — von David entfernt, siehe Nachtrag v2.)
- Pre-Delivery Review: 5 Testframes mit Safe-Zone-Guides gerendert und
  geprüft (`_intern/preview/`); Zitat-Umbruch Slide 5 gefixt. Grafik endet
  bei x=1064, Fenster ab x=1200 — nichts überdeckt das Video.

- Render-Pipeline vorab verifiziert (während Davids Export rendert):
  Loop-Naht-Frames 0/4606 identisch ✓; Dummy aus echtem B-Roll-Clip
  (a7MK4_0012, auf 1080×1920 @ 25fps transkodiert) durch die komplette
  Kette gerendert (Symlink → staticFile → OffthreadVideo → H.264) ✓;
  10-s-Proberender: 250 Frames ≈ 54 s → Final (4607 Frames) ≈ 15–17 Min.
  Dummy liegt als `_pipeline-test-dummy.mp4` in Material/Video (Studio
  zeigt damit sofort echtes Video); wird beim Final-Render entfernt.

**Geliefert:**
- **FINAL: `Ergebnisse/Renders/bumbleclean-messe-loop-4k.mp4`** — 3840×2160
  @ 25fps, 4607 Frames, H.264 CRF 22, 195 MB (Limit 500 MB). Quell-Export
  `Material/Video/Messevideo.mp4` (2160×3840, punktgenau 4607 Frames) wird
  im Fenster nativ halbiert. Stichproben 20 s/130 s geprüft, Renderzeit ≈ 9 Min.
- `tools/motion/src/clients/bumble-clean/` (brand.json + projects/messevideo/Composition.tsx)
- `tools/motion/public/clients/bumble-clean/logo.png` (Website-Logo, 297 px)
- Symlink `tools/motion/public/projects/bumble-clean-messevideo` → Material/Video
- Review-Frames in `_intern/preview/`

**CI-Entscheidungen (von bumble-clean.de abgeleitet):**
- Schwarz #050505, Gold #FFD700 (tief #C9A227, hell #FFE27A), Weiß, Muted #CFCFCF
- Glass-Panels rgba(255,255,255,0.06) + Border 0.18, Radius 24, Schatten weich
- Font Inter (Website-Font), Headlines Versalien 800
- Waben-Motiv (Logo-Hexagone) als dezentes Ambient + Platzhalter-Emblem
- Logo: Website-Asset (297 px) ist final — kein größeres vorhanden
  (David 2026-08-01)

**Nachtrag Final (gleiche Session):** David wollte 4K, < 500 MB, runde
Ecken — Ecken waren bereits drin (CI-Radius 24 ≙ 48 px bei 4K, per
Ecken-Crop belegt). Export kam als `Messevideo.mp4` (4K-Hochkant),
ffprobe-Check exakt Soll. 4K-Final gerendert und geprüft, Dummy gelöscht.

**Nachtrag v2 (gleiche Session):**
- **Steinschlag-Slide entfernt** (stand nicht auf der Website; Quelle war
  Davids Dreh-Briefing). Neue David-Regel, gilt ab sofort für alle Kunden:
  **In Deliverables nur Website-belegte Inhalte** — nichts aus Briefings
  ableiten. Jetzt 5 Slides × 2 Runden à ~18,4 s.
- **Logo größer + schärfer:** Website-Asset (297 px) via Higgsfield-Upscale
  auf 4096 px (Wabe zeigt jetzt sichtbar die Hummel, Schrift artefaktfrei).
  Erster Ansatz mixBlendMode "screen" scheiterte (Stage-Stacking-Context
  isoliert das Img — Blend griff nie, messbar schwarzer Kasten Y16 vs.
  Bühne Y20). Lösung: Alpha Luma-basiert rekonstruiert (×3 mit Klipp —
  Goldkerne opak, Kanten weich), normales Compositing. Messbeleg am
  Testframe: innen = außen = Y20. Design-Breite 260 → 340 px.
  Datei: `logo-4x.png` (RGBA).
- v2-Final neu gerendert (ersetzt v1-Datei gleichen Namens).

**Offen:**
- Abnahme des Finals durch David/Henor; danach ggf. Übergabe-Format klären
  (USB-Stick fürs Messe-TV o. Ä.).
- Ad-Konzeption (Paid Ads Meta + TikTok, 9 Ideen vorgestellt) pausiert —
  Davids Auswahl steht aus.
- Loop-Naht: Slide 6 blendet aus, Slide 1 ein — Video-Hartschnitt an der
  Naht macht der TV-Loop; ggf. prüfen, ob der Schnitt loopbar endet.
- Ad-Konzeption (Paid Ads Meta + TikTok, 9 Ideen vorgestellt) pausiert —
  Davids Auswahl steht aus.
