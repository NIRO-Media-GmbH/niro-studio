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
  GREY_WEATHERED,
  WATER_BLUE,
  WATER_BLUE_LIGHT,
  CLAY_PARTICLE_SHADOW,
} from "./constants";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface CrackSystemProps {
  progress: number;
  localFrame: number;
}

interface CrackDef {
  path: string;
  length: number;
  staggerFrame: number;
  endX: number;
  endY: number;
}

interface SplinterDef {
  points: string;
  cx: number;
  cy: number;
  w: number;
  h: number;
  rx: number;
  ry: number;
  angle: number;
  startFrame: number;
}

interface WaterDropDef {
  x: number;
  startY: number;
  travelY: number;
  startFrame: number;
  radius: number;
  seed: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const roof = roofPixels(CANVAS.width, CANVAS.height);
const roofMinX = Math.min(...roof.points.map((p) => p.x));
const roofMaxX = Math.max(...roof.points.map((p) => p.x));
const roofMinY = Math.min(...roof.points.map((p) => p.y));
const roofMaxY = Math.max(...roof.points.map((p) => p.y));

/** Clamp a value between min and max */
function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

/** Build a jagged crack path string within roof bounds */
function buildCrackPath(
  startX: number,
  startY: number,
  segments: number,
  seed: string,
): { path: string; endX: number; endY: number; approxLength: number } {
  let x = startX;
  let y = startY;
  let d = `M ${x} ${y}`;
  let totalLen = 0;

  for (let i = 0; i < segments; i++) {
    const dx = (random(`${seed}-dx-${i}`) - 0.5) * 180;
    const dy = random(`${seed}-dy-${i}`) * 100 + 20;
    const nx = clamp(x + dx, roofMinX + 60, roofMaxX - 60);
    const ny = clamp(y + dy, roofMinY + 20, roofMaxY - 20);
    const segLen = Math.sqrt((nx - x) ** 2 + (ny - y) ** 2);
    totalLen += segLen;
    d += ` L ${nx} ${ny}`;
    x = nx;
    y = ny;
  }

  return { path: d, endX: x, endY: y, approxLength: totalLen };
}

// ---------------------------------------------------------------------------
// Crack definitions (generated once)
// ---------------------------------------------------------------------------
const CRACK_DEFS: CrackDef[] = (() => {
  const cracks: CrackDef[] = [];
  const seeds = ["crk-a", "crk-b", "crk-c", "crk-d", "crk-e", "crk-f"];
  const startPositions = [
    { x: roofMinX + 200, y: roofMinY + 40 },
    { x: roofMinX + 600, y: roofMinY + 60 },
    { x: roofMinX + 1000, y: roofMinY + 30 },
    { x: roofMinX + 1500, y: roofMinY + 50 },
    { x: roofMinX + 1900, y: roofMinY + 70 },
    { x: roofMinX + 1200, y: roofMinY + 180 },
  ];

  for (let i = 0; i < seeds.length; i++) {
    const segs = 4 + Math.floor(random(`${seeds[i]}-segs`) * 3);
    const { path, endX, endY, approxLength } = buildCrackPath(
      startPositions[i].x,
      startPositions[i].y,
      segs,
      seeds[i],
    );
    cracks.push({
      path,
      length: approxLength,
      staggerFrame: i * 15,
      endX,
      endY,
    });
  }
  return cracks;
})();

// ---------------------------------------------------------------------------
// Splinter definitions (rounded rectangles for clay style)
// ---------------------------------------------------------------------------
const SPLINTER_DEFS: SplinterDef[] = (() => {
  const splinters: SplinterDef[] = [];
  for (let i = 0; i < 5; i++) {
    const crack = CRACK_DEFS[i % CRACK_DEFS.length];
    const cx = crack.endX + (random(`spl-x-${i}`) - 0.5) * 100;
    const cy = crack.endY + (random(`spl-y-${i}`) - 0.3) * 60;
    const w = 14 + random(`spl-w-${i}`) * 20;
    const h = 8 + random(`spl-h-${i}`) * 12;
    // Triangle splinter points (kept for reference/fallback)
    const a1 = random(`spl-a1-${i}`) * Math.PI * 2;
    const a2 = a1 + 1.8 + random(`spl-a2-${i}`) * 0.6;
    const a3 = a2 + 1.8 + random(`spl-a3-${i}`) * 0.6;
    const size = 12 + random(`spl-s-${i}`) * 18;
    const pts = [
      `${cx + Math.cos(a1) * size},${cy + Math.sin(a1) * size}`,
      `${cx + Math.cos(a2) * size},${cy + Math.sin(a2) * size}`,
      `${cx + Math.cos(a3) * size},${cy + Math.sin(a3) * size}`,
    ].join(" ");
    splinters.push({
      points: pts,
      cx,
      cy,
      w,
      h,
      rx: 4 + random(`spl-rx-${i}`) * 3,
      ry: 3 + random(`spl-ry-${i}`) * 2,
      angle: random(`spl-rot-${i}`) * 360,
      startFrame: 60 + i * 8,
    });
  }
  return splinters;
})();

// ---------------------------------------------------------------------------
// Water drop definitions
// ---------------------------------------------------------------------------
const WATER_DROP_DEFS: WaterDropDef[] = (() => {
  const drops: WaterDropDef[] = [];
  for (let i = 0; i < 5; i++) {
    const crack = CRACK_DEFS[i % CRACK_DEFS.length];
    const midFactor = 0.4 + random(`wd-mid-${i}`) * 0.4;
    drops.push({
      x: crack.endX + (random(`wd-x-${i}`) - 0.5) * 60,
      startY: crack.endY - 20,
      travelY: 200 + random(`wd-travel-${i}`) * 150,
      startFrame: 50 + i * 12,
      radius: 6 + random(`wd-r-${i}`) * 6,
      seed: `wd-${i}`,
    });
  }
  return drops;
})();

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Single crack with stroke-dashoffset draw-in animation — clay style */
const CrackPath: React.FC<{
  def: CrackDef;
  localFrame: number;
}> = ({ def, localFrame }) => {
  const adjustedFrame = localFrame - def.staggerFrame;
  if (adjustedFrame < 0) return null;

  const drawDuration = 40;
  const drawProgress = clamp(adjustedFrame / drawDuration, 0, 1);
  const offset = def.length * (1 - drawProgress);

  return (
    <path
      d={def.path}
      fill="none"
      stroke="#1A1A10"
      strokeWidth={7}
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray={def.length}
      strokeDashoffset={offset}
    />
  );
};

/** Dust burst at the tip of a crack — clay style with radial gradient circles */
const CrackDust: React.FC<{
  def: CrackDef;
  localFrame: number;
}> = ({ def, localFrame }) => {
  const drawEnd = def.staggerFrame + 40;
  const dustStart = drawEnd - 4; // trigger when draw > ~0.9
  const elapsed = localFrame - dustStart;
  if (elapsed < 0 || elapsed > 30) return null;

  const particles = useMemo(() => {
    const arr: { angle: number; speed: number; size: number; id: number }[] = [];
    for (let i = 0; i < 7; i++) {
      arr.push({
        id: i,
        angle: random(`dust-a-${def.staggerFrame}-${i}`) * Math.PI * 2,
        speed: 15 + random(`dust-sp-${def.staggerFrame}-${i}`) * 30,
        size: 3 + random(`dust-sz-${def.staggerFrame}-${i}`) * 5,
      });
    }
    return arr;
  }, [def.staggerFrame]);

  const lifeProgress = clamp(elapsed / 25, 0, 1);

  return (
    <g>
      {particles.map((p) => {
        const dist = p.speed * lifeProgress;
        const px = def.endX + Math.cos(p.angle) * dist;
        const py = def.endY + Math.sin(p.angle) * dist;
        const opacity = interpolate(lifeProgress, [0, 0.3, 1], [0, 0.8, 0]);
        const scale = interpolate(lifeProgress, [0, 0.2, 1], [0.3, 1, 0.5]);
        const gradId = `crack-dust-grad-${def.staggerFrame}-${p.id}`;
        return (
          <g key={p.id}>
            <defs>
              <radialGradient id={gradId} cx="40%" cy="35%" r="60%">
                <stop offset="0%" stopColor="#8A8A6A" stopOpacity="1" />
                <stop offset="70%" stopColor={GREY_WEATHERED} stopOpacity="0.6" />
                <stop offset="100%" stopColor={GREY_WEATHERED} stopOpacity="0" />
              </radialGradient>
            </defs>
            <circle
              cx={px}
              cy={py}
              r={p.size * scale}
              fill={`url(#${gradId})`}
              opacity={opacity}
            />
          </g>
        );
      })}
    </g>
  );
};

/** Tile splinter — clay rounded rectangle with subtle shadow */
const TileSplinter: React.FC<{
  def: SplinterDef;
  localFrame: number;
}> = ({ def, localFrame }) => {
  const elapsed = localFrame - def.startFrame;
  if (elapsed < 0) return null;

  const fallDuration = 50;
  const t = clamp(elapsed / fallDuration, 0, 1);

  // Gravity: quadratic fall
  const fallY = 600 * t * t;
  const driftX = (random(`spl-drift-${def.startFrame}`) - 0.5) * 80 * t;
  const rotation = def.angle + t * 360 * (random(`spl-spin-${def.startFrame}`) > 0.5 ? 1 : -1);
  const opacity = interpolate(t, [0, 0.7, 1], [1, 0.8, 0]);

  const gradId = `splinter-grad-${def.startFrame}`;
  const shadowId = `splinter-shadow-${def.startFrame}`;

  return (
    <g
      opacity={opacity}
      transform={`translate(${driftX}, ${fallY}) rotate(${rotation}, ${def.cx}, ${def.cy})`}
    >
      <defs>
        <radialGradient id={gradId} cx="35%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#7A7A5A" />
          <stop offset="100%" stopColor={GREY_WEATHERED} />
        </radialGradient>
        <filter id={shadowId} x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="1" dy="2" stdDeviation="2" floodColor={CLAY_PARTICLE_SHADOW} />
        </filter>
      </defs>
      <rect
        x={def.cx - def.w / 2}
        y={def.cy - def.h / 2}
        width={def.w}
        height={def.h}
        rx={def.rx}
        ry={def.ry}
        fill={`url(#${gradId})`}
        stroke="#1A1A10"
        strokeWidth={1.5}
        filter={`url(#${shadowId})`}
      />
    </g>
  );
};

/** Water droplet — clay ellipse with radial gradient + specular highlight */
const WaterDrop: React.FC<{
  def: WaterDropDef;
  localFrame: number;
}> = ({ def, localFrame }) => {
  const elapsed = localFrame - def.startFrame;
  if (elapsed < 0) return null;

  const dripDuration = 45;
  const t = clamp(elapsed / dripDuration, 0, 1);

  // Accelerating fall
  const y = def.startY + def.travelY * t * t;
  // Slight horizontal wobble via noise
  const wobble = noise2D(def.seed, t * 3, 0) * 12;
  const x = def.x + wobble;

  // Drop stretches vertically as it falls
  const scaleY = interpolate(t, [0, 0.5, 1], [1, 1.4, 2]);
  const scaleX = interpolate(t, [0, 0.5, 1], [1, 0.85, 0.6]);
  const opacity = interpolate(t, [0, 0.1, 0.85, 1], [0, 0.75, 0.65, 0]);

  const gradId = `water-drop-grad-${def.seed}`;
  const shadowId = `water-drop-shadow-${def.seed}`;

  const rx = def.radius * scaleX;
  const ry = def.radius * scaleY;

  return (
    <g opacity={opacity}>
      <defs>
        <radialGradient id={gradId} cx="35%" cy="25%" r="65%">
          <stop offset="0%" stopColor={WATER_BLUE_LIGHT} />
          <stop offset="60%" stopColor={WATER_BLUE} />
          <stop offset="100%" stopColor="#2A7EDF" />
        </radialGradient>
        <filter id={shadowId} x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow dx="0" dy="1" stdDeviation="1.5" floodColor={CLAY_PARTICLE_SHADOW} />
        </filter>
      </defs>
      {/* Main drop body */}
      <ellipse
        cx={x}
        cy={y}
        rx={rx}
        ry={ry}
        fill={`url(#${gradId})`}
        filter={`url(#${shadowId})`}
      />
      {/* Specular highlight — small white ellipse offset toward top-left */}
      <ellipse
        cx={x - rx * 0.25}
        cy={y - ry * 0.3}
        rx={rx * 0.35}
        ry={ry * 0.2}
        fill="#FFFFFF"
        opacity={0.6}
      />
    </g>
  );
};

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------
export const CrackSystem: React.FC<CrackSystemProps> = ({
  progress,
  localFrame,
}) => {
  return (
    <AbsoluteFill>
      <svg
        viewBox={`0 0 ${CANVAS.width} ${CANVAS.height}`}
        width={CANVAS.width}
        height={CANVAS.height}
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        {/* Crack paths */}
        {CRACK_DEFS.map((crack, i) => (
          <CrackPath key={`crack-${i}`} def={crack} localFrame={localFrame} />
        ))}

        {/* Dust bursts at crack tips */}
        {CRACK_DEFS.map((crack, i) => (
          <CrackDust key={`dust-${i}`} def={crack} localFrame={localFrame} />
        ))}

        {/* Tile splinters breaking off */}
        {SPLINTER_DEFS.map((spl, i) => (
          <TileSplinter key={`spl-${i}`} def={spl} localFrame={localFrame} />
        ))}

        {/* Water drops seeping through */}
        {WATER_DROP_DEFS.map((drop, i) => (
          <WaterDrop key={`drop-${i}`} def={drop} localFrame={localFrame} />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
