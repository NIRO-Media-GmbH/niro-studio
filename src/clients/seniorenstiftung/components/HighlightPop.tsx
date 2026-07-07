// ============================================================
// Seniorenstiftung — HighlightPop (v2, word-synced)
// One key phrase in a white frosted pill: soft spring pop-in,
// clip-path reveal, growing teal accent underline. The optional
// `emphasis` word is teal and PULSES with a soft glow exactly on
// the frame it is spoken (emphasisDelayFrames). Auto-fits to one
// line via measureText. Sits below the face zone.
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
import { measureText } from "@remotion/layout-utils";
import {
  TEAL,
  TEAL_LIGHT,
  INK,
  CONTENT_BOTTOM,
  WARM_SPRING,
  SMOOTH_SPRING,
} from "./constants";
import { useExit } from "./useExit";

const { fontFamily } = loadFont();

interface HighlightPopProps {
  text: string;
  /** Substring of `text` rendered in teal. Must appear verbatim in text. */
  emphasis?: string;
  /** Frame (relative to scene start) at which the emphasis word is spoken.
   *  Triggers a scale pulse + glow on the emphasis span. */
  emphasisDelayFrames?: number;
  /** Distance of pill bottom from frame bottom, as fraction of height. */
  bottomRatio?: number;
  /** Font size as fraction of height. Default 0.044. */
  fontSizeRatio?: number;
}

export const HighlightPop: React.FC<HighlightPopProps> = ({
  text,
  emphasis,
  emphasisDelayFrames,
  bottomRatio = CONTENT_BOTTOM,
  fontSizeRatio = 0.044,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  // Auto-fit: measure the phrase at the base size and scale the font down
  // so it always fits one line inside the pill.
  const maxWidth = Math.round(width * 0.86);
  const baseFontSize = Math.round(height * fontSizeRatio);
  const baseLetterSpacing = -Math.round(baseFontSize * 0.01);
  const basePadH = Math.round(baseFontSize * 0.8);
  const available = maxWidth - 2 * basePadH;
  const measured = measureText({
    text,
    fontFamily,
    fontSize: baseFontSize,
    fontWeight: 800,
    letterSpacing: `${baseLetterSpacing}px`,
  });
  const scaleFactor =
    measured.width > available ? available / measured.width : 1;
  const fontSize = Math.max(
    Math.round(baseFontSize * scaleFactor),
    Math.round(baseFontSize * 0.5),
  );
  const padV = Math.round(fontSize * 0.55);
  const padH = Math.round(fontSize * 0.8);
  const underlineHeight = Math.max(5, Math.round(fontSize * 0.09));

  // Soft entrance (warm spring + longer fade-in)
  const enter = spring({ frame, fps, config: WARM_SPRING });
  const enterY = interpolate(enter, [0, 1], [36, 0]);
  const enterOpacity = interpolate(enter, [0, 0.55], [0, 1], {
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

  // Emphasis pulse, synced to the spoken word: the WHOLE pill breathes
  // gently (one smooth sine bump). Scaling the word itself clips against
  // the reveal clip-path and collides with neighboring text.
  const pulseAt = emphasisDelayFrames ?? 3 + revealFrames;
  const pulseT = interpolate(
    frame - pulseAt,
    [0, Math.round(fps * 0.56)],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const pulseScale = 1 + Math.sin(pulseT * Math.PI) * 0.035;

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
      <div
        style={{
          transform: `translateY(${enterY - exitSlide}px) scale(${pulseScale})`,
          transformOrigin: "center bottom",
        }}
      >
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
            }}
          />
        </div>
      </div>
    </div>
  );
};
