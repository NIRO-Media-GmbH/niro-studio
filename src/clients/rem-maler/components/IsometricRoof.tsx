// ============================================================
// REM Dachbeschichtung — Isometric House with Gable Roof
// 3D Clay/Toy style: walls, windows, door, pitched Satteldach
// Front slope is the animated surface (coating, weathering, etc.)
// Gable wall triangle visible on the right side
// ============================================================

import React, { useMemo } from "react";
import { AbsoluteFill, interpolate } from "remotion";
import { adjustBrightness } from "../../../utils/color-utils";
import {
  CANVAS,
  TILE_GRID,
  roofPixels,
  housePixels,
  pointsToSvg,
  RED,
  DARK_NAVY,
  CLAY_RIM,
  WALL_CREAM,
  WALL_LIGHT,
  WALL_DARK,
  WALL_SHADOW,
  WINDOW_BLUE,
  WINDOW_HIGHLIGHT,
  DOOR_BROWN,
  DOOR_DARK,
} from "./constants";

interface IsometricRoofProps {
  drawProgress: number;
  fillOpacity: number;
  roofColor: string;
  tileAccent: string;
  noiseOpacity: number;
  coatingProgress: number;
  coatingColor: string;
  coatingAccent: string;
  glowIntensity: number;
  shake: { x: number; y: number };
  specularPos: number;
}

function lerp2D(
  a: { x: number; y: number },
  b: { x: number; y: number },
  t: number
): { x: number; y: number } {
  return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
}

/** Generate tile quad paths on a 4-point surface via bilinear interpolation */
function generateTilePaths(
  points: { x: number; y: number }[],
  rows: number,
  cols: number
): { path: string; row: number; col: number; cx: number; cy: number }[] {
  const [tl, tr, br, bl] = points;
  const tiles: { path: string; row: number; col: number; cx: number; cy: number }[] = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const rt = r / rows;
      const rb = (r + 1) / rows;
      const cl = c / cols;
      const cr2 = (c + 1) / cols;
      const topLeft = lerp2D(lerp2D(tl, tr, cl), lerp2D(bl, br, cl), rt);
      const topRight = lerp2D(lerp2D(tl, tr, cr2), lerp2D(bl, br, cr2), rt);
      const bottomRight = lerp2D(lerp2D(tl, tr, cr2), lerp2D(bl, br, cr2), rb);
      const bottomLeft = lerp2D(lerp2D(tl, tr, cl), lerp2D(bl, br, cl), rb);
      const cx = (topLeft.x + topRight.x + bottomRight.x + bottomLeft.x) / 4;
      const cy = (topLeft.y + topRight.y + bottomRight.y + bottomLeft.y) / 4;
      tiles.push({
        path: `M ${topLeft.x},${topLeft.y} L ${topRight.x},${topRight.y} L ${bottomRight.x},${bottomRight.y} L ${bottomLeft.x},${bottomLeft.y} Z`,
        row: r, col: c, cx, cy,
      });
    }
  }
  return tiles;
}

/** Build an SVG path with rounded corners via quadratic bezier */
function roundedPath(pts: { x: number; y: number }[], radius: number): string {
  const n = pts.length;
  let d = "";
  for (let i = 0; i < n; i++) {
    const prev = pts[(i - 1 + n) % n];
    const curr = pts[i];
    const next = pts[(i + 1) % n];
    const dxIn = curr.x - prev.x;
    const dyIn = curr.y - prev.y;
    const lenIn = Math.sqrt(dxIn * dxIn + dyIn * dyIn);
    const dxOut = next.x - curr.x;
    const dyOut = next.y - curr.y;
    const lenOut = Math.sqrt(dxOut * dxOut + dyOut * dyOut);
    const r = Math.min(radius, lenIn / 3, lenOut / 3);
    const sx = curr.x - (dxIn / lenIn) * r;
    const sy = curr.y - (dyIn / lenIn) * r;
    const ex = curr.x + (dxOut / lenOut) * r;
    const ey = curr.y + (dyOut / lenOut) * r;
    if (i === 0) d += `M ${sx},${sy} `;
    else d += `L ${sx},${sy} `;
    d += `Q ${curr.x},${curr.y} ${ex},${ey} `;
  }
  return d + "Z";
}

export const IsometricRoof: React.FC<IsometricRoofProps> = ({
  drawProgress,
  fillOpacity,
  roofColor,
  tileAccent,
  noiseOpacity,
  coatingProgress,
  coatingColor,
  coatingAccent,
  glowIntensity,
  shake,
  specularPos,
}) => {
  const { width: W, height: H } = CANVAS;
  const rp = roofPixels(W, H);
  const hp = housePixels(W, H);
  const slope = rp.frontSlope; // [ridgeL, ridgeR, eaveR, eaveL]
  const overhang = rp.rightOverhang; // [ridgeR, backEaveR, eaveR]
  const cornerR = rp.cornerRadius;

  // Tile grid on the front slope
  const tiles = useMemo(
    () => generateTilePaths(slope, TILE_GRID.rows, TILE_GRID.cols),
    [slope]
  );

  // Paths
  const slopePath = useMemo(() => roundedPath(slope, cornerR), [slope, cornerR]);
  const frontWallPath = useMemo(() => roundedPath(hp.frontWall, cornerR * 0.8), [hp.frontWall, cornerR]);

  // Ridge cap — 3D strip along the peak (ridge-left to ridge-right, offset up-right)
  const ridgeCap = [
    slope[0], // ridge-left
    slope[1], // ridge-right
    { x: slope[1].x + rp.ridgeCapOffsetX, y: slope[1].y + rp.ridgeCapOffsetY },
    { x: slope[0].x + rp.ridgeCapOffsetX, y: slope[0].y + rp.ridgeCapOffsetY },
  ];

  // Gable-side roof edge (thin strip showing roof thickness on the right side)
  // Connects frontSlope right edge to the overhang back, showing material depth
  const gableRoofEdge = [
    slope[1],       // ridge-right (top of front slope)
    overhang[1],    // back-eave-right (back of overhang)
    slope[2],       // eave-right (bottom of front slope)
  ];

  // Eave fascia — horizontal band below front eave connecting roof to wall
  const eaveFascia = [
    slope[3], // eave-left
    slope[2], // eave-right
    { x: slope[2].x, y: slope[2].y + rp.eaveDepth },
    { x: slope[3].x, y: slope[3].y + rp.eaveDepth },
  ];

  // Right eave return — small quad connecting front eave fascia to gable overhang
  const rightEaveReturn = [
    slope[2], // eave-right = front eave right end
    overhang[1], // back-eave-right
    { x: overhang[1].x, y: overhang[1].y + rp.eaveDepth * 0.7 },
    { x: slope[2].x, y: slope[2].y + rp.eaveDepth },
  ];

  // Bounding box for clip paths and effects
  const slopeMinX = Math.min(...slope.map((p) => p.x));
  const slopeMaxX = Math.max(...slope.map((p) => p.x));
  const slopeMinY = Math.min(...slope.map((p) => p.y));
  const slopeMaxY = Math.max(...slope.map((p) => p.y));

  const clipX = slopeMinX + (slopeMaxX - slopeMinX) * coatingProgress;
  const specX = slopeMinX + (slopeMaxX - slopeMinX) * specularPos;
  const outlineLength = 6000;

  // Safe color helpers for clay gradients
  const safeRoof = roofColor.startsWith("#") ? roofColor : "#8B6914";
  const safeAccent = tileAccent.startsWith("#") ? tileAccent : "#9A7818";
  const safeCoat = coatingColor.startsWith("#") ? coatingColor : "#D83C31";
  const safeCoatAcc = coatingAccent.startsWith("#") ? coatingAccent : "#F05545";

  const roofLight = adjustBrightness(safeRoof, 40);
  const roofDark = adjustBrightness(safeRoof, -30);
  const roofDarker = adjustBrightness(safeRoof, -60);
  const accentLight = adjustBrightness(safeAccent, 30);
  const accentDark = adjustBrightness(safeAccent, -20);

  const coatLight = adjustBrightness(safeCoat, 40);
  const coatDark = adjustBrightness(safeCoat, -30);
  const coatDarker = adjustBrightness(safeCoat, -60);
  const coatAccLight = adjustBrightness(safeCoatAcc, 30);
  const coatAccDark = adjustBrightness(safeCoatAcc, -20);

  return (
    <AbsoluteFill>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{
          width: "100%",
          height: "100%",
          transform: `translate(${shake.x}px, ${shake.y}px)`,
        }}
      >
        <defs>
          {/* === CLAY GRADIENTS — ROOF SLOPE === */}
          <linearGradient id="clay-roof-surface" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={roofLight} />
            <stop offset="35%" stopColor={safeRoof} />
            <stop offset="80%" stopColor={roofDark} />
            <stop offset="100%" stopColor={roofDarker} />
          </linearGradient>
          <radialGradient id="clay-tile-main" cx="0.4" cy="0.35" r="0.7">
            <stop offset="0%" stopColor={roofLight} />
            <stop offset="100%" stopColor={roofDark} />
          </radialGradient>
          <radialGradient id="clay-tile-alt" cx="0.4" cy="0.35" r="0.7">
            <stop offset="0%" stopColor={accentLight} />
            <stop offset="100%" stopColor={accentDark} />
          </radialGradient>

          {/* Ridge cap gradient (lit from above) */}
          <linearGradient id="clay-ridge-cap" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={adjustBrightness(safeRoof, 55)} />
            <stop offset="100%" stopColor={roofLight} />
          </linearGradient>

          {/* Gable-side roof edge (darker, shadow side) */}
          <linearGradient id="clay-gable-edge" x1="0" y1="0" x2="1" y2="0.3">
            <stop offset="0%" stopColor={roofDark} />
            <stop offset="100%" stopColor={roofDarker} />
          </linearGradient>

          {/* Eave fascia gradient */}
          <linearGradient id="clay-eave-fascia" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={roofDark} />
            <stop offset="100%" stopColor={roofDarker} />
          </linearGradient>

          {/* === COATED SURFACE GRADIENTS === */}
          <linearGradient id="clay-coat-surface" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={coatLight} />
            <stop offset="35%" stopColor={safeCoat} />
            <stop offset="80%" stopColor={coatDark} />
            <stop offset="100%" stopColor={coatDarker} />
          </linearGradient>
          <radialGradient id="clay-coat-tile-main" cx="0.4" cy="0.35" r="0.7">
            <stop offset="0%" stopColor={coatLight} />
            <stop offset="100%" stopColor={coatDark} />
          </radialGradient>
          <radialGradient id="clay-coat-tile-alt" cx="0.4" cy="0.35" r="0.7">
            <stop offset="0%" stopColor={coatAccLight} />
            <stop offset="100%" stopColor={coatAccDark} />
          </radialGradient>

          {/* === HOUSE WALL GRADIENTS === */}
          <linearGradient id="wall-front" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={WALL_LIGHT} />
            <stop offset="50%" stopColor={WALL_CREAM} />
            <stop offset="100%" stopColor={WALL_DARK} />
          </linearGradient>
          <linearGradient id="wall-right" x1="0" y1="0" x2="1" y2="0.3">
            <stop offset="0%" stopColor={WALL_DARK} />
            <stop offset="100%" stopColor={WALL_SHADOW} />
          </linearGradient>
          <linearGradient id="wall-gable" x1="0" y1="1" x2="0.3" y2="0">
            <stop offset="0%" stopColor={WALL_DARK} />
            <stop offset="60%" stopColor={WALL_SHADOW} />
            <stop offset="100%" stopColor={adjustBrightness(WALL_SHADOW, -15)} />
          </linearGradient>
          <radialGradient id="window-grad" cx="0.3" cy="0.25" r="0.8">
            <stop offset="0%" stopColor={WINDOW_HIGHLIGHT} />
            <stop offset="100%" stopColor={WINDOW_BLUE} />
          </radialGradient>
          <linearGradient id="door-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={DOOR_BROWN} />
            <stop offset="100%" stopColor={DOOR_DARK} />
          </linearGradient>

          {/* === FILTERS === */}
          <filter id="house-shadow" x="-15%" y="-10%" width="140%" height="130%">
            <feDropShadow dx="12" dy="20" stdDeviation="30" floodColor="black" floodOpacity="0.45" />
          </filter>
          <filter id="roof-noise">
            <feTurbulence type="fractalNoise" baseFrequency="0.015" numOctaves="4" seed="42" result="noise" />
            <feColorMatrix in="noise" type="saturate" values="0" result="grey-noise" />
            <feComponentTransfer in="grey-noise" result="dark-noise">
              <feFuncA type="linear" slope={noiseOpacity * 1.5} intercept={0} />
            </feComponentTransfer>
            <feBlend in="SourceGraphic" in2="dark-noise" mode="multiply" />
          </filter>
          <filter id="roof-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation={glowIntensity * 30} result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="wipe-glow" x="-50%" y="-20%" width="200%" height="140%">
            <feGaussianBlur stdDeviation="12" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="window-glow">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          {/* === CLIP PATHS === */}
          <clipPath id="roof-shape-clip">
            <path d={slopePath} />
          </clipPath>
          <clipPath id="coating-clip">
            <rect x={0} y={0} width={clipX} height={H} />
          </clipPath>

          {/* Inner highlight (top-to-bottom white fade) */}
          <linearGradient id="inner-highlight" x1={slopeMinX} y1={slopeMinY} x2={slopeMinX} y2={slopeMaxY} gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="white" stopOpacity="0.18" />
            <stop offset="20%" stopColor="white" stopOpacity="0.06" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>

          {/* Specular sweep highlight */}
          <linearGradient id="specular" x1={specX - 150} y1="0" x2={specX + 150} y2="0" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="white" stopOpacity="0" />
            <stop offset="0.5" stopColor="white" stopOpacity={0.35 * (coatingProgress > 0.1 ? 1 : 0)} />
            <stop offset="1" stopColor="white" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* ================================================ */}
        {/* GROUND SHADOW                                    */}
        {/* ================================================ */}
        <ellipse
          cx={(hp.frontWall[0].x + hp.frontWall[1].x) / 2 + 30}
          cy={hp.shadowY + 15}
          rx={(hp.frontWall[1].x - hp.frontWall[0].x) * 0.6}
          ry={55}
          fill={DARK_NAVY}
          opacity={fillOpacity * 0.7}
          filter="url(#roof-glow)"
        />

        {/* ================================================ */}
        {/* HOUSE WALLS (static, behind roof)                */}
        {/* ================================================ */}
        <g filter="url(#house-shadow)" opacity={fillOpacity}>
          {/* Right side wall (darker, depth face) */}
          <polygon
            points={pointsToSvg(hp.rightWall)}
            fill="url(#wall-right)"
          />
          <polygon
            points={pointsToSvg(hp.rightWall)}
            fill="none"
            stroke={CLAY_RIM}
            strokeWidth={1.5}
            strokeLinejoin="round"
          />
          {/* Side window */}
          <rect
            x={hp.sideWindow.x}
            y={hp.sideWindow.y}
            width={hp.sideWindow.w}
            height={hp.sideWindow.h}
            rx={6}
            fill="url(#window-grad)"
            opacity={0.8}
          />

          {/* Right gable wall (triangle above right wall) */}
          <polygon
            points={pointsToSvg(hp.gableWall)}
            fill="url(#wall-gable)"
          />
          <polygon
            points={pointsToSvg(hp.gableWall)}
            fill="none"
            stroke={CLAY_RIM}
            strokeWidth={1.5}
            strokeLinejoin="round"
          />
          {/* Gable wall center line decoration */}
          <line
            x1={(hp.gableWall[0].x + hp.gableWall[1].x) / 2}
            y1={(hp.gableWall[0].y + hp.gableWall[1].y) / 2}
            x2={hp.gableWall[2].x}
            y2={hp.gableWall[2].y + 25}
            stroke={CLAY_RIM}
            strokeWidth={2}
            opacity={0.3}
          />

          {/* Front wall */}
          <path
            d={frontWallPath}
            fill="url(#wall-front)"
          />
          <path
            d={frontWallPath}
            fill="none"
            stroke={CLAY_RIM}
            strokeWidth={1.5}
            strokeLinejoin="round"
          />

          {/* Windows on front wall */}
          {hp.windows.map((win, i) => (
            <g key={`win-${i}`}>
              <rect
                x={win.x - 6}
                y={win.y - 6}
                width={win.w + 12}
                height={win.h + 12}
                rx={10}
                fill={WALL_DARK}
              />
              <rect
                x={win.x}
                y={win.y}
                width={win.w}
                height={win.h}
                rx={6}
                fill="url(#window-grad)"
                filter="url(#window-glow)"
              />
              <ellipse
                cx={win.x + win.w * 0.3}
                cy={win.y + win.h * 0.25}
                rx={win.w * 0.12}
                ry={win.h * 0.1}
                fill="white"
                opacity={0.25}
              />
              <line
                x1={win.x + win.w / 2}
                y1={win.y + 4}
                x2={win.x + win.w / 2}
                y2={win.y + win.h - 4}
                stroke={WALL_DARK}
                strokeWidth={4}
                opacity={0.6}
              />
              <line
                x1={win.x + 4}
                y1={win.y + win.h / 2}
                x2={win.x + win.w - 4}
                y2={win.y + win.h / 2}
                stroke={WALL_DARK}
                strokeWidth={4}
                opacity={0.6}
              />
            </g>
          ))}

          {/* Door */}
          <g>
            <rect
              x={hp.door.x - 6}
              y={hp.door.y - 6}
              width={hp.door.w + 12}
              height={hp.door.h + 6}
              rx={8}
              fill={WALL_DARK}
            />
            <rect
              x={hp.door.x}
              y={hp.door.y}
              width={hp.door.w}
              height={hp.door.h}
              rx={5}
              fill="url(#door-grad)"
            />
            <rect
              x={hp.door.x + 8}
              y={hp.door.y + 8}
              width={hp.door.w * 0.35}
              height={hp.door.h - 16}
              rx={4}
              fill="white"
              opacity={0.06}
            />
            <circle
              cx={hp.door.x + hp.door.w * 0.78}
              cy={hp.door.y + hp.door.h * 0.52}
              r={8}
              fill={WALL_SHADOW}
              stroke="white"
              strokeWidth={1}
              strokeOpacity={0.15}
            />
          </g>
        </g>

        {/* ================================================ */}
        {/* EAVE FASCIA (connects roof to wall top)          */}
        {/* ================================================ */}
        <g opacity={fillOpacity}>
          {/* Front fascia band */}
          <polygon
            points={pointsToSvg(eaveFascia)}
            fill="url(#clay-eave-fascia)"
          />
          {/* Front fascia highlight line */}
          <line
            x1={slope[3].x + 5}
            y1={slope[3].y + 3}
            x2={slope[2].x - 5}
            y2={slope[2].y + 3}
            stroke={roofLight}
            strokeWidth={3}
            opacity={0.4}
          />
          {/* Right eave return (wraps around to gable side) */}
          <polygon
            points={pointsToSvg(rightEaveReturn)}
            fill={roofDarker}
            opacity={0.8}
          />
        </g>

        {/* ================================================ */}
        {/* GABLE-SIDE ROOF EDGE (thickness visible)         */}
        {/* ================================================ */}
        <polygon
          points={pointsToSvg(gableRoofEdge)}
          fill="url(#clay-gable-edge)"
          opacity={fillOpacity * 0.85}
        />

        {/* ================================================ */}
        {/* RIDGE CAP (3D strip along the peak)              */}
        {/* ================================================ */}
        <polygon
          points={pointsToSvg(ridgeCap)}
          fill="url(#clay-ridge-cap)"
          opacity={fillOpacity}
        />
        {/* Ridge cap highlight */}
        <line
          x1={slope[0].x + 10}
          y1={slope[0].y - 2}
          x2={slope[1].x - 10}
          y2={slope[1].y - 2}
          stroke="white"
          strokeWidth={2.5}
          opacity={fillOpacity * 0.2}
        />

        {/* ================================================ */}
        {/* FRONT SLOPE — BASE LAYER (weathered, clay tiles) */}
        {/* ================================================ */}
        <g
          clipPath="url(#roof-shape-clip)"
          filter={noiseOpacity > 0 ? "url(#roof-noise)" : undefined}
          opacity={fillOpacity}
        >
          <path d={slopePath} fill="url(#clay-roof-surface)" />
          {tiles.map((tile, i) => {
            const isAlt = (tile.row + tile.col) % 2 === 0;
            return (
              <path
                key={i}
                d={tile.path}
                fill={isAlt ? "url(#clay-tile-alt)" : "url(#clay-tile-main)"}
                opacity={0.92}
                stroke={roofDarker}
                strokeWidth={3}
                strokeOpacity={0.35}
                strokeLinejoin="round"
              />
            );
          })}
          <path d={slopePath} fill="url(#inner-highlight)" />
        </g>

        {/* ================================================ */}
        {/* COATED LAYER (clipped, reveals left to right)    */}
        {/* ================================================ */}
        {coatingProgress > 0 && (
          <g clipPath="url(#coating-clip)">
            <g clipPath="url(#roof-shape-clip)">
              <path d={slopePath} fill="url(#clay-coat-surface)" />
              {tiles.map((tile, i) => {
                const isAlt = (tile.row + tile.col) % 2 === 0;
                return (
                  <path
                    key={`c-${i}`}
                    d={tile.path}
                    fill={isAlt ? "url(#clay-coat-tile-alt)" : "url(#clay-coat-tile-main)"}
                    opacity={0.92}
                    stroke={coatDarker}
                    strokeWidth={3}
                    strokeOpacity={0.3}
                    strokeLinejoin="round"
                  />
                );
              })}
              <path d={slopePath} fill="url(#inner-highlight)" />
              <path d={slopePath} fill="url(#specular)" />
            </g>
          </g>
        )}

        {/* Slope rim light */}
        <path
          d={slopePath}
          fill="none"
          stroke={CLAY_RIM}
          strokeWidth={2}
          opacity={fillOpacity * 0.6}
          strokeLinejoin="round"
        />

        {/* Outline draw-in animation */}
        <path
          d={slopePath}
          fill="none"
          stroke="white"
          strokeWidth={5}
          strokeOpacity={interpolate(drawProgress, [0, 0.3, 1], [0.9, 0.5, 0.08], { extrapolateRight: "clamp" })}
          strokeDasharray={outlineLength}
          strokeDashoffset={outlineLength * (1 - drawProgress)}
          strokeLinejoin="round"
        />

        {/* Glow overlay (finale) */}
        {glowIntensity > 0 && (
          <path
            d={slopePath}
            fill={coatingColor || RED}
            opacity={glowIntensity * 0.35}
            filter="url(#roof-glow)"
          />
        )}

        {/* Wipe glow line */}
        {coatingProgress > 0.01 && coatingProgress < 0.99 && (
          <line
            x1={clipX}
            y1={slope[0].y - 60}
            x2={clipX}
            y2={slope[2].y + 60}
            stroke="white"
            strokeWidth={10}
            opacity={0.95}
            filter="url(#wipe-glow)"
          />
        )}
      </svg>
    </AbsoluteFill>
  );
};
