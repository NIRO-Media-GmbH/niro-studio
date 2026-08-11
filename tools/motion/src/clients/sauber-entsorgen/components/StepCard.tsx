// ============================================================
// Sauber Entsorgen — StepCard
// Numbered process step card (big number + icon + title + sub).
// Left-anchored, clears the GF on the right.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { BLUE, BLUE_LIGHT, INK, GRAY, WHITE, SAFE, PUNCH_SPRING, SMOOTH_SPRING } from "./constants";
import { useExit } from "./useExit";
import { ServiceIcon, type ServiceIconName } from "./ServiceIcons";

const { fontFamily } = loadFont();

interface StepCardProps {
  number: string;
  title: string;
  subtitle?: string;
  icon: ServiceIconName;
  /** Horizontal anchor (default: left) */
  align?: "left" | "center";
  /** Vertical center as fraction of height (default: 0.42) */
  anchorY?: number;
  offsetX?: number;
  /** Font size as fraction of height (default: 0.046) */
  fontSizeRatio?: number;
}

export const StepCard: React.FC<StepCardProps> = ({
  number,
  title,
  subtitle,
  icon,
  align = "left",
  anchorY = 0.42,
  offsetX = 0,
  fontSizeRatio = 0.046,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const fontSize = Math.round(height * fontSizeRatio);
  const numberSize = Math.round(fontSize * 1.9);
  const numBox = Math.round(fontSize * 2.5);
  const pad = Math.round(fontSize * 0.7);
  const centered = align === "center";
  const maxWidth = Math.round(width * (centered ? 0.86 : 0.44));

  const enter = spring({ frame, fps, config: PUNCH_SPRING });
  const opacity = interpolate(enter, [0, 0.45], [0, 1], { extrapolateRight: "clamp" });
  const slideX = interpolate(enter, [0, 1], [-44, 0]);
  const scale = interpolate(enter, [0, 1], [0.94, 1]);

  const textProg = spring({ frame: frame - 4, fps, config: SMOOTH_SPRING });
  const iconProg = spring({ frame: frame - 6, fps, config: PUNCH_SPRING });

  const xShift = centered ? 0 : slideX;

  return (
    <div
      style={{
        position: "absolute",
        top: Math.round(height * anchorY),
        left: centered ? "50%" : Math.round(width * SAFE.left) + offsetX,
        maxWidth,
        opacity: opacity * exitOpacity,
        transform: centered
          ? `translateX(calc(-50% + ${offsetX}px)) translateY(calc(-50% + ${exitSlide}px)) scale(${scale})`
          : `translateY(calc(-50% + ${exitSlide}px)) translateX(${xShift}px) scale(${scale})`,
        transformOrigin: centered ? "center" : "left center",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: pad,
          padding: `${pad}px ${Math.round(pad * 1.3)}px`,
          backgroundColor: "rgba(255,255,255,0.96)",
          borderRadius: Math.round(fontSize * 0.55),
          boxShadow:
            "0 22px 56px rgba(20,30,55,0.32), 0 5px 16px rgba(20,30,55,0.18)",
        }}
      >
        {/* Number block */}
        <div
          style={{
            width: numBox,
            height: numBox,
            borderRadius: Math.round(fontSize * 0.4),
            background: `linear-gradient(140deg, ${BLUE}, ${BLUE_LIGHT})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: `0 10px 24px ${BLUE}55`,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: numberSize,
              fontWeight: 900,
              color: WHITE,
              lineHeight: 1,
            }}
          >
            {number}
          </span>
        </div>

        {/* Text */}
        <div style={{ paddingRight: Math.round(pad * 0.4) }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: Math.round(fontSize * 0.35),
              opacity: textProg,
              transform: `translateX(${interpolate(textProg, [0, 1], [14, 0])}px)`,
            }}
          >
            <span
              style={{
                color: BLUE,
                display: "inline-flex",
                transform: `scale(${interpolate(iconProg, [0, 1], [0.4, 1])})`,
              }}
            >
              <ServiceIcon name={icon} size={Math.round(fontSize * 1.05)} strokeWidth={2.1} />
            </span>
            <span
              style={{
                fontFamily,
                fontSize,
                fontWeight: 800,
                color: INK,
                letterSpacing: -Math.round(fontSize * 0.012),
                whiteSpace: "nowrap",
              }}
            >
              {title}
            </span>
          </div>
          {subtitle && (
            <div
              style={{
                fontFamily,
                fontSize: Math.round(fontSize * 0.56),
                fontWeight: 600,
                color: GRAY,
                marginTop: Math.round(fontSize * 0.18),
                opacity: textProg,
                whiteSpace: "nowrap",
              }}
            >
              {subtitle}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
