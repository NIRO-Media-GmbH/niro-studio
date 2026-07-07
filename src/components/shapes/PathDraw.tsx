import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";
import { useCI } from "../../core/ci-provider";
import { motionSpring } from "../../utils/animation-helpers";

interface PathDrawProps {
  path: string;
  strokeColor?: string;
  strokeWidth?: number;
  delay?: number;
  durationInSeconds?: number;
  viewBox?: string;
  fill?: string;
  fillAfterDraw?: boolean;
  width?: number | string;
  height?: number | string;
}

export const PathDraw: React.FC<PathDrawProps> = ({
  path = "M 10 80 C 40 10, 65 10, 95 80 S 150 150, 180 80",
  strokeColor,
  strokeWidth = 3,
  delay = 0,
  durationInSeconds = 1.5,
  viewBox = "0 0 200 200",
  fill = "none",
  fillAfterDraw = false,
  width = 400,
  height = 400,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ci = useCI();

  const progress = motionSpring(frame, fps, {
    delay,
    damping: 20,
    stiffness: 80,
  });

  const evolved = evolvePath(progress, path);

  const fillOpacity = fillAfterDraw
    ? Math.max(0, Math.min(1, (progress - 0.8) / 0.2))
    : fill !== "none"
      ? 1
      : 0;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <svg viewBox={viewBox} style={{ width, height }}>
        <path
          d={path}
          fill={fillAfterDraw ? strokeColor ?? ci.colors.primary : fill}
          fillOpacity={fillOpacity}
          stroke={strokeColor ?? ci.colors.primary}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={evolved.strokeDasharray}
          strokeDashoffset={evolved.strokeDashoffset}
        />
      </svg>
    </AbsoluteFill>
  );
};
