import React, { useMemo } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, random, interpolate } from "remotion";
import { noise2D } from "@remotion/noise";
import { useCI } from "../../core/ci-provider";

interface ParticleFieldProps {
  count?: number;
  minSize?: number;
  maxSize?: number;
  color?: string;
  speed?: number;
  seed?: string;
  opacity?: number;
}

export const ParticleField: React.FC<ParticleFieldProps> = ({
  count = 60,
  minSize = 1,
  maxSize = 5,
  color,
  speed = 1,
  seed = "particles",
  opacity = 0.6,
}) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const ci = useCI();

  const particleColor = color ?? ci.colors.accent;

  const particles = useMemo(
    () =>
      Array.from({ length: count }, (_, i) => ({
        id: i,
        x: random(seed + "-x-" + i) * width,
        y: random(seed + "-y-" + i) * height,
        size: minSize + random(seed + "-s-" + i) * (maxSize - minSize),
        baseOpacity: 0.3 + random(seed + "-o-" + i) * 0.7,
      })),
    [count, width, height, seed, minSize, maxSize]
  );

  return (
    <AbsoluteFill>
      {particles.map((p) => {
        const noiseX =
          noise2D(seed + "-nx-" + p.id, frame * 0.005 * speed, p.id * 0.3) *
          80;
        const noiseY =
          noise2D(seed + "-ny-" + p.id, p.id * 0.3, frame * 0.005 * speed) *
          80;

        const drift = frame * speed * 0.3;
        const x = ((p.x + noiseX + drift) % (width + 40)) - 20;
        const y = ((p.y + noiseY - drift * 0.5) % (height + 40)) - 20;

        // Fade particles near edges
        const edgeFade = Math.min(
          interpolate(x, [0, 60], [0, 1], { extrapolateRight: "clamp" }),
          interpolate(x, [width - 60, width], [1, 0], { extrapolateLeft: "clamp" }),
          interpolate(y, [0, 60], [0, 1], { extrapolateRight: "clamp" }),
          interpolate(y, [height - 60, height], [1, 0], { extrapolateLeft: "clamp" })
        );

        return (
          <div
            key={p.id}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              backgroundColor: particleColor,
              opacity: p.baseOpacity * opacity * edgeFade,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
