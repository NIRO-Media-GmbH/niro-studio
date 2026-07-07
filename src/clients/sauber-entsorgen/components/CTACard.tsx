// ============================================================
// Sauber Entsorgen — CTACard
// Final call-to-action: headline + phone pill + closing line.
// Reveals in stages, left-anchored.
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
import { ServiceIcon } from "./ServiceIcons";

const { fontFamily } = loadFont();

interface CTACardProps {
  headline: string;
  phone: string;
  closing?: string;
  /** Horizontal anchor (default: left) */
  align?: "left" | "center";
  /** Top anchor as fraction of height (default: 0.34) */
  anchorY?: number;
  offsetX?: number;
  /** Font size as fraction of height (default: 0.062) */
  fontSizeRatio?: number;
}

export const CTACard: React.FC<CTACardProps> = ({
  headline,
  phone,
  closing,
  align = "left",
  anchorY = 0.34,
  offsetX = 0,
  fontSizeRatio = 0.062,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  const headSize = Math.round(height * fontSizeRatio);
  const pad = Math.round(headSize * 0.55);
  const centered = align === "center";
  const maxWidth = Math.round(width * (centered ? 0.86 : 0.46));

  const enter = spring({ frame, fps, config: PUNCH_SPRING });
  const opacity = interpolate(enter, [0, 0.4], [0, 1], { extrapolateRight: "clamp" });
  const slideX = interpolate(enter, [0, 1], [-50, 0]);

  const phoneProg = spring({ frame: frame - 12, fps, config: PUNCH_SPRING });
  const closeProg = spring({ frame: frame - 26, fps, config: SMOOTH_SPRING });

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
          padding: `${Math.round(pad * 1.2)}px ${Math.round(pad * 1.4)}px`,
          backgroundColor: "rgba(255,255,255,0.97)",
          borderRadius: Math.round(headSize * 0.42),
          boxShadow:
            "0 26px 64px rgba(20,30,55,0.36), 0 6px 18px rgba(20,30,55,0.2)",
          textAlign: centered ? "center" : "left",
        }}
      >
        {/* Eyebrow */}
        <div
          style={{
            fontFamily,
            fontSize: Math.round(headSize * 0.34),
            fontWeight: 800,
            color: BLUE,
            textTransform: "uppercase",
            letterSpacing: Math.round(headSize * 0.05),
            marginBottom: Math.round(headSize * 0.18),
          }}
        >
          Jetzt anfragen
        </div>

        {/* Headline */}
        <div
          style={{
            fontFamily,
            fontSize: headSize,
            fontWeight: 900,
            color: INK,
            lineHeight: 1.15,
            paddingBottom: Math.round(headSize * 0.06),
            letterSpacing: -Math.round(headSize * 0.015),
            maxWidth: Math.round(maxWidth * 0.9),
            marginInline: centered ? "auto" : undefined,
          }}
        >
          {headline}
        </div>

        {/* Phone pill */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: Math.round(headSize * 0.3),
            marginTop: Math.round(headSize * 0.4),
            padding: `${Math.round(headSize * 0.28)}px ${Math.round(headSize * 0.5)}px`,
            background: `linear-gradient(135deg, ${BLUE}, ${BLUE_LIGHT})`,
            borderRadius: 999,
            boxShadow: `0 12px 30px ${BLUE}66`,
            opacity: interpolate(phoneProg, [0, 0.5], [0, 1], { extrapolateRight: "clamp" }),
            transform: `translateY(${interpolate(phoneProg, [0, 1], [18, 0])}px) scale(${interpolate(phoneProg, [0, 1], [0.85, 1])})`,
          }}
        >
          <ServiceIcon name="telefon" size={Math.round(headSize * 0.7)} color={WHITE} strokeWidth={2.1} />
          <span
            style={{
              fontFamily,
              fontSize: Math.round(headSize * 0.66),
              fontWeight: 800,
              color: WHITE,
              whiteSpace: "nowrap",
            }}
          >
            {phone}
          </span>
        </div>

        {/* Closing line */}
        {closing && (
          <div
            style={{
              fontFamily,
              fontSize: Math.round(headSize * 0.42),
              fontWeight: 600,
              color: GRAY,
              marginTop: Math.round(headSize * 0.35),
              opacity: closeProg,
              transform: `translateY(${interpolate(closeProg, [0, 1], [10, 0])}px)`,
            }}
          >
            {closing}
          </div>
        )}
      </div>
    </div>
  );
};
