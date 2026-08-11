// ============================================================
// FinaleEffect — Scene 6 (frames 775–925)
// Ambient radial glow + sparkle stars near the roof
// ============================================================

import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../../utils/easing";
import { REM_RED, WHITE, SCENES, LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS } from "../constants";
import type { CameraState } from "../projection";
import { surfacePoint } from "../projection";

const appleEase = EASING_PRESETS.appleEase;
const SPARKLE_COUNT = 3;
const SCENE = SCENES.finale;

interface Sparkle {
  u: number;
  v: number;
  size: number;
  delay: number;
  pulsePhaseOffset: number;
  rotation: number;
}

interface FinaleEffectProps {
  sceneProgress: number;
  cam: CameraState;
  showSparkles?: boolean;
}

/**
 * Build a four-pointed star path centred at (0,0).
 */
function starPath(outer: number): string {
  const inner = outer * 0.3;
  return [
    `M 0 ${-outer}`,
    `L ${inner} 0`,
    `L 0 ${outer}`,
    `L ${-inner} 0`,
    `Z`,
    `M ${-outer} 0`,
    `L 0 ${inner}`,
    `L ${outer} 0`,
    `L 0 ${-inner}`,
    `Z`,
  ].join(" ");
}

export const FinaleEffect: React.FC<FinaleEffectProps> = ({
  sceneProgress,
  cam,
  showSparkles = true,
}) => {
  const frame = useCurrentFrame();
  const sceneFrame = frame - SCENE.start;

  // --- Sparkle stars (grid + large jitter for even but organic spread) ---
  const sparkles = useMemo<Sparkle[]>(() => {
    const margin = 0.12;
    return Array.from({ length: SPARKLE_COUNT }, (_, i) => ({
      u: margin + random(`sparkle-u3-${i}`) * (1 - margin * 2),
      v: margin + random(`sparkle-v3-${i}`) * (1 - margin * 2),
      size: 12 + random(`sparkle-s3-${i}`) * 10,
      delay: 15 + i * 18,
      pulsePhaseOffset: random(`sparkle-ph-${i}`) * Math.PI * 2,
      rotation: random(`sparkle-rot-${i}`) * 90 - 45,
    }));
  }, []);

  const bothSlopes = [LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS];

  // --- Ambient glow fade ---
  const glowOpacity = interpolate(sceneFrame, [0, 60], [0, 0.15], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  return (
    <g>
      {/* Sparkle stars — on both roof slopes */}
      {showSparkles && bothSlopes.map((corners, si) =>
        sparkles.map((sp, i) => {
          const entryStart = sp.delay + si * 10;
          const entryEnd = entryStart + 25;
          const scaleIn = interpolate(sceneFrame, [entryStart, entryEnd], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: appleEase,
          });

          if (scaleIn <= 0) return null;

          const pulse =
            1 + Math.sin(frame * 0.1 + sp.pulsePhaseOffset) * 0.2;
          const totalScale = scaleIn * pulse;
          const d = starPath(sp.size);
          const pos = surfacePoint(sp.u, sp.v, corners, cam);

          return (
            <path
              key={`sparkle-${si}-${i}`}
              d={d}
              fill={WHITE}
              opacity={0.45}
              transform={`translate(${pos.x}, ${pos.y}) rotate(${sp.rotation}) scale(${totalScale})`}
            />
          );
        }),
      )}
    </g>
  );
};
