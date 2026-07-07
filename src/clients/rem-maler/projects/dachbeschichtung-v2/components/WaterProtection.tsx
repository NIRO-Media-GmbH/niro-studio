// ============================================================
// WaterProtection — Scene 5 (frames 600–775)
// Localized rain, water beads sliding off coated roof, vapor wisps
// ============================================================

import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../../utils/easing";
import { W, H, WHITE, WATER_BLUE, SCENES, LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS } from "../constants";
import type { CameraState } from "../projection";
import { surfacePoint } from "../projection";

const appleEase = EASING_PRESETS.appleEase;
const accelerate = EASING_PRESETS.accelerate;
const RAIN_COUNT = 30;
const BEAD_COUNT = 12;
const VAPOR_COUNT = 8;
const SCENE = SCENES.water;

interface RainDrop {
  xNorm: number;
  speed: number;
  length: number;
  opacity: number;
  phaseOffset: number;
}

interface WaterBead {
  u: number;
  v: number;
  maxRadius: number;
  delay: number;
  slope: number; // 0 = left, 1 = right
}

interface VaporWisp {
  u: number;
  v: number;
  delay: number;
  slope: number;
}

interface WaterProtectionProps {
  sceneProgress: number;
  cam: CameraState;
}

export const WaterProtection: React.FC<WaterProtectionProps> = ({
  sceneProgress,
  cam,
}) => {
  const frame = useCurrentFrame();
  const sceneFrame = frame - SCENE.start;

  // --- Rain drops (localized over house, same as Scene 1) ---
  const rainDrops = useMemo<RainDrop[]>(() => {
    return Array.from({ length: RAIN_COUNT }, (_, i) => ({
      xNorm: random(`wrain-x-${i}`),
      speed: 0.7 + random(`wrain-sp-${i}`) * 0.9,
      length: 80 + random(`wrain-len-${i}`) * 120,
      opacity: 0.15 + random(`wrain-op-${i}`) * 0.3,
      phaseOffset: random(`wrain-ph-${i}`) * 800,
    }));
  }, []);

  // --- Water beads on both slopes ---
  const waterBeads = useMemo<WaterBead[]>(() => {
    const margin = 0.12;
    return Array.from({ length: BEAD_COUNT }, (_, i) => ({
      u: margin + random(`bead-u-${i}`) * (1 - margin * 2),
      v: margin + random(`bead-v-${i}`) * 0.5,
      maxRadius: 8 + random(`bead-r-${i}`) * 10,
      delay: 10 + i * 8,
      slope: i < BEAD_COUNT / 2 ? 0 : 1,
    }));
  }, []);

  // --- Vapor wisps on both slopes ---
  const vaporWisps = useMemo<VaporWisp[]>(() => {
    const margin = 0.15;
    return Array.from({ length: VAPOR_COUNT }, (_, i) => ({
      u: margin + random(`vapor-u-${i}`) * (1 - margin * 2),
      v: margin + random(`vapor-v-${i}`) * 0.6,
      delay: 20 + Math.floor(random(`vapor-del-${i}`) * 30),
      slope: i < VAPOR_COUNT / 2 ? 0 : 1,
    }));
  }, []);

  const fadeIn = interpolate(sceneProgress, [0, 0.08], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  // Rain zone: localized over the house
  const RAIN_ZONE = W * 0.35;
  const rainCenterX = cam.cx;

  // Roof eave y-level to clip rain
  const eaveSamples = [0, 0.25, 0.5, 0.75, 1];
  const roofClipY = Math.max(
    ...eaveSamples.map((v) => surfacePoint(1, v, RIGHT_ROOF_CORNERS, cam).y),
    ...eaveSamples.map((v) => surfacePoint(1, v, LEFT_ROOF_CORNERS, cam).y),
  );

  // Pick camera-facing slope (largest projected area — stable, no flicker)
  const slopeAreas = [LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS].map((corners) => {
    const p0 = surfacePoint(0.3, 0.3, corners, cam);
    const p1 = surfacePoint(0.7, 0.3, corners, cam);
    const p2 = surfacePoint(0.3, 0.7, corners, cam);
    return Math.abs((p1.x - p0.x) * (p2.y - p0.y) - (p1.y - p0.y) * (p2.x - p0.x));
  });
  const visibleCorners = slopeAreas[0] > slopeAreas[1] ? LEFT_ROOF_CORNERS : RIGHT_ROOF_CORNERS;

  return (
    <g opacity={fadeIn}>
      <defs>
        <filter id="vaporBlur" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation={8} />
        </filter>
        <filter id="beadGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation={3} />
        </filter>
      </defs>

      {/* Rain lines — localized over the house, clipped at roof */}
      {rainDrops.map((drop, i) => {
        const x = rainCenterX + (drop.xNorm - 0.5) * RAIN_ZONE;
        const cycleLength = H + drop.length;
        const rawOffset =
          ((frame * drop.speed * 54 + drop.phaseOffset) % cycleLength) -
          drop.length;
        const y1 = rawOffset;
        const y2 = y1 + drop.length;

        if (y2 < 0 || y1 > roofClipY) return null;
        const clampedY1 = Math.max(y1, 0);
        const clampedY2 = Math.min(y2, roofClipY);

        return (
          <line
            key={`wrain-${i}`}
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

      {/* Splash rings on roof (same as Scene 1) */}
      {waterBeads.slice(0, 8).map((bead, i) => {
        const corners = visibleCorners;
        const splashCycle = 22;
        const localFrame = (frame + bead.delay) % splashCycle;
        const splashProgress = localFrame / splashCycle;
        const p = surfacePoint(bead.u, bead.v, corners, cam);
        const scaleFactor = cam.scale / 1.8;
        const radius = 12 * splashProgress * scaleFactor;
        const opacity = interpolate(
          splashProgress,
          [0, 0.15, 0.5, 1],
          [0, 0.4, 0.2, 0],
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

      {/* Water beads forming and sliding off */}
      {waterBeads.map((bead, i) => {
        const corners = visibleCorners;
        const growStart = bead.delay;
        const growEnd = growStart + 25;
        const slideStart = growEnd;
        const slideEnd = slideStart + 35;

        const growProgress = interpolate(sceneFrame, [growStart, growEnd], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: appleEase,
        });

        if (growProgress <= 0) return null;

        const slideProgress = interpolate(sceneFrame, [slideStart, slideEnd], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: accelerate,
        });

        const currentV = bead.v + slideProgress * 0.5;
        const p = surfacePoint(bead.u, Math.min(currentV, 0.95), corners, cam);

        const currentR = bead.maxRadius * growProgress * (cam.scale / 1.8);
        const opacity = interpolate(slideProgress, [0, 0.6, 1], [0.6, 0.5, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        const highlightR = currentR * 0.3;

        return (
          <g key={`bead-${i}`} opacity={opacity}>
            {/* Bead glow */}
            <circle cx={p.x} cy={p.y} r={currentR * 1.5} fill={WATER_BLUE} opacity={0.2} filter="url(#beadGlow)" />
            {/* Bead body */}
            <circle cx={p.x} cy={p.y} r={currentR} fill={WATER_BLUE} opacity={0.7} />
            {/* Highlight */}
            <circle
              cx={p.x - currentR * 0.25}
              cy={p.y - currentR * 0.25}
              r={highlightR}
              fill={WHITE}
              opacity={0.7}
            />
          </g>
        );
      })}

      {/* Vapor wisps rising from roof — breathability */}
      {vaporWisps.map((wisp, i) => {
        const corners = visibleCorners;
        const cycleDuration = 90;
        const localFrame = (sceneFrame - wisp.delay + cycleDuration * 10) % cycleDuration;
        const vaporProgress = localFrame / cycleDuration;

        if (sceneFrame < wisp.delay) return null;

        const p = surfacePoint(wisp.u, wisp.v, corners, cam);
        const rise = vaporProgress * 180;
        const y = p.y - rise;
        const opacity = interpolate(
          vaporProgress,
          [0, 0.1, 0.5, 1],
          [0, 0.2, 0.15, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );

        const scaleFactor = cam.scale / 1.8;
        const rx = (20 + vaporProgress * 15) * scaleFactor;
        const ry = (10 + vaporProgress * 8) * scaleFactor;

        return (
          <ellipse
            key={`vapor-${i}`}
            cx={p.x + Math.sin(vaporProgress * Math.PI * 2 + i) * 15}
            cy={y}
            rx={rx}
            ry={ry}
            fill={WHITE}
            opacity={opacity}
            filter="url(#vaporBlur)"
          />
        );
      })}
    </g>
  );
};
