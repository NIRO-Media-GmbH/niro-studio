import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { GOLD, DARK_BG, SAFE } from "./constants";
import { useExit } from "./useExit";

/** Temperature / info callout badge */
export const Callout: React.FC<{
  text: string;
  subtext?: string;
  position?: "center" | "bottom-right" | "top-right";
}> = ({ text, subtext, position = "center" }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg } = useExit(10);

  const enterProg = spring({
    frame: frame - 2,
    fps,
    config: { damping: 8, stiffness: 160 },
  });

  const scale = interpolate(enterProg, [0, 1], [0.5, 1]);
  const glowPulse = Math.sin(frame * 0.1) * 0.35 + 0.65;

  const safeRight = width * SAFE.right;
  const safeTop = height * SAFE.top;

  const posMap: Record<string, React.CSSProperties> = {
    center: {
      top: ((SAFE.top + SAFE.bottom) / 2) * height,
      left: "50%",
      transform: `translate(-50%, -50%) scale(${scale})`,
    },
    "bottom-right": {
      bottom: height * (1 - SAFE.bottom + 0.02),
      right: width - safeRight,
      transform: `scale(${scale})`,
    },
    "top-right": {
      top: safeTop,
      right: width - safeRight,
      transform: `scale(${scale})`,
    },
  };

  // Limit width so top-right / bottom-right callouts don't cover the StepBadge
  const maxW =
    position === "center" ? undefined : width * 0.48;

  // --- auto-scale main text so it never overflows the box ---
  const hPad = height * 0.03; // horizontal padding each side
  const availableW = maxW ? maxW - hPad * 2 : width * 0.8;
  const baseFontSize = height * 0.048;
  // approx char width ≈ 0.58 em for Bitter 800
  const estTextW = text.length * baseFontSize * 0.58;
  const titleFontSize =
    estTextW > availableW
      ? availableW / (text.length * 0.58)
      : baseFontSize;

  return (
    <div
      style={{
        position: "absolute",
        ...posMap[position],
        maxWidth: maxW,
        opacity: enterProg * exitProg,
      }}
    >
      <div
        style={{
          backgroundColor: DARK_BG,
          borderRadius: 10,
          padding: `${height * 0.015}px ${hPad}px`,
          border: `2.5px solid ${GOLD}`,
          backdropFilter: "blur(14px)",
          textAlign: "center",
          overflow: "hidden",
          boxShadow: `0 0 ${24 * glowPulse}px ${GOLD}40, 0 4px 24px rgba(0,0,0,0.5)`,
        }}
      >
        <div
          style={{
            fontFamily: "Bitter, serif",
            fontSize: titleFontSize,
            fontWeight: 800,
            color: GOLD,
            lineHeight: 1.1,
            textShadow: `0 0 24px ${GOLD}50`,
          }}
        >
          {text}
        </div>
        {subtext && (
          <div
            style={{
              fontFamily: "Montserrat, sans-serif",
              fontSize: height * 0.015,
              fontWeight: 600,
              color: "rgba(255,255,255,0.85)",
              letterSpacing: 1.5,
              marginTop: 6,
            }}
          >
            {subtext}
          </div>
        )}
      </div>
    </div>
  );
};
