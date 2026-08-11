// ============================================================
// MinimalHouse — 3D projected house with face culling
// Supports buildProgress for line-drawing intro/outro animation
// ============================================================

import React from "react";
import { interpolate } from "remotion";
import { EASING_PRESETS } from "../../../../../utils/easing";
import {
  WHITE,
  REM_RED,
  HOUSE_VERTS,
  HOUSE_FACES,
  LEFT_ROOF_CORNERS,
  RIGHT_ROOF_CORNERS,
} from "../constants";
import type { CameraState, Projected } from "../projection";
import { project3D, isFrontFacing, faceMidDepth, toSvgPoints, surfacePoint } from "../projection";

const appleEase = EASING_PRESETS.appleEase;
const FILL_WALL = "rgba(255,255,255,0.03)";
const FILL_GABLE = "rgba(255,255,255,0.03)";
const STROKE_COLOR = "rgba(255,255,255,0.4)";
const STROKE_WIDTH = 2;
const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

interface MinimalHouseProps {
  cam: CameraState;
  roofColor: string;
  coatingProgress: number;
  buildProgress?: number;
}

function edgeLen(a: Projected, b: Projected): number {
  return Math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2);
}

// Front wall top (idx 0, edge 2) and back wall top (idx 2, edge 2)
// coincide with gable bottom — skip them
function isGableBottom(faceIdx: number, edgeIdx: number): boolean {
  return (faceIdx === 0 && edgeIdx === 2) || (faceIdx === 2 && edgeIdx === 2);
}

export const MinimalHouse: React.FC<MinimalHouseProps> = ({
  cam,
  roofColor,
  coatingProgress,
  buildProgress = 1,
}) => {
  // 1. Project all vertices
  const projected: Record<string, Projected> = {};
  for (const [key, v] of Object.entries(HOUSE_VERTS)) {
    projected[key] = project3D(v, cam);
  }

  // 2. Build renderable faces
  const renderFaces = HOUSE_FACES.map((face, i) => {
    const verts = face.verts.map((k) => projected[k]);
    return { ...face, verts, index: i, depth: faceMidDepth(verts) };
  });

  // 3. Face culling (right roof has reversed winding)
  const visibleFaces = renderFaces.filter((face, i) => {
    if (i === 7) return !isFrontFacing(face.verts);
    return isFrontFacing(face.verts);
  });

  // 4. Sort back-to-front
  visibleFaces.sort((a, b) => a.depth - b.depth);

  // 5. Coating clip polygons
  const buildClipPoly = (corners: typeof LEFT_ROOF_CORNERS) =>
    toSvgPoints([
      surfacePoint(-0.01, -0.01, corners, cam),
      surfacePoint(coatingProgress + 0.01, -0.01, corners, cam),
      surfacePoint(coatingProgress + 0.01, 1.01, corners, cam),
      surfacePoint(-0.01, 1.01, corners, cam),
    ]);

  const ridgeStart = projected.rF;
  const ridgeEnd = projected.rB;

  // === Build animation phases ===
  // Edge drawing: buildProgress 0→0.7
  const drawProg = interpolate(buildProgress, [0, 0.7], [0, 1], clamp);
  // Face fills: buildProgress 0.3→1.0
  const fillProg = interpolate(buildProgress, [0.3, 1.0], [0, 1], clamp);

  const getEdgeProg = (type: string, j: number) => {
    const base = type === "wall" ? 0 : 0.3;
    const d = base + j * 0.04;
    return interpolate(drawProg, [d, Math.min(d + 0.45, 1)], [0, 1], {
      ...clamp, easing: appleEase,
    });
  };

  const getFillOp = (type: string) => {
    const d = type === "wall" ? 0 : type === "gable" ? 0.1 : 0.25;
    return interpolate(fillProg, [d, Math.min(d + 0.6, 1)], [0, 1], {
      ...clamp, easing: appleEase,
    });
  };

  return (
    <g>
      <defs>
        {coatingProgress > 0 && (
          <>
            <clipPath id="coatingClipLeft">
              <polygon points={buildClipPoly(LEFT_ROOF_CORNERS)} />
            </clipPath>
            <clipPath id="coatingClipRight">
              <polygon points={buildClipPoly(RIGHT_ROOF_CORNERS)} />
            </clipPath>
          </>
        )}
        <filter id="rimGlow" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="6" />
        </filter>
      </defs>

      {/* Face fills (no stroke — edges drawn separately) */}
      {visibleFaces.map((face) => {
        const points = toSvgPoints(face.verts);
        const isRoof = face.type === "roof";
        const fill = isRoof ? roofColor : face.type === "wall" ? FILL_WALL : FILL_GABLE;
        const baseOp = isRoof ? 0.9 : 1;
        const fp = getFillOp(face.type);

        return (
          <React.Fragment key={`fill-${face.index}`}>
            <polygon
              points={points}
              fill={fill}
              stroke="none"
              opacity={baseOp * fp}
            />
            {isRoof && coatingProgress > 0 && (
              <polygon
                points={points}
                fill={REM_RED}
                stroke="none"
                opacity={0.9 * fp}
                clipPath={face.index === 6 ? "url(#coatingClipLeft)" : "url(#coatingClipRight)"}
              />
            )}
          </React.Fragment>
        );
      })}

      {/* Edge lines with stroke-dasharray draw animation */}
      {visibleFaces.map((face) =>
        face.verts.map((v, j) => {
          // Skip gable bottom edge (j=0), keep sloped edges (j=1,2)
          if (face.type === "gable" && j === 0) return null;
          // Skip gable bottom from wall faces
          if (isGableBottom(face.index, j)) return null;

          const next = face.verts[(j + 1) % face.verts.length];
          const l = edgeLen(v, next);
          const ep = getEdgeProg(face.type, j);
          if (ep <= 0) return null;

          return (
            <line
              key={`edge-${face.index}-${j}`}
              x1={v.x} y1={v.y}
              x2={next.x} y2={next.y}
              stroke={STROKE_COLOR}
              strokeWidth={STROKE_WIDTH}
              strokeDasharray={l}
              strokeDashoffset={l * (1 - ep)}
            />
          );
        }),
      )}

      {/* Ridge line */}
      {(() => {
        const l = edgeLen(ridgeStart, ridgeEnd);
        const rp = interpolate(drawProg, [0.5, 0.9], [0, 1], {
          ...clamp, easing: appleEase,
        });
        if (rp <= 0) return null;
        return (
          <>
            <line
              x1={ridgeStart.x} y1={ridgeStart.y}
              x2={ridgeEnd.x} y2={ridgeEnd.y}
              stroke="rgba(180,200,255,0.5)"
              strokeWidth={8}
              filter="url(#rimGlow)"
              strokeDasharray={l}
              strokeDashoffset={l * (1 - rp)}
            />
            <line
              x1={ridgeStart.x} y1={ridgeStart.y}
              x2={ridgeEnd.x} y2={ridgeEnd.y}
              stroke={WHITE}
              strokeWidth={3}
              opacity={0.9}
              strokeDasharray={l}
              strokeDashoffset={l * (1 - rp)}
            />
          </>
        );
      })()}

      {/* Rim light with draw animation */}
      {visibleFaces.map((face) =>
        face.verts.map((v, j) => {
          if (face.type === "gable" && j === 0) return null;
          if (isGableBottom(face.index, j)) return null;

          const next = face.verts[(j + 1) % face.verts.length];
          const l = edgeLen(v, next);
          const ep = getEdgeProg(face.type, j);
          if (ep <= 0) return null;

          return (
            <React.Fragment key={`rim-${face.index}-${j}`}>
              <line
                x1={v.x} y1={v.y} x2={next.x} y2={next.y}
                stroke="rgba(180,200,255,0.5)"
                strokeWidth={8}
                filter="url(#rimGlow)"
                strokeDasharray={l}
                strokeDashoffset={l * (1 - ep)}
              />
              <line
                x1={v.x} y1={v.y} x2={next.x} y2={next.y}
                stroke="rgba(200,220,255,0.85)"
                strokeWidth={3}
                strokeDasharray={l}
                strokeDashoffset={l * (1 - ep)}
              />
            </React.Fragment>
          );
        }),
      )}
    </g>
  );
};
