// ============================================================
// Top Fotografie — Keine Fotos / Momente festhalten
// Transparent overlay (ProRes 4444 with Alpha)
// 9:16 portrait (1080×1920), 30fps, 10s
// Word swap: "FOTOS" → strikethrough → "MOMENTE" at same position
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  useVideoConfig,
  useCurrentFrame,
  spring,
  interpolate,
} from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/OpenSans";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { WORD_1, WORD_2, TIMINGS } from "./transcript";
import brandJson from "../../brand.json";

loadFont();
const ci = loadBrand("top-fotografie", brandJson as any);

const WHITE = "#FFFFFF";
const PRIMARY = "#104697";

const EXIT_SPRING = { damping: 12, stiffness: 160, mass: 1 };
const EXIT_LEAD = 15;

// --- Schemas ---

const timingsSchema = z.object({
  word1StartSec: z.number().step(0.1).describe("Wort 1 Start (Sek)"),
  swapSec: z.number().step(0.1).describe("Swap-Zeitpunkt (Sek)"),
  word2StartSec: z.number().step(0.1).describe("Wort 2 Start (Sek)"),
  totalDurationSec: z.number().step(0.1).describe("Gesamtdauer (Sek)"),
});

export const keineFotosSchema = projectPropsSchema.extend({
  word1: z.string().describe("Wort 1 (wird ersetzt)"),
  word2: z.string().describe("Wort 2 (Ersetzung)"),
  timings: timingsSchema.describe("Timings"),
});

export type KeineFotosProps = z.infer<typeof keineFotosSchema>;

export const keineFotosDefaults: KeineFotosProps = {
  format: "portrait" as const,
  fps: 30 as const,
  durationInSeconds: TIMINGS.totalDurationSec,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  word1: WORD_1,
  word2: WORD_2,
  timings: { ...TIMINGS },
};

// =============================================================
// Word Swap Component
// =============================================================

const FONT_SIZE = 96;

const WordSwap: React.FC<{
  word1: string;
  word2: string;
  timings: typeof TIMINGS;
}> = ({ word1, word2, timings }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);

  // --- Exit ---
  const exitFrame = durationInFrames - EXIT_LEAD;
  const exitProgress =
    frame >= exitFrame
      ? spring({ frame: frame - exitFrame, fps, config: EXIT_SPRING })
      : 0;
  const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);
  const exitScale = interpolate(exitProgress, [0, 1], [1, 0.9]);

  // --- Word 1: scale in ---
  const w1Frame = s(timings.word1StartSec);
  const w1Local = frame - w1Frame;
  const w1Entrance =
    frame >= w1Frame
      ? spring({
          frame: w1Local,
          fps,
          config: { damping: 10, stiffness: 160, mass: 1 },
        })
      : 0;
  const w1Scale = interpolate(w1Entrance, [0, 1], [0.6, 1]);
  const w1Opacity = interpolate(w1Local, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- Swap: strikethrough + word1 out ---
  const swapFrame = s(timings.swapSec);
  const swapLocal = frame - swapFrame;

  // Strikethrough line — 25% slower
  const strikeStarted = frame >= swapFrame;
  const strikeProgress = strikeStarted
    ? spring({
        frame: swapLocal,
        fps,
        config: { damping: 22, stiffness: 140, mass: 1.2, overshootClamping: true },
      })
    : 0;
  const strikeWidth = interpolate(strikeProgress, [0, 1], [0, 110]);

  // Word 1 fades out after strike
  const w1FadeOut =
    frame >= swapFrame
      ? interpolate(swapLocal, [6, 14], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 1;

  // Strike line fades out too
  const strikeFadeOut =
    frame >= swapFrame
      ? interpolate(swapLocal, [8, 16], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 1;

  // --- Word 2: appears at same position ---
  const w2Frame = s(timings.word2StartSec);
  const w2Local = frame - w2Frame;
  const w2Entrance =
    frame >= w2Frame
      ? spring({
          frame: w2Local,
          fps,
          config: { damping: 12, stiffness: 140, mass: 1 },
        })
      : 0;
  const w2Scale = interpolate(w2Entrance, [0, 1], [0.7, 1]);
  const w2Opacity = interpolate(w2Local, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        opacity: exitOpacity,
        transform: `scale(${exitScale})`,
      }}
    >
      {/* Word 1 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          opacity: w1Opacity * w1FadeOut,
          transform: `scale(${w1Scale})`,
        }}
      >
        <div style={{ position: "relative" }}>
          <div
            style={{
              fontFamily: "Open Sans",
              fontWeight: 800,
              fontSize: FONT_SIZE,
              color: WHITE,
              textAlign: "center",
              textTransform: "uppercase",
              letterSpacing: 6,
              textShadow: "0 4px 30px rgba(0,0,0,0.7)",
            }}
          >
            {word1}
          </div>

          {/* Diagonal strikethrough — thick, bright red, hidden until swap */}
          {strikeStarted && (
          <svg
            style={{
              position: "absolute",
              top: "-10%",
              left: "-8%",
              width: "116%",
              height: "120%",
              opacity: strikeFadeOut,
              overflow: "visible",
            }}
          >
            <line
              x1="0%"
              y1="85%"
              x2={`${strikeWidth}%`}
              y2={`${85 - strikeWidth * 0.6}%`}
              stroke="#FF0000"
              strokeWidth={10}
              strokeLinecap="round"
              filter="drop-shadow(0 0 12px rgba(255, 0, 0, 0.7))"
            />
          </svg>
          )}
        </div>
      </div>

      {/* Word 2 — exact same centering */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          opacity: w2Opacity,
          transform: `scale(${w2Scale})`,
        }}
      >
        <div
          style={{
            fontFamily: "Open Sans",
            fontWeight: 800,
            fontSize: FONT_SIZE,
            color: WHITE,
            textAlign: "center",
            textTransform: "uppercase",
            letterSpacing: 6,
            textShadow: `0 4px 30px rgba(0,0,0,0.7), 0 0 40px rgba(16, 70, 151, 0.4)`,
          }}
        >
          {word2}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// Composition
// =============================================================

export const TopFotografieKeineFotos: React.FC<KeineFotosProps> = ({
  review,
  word1,
  word2,
  timings,
}) => {
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        <WordSwap word1={word1} word2={word2} timings={timings} />

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
    </CIProvider>
  );
};
