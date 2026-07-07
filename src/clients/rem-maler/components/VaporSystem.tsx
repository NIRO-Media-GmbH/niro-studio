// ============================================================
// REM Dachbeschichtung — Scene 5: Vapor / Breathability System
// Rising steam/vapor columns from the coated roof surface,
// demonstrating that the coating is breathable (dampfdurchlaessig).
// 3D Clay/Toy visual style: larger rounded particles, radial
// gradients, stronger blur, soft glows.
// ============================================================

import React, { useMemo } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  random,
  interpolate,
} from "remotion";
import { noise2D } from "@remotion/noise";
import {
  CANVAS,
  FPS,
  ROOF,
  roofPixels,
  WHITE,
  CLAY_HIGHLIGHT,
  CLAY_SHADOW,
  CLAY_PARTICLE_SHADOW,
} from "./constants";

interface VaporSystemProps {
  progress: number;
  localFrame: number;
}

// --- Geometry ---

const W = CANVAS.width;
const H = CANVAS.height;
const rp = roofPixels(W, H);
const pts = rp.points;

const ROOF_TOP_Y = pts[0].y;
const ROOF_BOT_Y = pts[2].y;

// The roof parallelogram skew
const skewDx = pts[3].x - pts[0].x;

// Get the X range at a given vertical ratio (0=top edge, 1=bottom edge)
function roofXRange(vt: number): { min: number; max: number } {
  const leftX = pts[0].x + skewDx * vt;
  const rightX = pts[1].x + (pts[2].x - pts[1].x) * vt;
  return { min: leftX, max: rightX };
}

// --- Vapor column data ---

interface VaporColumn {
  id: number;
  /** Normalized horizontal position along the roof (0=left, 1=right) */
  surfaceT: number;
  /** Vertical ratio on roof surface where column originates (0=top, 1=bottom) */
  originVt: number;
  /** Frame when this column starts emitting */
  startFrame: number;
  /** Number of particles in this column */
  particleCount: number;
  /** Base drift seed for Perlin noise */
  noiseSeed: number;
}

interface VaporParticle {
  id: number;
  /** Delay from column start (frames) */
  delay: number;
  /** Rising speed in pixels per frame */
  speed: number;
  /** Base radius */
  radius: number;
  /** Max opacity at source */
  maxOpacity: number;
  /** Horizontal offset from column center */
  offsetX: number;
}

function generateColumns(count: number, seed: string): VaporColumn[] {
  const columns: VaporColumn[] = [];
  for (let i = 0; i < count; i++) {
    columns.push({
      id: i,
      surfaceT: 0.1 + (i / (count - 1)) * 0.8, // evenly spread with padding
      originVt: 0.3 + random(`${seed}-ov-${i}`) * 0.35, // mid-roof area
      startFrame: Math.floor(random(`${seed}-sf-${i}`) * 55), // stagger over first ~55 frames
      particleCount: 6 + Math.floor(random(`${seed}-pc-${i}`) * 3), // 6-8 particles (clay: fewer but bigger)
      noiseSeed: random(`${seed}-ns-${i}`) * 1000,
    });
  }
  return columns;
}

function generateParticles(
  column: VaporColumn,
  seed: string
): VaporParticle[] {
  const particles: VaporParticle[] = [];
  for (let i = 0; i < column.particleCount; i++) {
    particles.push({
      id: i,
      delay: Math.floor(random(`${seed}-pd-${column.id}-${i}`) * 50),
      speed: 1.8 + random(`${seed}-ps-${column.id}-${i}`) * 2.2,
      radius: (15 + random(`${seed}-pr-${column.id}-${i}`) * 15) * 1.6, // 60% larger for clay
      maxOpacity: 0.1 + random(`${seed}-po-${column.id}-${i}`) * 0.2,
      offsetX: (random(`${seed}-px-${column.id}-${i}`) - 0.5) * 40,
    });
  }
  return particles;
}

// --- Component ---

export const VaporSystem: React.FC<VaporSystemProps> = ({
  progress,
  localFrame,
}) => {
  const seed = "vapor-sys-s5";

  const columns = useMemo(() => generateColumns(6, seed), []);

  const columnParticles = useMemo(
    () => columns.map((col) => generateParticles(col, seed)),
    [columns]
  );

  // Max rise distance: from roof surface up to ~200px above the roof top
  const maxRiseDistance = (ROOF_BOT_Y - ROOF_TOP_Y) * 0.5 + 200;

  // Overall system opacity fades in and out with scene
  const systemOpacity = interpolate(
    progress,
    [0, 0.08, 0.85, 1],
    [0, 1, 1, 0.2],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: "100%", height: "100%" }}
      >
        <defs>
          {/* Clay vapor radial gradient: white center → transparent edge */}
          <radialGradient id="vapor-clay-grad" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0%" stopColor={WHITE} stopOpacity="0.9" />
            <stop offset="30%" stopColor={WHITE} stopOpacity="0.5" />
            <stop offset="70%" stopColor={WHITE} stopOpacity="0.15" />
            <stop offset="100%" stopColor={WHITE} stopOpacity="0" />
          </radialGradient>

          {/* Emission glow gradient — larger, softer for clay */}
          <radialGradient id="vapor-emission-grad" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0%" stopColor={WHITE} stopOpacity="0.6" />
            <stop offset="50%" stopColor={WHITE} stopOpacity="0.2" />
            <stop offset="100%" stopColor={WHITE} stopOpacity="0" />
          </radialGradient>

          {/* Stronger blur filter for clay vapor (stdDeviation 25) */}
          <filter id="vapor-clay-glow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="25" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          {/* Emission glow filter — extra soft */}
          <filter id="vapor-emission-filter" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="18" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <g opacity={systemOpacity}>
          {columns.map((column, ci) => {
            // Column appearance fade-in
            const colFrame = localFrame - column.startFrame;
            if (colFrame < 0) return null;

            const colFadeIn = interpolate(colFrame, [0, 25], [0, 1], {
              extrapolateRight: "clamp",
            });

            // Column origin on the roof surface
            const xRange = roofXRange(column.originVt);
            const originX =
              xRange.min + column.surfaceT * (xRange.max - xRange.min);
            const originY =
              ROOF_TOP_Y + column.originVt * (ROOF_BOT_Y - ROOF_TOP_Y);

            return (
              <g key={`col-${column.id}`} opacity={colFadeIn}>
                {columnParticles[ci].map((particle) => {
                  const pf = colFrame - particle.delay;
                  if (pf < 0) return null;

                  // Particle rises continuously, looping when it exceeds max distance
                  const rawRise = pf * particle.speed;
                  const cycleLen = maxRiseDistance + 60;
                  const riseInCycle = rawRise % cycleLen;
                  const riseT = Math.min(riseInCycle / maxRiseDistance, 1);

                  // Current Y: rises upward from origin
                  const py = originY - riseInCycle;

                  // Perlin noise horizontal drift
                  const noiseFreq = 0.012;
                  const drift =
                    noise2D(
                      `vp-${column.noiseSeed}-${particle.id}`,
                      pf * noiseFreq,
                      particle.id * 0.3
                    ) * 60;

                  const px = originX + particle.offsetX + drift;

                  // Particle grows slightly as it rises
                  const currentRadius =
                    particle.radius * (1 + riseT * 0.5);

                  // Opacity: fades out as particle rises further from roof
                  const distanceOpacity = interpolate(
                    riseT,
                    [0, 0.15, 0.7, 1],
                    [0, 1, 0.4, 0],
                    { extrapolateRight: "clamp" }
                  );

                  const finalOpacity =
                    particle.maxOpacity * distanceOpacity;

                  if (finalOpacity < 0.01) return null;

                  return (
                    <circle
                      key={`vp-${column.id}-${particle.id}`}
                      cx={px}
                      cy={py}
                      r={currentRadius}
                      fill="url(#vapor-clay-grad)"
                      opacity={finalOpacity}
                      filter="url(#vapor-clay-glow)"
                    />
                  );
                })}

                {/* Emission glow at column base — larger and softer for clay */}
                <ellipse
                  cx={originX}
                  cy={originY}
                  rx={48}
                  ry={16}
                  fill="url(#vapor-emission-grad)"
                  opacity={
                    colFadeIn *
                    0.2 *
                    (0.8 + 0.2 * Math.sin(localFrame * 0.08 + column.id))
                  }
                  filter="url(#vapor-emission-filter)"
                />
              </g>
            );
          })}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
