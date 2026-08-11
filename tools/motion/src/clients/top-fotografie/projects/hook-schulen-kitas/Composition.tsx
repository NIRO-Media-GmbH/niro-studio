// ============================================================
// Top Fotografie — Hook "Schulen & Kitas?"
// Transparent overlay (ProRes 4444 with Alpha)
// 9:16 portrait (1080×1920), 30fps, 5s
// Punchy staggered word reveal for video hook
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
import brandJson from "../../brand.json";

loadFont();
const ci = loadBrand("top-fotografie", brandJson as any);

const PRIMARY = "#104697";
const WHITE = "#FFFFFF";

const PUNCH = { damping: 9, stiffness: 200, mass: 1 };
const BOUNCE = { damping: 7, stiffness: 180, mass: 1 };
const SMOOTH = { damping: 14, stiffness: 120, mass: 1 };

const EXIT_LEAD = 15;

// --- Schema ---

export const hookSchulenKitasSchema = projectPropsSchema.extend({
  word1: z.string().describe("Wort 1"),
  word2: z.string().describe("Wort 2"),
  ampersand: z.string().describe("Verbindungszeichen"),
  punctuation: z.string().describe("Satzzeichen"),
});

export type HookSchulenKitasProps = z.infer<typeof hookSchulenKitasSchema>;

export const hookSchulenKitasDefaults: HookSchulenKitasProps = {
  format: "portrait" as const,
  fps: 30 as const,
  durationInSeconds: 5,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  word1: "SCHULEN",
  word2: "KITAS",
  ampersand: "&",
  punctuation: "?",
};

// =============================================================
// Component
// =============================================================

export const TopHookSchulenKitas: React.FC<HookSchulenKitasProps> = ({
  review,
  word1,
  word2,
  ampersand,
  punctuation,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // --- Exit ---
  const exitFrame = durationInFrames - EXIT_LEAD;
  const exitProgress =
    frame >= exitFrame
      ? spring({ frame: frame - exitFrame, fps, config: { damping: 12, stiffness: 160, mass: 1 } })
      : 0;
  const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);
  const exitScale = interpolate(exitProgress, [0, 1], [1, 0.92]);

  // --- Word 1 (SCHULEN) — slides from left ---
  const w1Delay = 0;
  const w1Progress = spring({
    frame: frame - w1Delay,
    fps,
    config: PUNCH,
  });
  const w1Opacity = interpolate(frame, [w1Delay, w1Delay + 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const w1SlideX = Math.round(interpolate(w1Progress, [0, 1], [-120, 0]));
  const w1Scale = interpolate(w1Progress, [0, 1], [0.7, 1]);

  // --- Ampersand (&) — scales in with rotation ---
  const ampDelay = 8;
  const ampProgress = spring({
    frame: frame - ampDelay,
    fps,
    config: BOUNCE,
  });
  const ampOpacity = interpolate(frame, [ampDelay, ampDelay + 5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const ampScale = interpolate(ampProgress, [0, 1], [0, 1]);
  const ampRotate = interpolate(ampProgress, [0, 1], [-90, 0]);

  // --- Word 2 (KITAS) — slides from right ---
  const w2Delay = 16;
  const w2Progress = spring({
    frame: frame - w2Delay,
    fps,
    config: PUNCH,
  });
  const w2Opacity = interpolate(frame, [w2Delay, w2Delay + 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const w2SlideX = Math.round(interpolate(w2Progress, [0, 1], [120, 0]));
  const w2Scale = interpolate(w2Progress, [0, 1], [0.7, 1]);

  // --- Punctuation (?) — bounces in last ---
  const pDelay = 24;
  const pProgress = spring({
    frame: frame - pDelay,
    fps,
    config: BOUNCE,
  });
  const pOpacity = interpolate(frame, [pDelay, pDelay + 4], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const pScale = interpolate(pProgress, [0, 1], [0, 1]);

  // --- Subtle emphasis shake after everything is in (one quick shake) ---
  const shakeFrame = 32;
  const shakeProgress = frame >= shakeFrame && frame < shakeFrame + 8
    ? (frame - shakeFrame) / 8
    : 0;
  const shake = shakeProgress > 0 && shakeProgress < 1
    ? Math.sin(shakeProgress * Math.PI * 3) * 4 * (1 - shakeProgress)
    : 0;

  const FONT_SIZE = 130;

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          opacity: exitOpacity,
          transform: `scale(${exitScale}) translateY(${shake}px)`,
        }}
      >
        {/* Two-line stacked layout for 9:16 */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 20,
          }}
        >
          {/* Line 1: SCHULEN */}
          <div
            style={{
              fontFamily: "Open Sans",
              fontWeight: 900,
              fontSize: FONT_SIZE,
              color: WHITE,
              textTransform: "uppercase",
              letterSpacing: 2,
              lineHeight: 1,
              textShadow:
                "0 6px 32px rgba(0,0,0,0.6), 0 0 12px rgba(16, 70, 151, 0.4)",
              opacity: w1Opacity,
              transform: `translateX(${w1SlideX}px) scale(${w1Scale})`,
            }}
          >
            {word1}
          </div>

          {/* Line 2: & KITAS? */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 24,
            }}
          >
            {/* & */}
            <div
              style={{
                fontFamily: "Open Sans",
                fontWeight: 900,
                fontStyle: "italic",
                fontSize: FONT_SIZE * 1.05,
                color: PRIMARY,
                lineHeight: 1,
                textShadow: "0 4px 20px rgba(0,0,0,0.3)",
                opacity: ampOpacity,
                transform: `scale(${ampScale}) rotate(${ampRotate}deg)`,
                WebkitTextStroke: `3px ${WHITE}`,
              }}
            >
              {ampersand}
            </div>

            {/* KITAS */}
            <div
              style={{
                fontFamily: "Open Sans",
                fontWeight: 900,
                fontSize: FONT_SIZE,
                color: WHITE,
                textTransform: "uppercase",
                letterSpacing: 2,
                lineHeight: 1,
                textShadow:
                  "0 6px 32px rgba(0,0,0,0.6), 0 0 12px rgba(16, 70, 151, 0.4)",
                opacity: w2Opacity,
                transform: `translateX(${w2SlideX}px) scale(${w2Scale})`,
              }}
            >
              {word2}
            </div>

            {/* ? */}
            <div
              style={{
                fontFamily: "Open Sans",
                fontWeight: 900,
                fontSize: FONT_SIZE * 1.1,
                color: PRIMARY,
                lineHeight: 1,
                textShadow: "0 4px 20px rgba(0,0,0,0.3)",
                opacity: pOpacity,
                transform: `scale(${pScale})`,
                WebkitTextStroke: `3px ${WHITE}`,
              }}
            >
              {punctuation}
            </div>
          </div>
        </div>

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
