import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { useCI } from "../../core/ci-provider";
import { hexToRgba } from "../../utils/color-utils";

interface WaveBackgroundProps {
  layers?: number;
  amplitude?: number;
  frequency?: number;
  colors?: string[];
  speed?: number;
}

function generateWavePath(
  width: number,
  height: number,
  amplitude: number,
  frequency: number,
  phase: number,
  yOffset: number
): string {
  const points: string[] = [];
  const steps = 40;

  for (let i = 0; i <= steps; i++) {
    const x = (i / steps) * width;
    const y =
      yOffset + Math.sin(x * frequency * 0.01 + phase) * amplitude;
    points.push(i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`);
  }

  // Close path at bottom
  points.push(`L ${width} ${height}`);
  points.push(`L 0 ${height}`);
  points.push("Z");

  return points.join(" ");
}

export const WaveBackground: React.FC<WaveBackgroundProps> = ({
  layers = 3,
  amplitude = 60,
  frequency = 2,
  colors,
  speed = 1,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const ci = useCI();

  const waveColors = colors ?? [
    ci.colors.primary,
    ci.colors.secondary,
    ci.colors.accent,
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: ci.colors.background }}>
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", bottom: 0 }}
      >
        {Array.from({ length: layers }).map((_, i) => {
          const layerPhase = frame * 0.03 * speed * (1 + i * 0.3);
          const layerAmplitude = amplitude * (1 - i * 0.15);
          const yOffset = height * (0.5 + i * 0.12);
          const layerColor =
            waveColors[i % waveColors.length] ?? ci.colors.primary;
          const layerOpacity = 1 - i * 0.2;

          const path = generateWavePath(
            width,
            height,
            layerAmplitude,
            frequency,
            layerPhase,
            yOffset
          );

          return (
            <path
              key={i}
              d={path}
              fill={hexToRgba(layerColor, layerOpacity * 0.4)}
            />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
