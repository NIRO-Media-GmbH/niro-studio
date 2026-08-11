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
  MOSS_GREEN,
  MOSS_GREEN_LIGHT,
  MOSS_DARK,
  WARM_GOLD,
  WARM_GOLD_LIGHT,
  CLAY_HIGHLIGHT,
  CLAY_SHADOW,
  CLAY_PARTICLE_SHADOW,
} from "./constants";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CoatingWipeProps {
  /** 0-1 wipe progress from left to right */
  wipeProgress: number;
  localFrame: number;
}

interface Sparkle {
  id: number;
  triggerProgress: number;
  startX: number;
  startY: number;
  velocityX: number;
  velocityY: number;
  radius: number;
  color: string;
}

interface MossFragment {
  id: number;
  triggerProgress: number;
  startX: number;
  startY: number;
  velocityX: number;
  velocityY: number;
  size: number;
  rotation: number;
}

interface GlowParticle {
  id: number;
  yOffset: number;
  radius: number;
  phaseOffset: number;
}

// ---------------------------------------------------------------------------
// Roof geometry helpers
// ---------------------------------------------------------------------------

const roof = roofPixels(CANVAS.width, CANVAS.height);

/** Left X bound of roof surface */
const ROOF_LEFT = Math.min(...roof.points.map((p) => p.x));
/** Right X bound of roof surface */
const ROOF_RIGHT = Math.max(...roof.points.map((p) => p.x));
/** Top Y bound of roof surface */
const ROOF_TOP = Math.min(...roof.points.map((p) => p.y));
/** Bottom Y bound of roof surface */
const ROOF_BOTTOM = Math.max(...roof.points.map((p) => p.y));
/** Width of the roof area in pixels */
const ROOF_WIDTH = ROOF_RIGHT - ROOF_LEFT;
/** Height of the roof area in pixels */
const ROOF_HEIGHT = ROOF_BOTTOM - ROOF_TOP;

/** Get a random Y position within the roof area for a given X progress (0-1) */
function roofYAtProgress(progress: number, seed: string): number {
  const yCenter = (ROOF_TOP + ROOF_BOTTOM) / 2;
  const yRange = ROOF_HEIGHT * 0.4;
  return yCenter + (random(seed) - 0.5) * 2 * yRange;
}

// ---------------------------------------------------------------------------
// Constants — fewer but more impactful particles
// ---------------------------------------------------------------------------

const SPARKLE_COUNT = 24;
const MOSS_COUNT = 12;
const GLOW_COUNT = 10;
const SHOCKWAVE_DURATION = 30; // frames
const SHOCKWAVE_MAX_RADIUS = 400;
const MOSS_FADE_FRAMES = 20;

// ---------------------------------------------------------------------------
// CoatingWipe
// ---------------------------------------------------------------------------

export const CoatingWipe: React.FC<CoatingWipeProps> = ({
  wipeProgress,
  localFrame,
}) => {
  const { fps } = useVideoConfig();

  // -----------------------------------------------------------------------
  // Generate particles once via useMemo
  // -----------------------------------------------------------------------

  const sparkles = useMemo<Sparkle[]>(() => {
    return Array.from({ length: SPARKLE_COUNT }, (_, i) => {
      const triggerProgress = random(`sparkle-trigger-${i}`) * 0.92 + 0.04;
      const startX = ROOF_LEFT + triggerProgress * ROOF_WIDTH;
      const startY = roofYAtProgress(triggerProgress, `sparkle-y-${i}`);
      const angle = (random(`sparkle-angle-${i}`) - 0.5) * Math.PI * 1.6;
      const speed = 3 + random(`sparkle-speed-${i}`) * 7;
      return {
        id: i,
        triggerProgress,
        startX,
        startY,
        velocityX: Math.cos(angle) * speed,
        velocityY: Math.sin(angle) * speed,
        radius: 5 + random(`sparkle-r-${i}`) * 7, // slightly larger: 5-12
        color: random(`sparkle-color-${i}`) > 0.5 ? WHITE : RED_LIGHT,
      };
    });
  }, []);

  const mossFragments = useMemo<MossFragment[]>(() => {
    return Array.from({ length: MOSS_COUNT }, (_, i) => {
      const triggerProgress = random(`moss-trigger-${i}`) * 0.88 + 0.06;
      const startX = ROOF_LEFT + triggerProgress * ROOF_WIDTH;
      const startY = roofYAtProgress(triggerProgress, `moss-y-${i}`);
      const angle = (random(`moss-angle-${i}`) - 0.5) * Math.PI;
      const speed = 2 + random(`moss-speed-${i}`) * 5;
      return {
        id: i,
        triggerProgress,
        startX,
        startY,
        velocityX: Math.cos(angle) * speed,
        velocityY: Math.sin(angle) * speed - 2, // slight upward bias
        size: 8 + random(`moss-size-${i}`) * 12, // slightly larger: 8-20
        rotation: random(`moss-rot-${i}`) * 360,
      };
    });
  }, []);

  const glowParticles = useMemo<GlowParticle[]>(() => {
    return Array.from({ length: GLOW_COUNT }, (_, i) => ({
      id: i,
      yOffset: (random(`glow-y-${i}`) - 0.5) * ROOF_HEIGHT * 0.6,
      radius: 6 + random(`glow-r-${i}`) * 8, // larger: 6-14
      phaseOffset: random(`glow-phase-${i}`) * Math.PI * 2,
    }));
  }, []);

  // -----------------------------------------------------------------------
  // Shockwave ring
  // -----------------------------------------------------------------------

  const shockwaveProgress = Math.min(localFrame / SHOCKWAVE_DURATION, 1);
  const shockwaveRadius = shockwaveProgress * SHOCKWAVE_MAX_RADIUS;
  const shockwaveOpacity = interpolate(
    shockwaveProgress,
    [0, 0.3, 1],
    [1, 0.7, 0],
  );
  const shockwaveCx = ROOF_LEFT;
  const shockwaveCy = (ROOF_TOP + ROOF_BOTTOM) / 2;

  // -----------------------------------------------------------------------
  // Current wipe X position
  // -----------------------------------------------------------------------

  const wipeX = ROOF_LEFT + wipeProgress * ROOF_WIDTH;
  const wipeCenterY = (ROOF_TOP + ROOF_BOTTOM) / 2;

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <AbsoluteFill>
      <svg
        viewBox={`0 0 ${CANVAS.width} ${CANVAS.height}`}
        style={{ width: "100%", height: "100%" }}
      >
        <defs>
          {/* Shockwave glow filter */}
          <filter id="shockwave-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Clay particle shadow */}
          <filter id="clay-particle-drop" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow
              dx={0}
              dy={2}
              stdDeviation={3}
              floodColor="black"
              floodOpacity={0.3}
            />
          </filter>

          {/* Per-sparkle radial gradients */}
          {sparkles.map((s) => (
            <radialGradient
              key={`sparkle-grad-${s.id}`}
              id={`sparkle-grad-${s.id}`}
              cx="40%"
              cy="35%"
              r="60%"
            >
              <stop offset="0%" stopColor={WHITE} />
              <stop
                offset="50%"
                stopColor={s.color === WHITE ? WARM_GOLD_LIGHT : RED_LIGHT}
              />
              <stop offset="100%" stopColor={s.color === WHITE ? WARM_GOLD : RED} stopOpacity={0} />
            </radialGradient>
          ))}

          {/* Per-moss-fragment radial gradients */}
          {mossFragments.map((m) => (
            <radialGradient
              key={`moss-frag-grad-${m.id}`}
              id={`moss-frag-grad-${m.id}`}
              cx="40%"
              cy="35%"
              r="60%"
            >
              <stop offset="0%" stopColor={MOSS_GREEN_LIGHT} />
              <stop offset="55%" stopColor={MOSS_GREEN} />
              <stop offset="100%" stopColor={MOSS_DARK} />
            </radialGradient>
          ))}

          {/* Per-glow-particle radial gradients */}
          {glowParticles.map((g) => (
            <radialGradient
              key={`glow-grad-${g.id}`}
              id={`glow-grad-${g.id}`}
              cx="45%"
              cy="40%"
              r="55%"
            >
              <stop offset="0%" stopColor={WHITE} />
              <stop offset="50%" stopColor={WHITE} stopOpacity={0.7} />
              <stop offset="100%" stopColor={WHITE} stopOpacity={0} />
            </radialGradient>
          ))}
        </defs>

        {/* --- Shockwave ring (thicker + glow filter) --- */}
        {localFrame < SHOCKWAVE_DURATION + 10 && (
          <circle
            cx={shockwaveCx}
            cy={shockwaveCy}
            r={shockwaveRadius}
            fill="none"
            stroke={WHITE}
            strokeWidth={5}
            opacity={shockwaveOpacity}
            filter="url(#shockwave-glow)"
          />
        )}

        {/* --- Sparkle explosions (circles with radial gradient) --- */}
        {sparkles.map((s) => {
          if (wipeProgress < s.triggerProgress) return null;

          const elapsed =
            (wipeProgress - s.triggerProgress) * 175; // approx frame count since trigger
          const x = s.startX + s.velocityX * elapsed;
          const y = s.startY + s.velocityY * elapsed;

          const lifeProgress = Math.min(elapsed / 40, 1);
          const opacity = interpolate(lifeProgress, [0, 0.2, 1], [1, 1, 0]);
          const scale = interpolate(
            lifeProgress,
            [0, 0.15, 0.4, 1],
            [0, 1.3, 1, 0.3],
          );

          if (opacity <= 0) return null;

          return (
            <circle
              key={`sparkle-${s.id}`}
              cx={x}
              cy={y}
              r={s.radius * scale}
              fill={`url(#sparkle-grad-${s.id})`}
              opacity={opacity}
              filter="url(#clay-particle-drop)"
            />
          );
        })}

        {/* --- Moss disintegration (all circles with radial gradient) --- */}
        {mossFragments.map((m) => {
          if (wipeProgress < m.triggerProgress) {
            // Still intact — draw stationary moss blob (rounded circle)
            return (
              <circle
                key={`moss-${m.id}`}
                cx={m.startX}
                cy={m.startY}
                r={m.size / 2}
                fill={`url(#moss-frag-grad-${m.id})`}
                opacity={0.8}
                filter="url(#clay-particle-drop)"
              />
            );
          }

          // Scattered — animate outward and fade
          const elapsedFrames =
            (wipeProgress - m.triggerProgress) * 175;
          const fadeProgress = Math.min(elapsedFrames / MOSS_FADE_FRAMES, 1);
          const opacity = interpolate(fadeProgress, [0, 1], [0.8, 0]);
          const scatter = elapsedFrames;
          const x = m.startX + m.velocityX * scatter;
          const y = m.startY + m.velocityY * scatter;

          if (opacity <= 0) return null;

          return (
            <circle
              key={`moss-${m.id}`}
              cx={x}
              cy={y}
              r={(m.size / 2) * (1 - fadeProgress * 0.4)}
              fill={`url(#moss-frag-grad-${m.id})`}
              opacity={opacity}
              filter="url(#clay-particle-drop)"
            />
          );
        })}

        {/* --- Glow wipe line particles (with radial gradient) --- */}
        {wipeProgress > 0.05 &&
          wipeProgress < 0.95 &&
          glowParticles.map((g) => {
            const noiseVal = noise2D(
              `glow-${g.id}`,
              localFrame * 0.08,
              g.phaseOffset,
            );
            const px = wipeX + noiseVal * 30;
            const py = wipeCenterY + g.yOffset + noiseVal * 20;

            const flicker = interpolate(
              Math.sin(localFrame * 0.5 + g.phaseOffset),
              [-1, 1],
              [0.5, 1],
            );

            return (
              <circle
                key={`glow-${g.id}`}
                cx={px}
                cy={py}
                r={g.radius}
                fill={`url(#glow-grad-${g.id})`}
                opacity={flicker}
                filter="url(#clay-particle-drop)"
              />
            );
          })}
      </svg>
    </AbsoluteFill>
  );
};
