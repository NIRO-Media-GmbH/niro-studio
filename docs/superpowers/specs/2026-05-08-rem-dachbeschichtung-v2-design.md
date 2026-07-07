# REM Dachbeschichtung V2 — Design Spec

## Overview

A 37-second premium motion graphics video for REM Malerfachbetrieb showcasing their roof coating ("Dachbeschichtung") service. Silent social media ad — purely visual with animated text, no voiceover.

**Visual direction:** Minimalist / Apple-like. Clean compositions, thin lines, generous negative space, smooth easing. The opposite of the existing v1 clay/toy style.

**New project alongside v1** at `src/clients/rem-maler/projects/dachbeschichtung-v2/`.

## Technical Specs

- Resolution: 3840 x 2160 (4K, 16:9 landscape)
- Frame rate: 25 fps
- Total duration: 925 frames (37 seconds)
- Background: `#0D0D1A` (near-black navy)
- Rendering: All-SVG (`<svg viewBox="0 0 3840 2160">`)
- No logo needed

## Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| Background | `#0D0D1A` | Canvas fill |
| REM Red | `#D83C31` | Coating, CTAs, highlights |
| White | `#FFFFFF` | Text, house strokes |
| White 60% | `rgba(255,255,255,0.6)` | Secondary text, lines |
| Cream | `#F5E6D0` | House walls (if using fills) |
| Weathered grey | `#6B6B5A` | Aged roof state |
| Moss green | `#4A7A42` | Moss spots (desaturated) |
| Water blue | `#5AADFF` | Water droplets (sparingly) |

## File Structure

```
src/clients/rem-maler/projects/dachbeschichtung-v2/
├── Composition.tsx          # Main composition, scene orchestration
├── constants.ts             # Colors, timing, easing, geometry
├── components/
│   ├── MinimalHouse.tsx     # Persistent isometric house icon
│   ├── RainEffect.tsx       # Scene 1: rain lines, lightning, snow
│   ├── WeatheringEffect.tsx # Scene 2: cracks, color shift, dust
│   ├── MossEffect.tsx       # Scene 3: green circles, lichen patches
│   ├── CoatingWipe.tsx      # Scene 4: red wipe, glow edge, specular
│   ├── WaterProtection.tsx  # Scene 5: beading droplets, vapor wisps
│   ├── FinaleEffect.tsx     # Scene 6: ambient glow, sparkles
│   └── TextReveal.tsx       # Reusable staggered word fade-up
└── utils/
    └── easing.ts            # Apple easing curve helper
```

## Architecture

### Composition Structure

```tsx
<AbsoluteFill style={{ backgroundColor: '#0D0D1A' }}>
  <svg viewBox="0 0 3840 2160">
    <defs>{/* SVG filters: blur, glow */}</defs>

    {/* Persistent house — always renders, props driven by global frame */}
    <MinimalHouse roofColor={...} coatingProgress={...} scale={...} />

    {/* Scene effect layers — opacity-controlled, 30-frame overlaps */}
    <g opacity={scene1Opacity}><RainEffect frame={...} /></g>
    <g opacity={scene2Opacity}><WeatheringEffect frame={...} /></g>
    <g opacity={scene3Opacity}><MossEffect frame={...} /></g>
    <g opacity={scene4Opacity}><CoatingWipe frame={...} /></g>
    <g opacity={scene5Opacity}><WaterProtection frame={...} /></g>
    <g opacity={scene6Opacity}><FinaleEffect frame={...} /></g>

    {/* Text layer — on top */}
    <g opacity={scene1Opacity}>{/* Scene 1 text */}</g>
    ...
  </svg>

  {/* Review overlay (outside SVG, conditional) */}
  {props.review?.showGuides && <ReviewOverlay ... />}
</AbsoluteFill>
```

### Key Architectural Decisions

- **No `<Sequence>` wrappers:** Scenes overlap by 30 frames for cross-fades. Using frame-based opacity groups (`<g opacity={...}>`) instead of Sequences avoids unmounting during transitions.
- **All components local:** No shared code with v1. The visual style is fundamentally different.
- **Frame-driven state:** `Composition.tsx` computes all derived state (roof color, coating progress, scene opacities) from the global frame number and passes as props.
- **No studio-editable per-scene props:** Text content and timing are hardcoded in `constants.ts`. Keeps the schema simple.

### Scene Transition Formula

Each scene's opacity is computed as:
```ts
const opacity = interpolate(
  frame,
  [sceneStart, sceneStart + 30, sceneEnd - 30, sceneEnd],
  [0, 1, 1, 0],
  { easing: appleEase, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);
```

Exception: Scene 1 starts at full opacity (no fade-in). Scene 6 holds at full opacity (no fade-out).

## MinimalHouse Component

A persistent isometric house icon, always visible, receiving frame-driven props.

### Geometry
- Center position: `(1920, 1200)` — slightly below canvas center for text headroom
- Total size: ~800px wide, ~600px tall (small relative to 4K = generous negative space)
- Isometric angle: 30 degrees
- Three visible faces: front wall, right side wall, pitched roof (Satteldach)

### Rendering Style
- Thin white stroke: 2-3px, no fill or very subtle fill (`rgba(255,255,255,0.05)`)
- Roof tiles suggested with 3-4 thin horizontal lines (not individual tile detail)
- One front window, one side window, one door — minimal stroke rectangles
- No gradients, no shadows, no 3D depth tricks

### Dynamic Props
| Prop | Type | Description |
|------|------|-------------|
| `roofColor` | string | Interpolated: cream → grey → red |
| `coatingProgress` | number (0-1) | Left-to-right clipPath reveal |
| `crackOpacity` | number (0-1) | Fade for crack overlay |
| `mossOpacity` | number (0-1) | Fade for moss spots |
| `specularX` | number | Horizontal position of gloss sweep |
| `scale` | number | Subtle scale for finale (1.0→1.03) |
| `shake` | {x, y} | Camera shake offset during weathering |

### Coating Wipe Mechanic
A `<clipPath>` with a `<rect>` whose width animates from 0 to full roof width. The red coating surface is always present but clipped. A thin white `<line>` with `feGaussianBlur(stdDeviation=2)` follows the wipe edge.

## TextReveal Component

Reusable staggered word-by-word fade-up animation, used by all scenes.

### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `words` | string[] | — | Words to reveal |
| `startFrame` | number | — | Global frame for first word |
| `staggerFrames` | number | 12 | Delay between words |
| `fontSize` | number | — | SVG px |
| `color` | string | `#FFFFFF` | Text fill |
| `y` | number | — | Vertical position in SVG coords |
| `exitFrame` | number | — | When to fade out |
| `fontWeight` | number | 400 | Font weight |
| `glow` | boolean | false | Add blur glow filter behind text |
| `glowColor` | string | same as color | Glow tint |

### Animation Per Word
- **Enter:** `translateY(25px) → translateY(0)` + `opacity: 0→1` over 22 frames
- **Hold:** Stays visible
- **Exit:** `opacity: 1→0` over 20 frames (no movement)
- **Easing:** Apple cubic-bezier `(0.25, 0.1, 0.25, 1)`
- **Text anchor:** Always `middle`, x=1920 (centered)

## Scene Details

### Scene 1: WEATHER (Frames 0–125)

**Effects (RainEffect):**
- 15-20 thin white vertical `<line>` elements, 30% opacity, falling via `interpolate`
- 1 lightning flash: full-canvas `<rect>` at `rgba(255,255,255,0.05)` for 3 frames at ~frame 100
- 5-7 snowflake dots drifting in at frames 105-125

**Text:**
- Frame 20: "Ihr Dach." — 120px, centered above house
- Frame 45: "365 Tage. Jedes Wetter." — 80px, white 60%, below first text
- Frame 100: Both texts fade out

### Scene 2: WEATHERING (Frames 125–250)

**Effects (WeatheringEffect):**
- 4-5 crack `<path>` elements drawn via `strokeDashoffset` animation (white, 1.5px)
- Roof color shift: `interpolateColors` cream → grey over 80 frames
- 8-10 dust particles: tiny white circles drifting upward, very low opacity

**Text:**
- Frame 140: "Jahre vergehen." — 100px, centered
- Frame 180: "Risse." → "Verwitterung." → "Substanzverlust." — 80px, staggered 15 frames
- Frame 240: All text fades out

### Scene 3: MOSS (Frames 250–425)

**Effects (MossEffect):**
- 8-10 green circles (`#4A7A42`, 40% opacity) scaling 0→target with `appleEase`
- 3-4 lichen patches: slightly larger, yellow-green (`#6B8A42`), slower growth

**Text:**
- Frame 270: "Moos." → "Algen." → "Flechten." — 100px, staggered
- Frame 340: "Ohne Schutz zerfällt Ihr Dach." — 70px, white 50%
- Frame 410: All text fades out

### Scene 4: COATING / HERO (Frames 425–600)

**Effects (CoatingWipe):**
- Red `#D83C31` surface revealed via animated `<clipPath>` rect (left→right, ~100 frames)
- Wipe edge: thin white `<line>` with `feGaussianBlur(2)` glow
- Post-wipe specular sweep: white gradient moving left→right across roof
- Subtle house scale pulse: 1.0 → 1.02 → 1.0 over 30 frames

**Text:**
- Frame 440: "Professionelle" — 90px, white
- Frame 460: "Dachbeschichtung." — 120px, `#D83C31`, bold (700), with glow filter
- Frame 540: Both texts fade out

### Scene 5: WATER PROTECTION (Frames 600–775)

**Effects (WaterProtection):**
- 12-15 thin rain lines falling (same style as Scene 1)
- 6-8 water bead circles on roof surface: grow, slide down with gravity
- 3-4 vapor wisps: white paths rising upward, low opacity, `feGaussianBlur`

**Text:**
- Frame 620: "100% Wetterschutz." — 100px, white
- Frame 670: "Wasserabweisend." → "Langlebig." → "Schön." — 70px, staggered
- Frame 760: All text fades out

### Scene 6: FINALE (Frames 775–925)

**Effects (FinaleEffect):**
- Ambient glow: `<radialGradient>` with `#D83C31` at 8% opacity around house
- 2-3 sparkle stars: four-pointed SVG shapes with scale-in + pulse
- House scales to 1.03

**Text:**
- Frame 790: "REM Malerfachbetrieb" — 80px, white, letter-spacing +2px
- Frame 820: "rem-maler.de" — 60px, `#D83C31`
- Frame 850: "Jetzt Angebot anfragen →" — 50px, white 70%, subtle underline draw
- All text holds until end (no exit fade)

## Animation Principles

1. **Easing:** Always Apple ease `cubic-bezier(0.25, 0.1, 0.25, 1)`. Never linear. Never bouncy springs.
2. **Duration:** Text animations take 20-25 frames. Nothing instant.
3. **Stagger:** Multiple words stagger 10-15 frames apart.
4. **Text enter:** `translateY(25px) → 0` + `opacity 0→1`
5. **Text exit:** `opacity 1→0` only (no movement)
6. **Scale:** Max +/-3%
7. **Particles:** Few, well-placed. Max 15-20 rain drops, 8-10 moss blobs.

## Easing Utility

```ts
// utils/easing.ts
import { Easing } from 'remotion';

export const appleEase = Easing.bezier(0.25, 0.1, 0.25, 1);
```

All `interpolate()` calls use `{ easing: appleEase }`.

## Schema & Registration

**Schema:** Extends `projectPropsSchema` with no custom scene props.

**Default Props:**
```ts
{
  format: "landscape-4k",
  fps: 25,
  durationInSeconds: 37,
  transparent: false,
  review: { showGuides: false, showSafeZone: false, showFaceZone: false, showGrid: false, guideOpacity: 0.5 }
}
```

**Root.tsx registration:**
- Composition ID: `"REM-Dachbeschichtung-V2"`
- Separate entry from existing `"REM-Dachbeschichtung"`

## What to Avoid

- Heavy textures, noise filters, grungy effects
- Bouncy/elastic animations
- Too many particles
- Photorealistic rendering
- Cluttered compositions
- Text too small or too brief
