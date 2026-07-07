// ============================================================
// CoatingBloom — Bloom glow during Scene 4 coating
// Blurred red overlay that intensifies with coating progress
// ============================================================

import React from "react";
import { interpolate } from "remotion";
import { REM_RED, LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS, SCENES } from "../constants";
import type { CameraState } from "../projection";
import { surfacePoint, toSvgPoints } from "../projection";

interface CoatingBloomProps {
  coatingProgress: number;
  cam: CameraState;
  frame: number;
}

export const CoatingBloom: React.FC<CoatingBloomProps> = ({
  coatingProgress,
  cam,
  frame,
}) => {
  if (coatingProgress <= 0) return null;

  const bloomFadeIn = interpolate(coatingProgress, [0, 0.1, 0.5], [0, 0.3, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bloomFadeOut = interpolate(
    frame,
    [SCENES.coating.end - 30, SCENES.coating.end + 60],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const bloomOpacity = bloomFadeIn * bloomFadeOut * 0.5;

  if (bloomOpacity <= 0.01) return null;

  const buildClipPoly = (corners: typeof LEFT_ROOF_CORNERS) =>
    toSvgPoints([
      surfacePoint(-0.02, -0.02, corners, cam),
      surfacePoint(coatingProgress + 0.02, -0.02, corners, cam),
      surfacePoint(coatingProgress + 0.02, 1.02, corners, cam),
      surfacePoint(-0.02, 1.02, corners, cam),
    ]);

  const buildFullPoly = (corners: typeof LEFT_ROOF_CORNERS) =>
    toSvgPoints([
      surfacePoint(0, 0, corners, cam),
      surfacePoint(1, 0, corners, cam),
      surfacePoint(1, 1, corners, cam),
      surfacePoint(0, 1, corners, cam),
    ]);

  return (
    <g opacity={bloomOpacity}>
      <defs>
        <filter id="coatingBloom" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="40" />
        </filter>
        <clipPath id="bloomClipL">
          <polygon points={buildClipPoly(LEFT_ROOF_CORNERS)} />
        </clipPath>
        <clipPath id="bloomClipR">
          <polygon points={buildClipPoly(RIGHT_ROOF_CORNERS)} />
        </clipPath>
      </defs>
      <polygon
        points={buildFullPoly(LEFT_ROOF_CORNERS)}
        fill={REM_RED}
        clipPath="url(#bloomClipL)"
        filter="url(#coatingBloom)"
      />
      <polygon
        points={buildFullPoly(RIGHT_ROOF_CORNERS)}
        fill={REM_RED}
        clipPath="url(#bloomClipR)"
        filter="url(#coatingBloom)"
      />
    </g>
  );
};
