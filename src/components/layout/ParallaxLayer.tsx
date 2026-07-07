import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

interface ParallaxLayerProps {
  speed?: number;
  direction?: "vertical" | "horizontal";
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export const ParallaxLayer: React.FC<ParallaxLayerProps> = ({
  speed = 0.5,
  direction = "vertical",
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progress = frame / durationInFrames;
  const movement = progress * speed * 100;

  const transform =
    direction === "vertical"
      ? `translateY(${-movement}px)`
      : `translateX(${-movement}px)`;

  return (
    <AbsoluteFill style={{ transform, ...style }}>{children}</AbsoluteFill>
  );
};
