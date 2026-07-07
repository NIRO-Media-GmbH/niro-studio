# MAN Lagerlogistik — CTA Endslide (Design Spec)

**Date:** 2026-06-18
**Client:** MAN Truck & Bus (new client `man`)
**Project:** Recruiting-Video Endslide für Ausbildung „Fachkraft für Lagerlogistik"
**Owner:** NIRO Media (david@niro-media.de)

## 1. Purpose

Eine moderne, stylische Call-to-Action-Endslide als Standalone-Clip, der ans Recruiting-Video angehängt wird. Sie greift den Look der bestehenden MAN-Still-Ads auf (dunkler BG + MAN-Rot, weißes Logo, rote Pill-Badges/Chips, große Condensed-Headline), aber reduziert auf den CTA-Fokus und voll animiert.

## 2. Decisions (locked)

- **Format:** 9:16 portrait, 1080×1920, 30fps, **8 Sekunden** (240 Frames)
- **Inhalt:** Reduziert / CTA-Fokus — Eyebrow-Badge + Headline + 3–4 Top-Benefits + starker CTA-Button + Sub-Text
- **Hintergrund:** Animierter MAN-Grafik-BG (kein Foto) — keine Foto-Abhängigkeit, voll wiederverwendbar
- **Animationsstil:** „Krank" / over-the-top — heftige Springs, Glow-Pulse, Micro-Shake, schnell gestaffelte Einflüge

## 3. Brand

Offizielle MAN-Farben (von man.eu / MAN Brand Guidelines):

| Rolle | Name | Hex | RGB |
|-------|------|-----|-----|
| Primary | MAN Red „Red Ribbon" | `#E30045` | 227, 0, 69 |
| Secondary dark | „Venetian Red" | `#720022` | 114, 0, 34 |
| Text / Logo | Weiß | `#FFFFFF` | 255, 255, 255 |
| Basis (dunkel) | — | `#12000A` | abgeleitet, near-black mit Rotstich |

**Fonts:** MAN Global (lokale TTFs aus `Videos/Man Lagerausbildung/MAN-Global_Desktop (1)/`)
- Headline: `MAN_Global-BoldCondensed`
- Eyebrow / Chips / CTA: `MAN_Global-Bold` / `MAN_Global-Medium`
- Body / Sub: `MAN_Global-Regular`

**Logos:** `MANlogoWeiss.png` (weißes Logo, oben), `man_footer_logo.png` (optional Footer).

## 4. Content (default props, alle editierbar im Studio)

- **Eyebrow / Badge:** „STARTE DEINE AUSBILDUNG"
- **Headline:** „FACHKRAFT FÜR LAGERLOGISTIK" (zweizeilig umbrochen) + kleiner Zusatz „(m/w/d)"
- **Benefits (4 Chips):** „Attraktive Vergütung" · „30 Tage Urlaub" · „Kostenloses iPad" · „36h Woche"
- **CTA-Button:** „Jetzt in unter 1 Min. bewerben"
- **Sub-Text:** „In Karlsruhe – Ohne Lebenslauf!"

## 5. Architecture & Integration

Folgt den bestehenden Projekt-Konventionen (vgl. `src/clients/top-fotografie/projects/endscreen-job/Composition.tsx`):

- **Neuer Client:** `src/clients/man/brand.json` (colors + fonts + logo Pfade)
- **Assets:**
  - `public/clients/man/logo-weiss.png` (kopiert aus `MANlogoWeiss.png`)
  - `public/clients/man/footer-logo.png` (kopiert aus `man_footer_logo.png`)
  - `public/fonts/man/MAN_Global-*.ttf` (kopierte Font-Dateien)
- **Composition:** `src/clients/man/projects/lager-ausbildung-cta/Composition.tsx`
- **Registry:** Eintrag in `src/Root.tsx`
- **Schema:** `manLagerCtaSchema = projectPropsSchema.extend({ eyebrow, headline, headlineSuffix, benefits: string[], ctaText, subText })`
- **Fonts:** Lokal geladen via `@remotion/fonts` `loadFont()` + `staticFile()` (Family-Namen `"MAN Global"` / `"MAN Global Cond"`). Genaue Lade-Mechanik beim Implementieren am bestehenden Pattern verifizieren.
- **Pflicht-Komponenten:** Inhalt in `<SafeZone>`; `<ReviewOverlay>` konditional auf `review?.showGuides`.

## 6. Layout (innerhalb Safe Zone, top→bottom)

1. **MAN-Logo** (weiß) — oben mittig, ~10% top
2. **Eyebrow-Badge** — rote Pill (`#E30045`), weißer Text, uppercase
3. **Headline** — weiß, `BoldCondensed`, sehr groß, zweizeilig, uppercase; roter **Highlight-Sweep** hinter/unter dem Wort „LAGERLOGISTIK"; „(m/w/d)" klein hochgestellt
4. **Benefit-Chips** — 4 rote Pills, zentriert, umbrechend (2×2 oder flow), weißer Bold-Text
5. **CTA-Button** — weiße abgerundete Box mit Schatten, Text in MAN-Rot, prominent; darunter Sub-Text klein/kursiv weiß

Alle Elemente bleiben im grünen Safe Zone; CTA NICHT im unteren Unsafe-Bereich (IG/TikTok-UI). Horizontaler Pad ~5%.

## 7. Animation Timeline (30fps, ~240 Frames)

| Frame | Element | Bewegung |
|-------|---------|----------|
| 0–240 | Hintergrund-Glow | Radialer MAN-Rot-Glow pulsiert kontinuierlich; Grid/Partikel driften langsam |
| 0–12 | Logo | Punch-In (Scale 0.7→1, spring PUNCH) + Fade |
| 12–28 | Eyebrow-Badge | Slide+Scale-In, harter Spring; Pill-Breite sweept auf |
| 25–70 | Headline | Zeilenweise „Smash"-In (Scale 1.15→1 + Micro-Shake + Fade); roter Highlight-Sweep (`scaleX` 0→1) hinter „LAGERLOGISTIK" |
| 70–110 | Chips | Schnell gestaffelt (delay ~5f/Chip): Pop von unten (translateY + Scale + Fade) |
| 105–125 | CTA | Scale-In (0.8→1, PUNCH) + Glow-Pulse-Ring; Sub-Text Fade-In leicht verzögert |
| 125–240 | Halten | CTA dezenter Dauer-Glow-Puls; schwebende Partikel als „Leben"; alles bleibt im Bild |

Spring-Configs: `PUNCH = {damping:10, stiffness:180, mass:1}`, `SMOOTH = {damping:20, stiffness:100, mass:1, overshootClamping:true}`. Micro-Shake nur kurz beim Headline-Eingang (kein Dauer-Wackeln), darf NICHT in die Face-Zone überschwingen.

## 8. Pre-Delivery Review (CLAUDE.md Checkliste)

- `review.showGuides`/`showSafeZone`/`showFaceZone` zum Prüfen aktivieren
- Frame-by-frame: KEIN Element überdeckt die Gesichts-Zone; Spring-Overshoots prüfen
- Alle Texte im Safe Zone; CTA nicht im unteren Unsafe-Bereich
- `review.showGuides: false` vor jedem finalen Render
- Default-Props: `review.showGuides: false`

## 9. Out of Scope (YAGNI)

- Keine Foto-/Footage-Integration
- Kein QR-Code (CTA ist Text); kann später als Prop ergänzt werden
- Keine Audio/Voiceover
- Keine weiteren Formate (1:1 / 16:9) in diesem Durchgang
