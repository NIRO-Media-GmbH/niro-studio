import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { staggeredSpring, slideOffset } from "../../utils/animation-helpers";
import type { Direction } from "../../core/types";

interface StaggerChildrenProps {
  delayPerItem?: number;
  initialDelay?: number;
  direction?: Direction;
  distance?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export const StaggerChildren: React.FC<StaggerChildrenProps> = ({
  delayPerItem = 3,
  initialDelay = 0,
  direction = "up",
  distance = 40,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div style={style}>
      {React.Children.map(children, (child, index) => {
        const progress = staggeredSpring(
          frame,
          fps,
          index,
          delayPerItem,
          initialDelay
        );
        const offset = slideOffset(
          frame,
          fps,
          direction,
          distance,
          initialDelay + index * delayPerItem
        );

        return (
          <div
            style={{
              opacity: progress,
              transform: `translate(${offset.x}px, ${offset.y}px)`,
            }}
          >
            {child}
          </div>
        );
      })}
    </div>
  );
};
