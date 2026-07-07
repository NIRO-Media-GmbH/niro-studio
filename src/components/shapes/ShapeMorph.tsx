import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { evolvePath } from "@remotion/paths";
import { useCI } from "../../core/ci-provider";
import { motionSpring } from "../../utils/animation-helpers";

interface ShapeMorphProps {
  fromPath: string;
  toPath: string;
  strokeColor?: string;
  fillColor?: string;
  strokeWidth?: number;
  delay?: number;
  viewBox?: string;
  width?: number | string;
  height?: number | string;
}

/**
 * Morph between two shapes using crossfade evolvePath technique.
 * Source path draws down while target path draws up.
 */
export const ShapeMorph: React.FC<ShapeMorphProps> = ({
  fromPath = "M 50 150 L 100 50 L 150 150 Z",
  toPath = "M 50 50 L 150 50 L 150 150 L 50 150 Z",
  strokeColor,
  fillColor,
  strokeWidth = 3,
  delay = 0,
  viewBox = "0 0 200 200",
  width = 400,
  height = 400,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ci = useCI();

  const progress = motionSpring(frame, fps, { delay, damping: 16 });
  const color = strokeColor ?? ci.colors.primary;
  const fill = fillColor ?? ci.colors.accent;

  // Source fades/draws out
  const sourceProgress = interpolate(progress, [0, 1], [1, 0]);
  const sourceEvolved = evolvePath(sourceProgress, fromPath);
  const sourceOpacity = interpolate(progress, [0, 0.5, 1], [1, 0.5, 0]);

  // Target draws in
  const targetEvolved = evolvePath(progress, toPath);
  const targetOpacity = interpolate(progress, [0, 0.5, 1], [0, 0.5, 1]);

  return (
    <AbsoluteFill
      style={{ justifyContent: "center", alignItems: "center" }}
    >
      <svg viewBox={viewBox} style={{ width, height }}>
        {/* Source shape (fading out) */}
        <path
          d={fromPath}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={sourceEvolved.strokeDasharray}
          strokeDashoffset={sourceEvolved.strokeDashoffset}
          opacity={sourceOpacity}
        />
        {/* Target shape (drawing in) */}
        <path
          d={toPath}
          fill={interpolate(progress, [0.7, 1], [0, 0.3], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }) > 0 ? fill : "none"}
          fillOpacity={interpolate(progress, [0.7, 1], [0, 0.3], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          })}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={targetEvolved.strokeDasharray}
          strokeDashoffset={targetEvolved.strokeDashoffset}
          opacity={targetOpacity}
        />
      </svg>
    </AbsoluteFill>
  );
};
