import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { useCI } from "../../core/ci-provider";
import { motionSpring } from "../../utils/animation-helpers";

interface AnimatedCircleProps {
  radius?: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  animateIn?: "scale" | "draw" | "fade";
  delay?: number;
  x?: number;
  y?: number;
}

export const AnimatedCircle: React.FC<AnimatedCircleProps> = ({
  radius = 80,
  fill,
  stroke,
  strokeWidth = 3,
  animateIn = "scale",
  delay = 0,
  x = 50,
  y = 50,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ci = useCI();

  const progress = motionSpring(frame, fps, { delay, damping: 12 });
  const fillColor = fill ?? ci.colors.primary;
  const strokeColor = stroke ?? ci.colors.accent;

  let scale = 1;
  let opacity = 1;
  let dashOffset = 0;
  const circumference = 2 * Math.PI * radius;

  switch (animateIn) {
    case "scale":
      scale = interpolate(progress, [0, 1], [0, 1]);
      opacity = interpolate(progress, [0, 0.3], [0, 1], {
        extrapolateRight: "clamp",
      });
      break;
    case "fade":
      opacity = progress;
      break;
    case "draw":
      dashOffset = circumference * (1 - progress);
      opacity = 1;
      break;
  }

  const svgSize = (radius + strokeWidth) * 2 + 4;
  const center = svgSize / 2;

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: `${x}%`,
          top: `${y}%`,
          transform: `translate(-50%, -50%) scale(${scale})`,
          opacity,
        }}
      >
        <svg width={svgSize} height={svgSize}>
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill={animateIn === "draw" ? "none" : fillColor}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={animateIn === "draw" ? circumference : undefined}
            strokeDashoffset={animateIn === "draw" ? dashOffset : undefined}
            strokeLinecap="round"
          />
        </svg>
      </div>
    </AbsoluteFill>
  );
};
