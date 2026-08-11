// ============================================================
// REM Dachbeschichtung — Scene 5: Water Beading Effect
// Water droplets hit the coated roof, bead up and slide off,
// demonstrating the hydrophobic coating protection.
// 3D Clay/Toy visual style: rounded forms, radial gradients,
// soft shadows, glossy highlights.
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
  WATER_BLUE,
  WATER_BLUE_LIGHT,
  WHITE,
  CLAY_HIGHLIGHT,
  CLAY_SHADOW,
  CLAY_PARTICLE_SHADOW,
} from "./constants";

interface WaterBeadingProps {
  progress: number;
  localFrame: number;
}

// --- Geometry helpers ---

const W = CANVAS.width;
const H = CANVAS.height;
const rp = roofPixels(W, H);
const pts = rp.points;

// Roof surface boundaries
const ROOF_TOP_Y = pts[0].y;
const ROOF_BOT_Y = pts[2].y;
const ROOF_LEFT_X = pts[0].x;
const ROOF_RIGHT_X = pts[1].x;

// The roof is a parallelogram: bottom edge is shifted right.
// Slope vector from top-left to bottom-left gives the skew direction.
const skewDx = pts[3].x - pts[0].x;
const skewDy = pts[3].y - pts[0].y;

// Given a normalized t along the roof height (0=top, 1=bottom),
// return the X offset added by the parallelogram skew.
function skewOffsetX(t: number): number {
  return skewDx * t;
}

// X range at a given vertical t on the roof surface
function roofXRange(t: number): { min: number; max: number } {
  const topLeftAtT = pts[0].x + skewDx * t;
  const topRightAtT = pts[1].x + (pts[2].x - pts[1].x) * t;
  return { min: topLeftAtT, max: topRightAtT };
}

// --- Rain drop data ---

interface RainDrop {
  id: number;
  startX: number; // top of screen X
  speed: number; // pixels per frame
  delay: number; // frame delay before appearing
  length: number; // elongation (used for ry scaling)
  opacity: number;
}

function generateRainDrops(count: number, seed: string): RainDrop[] {
  const drops: RainDrop[] = [];
  for (let i = 0; i < count; i++) {
    drops.push({
      id: i,
      startX: random(`${seed}-rain-x-${i}`) * W,
      speed: 30 + random(`${seed}-rain-sp-${i}`) * 25,
      delay: Math.floor(random(`${seed}-rain-d-${i}`) * 120),
      length: 40 + random(`${seed}-rain-l-${i}`) * 50,
      opacity: 0.3 + random(`${seed}-rain-o-${i}`) * 0.4,
    });
  }
  return drops;
}

// --- Water bead data ---

interface WaterBead {
  id: number;
  /** Normalized position along roof top edge (0=left, 1=right) */
  surfaceT: number;
  /** Frame when this bead appears */
  appearFrame: number;
  /** Frame when bead starts sliding (after forming) */
  slideFrame: number;
  /** Bead radius */
  radius: number;
  /** Slide speed factor */
  slideSpeed: number;
}

function generateWaterBeads(count: number, seed: string): WaterBead[] {
  const beads: WaterBead[] = [];
  for (let i = 0; i < count; i++) {
    const appear = 8 + Math.floor(random(`${seed}-wb-a-${i}`) * 80);
    beads.push({
      id: i,
      surfaceT: 0.08 + random(`${seed}-wb-t-${i}`) * 0.84,
      appearFrame: appear,
      slideFrame: appear + 15 + Math.floor(random(`${seed}-wb-sf-${i}`) * 20),
      radius: 24 + random(`${seed}-wb-r-${i}`) * 28,
      slideSpeed: 0.003 + random(`${seed}-wb-ss-${i}`) * 0.004,
    });
  }
  return beads;
}

// --- Edge splash data ---

interface EdgeSplash {
  id: number;
  /** X position along the bottom edge */
  x: number;
  /** Frame when splash triggers */
  triggerFrame: number;
  /** Number of splash particles */
  particleCount: number;
}

// --- Component ---

export const WaterBeading: React.FC<WaterBeadingProps> = ({
  progress,
  localFrame,
}) => {
  const seed = "water-beading-s5";

  // Generate deterministic data — reduced counts for clay style
  const rainDrops = useMemo(() => generateRainDrops(30, seed), []);
  const waterBeads = useMemo(() => generateWaterBeads(10, seed), []);

  // Edge splashes triggered when beads reach the bottom
  const edgeSplashes = useMemo<EdgeSplash[]>(() => {
    return waterBeads.map((bead, i) => {
      const xRange = roofXRange(0);
      const baseX =
        xRange.min + bead.surfaceT * (xRange.max - xRange.min) + skewDx;
      return {
        id: i,
        x: baseX,
        triggerFrame:
          bead.slideFrame + Math.floor(60 + random(`${seed}-es-${i}`) * 30),
        particleCount: 3 + Math.floor(random(`${seed}-esp-${i}`) * 3),
      };
    });
  }, [waterBeads]);

  // Specular sweep: moves left to right over the scene duration
  const specSweepX = interpolate(localFrame, [20, 150], [ROOF_LEFT_X - 200, ROOF_RIGHT_X + 400], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: "100%", height: "100%" }}
      >
        <defs>
          {/* Clay raindrop radial gradient (light blue center → dark blue edge) */}
          <radialGradient id="wb-rain-clay-grad" cx="0.5" cy="0.3" r="0.7">
            <stop offset="0" stopColor={WATER_BLUE_LIGHT} stopOpacity="0.85" />
            <stop offset="0.6" stopColor={WATER_BLUE} stopOpacity="0.7" />
            <stop offset="1" stopColor="#2A6FCC" stopOpacity="0.5" />
          </radialGradient>

          {/* Clay bead radial gradient — richer, glossier */}
          <radialGradient id="wb-bead-clay-grad" cx="0.3" cy="0.25" r="0.7">
            <stop offset="0" stopColor={WHITE} stopOpacity="0.95" />
            <stop offset="0.2" stopColor={WATER_BLUE_LIGHT} stopOpacity="0.8" />
            <stop offset="0.6" stopColor={WATER_BLUE} stopOpacity="0.85" />
            <stop offset="1" stopColor="#2A6FCC" stopOpacity="0.9" />
          </radialGradient>

          {/* Splash particle radial gradient */}
          <radialGradient id="wb-splash-clay-grad" cx="0.4" cy="0.35" r="0.65">
            <stop offset="0" stopColor={WHITE} stopOpacity="0.8" />
            <stop offset="0.5" stopColor={WATER_BLUE_LIGHT} stopOpacity="0.6" />
            <stop offset="1" stopColor={WATER_BLUE} stopOpacity="0.3" />
          </radialGradient>

          {/* Specular sweep gradient */}
          <linearGradient
            id="wb-specular-sweep"
            x1={specSweepX - 180}
            y1="0"
            x2={specSweepX + 180}
            y2="0"
            gradientUnits="userSpaceOnUse"
          >
            <stop offset="0" stopColor={WHITE} stopOpacity="0" />
            <stop offset="0.4" stopColor={WHITE} stopOpacity="0.12" />
            <stop offset="0.5" stopColor={WHITE} stopOpacity="0.22" />
            <stop offset="0.6" stopColor={WHITE} stopOpacity="0.12" />
            <stop offset="1" stopColor={WHITE} stopOpacity="0" />
          </linearGradient>

          {/* Clip to roof surface */}
          <clipPath id="wb-roof-clip">
            <polygon
              points={pts.map((p) => `${p.x},${p.y}`).join(" ")}
            />
          </clipPath>

          {/* Splash glow filter — soft round glow for clay particles */}
          <filter id="wb-splash-glow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          {/* Drop shadow filter for beads */}
          <filter id="wb-bead-shadow" x="-20%" y="-20%" width="140%" height="160%">
            <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="rgba(0,0,0,0.25)" />
          </filter>
        </defs>

        {/* ============ RAIN DROPS (clay ellipses) ============ */}
        <g opacity={interpolate(progress, [0, 0.05, 0.85, 1], [0, 0.8, 0.8, 0.3], { extrapolateRight: "clamp" })}>
          {rainDrops.map((drop) => {
            const f = localFrame - drop.delay;
            if (f < 0) return null;

            // Drop falls from above the canvas to below
            const totalTravel = H + 200;
            const rawY = -100 + (f * drop.speed) % totalTravel;
            const y = rawY;

            // Slight wind drift
            const windX = noise2D(`rain-w-${drop.id}`, f * 0.02, 0) * 15;
            const x = drop.startX + windX;

            return (
              <ellipse
                key={`rain-${drop.id}`}
                cx={x}
                cy={y}
                rx={4}
                ry={10}
                fill="url(#wb-rain-clay-grad)"
                opacity={drop.opacity}
              />
            );
          })}
        </g>

        {/* ============ WATER BEADS ON SURFACE (clay style) ============ */}
        <g clipPath="url(#wb-roof-clip)">
          {waterBeads.map((bead) => {
            const f = localFrame - bead.appearFrame;
            if (f < 0) return null;

            // Phase 1: Form on surface (grow from 0 to full radius)
            const formDuration = bead.slideFrame - bead.appearFrame;
            const formProgress = Math.min(f / formDuration, 1);
            const currentRadius = bead.radius * interpolate(
              formProgress,
              [0, 0.6, 1],
              [0, 1.1, 1],
              { extrapolateRight: "clamp" }
            );

            // Phase 2: Slide down the roof slope
            const slideF = localFrame - bead.slideFrame;
            const slideT = slideF > 0 ? slideF * bead.slideSpeed : 0;
            const clampedSlideT = Math.min(slideT, 1);

            // Starting position: on the roof surface, near the top
            const startVertT = 0.1 + random(`${seed}-sv-${bead.id}`) * 0.15;
            const vertT = startVertT + clampedSlideT * (1 - startVertT);

            // X position follows the parallelogram skew as bead slides down
            const xRange = roofXRange(vertT);
            const beadX = xRange.min + bead.surfaceT * (xRange.max - xRange.min);
            const beadY = ROOF_TOP_Y + vertT * (ROOF_BOT_Y - ROOF_TOP_Y);

            // Fade out as bead nears the bottom edge
            const fadeOut = interpolate(vertT, [0.8, 0.98], [1, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });

            // Slight squash when sliding (elongate vertically)
            const squash = slideF > 0 ? 1 + clampedSlideT * 0.3 : 1;

            return (
              <g key={`bead-${bead.id}`} opacity={fadeOut} filter="url(#wb-bead-shadow)">
                {/* Main bead body — clay radial gradient */}
                <ellipse
                  cx={beadX}
                  cy={beadY}
                  rx={currentRadius}
                  ry={currentRadius * squash}
                  fill="url(#wb-bead-clay-grad)"
                />
                {/* Glossy specular highlight — "window" reflection, top-left */}
                <ellipse
                  cx={beadX - currentRadius * 0.3}
                  cy={beadY - currentRadius * 0.3 * squash}
                  rx={currentRadius * 0.35}
                  ry={currentRadius * 0.25 * squash}
                  fill={WHITE}
                  opacity={0.85}
                />
                {/* Smaller secondary specular dot */}
                <ellipse
                  cx={beadX - currentRadius * 0.15}
                  cy={beadY - currentRadius * 0.45 * squash}
                  rx={currentRadius * 0.12}
                  ry={currentRadius * 0.08 * squash}
                  fill={WHITE}
                  opacity={0.6}
                />
                {/* Contact shadow beneath bead */}
                <ellipse
                  cx={beadX}
                  cy={beadY + currentRadius * squash * 0.85}
                  rx={currentRadius * 0.7}
                  ry={currentRadius * 0.15}
                  fill={CLAY_PARTICLE_SHADOW}
                  opacity={0.35}
                />
              </g>
            );
          })}
        </g>

        {/* ============ EDGE SPLASHES (clay round particles with glow) ============ */}
        <g>
          {edgeSplashes.map((splash) => {
            const f = localFrame - splash.triggerFrame;
            if (f < 0 || f > 35) return null;

            const splashProgress = f / 35;
            const splashOpacity = interpolate(
              splashProgress,
              [0, 0.2, 1],
              [0, 0.7, 0],
              { extrapolateRight: "clamp" }
            );

            // Splash origin at the bottom edge of the roof
            const originX = splash.x;
            const originY = ROOF_BOT_Y;

            return (
              <g key={`splash-${splash.id}`} opacity={splashOpacity}>
                {Array.from({ length: splash.particleCount }).map((_, pi) => {
                  const angle =
                    -Math.PI * 0.3 +
                    random(`${seed}-spa-${splash.id}-${pi}`) * -Math.PI * 0.4;
                  const dist =
                    (20 + random(`${seed}-spd-${splash.id}-${pi}`) * 40) *
                    splashProgress;
                  const px = originX + Math.cos(angle) * dist;
                  const py = originY - Math.sin(angle) * dist + splashProgress * 30;
                  const pr =
                    (6 + random(`${seed}-spr-${splash.id}-${pi}`) * 10) *
                    (1 - splashProgress * 0.6);

                  return (
                    <circle
                      key={`sp-${splash.id}-${pi}`}
                      cx={px}
                      cy={py}
                      r={pr}
                      fill="url(#wb-splash-clay-grad)"
                      opacity={0.7}
                      filter="url(#wb-splash-glow)"
                    />
                  );
                })}
                {/* Central splash ring — softer for clay */}
                <circle
                  cx={originX}
                  cy={originY + 10}
                  r={12 + splashProgress * 25}
                  fill="none"
                  stroke={WATER_BLUE_LIGHT}
                  strokeWidth={3}
                  opacity={splashOpacity * 0.4}
                  filter="url(#wb-splash-glow)"
                />
              </g>
            );
          })}
        </g>

        {/* ============ SPECULAR SWEEP ============ */}
        <g clipPath="url(#wb-roof-clip)">
          <polygon
            points={pts.map((p) => `${p.x},${p.y}`).join(" ")}
            fill="url(#wb-specular-sweep)"
            opacity={interpolate(
              localFrame,
              [20, 40, 130, 150],
              [0, 1, 1, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            )}
          />
        </g>
      </svg>
    </AbsoluteFill>
  );
};
