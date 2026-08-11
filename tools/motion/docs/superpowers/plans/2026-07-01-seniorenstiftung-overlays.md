# Seniorenstiftung Recruiting-Overlays — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fünf animierte, transparente 9:16-Text-Overlays (ProRes 4444) im Clean-Teal-Look der Seniorenstiftung Prenzlauer Berg, je eines pro Recruiting-Testimonial-Video.

**Architecture:** Neuer Client `seniorenstiftung` nach dem Muster von `sauber-entsorgen`. Geteilte Komponenten (`HighlightPop`, `ChipRow`, `CTASlide`, `Logo`) + ein `SceneRenderer`, der eine `Scene[]`-Liste auf `<Sequence>`s mappt. Jedes der 5 Projekte liefert nur `scenes.ts` (Content/Timing) + eine dünne `Composition.tsx`. Registrierung in `src/Root.tsx`, Render-Skripte in `package.json`.

**Tech Stack:** Remotion 4, React 18, TypeScript, Zod, `@remotion/google-fonts/Mulish`.

## Verifikations-Hinweis (kein Test-Framework)

Das Projekt hat **kein** vitest/jest — Remotion-Kompositionen werden visuell verifiziert. Der "Test-Zyklus" jeder Task ist deshalb:
1. **Typecheck:** `npx tsc --noEmit` → muss fehlerfrei sein.
2. **Still-Render** (bei Kompositions-Tasks): `npx remotion still src/index.ts <ID> <out.png> --frame=<N>` → transparentes PNG mit nur der Grafik; Datei per Read-Tool visuell prüfen.
3. **Face-/Safe-Zone-Check:** Referenzframe aus dem Quellvideo ziehen (ffmpeg) + Overlay-Still vergleichen → keine Pille in der Face-Zone.

Kein Git-Repo → **keine Commit-Steps** (die "Commit"-Konvention des Skills entfällt hier; stattdessen endet jede Task mit erfolgreichem Typecheck + Still).

## Global Constraints

- Format aller Kompositionen: `portrait` (1080×1920), **fps 25**, `transparent: true`.
- Quell-Video-Dauern (aus ffprobe, exakt): Pflegefachkraft **55.72s**, Pflege Azubis **57.0s**, Küchenhilfe **38.8s**, Putzfachkraft **52.32s**, Allgemeines **56.64s**. `durationInSeconds` = diese Werte.
- Primärfarbe **`#0E7EBE`** (Logo-Teal). Kein warmer Zweitakzent.
- Alle Kompositionen erweitern `projectPropsSchema` aus `src/core/schemas.ts` (um `timeOffsetSec`).
- Jede Komposition rendert `<ReviewOverlay>` conditional auf `review?.showGuides` und nutzt `getCalculateMetadata(props)`.
- **Face-Zone-Regel:** Alle Overlays sitzen zentriert im Reels-Safe-Band, unter der Face-Zone. Spring-Overshoot darf nicht in die Face-Zone ragen.
- Font: **Mulish** via `@remotion/google-fonts/Mulish` (`loadFont()` je Komponente).
- Scribe-Hörfehler sind im Wording bereits korrigiert (nur freigegebene Highlight-Texte im `scenes.ts`).
- Kein eingebranntes Footage in der Komposition (reines Alpha-Overlay).

---

## Datei-Struktur

```
public/seniorenstiftung/logo.svg                         # Marken-Logo (Teal)
src/clients/seniorenstiftung/
  brand.json
  components/
    constants.ts        # Farben, Springs, SAFE-Ratios, Anchors
    useExit.ts          # Exit-Fade/Slide-Hook
    Logo.tsx            # <Img> des Logo-SVG, breitenskaliert
    HighlightPop.tsx    # Kinetic-Keyword-Pille
    ChipRow.tsx         # gestaffelte Chips
    CTASlide.tsx        # Endslide-Card
    SceneRenderer.tsx   # Scene[] → <Sequence>s (+ ReviewOverlay); exportiert Scene-Typ
    index.ts            # Re-Exports
  projects/
    pflegefachkraft/ { scenes.ts, Composition.tsx }
    pflege-azubis/   { scenes.ts, Composition.tsx }
    kuechenhilfe/    { scenes.ts, Composition.tsx }
    putzfachkraft/   { scenes.ts, Composition.tsx }
    allgemeines/     { scenes.ts, Composition.tsx }
src/Root.tsx            # +1 Folder "Seniorenstiftung" mit 5 Compositions (Modify)
package.json            # +5 Render-Skripte (Modify)
```

---

## Task 1: Client-Fundament (Assets, Konstanten, Exit-Hook)

**Files:**
- Create: `public/seniorenstiftung/logo.svg`
- Create: `src/clients/seniorenstiftung/brand.json`
- Create: `src/clients/seniorenstiftung/components/constants.ts`
- Create: `src/clients/seniorenstiftung/components/useExit.ts`

**Interfaces:**
- Produces: Farb-/Spring-Konstanten `TEAL, TEAL_DARK, TEAL_LIGHT, INK, WHITE, SAFE, PUNCH_SPRING, SMOOTH_SPRING, GENTLE_SPRING, EXIT_LEAD, CONTENT_BOTTOM`; Hook `useExit(exitFrames?) => { exitOpacity, exitSlide }`.

- [ ] **Step 1: Logo-SVG ins public-Verzeichnis kopieren**

```bash
mkdir -p public/seniorenstiftung
curl -sSL -A "Mozilla/5.0" "https://www.seniorenstiftung.org/frontend/assets/images/logo_seniorenstiftung_prenzlauer_berg_REGULAR_VERSION.svg" -o public/seniorenstiftung/logo.svg
# Verify: enthält fill:#0E7EBE
grep -o '#0E7EBE' public/seniorenstiftung/logo.svg
```
Expected: `#0E7EBE` wird ausgegeben.

- [ ] **Step 2: `brand.json` anlegen**

```json
{
  "name": "Seniorenstiftung Prenzlauer Berg",
  "colors": {
    "primary": "#0E7EBE",
    "secondary": "#0B5E8F",
    "accent": "#3AA5D8",
    "background": "#FFFFFF",
    "text": "#1E2A32"
  },
  "fonts": {
    "heading": "Mulish",
    "body": "Mulish"
  },
  "logo": "seniorenstiftung/logo.svg",
  "style": {
    "borderRadius": 16,
    "animationSpeed": "normal"
  }
}
```

- [ ] **Step 3: `constants.ts` anlegen**

```ts
// ============================================================
// Seniorenstiftung Prenzlauer Berg — Shared Constants
// Primary color = exact logo teal (#0E7EBE).
// ============================================================

export const TEAL = "#0E7EBE"; // primary (logo)
export const TEAL_DARK = "#0B5E8F"; // deep variant
export const TEAL_LIGHT = "#3AA5D8"; // accent / glow
export const INK = "#1E2A32"; // dark text
export const WHITE = "#FFFFFF";

// Reels safe zone (fractional). Content lives BELOW the face zone,
// ABOVE the IG/TikTok bottom UI. See CLAUDE.md safe-zone system.
export const SAFE = {
  top: 0.07,
  bottom: 0.575,
  left: 0.05,
  right: 0.95,
} as const;

// Default vertical anchor for overlay pills: element bottom at this
// fraction of height from the bottom (~mid-screen, clear of face zone).
export const CONTENT_BOTTOM = 0.42;

// Spring configs (calm, premium — small overshoot, face-zone-safe)
export const PUNCH_SPRING = { damping: 12, stiffness: 190, mass: 1 };
export const SMOOTH_SPRING = { damping: 16, stiffness: 130, mass: 1 };
export const GENTLE_SPRING = { damping: 22, stiffness: 110, mass: 1 };

// Exit animation lead (frames before a Sequence ends)
export const EXIT_LEAD = 9;
```

- [ ] **Step 4: `useExit.ts` anlegen**

```ts
// ============================================================
// Seniorenstiftung — Exit Animation Hook
// Fades + lifts an element during the last frames of its Sequence.
// ============================================================

import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { EXIT_LEAD } from "./constants";

export function useExit(exitFrames = EXIT_LEAD) {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exitStart = Math.max(0, durationInFrames - exitFrames);

  const exitOpacity = interpolate(frame, [exitStart, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const exitSlide = interpolate(frame, [exitStart, durationInFrames], [0, 24], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return { exitOpacity, exitSlide };
}
```

- [ ] **Step 5: Typecheck**

Run: `npx tsc --noEmit`
Expected: keine Fehler (die neuen Dateien werden von noch niemandem importiert, müssen aber selbst typen).

---

## Task 2: `Logo` + `HighlightPop`

**Files:**
- Create: `src/clients/seniorenstiftung/components/Logo.tsx`
- Create: `src/clients/seniorenstiftung/components/HighlightPop.tsx`

**Interfaces:**
- Consumes: constants aus Task 1, `useExit`.
- Produces:
  - `Logo: React.FC<{ width?: number; style?: React.CSSProperties }>`
  - `HighlightPop: React.FC<{ text: string; emphasis?: string; bottomRatio?: number; fontSizeRatio?: number }>`

- [ ] **Step 1: `Logo.tsx` anlegen**

```tsx
// ============================================================
// Seniorenstiftung — Logo (teal wordmark from public/)
// ============================================================

import React from "react";
import { Img, staticFile } from "remotion";

interface LogoProps {
  /** Rendered width in px (height auto). Default 520. */
  width?: number;
  style?: React.CSSProperties;
}

export const Logo: React.FC<LogoProps> = ({ width = 520, style }) => {
  return (
    <Img
      src={staticFile("seniorenstiftung/logo.svg")}
      style={{ width, height: "auto", display: "block", ...style }}
    />
  );
};
```

- [ ] **Step 2: `HighlightPop.tsx` anlegen**

```tsx
// ============================================================
// Seniorenstiftung — HighlightPop
// One short key phrase in a white frosted pill: spring pop-in,
// clip-path reveal from the left, growing teal accent underline.
// Optional `emphasis` word is colored teal. Sits below the face zone.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Mulish";
import {
  TEAL,
  TEAL_LIGHT,
  INK,
  CONTENT_BOTTOM,
  PUNCH_SPRING,
  SMOOTH_SPRING,
} from "./constants";
import { useExit } from "./useExit";

const { fontFamily } = loadFont();

interface HighlightPopProps {
  text: string;
  /** Substring of `text` rendered in teal. Must appear verbatim in text. */
  emphasis?: string;
  /** Distance of pill bottom from frame bottom, as fraction of height. */
  bottomRatio?: number;
  /** Font size as fraction of height. Default 0.044. */
  fontSizeRatio?: number;
}

export const HighlightPop: React.FC<HighlightPopProps> = ({
  text,
  emphasis,
  bottomRatio = CONTENT_BOTTOM,
  fontSizeRatio = 0.044,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const fontSize = Math.round(height * fontSizeRatio);
  const padV = Math.round(fontSize * 0.55);
  const padH = Math.round(fontSize * 0.8);
  const underlineHeight = Math.max(5, Math.round(fontSize * 0.09));
  const maxWidth = Math.round(width * 0.86);

  const enter = spring({ frame, fps, config: PUNCH_SPRING });
  const enterY = interpolate(enter, [0, 1], [40, 0]);
  const enterOpacity = interpolate(enter, [0, 0.4], [0, 1], {
    extrapolateRight: "clamp",
  });

  const revealFrames = Math.min(
    Math.floor(durationInFrames * 0.35),
    Math.floor(fps * 0.6),
  );
  const revealPct = interpolate(frame - 3, [0, revealFrames], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const underlineProg = spring({
    frame: frame - 3 - revealFrames,
    fps,
    config: SMOOTH_SPRING,
  });

  const bottomPx = Math.round(height * bottomRatio);

  // Split text around the emphasis substring (first occurrence).
  let parts: React.ReactNode = text;
  if (emphasis && text.includes(emphasis)) {
    const i = text.indexOf(emphasis);
    parts = (
      <>
        {text.slice(0, i)}
        <span style={{ color: TEAL }}>{emphasis}</span>
        {text.slice(i + emphasis.length)}
      </>
    );
  }

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottomPx,
        left: "50%",
        transform: "translateX(-50%)",
        opacity: enterOpacity * exitOpacity,
      }}
    >
      <div style={{ transform: `translateY(${enterY - exitSlide}px)` }}>
        <div
          style={{
            maxWidth,
            padding: `${padV}px ${padH}px`,
            backgroundColor: "rgba(255,255,255,0.94)",
            borderRadius: Math.round(fontSize * 0.6),
            boxShadow:
              "0 18px 50px rgba(14,60,90,0.28), 0 4px 14px rgba(14,60,90,0.16)",
            backdropFilter: "blur(6px)",
            WebkitBackdropFilter: "blur(6px)",
          }}
        >
          <div
            style={{
              clipPath: `inset(0 ${100 - revealPct}% 0 0)`,
              fontFamily,
              fontSize,
              fontWeight: 800,
              color: INK,
              lineHeight: 1.25,
              letterSpacing: -Math.round(fontSize * 0.01),
              textAlign: "center",
              whiteSpace: "nowrap",
            }}
          >
            {parts}
          </div>
          <div
            style={{
              marginTop: Math.round(fontSize * 0.22),
              marginInline: "auto",
              height: underlineHeight,
              width: `${underlineProg * 70}%`,
              maxWidth: "70%",
              background: `linear-gradient(90deg, ${TEAL}, ${TEAL_LIGHT})`,
              borderRadius: underlineHeight,
              boxShadow: `0 0 16px ${TEAL_LIGHT}88`,
            }}
          />
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 3: Typecheck**

Run: `npx tsc --noEmit`
Expected: keine Fehler.

---

## Task 3: `ChipRow` + `CTASlide` + `index.ts`

**Files:**
- Create: `src/clients/seniorenstiftung/components/ChipRow.tsx`
- Create: `src/clients/seniorenstiftung/components/CTASlide.tsx`
- Create: `src/clients/seniorenstiftung/components/index.ts`

**Interfaces:**
- Consumes: constants, `useExit`, `Logo`.
- Produces:
  - `ChipRow: React.FC<{ chips: string[]; staggerFrames?: number; bottomRatio?: number; fontSizeRatio?: number }>`
  - `CTASlide: React.FC<{ headline: string; sub: string; emphasis?: string; anchorY?: number }>`
  - `index.ts` re-exportiert alle Komponenten + Konstanten.

- [ ] **Step 1: `ChipRow.tsx` anlegen**

```tsx
// ============================================================
// Seniorenstiftung — ChipRow
// A centered, wrapping row of frosted chips (teal dot + label)
// that pop in staggered. For value/role enumerations.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Mulish";
import { TEAL, INK, CONTENT_BOTTOM, PUNCH_SPRING } from "./constants";
import { useExit } from "./useExit";

const { fontFamily } = loadFont();

interface ChipRowProps {
  chips: string[];
  /** Frames between each chip's entrance. Default 8. */
  staggerFrames?: number;
  bottomRatio?: number;
  /** Font size as fraction of height. Default 0.03. */
  fontSizeRatio?: number;
}

export const ChipRow: React.FC<ChipRowProps> = ({
  chips,
  staggerFrames = 8,
  bottomRatio = CONTENT_BOTTOM,
  fontSizeRatio = 0.03,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const fontSize = Math.round(height * fontSizeRatio);
  const padV = Math.round(fontSize * 0.55);
  const padH = Math.round(fontSize * 0.85);
  const dot = Math.round(fontSize * 0.5);
  const bottomPx = Math.round(height * bottomRatio);

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottomPx,
        left: "50%",
        transform: `translateX(-50%) translateY(${-exitSlide}px)`,
        opacity: exitOpacity,
        width: Math.round(width * 0.9),
        display: "flex",
        flexWrap: "wrap",
        gap: Math.round(fontSize * 0.55),
        justifyContent: "center",
      }}
    >
      {chips.map((label, i) => {
        const p = spring({
          frame: frame - i * staggerFrames,
          fps,
          config: PUNCH_SPRING,
        });
        const opacity = interpolate(p, [0, 0.5], [0, 1], {
          extrapolateRight: "clamp",
        });
        const scale = interpolate(p, [0, 1], [0.7, 1]);
        const y = interpolate(p, [0, 1], [22, 0]);
        return (
          <div
            key={i}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: Math.round(fontSize * 0.4),
              padding: `${padV}px ${padH}px`,
              backgroundColor: "rgba(255,255,255,0.94)",
              borderRadius: 999,
              boxShadow: "0 12px 30px rgba(14,60,90,0.22)",
              backdropFilter: "blur(6px)",
              WebkitBackdropFilter: "blur(6px)",
              opacity,
              transform: `translateY(${y}px) scale(${scale})`,
            }}
          >
            <div
              style={{
                width: dot,
                height: dot,
                borderRadius: "50%",
                backgroundColor: TEAL,
                flexShrink: 0,
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize,
                fontWeight: 800,
                color: INK,
                whiteSpace: "nowrap",
              }}
            >
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
};
```

- [ ] **Step 2: `CTASlide.tsx` anlegen**

```tsx
// ============================================================
// Seniorenstiftung — CTASlide (end card)
// Frosted white card in the lower-mid band: eyebrow "JETZT BEWERBEN",
// role headline, logo, and the brand claim. Staged reveal.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Mulish";
import { TEAL, INK, TEAL_DARK, PUNCH_SPRING, SMOOTH_SPRING } from "./constants";
import { useExit } from "./useExit";
import { Logo } from "./Logo";

const { fontFamily } = loadFont();

interface CTASlideProps {
  /** Main line, e.g. "Werde Pflegefachkraft". */
  headline: string;
  /** Eyebrow / action line, e.g. "Jetzt bewerben". */
  sub: string;
  /** Optional teal-highlighted substring of headline. */
  emphasis?: string;
  /** Top anchor of the card as fraction of height. Default 0.34. */
  anchorY?: number;
}

export const CTASlide: React.FC<CTASlideProps> = ({
  headline,
  sub,
  emphasis,
  anchorY = 0.34,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const headSize = Math.round(height * 0.05);
  const pad = Math.round(headSize * 0.7);
  const maxWidth = Math.round(width * 0.84);

  const enter = spring({ frame, fps, config: PUNCH_SPRING });
  const opacity = interpolate(enter, [0, 0.4], [0, 1], {
    extrapolateRight: "clamp",
  });
  const y = interpolate(enter, [0, 1], [40, 0]);

  const logoProg = spring({ frame: frame - 14, fps, config: SMOOTH_SPRING });
  const claimProg = spring({ frame: frame - 24, fps, config: SMOOTH_SPRING });

  let head: React.ReactNode = headline;
  if (emphasis && headline.includes(emphasis)) {
    const i = headline.indexOf(emphasis);
    head = (
      <>
        {headline.slice(0, i)}
        <span style={{ color: TEAL }}>{emphasis}</span>
        {headline.slice(i + emphasis.length)}
      </>
    );
  }

  return (
    <div
      style={{
        position: "absolute",
        top: Math.round(height * anchorY),
        left: "50%",
        transform: `translateX(-50%) translateY(${y + exitSlide}px)`,
        opacity: opacity * exitOpacity,
        width: maxWidth,
      }}
    >
      <div
        style={{
          padding: `${Math.round(pad * 1.3)}px ${pad}px`,
          backgroundColor: "rgba(255,255,255,0.97)",
          borderRadius: Math.round(headSize * 0.5),
          boxShadow:
            "0 26px 64px rgba(14,60,90,0.34), 0 6px 18px rgba(14,60,90,0.2)",
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily,
            fontSize: Math.round(headSize * 0.36),
            fontWeight: 900,
            color: TEAL,
            textTransform: "uppercase",
            letterSpacing: Math.round(headSize * 0.06),
            marginBottom: Math.round(headSize * 0.28),
          }}
        >
          {sub}
        </div>
        <div
          style={{
            fontFamily,
            fontSize: headSize,
            fontWeight: 900,
            color: INK,
            lineHeight: 1.15,
            letterSpacing: -Math.round(headSize * 0.015),
          }}
        >
          {head}
        </div>
        <div
          style={{
            marginTop: Math.round(headSize * 0.6),
            display: "flex",
            justifyContent: "center",
            opacity: logoProg,
            transform: `translateY(${interpolate(logoProg, [0, 1], [12, 0])}px)`,
          }}
        >
          <Logo width={Math.round(width * 0.52)} />
        </div>
        <div
          style={{
            marginTop: Math.round(headSize * 0.4),
            fontFamily,
            fontSize: Math.round(headSize * 0.4),
            fontWeight: 700,
            fontStyle: "italic",
            color: TEAL_DARK,
            opacity: claimProg,
          }}
        >
          Geborgen in guten Händen
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 3: `index.ts` anlegen**

```ts
export { Logo } from "./Logo";
export { HighlightPop } from "./HighlightPop";
export { ChipRow } from "./ChipRow";
export { CTASlide } from "./CTASlide";
export { SceneRenderer } from "./SceneRenderer";
export type { Scene } from "./SceneRenderer";
export { useExit } from "./useExit";
export {
  TEAL,
  TEAL_DARK,
  TEAL_LIGHT,
  INK,
  WHITE,
  SAFE,
  CONTENT_BOTTOM,
  PUNCH_SPRING,
  SMOOTH_SPRING,
  GENTLE_SPRING,
  EXIT_LEAD,
} from "./constants";
```

Note: `index.ts` referenziert `SceneRenderer` (Task 4). Typecheck von Task 3 wird deshalb ERST nach Task 4 grün — daher Typecheck-Step am Ende von Task 4.

- [ ] **Step 4: Typecheck der Einzelkomponenten (ohne index)**

Run: `npx tsc --noEmit`
Expected: EIN erwarteter Fehler — `index.ts` findet `./SceneRenderer` noch nicht. `Logo.tsx`, `HighlightPop.tsx`, `ChipRow.tsx`, `CTASlide.tsx` selbst sind fehlerfrei. (Wird in Task 4 aufgelöst.)

---

## Task 4: `SceneRenderer` + erste Komposition (Pflegefachkraft, Referenz)

**Files:**
- Create: `src/clients/seniorenstiftung/components/SceneRenderer.tsx`
- Create: `src/clients/seniorenstiftung/projects/pflegefachkraft/scenes.ts`
- Create: `src/clients/seniorenstiftung/projects/pflegefachkraft/Composition.tsx`
- Modify: `src/Root.tsx` (Import + Folder "Seniorenstiftung" + 1. Composition)
- Modify: `package.json` (Render-Skript `render:st:pflegefachkraft`)

**Interfaces:**
- Consumes: `HighlightPop`, `ChipRow`, `CTASlide` (Tasks 2–3).
- Produces:
  - `type Scene` (diskriminierte Union, siehe unten)
  - `SceneRenderer: React.FC<{ scenes: Scene[]; timeOffsetSec: number; review?: ReviewConfig }>`
  - `PflegefachkraftOverlay` + `pflegefachkraftSchema` + `pflegefachkraftDefaults`

- [ ] **Step 1: `SceneRenderer.tsx` anlegen**

```tsx
// ============================================================
// Seniorenstiftung — SceneRenderer
// Maps a Scene[] to <Sequence>s and draws the ReviewOverlay.
// Shared by all 5 project compositions.
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { reviewConfigSchema } from "../../../core/schemas";
import { ReviewOverlay } from "../../../components/layout/ReviewOverlay";
import { HighlightPop } from "./HighlightPop";
import { ChipRow } from "./ChipRow";
import { CTASlide } from "./CTASlide";

export type Scene =
  | {
      kind: "highlight";
      startSec: number;
      durationSec: number;
      text: string;
      emphasis?: string;
      bottomRatio?: number;
      fontSizeRatio?: number;
    }
  | {
      kind: "chips";
      startSec: number;
      durationSec: number;
      chips: string[];
      staggerFrames?: number;
      bottomRatio?: number;
    }
  | {
      kind: "cta";
      startSec: number;
      durationSec: number;
      headline: string;
      sub: string;
      emphasis?: string;
      anchorY?: number;
    };

interface SceneRendererProps {
  scenes: Scene[];
  timeOffsetSec: number;
  review?: z.infer<typeof reviewConfigSchema>;
}

export const SceneRenderer: React.FC<SceneRendererProps> = ({
  scenes,
  timeOffsetSec,
  review,
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.max(0, Math.floor((sec + timeOffsetSec) * fps));

  return (
    <AbsoluteFill>
      {scenes.map((scene, i) => {
        const from = s(scene.startSec);
        const durationInFrames = Math.floor(scene.durationSec * fps);
        const key = `scene-${i}-${scene.kind}`;
        let name: string = scene.kind;
        let body: React.ReactNode = null;

        switch (scene.kind) {
          case "highlight":
            name = `Highlight: ${scene.text}`;
            body = (
              <HighlightPop
                text={scene.text}
                emphasis={scene.emphasis}
                bottomRatio={scene.bottomRatio}
                fontSizeRatio={scene.fontSizeRatio}
              />
            );
            break;
          case "chips":
            name = `Chips: ${scene.chips.join(" · ")}`;
            body = (
              <ChipRow
                chips={scene.chips}
                staggerFrames={scene.staggerFrames}
                bottomRatio={scene.bottomRatio}
              />
            );
            break;
          case "cta":
            name = `CTA: ${scene.headline}`;
            body = (
              <CTASlide
                headline={scene.headline}
                sub={scene.sub}
                emphasis={scene.emphasis}
                anchorY={scene.anchorY}
              />
            );
            break;
        }

        return (
          <Sequence key={key} from={from} durationInFrames={durationInFrames} name={name}>
            {body}
          </Sequence>
        );
      })}

      {review?.showGuides && (
        <ReviewOverlay
          showSafeZone={review.showSafeZone ?? true}
          showFaceZone={review.showFaceZone ?? true}
          showGrid={review.showGrid ?? false}
          faceZone={review.faceZone}
          guideOpacity={review.guideOpacity ?? 0.35}
        />
      )}
    </AbsoluteFill>
  );
};
```

Note: `ReviewOverlay`-Props anhand `src/components/layout/ReviewOverlay.tsx` verifizieren; falls die Prop-Signatur abweicht, exakt an die dort definierte anpassen (gleiches Muster wie in `sauber-entsorgen/projects/reel-1/Composition.tsx:161-168`).

- [ ] **Step 2: Referenzframe aus dem Quellvideo ziehen (Face-Position bestimmen)**

```bash
ffmpeg -y -i "Video inputs/Seniorenstiftung/Pflegefachkraft.mp4" -vf "select=eq(n\,120)" -vframes 1 /tmp/st-pflege-ref.png -loglevel error
```
Referenzframe per Read-Tool ansehen; grob notieren, in welchem vertikalen Bereich (Fraktion der Höhe) das Gesicht liegt → daraus `faceZone` + ob `CONTENT_BOTTOM` (0.42) die Pillen sicher darunter hält. Default-`faceZone` unten in Step 4; nur anpassen, wenn das Gesicht deutlich tiefer/höher sitzt.

- [ ] **Step 3: `scenes.ts` (Pflegefachkraft) anlegen**

```ts
// Seniorenstiftung — Pflegefachkraft (9:16, 25fps, 55.72s)
// Highlight timings derived from transcript SRT. t=0 = video start.
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  { kind: "highlight", startSec: 2.4, durationSec: 3.0, text: "Mehr als Aufgaben", emphasis: "Aufgaben" },
  { kind: "chips", startSec: 6.4, durationSec: 5.6, chips: ["Vertrauen", "Nähe", "Team"], staggerFrames: 10 },
  { kind: "highlight", startSec: 19.2, durationSec: 5.2, text: "Ein Platz mit Perspektive", emphasis: "Perspektive" },
  { kind: "highlight", startSec: 25.2, durationSec: 3.4, text: "Fort- & Weiterbildung" },
  { kind: "chips", startSec: 37.2, durationSec: 6.6, chips: ["Respekt", "Kommunikation", "Team"], staggerFrames: 10 },
  { kind: "cta", startSec: 48.0, durationSec: 7.72, headline: "Werde Pflegefachkraft", sub: "Jetzt bewerben", emphasis: "Pflegefachkraft" },
];
```

- [ ] **Step 4: `Composition.tsx` (Pflegefachkraft) anlegen**

```tsx
// Seniorenstiftung — Pflegefachkraft Overlay (transparent, 9:16)
import React from "react";
import { useVideoConfig } from "remotion";
import { z } from "zod";
import { projectPropsSchema } from "../../../../core/schemas";
import { SceneRenderer } from "../../components";
import { SCENES } from "./scenes";

export const pflegefachkraftSchema = projectPropsSchema.extend({
  timeOffsetSec: z
    .number()
    .step(0.1)
    .describe("Globaler Zeit-Offset (Sek) zum Ausrichten aufs Footage"),
});

export type PflegefachkraftProps = z.infer<typeof pflegefachkraftSchema>;

export const pflegefachkraftDefaults: PflegefachkraftProps = {
  format: "portrait",
  fps: 25,
  durationInSeconds: 55.72,
  transparent: true,
  timeOffsetSec: 0,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    faceZone: { top: 0.08, bottom: 0.45, left: 0.18, right: 0.82 },
    guideOpacity: 0.35,
  },
};

export const PflegefachkraftOverlay: React.FC<PflegefachkraftProps> = ({
  review,
  timeOffsetSec,
}) => {
  useVideoConfig();
  return (
    <SceneRenderer scenes={SCENES} timeOffsetSec={timeOffsetSec} review={review} />
  );
};
```

- [ ] **Step 5: In `src/Root.tsx` registrieren**

Import-Zeile nach den Sauber-Entsorgen-Imports (nach `src/Root.tsx:52`) einfügen:
```tsx
import { PflegefachkraftOverlay, pflegefachkraftSchema, pflegefachkraftDefaults } from "./clients/seniorenstiftung/projects/pflegefachkraft/Composition";
```
Neuen Folder direkt vor der schließenden `</Folder>` des Clients-Blocks (vor `src/Root.tsx:595`) einfügen:
```tsx
        <Folder name="Seniorenstiftung">
          <Composition
            id="Seniorenstiftung-Pflegefachkraft"
            component={PflegefachkraftOverlay}
            schema={pflegefachkraftSchema}
            defaultProps={pflegefachkraftDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>
```

- [ ] **Step 6: Render-Skript in `package.json` ergänzen**

Nach `src/index.ts` Skript-Block (nach der letzten `render:se:*`-Zeile) einfügen:
```json
    "render:st:pflegefachkraft": "remotion render src/index.ts Seniorenstiftung-Pflegefachkraft out/seniorenstiftung/pflegefachkraft.mov --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444",
```

- [ ] **Step 7: Typecheck**

Run: `npx tsc --noEmit`
Expected: keine Fehler (jetzt ist auch `index.ts` → `SceneRenderer` aufgelöst).

- [ ] **Step 8: Still-Renders zur Sichtprüfung**

```bash
mkdir -p out/seniorenstiftung/stills
# Highlight bei ~3s (frame 75), Chips bei ~8s (200), CTA bei ~51s (1275)
npx remotion still src/index.ts Seniorenstiftung-Pflegefachkraft out/seniorenstiftung/stills/pf-075.png --frame=75
npx remotion still src/index.ts Seniorenstiftung-Pflegefachkraft out/seniorenstiftung/stills/pf-200.png --frame=200
npx remotion still src/index.ts Seniorenstiftung-Pflegefachkraft out/seniorenstiftung/stills/pf-1275.png --frame=1275
```
Die drei PNGs per Read-Tool prüfen: Pille/Chips/CTA sichtbar, zentriert im unteren-mittleren Band, Text nicht abgeschnitten, Teal-Akzent sichtbar, transparenter Hintergrund.

- [ ] **Step 9: Face-/Safe-Zone-Guide-Still**

```bash
npx remotion still src/index.ts Seniorenstiftung-Pflegefachkraft out/seniorenstiftung/stills/pf-guides-075.png --frame=75 --props='{"review":{"showGuides":true,"showSafeZone":true,"showFaceZone":true,"showGrid":false,"guideOpacity":0.35}}'
```
Prüfen: HighlightPop liegt vollständig UNTER der roten Face-Zone und INNERHALB der grünen Safe-Zone. Falls nicht → `CONTENT_BOTTOM` in `constants.ts` senken (z.B. 0.40) oder `faceZone.bottom` anpassen und Step 8–9 wiederholen.

---

## Task 5: Komposition Pflege Azubis

**Files:**
- Create: `src/clients/seniorenstiftung/projects/pflege-azubis/scenes.ts`
- Create: `src/clients/seniorenstiftung/projects/pflege-azubis/Composition.tsx`
- Modify: `src/Root.tsx`
- Modify: `package.json`

**Interfaces:**
- Consumes: `SceneRenderer`, `Scene`, `projectPropsSchema`.
- Produces: `PflegeAzubisOverlay`, `pflegeAzubisSchema`, `pflegeAzubisDefaults`.

- [ ] **Step 1: `scenes.ts` anlegen**

```ts
// Seniorenstiftung — Pflege Azubis (9:16, 25fps, 57.0s)
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  { kind: "highlight", startSec: 3.0, durationSec: 3.4, text: "Wirklich gebraucht werden", emphasis: "gebraucht" },
  { kind: "highlight", startSec: 21.0, durationSec: 3.4, text: "Schritt für Schritt" },
  { kind: "chips", startSec: 32.0, durationSec: 6.0, chips: ["Blutdruck messen", "Puls messen", "Nähe"], staggerFrames: 10 },
  { kind: "highlight", startSec: 41.0, durationSec: 5.5, text: "Ein Lächeln schenken", emphasis: "Lächeln" },
  { kind: "highlight", startSec: 47.1, durationSec: 2.4, text: "Haus mit Garten" },
  { kind: "cta", startSec: 50.0, durationSec: 7.0, headline: "Starte deine Ausbildung", sub: "Jetzt bewerben", emphasis: "Ausbildung" },
];
```

- [ ] **Step 2: `Composition.tsx` anlegen**

```tsx
// Seniorenstiftung — Pflege Azubis Overlay (transparent, 9:16)
import React from "react";
import { useVideoConfig } from "remotion";
import { z } from "zod";
import { projectPropsSchema } from "../../../../core/schemas";
import { SceneRenderer } from "../../components";
import { SCENES } from "./scenes";

export const pflegeAzubisSchema = projectPropsSchema.extend({
  timeOffsetSec: z.number().step(0.1).describe("Globaler Zeit-Offset (Sek)"),
});

export type PflegeAzubisProps = z.infer<typeof pflegeAzubisSchema>;

export const pflegeAzubisDefaults: PflegeAzubisProps = {
  format: "portrait",
  fps: 25,
  durationInSeconds: 57.0,
  transparent: true,
  timeOffsetSec: 0,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    faceZone: { top: 0.08, bottom: 0.45, left: 0.18, right: 0.82 },
    guideOpacity: 0.35,
  },
};

export const PflegeAzubisOverlay: React.FC<PflegeAzubisProps> = ({
  review,
  timeOffsetSec,
}) => {
  useVideoConfig();
  return <SceneRenderer scenes={SCENES} timeOffsetSec={timeOffsetSec} review={review} />;
};
```

- [ ] **Step 3: In `src/Root.tsx` registrieren**

Import ergänzen:
```tsx
import { PflegeAzubisOverlay, pflegeAzubisSchema, pflegeAzubisDefaults } from "./clients/seniorenstiftung/projects/pflege-azubis/Composition";
```
Im Folder "Seniorenstiftung" ergänzen:
```tsx
          <Composition
            id="Seniorenstiftung-PflegeAzubis"
            component={PflegeAzubisOverlay}
            schema={pflegeAzubisSchema}
            defaultProps={pflegeAzubisDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
```

- [ ] **Step 4: Render-Skript in `package.json`**

```json
    "render:st:pflege-azubis": "remotion render src/index.ts Seniorenstiftung-PflegeAzubis out/seniorenstiftung/pflege-azubis.mov --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444",
```

- [ ] **Step 5: Typecheck**

Run: `npx tsc --noEmit`
Expected: keine Fehler.

- [ ] **Step 6: Stills prüfen**

```bash
npx remotion still src/index.ts Seniorenstiftung-PflegeAzubis out/seniorenstiftung/stills/pa-090.png --frame=90
npx remotion still src/index.ts Seniorenstiftung-PflegeAzubis out/seniorenstiftung/stills/pa-1075.png --frame=1075
npx remotion still src/index.ts Seniorenstiftung-PflegeAzubis out/seniorenstiftung/stills/pa-1325.png --frame=1325
```
Prüfen wie in Task 4, Step 8.

---

## Task 6: Komposition Küchenhilfe

**Files:**
- Create: `src/clients/seniorenstiftung/projects/kuechenhilfe/scenes.ts`
- Create: `src/clients/seniorenstiftung/projects/kuechenhilfe/Composition.tsx`
- Modify: `src/Root.tsx`
- Modify: `package.json`

**Interfaces:**
- Produces: `KuechenhilfeOverlay`, `kuechenhilfeSchema`, `kuechenhilfeDefaults`.

- [ ] **Step 1: `scenes.ts` anlegen**

```ts
// Seniorenstiftung — Küchenhilfe (9:16, 25fps, 38.8s)
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  { kind: "highlight", startSec: 13.1, durationSec: 3.6, text: "Willkommen & gesehen", emphasis: "gesehen" },
  { kind: "highlight", startSec: 17.3, durationSec: 6.4, text: "Struktur + echter Sinn", emphasis: "Sinn" },
  { kind: "highlight", startSec: 29.3, durationSec: 2.8, text: "Offenes Team" },
  { kind: "cta", startSec: 32.9, durationSec: 5.9, headline: "Küchen- & Servicekraft werden", sub: "Bewirb dich jetzt", emphasis: "Küchen- & Servicekraft" },
];
```

- [ ] **Step 2: `Composition.tsx` anlegen**

```tsx
// Seniorenstiftung — Küchenhilfe Overlay (transparent, 9:16)
import React from "react";
import { useVideoConfig } from "remotion";
import { z } from "zod";
import { projectPropsSchema } from "../../../../core/schemas";
import { SceneRenderer } from "../../components";
import { SCENES } from "./scenes";

export const kuechenhilfeSchema = projectPropsSchema.extend({
  timeOffsetSec: z.number().step(0.1).describe("Globaler Zeit-Offset (Sek)"),
});

export type KuechenhilfeProps = z.infer<typeof kuechenhilfeSchema>;

export const kuechenhilfeDefaults: KuechenhilfeProps = {
  format: "portrait",
  fps: 25,
  durationInSeconds: 38.8,
  transparent: true,
  timeOffsetSec: 0,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    faceZone: { top: 0.08, bottom: 0.45, left: 0.18, right: 0.82 },
    guideOpacity: 0.35,
  },
};

export const KuechenhilfeOverlay: React.FC<KuechenhilfeProps> = ({
  review,
  timeOffsetSec,
}) => {
  useVideoConfig();
  return <SceneRenderer scenes={SCENES} timeOffsetSec={timeOffsetSec} review={review} />;
};
```

- [ ] **Step 3: In `src/Root.tsx` registrieren**

```tsx
import { KuechenhilfeOverlay, kuechenhilfeSchema, kuechenhilfeDefaults } from "./clients/seniorenstiftung/projects/kuechenhilfe/Composition";
```
```tsx
          <Composition
            id="Seniorenstiftung-Kuechenhilfe"
            component={KuechenhilfeOverlay}
            schema={kuechenhilfeSchema}
            defaultProps={kuechenhilfeDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
```

- [ ] **Step 4: Render-Skript in `package.json`**

```json
    "render:st:kuechenhilfe": "remotion render src/index.ts Seniorenstiftung-Kuechenhilfe out/seniorenstiftung/kuechenhilfe.mov --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444",
```

- [ ] **Step 5: Typecheck**

Run: `npx tsc --noEmit`
Expected: keine Fehler.

- [ ] **Step 6: Stills prüfen**

```bash
npx remotion still src/index.ts Seniorenstiftung-Kuechenhilfe out/seniorenstiftung/stills/kh-350.png --frame=350
npx remotion still src/index.ts Seniorenstiftung-Kuechenhilfe out/seniorenstiftung/stills/kh-460.png --frame=460
npx remotion still src/index.ts Seniorenstiftung-Kuechenhilfe out/seniorenstiftung/stills/kh-880.png --frame=880
```
Prüfen wie in Task 4, Step 8. Der CTA-Titel „Küchen- & Servicekraft werden" ist lang → sicherstellen, dass er in der Card umbricht/passt; falls zu breit, `anchorY` unverändert lassen, aber ggf. Headline-`fontSizeRatio` in `CTASlide` bleibt fix — der Text darf 2-zeilig sein (lineHeight 1.15 deckt das ab).

---

## Task 7: Komposition Putzfachkraft

**Files:**
- Create: `src/clients/seniorenstiftung/projects/putzfachkraft/scenes.ts`
- Create: `src/clients/seniorenstiftung/projects/putzfachkraft/Composition.tsx`
- Modify: `src/Root.tsx`
- Modify: `package.json`

**Interfaces:**
- Produces: `PutzfachkraftOverlay`, `putzfachkraftSchema`, `putzfachkraftDefaults`.

- [ ] **Step 1: `scenes.ts` anlegen**

```ts
// Seniorenstiftung — Putzfachkraft / Reinigungskraft (9:16, 25fps, 52.32s)
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  { kind: "highlight", startSec: 0.2, durationSec: 2.9, text: "Erst auf, wenn sie fehlt", emphasis: "fehlt" },
  { kind: "chips", startSec: 21.0, durationSec: 7.2, chips: ["Respekt", "Hygiene", "Verantwortung"], staggerFrames: 10 },
  { kind: "highlight", startSec: 33.7, durationSec: 7.4, text: "Deine Arbeit wird gesehen", emphasis: "wird gesehen" },
  { kind: "cta", startSec: 42.3, durationSec: 10.0, headline: "Werde Reinigungskraft", sub: "Jetzt bewerben", emphasis: "Reinigungskraft" },
];
```

- [ ] **Step 2: `Composition.tsx` anlegen**

```tsx
// Seniorenstiftung — Putzfachkraft Overlay (transparent, 9:16)
import React from "react";
import { useVideoConfig } from "remotion";
import { z } from "zod";
import { projectPropsSchema } from "../../../../core/schemas";
import { SceneRenderer } from "../../components";
import { SCENES } from "./scenes";

export const putzfachkraftSchema = projectPropsSchema.extend({
  timeOffsetSec: z.number().step(0.1).describe("Globaler Zeit-Offset (Sek)"),
});

export type PutzfachkraftProps = z.infer<typeof putzfachkraftSchema>;

export const putzfachkraftDefaults: PutzfachkraftProps = {
  format: "portrait",
  fps: 25,
  durationInSeconds: 52.32,
  transparent: true,
  timeOffsetSec: 0,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    faceZone: { top: 0.08, bottom: 0.45, left: 0.18, right: 0.82 },
    guideOpacity: 0.35,
  },
};

export const PutzfachkraftOverlay: React.FC<PutzfachkraftProps> = ({
  review,
  timeOffsetSec,
}) => {
  useVideoConfig();
  return <SceneRenderer scenes={SCENES} timeOffsetSec={timeOffsetSec} review={review} />;
};
```

- [ ] **Step 3: In `src/Root.tsx` registrieren**

```tsx
import { PutzfachkraftOverlay, putzfachkraftSchema, putzfachkraftDefaults } from "./clients/seniorenstiftung/projects/putzfachkraft/Composition";
```
```tsx
          <Composition
            id="Seniorenstiftung-Putzfachkraft"
            component={PutzfachkraftOverlay}
            schema={putzfachkraftSchema}
            defaultProps={putzfachkraftDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
```

- [ ] **Step 4: Render-Skript in `package.json`**

```json
    "render:st:putzfachkraft": "remotion render src/index.ts Seniorenstiftung-Putzfachkraft out/seniorenstiftung/putzfachkraft.mov --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444",
```

- [ ] **Step 5: Typecheck**

Run: `npx tsc --noEmit`
Expected: keine Fehler.

- [ ] **Step 6: Stills prüfen**

```bash
npx remotion still src/index.ts Seniorenstiftung-Putzfachkraft out/seniorenstiftung/stills/pk-040.png --frame=40
npx remotion still src/index.ts Seniorenstiftung-Putzfachkraft out/seniorenstiftung/stills/pk-600.png --frame=600
npx remotion still src/index.ts Seniorenstiftung-Putzfachkraft out/seniorenstiftung/stills/pk-1150.png --frame=1150
```
Prüfen wie in Task 4, Step 8.

---

## Task 8: Komposition Allgemeines

**Files:**
- Create: `src/clients/seniorenstiftung/projects/allgemeines/scenes.ts`
- Create: `src/clients/seniorenstiftung/projects/allgemeines/Composition.tsx`
- Modify: `src/Root.tsx`
- Modify: `package.json`

**Interfaces:**
- Produces: `AllgemeinesOverlay`, `allgemeinesSchema`, `allgemeinesDefaults`.

- [ ] **Step 1: `scenes.ts` anlegen**

```ts
// Seniorenstiftung — Allgemeines Video (9:16, 25fps, 56.64s)
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  { kind: "highlight", startSec: 2.0, durationSec: 5.0, text: "Nicht Versprechen — spürbar", emphasis: "spürbar" },
  { kind: "highlight", startSec: 19.3, durationSec: 3.6, text: "Mehr als ein Job", emphasis: "Job" },
  { kind: "chips", startSec: 23.5, durationSec: 6.0, chips: ["Entwicklung", "Team", "Sinn"], staggerFrames: 10 },
  { kind: "chips", startSec: 36.0, durationSec: 4.4, chips: ["Pflege", "Ausbildung", "Küche", "Service", "Reinigung", "Betreuung"], staggerFrames: 6, bottomRatio: 0.44 },
  { kind: "highlight", startSec: 40.6, durationSec: 4.4, text: "Geborgen", emphasis: "Geborgen" },
  { kind: "cta", startSec: 45.3, durationSec: 11.34, headline: "Werde Teil der Seniorenstiftung", sub: "Jetzt bewerben", emphasis: "Seniorenstiftung" },
];
```

- [ ] **Step 2: `Composition.tsx` anlegen**

```tsx
// Seniorenstiftung — Allgemeines Overlay (transparent, 9:16)
import React from "react";
import { useVideoConfig } from "remotion";
import { z } from "zod";
import { projectPropsSchema } from "../../../../core/schemas";
import { SceneRenderer } from "../../components";
import { SCENES } from "./scenes";

export const allgemeinesSchema = projectPropsSchema.extend({
  timeOffsetSec: z.number().step(0.1).describe("Globaler Zeit-Offset (Sek)"),
});

export type AllgemeinesProps = z.infer<typeof allgemeinesSchema>;

export const allgemeinesDefaults: AllgemeinesProps = {
  format: "portrait",
  fps: 25,
  durationInSeconds: 56.64,
  transparent: true,
  timeOffsetSec: 0,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    faceZone: { top: 0.08, bottom: 0.45, left: 0.18, right: 0.82 },
    guideOpacity: 0.35,
  },
};

export const AllgemeinesOverlay: React.FC<AllgemeinesProps> = ({
  review,
  timeOffsetSec,
}) => {
  useVideoConfig();
  return <SceneRenderer scenes={SCENES} timeOffsetSec={timeOffsetSec} review={review} />;
};
```

- [ ] **Step 3: In `src/Root.tsx` registrieren**

```tsx
import { AllgemeinesOverlay, allgemeinesSchema, allgemeinesDefaults } from "./clients/seniorenstiftung/projects/allgemeines/Composition";
```
```tsx
          <Composition
            id="Seniorenstiftung-Allgemeines"
            component={AllgemeinesOverlay}
            schema={allgemeinesSchema}
            defaultProps={allgemeinesDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
```

- [ ] **Step 4: Render-Skript in `package.json`**

```json
    "render:st:allgemeines": "remotion render src/index.ts Seniorenstiftung-Allgemeines out/seniorenstiftung/allgemeines.mov --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444",
```

- [ ] **Step 5: Typecheck**

Run: `npx tsc --noEmit`
Expected: keine Fehler.

- [ ] **Step 6: Stills prüfen**

```bash
npx remotion still src/index.ts Seniorenstiftung-Allgemeines out/seniorenstiftung/stills/ag-060.png --frame=60
npx remotion still src/index.ts Seniorenstiftung-Allgemeines out/seniorenstiftung/stills/ag-950.png --frame=950
npx remotion still src/index.ts Seniorenstiftung-Allgemeines out/seniorenstiftung/stills/ag-1200.png --frame=1200
```
Prüfen wie in Task 4, Step 8. Die 6-Rollen-Chips (frame ~950) müssen zentriert umbrechen und in der Safe-Zone bleiben.

---

## Task 9: Gesamt-Review (Face-Zone-Scrub + Delivery-Konformität)

**Files:**
- Modify (bei Bedarf): `src/clients/seniorenstiftung/components/constants.ts` (`CONTENT_BOTTOM`), einzelne `scenes.ts` (Timing/`bottomRatio`), einzelne `Composition.tsx` (`faceZone`).

**Interfaces:** keine neuen.

- [ ] **Step 1: Composited-Check pro Video (Overlay über echtem Frame)**

Für jedes der 5 Videos einen Frame aus der Mitte einer Highlight-Szene extrahieren und den passenden Overlay-Still darüberlegen:
```bash
mkdir -p /tmp/st-check
# Beispiel Pflegefachkraft, Highlight bei ~3s → Videoframe 75 (25fps)
ffmpeg -y -i "Video inputs/Seniorenstiftung/Pflegefachkraft.mp4" -vf "select=eq(n\,75)" -vframes 1 /tmp/st-check/pf-bg-075.png -loglevel error
ffmpeg -y -i /tmp/st-check/pf-bg-075.png -i out/seniorenstiftung/stills/pf-075.png -filter_complex overlay /tmp/st-check/pf-comp-075.png -loglevel error
```
`/tmp/st-check/pf-comp-075.png` per Read-Tool ansehen: Die Pille darf das Gesicht der Person NICHT überdecken. Für alle 5 Videos an je einem repräsentativen Frame wiederholen (Frame-Nummer = Highlight-`startSec` × 25 + ~15).

- [ ] **Step 2: Korrekturen anwenden (falls nötig)**

Wenn eine Pille zu hoch sitzt (Gesicht überschneidet): in `constants.ts` `CONTENT_BOTTOM` senken (z.B. 0.42 → 0.38) ODER für die betroffene Szene `bottomRatio` explizit im `scenes.ts` setzen. Danach betroffene Stills neu rendern und Step 1 wiederholen.

- [ ] **Step 3: Delivery-Konformität sicherstellen**

Prüfen, dass in allen 5 `*Defaults` `review.showGuides: false` gesetzt ist (Grep):
```bash
grep -rn "showGuides" src/clients/seniorenstiftung/projects/
```
Expected: jede Composition zeigt `showGuides: false`. → Review-Overlay erscheint nie im Export.

- [ ] **Step 4: Final-Typecheck**

Run: `npx tsc --noEmit`
Expected: keine Fehler.

- [ ] **Step 5: Studio-Sichtprüfung (optional, empfohlen)**

`npm run studio` starten, im Folder "Seniorenstiftung" alle 5 Kompositionen scrubben: Einblendungen erscheinen/verschwinden sauber, Timing passt zum (separat abgespielten) Footage, keine Überlappungen, CTA am Ende vollständig sichtbar.

---

## Self-Review (Plan vs. Spec)

**Spec-Coverage:**
- Neuer Client + 5 Projekte → Tasks 1–8. ✓
- Transparent ProRes 4444 → Render-Skripte je Task + Global Constraints. ✓
- Clean Teal #0E7EBE → `constants.ts` (Task 1). ✓
- HighlightPop / ChipRow / CTASlide / Logo / SceneRenderer → Tasks 2–4. ✓
- Claim „Geborgen in guten Händen" → `CTASlide` (Task 3). ✓
- Content & Timing je Video → `scenes.ts` in Tasks 4–8 (aus SRT). ✓
- Face-/Safe-Zone-Konformität (CLAUDE.md) → `SceneRenderer` ReviewOverlay + Task 9 Scrub. ✓
- fps/Dauer per ffprobe fixiert → Global Constraints (25fps + exakte Dauern). ✓
- Font Mulish → Global Constraints + jede Komponente. ✓

**Placeholder-Scan:** Keine TBD/TODO; jeder Code-Step enthält vollständigen Code. ✓

**Typ-Konsistenz:** `Scene`-Union in `SceneRenderer.tsx` definiert, in allen `scenes.ts` via `import type { Scene }` konsumiert; Feldnamen (`kind`, `startSec`, `durationSec`, `text`, `emphasis`, `chips`, `staggerFrames`, `bottomRatio`, `headline`, `sub`, `anchorY`) sind über Komponenten-Props und Scene-Union identisch. Komponenten-Namen/Exports stimmen zwischen `index.ts`, `Composition.tsx` und `Root.tsx` überein. ✓

**Bekannte Verifikations-Abhängigkeit:** `ReviewOverlay`-Prop-Signatur in Task 4 gegen `src/components/layout/ReviewOverlay.tsx` prüfen (Muster wie Sauber-Entsorgen-Reel-1). Dokumentiert.
