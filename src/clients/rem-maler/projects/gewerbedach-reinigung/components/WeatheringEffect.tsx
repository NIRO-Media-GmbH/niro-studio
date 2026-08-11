// ============================================================
// WeatheringEffect — Scene 2 (frames 125–250)
// Crack paths drawn on the roof + dust particles rising (3D)
// ============================================================

import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, random } from "remotion";
import { EASING_PRESETS } from "../../../../../utils/easing";
import { WHITE, SCENES, LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS } from "../constants";
import type { CameraState } from "../projection";
import { surfacePoint } from "../projection";

const appleEase = EASING_PRESETS.appleEase;
const CRACK_COUNT = 8;
const DUST_COUNT = 15;
const SCENE = SCENES.weathering;

interface CrackDef {
  segments: Array<{ u: number; v: number }>;
  entryDelay: number;
}

interface DustDef {
  u: number;
  v: number;
  radius: number;
  delay: number;
}

interface WeatheringEffectProps {
  sceneProgress: number;
  cam: CameraState;
}

function generateCrackDef(index: number): CrackDef {
  const segCount = 3 + Math.floor(random(`crack-seg-${index}`) * 3);
  const margin = 0.1;
  const points: Array<{ u: number; v: number }> = [];

  let u = margin + random(`crack-su-${index}`) * (1 - margin * 2);
  let v = margin + random(`crack-sv-${index}`) * (1 - margin * 2);
  points.push({ u, v });

  for (let s = 0; s < segCount; s++) {
    const du = (random(`crack-du-${index}-${s}`) - 0.5) * 0.2;
    const dv = random(`crack-dv-${index}-${s}`) * 0.15 + 0.03;
    u = Math.max(margin, Math.min(1 - margin, u + du));
    v = Math.max(margin, Math.min(1 - margin, v + dv));
    points.push({ u, v });
  }

  return { segments: points, entryDelay: index * 15 };
}

export const WeatheringEffect: React.FC<WeatheringEffectProps> = ({
  sceneProgress,
  cam,
}) => {
  const frame = useCurrentFrame();
  const sceneFrame = frame - SCENE.start;

  const cracks = useMemo<CrackDef[]>(() => {
    return Array.from({ length: CRACK_COUNT }, (_, i) => generateCrackDef(i));
  }, []);

  const dustParticles = useMemo<DustDef[]>(() => {
    const margin = 0.1;
    return Array.from({ length: DUST_COUNT }, (_, i) => ({
      u: margin + random(`dust-u-${i}`) * (1 - margin * 2),
      v: margin + random(`dust-v-${i}`) * (1 - margin * 2),
      radius: 3 + random(`dust-r-${i}`) * 5,
      delay: Math.floor(random(`dust-del-${i}`) * 50),
    }));
  }, []);

  const fadeIn = interpolate(sceneProgress, [0, 0.1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  return (
    <g opacity={fadeIn}>
      {/* Crack paths on both roof slopes */}
      {[LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS].map((corners, si) =>
        cracks.map((crack, i) => {
          const drawStart = crack.entryDelay + si * 20;
          const drawEnd = drawStart + 40;
          const drawProgress = interpolate(sceneFrame, [drawStart, drawEnd], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: appleEase,
          });

          if (drawProgress <= 0) return null;

          const projected = crack.segments.map((s) =>
            surfacePoint(s.u, s.v, corners, cam),
          );

          const d = projected
            .map((p, j) => `${j === 0 ? "M" : "L"} ${Math.round(p.x)} ${Math.round(p.y)}`)
            .join(" ");

          let totalLength = 0;
          for (let j = 1; j < projected.length; j++) {
            const dx = projected[j].x - projected[j - 1].x;
            const dy = projected[j].y - projected[j - 1].y;
            totalLength += Math.sqrt(dx * dx + dy * dy);
          }
          totalLength = Math.max(totalLength, 1);

          return (
            <path
              key={`crack-${si}-${i}`}
              d={d}
              fill="none"
              stroke={WHITE}
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeDasharray={totalLength}
              strokeDashoffset={totalLength * (1 - drawProgress)}
              opacity={0.7 * drawProgress}
            />
          );
        }),
      )}

      {/* Dust particles on both roof slopes */}
      {[LEFT_ROOF_CORNERS, RIGHT_ROOF_CORNERS].map((corners, si) =>
        dustParticles.map((dust, i) => {
          const localStart = dust.delay + si * 10;
          const localEnd = localStart + 80;
          const dustProgress = interpolate(sceneFrame, [localStart, localEnd], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          if (dustProgress <= 0) return null;

          const p = surfacePoint(dust.u, dust.v, corners, cam);
          const y = p.y - dustProgress * 120;
          const opacity = interpolate(
            dustProgress,
            [0, 0.15, 0.7, 1],
            [0, 0.3, 0.25, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
          );

          return (
            <circle
              key={`dust-${si}-${i}`}
              cx={p.x}
              cy={y}
              r={dust.radius * (cam.scale / 1.8)}
              fill={WHITE}
              opacity={opacity}
            />
          );
        }),
      )}
    </g>
  );
};
