// ============================================================
// REM Dachbeschichtung — Scene 6: Sparkle Stars & Finale Glow
// Shimmering stars, floating light orbs, lens flare, and
// crescendo glow for the finale scene.
// 3D Clay/Toy visual style: thicker stars, larger orbs with
// drop shadows, wider lens flare, stronger crescendo.
// ============================================================

import React, { useMemo } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  random,
  interpolate,
  spring,
} from "remotion";
import { noise2D } from "@remotion/noise";
import {
  CANVAS,
  FPS,
  ROOF,
  roofPixels,
  RED,
  RED_LIGHT,
  WHITE,
  CLAY_HIGHLIGHT,
  CLAY_SHADOW,
  CLAY_PARTICLE_SHADOW,
} from "./constants";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface SparkleStarsProps {
  progress: number;
  localFrame: number;
}

interface StarDef {
  cx: number;
  cy: number;
  longRadius: number;
  shortRadius: number;
  appearFrame: number;
  seed: string;
}

interface OrbDef {
  cx: number;
  cy: number;
  radius: number;
  seed: string;
  speed: number;
  opacity: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const roof = roofPixels(CANVAS.width, CANVAS.height);
const roofMinX = Math.min(...roof.points.map((p) => p.x));
const roofMaxX = Math.max(...roof.points.map((p) => p.x));
const roofMinY = Math.min(...roof.points.map((p) => p.y));
const roofMaxY = Math.max(...roof.points.map((p) => p.y));
const roofCenterY = (roofMinY + roofMaxY) / 2;

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

/** Build a 4-pointed star SVG path: M 0,-R L w,0 L 0,R L -w,0 Z */
function starPath(longR: number, shortR: number): string {
  return [
    `M 0,${-longR}`,
    `L ${shortR},0`,
    `L 0,${longR}`,
    `L ${-shortR},0`,
    `Z`,
  ].join(" ");
}

// ---------------------------------------------------------------------------
// Star definitions (7 stars spread across the roof)
// ---------------------------------------------------------------------------
const STAR_COUNT = 7;
const STAR_DEFS: StarDef[] = (() => {
  const stars: StarDef[] = [];
  const rangeX = roofMaxX - roofMinX;
  const rangeY = roofMaxY - roofMinY;

  for (let i = 0; i < STAR_COUNT; i++) {
    const t = i / (STAR_COUNT - 1);
    const cx = roofMinX + rangeX * (0.08 + t * 0.84);
    const cy =
      roofMinY +
      rangeY * (0.15 + random(`star-y-${i}`) * 0.7);
    const longRadius = 28 + random(`star-lr-${i}`) * 22;
    const shortRadius = longRadius * (0.2 + random(`star-sr-${i}`) * 0.15);

    stars.push({
      cx,
      cy,
      longRadius,
      shortRadius,
      appearFrame: i * 18,
      seed: `star-${i}`,
    });
  }
  return stars;
})();

// ---------------------------------------------------------------------------
// Light orb definitions (8 orbs — larger for clay: 80-160px)
// ---------------------------------------------------------------------------
const ORB_COUNT = 8;
const ORB_DEFS: OrbDef[] = (() => {
  const orbs: OrbDef[] = [];
  for (let i = 0; i < ORB_COUNT; i++) {
    orbs.push({
      cx:
        roofMinX -
        200 +
        random(`orb-x-${i}`) * (roofMaxX - roofMinX + 400),
      cy:
        roofMinY -
        300 +
        random(`orb-y-${i}`) * (roofMaxY - roofMinY + 600),
      radius: 80 + random(`orb-r-${i}`) * 80, // clay: 80-160px (was 40-80)
      seed: `orb-${i}`,
      speed: 0.3 + random(`orb-sp-${i}`) * 0.7,
      opacity: 0.15 + random(`orb-op-${i}`) * 0.2,
    });
  }
  return orbs;
})();

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Single four-pointed sparkle star with spring-in, pulsing glow, and clay thickness */
const SparkleStar: React.FC<{
  def: StarDef;
  localFrame: number;
}> = ({ def, localFrame }) => {
  const adjustedFrame = localFrame - def.appearFrame;
  if (adjustedFrame < 0) return null;

  // Spring-in scale
  const scaleSpring = spring({
    frame: adjustedFrame,
    fps: FPS,
    config: { damping: 10, stiffness: 160 },
  });

  // Gentle pulsing after appearing (scale oscillates 0.85 -> 1.15)
  const pulse =
    1 + Math.sin(adjustedFrame * 0.12 + random(def.seed) * Math.PI * 2) * 0.15;
  const scale = scaleSpring * pulse;

  // Rotation wobble for life
  const rotation =
    noise2D(def.seed, adjustedFrame * 0.02, 0) * 15;

  // Glow opacity pulses
  const glowOpacity = interpolate(
    Math.sin(adjustedFrame * 0.1 + random(`${def.seed}-glow`) * 6),
    [-1, 1],
    [0.4, 0.9],
  );

  const d = starPath(def.longRadius, def.shortRadius);

  return (
    <g
      transform={`translate(${def.cx}, ${def.cy}) rotate(${rotation}) scale(${scale})`}
    >
      {/* Outer glow — clay: bigger glow */}
      <path
        d={starPath(def.longRadius * 1.8, def.shortRadius * 1.8)}
        fill={WHITE}
        opacity={glowOpacity * 0.25}
        filter="url(#starGlowClay)"
      />
      {/* Main star — clay: thicker stroke for rounded feel */}
      <path
        d={d}
        fill={WHITE}
        opacity={glowOpacity}
        stroke={WHITE}
        strokeWidth={5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {/* Inner bright core */}
      <circle
        cx={0}
        cy={0}
        r={def.shortRadius * 0.7}
        fill={WHITE}
        opacity={glowOpacity * 0.9}
      />
    </g>
  );
};

/** Soft glowing light orb that drifts with noise — clay: larger with drop shadow */
const LightOrb: React.FC<{
  def: OrbDef;
  localFrame: number;
  progress: number;
}> = ({ def, localFrame, progress }) => {
  // Fade in over first 40 frames
  const fadeIn = clamp(localFrame / 40, 0, 1);

  // Drift via noise
  const driftX = noise2D(def.seed, localFrame * 0.008 * def.speed, 0) * 80;
  const driftY = noise2D(def.seed, 0, localFrame * 0.006 * def.speed) * 60;

  const x = def.cx + driftX;
  const y = def.cy + driftY;

  // Opacity pulses gently
  const pulse =
    1 + Math.sin(localFrame * 0.05 + random(def.seed) * Math.PI * 2) * 0.3;
  const opacity = def.opacity * fadeIn * pulse;

  return (
    <g filter="url(#orbDropShadow)">
      <circle
        cx={x}
        cy={y}
        r={def.radius}
        fill="url(#orbGradientClay)"
        opacity={opacity}
      />
    </g>
  );
};

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------
export const SparkleStars: React.FC<SparkleStarsProps> = ({
  progress,
  localFrame,
}) => {
  // Scene 6 runs 150 frames total
  const SCENE_DUR = 150;

  // Lens flare: fades in during last 60 frames
  const flareFadeStart = SCENE_DUR - 60;
  const flareOpacity = interpolate(
    localFrame,
    [flareFadeStart, SCENE_DUR - 10],
    [0, 0.6],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // Crescendo glow: overall warm tint that grows across the scene — clay: stronger
  const crescendoOpacity = interpolate(
    localFrame,
    [0, SCENE_DUR],
    [0, 0.14],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill>
      {/* SVG layer: stars, orbs, lens flare */}
      <svg
        viewBox={`0 0 ${CANVAS.width} ${CANVAS.height}`}
        width={CANVAS.width}
        height={CANVAS.height}
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        <defs>
          {/* Glow filter for stars — clay: bigger stdDeviation (was 18, now 24) */}
          <filter id="starGlowClay" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="24" />
          </filter>

          {/* Radial gradient for light orbs — clay: more intense */}
          <radialGradient id="orbGradientClay" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={WHITE} stopOpacity={0.95} />
            <stop offset="25%" stopColor={WHITE} stopOpacity={0.6} />
            <stop offset="60%" stopColor={WHITE} stopOpacity={0.2} />
            <stop offset="100%" stopColor={WHITE} stopOpacity={0} />
          </radialGradient>

          {/* Subtle drop shadow for orbs */}
          <filter id="orbDropShadow" x="-30%" y="-30%" width="160%" height="170%">
            <feDropShadow dx="0" dy="6" stdDeviation="10" floodColor={CLAY_PARTICLE_SHADOW} floodOpacity="0.4" />
          </filter>

          {/* Horizontal gradient for lens flare — clay: wider, softer edges */}
          <linearGradient id="flareGradientClay" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={WHITE} stopOpacity={0} />
            <stop offset="15%" stopColor={WHITE} stopOpacity={0.15} />
            <stop offset="35%" stopColor={WHITE} stopOpacity={0.4} />
            <stop offset="50%" stopColor={WHITE} stopOpacity={1} />
            <stop offset="65%" stopColor={WHITE} stopOpacity={0.4} />
            <stop offset="85%" stopColor={WHITE} stopOpacity={0.15} />
            <stop offset="100%" stopColor={WHITE} stopOpacity={0} />
          </linearGradient>

          {/* Lens flare vertical glow */}
          <filter id="flareGlow" x="-10%" y="-200%" width="120%" height="500%">
            <feGaussianBlur stdDeviation="4 20" />
          </filter>
        </defs>

        {/* Light orbs (behind stars) — clay: larger with shadow */}
        {ORB_DEFS.map((orb, i) => (
          <LightOrb
            key={`orb-${i}`}
            def={orb}
            localFrame={localFrame}
            progress={progress}
          />
        ))}

        {/* Sparkle stars — clay: thicker strokes, bigger glow */}
        {STAR_DEFS.map((star, i) => (
          <SparkleStar key={`star-${i}`} def={star} localFrame={localFrame} />
        ))}

        {/* Lens flare — horizontal streak across the roof center, clay: wider (300px) with softer edges */}
        {flareOpacity > 0 && (
          <g>
            {/* Main flare bar — wider */}
            <rect
              x={0}
              y={roofCenterY - 3}
              width={CANVAS.width}
              height={6}
              fill="url(#flareGradientClay)"
              opacity={flareOpacity}
            />
            {/* Soft vertical glow around flare for clay depth */}
            <rect
              x={0}
              y={roofCenterY - 150}
              width={CANVAS.width}
              height={300}
              fill="url(#flareGradientClay)"
              opacity={flareOpacity * 0.15}
              filter="url(#flareGlow)"
            />
          </g>
        )}
      </svg>

      {/* Crescendo glow — full canvas warm tint overlay, clay: stronger opacity */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: CANVAS.width,
          height: CANVAS.height,
          backgroundColor: RED,
          opacity: crescendoOpacity,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
