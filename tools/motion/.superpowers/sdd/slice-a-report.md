# Slice A Report — Seniorenstiftung Foundation (Tasks 1–4)
Date: 2026-07-01

## Status: DONE

## Files Created / Modified

### Task 1 — Client Foundation
- CREATED: `public/seniorenstiftung/logo.svg` (6311 bytes, downloaded from seniorenstiftung.org, verified contains `#0E7EBE`)
- CREATED: `src/clients/seniorenstiftung/brand.json`
- CREATED: `src/clients/seniorenstiftung/components/constants.ts`
- CREATED: `src/clients/seniorenstiftung/components/useExit.ts`

### Task 2 — Logo + HighlightPop
- CREATED: `src/clients/seniorenstiftung/components/Logo.tsx`
- CREATED: `src/clients/seniorenstiftung/components/HighlightPop.tsx`

### Task 3 — ChipRow + CTASlide + index.ts
- CREATED: `src/clients/seniorenstiftung/components/ChipRow.tsx`
- CREATED: `src/clients/seniorenstiftung/components/CTASlide.tsx`
- CREATED: `src/clients/seniorenstiftung/components/index.ts`
  - Note: index.ts references SceneRenderer (Task 4) — produced expected TS2307 errors during Task 3, resolved in Task 4.

### Task 4 — SceneRenderer + Pflegefachkraft + Root.tsx + package.json
- CREATED: `src/clients/seniorenstiftung/components/SceneRenderer.tsx`
- CREATED: `src/clients/seniorenstiftung/projects/pflegefachkraft/scenes.ts`
- CREATED: `src/clients/seniorenstiftung/projects/pflegefachkraft/Composition.tsx`
- MODIFIED: `src/Root.tsx` — added import for PflegefachkraftOverlay after line 52; added `<Folder name="Seniorenstiftung">` with Composition before closing `</Folder>` of Clients block
- MODIFIED: `package.json` — added `"render:st:pflegefachkraft"` script

## TypeScript Check Result

`npx tsc --noEmit` — **ZERO ERRORS** after Task 4 completion.

Intermediate state after Task 3: 2 expected errors (index.ts → SceneRenderer not yet created). All resolved by Task 4.

## Still Renders

All 4 stills rendered successfully with `npx remotion still`:

| Still | Frame | Scene | Visual verdict |
|-------|-------|-------|----------------|
| `pf-075.png` | 75 | HighlightPop "Mehr als **Aufgaben**" | PASS — white frosted pill centered in lower-mid band, INK text with teal emphasis "Aufgaben", background transparent, text not clipped |
| `pf-200.png` | 200 | ChipRow [Vertrauen / Nähe / Team] | PASS — three frosted pill chips with teal dots, centered, wrapping layout, transparent background |
| `pf-1275.png` | 1275 | CTASlide "Werde **Pflegefachkraft**" | PASS — frosted card with "JETZT BEWERBEN" eyebrow, headline with teal emphasis, logo (correct SVG wordmark), claim "Geborgen in guten Händen" in italic teal-dark; card occupies ~34%–80% of height |
| `pf-guides-075.png` | 75 | HighlightPop + guide overlay | PASS — HighlightPop pill sits clearly BELOW the red face zone (bottom edge ~0.45h) and is contained INSIDE the green safe zone border; no overshoot detected |

## Face Zone / Safe Zone Check

Guide still confirmed:
- Red face zone: top=8%, bottom=45% of frame height
- Green safe zone: top=7%, right/left=5% margins, bottom at 57.5%
- HighlightPop bottom anchor: `CONTENT_BOTTOM = 0.42` (42% from frame bottom = ~807px from bottom in 1920px)
- Safe zone bottom limit: 57.5% from top = 42.5% from bottom = ~816px from bottom
- Pill sits ~9px above the safe zone bottom boundary — fully inside.
- No CONTENT_BOTTOM adjustment was needed; 0.42 is safe.

## Deviations from Plan

None. All code blocks implemented verbatim. ReviewOverlay props matched exactly (`showSafeZone`, `showFaceZone`, `showGrid`, `faceZone`, `guideOpacity`, `format` optional) — no adjustments needed.

The reference frame extraction (Task 4 Step 2, frame 120) showed hands/book scene with no face — consistent with the interview-style footage; the default faceZone `{ top: 0.08, bottom: 0.45, left: 0.18, right: 0.82 }` is appropriate.

## Node / npx Path Note

`npx` not on PATH at `/usr/local/bin` or `/opt/homebrew/bin`. Used `/Users/jansantos/.nvm/versions/node/v24.14.0/bin/npx` for all commands. ffmpeg found at `/opt/homebrew/bin/ffmpeg`.
