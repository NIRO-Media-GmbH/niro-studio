import React, { useMemo } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { noise2D } from "@remotion/noise";
import { useCI } from "../../core/ci-provider";

interface NoiseBackgroundProps {
  gridSize?: number;
  speed?: number;
  color?: string;
  opacity?: number;
  seed?: string;
}

export const NoiseBackground: React.FC<NoiseBackgroundProps> = ({
  gridSize = 15,
  speed = 0.01,
  color,
  opacity = 0.15,
  seed = "noise-bg",
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const ci = useCI();

  const noiseColor = color ?? ci.colors.primary;

  const cellW = Math.ceil(width / gridSize);
  const cellH = Math.ceil(height / gridSize);

  const cells = useMemo(() => {
    const result: Array<{ x: number; y: number; col: number; row: number }> = [];
    for (let row = 0; row < gridSize; row++) {
      for (let col = 0; col < gridSize; col++) {
        result.push({ x: col * cellW, y: row * cellH, col, row });
      }
    }
    return result;
  }, [gridSize, cellW, cellH]);

  return (
    <AbsoluteFill>
      <svg width={width} height={height}>
        {cells.map((cell) => {
          const noiseVal = noise2D(
            seed,
            cell.col * 0.15 + frame * speed,
            cell.row * 0.15 + frame * speed * 0.7
          );
          const cellOpacity = interpolate(noiseVal, [-1, 1], [0, opacity]);

          return (
            <rect
              key={`${cell.col}-${cell.row}`}
              x={cell.x}
              y={cell.y}
              width={cellW + 1}
              height={cellH + 1}
              fill={noiseColor}
              opacity={cellOpacity}
            />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
