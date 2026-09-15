# Protokoll — BumbleClean · 2026-08 Cinematic Ad „Was die Zeit nimmt"

## 2026-08-29 — Konzept

Konzept-PDF erstellt (`AD-KONZEPT Was die Zeit nimmt.pdf`): 9:16, max 40 s geplant, Story „Die Zeit ist der Feind", KI-Shot-Prompts (David generiert selbst, Image-to-Video mit Boxster-Referenzfotos), deutsche KI-VO (ElevenLabs). VO-Findung über mehrere Runden: poetisch (verworfen, kitschig) → 4 nüchterne Richtungen → D+ minimal → Meta-Ebene mit Vierte-Wand-Bruch. Finaler gesprochener Schluss: Website-Satz „Ein Fahrzeug ist erst fertig, wenn jedes Detail stimmt." (Variante A, website-belegt 29.08.). Claim-Änderung der Website eingearbeitet („Showroom-Finish. Ohne Kompromisse."), dabei Preis-Inkonsistenz in V1 der Social-Serie entdeckt (siehe Protokoll Schnittplan Social).

## 2026-08-29 — Animations-Overlay zum fertigen Schnitt

**Input:** `Cinemtatic Werbeanzeige.mov` — 1080×1920 (nativ, nicht 4K), 25 fps, HEVC + PCM, **50,2 s** (Konzept war 38 s; Schnitt erweitert: S/W-Verfalls-Welt mit Fremdfahrzeugen inkl. Huracán, Duftbaum-Brand-Shot, Schäden-Katalog, Schwarz-Atemloch bei 18 s, 18 s stumme Arbeitsstrecke, Beauty-Auflösung, statische Front mit Rollup ab ~47 s, Video-Fade ab ~49,4 s).

**Analyse:** Szenen-Erkennung (~50 Cuts, keine nach 35,2 außer weichen Übergängen), 100 Frames (2 fps) auf 5 Kontaktbögen, Waveform, **Whisper-Transkription (faster-whisper base, Wort-Timestamps)** — VO im Schnitt weicht vom Konzept ab: „liebst"-Zeile entfällt, „Es ist NICHT ZU SPÄT" → „Es ist ZEIT, etwas dagegen zu tun", Schluss = Website-Satz + „BumbleClean" (gesprochen bei 41,0 s). Captions wortgleich zur Transkription gesetzt.

**Komposition:** `tools/motion/src/clients/bumble-clean/projects/cinematic-ad/AdZeit.tsx`, Comp-ID `bumble-clean-ad-zeit` (portrait 1080×1920, 1255 F). Kein Chip-/Grafik-Einsatz — nur:
- „🔊 MIT TON."-Hinweis f12–65 (Sound-Off-Feeds)
- 5 VO-Captions (f166–445 + f898–995) mit weichem Unterkanten-Verlauf (Lesbarkeit auf hellen Kratzer-Shots, u. a. rote Haube)
- Stumme Strecke 17,8–35,9 s bewusst ohne jedes Overlay
- Endcard: Waben-Draw startet exakt auf gesprochenem „BumbleClean" (f1025), Claim „SHOWROOM-FINISH. OHNE KOMPROMISSE." + Gold-Button „TERMIN BUCHEN →" auf der Musik-Auflösung (f1115/1135), „bumble-clean.de · Bad Rappenau", Button-Puls bei 47,5 s, Fade synchron zum Video-Fade (f1235–1247)

**Pre-Delivery-Review (CLAUDE.md):** 9 Stills (f30/200/280/340/410/950/1060/1170/1240) mit Guides: Safe Zones ✓, keine Face-Konflikte ✓, kritischster Fall (weiße Caption auf roter Kratzer-Haube) durch Verlauf gelöst ✓. Final-Render ohne Guides.

**Renders** (`Ergebnisse/Renders/`):
- `Ad Was die Zeit nimmt - Animation-Overlay ProRes4444.mov` — Alpha-Overlay 1080×1920 (Resolve-Spur)
- `Ad Was die Zeit nimmt FINAL.mp4` — fertiges Composite mit Original-Audio, H.264 (Meta-tauglich), Ziel ≤ Quellgröße (63,1 MB)

**Revision 2 (2026-08-29, Feedback David):** Captions → große **Kinetic-Typo-Statements**: Wort-für-Wort-Pop synchron zu den Whisper-Wort-Timestamps, Inter 800 Uppercase zentriert (56–84 px), Schlüsselwörter in Gold mit Glow (WERBUNG/ECHT/INTERIEUR/ZEIT/DETAIL), Radial-Scrim hinter dem Block statt Unterkanten-Verlauf. „MIT TON."-Hinweis komplett entfernt. Beide Renders neu erzeugt (--overwrite).

**Offen:**
- Davids Abnahme; Caption-Wortlaut ggf. gegen finales VO-Feintuning prüfen.
- Meta-Setup: Kampagne mit Button „Jetzt buchen" → Online-Buchung, UTM-Parameter setzen (siehe Konzept-PDF Abschnitt 6/7).
- Optional aus Konzept-Review: 20–22-s-Cutdown + Hook-A/B-Varianten (erste 3 s) für Performance-Tests.
