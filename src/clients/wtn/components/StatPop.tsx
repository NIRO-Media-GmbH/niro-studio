// ============================================================
// WTN — StatPop (word-synced, brand look)
// A punchy stat on a dark navy card: an optional light prefix line
// ("über"), a big LIME number that counts up, a slanted lime signet
// bar, and an off-white label. The card size is LOCKED for the final
// value (fixed number width + tabular figures) so the box never jumps
// while the counter rolls — critical when a face is behind it.
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
  CARD_BG,
  CARD_SHADOW,
} from "./constants";
import { useExit } from "./useExit";

interface StatPopProps {
  value: number;
  prefix?: string;
  suffix?: string;
  label: string;
  emphasisDelayFrames?: number;
  bottomRatio?: number;
}

export const StatPop: React.FC<StatPopProps> = ({
  value,
  prefix = "",
  suffix = "",
  label,
  emphasisDelayFrames,
  bottomRatio = CONTENT_BOTTOM,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const numSize = Math.round(height * 0.092);
  const preSize = Math.round(numSize * 0.42);
  const labelSize = Math.round(height * 0.03);
  const padV = Math.round(numSize * 0.34);
  const padH = Math.round(numSize * 0.62);
  const bottomPx = Math.round(height * bottomRatio);
  const barH = Math.max(6, Math.round(numSize * 0.1));

  // Lock the number line to the FINAL value's width so the box never
  // resizes while counting (tabular figures keep digits equal-width).
  const numberWidth = Math.ceil(
    measureText({
      text: `${value}${suffix}`,
      fontFamily: FONT,
      fontSize: numSize,
      fontWeight: 900,
      letterSpacing: `${-Math.round(numSize * 0.02)}px`,
    }).width,
  );

  const enter = spring({ frame, fps, config: PUNCH_SPRING });
  const opacity = interpolate(enter, [0, 0.45], [0, 1], {
    extrapolateRight: "clamp",
  });
  const y = interpolate(enter, [0, 1], [40, 0]);

  const landFrame = emphasisDelayFrames ?? Math.round(fps * 0.9);
  const count = Math.round(
    interpolate(frame, [2, Math.max(3, landFrame)], [0, value], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }),
  );

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottomPx,
        left: "50%",
        transform: `translateX(-50%) translateY(${y - exitSlide}px)`,
        opacity: opacity * exitOpacity,
      }}
    >
      <div
        style={{
          padding: `${padV}px ${padH}px`,
          backgroundColor: CARD_BG,
          borderRadius: Math.round(numSize * 0.24),
          boxShadow: CARD_SHADOW,
          backdropFilter: "blur(4px)",
          WebkitBackdropFilter: "blur(4px)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {prefix ? (
          <div
            style={{
              fontFamily: FONT,
              fontSize: preSize,
              fontWeight: 500,
              lineHeight: 1,
              color: LIME,
              marginBottom: Math.round(numSize * 0.04),
            }}
          >
            {prefix.trim()}
          </div>
        ) : null}
        <div
          style={{
            width: numberWidth,
            fontFamily: FONT,
            fontSize: numSize,
            fontWeight: 900,
            lineHeight: 1,
            letterSpacing: -Math.round(numSize * 0.02),
            color: LIME,
            textAlign: "center",
            fontVariantNumeric: "tabular-nums",
            fontFeatureSettings: '"tnum"',
          }}
        >
          {count}
          {suffix}
        </div>
        <div
          style={{
            marginTop: Math.round(numSize * 0.14),
            height: barH,
            width: "58%",
            transform: `skewX(${SIGNET_SKEW}deg)`,
            background: `linear-gradient(90deg, ${LIME_DEEP}, ${LIME})`,
            borderRadius: 2,
          }}
        />
        <div
          style={{
            marginTop: Math.round(numSize * 0.16),
            fontFamily: FONT,
            fontSize: labelSize,
            fontWeight: 500,
            color: OFF_WHITE,
            letterSpacing: Math.round(labelSize * 0.04),
            textAlign: "center",
          }}
        >
          {label}
        </div>
      </div>
    </div>
  );
};
