// ============================================================
// AmbientBackground — Persistent background layer
// Subtle floating particles + vignette to fill empty space
// ============================================================

import React, { useMemo } from "react";
import { useCurrentFrame, random } from "remotion";
import { W, H, WHITE } from "../constants";

const PARTICLE_COUNT = 40;

interface Particle {
  x: number;
  y: number;
  radius: number;
  speed: number;
  driftX: number;
  phaseOffset: number;
  opacity: number;
}

export const AmbientBackground: React.FC = () => {
  const frame = useCurrentFrame();

  const particles = useMemo<Particle[]>(() => {
    return Array.from({ length: PARTICLE_COUNT }, (_, i) => ({
      x: random(`bg-x-${i}`) * W,
      y: random(`bg-y-${i}`) * H,
      radius: 1.5 + random(`bg-r-${i}`) * 3.5,
      speed: 0.2 + random(`bg-sp-${i}`) * 0.5,
      driftX: (random(`bg-dx-${i}`) - 0.5) * 0.3,
      phaseOffset: random(`bg-ph-${i}`) * Math.PI * 2,
      opacity: 0.03 + random(`bg-op-${i}`) * 0.05,
    }));
  }, []);

  return (
    <g>
      {/* Vignette — darker edges */}
      <defs>
        <radialGradient id="bgVignette" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="transparent" stopOpacity="0" />
          <stop offset="70%" stopColor="transparent" stopOpacity="0" />
          <stop offset="100%" stopColor="#000000" stopOpacity="0.4" />
        </radialGradient>
      </defs>
      <rect x={0} y={0} width={W} height={H} fill="url(#bgVignette)" />

      {/* Floating particles — slow drift upward */}
      {particles.map((p, i) => {
        const yOffset = (frame * p.speed) % H;
        const y = ((p.y - yOffset + H) % H);
        const x = p.x + Math.sin(frame * 0.02 + p.phaseOffset) * 30 * p.driftX;
        // Subtle pulse
        const pulse = 1 + Math.sin(frame * 0.05 + p.phaseOffset) * 0.3;

        return (
          <circle
            key={`bgp-${i}`}
            cx={((x % W) + W) % W}
            cy={y}
            r={p.radius * pulse}
            fill={WHITE}
            opacity={p.opacity}
          />
        );
      })}
    </g>
  );
};
