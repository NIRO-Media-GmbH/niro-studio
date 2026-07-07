// ============================================================
// Sauber Entsorgen — KeywordLowerThird
// White frosted pill in the lower third: blue icon badge +
// keyword with clip-path reveal + animated blue accent underline.
// Sits below the face zone, legible over any footage.
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
import {
  BLUE,
  BLUE_LIGHT,
  INK,
  WHITE,
  SAFE,
  PUNCH_SPRING,
  SMOOTH_SPRING,
} from "./constants";
import { useExit } from "./useExit";
import { ServiceIcon, type ServiceIconName } from "./ServiceIcons";

const { fontFamily } = loadFont();

export type Align = "left" | "center";

interface KeywordLowerThirdProps {
  word: string;
  icon: ServiceIconName;
  align?: Align;
  /** X offset in pixels */
  offsetX?: number;
  /** Y offset in pixels (positive = lower) */
  offsetY?: number;
  /** Distance from bottom as fraction of height (default: 0.09) */
  bottomRatio?: number;
  /** Max pill width as fraction of width (default: 0.43 left / 0.86 center) */
  maxWidthRatio?: number;
  /** Font size as fraction of height (default: 0.05) */
  fontSizeRatio?: number;
}

export const KeywordLowerThird: React.FC<KeywordLowerThirdProps> = ({
  word,
  icon,
  align = "left",
  offsetX = 0,
  offsetY = 0,
  bottomRatio = 0.09,
  maxWidthRatio,
  fontSizeRatio = 0.05,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  // --- Auto-scale the whole pill to fit the LEFT content zone ---
  // (GF sits on the right — keep everything clear of the right half.)
  const baseFontSize = Math.round(height * fontSizeRatio);
  const maxWidth = width * (maxWidthRatio ?? (align === "center" ? 0.82 : 0.43));
  const estCharW = baseFontSize * 0.66; // conservative for bold Inter + letter-spacing
  const estFixed = baseFontSize * 3.2; // badge + gaps + horizontal padding
  const estTotal = word.length * estCharW + estFixed;
  const scaleFactor = estTotal > maxWidth ? maxWidth / estTotal : 1;
  const fontSize = Math.round(baseFontSize * scaleFactor);
  const badgeSize = Math.round(fontSize * 1.7);
  const pad = Math.round(fontSize * 0.55);
  const gap = Math.round(fontSize * 0.55);
  const underlineHeight = Math.max(5, Math.round(fontSize * 0.07));

  // --- Pill entrance: spring up + fade ---
  const enter = spring({ frame, fps, config: PUNCH_SPRING });
  const enterY = interpolate(enter, [0, 1], [46, 0]);
  const enterOpacity = interpolate(enter, [0, 0.4], [0, 1], {
    extrapolateRight: "clamp",
  });

  // --- Icon badge pop (slightly delayed) ---
  const badgePop = spring({ frame: frame - 2, fps, config: PUNCH_SPRING });
  const badgeScale = interpolate(badgePop, [0, 1], [0.4, 1]);

  // --- Keyword clip-path reveal from left ---
  const revealFrames = Math.min(
    Math.floor(durationInFrames * 0.35),
    Math.floor(fps * 0.7),
  );
  const revealPct = interpolate(frame - 4, [0, revealFrames], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // --- Accent underline grows after the reveal completes ---
  const underlineProg = spring({
    frame: frame - 4 - revealFrames,
    fps,
    config: SMOOTH_SPRING,
  });

  const bottomPx = Math.round(height * bottomRatio) - offsetY;

  const positionStyle: React.CSSProperties =
    align === "center"
      ? { left: "50%", transform: "translateX(-50%)" }
      : { left: Math.round(width * SAFE.left) + offsetX };

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottomPx,
        ...positionStyle,
        opacity: enterOpacity * exitOpacity,
      }}
    >
      <div
        style={{
          transform: `translateY(${enterY - exitSlide}px)`,
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap,
            padding: `${pad}px ${Math.round(pad * 1.3)}px`,
            backgroundColor: "rgba(255,255,255,0.94)",
            borderRadius: Math.round(badgeSize * 0.5 + pad),
            boxShadow:
              "0 18px 50px rgba(20,30,55,0.30), 0 4px 14px rgba(20,30,55,0.18)",
            backdropFilter: "blur(6px)",
            WebkitBackdropFilter: "blur(6px)",
          }}
        >
          {/* Icon badge */}
          <div
            style={{
              width: badgeSize,
              height: badgeSize,
              borderRadius: "50%",
              backgroundColor: BLUE,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              transform: `scale(${badgeScale})`,
              boxShadow: `0 6px 18px ${BLUE}66`,
            }}
          >
            <ServiceIcon
              name={icon}
              size={Math.round(badgeSize * 0.58)}
              color={WHITE}
              strokeWidth={2.1}
            />
          </div>

          {/* Keyword + underline */}
          <div style={{ paddingRight: Math.round(pad * 0.3) }}>
            <div
              style={{
                clipPath: `inset(0 ${100 - revealPct}% 0 0)`,
                fontFamily,
                fontSize,
                fontWeight: 800,
                color: INK,
                letterSpacing: -Math.round(fontSize * 0.01),
                lineHeight: 1.3,
                paddingBottom: Math.round(fontSize * 0.1),
                whiteSpace: "nowrap",
              }}
            >
              {word}
            </div>
            <div
              style={{
                marginTop: Math.round(fontSize * 0.04),
                height: underlineHeight,
                width: `${underlineProg * 100}%`,
                background: `linear-gradient(90deg, ${BLUE}, ${BLUE_LIGHT})`,
                borderRadius: underlineHeight,
                boxShadow: `0 0 16px ${BLUE_LIGHT}88`,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
