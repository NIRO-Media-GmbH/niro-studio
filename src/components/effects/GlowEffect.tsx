import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { useCI } from "../../core/ci-provider";

interface GlowEffectProps {
  color?: string;
  intensity?: number;
  pulseSpeed?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export const GlowEffect: React.FC<GlowEffectProps> = ({
  color,
  intensity = 20,
  pulseSpeed = 0.1,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const ci = useCI();

  const glowColor = color ?? ci.colors.accent;
  const pulseAmount = Math.sin(frame * pulseSpeed) * 0.3 + 0.7;
  const glowRadius = intensity * pulseAmount;

  return (
    <div
      style={{
        filter: `drop-shadow(0 0 ${glowRadius}px ${glowColor}) drop-shadow(0 0 ${glowRadius * 0.5}px ${glowColor})`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
