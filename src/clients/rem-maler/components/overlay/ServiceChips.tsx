// ============================================================
// REM Overlay — ServiceChips
// Eine Reihe kantiger Chips (Icon + Label), die gestaffelt
// einspringen. Links verankert (Sprecher rechts).
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { RED, INK, SAFE, RADIUS, PUNCH_SPRING } from "./constants";
import { useExit } from "./useExit";
import { RemIcon, type RemIconName } from "./RemIcons";

const { fontFamily } = loadFont();

export interface ChipItem {
  label: string;
  icon: RemIconName;
}

interface ServiceChipsProps {
  chips: ChipItem[];
  /** Horizontal anchor (default: left) */
  align?: "left" | "center";
  /** X offset in pixels */
  offsetX?: number;
  /** Y offset in pixels (positive = lower) */
  offsetY?: number;
  /** Distance from bottom as fraction of height (default: 0.1) */
  bottomRatio?: number;
  /** Font size as fraction of height (default: 0.034) */
  fontSizeRatio?: number;
  /** Frames between each chip's entrance */
  staggerFrames?: number;
}

export const ServiceChips: React.FC<ServiceChipsProps> = ({
  chips,
  align = "left",
  offsetX = 0,
  offsetY = 0,
  bottomRatio = 0.1,
  fontSizeRatio = 0.034,
  staggerFrames = 5,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const fontSize = Math.round(height * fontSizeRatio);
  const iconSize = Math.round(fontSize * 1.35);
  const padV = Math.round(fontSize * 0.55);
  const padH = Math.round(fontSize * 0.85);
  const gap = Math.round(fontSize * 0.9);

  const bottomPx = Math.round(height * bottomRatio) - offsetY;

  const centered = align === "center";
  const positionStyle: React.CSSProperties = centered
    ? {
        left: "50%",
        transform: `translateX(calc(-50% + ${offsetX}px))`,
        width: Math.round(width * 0.9),
        flexWrap: "wrap",
        justifyContent: "center",
        rowGap: Math.round(gap * 0.7),
      }
    : { left: Math.round(width * SAFE.left) + offsetX };

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottomPx,
        ...positionStyle,
        display: "flex",
        gap,
        opacity: exitOpacity,
      }}
    >
      {chips.map((chip, i) => {
        const enter = spring({
          frame: frame - i * staggerFrames,
          fps,
          config: PUNCH_SPRING,
        });
        const scale = interpolate(enter, [0, 1], [0.5, 1]);
        const slideY = interpolate(enter, [0, 1], [40, 0]);
        const opacity = interpolate(enter, [0, 0.45], [0, 1], {
          extrapolateRight: "clamp",
        });

        return (
          <div
            key={i}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: Math.round(fontSize * 0.45),
              padding: `${padV}px ${padH}px`,
              backgroundColor: "rgba(255,255,255,0.95)",
              borderRadius: RADIUS,
              boxShadow:
                "0 14px 38px rgba(26,26,46,0.28), 0 3px 10px rgba(26,26,46,0.16)",
              opacity: opacity * exitOpacity,
              transform: `translateY(${slideY + exitSlide}px) scale(${scale})`,
            }}
          >
            <span
              style={{
                color: RED,
                display: "inline-flex",
                alignItems: "center",
              }}
            >
              <RemIcon name={chip.icon} size={iconSize} strokeWidth={2.1} />
            </span>
            <span
              style={{
                fontFamily,
                fontSize,
                fontWeight: 700,
                color: INK,
                letterSpacing: -Math.round(fontSize * 0.01),
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
