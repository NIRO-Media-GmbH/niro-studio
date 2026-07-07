import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { useCI } from "../../core/ci-provider";
import { motionSpring } from "../../utils/animation-helpers";

interface AnimatedRectProps {
  rectWidth?: number;
  rectHeight?: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  cornerRadius?: number;
  animateIn?: "scale" | "draw" | "fade";
  delay?: number;
  x?: number;
  y?: number;
}

export const AnimatedRect: React.FC<AnimatedRectProps> = ({
  rectWidth = 200,
  rectHeight = 120,
  fill,
  stroke,
  strokeWidth = 3,
  cornerRadius,
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
  const rx = cornerRadius ?? ci.style.borderRadius;

  let scale = 1;
  let opacity = 1;
  let dashOffset = 0;
  const perimeter = 2 * (rectWidth + rectHeight);

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
      dashOffset = perimeter * (1 - progress);
      opacity = 1;
      break;
  }

  const svgW = rectWidth + strokeWidth * 2 + 4;
  const svgH = rectHeight + strokeWidth * 2 + 4;
  const rX = strokeWidth + 2;
  const rY = strokeWidth + 2;

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
        <svg width={svgW} height={svgH}>
          <rect
            x={rX}
            y={rY}
            width={rectWidth}
            height={rectHeight}
            rx={rx}
            ry={rx}
            fill={animateIn === "draw" ? "none" : fillColor}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={animateIn === "draw" ? perimeter : undefined}
            strokeDashoffset={animateIn === "draw" ? dashOffset : undefined}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </AbsoluteFill>
  );
};
