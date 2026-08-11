import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { GOLD, SAFE } from "./constants";
import { useExit } from "./useExit";

/** Step indicator */
export const StepBadge: React.FC<{
  step: number;
  label: string;
}> = ({ step, label }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { exitProg, exitSlide } = useExit(10);

  const circleProg = spring({
    frame: frame - 1,
    fps,
    config: { damping: 8, stiffness: 200 },
  });

  const numberProg = spring({
    frame: frame - 4,
    fps,
    config: { damping: 10, stiffness: 180 },
  });

  const labelProg = spring({
    frame: frame - 7,
    fps,
    config: { damping: 10, stiffness: 150 },
  });

  const circleScale = interpolate(circleProg, [0, 1], [0, 1]);
  const glowPulse = Math.sin(frame * 0.08) * 0.4 + 0.6;
  const circleSize = height * 0.044;

  return (
    <div
      style={{
        position: "absolute",
        top: height * SAFE.top,
        left: width * SAFE.left,
        opacity: exitProg,
        transform: `translateY(${exitSlide}px)`,
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}
    >
      <div
        style={{
          width: circleSize,
          height: circleSize,
          borderRadius: "50%",
          border: `2.5px solid ${GOLD}`,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${circleScale})`,
          boxShadow: `0 0 ${14 * glowPulse}px ${GOLD}50`,
          backgroundColor: "rgba(12, 10, 8, 0.65)",
        }}
      >
        <span
          style={{
            fontFamily: "Bitter, serif",
            fontSize: height * 0.024,
            fontWeight: 800,
            color: GOLD,
            opacity: numberProg,
            transform: `scale(${interpolate(numberProg, [0, 1], [0.3, 1])})`,
          }}
        >
          {step}
        </span>
      </div>

      <span
        style={{
          opacity: labelProg,
          transform: `translateX(${interpolate(labelProg, [0, 1], [-20, 0])}px)`,
          fontFamily: "Montserrat, sans-serif",
          fontSize: height * 0.017,
          fontWeight: 700,
          color: "#FFFFFF",
          letterSpacing: 2.5,
          textTransform: "uppercase",
          textShadow:
            "0 2px 14px rgba(0,0,0,0.95), 0 0 35px rgba(0,0,0,0.5)",
        }}
      >
        {label}
      </span>
    </div>
  );
};
