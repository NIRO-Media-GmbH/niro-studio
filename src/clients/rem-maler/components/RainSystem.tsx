// ============================================================
// REM Dachbeschichtung — Rain System (Scene 1: Weather)
// Rain particles, splash rings, sun beams, lightning flash,
// frost crystals, ambient dust, and wind streaks
// 3D Clay / Toy visual style
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
import { CANVAS, FPS, ROOF, roofPixels } from "./constants";

interface RainSystemProps {
  /** 0-1 scene progress */
  progress: number;
  /** Current local frame within scene (0-based) */
  localFrame: number;
}

// --- Particle generation types ---
interface RainDrop {
  id: number;
  startX: number;
  startY: number;
  speed: number;
  length: number;
  delay: number;
  opacity: number;
  drift: number;
}

interface SplashRing {
  id: number;
  x: number;
  y: number;
  triggerFrame: number;
  maxRadius: number;
}

interface DustParticle {
  id: number;
  baseX: number;
  baseY: number;
  radius: number;
  opacity: number;
  seed: string;
}

interface FrostCrystal {
  id: number;
  x: number;
  y: number;
  size: number;
  rotation: number;
  appearFrame: number;
}

interface WindStreak {
  id: number;
  y: number;
  startX: number;
  width: number;
  opacity: number;
  speed: number;
  delay: number;
}

// --- Constants ---
const W = CANVAS.width;
const H = CANVAS.height;
const SCENE_FRAMES = 125;
const RAIN_COUNT = 55;
const SPLASH_COUNT = 12;
const DUST_COUNT = 25;
const FROST_COUNT = 7;
const WIND_COUNT = 12;
const GRAVITY = 1.08;

// 6-pointed star SVG path for frost crystals
function frostStarPath(cx: number, cy: number, size: number): string {
  const spikes = 6;
  const outerR = size;
  const innerR = size * 0.4;
  const pts: string[] = [];

  for (let i = 0; i < spikes * 2; i++) {
    const angle = (Math.PI / spikes) * i - Math.PI / 2;
    const r = i % 2 === 0 ? outerR : innerR;
    pts.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
  }
  return `M ${pts.join(" L ")} Z`;
}

export const RainSystem: React.FC<RainSystemProps> = ({
  progress,
  localFrame,
}) => {
  const rp = roofPixels(W, H);
  const roofPts = rp.points;

  // --- Generate rain drops ---
  const rainDrops = useMemo<RainDrop[]>(() => {
    const drops: RainDrop[] = [];
    for (let i = 0; i < RAIN_COUNT; i++) {
      drops.push({
        id: i,
        startX: random(`rain-x-${i}`) * W * 1.2 - W * 0.1,
        startY: -random(`rain-y-${i}`) * 400 - 50,
        speed: 8 + random(`rain-spd-${i}`) * 10,
        length: 15 + random(`rain-len-${i}`) * 10,
        delay: Math.floor(random(`rain-del-${i}`) * 60),
        opacity: 0.3 + random(`rain-op-${i}`) * 0.5,
        drift: (random(`rain-dr-${i}`) - 0.5) * 2,
      });
    }
    return drops;
  }, []);

  // --- Generate splash rings along the roof surface ---
  const splashRings = useMemo<SplashRing[]>(() => {
    const splashes: SplashRing[] = [];
    for (let i = 0; i < SPLASH_COUNT; i++) {
      const t = random(`splash-t-${i}`);
      // Interpolate along top edge of roof
      const x =
        roofPts[0].x + (roofPts[1].x - roofPts[0].x) * t;
      const y =
        roofPts[0].y + (roofPts[1].y - roofPts[0].y) * t;
      splashes.push({
        id: i,
        x,
        y,
        triggerFrame: Math.floor(random(`splash-fr-${i}`) * 100) + 10,
        maxRadius: 12 + random(`splash-r-${i}`) * 16,
      });
    }
    return splashes;
  }, [roofPts]);

  // --- Generate ambient dust ---
  const dustParticles = useMemo<DustParticle[]>(() => {
    const particles: DustParticle[] = [];
    for (let i = 0; i < DUST_COUNT; i++) {
      particles.push({
        id: i,
        baseX: random(`dust-x-${i}`) * W,
        baseY: random(`dust-y-${i}`) * H,
        radius: 1.5 + random(`dust-r-${i}`) * 3,
        opacity: 0.08 + random(`dust-op-${i}`) * 0.15,
        seed: `dust-noise-${i}`,
      });
    }
    return particles;
  }, []);

  // --- Generate frost crystals near roof edges ---
  const frostCrystals = useMemo<FrostCrystal[]>(() => {
    const crystals: FrostCrystal[] = [];
    // Distribute along roof edges (top-left to bottom-left, and top-right to bottom-right)
    const edgePoints = [
      ...Array.from({ length: 4 }, (_, i) => {
        const t = random(`frost-edge-${i}`) * 1;
        return {
          x: roofPts[0].x + (roofPts[3].x - roofPts[0].x) * t,
          y: roofPts[0].y + (roofPts[3].y - roofPts[0].y) * t,
        };
      }),
      ...Array.from({ length: 3 }, (_, i) => {
        const t = random(`frost-edgeR-${i}`) * 1;
        return {
          x: roofPts[1].x + (roofPts[2].x - roofPts[1].x) * t,
          y: roofPts[1].y + (roofPts[2].y - roofPts[1].y) * t,
        };
      }),
    ];

    edgePoints.forEach((pt, i) => {
      crystals.push({
        id: i,
        x: pt.x + (random(`frost-offx-${i}`) - 0.5) * 40,
        y: pt.y + (random(`frost-offy-${i}`) - 0.5) * 30,
        size: 18 + random(`frost-sz-${i}`) * 20,
        rotation: random(`frost-rot-${i}`) * 360,
        appearFrame: SCENE_FRAMES - 30 + Math.floor(random(`frost-af-${i}`) * 20),
      });
    });
    return crystals;
  }, [roofPts]);

  // --- Generate wind streaks ---
  const windStreaks = useMemo<WindStreak[]>(() => {
    const streaks: WindStreak[] = [];
    for (let i = 0; i < WIND_COUNT; i++) {
      streaks.push({
        id: i,
        y: random(`wind-y-${i}`) * H * 0.8 + H * 0.05,
        startX: -random(`wind-sx-${i}`) * W * 0.5,
        width: 200 + random(`wind-w-${i}`) * 600,
        opacity: 0.04 + random(`wind-op-${i}`) * 0.08,
        speed: 4 + random(`wind-spd-${i}`) * 8,
        delay: Math.floor(random(`wind-del-${i}`) * 40),
      });
    }
    return streaks;
  }, []);

  // --- Sun beams (3 transparent polygon wedges from upper-right) ---
  const sunBeams = useMemo(() => {
    const originX = W * 0.92;
    const originY = H * 0.02;
    return [
      {
        id: 0,
        points: `${originX},${originY} ${W * 0.55},${H * 0.45} ${W * 0.65},${H * 0.55}`,
        opacity: 0.04,
      },
      {
        id: 1,
        points: `${originX},${originY} ${W * 0.4},${H * 0.5} ${W * 0.52},${H * 0.6}`,
        opacity: 0.03,
      },
      {
        id: 2,
        points: `${originX},${originY} ${W * 0.3},${H * 0.35} ${W * 0.42},${H * 0.48}`,
        opacity: 0.035,
      },
      {
        id: 3,
        points: `${originX},${originY} ${W * 0.6},${H * 0.3} ${W * 0.72},${H * 0.42}`,
        opacity: 0.025,
      },
    ];
  }, []);

  // --- Lightning flash (around frame 100) ---
  const LIGHTNING_CENTER = 100;
  const lightningOpacity = interpolate(
    localFrame,
    [
      LIGHTNING_CENTER - 2,
      LIGHTNING_CENTER - 1,
      LIGHTNING_CENTER,
      LIGHTNING_CENTER + 1,
      LIGHTNING_CENTER + 3,
    ],
    [0, 0.4, 1, 0.6, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // --- Sun beam fade (stronger in first half, fading out) ---
  const sunBeamFade = interpolate(progress, [0, 0.3, 0.7, 1], [0, 1, 0.6, 0.2], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: "100%", height: "100%" }}
      >
        <defs>
          {/* Glow filter for frost crystals */}
          <filter id="rain-frost-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          {/* Blur for sun beams */}
          <filter id="rain-beam-blur">
            <feGaussianBlur stdDeviation="40" />
          </filter>

          {/* Splash ring gradient */}
          <radialGradient id="rain-splash-grad">
            <stop offset="0%" stopColor="#88D0FF" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#88D0FF" stopOpacity="0" />
          </radialGradient>

          {/* Clay rain drop shadow filter */}
          <filter id="rain-drop-shadow" x="-40%" y="-40%" width="180%" height="180%">
            <feDropShadow dx="0" dy="2" stdDeviation="2" floodColor="rgba(0,0,0,0.3)" />
          </filter>

          {/* Splash glow filter */}
          <filter id="rain-splash-glow" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          {/* Per-drop radial gradients */}
          {rainDrops.map((drop) => (
            <radialGradient
              key={`rain-grad-${drop.id}`}
              id={`rain-grad-${drop.id}`}
              cx="40%"
              cy="30%"
              r="60%"
            >
              <stop offset="0%" stopColor="#B8E4FF" />
              <stop offset="60%" stopColor="#88D0FF" />
              <stop offset="100%" stopColor="#4A9EFF" />
            </radialGradient>
          ))}

          {/* Frost crystal radial gradient */}
          <radialGradient id="rain-frost-fill" cx="40%" cy="30%" r="65%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="50%" stopColor="#E8F4FF" />
            <stop offset="100%" stopColor="#CCEEFF" />
          </radialGradient>

          {/* Dust radial gradient */}
          <radialGradient id="rain-dust-grad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#FFFFFF" stopOpacity="1" />
            <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0.2" />
          </radialGradient>
        </defs>

        {/* ===== AMBIENT DUST (background layer) ===== */}
        {dustParticles.map((p) => {
          const nx = noise2D(p.seed, localFrame * 0.008, 0) * 60;
          const ny = noise2D(p.seed, 0, localFrame * 0.006) * 40;
          return (
            <circle
              key={`dust-${p.id}`}
              cx={p.baseX + nx}
              cy={p.baseY + ny}
              r={p.radius}
              fill="url(#rain-dust-grad)"
              opacity={p.opacity * interpolate(progress, [0, 0.1, 0.9, 1], [0, 1, 1, 0.3], {
                extrapolateRight: "clamp",
              })}
            />
          );
        })}

        {/* ===== SUN BEAMS ===== */}
        {sunBeams.map((beam) => {
          const pulse = 1 + noise2D("beam-pulse", localFrame * 0.02, beam.id) * 0.3;
          return (
            <polygon
              key={`beam-${beam.id}`}
              points={beam.points}
              fill="#FFF8E1"
              opacity={beam.opacity * sunBeamFade * pulse}
              filter="url(#rain-beam-blur)"
            />
          );
        })}

        {/* ===== WIND STREAKS ===== */}
        {windStreaks.map((ws) => {
          const activeFrame = Math.max(0, localFrame - ws.delay);
          const x = ws.startX + activeFrame * ws.speed;
          // Wrap around
          const wrappedX = ((x % (W + ws.width)) + W + ws.width) % (W + ws.width) - ws.width;
          const fadeIn = interpolate(progress, [0, 0.15], [0, 1], {
            extrapolateRight: "clamp",
          });
          return (
            <line
              key={`wind-${ws.id}`}
              x1={wrappedX}
              y1={ws.y}
              x2={wrappedX + ws.width}
              y2={ws.y + 2}
              stroke="#FFFFFF"
              strokeWidth={3}
              opacity={ws.opacity * fadeIn}
              strokeLinecap="round"
            />
          );
        })}

        {/* ===== RAIN DROPS (clay ellipses with radial gradient) ===== */}
        {rainDrops.map((drop) => {
          const activeFrame = localFrame - drop.delay;
          if (activeFrame < 0) return null;

          // Gravity-accelerated fall
          const yOffset = activeFrame * drop.speed * GRAVITY;
          const xOffset = activeFrame * drop.drift + noise2D("rain-drift", activeFrame * 0.05, drop.id) * 15;

          const currentY = drop.startY + yOffset;
          const currentX = drop.startX + xOffset;

          // Don't render if past the bottom
          if (currentY > H + 50) return null;

          // Slight fade as drop falls
          const fallFade = interpolate(currentY, [0, H * 0.8, H], [1, 0.8, 0.4], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          // Scene entrance/exit
          const sceneFade = interpolate(progress, [0, 0.05, 0.85, 1], [0, 1, 1, 0.3], {
            extrapolateRight: "clamp",
          });

          return (
            <ellipse
              key={`rain-${drop.id}`}
              cx={currentX}
              cy={currentY}
              rx={4}
              ry={12}
              fill={`url(#rain-grad-${drop.id})`}
              opacity={drop.opacity * fallFade * sceneFade}
              filter="url(#rain-drop-shadow)"
              transform={`rotate(${4 + drop.drift * 2}, ${currentX}, ${currentY})`}
            />
          );
        })}

        {/* ===== SPLASH RINGS (at roof surface) ===== */}
        {splashRings.map((sp) => {
          const elapsed = localFrame - sp.triggerFrame;
          // Repeat splashes every 35 frames
          const cycle = 35;
          const cycleElapsed = ((elapsed % cycle) + cycle) % cycle;

          if (elapsed < 0) return null;

          const ringProgress = interpolate(cycleElapsed, [0, 12], [0, 1], {
            extrapolateRight: "clamp",
          });
          const ringRadius = sp.maxRadius * ringProgress;
          const ringOpacity = interpolate(cycleElapsed, [0, 3, 12], [0, 0.7, 0], {
            extrapolateRight: "clamp",
          });

          return (
            <g key={`splash-${sp.id}`} filter="url(#rain-splash-glow)">
              <circle
                cx={sp.x}
                cy={sp.y}
                r={ringRadius}
                fill="none"
                stroke="#88D0FF"
                strokeWidth={5}
                opacity={ringOpacity}
              />
              <circle
                cx={sp.x}
                cy={sp.y}
                r={ringRadius * 0.6}
                fill="none"
                stroke="#88D0FF"
                strokeWidth={3}
                opacity={ringOpacity * 0.5}
              />
            </g>
          );
        })}

        {/* ===== FROST CRYSTALS (appear in last ~30 frames, 1.5x larger, radial fill) ===== */}
        {frostCrystals.map((fc) => {
          const framesSinceAppear = localFrame - fc.appearFrame;
          if (framesSinceAppear < 0) return null;

          const scaleIn = interpolate(framesSinceAppear, [0, 12], [0, 1.5], {
            extrapolateRight: "clamp",
          });
          const fadeIn = interpolate(framesSinceAppear, [0, 8], [0, 0.85], {
            extrapolateRight: "clamp",
          });
          // Slow rotation over time
          const rot = fc.rotation + framesSinceAppear * 0.8;

          return (
            <g
              key={`frost-${fc.id}`}
              transform={`translate(${fc.x}, ${fc.y}) rotate(${rot}) scale(${scaleIn})`}
              opacity={fadeIn}
              filter="url(#rain-frost-glow)"
            >
              <path
                d={frostStarPath(0, 0, fc.size)}
                fill="url(#rain-frost-fill)"
                stroke="#CCEEFF"
                strokeWidth={2}
              />
              {/* Inner detail lines */}
              {Array.from({ length: 6 }).map((_, arm) => {
                const angle = (Math.PI / 3) * arm - Math.PI / 2;
                const len = fc.size * 0.75;
                return (
                  <line
                    key={arm}
                    x1={0}
                    y1={0}
                    x2={len * Math.cos(angle)}
                    y2={len * Math.sin(angle)}
                    stroke="#CCEEFF"
                    strokeWidth={1.5}
                    opacity={0.5}
                  />
                );
              })}
            </g>
          );
        })}

        {/* ===== LIGHTNING FLASH ===== */}
        {lightningOpacity > 0.01 && (
          <rect
            x={0}
            y={0}
            width={W}
            height={H}
            fill="#FFFFFF"
            opacity={lightningOpacity * 0.85}
          />
        )}
      </svg>
    </AbsoluteFill>
  );
};
