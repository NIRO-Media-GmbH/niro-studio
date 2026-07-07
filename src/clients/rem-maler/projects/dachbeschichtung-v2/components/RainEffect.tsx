// ============================================================
// RainEffect — Scene 1 (frames 0–125)
// Rain falling from top of frame onto the roof with splashes
// ============================================================

import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../../utils/easing";
import { W, H, WHITE, SCENES, LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS } from "../constants";
import type { CameraState } from "../projection";
import { surfacePoint } from "../projection";

const appleEase = EASING_PRESETS.appleEase;
const RAIN_COUNT = 35;
const SPLASH_COUNT = 18;
const SCENE = SCENES.weather;

interface RainDrop {
  xNorm: number; // 0–1 offset within rain zone
  speed: number;
  length: number;
  opacity: number;
  phaseOffset: number;
}

interface RoofSplash {
  u: number;
  v: number;
  delay: number;
  maxRadius: number;
}

interface RainEffectProps {
  sceneProgress: number;
  cam: CameraState;
}

export const RainEffect: React.FC<RainEffectProps> = ({ sceneProgress, cam }) => {
  const frame = useCurrentFrame();

  // --- Rain drops (localized around the house) ---
  const rainDrops = useMemo<RainDrop[]>(() => {
    return Array.from({ length: RAIN_COUNT }, (_, i) => ({
      xNorm: random(`rain-x-${i}`),
      speed: 0.7 + random(`rain-speed-${i}`) * 0.9,
      length: 80 + random(`rain-len-${i}`) * 120,
      opacity: 0.15 + random(`rain-op-${i}`) * 0.3,
      phaseOffset: random(`rain-phase-${i}`) * 800,
    }));
  }, []);

  // --- Splash particles on roof surface (parametric UV) ---
  const splashes = useMemo<RoofSplash[]>(() => {
    const margin = 0.08;
    const range = 1 - margin * 2;
    return Array.from({ length: SPLASH_COUNT }, (_, i) => ({
      u: margin + random(`rsplash-u-${i}`) * range,
      v: margin + random(`rsplash-v-${i}`) * range,
      delay: Math.floor(random(`rsplash-del-${i}`) * 22),
      maxRadius: 8 + random(`rsplash-r-${i}`) * 14,
    }));
  }, []);

  // --- Lightning flash (frame ~100, 3 frames) ---
  const lightningOpacity = interpolate(frame, [98, 100, 103], [0, 0.06, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- Scene fade envelope ---
  const fadeIn = interpolate(sceneProgress, [0, 0.08], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  // Rain zone: ~35% of frame width, centered on the house
  const RAIN_ZONE = W * 0.35;
  const rainCenterX = cam.cx;
  const fallHeight = H;

  // Compute roof eave y-level to clip rain at the roof surface
  const eaveSamples = [0, 0.25, 0.5, 0.75, 1];
  const roofClipY = Math.max(
    ...eaveSamples.map((v) => surfacePoint(1, v, RIGHT_ROOF_CORNERS, cam).y),
    ...eaveSamples.map((v) => surfacePoint(1, v, LEFT_ROOF_CORNERS, cam).y),
  );

  return (
    <g opacity={fadeIn}>
      {/* Rain lines — localized over the house */}
      {rainDrops.map((drop, i) => {
        const x = rainCenterX + (drop.xNorm - 0.5) * RAIN_ZONE;
        const cycleLength = fallHeight + drop.length;
        const rawOffset =
          ((frame * drop.speed * 54 + drop.phaseOffset) % cycleLength) -
          drop.length;
        const y1 = rawOffset;
        const y2 = y1 + drop.length;

        // Clip to roof level (rain stops at the roof, not below the house)
        if (y2 < 0 || y1 > roofClipY) return null;
        const clampedY1 = Math.max(y1, 0);
        const clampedY2 = Math.min(y2, roofClipY);

        return (
          <line
            key={`rain-${i}`}
            x1={x}
            y1={clampedY1}
            x2={x}
            y2={clampedY2}
            stroke={WHITE}
            strokeWidth={1.5}
            opacity={drop.opacity}
          />
        );
      })}

      {/* Splash rings on the roof surface */}
      {splashes.map((sp, i) => {
        const splashCycle = 20;
        const localFrame = (frame + sp.delay) % splashCycle;
        const splashProgress = localFrame / splashCycle;

        const p = surfacePoint(sp.u, sp.v, RIGHT_ROOF_CORNERS, cam);
        const scaleFactor = cam.scale / 1.8;
        const radius = sp.maxRadius * splashProgress * scaleFactor;

        // Ring expanding + fading
        const opacity = interpolate(
          splashProgress,
          [0, 0.15, 0.5, 1],
          [0, 0.5, 0.25, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );

        if (opacity <= 0) return null;

        return (
          <circle
            key={`splash-${i}`}
            cx={p.x}
            cy={p.y}
            r={radius}
            fill="none"
            stroke={WHITE}
            strokeWidth={1.5 * scaleFactor}
            opacity={opacity}
          />
        );
      })}

      {/* Lightning flash */}
      {lightningOpacity > 0 && (
        <rect
          x={0}
          y={0}
          width={W}
          height={H}
          fill={WHITE}
          opacity={lightningOpacity}
        />
      )}
    </g>
  );
};
