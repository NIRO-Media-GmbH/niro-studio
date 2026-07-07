import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { motionSpring, slideOffset } from "../../utils/animation-helpers";
import type { Direction } from "../../core/types";

interface SlideInProps {
  delay?: number;
  direction?: Direction;
  distance?: number;
  damping?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export const SlideIn: React.FC<SlideInProps> = ({
  delay = 0,
  direction = "up",
  distance = 200,
  damping = 14,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = motionSpring(frame, fps, { delay, damping });
  const offset = slideOffset(frame, fps, direction, distance, delay);

  return (
    <div
      style={{
        opacity: progress,
        transform: `translate(${offset.x}px, ${offset.y}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
