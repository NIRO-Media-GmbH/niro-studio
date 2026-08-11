# Sauber Entsorgen — Leistungen-Overlay (12s Einschub)

**Datum:** 2026-06-26
**Client:** `sauber-entsorgen` (neu)
**Projekt:** `leistungen-overlay`

## Ziel

12-Sekunden-Alpha-Overlay (16:9, 1920×1080, 25 fps, 300 Frames), das in der Mitte
eines ~2-minütigen Erklärvideos über das Footage des Geschäftsführers gelegt wird
und dessen gesprochene Leistungen visualisiert. Kein CTA, kein End-Slide, kein
sichtbares Gesicht im Clip — der Clip ist ein reines Grafik-Overlay.

**Transkript (Sprecher = GF):**
> „Wir übernehmen Haushaltsauflösungen und Nachlassauflösungen, einzelne Keller,
> Dachböden, Garagen, genau wie Firmen und Insolvenzauflösungen. Und wenn es auch
> mal schnell gehen muss, auch natürlich kurzfristig."

## Rahmen

- Format: `landscape` (1920×1080), `fps: 25`, `durationInSeconds: 12`, `transparent: true`
- Export: ProRes 4444 (Alpha) zum Drüberlegen aufs Footage
- `transparent: true` → `AbsoluteFill` ohne Hintergrund (Default-Muster wie bremsen-schneider-Imagefilm)

## Marke (aus Logo-SVG gesampelt)

- Primär-Blau `#3B5998`, Sekundär-Grau `#9CA3AF`, Anthrazit-Text `#2B3140`, Weiß `#FFFFFF`
- Akzent (Glow/Unterstreichung): aufgehelltes Blau `#5B86D6`
- Font: Inter (wie übrige Projekte, via `@remotion/google-fonts`)

## Stil

„dynamisch + clean": weiße/leicht frostige Lower-Third-Pille mit Anthrazit-Text,
Clip-Path-Reveal des Keywords, Spring-Einflug von unten, animierte blaue
Akzent-Unterstreichung mit Glow, flache Linien-Icons. Legibel über beliebigem
Footage. Bildmitte (Gesichtszone) bleibt frei.

## Beat-Plan (Zeiten als Props feinjustierbar)

| # | Zeit (s)   | Typ      | Inhalt                                   | Icon              |
|---|------------|----------|------------------------------------------|-------------------|
| 1 | 0.0–2.2    | Keyword  | Haushaltsauflösungen                     | haus              |
| 2 | 2.2–3.8    | Keyword  | Nachlassauflösungen                      | nachlass          |
| 3 | 3.8–6.6    | Chips    | Keller · Dachboden · Garage (gestaffelt) | keller/dachboden/garage |
| 4 | 6.6–9.2    | Keyword  | Firmen- & Insolvenzauflösungen           | firma             |
| 5 | 9.2–12.0   | Keyword  | Kurzfristig & schnell                    | express           |

## Architektur (spiegelt `bremsen-schneider`-Overlay-Muster)

```
src/clients/sauber-entsorgen/
  brand.json                       # CI-Farben/Fonts
  components/
    constants.ts                   # Farben, SAFE (16:9), Spring-Configs, EXIT_LEAD
    useExit.ts                     # Exit-Fade/Slide am Sequence-Ende (Muster wie bremsen)
    ServiceIcons.tsx               # Inline-SVG-Linien-Icons (currentColor), name-Enum
    KeywordLowerThird.tsx          # Lower-Third-Pille: Icon-Badge + Keyword-Reveal + Akzentlinie
    ServiceChips.tsx               # gestaffelte Chip-Reihe (Icon + Label)
    index.ts                       # Re-Exports
  projects/leistungen-overlay/
    transcript.ts                  # Beats (KEYWORDS[], CHIP_GROUPS[]) + Typen
    Composition.tsx                # Schema + Defaults + Komposition, ReviewOverlay integriert
```

Registrierung in `src/Root.tsx` unter neuem `Folder name="SauberEntsorgen"`,
`calculateMetadata={getCalculateMetadata}`.

### Komponenten-Verträge

- **ServiceIcon** `{ name: "haus"|"nachlass"|"keller"|"dachboden"|"garage"|"firma"|"express", size, color }`
  → reines SVG, `stroke=currentColor`, keine Animation (Animation kommt vom Container).
- **KeywordLowerThird** `{ word, icon, align?, offsetX?, offsetY? }`
  → positioniert sich im unteren Drittel (unter Gesichtszone), Clip-Reveal + Spring-Einflug,
  Auto-Scale für lange Wörter (wie `KeywordReveal`), Exit via `useExit`.
- **ServiceChips** `{ chips: {label, icon}[], offsetX?, offsetY? }`
  → horizontale Reihe, Stagger-Einflug pro Chip, Exit via `useExit`.

### Schema (Studio-editierbar)

`projectPropsSchema.extend({ keywords: keywordSchema[], chipGroups: chipGroupSchema[] })`
- `keywordSchema`: `{ word, icon(enum), startSec, durationSec, align?, offsetX?, offsetY? }`
- `chipGroupSchema`: `{ startSec, durationSec, chips: {label, icon}[] }`

## Gesichts-/Safe-Zone (CLAUDE.md)

- `SAFE` (16:9): top 0.05, bottom 0.93, left 0.05, right 0.95 (title-safe)
- Default-Face-Zone (zentrierter Talking-Head): `{ top:0.04, bottom:0.74, left:0.28, right:0.72 }`
- Alle Overlays sitzen bei y ≳ 0.76 → unter der Gesichtszone
- `ReviewOverlay` integriert, `review.showGuides` default `false` (nie im Export)
- Vor Auslieferung: Guides an, Frame-by-Frame Face-Zone prüfen; Position der Face-Zone
  ggf. an die echte GF-Position im Footage anpassen (per `review.faceZone`-Override).

## Nicht im Scope (YAGNI)

- Kein Voiceover/Audio (liegt im Haupt-Footage), keine generierte Stimme
- Kein Logo-Bild-Reveal, kein CTA/End-Card, keine Telefon/Website-Einblendung
- Keine Hintergrundgrafik (Overlay ist transparent)
