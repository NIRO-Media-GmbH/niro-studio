// ============================================================
// Seniorenstiftung — ChipRow (v2, word-synced)
// A centered, wrapping row of frosted chips (teal icon badge +
// label). Each chip pops on its own spoken-word frame via
// delayFrames — no uniform stagger.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Mulish";
import { TEAL, INK, CONTENT_BOTTOM, WARM_SPRING } from "./constants";
import { useExit } from "./useExit";
import { ChipIcon, type ChipIconName } from "./Icons";

const { fontFamily } = loadFont();

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
  const padH = Math.round(fontSize * 0.8);
  const badge = Math.round(fontSize * 1.15);
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
          config: WARM_SPRING,
        });
        const opacity = interpolate(p, [0, 0.45], [0, 1], {
          extrapolateRight: "clamp",
        });
        const scale = interpolate(p, [0, 1], [0.72, 1]);
        const y = interpolate(p, [0, 1], [20, 0]);
        return (
          <div
            key={i}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: Math.round(fontSize * 0.42),
              padding: `${padV}px ${padH}px ${padV}px ${Math.round(padH * 0.7)}px`,
              backgroundColor: "rgba(255,255,255,0.94)",
              borderRadius: 999,
              boxShadow: "0 12px 30px rgba(14,60,90,0.22)",
              backdropFilter: "blur(6px)",
              WebkitBackdropFilter: "blur(6px)",
              opacity,
              transform: `translateY(${y}px) scale(${scale})`,
            }}
          >
            <div
              style={{
                width: badge,
                height: badge,
                borderRadius: "50%",
                backgroundColor: TEAL,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                boxShadow: `0 4px 12px ${TEAL}55`,
              }}
            >
              {chip.icon ? (
                <ChipIcon
                  name={chip.icon}
                  size={Math.round(badge * 0.62)}
                  color="#FFFFFF"
                  strokeWidth={2.1}
                />
              ) : (
                <div
                  style={{
                    width: Math.round(badge * 0.32),
                    height: Math.round(badge * 0.32),
                    borderRadius: "50%",
                    backgroundColor: "#FFFFFF",
                  }}
                />
              )}
            </div>
            <span
              style={{
                fontFamily,
                fontSize,
                fontWeight: 800,
                color: INK,
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
