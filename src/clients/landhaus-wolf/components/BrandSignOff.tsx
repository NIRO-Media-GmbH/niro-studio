import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { GOLD, SAFE } from "./constants";
import { useExit } from "./useExit";

/** End sign-off screen */
export const BrandSignOff: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg } = useExit(12);

  const lineProg = spring({
    frame: frame - 3,
    fps,
    config: { damping: 12, stiffness: 100 },
  });

  const titleProg = spring({
    frame: frame - 8,
    fps,
    config: { damping: 10, stiffness: 120 },
  });

  const subtitleProg = spring({
    frame: frame - 14,
    fps,
    config: { damping: 12, stiffness: 100 },
  });

  const lineWidth = interpolate(lineProg, [0, 1], [0, width * 0.35]);
  const glowPulse = Math.sin(frame * 0.09) * 0.4 + 0.6;
  const safeCenterY = ((SAFE.top + SAFE.bottom) / 2) * height;

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: safeCenterY,
          left: "50%",
          transform: "translate(-50%, -50%)",
          opacity: exitProg,
          textAlign: "center",
        }}
      >
        <div
          style={{
            width: lineWidth,
            height: 2,
            backgroundColor: GOLD,
            margin: "0 auto 14px",
            borderRadius: 1,
            boxShadow: `0 0 ${12 * glowPulse}px ${GOLD}60`,
          }}
        />
        <div
          style={{
            opacity: titleProg,
            transform: `scale(${interpolate(titleProg, [0, 1], [0.7, 1])})`,
            fontFamily: "Bitter, serif",
            fontSize: height * 0.05,
            fontWeight: 800,
            color: GOLD,
            letterSpacing: 2,
            textShadow: `0 0 30px ${GOLD}50`,
          }}
        >
          Guten Appetit
        </div>
        <div
          style={{
            width: lineWidth * 0.6,
            height: 2,
            backgroundColor: GOLD,
            margin: "14px auto 10px",
            borderRadius: 1,
            opacity: lineProg * 0.6,
          }}
        />
        <div
          style={{
            opacity: subtitleProg,
            transform: `translateY(${interpolate(subtitleProg, [0, 1], [10, 0])}px)`,
            fontFamily: "Montserrat, sans-serif",
            fontSize: height * 0.016,
            fontWeight: 600,
            color: "rgba(255,255,255,0.7)",
            letterSpacing: 5,
            textTransform: "uppercase",
          }}
        >
          Landhaus Wolf
        </div>
      </div>
    </AbsoluteFill>
  );
};
