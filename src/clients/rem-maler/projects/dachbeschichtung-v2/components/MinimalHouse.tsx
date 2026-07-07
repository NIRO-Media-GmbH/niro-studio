// ============================================================
// MinimalHouse — 3D projected house with face culling
// Central visual element for the Dachbeschichtung V2 animation
// ============================================================

import React from "react";
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

const FILL_WALL = "rgba(255,255,255,0.03)";
const FILL_GABLE = "rgba(255,255,255,0.03)";
const STROKE_COLOR = "rgba(255,255,255,0.4)";
const STROKE_WIDTH = 2;

interface MinimalHouseProps {
  cam: CameraState;
  roofColor: string;
  coatingProgress: number;
}

export const MinimalHouse: React.FC<MinimalHouseProps> = ({
  cam,
  roofColor,
  coatingProgress,
}) => {
  // 1. Project all vertices
  const projected: Record<string, Projected> = {};
  for (const [key, v] of Object.entries(HOUSE_VERTS)) {
    projected[key] = project3D(v, cam);
  }

  // 2. Build renderable faces with projected vertices
  const renderFaces = HOUSE_FACES.map((face, i) => {
    const verts = face.verts.map((k) => projected[k]);
    return { ...face, verts, index: i, depth: faceMidDepth(verts) };
  });

  // 3. Filter front-facing only (face culling)
  // Right roof has reversed winding, so we invert the check for it
  const visibleFaces = renderFaces.filter((face, i) => {
    // Index 7 is the right roof slope (reversed winding in our data)
    if (i === 7) return !isFrontFacing(face.verts);
    return isFrontFacing(face.verts);
  });

  // 4. Sort back-to-front (painter's algorithm)
  visibleFaces.sort((a, b) => a.depth - b.depth);

  // 5. Compute coating clip polygons per roof slope (surface-based, matches CoatingWipe)
  const buildClipPoly = (corners: typeof LEFT_ROOF_CORNERS) =>
    toSvgPoints([
      surfacePoint(-0.01, -0.01, corners, cam),
      surfacePoint(coatingProgress + 0.01, -0.01, corners, cam),
      surfacePoint(coatingProgress + 0.01, 1.01, corners, cam),
      surfacePoint(-0.01, 1.01, corners, cam),
    ]);

  // Ridge line projected endpoints
  const ridgeStart = projected.rF;
  const ridgeEnd = projected.rB;

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
      </defs>

      {/* Render faces back-to-front */}
      {visibleFaces.map((face) => {
        const points = toSvgPoints(face.verts);
        const isRoof = face.type === "roof";

        const fill = isRoof
          ? roofColor
          : face.type === "wall"
            ? FILL_WALL
            : FILL_GABLE;
        const opacity = isRoof ? 0.9 : 1;

        return (
          <React.Fragment key={face.index}>
            {/* Base face */}
            <polygon
              points={points}
              fill={fill}
              stroke={STROKE_COLOR}
              strokeWidth={STROKE_WIDTH}
              opacity={opacity}
            />
            {/* Coating overlay on roof faces */}
            {isRoof && coatingProgress > 0 && (
              <polygon
                points={points}
                fill={REM_RED}
                stroke={STROKE_COLOR}
                strokeWidth={STROKE_WIDTH}
                opacity={0.9}
                clipPath={face.index === 6 ? "url(#coatingClipLeft)" : "url(#coatingClipRight)"}
              />
            )}
          </React.Fragment>
        );
      })}

      {/* Ridge line (emphasized) */}
      <line
        x1={ridgeStart.x}
        y1={ridgeStart.y}
        x2={ridgeEnd.x}
        y2={ridgeEnd.y}
        stroke={WHITE}
        strokeWidth={3}
        opacity={0.9}
      />
    </g>
  );
};
