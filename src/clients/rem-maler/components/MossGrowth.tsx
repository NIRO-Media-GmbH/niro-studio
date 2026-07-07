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
  MOSS_GREEN,
  MOSS_GREEN_LIGHT,
  MOSS_DARK,
  LICHEN_YELLOW,
  RED,
  CLAY_HIGHLIGHT,
  CLAY_SHADOW,
  CLAY_PARTICLE_SHADOW,
} from "./constants";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface MossGrowthProps {
  progress: number;
  localFrame: number;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------
const roof = roofPixels(CANVAS.width, CANVAS.height);
const ROOF_MIN_X = Math.min(...roof.points.map((p) => p.x));
const ROOF_MAX_X = Math.max(...roof.points.map((p) => p.x));
const ROOF_MIN_Y = Math.min(...roof.points.map((p) => p.y));
const ROOF_MAX_Y = Math.max(...roof.points.map((p) => p.y));

/** Random point inside the roof bounding box. */
function roofPoint(seed: string) {
  return {
    x: ROOF_MIN_X + random(seed + "x") * (ROOF_MAX_X - ROOF_MIN_X),
    y: ROOF_MIN_Y + random(seed + "y") * (ROOF_MAX_Y - ROOF_MIN_Y),
  };
}

// ---------------------------------------------------------------------------
// Seed-based data generators (stable across renders via useMemo)
// ---------------------------------------------------------------------------

interface MossBlob {
  x: number;
  y: number;
  rx: number;
  ry: number;
  rotation: number;
  delay: number;
  color: string;
  colorLight: string;
  colorDark: string;
}

function generateMossBlobs(count: number): MossBlob[] {
  const palette: { base: string; light: string; dark: string }[] = [
    { base: MOSS_GREEN, light: MOSS_GREEN_LIGHT, dark: MOSS_DARK },
    { base: MOSS_GREEN_LIGHT, light: "#7CBF6F", dark: MOSS_GREEN },
    { base: MOSS_DARK, light: MOSS_GREEN, dark: "#1A3515" },
  ];
  return Array.from({ length: count }, (_, i) => {
    const pos = roofPoint(`moss-${i}`);
    const baseRadius = 28 + random(`moss-r-${i}`) * 50; // slightly larger: 28-78
    const pal = palette[Math.floor(random(`moss-c-${i}`) * palette.length)];
    return {
      x: pos.x,
      y: pos.y,
      rx: baseRadius * (0.8 + random(`moss-rx-${i}`) * 0.4),
      ry: baseRadius * (0.8 + random(`moss-ry-${i}`) * 0.4),
      rotation: random(`moss-rot-${i}`) * 360,
      delay: i * 8, // stagger
      color: pal.base,
      colorLight: pal.light,
      colorDark: pal.dark,
    };
  });
}

interface VineTendril {
  path: string;
  length: number;
  delay: number;
}

function generateVines(count: number): VineTendril[] {
  return Array.from({ length: count }, (_, i) => {
    const start = roofPoint(`vine-s-${i}`);
    // Build a multi-segment cubic bezier within the roof area
    const segments = 2 + Math.floor(random(`vine-seg-${i}`) * 3); // 2-4
    let d = `M ${start.x} ${start.y}`;
    let cx = start.x;
    let cy = start.y;
    for (let s = 0; s < segments; s++) {
      const dx = (random(`vine-dx-${i}-${s}`) - 0.5) * 400;
      const dy = (random(`vine-dy-${i}-${s}`) - 0.3) * 200;
      const cp1x = cx + dx * 0.3 + (random(`vine-c1x-${i}-${s}`) - 0.5) * 120;
      const cp1y = cy + dy * 0.3 + (random(`vine-c1y-${i}-${s}`) - 0.5) * 80;
      const cp2x = cx + dx * 0.7 + (random(`vine-c2x-${i}-${s}`) - 0.5) * 120;
      const cp2y = cy + dy * 0.7 + (random(`vine-c2y-${i}-${s}`) - 0.5) * 80;
      cx += dx;
      cy += dy;
      // Clamp to roof area
      cx = Math.max(ROOF_MIN_X, Math.min(ROOF_MAX_X, cx));
      cy = Math.max(ROOF_MIN_Y, Math.min(ROOF_MAX_Y, cy));
      d += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${cx},${cy}`;
    }
    return {
      path: d,
      length: 300 + random(`vine-len-${i}`) * 500,
      delay: i * 12,
    };
  });
}

interface Spore {
  startX: number;
  startY: number;
  radius: number;
  speed: number;
  driftSeed: string;
  opacity: number;
}

function generateSpores(count: number): Spore[] {
  return Array.from({ length: count }, (_, i) => {
    const pos = roofPoint(`spore-${i}`);
    return {
      startX: pos.x,
      startY: pos.y,
      radius: 6 + random(`spore-r-${i}`) * 6, // larger: 6-12
      speed: 0.8 + random(`spore-spd-${i}`) * 1.2,
      driftSeed: `spore-drift-${i}`,
      opacity: 0.3 + random(`spore-o-${i}`) * 0.5,
    };
  });
}

interface LichenCrust {
  x: number;
  y: number;
  targetRadius: number;
  delay: number;
}

function generateLichen(count: number): LichenCrust[] {
  return Array.from({ length: count }, (_, i) => {
    const pos = roofPoint(`lichen-${i}`);
    return {
      x: pos.x,
      y: pos.y,
      targetRadius: 15 + random(`lichen-r-${i}`) * 15, // 15-30
      delay: i * 14,
    };
  });
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const MossGrowth: React.FC<MossGrowthProps> = ({
  progress,
  localFrame,
}) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  // Stable data across renders
  const mossBlobs = useMemo(() => generateMossBlobs(10), []);
  const vines = useMemo(() => generateVines(6), []);
  const spores = useMemo(() => generateSpores(12), []);
  const lichens = useMemo(() => generateLichen(8), []);

  // ---- Breathing pulse (shared by all blobs) ----
  const breathe = 1.0 + Math.sin(localFrame * 0.08) * 0.02; // 1.0 <-> 1.02

  // ---- Danger vignette pulse ----
  const vignetteAlpha =
    0.1 + Math.sin(localFrame * 0.06) * 0.05; // 0.05 <-> 0.15

  return (
    <AbsoluteFill>
      {/* ---- SVG layer: moss, vines, spores, lichen ---- */}
      <AbsoluteFill>
        <svg
          viewBox={`0 0 ${CANVAS.width} ${CANVAS.height}`}
          width="100%"
          height="100%"
          style={{ position: "absolute", top: 0, left: 0 }}
        >
          <defs>
            {/* Toxic glow filter — clay version with soft shadow */}
            <filter id="toxic-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow
                dx={0}
                dy={0}
                stdDeviation={15}
                floodColor={MOSS_GREEN}
                floodOpacity={0.7}
              />
            </filter>

            {/* Per-blob clay drop shadow */}
            <filter id="clay-blob-shadow" x="-30%" y="-30%" width="160%" height="180%">
              <feDropShadow
                dx={0}
                dy={4}
                stdDeviation={6}
                floodColor="black"
                floodOpacity={0.35}
              />
            </filter>

            {/* Per-spore soft shadow */}
            <filter id="clay-spore-shadow" x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow
                dx={0}
                dy={2}
                stdDeviation={3}
                floodColor="black"
                floodOpacity={0.25}
              />
            </filter>

            {/* Moss blob radial gradients */}
            {mossBlobs.map((blob, i) => (
              <radialGradient
                key={`moss-grad-${i}`}
                id={`moss-grad-${i}`}
                cx="40%"
                cy="35%"
                r="60%"
              >
                <stop offset="0%" stopColor={blob.colorLight} />
                <stop offset="50%" stopColor={blob.color} />
                <stop offset="100%" stopColor={blob.colorDark} />
              </radialGradient>
            ))}

            {/* Spore radial gradients */}
            {spores.map((_, i) => (
              <radialGradient
                key={`spore-grad-${i}`}
                id={`spore-grad-${i}`}
                cx="40%"
                cy="35%"
                r="55%"
              >
                <stop offset="0%" stopColor="#9ADE8F" />
                <stop offset="60%" stopColor={MOSS_GREEN_LIGHT} />
                <stop offset="100%" stopColor={MOSS_GREEN} />
              </radialGradient>
            ))}

            {/* Lichen radial gradients */}
            {lichens.map((_, i) => (
              <radialGradient
                key={`lichen-grad-${i}`}
                id={`lichen-grad-${i}`}
                cx="40%"
                cy="35%"
                r="60%"
              >
                <stop offset="0%" stopColor="#A89548" />
                <stop offset="55%" stopColor={LICHEN_YELLOW} />
                <stop offset="100%" stopColor="#6B5F28" />
              </radialGradient>
            ))}
          </defs>

          {/* ---- Moss blobs (with toxic glow + clay shadow + radial gradient) ---- */}
          <g filter="url(#toxic-glow)">
            {mossBlobs.map((blob, i) => {
              const delayedFrame = Math.max(0, localFrame - blob.delay);
              const scaleSpring = spring({
                frame: delayedFrame,
                fps,
                config: { damping: 14, stiffness: 80 },
              });
              const s = scaleSpring * breathe;

              return (
                <ellipse
                  key={`moss-${i}`}
                  cx={blob.x}
                  cy={blob.y}
                  rx={blob.rx * s}
                  ry={blob.ry * s}
                  fill={`url(#moss-grad-${i})`}
                  opacity={interpolate(scaleSpring, [0, 0.3, 1], [0, 0.6, 0.85])}
                  transform={`rotate(${blob.rotation} ${blob.x} ${blob.y})`}
                  filter="url(#clay-blob-shadow)"
                />
              );
            })}
          </g>

          {/* ---- Vine tendrils (thicker, rounded caps/joins) ---- */}
          {vines.map((vine, i) => {
            const delayedFrame = Math.max(0, localFrame - vine.delay);
            const drawProgress = interpolate(
              delayedFrame,
              [0, 60],
              [0, 1],
              { extrapolateRight: "clamp" },
            );
            const dashOffset = vine.length * (1 - drawProgress);

            return (
              <path
                key={`vine-${i}`}
                d={vine.path}
                fill="none"
                stroke={MOSS_GREEN}
                strokeWidth={5}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray={vine.length}
                strokeDashoffset={dashOffset}
                opacity={interpolate(drawProgress, [0, 0.1, 1], [0, 0.7, 0.9])}
              />
            );
          })}

          {/* ---- Lichen crusts (with radial gradient) ---- */}
          {lichens.map((lichen, i) => {
            const delayedFrame = Math.max(0, localFrame - lichen.delay);
            const scaleSpring = spring({
              frame: delayedFrame,
              fps,
              config: { damping: 22, stiffness: 40 }, // slow expansion
            });

            return (
              <circle
                key={`lichen-${i}`}
                cx={lichen.x}
                cy={lichen.y}
                r={lichen.targetRadius * scaleSpring}
                fill={`url(#lichen-grad-${i})`}
                opacity={interpolate(scaleSpring, [0, 0.2, 1], [0, 0.4, 0.7])}
                filter="url(#clay-blob-shadow)"
              />
            );
          })}

          {/* ---- Spore particles (with radial gradient + clay shadow) ---- */}
          {spores.map((spore, i) => {
            // Continuous upward float with noise-based drift
            const lifeT = (localFrame * spore.speed) % 120; // loop every ~120 frames
            const yOffset = -lifeT * 3; // float upward
            const xDrift = noise2D(spore.driftSeed, localFrame * 0.02, 0) * 40;
            const fadeIn = interpolate(lifeT, [0, 10], [0, 1], {
              extrapolateRight: "clamp",
            });
            const fadeOut = interpolate(lifeT, [90, 120], [1, 0], {
              extrapolateLeft: "clamp",
            });

            return (
              <circle
                key={`spore-${i}`}
                cx={spore.startX + xDrift}
                cy={spore.startY + yOffset}
                r={spore.radius}
                fill={`url(#spore-grad-${i})`}
                opacity={spore.opacity * fadeIn * fadeOut}
                filter="url(#clay-spore-shadow)"
              />
            );
          })}
        </svg>
      </AbsoluteFill>

      {/* ---- Danger vignette overlay (div-based) ---- */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, transparent 40%, ${RED}${Math.round(vignetteAlpha * 255)
            .toString(16)
            .padStart(2, "0")} 100%)`,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
