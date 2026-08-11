// ============================================================
// Sauber Entsorgen — IntroCard
// Name / role / company lower-third for the GF introduction.
// Left-anchored.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { BLUE, BLUE_LIGHT, INK, GRAY, SAFE, PUNCH_SPRING, SMOOTH_SPRING } from "./constants";
import { useExit } from "./useExit";

const { fontFamily } = loadFont();

interface IntroCardProps {
  name: string;
  role: string;
  company: string;
  /** Horizontal anchor (default: left) */
  align?: "left" | "center";
  /** Top anchor as fraction of height (default: 0.6) */
  anchorY?: number;
  offsetX?: number;
  /** Font size as fraction of height (default: 0.058) */
  fontSizeRatio?: number;
}

export const IntroCard: React.FC<IntroCardProps> = ({
  name,
  role,
  company,
  align = "left",
  anchorY = 0.6,
  offsetX = 0,
  fontSizeRatio = 0.058,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const nameSize = Math.round(height * fontSizeRatio);
  const pad = Math.round(nameSize * 0.5);
  const centered = align === "center";
  const maxWidth = Math.round(width * (centered ? 0.84 : 0.46));

  const enter = spring({ frame, fps, config: PUNCH_SPRING });
  const opacity = interpolate(enter, [0, 0.45], [0, 1], { extrapolateRight: "clamp" });
  const slideX = interpolate(enter, [0, 1], [-46, 0]);

  const barProg = spring({ frame: frame - 3, fps, config: SMOOTH_SPRING });
  const lineProg = spring({ frame: frame - 7, fps, config: SMOOTH_SPRING });

  return (
    <div
      style={{
        position: "absolute",
        top: Math.round(height * anchorY),
        left: centered ? "50%" : Math.round(width * SAFE.left) + offsetX,
        maxWidth,
        opacity: opacity * exitOpacity,
        transform: centered
          ? `translateX(calc(-50% + ${offsetX}px)) translateY(${exitSlide}px)`
          : `translateX(${slideX}px) translateY(${exitSlide}px)`,
      }}
    >
      <div
        style={{
          display: "flex",
          backgroundColor: "rgba(255,255,255,0.96)",
          borderRadius: Math.round(nameSize * 0.4),
          boxShadow:
            "0 22px 56px rgba(20,30,55,0.32), 0 5px 16px rgba(20,30,55,0.18)",
          overflow: "hidden",
        }}
      >
        {/* Accent bar */}
        <div
          style={{
            width: Math.round(nameSize * 0.18),
            background: `linear-gradient(${BLUE}, ${BLUE_LIGHT})`,
            transform: `scaleY(${barProg})`,
            transformOrigin: "top",
          }}
        />
        <div style={{ padding: `${pad}px ${Math.round(pad * 1.6)}px` }}>
          <div
            style={{
              fontFamily,
              fontSize: Math.round(nameSize * 0.34),
              fontWeight: 800,
              color: BLUE,
              textTransform: "uppercase",
              letterSpacing: Math.round(nameSize * 0.05),
            }}
          >
            {role}
          </div>
          <div
            style={{
              fontFamily,
              fontSize: nameSize,
              fontWeight: 900,
              color: INK,
              lineHeight: 1.04,
              letterSpacing: -Math.round(nameSize * 0.015),
              marginTop: Math.round(nameSize * 0.06),
            }}
          >
            {name}
          </div>
          <div
            style={{
              fontFamily,
              fontSize: Math.round(nameSize * 0.42),
              fontWeight: 600,
              color: GRAY,
              marginTop: Math.round(nameSize * 0.1),
              clipPath: `inset(0 ${100 - lineProg * 100}% 0 0)`,
              lineHeight: 1.3,
              paddingBottom: Math.round(nameSize * 0.05),
              whiteSpace: "nowrap",
            }}
          >
            {company}
          </div>
        </div>
      </div>
    </div>
  );
};
