import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { GOLD, SAFE } from "./constants";

/** Brand watermark — bottom corner */
export const BrandWatermark: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();

  const enterProg = spring({
    frame: frame - 10,
    fps,
    config: { damping: 20, stiffness: 80 },
  });

  const exitProg = interpolate(
    frame,
    [durationInFrames - 30, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const diamondSpin = interpolate(enterProg, [0, 1], [0, 45]);

  return (
    <div
      style={{
        position: "absolute",
        bottom: height * (1 - SAFE.bottom + 0.01),
        right: width * (1 - SAFE.right),
        opacity: enterProg * exitProg * 0.6,
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      <div
        style={{
          width: 4,
          height: 4,
          backgroundColor: GOLD,
          transform: `rotate(${diamondSpin}deg)`,
        }}
      />
      <span
        style={{
          fontFamily: "Montserrat, sans-serif",
          fontSize: height * 0.012,
          fontWeight: 500,
          color: GOLD,
          letterSpacing: 3,
          textTransform: "uppercase",
          opacity: enterProg,
          transform: `translateX(${interpolate(enterProg, [0, 1], [8, 0])}px)`,
        }}
      >
        Landhaus Wolf
      </span>
    </div>
  );
};
