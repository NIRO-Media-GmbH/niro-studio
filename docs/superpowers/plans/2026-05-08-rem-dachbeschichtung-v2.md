# REM Dachbeschichtung V2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 37-second minimalist/Apple-style motion graphics video for REM Malerfachbetrieb's roof coating service, as a new project alongside the existing clay-style v1.

**Architecture:** All-SVG rendering inside a single `<svg viewBox="0 0 3840 2160">`. Frame-driven opacity groups for 30-frame cross-fade scene transitions (no `<Sequence>` wrappers). Persistent `MinimalHouse` component receives interpolated props from the main Composition.

**Tech Stack:** Remotion 4.0, React, TypeScript, Zod, SVG

**Spec:** `docs/superpowers/specs/2026-05-08-rem-dachbeschichtung-v2-design.md`

---

## File Structure

```
src/clients/rem-maler/projects/dachbeschichtung-v2/
├── Composition.tsx          # Main composition, schema, scene orchestration
├── constants.ts             # Colors, timing, geometry, text content
└── components/
    ├── MinimalHouse.tsx     # Persistent isometric house icon
    ├── RainEffect.tsx       # Scene 1: rain, lightning, snow
    ├── WeatheringEffect.tsx # Scene 2: cracks, dust
    ├── MossEffect.tsx       # Scene 3: moss circles, lichen
    ├── CoatingWipe.tsx      # Scene 4: wipe glow edge, specular
    ├── WaterProtection.tsx  # Scene 5: beads, rain, vapor
    ├── FinaleEffect.tsx     # Scene 6: glow, sparkles
    └── TextReveal.tsx       # Reusable staggered word fade-up

Modified:
  src/Root.tsx               # Add composition registration
```

Note: No local `easing.ts` needed — `EASING_PRESETS.appleEase` already exists in `src/utils/easing.ts`.

---

## Testing Approach

This is a visual motion graphics project. There are no unit tests. Verification is via Remotion Studio:
- **Compilation check:** `npm run studio` loads without errors
- **Visual check:** Preview the composition in the browser, scrub timeline
- The plan marks verification steps explicitly

---

### Task 1: Create constants.ts (foundation)

**Files:**
- Create: `src/clients/rem-maler/projects/dachbeschichtung-v2/constants.ts`

- [ ] **Step 1: Create the project directory**

Run: `mkdir -p src/clients/rem-maler/projects/dachbeschichtung-v2/components`

- [ ] **Step 2: Create constants.ts**

```ts
// src/clients/rem-maler/projects/dachbeschichtung-v2/constants.ts
// ============================================================
// REM Dachbeschichtung V2 — Constants
// Minimalist / Apple-style animation
// ============================================================

// --- Colors ---
export const BG = "#0D0D1A";
export const REM_RED = "#D83C31";
export const WHITE = "#FFFFFF";
export const WHITE_60 = "rgba(255,255,255,0.6)";
export const WHITE_30 = "rgba(255,255,255,0.3)";
export const WHITE_05 = "rgba(255,255,255,0.05)";
export const CREAM = "#F5E6D0";
export const GREY_WEATHERED = "#6B6B5A";
export const MOSS_GREEN = "#4A7A42";
export const LICHEN_GREEN = "#6B8A42";
export const WATER_BLUE = "#5AADFF";

// --- Canvas ---
export const W = 3840;
export const H = 2160;
export const FPS = 25;
export const TOTAL_FRAMES = 925;

// --- Scene Timing ---
// 30-frame overlap between adjacent scenes for cross-fades
export const OVERLAP = 30;

export const SCENES = {
  weather:    { start: 0,   end: 125, dur: 125 },
  weathering: { start: 125, end: 250, dur: 125 },
  moss:       { start: 250, end: 425, dur: 175 },
  coating:    { start: 425, end: 600, dur: 175 },
  water:      { start: 600, end: 775, dur: 175 },
  finale:     { start: 775, end: 925, dur: 150 },
} as const;

// Overlapping scene timing (each scene extends ±OVERLAP/2 into neighbors)
export const SCENES_OV = {
  weather:    { start: 0,   end: 140, dur: 140 },
  weathering: { start: 110, end: 265, dur: 155 },
  moss:       { start: 235, end: 440, dur: 205 },
  coating:    { start: 410, end: 615, dur: 205 },
  water:      { start: 585, end: 790, dur: 205 },
  finale:     { start: 760, end: 925, dur: 165 },
} as const;

// --- Isometric House Geometry ---
// 3D dimensions (origin at center-base of house)
const HOUSE_WIDTH = 220;  // half-width along X
const HOUSE_DEPTH = 160;  // half-depth along Y
const WALL_HEIGHT = 260;
const ROOF_PEAK = 170;    // above wall top

// Center of the house in SVG space
export const CX = 1920;
export const CY = 1300;

// Isometric projection: 3D → 2D SVG coordinates
export function iso(x: number, y: number, z: number): [number, number] {
  return [
    CX + (x - y) * 0.866,
    CY + (x + y) * 0.5 - z,
  ];
}

// Pre-computed house points (projected to SVG coords)
export const HP = {
  // Ground corners
  gFL: iso(-HOUSE_WIDTH, -HOUSE_DEPTH, 0),
  gFR: iso(HOUSE_WIDTH, -HOUSE_DEPTH, 0),
  gBR: iso(HOUSE_WIDTH, HOUSE_DEPTH, 0),
  gBL: iso(-HOUSE_WIDTH, HOUSE_DEPTH, 0),
  // Wall top corners
  wFL: iso(-HOUSE_WIDTH, -HOUSE_DEPTH, WALL_HEIGHT),
  wFR: iso(HOUSE_WIDTH, -HOUSE_DEPTH, WALL_HEIGHT),
  wBR: iso(HOUSE_WIDTH, HOUSE_DEPTH, WALL_HEIGHT),
  wBL: iso(-HOUSE_WIDTH, HOUSE_DEPTH, WALL_HEIGHT),
  // Ridge (centered X=0, runs front-to-back along Y)
  rF: iso(0, -HOUSE_DEPTH, WALL_HEIGHT + ROOF_PEAK),
  rB: iso(0, HOUSE_DEPTH, WALL_HEIGHT + ROOF_PEAK),
} as const;

// Roof bounding box (for effects positioning — left slope)
export const ROOF_BOUNDS = {
  left: HP.wBL[0],
  right: HP.wFR[0],
  top: HP.rF[1],
  bottom: Math.max(HP.wFL[1], HP.wFR[1]),
};

// Helper: convert point array to SVG polygon points string
export function pts(...points: (readonly [number, number])[]): string {
  return points.map(([x, y]) => `${Math.round(x)},${Math.round(y)}`).join(" ");
}

// --- Window / Door positions (3D, projected at render) ---
export const FRONT_WINDOW_1 = {
  center: iso(-80, -HOUSE_DEPTH, 170),
  width: 55,
  height: 70,
};
export const FRONT_WINDOW_2 = {
  center: iso(80, -HOUSE_DEPTH, 170),
  width: 55,
  height: 70,
};
export const FRONT_DOOR = {
  center: iso(0, -HOUSE_DEPTH, 70),
  width: 50,
  height: 110,
};
export const SIDE_WINDOW = {
  center: iso(HOUSE_WIDTH, 0, 170),
  width: 55,
  height: 70,
};

// --- Text Content per Scene ---
export const TEXT = {
  scene1: {
    line1: { words: ["Ihr", "Dach."], startFrame: 20, y: 500, fontSize: 120 },
    line2: { words: ["365", "Tage.", "Jedes", "Wetter."], startFrame: 45, y: 620, fontSize: 80, color: WHITE_60 },
    exitFrame: 100,
  },
  scene2: {
    line1: { words: ["Jahre", "vergehen."], startFrame: 140, y: 500, fontSize: 100 },
    line2: { words: ["Risse.", "Verwitterung.", "Substanzverlust."], startFrame: 180, y: 630, fontSize: 80, staggerFrames: 15 },
    exitFrame: 240,
  },
  scene3: {
    line1: { words: ["Moos.", "Algen.", "Flechten."], startFrame: 270, y: 500, fontSize: 100 },
    line2: { words: ["Ohne", "Schutz", "zerfällt", "Ihr", "Dach."], startFrame: 340, y: 630, fontSize: 70, color: "rgba(255,255,255,0.5)" },
    exitFrame: 410,
  },
  scene4: {
    line1: { words: ["Professionelle"], startFrame: 440, y: 480, fontSize: 90 },
    line2: { words: ["Dachbeschichtung."], startFrame: 460, y: 610, fontSize: 120, color: REM_RED, fontWeight: 700, glow: true },
    exitFrame: 540,
  },
  scene5: {
    line1: { words: ["100%", "Wetterschutz."], startFrame: 620, y: 500, fontSize: 100 },
    line2: { words: ["Wasserabweisend.", "Langlebig.", "Schön."], startFrame: 670, y: 630, fontSize: 70 },
    exitFrame: 760,
  },
  scene6: {
    line1: { words: ["REM", "Malerfachbetrieb"], startFrame: 790, y: 480, fontSize: 80, letterSpacing: 2 },
    line2: { words: ["rem-maler.de"], startFrame: 820, y: 590, fontSize: 60, color: REM_RED },
    line3: { words: ["Jetzt", "Angebot", "anfragen", "→"], startFrame: 850, y: 690, fontSize: 50, color: "rgba(255,255,255,0.7)" },
    // No exitFrame — holds until end
  },
} as const;
```

- [ ] **Step 3: Verify file compiles**

Run: `npx tsc --noEmit src/clients/rem-maler/projects/dachbeschichtung-v2/constants.ts 2>&1 | head -20`

If tsc is not configured for isolated files, just proceed — compilation will be verified when the full composition loads in Studio.

---

### Task 2: Create TextReveal component

**Files:**
- Create: `src/clients/rem-maler/projects/dachbeschichtung-v2/components/TextReveal.tsx`

- [ ] **Step 1: Create TextReveal.tsx**

```tsx
// src/clients/rem-maler/projects/dachbeschichtung-v2/components/TextReveal.tsx
import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { EASING_PRESETS } from "../../../../utils/easing";
import { W } from "../constants";

interface TextRevealProps {
  words: readonly string[];
  startFrame: number;
  staggerFrames?: number;
  fontSize: number;
  color?: string;
  y: number;
  exitFrame?: number;
  fontWeight?: number;
  glow?: boolean;
  glowColor?: string;
  letterSpacing?: number;
}

const ENTER_DURATION = 22;
const EXIT_DURATION = 20;
const TRANSLATE_Y = 25;
const appleEase = EASING_PRESETS.appleEase;

export const TextReveal: React.FC<TextRevealProps> = ({
  words,
  startFrame,
  staggerFrames = 12,
  fontSize,
  color = "#FFFFFF",
  y,
  exitFrame,
  fontWeight = 400,
  glow = false,
  glowColor,
  letterSpacing = 0,
}) => {
  const frame = useCurrentFrame();
  const centerX = W / 2; // 1920

  // Build the full text string for measurement reference
  const fullText = words.join(" ");

  // Calculate total text width estimate for word positioning
  // In SVG we use textAnchor="middle" so words are centered as a group
  // We render each word separately for stagger but position them as a line

  // Compute per-word enter/exit animations
  const wordElements = words.map((word, i) => {
    const wordStart = startFrame + i * staggerFrames;

    // Enter animation
    const enterProgress = interpolate(
      frame,
      [wordStart, wordStart + ENTER_DURATION],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
    );
    const enterOpacity = enterProgress;
    const enterY = interpolate(enterProgress, [0, 1], [TRANSLATE_Y, 0]);

    // Exit animation (if exitFrame specified)
    let exitOpacity = 1;
    if (exitFrame != null) {
      exitOpacity = interpolate(
        frame,
        [exitFrame, exitFrame + EXIT_DURATION],
        [1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
      );
    }

    const opacity = enterOpacity * exitOpacity;
    const translateY = enterY;

    return { word, opacity, translateY, key: `${word}-${i}` };
  });

  // If all words are fully transparent, skip rendering
  const allHidden = wordElements.every((w) => w.opacity < 0.01);
  if (allHidden) return null;

  // We render the full text as one <text> but animate each <tspan> word
  // This way SVG handles word spacing/positioning naturally
  return (
    <g>
      {/* Glow layer (behind main text) */}
      {glow && (
        <text
          x={centerX}
          y={y}
          textAnchor="middle"
          fontFamily="Inter, system-ui, -apple-system, sans-serif"
          fontSize={fontSize}
          fontWeight={fontWeight}
          letterSpacing={letterSpacing}
          fill={glowColor || color}
          filter="url(#textGlow)"
        >
          {wordElements.map(({ word, opacity, key }) => (
            <tspan key={`glow-${key}`} opacity={opacity * 0.4}>
              {word}{" "}
            </tspan>
          ))}
        </text>
      )}

      {/* Main text */}
      {wordElements.map(({ word, opacity, translateY, key }, i) => {
        // For staggered individual word positioning, we render each as separate <text>
        // but since SVG doesn't auto-flow words, we use a single <text> with <tspan>
        return null; // placeholder, actual rendering below
      })}

      <text
        x={centerX}
        y={y}
        textAnchor="middle"
        fontFamily="Inter, system-ui, -apple-system, sans-serif"
        fontSize={fontSize}
        fontWeight={fontWeight}
        letterSpacing={letterSpacing}
        fill="transparent"
      >
        {wordElements.map(({ word, opacity, translateY, key }, i) => (
          <tspan
            key={key}
            fill={color}
            opacity={opacity}
            dy={translateY}
            dx={i === 0 ? 0 : undefined}
          >
            {word}{i < wordElements.length - 1 ? " " : ""}
          </tspan>
        ))}
      </text>
    </g>
  );
};
```

**Important note:** The `<tspan>` approach with per-word `dy` has limitations — the `dy` offset accumulates. A better approach renders each word as a separate `<text>` element positioned manually. The implementer should refine this during visual verification. An alternative implementation:

```tsx
// Alternative: render each word separately, manually computing x positions
// This gives full control over per-word translateY
// However, horizontal positioning requires measuring text width.
// For simplicity, join all words into one text element and apply
// uniform opacity (the least animated word's opacity) with a single translateY.
// OR: render the entire line as one element and animate the whole line.
```

**Recommended simplified approach:** Since SVG `<tspan>` dy offsets are cumulative and hard to control per-word, render each scene's text as full-line `<text>` elements (not per-word). Each line fades up as a unit. This is simpler and matches the Apple aesthetic (clean, not frenetic). The stagger then applies between LINES, not words.

The implementer should decide during visual testing which looks better: per-word stagger or per-line fade. Either way, the component interface stays the same.

- [ ] **Step 2: Verify file has no syntax errors**

Run: `npx tsc --noEmit --jsx react-jsx --esModuleInterop --moduleResolution node src/clients/rem-maler/projects/dachbeschichtung-v2/components/TextReveal.tsx 2>&1 | head -10`

---

### Task 3: Create MinimalHouse component

**Files:**
- Create: `src/clients/rem-maler/projects/dachbeschichtung-v2/components/MinimalHouse.tsx`

- [ ] **Step 1: Create MinimalHouse.tsx**

```tsx
// src/clients/rem-maler/projects/dachbeschichtung-v2/components/MinimalHouse.tsx
import React from "react";
import {
  HP, pts, CX, CY,
  WHITE, WHITE_05, CREAM, REM_RED,
  FRONT_WINDOW_1, FRONT_WINDOW_2, FRONT_DOOR, SIDE_WINDOW,
} from "../constants";

interface MinimalHouseProps {
  roofColor: string;
  coatingProgress: number; // 0-1, left-to-right clipPath reveal
  crackOpacity: number;
  mossOpacity: number;
  specularX: number; // 0-1, horizontal position of gloss sweep
  scale: number;
  shake: { x: number; y: number };
}

// Roof slope left polygon bounds for clipPath calculation
const roofLeftX = Math.min(HP.wFL[0], HP.wBL[0], HP.rF[0], HP.rB[0]);
const roofRightX = Math.max(HP.wFL[0], HP.wBL[0], HP.rF[0], HP.rB[0]);
const roofWidth = roofRightX - roofLeftX;

export const MinimalHouse: React.FC<MinimalHouseProps> = ({
  roofColor,
  coatingProgress,
  scale,
  shake,
  specularX,
}) => {
  const tx = shake.x;
  const ty = shake.y;
  const coatingClipWidth = roofWidth * coatingProgress;

  return (
    <g
      transform={`translate(${tx}, ${ty}) scale(${scale})`}
      style={{ transformOrigin: `${CX}px ${CY}px` }}
    >
      {/* --- Defs: filters & clipPaths --- */}
      <defs>
        {/* Coating wipe clipPath */}
        <clipPath id="coatingClip">
          <rect
            x={roofLeftX}
            y={HP.rF[1] - 20}
            width={coatingClipWidth}
            height={HP.wFL[1] - HP.rF[1] + 40}
          />
        </clipPath>

        {/* Specular highlight gradient */}
        <linearGradient id="specularGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="white" stopOpacity="0" />
          <stop offset="0.4" stopColor="white" stopOpacity="0.15" />
          <stop offset="0.5" stopColor="white" stopOpacity="0.25" />
          <stop offset="0.6" stopColor="white" stopOpacity="0.15" />
          <stop offset="1" stopColor="white" stopOpacity="0" />
        </linearGradient>

        {/* Wipe edge glow */}
        <filter id="wipeGlow">
          <feGaussianBlur stdDeviation="4" />
        </filter>
      </defs>

      {/* === WALLS === */}
      {/* Right side wall */}
      <polygon
        points={pts(HP.gFR, HP.gBR, HP.wBR, HP.wFR)}
        fill={WHITE_05}
        stroke={WHITE}
        strokeWidth={2.5}
        strokeLinejoin="round"
      />

      {/* Front wall (rectangle part) */}
      <polygon
        points={pts(HP.gFL, HP.gFR, HP.wFR, HP.wFL)}
        fill={WHITE_05}
        stroke={WHITE}
        strokeWidth={2.5}
        strokeLinejoin="round"
      />

      {/* Front gable triangle */}
      <polygon
        points={pts(HP.wFL, HP.rF, HP.wFR)}
        fill={WHITE_05}
        stroke={WHITE}
        strokeWidth={2.5}
        strokeLinejoin="round"
      />

      {/* === ROOF (base color) === */}
      {/* Left roof slope (faces viewer) */}
      <polygon
        points={pts(HP.wFL, HP.rF, HP.rB, HP.wBL)}
        fill={roofColor}
        stroke={WHITE}
        strokeWidth={2.5}
        strokeLinejoin="round"
        opacity={0.9}
      />

      {/* Right roof slope */}
      <polygon
        points={pts(HP.wFR, HP.rF, HP.rB, HP.wBR)}
        fill={roofColor}
        stroke={WHITE}
        strokeWidth={2.5}
        strokeLinejoin="round"
        opacity={0.7}
      />

      {/* Roof tile suggestion: thin horizontal lines on left slope */}
      {[0.25, 0.5, 0.75].map((t) => {
        // Interpolate along the left slope from eave to ridge
        const leftX = HP.wBL[0] + (HP.rB[0] - HP.wBL[0]) * t;
        const leftY = HP.wBL[1] + (HP.rB[1] - HP.wBL[1]) * t;
        const rightX = HP.wFL[0] + (HP.rF[0] - HP.wFL[0]) * t;
        const rightY = HP.wFL[1] + (HP.rF[1] - HP.wFL[1]) * t;
        return (
          <line
            key={`tile-${t}`}
            x1={leftX}
            y1={leftY}
            x2={rightX}
            y2={rightY}
            stroke={WHITE}
            strokeWidth={1}
            opacity={0.2}
          />
        );
      })}

      {/* === COATING OVERLAY (red, clipped by progress) === */}
      {coatingProgress > 0 && (
        <g clipPath="url(#coatingClip)">
          {/* Red left slope */}
          <polygon
            points={pts(HP.wFL, HP.rF, HP.rB, HP.wBL)}
            fill={REM_RED}
            opacity={0.95}
          />
          {/* Red right slope */}
          <polygon
            points={pts(HP.wFR, HP.rF, HP.rB, HP.wBR)}
            fill={REM_RED}
            opacity={0.8}
          />
        </g>
      )}

      {/* Wipe edge glow line */}
      {coatingProgress > 0.01 && coatingProgress < 0.99 && (
        <line
          x1={roofLeftX + coatingClipWidth}
          y1={HP.rF[1] - 10}
          x2={roofLeftX + coatingClipWidth}
          y2={HP.wFL[1] + 10}
          stroke={WHITE}
          strokeWidth={2}
          filter="url(#wipeGlow)"
          opacity={0.8}
        />
      )}

      {/* Specular sweep (post-coating) */}
      {coatingProgress >= 1 && specularX > 0 && (
        <rect
          x={roofLeftX + roofWidth * specularX - 60}
          y={HP.rF[1]}
          width={120}
          height={HP.wFL[1] - HP.rF[1]}
          fill="url(#specularGrad)"
          opacity={0.6}
        />
      )}

      {/* === WINDOWS & DOOR === */}
      {/* Front window 1 */}
      <rect
        x={FRONT_WINDOW_1.center[0] - FRONT_WINDOW_1.width / 2}
        y={FRONT_WINDOW_1.center[1] - FRONT_WINDOW_1.height / 2}
        width={FRONT_WINDOW_1.width}
        height={FRONT_WINDOW_1.height}
        fill="none"
        stroke={WHITE}
        strokeWidth={1.5}
        opacity={0.5}
      />

      {/* Front window 2 */}
      <rect
        x={FRONT_WINDOW_2.center[0] - FRONT_WINDOW_2.width / 2}
        y={FRONT_WINDOW_2.center[1] - FRONT_WINDOW_2.height / 2}
        width={FRONT_WINDOW_2.width}
        height={FRONT_WINDOW_2.height}
        fill="none"
        stroke={WHITE}
        strokeWidth={1.5}
        opacity={0.5}
      />

      {/* Front door */}
      <rect
        x={FRONT_DOOR.center[0] - FRONT_DOOR.width / 2}
        y={FRONT_DOOR.center[1] - FRONT_DOOR.height / 2}
        width={FRONT_DOOR.width}
        height={FRONT_DOOR.height}
        fill="none"
        stroke={WHITE}
        strokeWidth={1.5}
        opacity={0.4}
      />

      {/* Side window */}
      <rect
        x={SIDE_WINDOW.center[0] - SIDE_WINDOW.width / 2}
        y={SIDE_WINDOW.center[1] - SIDE_WINDOW.height / 2}
        width={SIDE_WINDOW.width}
        height={SIDE_WINDOW.height}
        fill="none"
        stroke={WHITE}
        strokeWidth={1.5}
        opacity={0.4}
      />

      {/* Ridge line (emphasized) */}
      <line
        x1={HP.rF[0]}
        y1={HP.rF[1]}
        x2={HP.rB[0]}
        y2={HP.rB[1]}
        stroke={WHITE}
        strokeWidth={3}
        opacity={0.8}
      />
    </g>
  );
};
```

- [ ] **Step 2: Commit foundation + house**

```bash
git add src/clients/rem-maler/projects/dachbeschichtung-v2/constants.ts \
        src/clients/rem-maler/projects/dachbeschichtung-v2/components/MinimalHouse.tsx \
        src/clients/rem-maler/projects/dachbeschichtung-v2/components/TextReveal.tsx
git commit -m "feat(rem-v2): add constants, TextReveal, and MinimalHouse components"
```

---

### Task 4: Create RainEffect (Scene 1)

**Files:**
- Create: `src/clients/rem-maler/projects/dachbeschichtung-v2/components/RainEffect.tsx`

**Parallelizable:** Tasks 4-9 can be implemented simultaneously.

- [ ] **Step 1: Create RainEffect.tsx**

```tsx
// src/clients/rem-maler/projects/dachbeschichtung-v2/components/RainEffect.tsx
import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../utils/easing";
import { W, H, WHITE, WHITE_30, SCENES } from "../constants";

interface RainEffectProps {
  sceneProgress: number; // 0-1
}

const appleEase = EASING_PRESETS.appleEase;
const RAIN_COUNT = 18;
const SNOW_COUNT = 6;
const LIGHTNING_FRAME = 100; // global frame

export const RainEffect: React.FC<RainEffectProps> = ({ sceneProgress }) => {
  const frame = useCurrentFrame();

  // Generate rain drop positions (deterministic)
  const rainDrops = useMemo(() => {
    return Array.from({ length: RAIN_COUNT }, (_, i) => ({
      x: random(`rain-x-${i}`) * W,
      speed: 0.7 + random(`rain-speed-${i}`) * 0.6,
      delay: random(`rain-delay-${i}`) * 40,
      length: 40 + random(`rain-len-${i}`) * 60,
      opacity: 0.15 + random(`rain-op-${i}`) * 0.2,
    }));
  }, []);

  // Generate snowflake positions
  const snowflakes = useMemo(() => {
    return Array.from({ length: SNOW_COUNT }, (_, i) => ({
      x: W * 0.2 + random(`snow-x-${i}`) * W * 0.6,
      startY: -20 - random(`snow-sy-${i}`) * 100,
      drift: (random(`snow-drift-${i}`) - 0.5) * 80,
      size: 3 + random(`snow-size-${i}`) * 4,
    }));
  }, []);

  // Lightning flash (3 frames around LIGHTNING_FRAME)
  const lightningOpacity = interpolate(
    frame,
    [LIGHTNING_FRAME - 1, LIGHTNING_FRAME, LIGHTNING_FRAME + 2, LIGHTNING_FRAME + 3],
    [0, 0.06, 0.03, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Snow appears in last 20 frames of the scene (frames ~105-125)
  const snowProgress = interpolate(
    frame,
    [105, 110, 120, 125],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
  );

  return (
    <g>
      {/* Rain drops — thin vertical lines */}
      {rainDrops.map((drop, i) => {
        const localFrame = frame - drop.delay;
        if (localFrame < 0) return null;

        // Rain falls from top to bottom, cycling
        const fallProgress = ((localFrame * drop.speed * 0.08) % 1.2) - 0.1;
        const y1 = fallProgress * (H + 200) - 100;
        const y2 = y1 + drop.length;

        // Fade in rain at scene start
        const fadeIn = interpolate(frame, [0, 20], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <line
            key={`rain-${i}`}
            x1={drop.x}
            y1={y1}
            x2={drop.x + 2}
            y2={y2}
            stroke={WHITE}
            strokeWidth={1.5}
            opacity={drop.opacity * fadeIn}
          />
        );
      })}

      {/* Lightning flash */}
      {lightningOpacity > 0.001 && (
        <rect
          x={0}
          y={0}
          width={W}
          height={H}
          fill={WHITE}
          opacity={lightningOpacity}
        />
      )}

      {/* Snowflakes */}
      {snowProgress > 0.01 &&
        snowflakes.map((flake, i) => {
          const t = interpolate(frame, [105, 125], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const y = flake.startY + t * 300;
          const x = flake.x + flake.drift * t;

          return (
            <circle
              key={`snow-${i}`}
              cx={x}
              cy={y}
              r={flake.size}
              fill={WHITE}
              opacity={snowProgress * 0.4}
            />
          );
        })}
    </g>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add src/clients/rem-maler/projects/dachbeschichtung-v2/components/RainEffect.tsx
git commit -m "feat(rem-v2): add RainEffect component (Scene 1)"
```

---

### Task 5: Create WeatheringEffect (Scene 2)

**Files:**
- Create: `src/clients/rem-maler/projects/dachbeschichtung-v2/components/WeatheringEffect.tsx`

- [ ] **Step 1: Create WeatheringEffect.tsx**

```tsx
// src/clients/rem-maler/projects/dachbeschichtung-v2/components/WeatheringEffect.tsx
import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../utils/easing";
import { WHITE, ROOF_BOUNDS, SCENES } from "../constants";

interface WeatheringEffectProps {
  sceneProgress: number;
}

const appleEase = EASING_PRESETS.appleEase;
const CRACK_COUNT = 5;
const DUST_COUNT = 9;

export const WeatheringEffect: React.FC<WeatheringEffectProps> = ({ sceneProgress }) => {
  const frame = useCurrentFrame();
  const sceneStart = SCENES.weathering.start;

  // Generate crack paths on the roof surface
  const cracks = useMemo(() => {
    const rb = ROOF_BOUNDS;
    return Array.from({ length: CRACK_COUNT }, (_, i) => {
      const startX = rb.left + random(`crack-sx-${i}`) * (rb.right - rb.left) * 0.8 + (rb.right - rb.left) * 0.1;
      const startY = rb.top + random(`crack-sy-${i}`) * (rb.bottom - rb.top) * 0.8 + (rb.bottom - rb.top) * 0.1;
      // Random jagged path
      const segments = 3 + Math.floor(random(`crack-seg-${i}`) * 3);
      let path = `M${startX},${startY}`;
      let cx = startX;
      let cy = startY;
      for (let s = 0; s < segments; s++) {
        const dx = (random(`crack-dx-${i}-${s}`) - 0.5) * 80;
        const dy = (random(`crack-dy-${i}-${s}`) - 0.3) * 50;
        cx += dx;
        cy += dy;
        path += ` L${cx},${cy}`;
      }
      const totalLength = segments * 60; // approximate
      return {
        path,
        totalLength,
        delay: i * 15, // stagger in frames from scene start
      };
    });
  }, []);

  // Dust particles drifting upward
  const dustParticles = useMemo(() => {
    const rb = ROOF_BOUNDS;
    return Array.from({ length: DUST_COUNT }, (_, i) => ({
      x: rb.left + random(`dust-x-${i}`) * (rb.right - rb.left),
      startY: rb.top + random(`dust-y-${i}`) * (rb.bottom - rb.top),
      drift: (random(`dust-drift-${i}`) - 0.5) * 40,
      size: 2 + random(`dust-size-${i}`) * 3,
      delay: random(`dust-delay-${i}`) * 60,
    }));
  }, []);

  return (
    <g>
      {/* Crack lines drawing in */}
      {cracks.map((crack, i) => {
        const crackStart = sceneStart + crack.delay;
        const drawProgress = interpolate(
          frame,
          [crackStart, crackStart + 40],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
        );

        return (
          <path
            key={`crack-${i}`}
            d={crack.path}
            fill="none"
            stroke={WHITE}
            strokeWidth={1.5}
            strokeLinecap="round"
            strokeDasharray={crack.totalLength}
            strokeDashoffset={crack.totalLength * (1 - drawProgress)}
            opacity={0.6 * drawProgress}
          />
        );
      })}

      {/* Dust particles drifting up */}
      {dustParticles.map((dust, i) => {
        const dustStart = sceneStart + 30 + dust.delay;
        const t = interpolate(
          frame,
          [dustStart, dustStart + 80],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );
        if (t <= 0) return null;

        const y = dust.startY - t * 120;
        const x = dust.x + dust.drift * t;
        const opacity = interpolate(t, [0, 0.2, 0.8, 1], [0, 0.15, 0.15, 0]);

        return (
          <circle
            key={`dust-${i}`}
            cx={x}
            cy={y}
            r={dust.size}
            fill={WHITE}
            opacity={opacity}
          />
        );
      })}
    </g>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add src/clients/rem-maler/projects/dachbeschichtung-v2/components/WeatheringEffect.tsx
git commit -m "feat(rem-v2): add WeatheringEffect component (Scene 2)"
```

---

### Task 6: Create MossEffect (Scene 3)

**Files:**
- Create: `src/clients/rem-maler/projects/dachbeschichtung-v2/components/MossEffect.tsx`

- [ ] **Step 1: Create MossEffect.tsx**

```tsx
// src/clients/rem-maler/projects/dachbeschichtung-v2/components/MossEffect.tsx
import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../utils/easing";
import { MOSS_GREEN, LICHEN_GREEN, ROOF_BOUNDS, SCENES } from "../constants";

interface MossEffectProps {
  sceneProgress: number;
}

const appleEase = EASING_PRESETS.appleEase;
const MOSS_COUNT = 9;
const LICHEN_COUNT = 4;

export const MossEffect: React.FC<MossEffectProps> = ({ sceneProgress }) => {
  const frame = useCurrentFrame();
  const sceneStart = SCENES.moss.start;

  // Moss blobs on the roof
  const mossSpots = useMemo(() => {
    const rb = ROOF_BOUNDS;
    return Array.from({ length: MOSS_COUNT }, (_, i) => ({
      cx: rb.left + random(`moss-x-${i}`) * (rb.right - rb.left) * 0.8 + (rb.right - rb.left) * 0.1,
      cy: rb.top + random(`moss-y-${i}`) * (rb.bottom - rb.top) * 0.8 + (rb.bottom - rb.top) * 0.1,
      targetRadius: 12 + random(`moss-r-${i}`) * 18,
      delay: i * 10 + random(`moss-delay-${i}`) * 20,
    }));
  }, []);

  // Lichen patches (larger, slower)
  const lichenPatches = useMemo(() => {
    const rb = ROOF_BOUNDS;
    return Array.from({ length: LICHEN_COUNT }, (_, i) => ({
      cx: rb.left + random(`lichen-x-${i}`) * (rb.right - rb.left) * 0.7 + (rb.right - rb.left) * 0.15,
      cy: rb.top + random(`lichen-y-${i}`) * (rb.bottom - rb.top) * 0.7 + (rb.bottom - rb.top) * 0.15,
      targetRadius: 20 + random(`lichen-r-${i}`) * 15,
      delay: 30 + i * 18,
    }));
  }, []);

  return (
    <g>
      {/* Moss spots */}
      {mossSpots.map((spot, i) => {
        const growStart = sceneStart + spot.delay;
        const growProgress = interpolate(
          frame,
          [growStart, growStart + 50],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
        );
        if (growProgress <= 0) return null;

        const r = spot.targetRadius * growProgress;

        return (
          <circle
            key={`moss-${i}`}
            cx={spot.cx}
            cy={spot.cy}
            r={r}
            fill={MOSS_GREEN}
            opacity={0.4 * growProgress}
          />
        );
      })}

      {/* Lichen patches */}
      {lichenPatches.map((patch, i) => {
        const growStart = sceneStart + patch.delay;
        const growProgress = interpolate(
          frame,
          [growStart, growStart + 70],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
        );
        if (growProgress <= 0) return null;

        const r = patch.targetRadius * growProgress;

        return (
          <circle
            key={`lichen-${i}`}
            cx={patch.cx}
            cy={patch.cy}
            r={r}
            fill={LICHEN_GREEN}
            opacity={0.3 * growProgress}
          />
        );
      })}
    </g>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add src/clients/rem-maler/projects/dachbeschichtung-v2/components/MossEffect.tsx
git commit -m "feat(rem-v2): add MossEffect component (Scene 3)"
```

---

### Task 7: Create CoatingWipe (Scene 4 — Hero)

**Files:**
- Create: `src/clients/rem-maler/projects/dachbeschichtung-v2/components/CoatingWipe.tsx`

Note: The actual coating wipe (red overlay with clipPath) is handled by `MinimalHouse` via `coatingProgress`. This component handles the SUPPLEMENTARY effects: glow particles along the wipe edge and post-wipe shimmer.

- [ ] **Step 1: Create CoatingWipe.tsx**

```tsx
// src/clients/rem-maler/projects/dachbeschichtung-v2/components/CoatingWipe.tsx
import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../utils/easing";
import { WHITE, REM_RED, ROOF_BOUNDS, SCENES } from "../constants";

interface CoatingWipeProps {
  coatingProgress: number; // 0-1, same as passed to MinimalHouse
}

const appleEase = EASING_PRESETS.appleEase;
const GLOW_PARTICLE_COUNT = 6;

export const CoatingWipe: React.FC<CoatingWipeProps> = ({ coatingProgress }) => {
  const frame = useCurrentFrame();
  const rb = ROOF_BOUNDS;
  const wipeX = rb.left + (rb.right - rb.left) * coatingProgress;

  // Small glow particles along the wipe edge
  const glowParticles = useMemo(() => {
    return Array.from({ length: GLOW_PARTICLE_COUNT }, (_, i) => ({
      yOffset: (random(`glow-y-${i}`) - 0.5) * (rb.bottom - rb.top) * 0.8,
      size: 4 + random(`glow-size-${i}`) * 6,
      drift: (random(`glow-drift-${i}`) - 0.5) * 30,
      pulseSpeed: 0.5 + random(`glow-pulse-${i}`) * 1.5,
    }));
  }, []);

  // Only show effects while wipe is active
  if (coatingProgress <= 0.01 || coatingProgress >= 0.99) return null;

  const centerY = (rb.top + rb.bottom) / 2;

  return (
    <g>
      {/* Glow particles at wipe edge */}
      {glowParticles.map((p, i) => {
        const pulsePhase = Math.sin(frame * 0.15 * p.pulseSpeed) * 0.5 + 0.5;
        const y = centerY + p.yOffset;
        const x = wipeX + p.drift;

        return (
          <circle
            key={`glow-${i}`}
            cx={x}
            cy={y}
            r={p.size * (0.7 + pulsePhase * 0.3)}
            fill={WHITE}
            opacity={0.3 * pulsePhase}
          />
        );
      })}

      {/* Red accent glow at wipe line */}
      <line
        x1={wipeX}
        y1={rb.top}
        x2={wipeX}
        y2={rb.bottom}
        stroke={REM_RED}
        strokeWidth={3}
        opacity={0.4}
        filter="url(#wipeGlow)"
      />
    </g>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add src/clients/rem-maler/projects/dachbeschichtung-v2/components/CoatingWipe.tsx
git commit -m "feat(rem-v2): add CoatingWipe component (Scene 4)"
```

---

### Task 8: Create WaterProtection (Scene 5)

**Files:**
- Create: `src/clients/rem-maler/projects/dachbeschichtung-v2/components/WaterProtection.tsx`

- [ ] **Step 1: Create WaterProtection.tsx**

```tsx
// src/clients/rem-maler/projects/dachbeschichtung-v2/components/WaterProtection.tsx
import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../utils/easing";
import { W, H, WHITE, WATER_BLUE, ROOF_BOUNDS, SCENES } from "../constants";

interface WaterProtectionProps {
  sceneProgress: number;
}

const appleEase = EASING_PRESETS.appleEase;
const RAIN_COUNT = 14;
const BEAD_COUNT = 7;
const VAPOR_COUNT = 4;

export const WaterProtection: React.FC<WaterProtectionProps> = ({ sceneProgress }) => {
  const frame = useCurrentFrame();
  const sceneStart = SCENES.water.start;
  const rb = ROOF_BOUNDS;

  // Rain drops (same thin style as Scene 1)
  const rainDrops = useMemo(() => {
    return Array.from({ length: RAIN_COUNT }, (_, i) => ({
      x: random(`wr-x-${i}`) * W,
      speed: 0.6 + random(`wr-speed-${i}`) * 0.5,
      delay: random(`wr-delay-${i}`) * 30,
      length: 35 + random(`wr-len-${i}`) * 50,
      opacity: 0.12 + random(`wr-op-${i}`) * 0.18,
    }));
  }, []);

  // Water beads on roof (grow, then slide down)
  const beads = useMemo(() => {
    return Array.from({ length: BEAD_COUNT }, (_, i) => ({
      startX: rb.left + random(`bead-x-${i}`) * (rb.right - rb.left) * 0.8 + (rb.right - rb.left) * 0.1,
      startY: rb.top + random(`bead-y-${i}`) * (rb.bottom - rb.top) * 0.5 + (rb.bottom - rb.top) * 0.1,
      maxR: 6 + random(`bead-r-${i}`) * 8,
      delay: 15 + i * 12,
      slideSpeed: 0.8 + random(`bead-slide-${i}`) * 0.4,
    }));
  }, []);

  // Vapor wisps rising from roof
  const vaporWisps = useMemo(() => {
    return Array.from({ length: VAPOR_COUNT }, (_, i) => ({
      x: rb.left + random(`vap-x-${i}`) * (rb.right - rb.left) * 0.6 + (rb.right - rb.left) * 0.2,
      startY: rb.top + random(`vap-sy-${i}`) * 20,
      drift: (random(`vap-drift-${i}`) - 0.5) * 60,
      delay: 40 + i * 20,
    }));
  }, []);

  return (
    <g>
      {/* Defs for vapor blur */}
      <defs>
        <filter id="vaporBlur">
          <feGaussianBlur stdDeviation="6" />
        </filter>
      </defs>

      {/* Rain drops */}
      {rainDrops.map((drop, i) => {
        const localFrame = frame - sceneStart - drop.delay;
        if (localFrame < 0) return null;

        const fallProgress = ((localFrame * drop.speed * 0.08) % 1.2) - 0.1;
        const y1 = fallProgress * (H + 200) - 100;
        const y2 = y1 + drop.length;

        return (
          <line
            key={`wr-${i}`}
            x1={drop.x}
            y1={y1}
            x2={drop.x + 2}
            y2={y2}
            stroke={WHITE}
            strokeWidth={1.5}
            opacity={drop.opacity}
          />
        );
      })}

      {/* Water beads on roof surface */}
      {beads.map((bead, i) => {
        const beadStart = sceneStart + bead.delay;
        // Phase 1: grow (30 frames)
        const growProgress = interpolate(
          frame,
          [beadStart, beadStart + 30],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
        );
        // Phase 2: slide down (40 frames after grow)
        const slideProgress = interpolate(
          frame,
          [beadStart + 30, beadStart + 70],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.accelerate }
        );

        if (growProgress <= 0) return null;

        const r = bead.maxR * growProgress * (1 - slideProgress * 0.3);
        const x = bead.startX;
        const y = bead.startY + slideProgress * 100;
        const opacity = interpolate(slideProgress, [0.7, 1], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <g key={`bead-${i}`}>
            <circle cx={x} cy={y} r={r} fill={WATER_BLUE} opacity={opacity * 0.5} />
            {/* Highlight dot */}
            <circle cx={x - r * 0.3} cy={y - r * 0.3} r={r * 0.3} fill={WHITE} opacity={opacity * 0.6} />
          </g>
        );
      })}

      {/* Vapor wisps */}
      {vaporWisps.map((wisp, i) => {
        const wispStart = sceneStart + wisp.delay;
        const t = interpolate(
          frame,
          [wispStart, wispStart + 80],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );
        if (t <= 0) return null;

        const x = wisp.x + wisp.drift * t;
        const y = wisp.startY - t * 150;
        const opacity = interpolate(t, [0, 0.2, 0.7, 1], [0, 0.12, 0.12, 0]);

        return (
          <ellipse
            key={`vapor-${i}`}
            cx={x}
            cy={y}
            rx={25}
            ry={12}
            fill={WHITE}
            opacity={opacity}
            filter="url(#vaporBlur)"
          />
        );
      })}
    </g>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add src/clients/rem-maler/projects/dachbeschichtung-v2/components/WaterProtection.tsx
git commit -m "feat(rem-v2): add WaterProtection component (Scene 5)"
```

---

### Task 9: Create FinaleEffect (Scene 6)

**Files:**
- Create: `src/clients/rem-maler/projects/dachbeschichtung-v2/components/FinaleEffect.tsx`

- [ ] **Step 1: Create FinaleEffect.tsx**

```tsx
// src/clients/rem-maler/projects/dachbeschichtung-v2/components/FinaleEffect.tsx
import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../utils/easing";
import { W, H, CX, CY, REM_RED, WHITE, SCENES } from "../constants";

interface FinaleEffectProps {
  sceneProgress: number;
}

const appleEase = EASING_PRESETS.appleEase;
const SPARKLE_COUNT = 3;

export const FinaleEffect: React.FC<FinaleEffectProps> = ({ sceneProgress }) => {
  const frame = useCurrentFrame();
  const sceneStart = SCENES.finale.start;

  // Sparkle star positions (near the roof area)
  const sparkles = useMemo(() => {
    return Array.from({ length: SPARKLE_COUNT }, (_, i) => ({
      cx: CX + (random(`spark-x-${i}`) - 0.5) * 500,
      cy: CY - 200 + (random(`spark-y-${i}`) - 0.5) * 200,
      size: 10 + random(`spark-size-${i}`) * 12,
      delay: 20 + i * 15,
      pulseSpeed: 0.08 + random(`spark-pulse-${i}`) * 0.06,
    }));
  }, []);

  // Ambient glow fade-in
  const glowOpacity = interpolate(
    frame,
    [sceneStart, sceneStart + 60],
    [0, 0.08],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
  );

  return (
    <g>
      <defs>
        {/* Ambient radial glow */}
        <radialGradient id="finaleGlow" cx="50%" cy="50%" r="40%">
          <stop offset="0" stopColor={REM_RED} stopOpacity="1" />
          <stop offset="1" stopColor={REM_RED} stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Ambient glow behind the house */}
      <ellipse
        cx={CX}
        cy={CY - 100}
        rx={500}
        ry={350}
        fill="url(#finaleGlow)"
        opacity={glowOpacity}
      />

      {/* Sparkle stars */}
      {sparkles.map((spark, i) => {
        const sparkStart = sceneStart + spark.delay;
        const scaleIn = interpolate(
          frame,
          [sparkStart, sparkStart + 25],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
        );
        if (scaleIn <= 0) return null;

        // Pulsing size
        const pulse = Math.sin(frame * spark.pulseSpeed) * 0.2 + 0.8;
        const size = spark.size * scaleIn * pulse;

        // Four-pointed star shape
        const d = `
          M${spark.cx},${spark.cy - size}
          L${spark.cx + size * 0.3},${spark.cy}
          L${spark.cx},${spark.cy + size}
          L${spark.cx - size * 0.3},${spark.cy}
          Z
          M${spark.cx - size},${spark.cy}
          L${spark.cx},${spark.cy + size * 0.3}
          L${spark.cx + size},${spark.cy}
          L${spark.cx},${spark.cy - size * 0.3}
          Z
        `;

        return (
          <path
            key={`sparkle-${i}`}
            d={d}
            fill={WHITE}
            opacity={0.6 * scaleIn}
          />
        );
      })}
    </g>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add src/clients/rem-maler/projects/dachbeschichtung-v2/components/FinaleEffect.tsx
git commit -m "feat(rem-v2): add FinaleEffect component (Scene 6)"
```

---

### Task 10: Create Composition.tsx (main orchestrator)

**Files:**
- Create: `src/clients/rem-maler/projects/dachbeschichtung-v2/Composition.tsx`

- [ ] **Step 1: Create Composition.tsx**

```tsx
// src/clients/rem-maler/projects/dachbeschichtung-v2/Composition.tsx
// ============================================================
// REM Dachbeschichtung V2 — Apple-Minimal Style
// 37s (925 frames) at 25fps, 4K Landscape (3840×2160)
// All-SVG rendering with frame-driven cross-fade scenes
// ============================================================

import React from "react";
import { z } from "zod";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  interpolateColors,
} from "remotion";
import { noise2D } from "@remotion/noise";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { EASING_PRESETS } from "../../../../utils/easing";
import {
  W, H, BG, CREAM, GREY_WEATHERED, REM_RED,
  SCENES, SCENES_OV, OVERLAP, TEXT, CX, CY,
} from "./constants";
import { MinimalHouse } from "./components/MinimalHouse";
import { RainEffect } from "./components/RainEffect";
import { WeatheringEffect } from "./components/WeatheringEffect";
import { MossEffect } from "./components/MossEffect";
import { CoatingWipe } from "./components/CoatingWipe";
import { WaterProtection } from "./components/WaterProtection";
import { FinaleEffect } from "./components/FinaleEffect";
import { TextReveal } from "./components/TextReveal";

// --- Schema ---
export const remDachV2Schema = projectPropsSchema.extend({});
export type RemDachV2Props = z.infer<typeof remDachV2Schema>;

export const remDachV2Defaults: RemDachV2Props = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 37,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
};

const appleEase = EASING_PRESETS.appleEase;

// --- Scene fade helper ---
function sceneFade(
  frame: number,
  start: number,
  end: number,
  overlap: number,
  isFirst: boolean,
  isLast: boolean
): number {
  const fadeIn = isFirst
    ? 1
    : interpolate(frame, [start, start + overlap], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: appleEase,
      });
  const fadeOut = isLast
    ? 1
    : interpolate(frame, [end - overlap, end], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: appleEase,
      });
  return Math.min(fadeIn, fadeOut);
}

// --- Main Composition ---
export const RemDachbeschichtungV2: React.FC<RemDachV2Props> = (props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // === ROOF STATE MACHINE ===

  // 1. Roof color: Cream → Grey (weathering) → Red (coating via clipPath)
  const roofColor = interpolateColors(
    frame,
    [0, SCENES.weathering.start, SCENES.weathering.start + 60, SCENES.weathering.end],
    [CREAM, CREAM, GREY_WEATHERED, GREY_WEATHERED]
  );

  // 2. Coating wipe progress (Scene 4: frames 425-600)
  const coatingProgress = interpolate(
    frame,
    [SCENES.coating.start + 15, SCENES.coating.end - 40],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.emphasized }
  );

  // 3. Crack opacity (visible during Scene 2-3, fades during coating)
  const crackOpacity = interpolate(
    frame,
    [SCENES.weathering.start + 20, SCENES.weathering.end, SCENES.coating.start, SCENES.coating.end - 30],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // 4. Moss opacity (visible during Scene 3, fades during coating)
  const mossOpacity = interpolate(
    frame,
    [SCENES.moss.start + 15, SCENES.moss.end, SCENES.coating.start, SCENES.coating.end - 30],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // 5. Specular sweep (Scene 5, after coating is complete)
  const specularX = interpolate(
    frame,
    [SCENES.water.start + 20, SCENES.water.end - 30],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.smooth }
  );

  // 6. House scale (finale: 1.0 → 1.03)
  const houseScale = interpolate(
    frame,
    [SCENES.finale.start, SCENES.finale.end],
    [1, 1.03],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
  );

  // 7. Scale pulse during coating (1.0 → 1.02 → 1.0)
  const coatingPulse = frame >= SCENES.coating.start + 80 && frame <= SCENES.coating.start + 110
    ? interpolate(
        frame,
        [SCENES.coating.start + 80, SCENES.coating.start + 95, SCENES.coating.start + 110],
        [1, 1.02, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase }
      )
    : 1;

  const scale = houseScale * coatingPulse;

  // 8. Camera shake (mild, during weathering)
  const shakeActive =
    frame >= SCENES.weathering.start + 50 && frame <= SCENES.weathering.start + 65;
  const shakeIntensity = shakeActive ? 3 : 0;
  const shake = {
    x: noise2D("shakeX", frame * 0.5, 0) * shakeIntensity,
    y: noise2D("shakeY", 0, frame * 0.5) * shakeIntensity,
  };

  // === SCENE FADE OPACITIES ===
  const SO = SCENES_OV;
  const s1Fade = sceneFade(frame, SO.weather.start, SO.weather.end, OVERLAP, true, false);
  const s2Fade = sceneFade(frame, SO.weathering.start, SO.weathering.end, OVERLAP, false, false);
  const s3Fade = sceneFade(frame, SO.moss.start, SO.moss.end, OVERLAP, false, false);
  const s4Fade = sceneFade(frame, SO.coating.start, SO.coating.end, OVERLAP, false, false);
  const s5Fade = sceneFade(frame, SO.water.start, SO.water.end, OVERLAP, false, false);
  const s6Fade = sceneFade(frame, SO.finale.start, SO.finale.end, OVERLAP, false, true);

  // Scene progress (0→1 within each scene)
  const s1Prog = interpolate(frame, [SCENES.weather.start, SCENES.weather.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s2Prog = interpolate(frame, [SCENES.weathering.start, SCENES.weathering.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s3Prog = interpolate(frame, [SCENES.moss.start, SCENES.moss.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s5Prog = interpolate(frame, [SCENES.water.start, SCENES.water.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s6Prog = interpolate(frame, [SCENES.finale.start, SCENES.finale.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // === RENDER ===
  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width={W}
        height={H}
        style={{ width: "100%", height: "100%" }}
      >
        {/* Global SVG defs */}
        <defs>
          <filter id="textGlow">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="wipeGlow">
            <feGaussianBlur stdDeviation="4" />
          </filter>
        </defs>

        {/* === PERSISTENT HOUSE === */}
        <MinimalHouse
          roofColor={roofColor}
          coatingProgress={coatingProgress}
          crackOpacity={crackOpacity}
          mossOpacity={mossOpacity}
          specularX={specularX}
          scale={scale}
          shake={shake}
        />

        {/* === SCENE EFFECT LAYERS === */}

        {/* Scene 1: Weather */}
        {s1Fade > 0.01 && (
          <g opacity={s1Fade}>
            <RainEffect sceneProgress={s1Prog} />
          </g>
        )}

        {/* Scene 2: Weathering */}
        {s2Fade > 0.01 && (
          <g opacity={s2Fade}>
            <WeatheringEffect sceneProgress={s2Prog} />
          </g>
        )}

        {/* Scene 3: Moss */}
        {s3Fade > 0.01 && (
          <g opacity={s3Fade}>
            <MossEffect sceneProgress={s3Prog} />
          </g>
        )}

        {/* Scene 4: Coating (hero) */}
        {s4Fade > 0.01 && (
          <g opacity={s4Fade}>
            <CoatingWipe coatingProgress={coatingProgress} />
          </g>
        )}

        {/* Scene 5: Water Protection */}
        {s5Fade > 0.01 && (
          <g opacity={s5Fade}>
            <WaterProtection sceneProgress={s5Prog} />
          </g>
        )}

        {/* Scene 6: Finale */}
        {s6Fade > 0.01 && (
          <g opacity={s6Fade}>
            <FinaleEffect sceneProgress={s6Prog} />
          </g>
        )}

        {/* === TEXT LAYERS === */}

        {/* Scene 1 text */}
        {s1Fade > 0.01 && (
          <g opacity={s1Fade}>
            <TextReveal {...TEXT.scene1.line1} exitFrame={TEXT.scene1.exitFrame} />
            <TextReveal {...TEXT.scene1.line2} exitFrame={TEXT.scene1.exitFrame} />
          </g>
        )}

        {/* Scene 2 text */}
        {s2Fade > 0.01 && (
          <g opacity={s2Fade}>
            <TextReveal {...TEXT.scene2.line1} exitFrame={TEXT.scene2.exitFrame} />
            <TextReveal {...TEXT.scene2.line2} exitFrame={TEXT.scene2.exitFrame} />
          </g>
        )}

        {/* Scene 3 text */}
        {s3Fade > 0.01 && (
          <g opacity={s3Fade}>
            <TextReveal {...TEXT.scene3.line1} exitFrame={TEXT.scene3.exitFrame} />
            <TextReveal {...TEXT.scene3.line2} exitFrame={TEXT.scene3.exitFrame} />
          </g>
        )}

        {/* Scene 4 text (hero) */}
        {s4Fade > 0.01 && (
          <g opacity={s4Fade}>
            <TextReveal {...TEXT.scene4.line1} exitFrame={TEXT.scene4.exitFrame} />
            <TextReveal {...TEXT.scene4.line2} exitFrame={TEXT.scene4.exitFrame} />
          </g>
        )}

        {/* Scene 5 text */}
        {s5Fade > 0.01 && (
          <g opacity={s5Fade}>
            <TextReveal {...TEXT.scene5.line1} exitFrame={TEXT.scene5.exitFrame} />
            <TextReveal {...TEXT.scene5.line2} exitFrame={TEXT.scene5.exitFrame} />
          </g>
        )}

        {/* Scene 6 text (holds to end, no exitFrame) */}
        {s6Fade > 0.01 && (
          <g opacity={s6Fade}>
            <TextReveal {...TEXT.scene6.line1} />
            <TextReveal {...TEXT.scene6.line2} />
            <TextReveal {...TEXT.scene6.line3} />
          </g>
        )}
      </svg>

      {/* Review overlay (outside SVG, conditional) */}
      {props.review?.showGuides && (
        <ReviewOverlay
          format={props.format}
          showSafeZone={props.review.showSafeZone}
          showFaceZone={props.review.showFaceZone}
          showGrid={props.review.showGrid}
          faceZone={props.review.faceZone}
          guideOpacity={props.review.guideOpacity}
        />
      )}
    </AbsoluteFill>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add src/clients/rem-maler/projects/dachbeschichtung-v2/Composition.tsx
git commit -m "feat(rem-v2): add main Composition with scene orchestration"
```

---

### Task 11: Register in Root.tsx + Verify in Studio

**Files:**
- Modify: `src/Root.tsx` (lines 61, 524-532)

- [ ] **Step 1: Add import to Root.tsx**

Add this import after the existing rem-maler import on line 61:

```ts
import { RemDachbeschichtungV2, remDachV2Schema, remDachV2Defaults } from "./clients/rem-maler/projects/dachbeschichtung-v2/Composition";
```

- [ ] **Step 2: Add Composition registration**

Inside the `<Folder name="REM-Maler">` block (after the existing `REM-Dachbeschichtung` Composition, around line 531), add:

```tsx
          <Composition
            id="REM-Dachbeschichtung-V2"
            component={RemDachbeschichtungV2}
            schema={remDachV2Schema}
            defaultProps={remDachV2Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
```

- [ ] **Step 3: Run Remotion Studio and verify**

Run: `npm run studio`

Expected: Studio loads at localhost:3000. In the composition list sidebar, under Clients → REM-Maler, "REM-Dachbeschichtung-V2" appears alongside the existing "REM-Dachbeschichtung".

- [ ] **Step 4: Visual verification**

1. Select "REM-Dachbeschichtung-V2" in Studio
2. Verify the house renders centered on the dark background
3. Scrub through the timeline: check that all 6 scenes transition smoothly
4. Check text appears and disappears at the correct frames
5. Verify the coating wipe in Scene 4 reveals red from left to right
6. Confirm the finale text holds until the end

Note: Window/door positions, particle counts, and moss placement may need visual tweaking — adjust coordinates in `constants.ts` or individual component files.

- [ ] **Step 5: Commit registration**

```bash
git add src/Root.tsx
git commit -m "feat(rem-v2): register REM-Dachbeschichtung-V2 composition"
```

---

### Task 12: Visual Polish Pass

**Files:**
- Potentially modify any component file based on Studio preview

This task is for adjustments discovered during visual verification. Common issues:

- [ ] **Step 1: Check TextReveal rendering**

If per-word `<tspan>` animation has issues with cumulative `dy` offsets, switch to rendering the entire line as one `<text>` element with uniform opacity/translateY. This is simpler and matches the Apple aesthetic.

- [ ] **Step 2: Verify house geometry**

Check that the isometric house looks correct. If windows/door appear misaligned (because `iso()` projects them correctly but SVG `<rect>` doesn't account for the isometric perspective), convert them to small `<polygon>` shapes using projected corners instead.

- [ ] **Step 3: Check scene transitions**

Scrub through transition points (frames ~110-140, ~235-265, ~410-440, ~585-615, ~760-790) and verify smooth cross-fades without visual glitches.

- [ ] **Step 4: Adjust particle positions if needed**

If moss/cracks appear outside the roof bounds, or rain drops are too sparse/dense, adjust counts and bounds in the respective component files.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "fix(rem-v2): visual polish adjustments from Studio review"
```

---

## Parallelization Notes

**Independent tasks (can run simultaneously):** Tasks 4, 5, 6, 7, 8, 9

**Sequential dependencies:**
- Task 1 (constants) must complete before any other task
- Task 2 (TextReveal) must complete before Task 10 (Composition)
- Task 3 (MinimalHouse) must complete before Task 10
- Tasks 4-9 must complete before Task 10
- Task 10 must complete before Task 11
- Task 11 must complete before Task 12
