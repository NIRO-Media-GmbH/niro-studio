import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, interpolateColors } from "remotion";
import { useCI } from "../../core/ci-provider";

interface GradientBackgroundProps {
  colors?: string[];
  type?: "linear" | "radial";
  animate?: boolean;
  rotationSpeed?: number;
  startAngle?: number;
}

export const GradientBackground: React.FC<GradientBackgroundProps> = ({
  colors,
  type = "linear",
  animate = true,
  rotationSpeed = 1,
  startAngle = 135,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const ci = useCI();

  const gradientColors = colors ?? [ci.colors.secondary, ci.colors.primary];

  const angle = animate
    ? interpolate(
        frame,
        [0, durationInFrames],
        [startAngle, startAngle + 360 * rotationSpeed],
      )
    : startAngle;

  const colorStops = gradientColors
    .map((c, i) => {
      const percent = (i / (gradientColors.length - 1)) * 100;
      return `${c} ${percent}%`;
    })
    .join(", ");

  const background =
    type === "linear"
      ? `linear-gradient(${angle}deg, ${colorStops})`
      : `radial-gradient(circle at 50% 50%, ${colorStops})`;

  return <AbsoluteFill style={{ background }} />;
};
