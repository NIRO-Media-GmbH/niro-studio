import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { useCI } from "../../core/ci-provider";
import { motionSpring } from "../../utils/animation-helpers";

interface CircleWipeProps {
  color?: string;
  delay?: number;
  originX?: number;
  originY?: number;
  children?: React.ReactNode;
}

export const CircleWipe: React.FC<CircleWipeProps> = ({
  color,
  delay = 0,
  originX = 50,
  originY = 50,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ci = useCI();

  const progress = motionSpring(frame, fps, {
    delay,
    damping: 14,
    stiffness: 80,
  });

  const radius = interpolate(progress, [0, 1], [0, 150]);
  const wipeColor = color ?? ci.colors.primary;

  return (
    <AbsoluteFill>
      {/* Colored circle expanding */}
      <AbsoluteFill
        style={{
          backgroundColor: wipeColor,
          clipPath: `circle(${radius}% at ${originX}% ${originY}%)`,
        }}
      />
      {/* Content revealed by the wipe */}
      {children && (
        <AbsoluteFill
          style={{
            clipPath: `circle(${radius}% at ${originX}% ${originY}%)`,
          }}
        >
          {children}
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
