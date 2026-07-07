import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { motionSpring } from "../../utils/animation-helpers";

interface SpringInProps {
  delay?: number;
  fromScale?: number;
  toScale?: number;
  damping?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export const SpringIn: React.FC<SpringInProps> = ({
  delay = 0,
  fromScale = 0,
  toScale = 1,
  damping = 10,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = motionSpring(frame, fps, { delay, damping });
  const scale = interpolate(progress, [0, 1], [fromScale, toScale]);
  const opacity = interpolate(progress, [0, 0.3], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        transform: `scale(${scale})`,
        opacity,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
