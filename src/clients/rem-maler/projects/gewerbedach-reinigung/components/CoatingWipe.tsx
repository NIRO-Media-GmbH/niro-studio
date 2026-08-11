// ============================================================
// CoatingWipe — Scene 4 (frames 425–600)
// Satisfying coating wipe with glow, sparkles, and shine sweep
// ============================================================

import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { REM_RED, WHITE, LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS } from "../constants";
import type { CameraState } from "../projection";
import { surfacePoint } from "../projection";

const GLOW_PARTICLE_COUNT = 12;
const SPARKLE_TRAIL_COUNT = 16;

interface GlowParticle {
  v: number;
  radius: number;
  phaseOffset: number;
  driftU: number;
}

interface SparkleTrail {
  v: number;
  uOffset: number; // behind the wipe edge
  radius: number;
  delay: number;
}

interface CoatingWipeProps {
  coatingProgress: number;
  cam: CameraState;
}

export const CoatingWipe: React.FC<CoatingWipeProps> = ({
  coatingProgress,
  cam,
}) => {
  const frame = useCurrentFrame();

  // Glow particles along the wipe edge
  const glowParticles = useMemo<GlowParticle[]>(() => {
    return Array.from({ length: GLOW_PARTICLE_COUNT }, (_, i) => ({
      v: 0.05 + random(`glow-v-${i}`) * 0.9,
      radius: 6 + random(`glow-r-${i}`) * 10,
      phaseOffset: random(`glow-ph-${i}`) * Math.PI * 2,
      driftU: (random(`glow-du-${i}`) - 0.5) * 0.04,
    }));
  }, []);

  // Sparkle trail — small bright dots that appear behind the wipe and fade
  const sparkleTrail = useMemo<SparkleTrail[]>(() => {
    return Array.from({ length: SPARKLE_TRAIL_COUNT }, (_, i) => ({
      v: 0.08 + random(`spark-v-${i}`) * 0.84,
      uOffset: random(`spark-uo-${i}`) * 0.15 + 0.02,
      radius: 2 + random(`spark-r-${i}`) * 4,
      delay: Math.floor(random(`spark-del-${i}`) * 30),
    }));
  }, []);

  if (coatingProgress <= 0) return null;

  // Smooth fade in/out at edges of the wipe
  const edgeFade = interpolate(coatingProgress, [0, 0.05, 0.85, 1], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  if (edgeFade <= 0.01) return null;

  const scaleFactor = cam.scale / 1.8;
  const bothSlopes = [LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS];

  return (
    <g opacity={edgeFade}>
      <defs>
        <filter id="wipeGlowFx" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="8" />
        </filter>
        <filter id="sparkleGlow" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="3" />
        </filter>
      </defs>

      {/* Wipe edge glow lines on both slopes */}
      {bothSlopes.map((corners, si) => {
        const top = surfacePoint(coatingProgress, 0.02, corners, cam);
        const bottom = surfacePoint(coatingProgress, 0.98, corners, cam);
        return (
          <React.Fragment key={`wipe-line-${si}`}>
            {/* Broad soft glow */}
            <line
              x1={top.x}
              y1={top.y}
              x2={bottom.x}
              y2={bottom.y}
              stroke={REM_RED}
              strokeWidth={12 * scaleFactor}
              opacity={0.3}
              filter="url(#wipeGlowFx)"
            />
            {/* Bright core line */}
            <line
              x1={top.x}
              y1={top.y}
              x2={bottom.x}
              y2={bottom.y}
              stroke={WHITE}
              strokeWidth={3 * scaleFactor}
              opacity={0.7}
              filter="url(#sparkleGlow)"
            />
            {/* Sharp edge line */}
            <line
              x1={top.x}
              y1={top.y}
              x2={bottom.x}
              y2={bottom.y}
              stroke={WHITE}
              strokeWidth={1.5 * scaleFactor}
              opacity={0.9}
            />
          </React.Fragment>
        );
      })}

      {/* Glow particles along wipe edge — both slopes */}
      {bothSlopes.map((corners, si) =>
        glowParticles.map((p, i) => {
          const u = Math.max(0, Math.min(1, coatingProgress + p.driftU));
          const pos = surfacePoint(u, p.v, corners, cam);

          const pulsePhase = (frame * 0.2 + p.phaseOffset) % (Math.PI * 2);
          const opacity = 0.3 + Math.sin(pulsePhase) * 0.2;

          return (
            <circle
              key={`glow-${si}-${i}`}
              cx={pos.x}
              cy={pos.y}
              r={p.radius * scaleFactor}
              fill={WHITE}
              opacity={Math.max(0, opacity)}
              filter="url(#sparkleGlow)"
            />
          );
        }),
      )}

      {/* Sparkle trail — bright dots behind the wipe edge */}
      {bothSlopes.map((corners, si) =>
        sparkleTrail.map((sp, i) => {
          const trailU = coatingProgress - sp.uOffset;
          if (trailU < 0) return null;

          const pos = surfacePoint(trailU, sp.v, corners, cam);

          // Sparkles twinkle based on frame
          const twinkle = Math.sin((frame + sp.delay) * 0.4 + i * 1.7);
          const opacity = interpolate(twinkle, [-1, 0, 1], [0, 0.2, 0.7], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          if (opacity <= 0.05) return null;

          return (
            <circle
              key={`spark-${si}-${i}`}
              cx={pos.x}
              cy={pos.y}
              r={sp.radius * scaleFactor}
              fill={WHITE}
              opacity={opacity}
            />
          );
        }),
      )}

      {/* Shine sweep — a bright highlight that follows the wipe */}
      {bothSlopes.map((corners, si) => {
        const sweepU = coatingProgress - 0.08;
        if (sweepU < 0) return null;

        const samples = [0.1, 0.3, 0.5, 0.7, 0.9];
        const points = samples.map((v) => surfacePoint(sweepU, v, corners, cam));
        const d = points
          .map((p, j) => `${j === 0 ? "M" : "L"} ${Math.round(p.x)} ${Math.round(p.y)}`)
          .join(" ");

        return (
          <path
            key={`shine-${si}`}
            d={d}
            fill="none"
            stroke={WHITE}
            strokeWidth={4 * scaleFactor}
            opacity={0.15}
            filter="url(#wipeGlowFx)"
            strokeLinecap="round"
          />
        );
      })}
    </g>
  );
};
