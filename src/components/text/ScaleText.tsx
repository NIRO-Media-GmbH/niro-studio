import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { useCI } from "../../core/ci-provider";
import { motionSpring } from "../../utils/animation-helpers";

interface ScaleTextProps {
  text: string;
  fromScale?: number;
  toScale?: number;
  delay?: number;
  fontSizeRatio?: number;
  color?: string;
  fontWeight?: string;
}

export const ScaleText: React.FC<ScaleTextProps> = ({
  text = "Scale Text",
  fromScale = 0,
  toScale = 1,
  delay = 0,
  fontSizeRatio = 0.06,
  color,
  fontWeight = "800",
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const ci = useCI();

  const progress = motionSpring(frame, fps, {
    delay,
    damping: 10,
    stiffness: 100,
  });

  const scale = interpolate(progress, [0, 1], [fromScale, toScale]);
  const opacity = interpolate(progress, [0, 0.3], [0, 1], {
    extrapolateRight: "clamp",
  });

  const fontSize = height * fontSizeRatio;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          opacity,
          fontFamily: ci.fonts.heading.family,
          fontSize,
          fontWeight,
          color: color ?? ci.colors.text,
          textAlign: "center",
          whiteSpace: "pre-line",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
