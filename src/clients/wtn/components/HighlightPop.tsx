// ============================================================
// WTN — HighlightPop (word-synced, brand look) — BOXED variant
// One key phrase in a dark navy pill: punchy spring pop-in with a
// lime GLOW bloom on entrance, L→R clip reveal, and a growing SLANTED
// lime accent bar (WTN signet). Mixed Robout weights — base Medium,
// LIME emphasis in Extrabold (open counters). Auto-fits to one line.
// No mid-scene pulse. Sits below the face zone.
// (For the box-less "plain" look see HighlightPlain — a deliberately
//  different animation used for variety.)
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { measureText } from "@remotion/layout-utils";
import { FONT } from "./fonts";
import {
  LIME,
  LIME_DEEP,
  OFF_WHITE,
  CONTENT_BOTTOM,
  SIGNET_SKEW,
  PUNCH_SPRING,
  SMOOTH_SPRING,
  GLOW_LIME,
  CARD_BG,
  CARD_SHADOW,
} from "./constants";
import { useExit } from "./useExit";

interface HighlightPopProps {
  text: string;
  /** Substring of `text` rendered in lime Extrabold. Verbatim in text. */
  emphasis?: string;
  /** Distance of pill bottom from frame bottom, as fraction of height. */
  bottomRatio?: number;
  /** Font size as fraction of height. Default 0.044. */
  fontSizeRatio?: number;
}

const EMPH_WEIGHT = 800; // Extrabold — heavy but counters stay open

export const HighlightPop: React.FC<HighlightPopProps> = ({
  text,
  emphasis,
  bottomRatio = CONTENT_BOTTOM,
  fontSizeRatio = 0.044,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  // Auto-fit to one line.
  const maxWidth = Math.round(width * 0.88);
  const baseFontSize = Math.round(height * fontSizeRatio);
  const baseLetterSpacing = -Math.round(baseFontSize * 0.005);
  const basePadH = Math.round(baseFontSize * 0.85);
  const available = maxWidth - 2 * basePadH;
  const measured = measureText({
    text,
    fontFamily: FONT,
    fontSize: baseFontSize,
    fontWeight: EMPH_WEIGHT,
    letterSpacing: `${baseLetterSpacing}px`,
  });
  const scaleFactor =
    measured.width > available ? available / measured.width : 1;
  const fontSize = Math.max(
    Math.round(baseFontSize * scaleFactor),
    Math.round(baseFontSize * 0.5),
  );
  const padV = Math.round(fontSize * 0.55);
  const padH = Math.round(fontSize * 0.85);
  const barHeight = Math.max(6, Math.round(fontSize * 0.13));

  // Punchy entrance
  const enter = spring({ frame, fps, config: PUNCH_SPRING });
  const enterY = interpolate(enter, [0, 1], [40, 0]);
  const enterOpacity = interpolate(enter, [0, 0.5], [0, 1], {
    extrapolateRight: "clamp",
  });

  const revealFrames = Math.min(
    Math.floor(durationInFrames * 0.3),
    Math.floor(fps * 0.5),
  );
  const revealPct = interpolate(frame - 2, [0, revealFrames], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const barProg = spring({
    frame: frame - 2 - revealFrames,
    fps,
    config: SMOOTH_SPRING,
  });

  // Lime glow blooms during the ENTRANCE, then fades. No mid pulse.
  const glow = interpolate(
    frame,
    [0, Math.round(fps * 0.3), Math.round(fps * 0.9)],
    [0, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const bottomPx = Math.round(height * bottomRatio);

  let parts: React.ReactNode = text;
  if (emphasis && text.includes(emphasis)) {
    const i = text.indexOf(emphasis);
    parts = (
      <>
        {text.slice(0, i)}
        <span style={{ color: LIME, fontWeight: EMPH_WEIGHT }}>{emphasis}</span>
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
      <div
        style={{
          transform: `translateY(${enterY - exitSlide}px)`,
          transformOrigin: "center bottom",
        }}
      >
        <div
          style={{
            maxWidth,
            padding: `${padV}px ${padH}px`,
            backgroundColor: CARD_BG,
            borderRadius: Math.round(fontSize * 0.34),
            boxShadow: `${CARD_SHADOW}${
              glow > 0.01 ? `, 0 0 ${Math.round(40 * glow)}px ${GLOW_LIME}` : ""
            }`,
            backdropFilter: "blur(4px)",
            WebkitBackdropFilter: "blur(4px)",
          }}
        >
          <div
            style={{
              // Descenders need room: clip-path bottom sits at the padded
              // box edge, so pad below + roomy line-height.
              clipPath: `inset(0 ${100 - revealPct}% 0 0)`,
              paddingBottom: Math.round(fontSize * 0.16),
              fontFamily: FONT,
              fontSize,
              fontWeight: 500,
              color: OFF_WHITE,
              lineHeight: 1.34,
              letterSpacing: -Math.round(fontSize * 0.005),
              textAlign: "center",
              whiteSpace: "nowrap",
            }}
          >
            {parts}
          </div>
          {/* Slanted lime accent bar — echoes the WTN signet lean */}
          <div
            style={{
              marginTop: Math.round(fontSize * 0.06),
              marginInline: "auto",
              height: barHeight,
              width: `${barProg * 64}%`,
              maxWidth: "64%",
              transform: `skewX(${SIGNET_SKEW}deg)`,
              background: `linear-gradient(90deg, ${LIME_DEEP}, ${LIME})`,
              borderRadius: 2,
            }}
          />
        </div>
      </div>
    </div>
  );
};
