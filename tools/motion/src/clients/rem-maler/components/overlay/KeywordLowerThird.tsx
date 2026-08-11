// ============================================================
// REM Overlay — KeywordLowerThird
// Weiße Karte im unteren Drittel: rotes Icon-Badge (kantig) +
// Keyword mit Clip-Reveal + roter Akzent-Unterstrich.
// Sitzt unterhalb der Face Zone, lesbar über jedem Footage.
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
  RED,
  RED_LIGHT,
  GREEN,
  GREEN_LIGHT,
  INK,
  WHITE,
  SAFE,
  RADIUS,
  BADGE_RADIUS,
  PUNCH_SPRING,
  SMOOTH_SPRING,
} from "./constants";
import { useExit } from "./useExit";
import { RemIcon, type RemIconName } from "./RemIcons";

const { fontFamily } = loadFont();

export type Align = "left" | "center";
export type CueTone = "default" | "pos" | "neg";

interface KeywordLowerThirdProps {
  word: string;
  icon: RemIconName;
  /** Kundenwunsch: "pos" = Grün, "neg"/"default" = REM-Rot */
  tone?: CueTone;
  align?: Align;
  /** X offset in pixels */
  offsetX?: number;
  /** Y offset in pixels (positive = lower) */
  offsetY?: number;
  /** Distance from bottom as fraction of height (default: 0.09) */
  bottomRatio?: number;
  /** Max card width as fraction of width (default: 0.43 left / 0.86 center) */
  maxWidthRatio?: number;
  /** Font size as fraction of height (default: 0.05) */
  fontSizeRatio?: number;
}

export const KeywordLowerThird: React.FC<KeywordLowerThirdProps> = ({
  word,
  icon,
  tone = "default",
  align = "left",
  offsetX = 0,
  offsetY = 0,
  bottomRatio = 0.09,
  maxWidthRatio,
  fontSizeRatio = 0.05,
}) => {
  const accent = tone === "pos" ? GREEN : RED;
  const accentLight = tone === "pos" ? GREEN_LIGHT : RED_LIGHT;
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  // --- Auto-scale the whole card to fit the content zone ---
  const baseFontSize = Math.round(height * fontSizeRatio);
  const maxWidth = width * (maxWidthRatio ?? (align === "center" ? 0.82 : 0.43));
  const estCharW = baseFontSize * 0.66;
  const estFixed = baseFontSize * 3.2;
  const estTotal = word.length * estCharW + estFixed;
  const scaleFactor = estTotal > maxWidth ? maxWidth / estTotal : 1;
  const fontSize = Math.round(baseFontSize * scaleFactor);
  const badgeSize = Math.round(fontSize * 1.7);
  const pad = Math.round(fontSize * 0.55);
  const gap = Math.round(fontSize * 0.55);
  const underlineHeight = Math.max(5, Math.round(fontSize * 0.08));

  // --- Card entrance: spring up + fade ---
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
            backgroundColor: "rgba(255,255,255,0.95)",
            borderRadius: RADIUS,
            borderLeft: `${Math.max(5, Math.round(fontSize * 0.12))}px solid ${accent}`,
            boxShadow:
              "0 18px 50px rgba(26,26,46,0.30), 0 4px 14px rgba(26,26,46,0.18)",
            backdropFilter: "blur(6px)",
            WebkitBackdropFilter: "blur(6px)",
          }}
        >
          {/* Icon badge — kantig, REM-Rot */}
          <div
            style={{
              width: badgeSize,
              height: badgeSize,
              borderRadius: BADGE_RADIUS,
              backgroundColor: accent,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              transform: `scale(${badgeScale})`,
              boxShadow: `0 6px 18px ${accent}66`,
            }}
          >
            <RemIcon
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
                background: `linear-gradient(90deg, ${accent}, ${accentLight})`,
                borderRadius: 2,
                boxShadow: `0 0 16px ${accentLight}88`,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
