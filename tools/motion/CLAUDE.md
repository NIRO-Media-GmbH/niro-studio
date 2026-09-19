# NIRO Motion Graphics

## Pre-Delivery Review Checklist

IMPORTANT: Before delivering ANY video composition, Claude MUST perform all of the following checks.

### 1. Face Coverage Prevention
- Enable `review.showGuides: true` and `review.showFaceZone: true` in Remotion Studio props
- Scrub through the ENTIRE video frame-by-frame in the face zone area
- NO opaque overlays, text, shapes, or UI elements may enter the red hatched face zone
- Lower-thirds must stay BELOW the face zone
- If the person's face is not in the default zone, adjust `review.faceZone` values for this project
- Check that spring/bounce animations do not temporarily overshoot into the face zone

### 2. Safe Zone Compliance
- Enable `review.showSafeZone: true`
- ALL text elements must stay within the green safe zone border at all times
- CTA elements must not be in the bottom unsafe region (IG/TikTok UI overlays)
- Check at key frames: first frame, each scene start, mid-scene, scene exit, last frame
- Animated elements must not exit safe zone during entrance/exit transitions

### 3. Pre-Render Verification
- Set `review.showGuides: false` before any final render
- The review overlay must NEVER appear in exported videos

### Review Overlay Controls
- `review.showGuides` — Master toggle for the entire overlay
- `review.showSafeZone` — Green dashed border = safe content area
- `review.showFaceZone` — Red hatched zone = face danger area (do not cover)
- `review.showGrid` — Rule-of-thirds grid within safe zone
- `review.faceZone` — Custom face zone position (override per project)
- `review.guideOpacity` — Transparency of all guide elements

## Motion Quality

Every composition follows `docs/motion-doctrine.md` (easing doctrine,
scene rhythm, video-scale typography, transition recipes, technical
traps). Read it before building new animations.

Craft references (art direction, lower thirds, testimonials, style
system, custom transitions, beat sync, 3D, QA) live in the project skill
`.claude/skills/remotion-craft/`; ready-made components (text reveals,
signature transitions, shader backgrounds) in the skill `remocn` — install
only via `npm run remocn:add -- <name>`, never via the shadcn CLI. Details:
`WORKFLOW-Motion.md` („Handwerk und Bausteine").

## Captions

For designed caption work (hero words, tinted-glass fills, subject-aware
placement) read `docs/cinematic-captions.md` first and write the caption
plan it specifies before implementing. Its verification section extends —
never replaces — the review checklist above.

## Coding Conventions

- All compositions extend `projectPropsSchema` from `src/core/schemas.ts`
- Per-element positioning via `posSchema` with `{x, y}` pixel offsets
- Scene timing via `timingSchema` with `startSec` and `durationSec`
- Integrate `<ReviewOverlay>` in every new composition (conditional on `review?.showGuides`)
- Safe zone constants from `src/core/format-utils.ts`
- Face zone defaults from `getDefaultFaceZone()` in `src/core/format-utils.ts`
- Overlay band (below the face zone, inside the safe zone) from `getOverlayBandPixels()` in `src/core/format-utils.ts` — lower thirds, cards and CTAs in 9:16 talking-head pieces live there (reference: `src/clients/niro-demo/projects/recruiting-overlay-test/`)
