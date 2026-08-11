import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { GOLD, GOLD_LIGHT, SAFE } from "./constants";
import { useExit } from "./useExit";

/** Lower-third section title bar */
export const SectionTitle: React.FC<{
  title: string;
  subtitle?: string;
  position?: "bottom" | "top";
}> = ({ title, subtitle, position = "bottom" }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitSlide } = useExit(12);

  const lineProg = spring({
    frame: frame - 2,
    fps,
    config: { damping: 12, stiffness: 160 },
  });

  const titleProg = spring({
    frame: frame - 5,
    fps,
    config: { damping: 10, stiffness: 150 },
  });

  const subtitleProg = spring({
    frame: frame - 10,
    fps,
    config: { damping: 12, stiffness: 140 },
  });

  const safeLeft = width * SAFE.left;
  const posStyle =
    position === "bottom"
      ? { bottom: height * (1 - SAFE.bottom + 0.02), left: safeLeft }
      : { top: height * SAFE.top, left: safeLeft };

  const lineWidth = interpolate(lineProg, [0, 1], [0, width * 0.3]);

  return (
    <div
      style={{
        position: "absolute",
        ...posStyle,
        opacity: exitProg,
        transform: `translateY(${exitSlide}px)`,
      }}
    >
      {/* Gold accent line */}
      <div
        style={{
          width: lineWidth,
          height: 3,
          backgroundColor: GOLD,
          marginBottom: 8,
          borderRadius: 2,
          boxShadow: `0 0 ${10 * lineProg}px ${GOLD}50`,
        }}
      />

      {/* Title */}
      <div
        style={{
          opacity: titleProg,
          transform: `translateY(${interpolate(titleProg, [0, 1], [20, 0])}px) scale(${interpolate(titleProg, [0, 1], [0.92, 1])})`,
          transformOrigin: "left center",
          fontFamily: "Bitter, serif",
          fontSize: height * 0.042,
          fontWeight: 800,
          color: "#FFFFFF",
          letterSpacing: 0.5,
          textShadow:
            "0 2px 16px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.5)",
          lineHeight: 1.15,
        }}
      >
        {title}
      </div>

      {/* Subtitle */}
      {subtitle && (
        <div
          style={{
            opacity: subtitleProg * 0.85,
            transform: `translateY(${interpolate(subtitleProg, [0, 1], [10, 0])}px)`,
            fontFamily: "Montserrat, sans-serif",
            fontSize: height * 0.018,
            fontWeight: 600,
            color: GOLD_LIGHT,
            letterSpacing: 2.5,
            textTransform: "uppercase",
            marginTop: 5,
            textShadow: "0 1px 10px rgba(0,0,0,0.9)",
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
};
