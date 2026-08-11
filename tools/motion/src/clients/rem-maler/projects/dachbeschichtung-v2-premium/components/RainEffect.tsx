// ============================================================
// RainEffect — Scene 1 (frames 0–125)
// Weather cycle: Rain → Sun → Frost on the roof
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
const FROST_COUNT = 22;
const SCENE = SCENES.weather;

// Phase timing (synced to text stagger: Regen @42, Sonne @54, Frost @66)
const RAIN_FADE_OUT = [48, 64]; // rain fades out as sun appears
const SUN_FADE = [44, 60, 68, 82]; // sun fades in/out (gradual)
const FROST_FADE = [62, 72, 105, 115]; // frost fades in/out

interface RainDrop {
  xNorm: number;
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

interface FrostCrystal {
  u: number;
  v: number;
  size: number;
  rotation: number;
  slope: number; // 0 = left, 1 = right
}

interface RainEffectProps {
  sceneProgress: number;
  cam: CameraState;
}

export const RainEffect: React.FC<RainEffectProps> = ({ sceneProgress, cam }) => {
  const frame = useCurrentFrame();
  const sceneFrame = frame - SCENE.start;

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

  // --- Frost crystals on roof surface ---
  const frostCrystals = useMemo<FrostCrystal[]>(() => {
    const margin = 0.1;
    const range = 1 - margin * 2;
    return Array.from({ length: FROST_COUNT }, (_, i) => ({
      u: margin + random(`frost-u-${i}`) * range,
      v: margin + random(`frost-v-${i}`) * range,
      size: 6 + random(`frost-s-${i}`) * 10,
      rotation: random(`frost-rot-${i}`) * 360,
      slope: random(`frost-sl-${i}`) > 0.5 ? 1 : 0,
    }));
  }, []);

  // --- Phase envelopes ---
  const rainPhase = interpolate(sceneFrame, RAIN_FADE_OUT, [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const sunPhase = interpolate(sceneFrame, SUN_FADE, [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const frostPhase = interpolate(sceneFrame, FROST_FADE, [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- Lightning flash (frame ~38, brief) ---
  const lightningOpacity = interpolate(sceneFrame, [36, 38, 41], [0, 0.06, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- Scene fade envelope ---
  const fadeIn = interpolate(sceneProgress, [0, 0.08], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  // Rain zone
  const RAIN_ZONE = W * 0.35;
  const rainCenterX = cam.cx;
  const fallHeight = H;

  const eaveSamples = [0, 0.25, 0.5, 0.75, 1];
  const roofClipY = Math.max(
    ...eaveSamples.map((v) => surfacePoint(1, v, RIGHT_ROOF_CORNERS, cam).y),
    ...eaveSamples.map((v) => surfacePoint(1, v, LEFT_ROOF_CORNERS, cam).y),
  );

  const scaleFactor = cam.scale / 1.8;

  // Sun glow center (upper-right of the house)
  const sunCenter = surfacePoint(0.5, 0, RIGHT_ROOF_CORNERS, cam);

  return (
    <g opacity={fadeIn}>
      <defs>
        <filter id="sunGlow" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="40" />
        </filter>
        <filter id="frostGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="4" />
        </filter>
        <radialGradient id="sunRadial" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FFB347" stopOpacity="1" />
          <stop offset="50%" stopColor="#FF8C00" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#FF6600" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* === RAIN PHASE === */}
      {rainPhase > 0.01 && (
        <g opacity={rainPhase}>
          {/* Rain lines */}
          {rainDrops.map((drop, i) => {
            const x = rainCenterX + (drop.xNorm - 0.5) * RAIN_ZONE;
            const cycleLength = fallHeight + drop.length;
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

          {/* Splash rings */}
          {splashes.map((sp, i) => {
            const splashCycle = 20;
            const localFrame = (frame + sp.delay) % splashCycle;
            const splashProgress = localFrame / splashCycle;
            const p = surfacePoint(sp.u, sp.v, RIGHT_ROOF_CORNERS, cam);
            const radius = sp.maxRadius * splashProgress * scaleFactor;
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
        </g>
      )}

      {/* Lightning flash (during rain) */}
      {lightningOpacity > 0 && (
        <rect x={0} y={0} width={W} height={H} fill={WHITE} opacity={lightningOpacity} />
      )}

      {/* === SUN PHASE === */}
      {sunPhase > 0.01 && (
        <g opacity={sunPhase}>
          {/* Warm glow on roof */}
          <circle
            cx={sunCenter.x + 200 * scaleFactor}
            cy={sunCenter.y - 300 * scaleFactor}
            r={250 * scaleFactor}
            fill="url(#sunRadial)"
            opacity={0.4}
            filter="url(#sunGlow)"
          />
          {/* Warm color wash over roof */}
          {[LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS].map((corners, si) => {
            const pts = [
              surfacePoint(0, 0, corners, cam),
              surfacePoint(1, 0, corners, cam),
              surfacePoint(1, 1, corners, cam),
              surfacePoint(0, 1, corners, cam),
            ];
            const points = pts.map((p) => `${p.x},${p.y}`).join(" ");
            return (
              <polygon
                key={`sun-wash-${si}`}
                points={points}
                fill="#FFB347"
                opacity={0.12}
              />
            );
          })}
          {/* Heat shimmer lines on roof */}
          {[0.2, 0.4, 0.6, 0.8].map((v, i) => {
            const p1 = surfacePoint(0.1, v, RIGHT_ROOF_CORNERS, cam);
            const p2 = surfacePoint(0.9, v, RIGHT_ROOF_CORNERS, cam);
            const wave = Math.sin(frame * 0.15 + i * 2) * 4 * scaleFactor;
            return (
              <line
                key={`shimmer-${i}`}
                x1={p1.x}
                y1={p1.y + wave}
                x2={p2.x}
                y2={p2.y + wave}
                stroke="#FFB347"
                strokeWidth={1.5 * scaleFactor}
                opacity={0.15 + Math.sin(frame * 0.1 + i) * 0.05}
                strokeDasharray={`${8 * scaleFactor} ${12 * scaleFactor}`}
              />
            );
          })}
        </g>
      )}

      {/* === FROST PHASE === */}
      {frostPhase > 0.01 && (
        <g opacity={frostPhase}>
          {/* Cold blue tint on roof */}
          {[LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS].map((corners, si) => {
            const pts = [
              surfacePoint(0, 0, corners, cam),
              surfacePoint(1, 0, corners, cam),
              surfacePoint(1, 1, corners, cam),
              surfacePoint(0, 1, corners, cam),
            ];
            const points = pts.map((p) => `${p.x},${p.y}`).join(" ");
            return (
              <polygon
                key={`frost-wash-${si}`}
                points={points}
                fill="#A0D4FF"
                opacity={0.1}
              />
            );
          })}
          {/* Frost crystals on roof */}
          {frostCrystals.map((fc, i) => {
            const corners = fc.slope === 0 ? LEFT_ROOF_CORNERS : RIGHT_ROOF_CORNERS;
            const p = surfacePoint(fc.u, fc.v, corners, cam);
            const s = fc.size * scaleFactor;
            // Staggered appear
            const crystalDelay = i * 0.4;
            const crystalOpacity = interpolate(
              sceneFrame,
              [FROST_FADE[0] + crystalDelay, FROST_FADE[0] + crystalDelay + 6],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );
            if (crystalOpacity <= 0.01) return null;
            // 6-point star/crystal shape
            const angle = (fc.rotation * Math.PI) / 180;
            const arms = 3;
            const d = Array.from({ length: arms }, (_, a) => {
              const theta = angle + (a * Math.PI) / arms;
              const x1 = p.x + Math.cos(theta) * s;
              const y1 = p.y + Math.sin(theta) * s;
              const x2 = p.x - Math.cos(theta) * s;
              const y2 = p.y - Math.sin(theta) * s;
              return `M${x1},${y1}L${x2},${y2}`;
            }).join("");

            return (
              <g key={`frost-${i}`} opacity={crystalOpacity * 0.6}>
                <path
                  d={d}
                  stroke="#C8E8FF"
                  strokeWidth={1.5 * scaleFactor}
                  fill="none"
                  filter="url(#frostGlow)"
                />
                <path
                  d={d}
                  stroke={WHITE}
                  strokeWidth={0.8 * scaleFactor}
                  fill="none"
                />
              </g>
            );
          })}
        </g>
      )}
    </g>
  );
};
