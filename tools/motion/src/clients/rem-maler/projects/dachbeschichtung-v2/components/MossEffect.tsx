// ============================================================
// MossEffect — Scene 3 (frames 250–425)
// Moss spots and lichen patches growing on the roof (3D)
// ============================================================

import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../../utils/easing";
import { MOSS_GREEN, LICHEN_GREEN, SCENES, LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS } from "../constants";
import type { CameraState } from "../projection";
import { surfacePoint } from "../projection";

const appleEase = EASING_PRESETS.appleEase;
const MOSS_COUNT = 20;
const LICHEN_COUNT = 8;
const SCENE = SCENES.moss;

interface MossSpot {
  u: number;
  v: number;
  targetRadius: number;
  delay: number;
}

interface MossEffectProps {
  sceneProgress: number;
  cam: CameraState;
}

export const MossEffect: React.FC<MossEffectProps> = ({ sceneProgress, cam }) => {
  const frame = useCurrentFrame();
  const sceneFrame = frame - SCENE.start;

  const margin = 0.12;

  // --- Moss spots (grid + jitter, spread across full slope) ---
  const mossSpots = useMemo<MossSpot[]>(() => {
    const cols = 5;
    const rows = 4;
    const range = 1 - margin * 2;
    const spots: MossSpot[] = [];
    let idx = 0;
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        if (idx >= MOSS_COUNT) break;
        const baseU = margin + (col + 0.5) / cols * range;
        const baseV = margin + (row + 0.5) / rows * range;
        const jitter = 0.06;
        spots.push({
          u: baseU + (random(`moss-ju-${idx}`) - 0.5) * jitter * 2,
          v: baseV + (random(`moss-jv-${idx}`) - 0.5) * jitter * 2,
          targetRadius: 10 + random(`moss-r-${idx}`) * 14,
          delay: idx * 10 + Math.floor(random(`moss-del-${idx}`) * 10),
        });
        idx++;
      }
    }
    return spots;
  }, []);

  // --- Lichen patches (grid + jitter, spread across slope) ---
  const lichenPatches = useMemo<MossSpot[]>(() => {
    const cols = 4;
    const rows = 2;
    const range = 1 - margin * 2;
    const patches: MossSpot[] = [];
    let idx = 0;
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        if (idx >= LICHEN_COUNT) break;
        const baseU = margin + (col + 0.5) / cols * range;
        const baseV = margin + (row + 0.5) / rows * range;
        const jitter = 0.06;
        patches.push({
          u: baseU + (random(`lichen-ju-${idx}`) - 0.5) * jitter * 2,
          v: baseV + (random(`lichen-jv-${idx}`) - 0.5) * jitter * 2,
          targetRadius: 16 + random(`lichen-r-${idx}`) * 12,
          delay: 30 + idx * 15,
        });
        idx++;
      }
    }
    return patches;
  }, []);

  // --- Scene fade envelope ---
  const fadeIn = interpolate(sceneProgress, [0, 0.08], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  // Pick the most camera-facing slope (largest projected area)
  // Using absolute cross product as proxy for projected area — avoids
  // noise-induced flipping between slopes
  const slopeAreas = [LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS].map((corners) => {
    const p0 = surfacePoint(0.3, 0.3, corners, cam);
    const p1 = surfacePoint(0.7, 0.3, corners, cam);
    const p2 = surfacePoint(0.3, 0.7, corners, cam);
    return Math.abs((p1.x - p0.x) * (p2.y - p0.y) - (p1.y - p0.y) * (p2.x - p0.x));
  });
  const visibleSlopes = slopeAreas[0] > slopeAreas[1]
    ? [LEFT_ROOF_CORNERS]
    : [RIGHT_ROOF_CORNERS];

  return (
    <g opacity={fadeIn}>
      {/* Render moss on the camera-facing slope */}
      {visibleSlopes.map((corners, si) =>
        mossSpots.map((spot, i) => {
          const growStart = spot.delay + si * 20; // slight delay for second slope
          const growEnd = growStart + 50;
          const scale = interpolate(sceneFrame, [growStart, growEnd], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: appleEase,
          });

          if (scale <= 0) return null;

          const p = surfacePoint(spot.u, spot.v, corners, cam);
          const r = spot.targetRadius * scale * (cam.scale / 1.8);

          return (
            <circle
              key={`moss-${si}-${i}`}
              cx={p.x}
              cy={p.y}
              r={r}
              fill={MOSS_GREEN}
              opacity={0.6}
            />
          );
        }),
      )}

      {/* Render lichen on the camera-facing slope */}
      {visibleSlopes.map((corners, si) =>
        lichenPatches.map((patch, i) => {
          const growStart = patch.delay + si * 15;
          const growEnd = growStart + 70;
          const scale = interpolate(sceneFrame, [growStart, growEnd], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: appleEase,
          });

          if (scale <= 0) return null;

          const p = surfacePoint(patch.u, patch.v, corners, cam);
          const r = patch.targetRadius * scale * (cam.scale / 1.8);

          return (
            <circle
              key={`lichen-${si}-${i}`}
              cx={p.x}
              cy={p.y}
              r={r}
              fill={LICHEN_GREEN}
              opacity={0.5}
            />
          );
        }),
      )}
    </g>
  );
};
