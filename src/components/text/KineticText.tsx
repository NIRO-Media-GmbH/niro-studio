import React, { useMemo } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, random, interpolate } from "remotion";
import { noise2D } from "@remotion/noise";
import { useCI } from "../../core/ci-provider";
import { staggeredSpring } from "../../utils/animation-helpers";

interface KineticTextProps {
  text: string;
  wobbleIntensity?: number;
  stagger?: { delayPerItem: number; initialDelay: number };
  fontSizeRatio?: number;
  color?: string;
  fontWeight?: string;
  seed?: string;
}

export const KineticText: React.FC<KineticTextProps> = ({
  text = "Kinetic Typography",
  wobbleIntensity = 8,
  stagger = { delayPerItem: 4, initialDelay: 0 },
  fontSizeRatio = 0.06,
  color,
  fontWeight = "800",
  seed = "kinetic",
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const ci = useCI();

  const words = useMemo(() => text.split(/\s+/), [text]);
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
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "center",
          gap: fontSize * 0.35,
        }}
      >
        {words.map((word, i) => {
          const entrance = staggeredSpring(
            frame,
            fps,
            i,
            stagger.delayPerItem,
            stagger.initialDelay
          );

          // Organic continuous motion after entrance
          const noiseX =
            noise2D(seed + "-x-" + i, frame * 0.015, i * 0.5) *
            wobbleIntensity *
            entrance;
          const noiseY =
            noise2D(seed + "-y-" + i, i * 0.5, frame * 0.015) *
            wobbleIntensity *
            entrance;
          const noiseRotate =
            noise2D(seed + "-r-" + i, frame * 0.01, i * 0.3) *
            (wobbleIntensity * 0.3) *
            entrance;

          // Entrance from random direction
          const entranceAngle = random(seed + i) * Math.PI * 2;
          const entranceDistance = 300;
          const entranceX =
            Math.cos(entranceAngle) * entranceDistance * (1 - entrance);
          const entranceY =
            Math.sin(entranceAngle) * entranceDistance * (1 - entrance);

          const scale = interpolate(entrance, [0, 1], [0.3, 1]);

          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                opacity: entrance,
                transform: `translate(${entranceX + noiseX}px, ${entranceY + noiseY}px) rotate(${noiseRotate}deg) scale(${scale})`,
                fontFamily: ci.fonts.heading.family,
                fontSize,
                fontWeight,
                color: color ?? ci.colors.text,
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
