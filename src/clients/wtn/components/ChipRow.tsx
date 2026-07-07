// ============================================================
// WTN — ChipRow (word-synced, brand look)
// Centered, wrapping row of navy chips with a LIME icon badge +
// off-white label. Each chip pops on its own spoken-word frame via
// delayFrames, entering with a tiny signet lean that settles upright.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { FONT } from "./fonts";
import {
  LIME,
  OFF_BLACK,
  OFF_WHITE,
  CONTENT_BOTTOM,
  PUNCH_SPRING,
  CARD_BG,
  CARD_SHADOW,
} from "./constants";
import { useExit } from "./useExit";
import { ChipIcon, type ChipIconName } from "./Icons";

export interface ChipSpec {
  label: string;
  /** Frame (relative to scene start) at which this chip pops in. */
  delayFrames: number;
  icon?: ChipIconName;
}

interface ChipRowProps {
  chips: ChipSpec[];
  bottomRatio?: number;
  /** Font size as fraction of height. Default 0.03. */
  fontSizeRatio?: number;
}

export const ChipRow: React.FC<ChipRowProps> = ({
  chips,
  bottomRatio = CONTENT_BOTTOM,
  fontSizeRatio = 0.03,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const fontSize = Math.round(height * fontSizeRatio);
  const padV = Math.round(fontSize * 0.5);
  const padH = Math.round(fontSize * 0.85);
  const badge = Math.round(fontSize * 1.2);
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
        alignItems: "center",
      }}
    >
      {chips.map((chip, i) => {
        const p = spring({
          frame: frame - chip.delayFrames,
          fps,
          config: PUNCH_SPRING,
        });
        const opacity = interpolate(p, [0, 0.4], [0, 1], {
          extrapolateRight: "clamp",
        });
        const scale = interpolate(p, [0, 1], [0.66, 1]);
        const y = interpolate(p, [0, 1], [24, 0]);
        const skew = interpolate(p, [0, 1], [-8, 0]);
        return (
          <div
            key={i}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: Math.round(fontSize * 0.44),
              padding: `${padV}px ${padH}px ${padV}px ${Math.round(padH * 0.6)}px`,
              backgroundColor: CARD_BG,
              borderRadius: 999,
              boxShadow: CARD_SHADOW,
              backdropFilter: "blur(4px)",
              WebkitBackdropFilter: "blur(4px)",
              opacity,
              transform: `translateY(${y}px) scale(${scale}) skewX(${skew}deg)`,
            }}
          >
            <div
              style={{
                width: badge,
                height: badge,
                borderRadius: "50%",
                backgroundColor: LIME,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                boxShadow: `0 4px 12px ${LIME}66`,
              }}
            >
              {chip.icon ? (
                <ChipIcon
                  name={chip.icon}
                  size={Math.round(badge * 0.62)}
                  color={OFF_BLACK}
                  strokeWidth={2.2}
                />
              ) : (
                <div
                  style={{
                    width: Math.round(badge * 0.32),
                    height: Math.round(badge * 0.32),
                    borderRadius: "50%",
                    backgroundColor: OFF_BLACK,
                  }}
                />
              )}
            </div>
            <span
              style={{
                fontFamily: FONT,
                fontSize,
                fontWeight: 700,
                color: OFF_WHITE,
                whiteSpace: "nowrap",
              }}
            >
              {chip.label}
            </span>
          </div>
        );
      })}
    </div>
  );
};
