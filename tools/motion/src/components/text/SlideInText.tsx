import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { useCI } from "../../core/ci-provider";
import { motionSpring, slideOffset } from "../../utils/animation-helpers";
import type { Direction } from "../../core/types";

interface SlideInTextProps {
  text: string;
  direction?: Direction;
  distance?: number;
  delay?: number;
  fontSizeRatio?: number;
  color?: string;
  fontWeight?: string;
  textAlign?: "left" | "center" | "right";
}

export const SlideInText: React.FC<SlideInTextProps> = ({
  text = "Slide In Text",
  direction = "up",
  distance = 200,
  delay = 0,
  fontSizeRatio = 0.05,
  color,
  fontWeight = "700",
  textAlign = "center",
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const ci = useCI();

  const progress = motionSpring(frame, fps, { delay, damping: 14 });
  const offset = slideOffset(frame, fps, direction, distance, delay);
  const fontSize = height * fontSizeRatio;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "5%",
      }}
    >
      <div
        style={{
          opacity: progress,
          transform: `translate(${offset.x}px, ${offset.y}px)`,
          fontFamily: ci.fonts.heading.family,
          fontSize,
          fontWeight,
          color: color ?? ci.colors.text,
          textAlign,
          width: "100%",
          whiteSpace: "pre-line",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
