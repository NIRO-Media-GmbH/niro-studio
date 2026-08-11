import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { useCI } from "../../core/ci-provider";
import { staggeredSpring } from "../../utils/animation-helpers";
import type { AnimationMode, Direction } from "../../core/types";

interface FadeInTextProps {
  text: string;
  mode?: AnimationMode;
  stagger?: { delayPerItem: number; initialDelay: number };
  fontSizeRatio?: number;
  color?: string;
  fontWeight?: string;
  textAlign?: "left" | "center" | "right";
  direction?: Direction;
  distance?: number;
}

function splitText(text: string, mode: AnimationMode): string[] {
  switch (mode) {
    case "word":
      return text.split(/\s+/);
    case "character":
      return text.split("");
    case "line":
      return text.split("\n");
  }
}

export const FadeInText: React.FC<FadeInTextProps> = ({
  text = "Your Text Here",
  mode = "word",
  stagger = { delayPerItem: 3, initialDelay: 0 },
  fontSizeRatio = 0.05,
  color,
  fontWeight = "700",
  textAlign = "center",
  direction = "up",
  distance = 30,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const ci = useCI();

  const segments = splitText(text, mode);
  const fontSize = height * fontSizeRatio;
  const gap = mode === "character" ? 0 : fontSize * 0.3;

  const justifyMap = {
    left: "flex-start" as const,
    center: "center" as const,
    right: "flex-end" as const,
  };

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
          display: "flex",
          flexWrap: "wrap",
          justifyContent: justifyMap[textAlign],
          alignItems: "center",
          gap,
          width: "100%",
        }}
      >
        {segments.map((segment, i) => {
          const progress = staggeredSpring(
            frame,
            fps,
            i,
            stagger.delayPerItem,
            stagger.initialDelay
          );

          const directionOffsets = {
            up: { x: 0, y: distance },
            down: { x: 0, y: -distance },
            left: { x: -distance, y: 0 },
            right: { x: distance, y: 0 },
          };

          const offset = directionOffsets[direction];
          const tx = interpolate(progress, [0, 1], [offset.x, 0]);
          const ty = interpolate(progress, [0, 1], [offset.y, 0]);

          return (
            <span
              key={i}
              style={{
                opacity: progress,
                transform: `translate(${tx}px, ${ty}px)`,
                fontFamily: ci.fonts.heading.family,
                fontSize,
                fontWeight,
                color: color ?? ci.colors.text,
                display: "inline-block",
                whiteSpace: mode === "character" ? "pre" : undefined,
              }}
            >
              {segment}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
