// ============================================================
// Bremsen Schneider — KeywordReveal
// Large uppercase white text with clip-path reveal from left
// and animated yellow underline
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { YELLOW, WHITE, SAFE, SMOOTH_SPRING, PUNCH_SPRING } from "./constants";
import { useExit } from "./useExit";

const { fontFamily } = loadFont();

export type OverlayPosition = "top" | "bottom" | "center";

interface KeywordRevealProps {
  word: string;
  position: OverlayPosition;
  /** Duration of clip-path reveal in seconds (default: synced to sequence) */
  revealDurationSec?: number;
  /** Y offset in pixels */
  offsetY?: number;
  /** X offset in pixels */
  offsetX?: number;
  /** Font size as fraction of height (default: 0.06) */
  fontSizeRatio?: number;
}

export const KeywordReveal: React.FC<KeywordRevealProps> = ({
  word,
  position,
  revealDurationSec,
  offsetY = 0,
  offsetX = 0,
  fontSizeRatio = 0.06,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  // Auto-scale font for long keywords to stay within safe zone
  const safeWidth = width * (SAFE.right - SAFE.left);
  const baseFontSize = Math.round(height * fontSizeRatio);
  // Approximate: each character ~0.65× font size at weight 900 + letter spacing
  const charWidth = baseFontSize * 0.65 + baseFontSize * 0.06;
  const estimatedWidth = word.length * charWidth;
  const scaleFactor = estimatedWidth > safeWidth * 0.95
    ? (safeWidth * 0.95) / estimatedWidth
    : 1;
  const fontSize = Math.round(baseFontSize * scaleFactor);
  const underlineHeight = Math.max(6, Math.round(fontSize * 0.06));

  // Clip-path reveal: 0→100% from left
  const revealFrames = revealDurationSec
    ? Math.floor(revealDurationSec * fps)
    : Math.min(Math.floor(durationInFrames * 0.4), Math.floor(fps * 0.8));

  const revealPct = interpolate(
    frame,
    [0, revealFrames],
    [0, 100],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) },
  );

  // Yellow underline: starts after reveal completes, spring animation
  const underlineDelay = revealFrames;
  const underlineProg = spring({
    frame: frame - underlineDelay,
    fps,
    config: SMOOTH_SPRING,
  });

  // Slight entrance slide from left
  const entranceSlide = spring({
    frame,
    fps,
    config: PUNCH_SPRING,
  });
  const slideX = interpolate(entranceSlide, [0, 1], [-40, 0]);

  // Position Y based on zone
  const safeTop = height * SAFE.top;
  const safeBottom = height * SAFE.bottom;
  const safeMid = (safeTop + safeBottom) / 2;

  const posY: Record<OverlayPosition, number> = {
    top: safeTop + height * 0.03,
    center: safeMid - fontSize / 2,
    bottom: safeBottom - fontSize - height * 0.05,
  };

  const y = posY[position] + offsetY;
  const x = width * SAFE.left + offsetX;

  return (
    <div
      style={{
        position: "absolute",
        top: y,
        left: x,
        opacity: exitOpacity,
        transform: `translateX(${slideX - exitSlide}px)`,
      }}
    >
      {/* Text with clip-path reveal */}
      <div
        style={{
          clipPath: `inset(0 ${100 - revealPct}% 0 0)`,
          fontFamily,
          fontSize,
          fontWeight: 900,
          color: WHITE,
          textTransform: "uppercase",
          letterSpacing: Math.round(fontSize * 0.06),
          lineHeight: 1.1,
          textShadow: "0 4px 30px rgba(0,0,0,0.5), 0 2px 8px rgba(0,0,0,0.3)",
          whiteSpace: "nowrap",
        }}
      >
        {word}
      </div>

      {/* Yellow underline */}
      <div
        style={{
          marginTop: Math.round(fontSize * 0.08),
          height: underlineHeight,
          width: `${underlineProg * 100}%`,
          backgroundColor: YELLOW,
          borderRadius: underlineHeight / 2,
          boxShadow: `0 0 20px ${YELLOW}66`,
        }}
      />
    </div>
  );
};
