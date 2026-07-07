import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { motionSpring, slideOffset } from "../../utils/animation-helpers";
import type { Direction } from "../../core/types";

interface FadeInProps {
  delay?: number;
  direction?: Direction;
  distance?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export const FadeIn: React.FC<FadeInProps> = ({
  delay = 0,
  direction,
  distance = 30,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = motionSpring(frame, fps, { delay });
  const offset = direction
    ? slideOffset(frame, fps, direction, distance, delay)
    : { x: 0, y: 0 };

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
