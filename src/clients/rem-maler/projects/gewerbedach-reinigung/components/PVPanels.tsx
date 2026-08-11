// ============================================================
// PVPanels — Szene „Ergebnis"
// Photovoltaik-Module auf der rechten Dachfläche, gestaffelter
// Aufbau + Glanz-Sweep („richtig gereinigt")
// ============================================================

import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { EASING_PRESETS } from "../../../../../utils/easing";
import { WHITE, PV_BLUE, PV_CELL, RIGHT_ROOF_CORNERS } from "../constants";
import type { CameraState } from "../projection";
import { surfacePoint, toSvgPoints } from "../projection";

const appleEase = EASING_PRESETS.appleEase;

const ROWS = 3;
const COLS = 6;
const U0 = 0.14;
const U1 = 0.86;
const V0 = 0.18;
const V1 = 0.82;
const GAP = 0.16; // Anteil Lücke zwischen Modulen

// Absoluter Frame: „Photovoltaikanlage … richtig gereinigt" (88,6 s)
export const PV_APPEAR_FRAME = 2216;
const STAGGER = 4;
const PANEL_ENTER = 16;
const SHINE_START = PV_APPEAR_FRAME + ROWS * COLS * STAGGER + PANEL_ENTER; // ≈ 2304
const SHINE_DUR = 55;

interface PVPanelsProps {
  cam: CameraState;
}

export const PVPanels: React.FC<PVPanelsProps> = ({ cam }) => {
  const frame = useCurrentFrame();
  if (frame < PV_APPEAR_FRAME) return null;

  const du = (U1 - U0) / COLS;
  const dv = (V1 - V0) / ROWS;

  // Glanz-Sweep läuft einmal diagonal über die Modulfläche
  const shineU = interpolate(frame, [SHINE_START, SHINE_START + SHINE_DUR], [U0 - 0.15, U1 + 0.15], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  const panels: React.ReactNode[] = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const idx = r * COLS + c;
      const enter = interpolate(
        frame,
        [PV_APPEAR_FRAME + idx * STAGGER, PV_APPEAR_FRAME + idx * STAGGER + PANEL_ENTER],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase },
      );
      if (enter <= 0) continue;

      const uA = U0 + c * du + du * GAP * 0.5;
      const uB = U0 + (c + 1) * du - du * GAP * 0.5;
      const vA = V0 + r * dv + dv * GAP * 0.5;
      const vB = V0 + (r + 1) * dv - dv * GAP * 0.5;

      // Panel wächst vom Mittelpunkt auf
      const um = (uA + uB) / 2;
      const vm = (vA + vB) / 2;
      const ua = um + (uA - um) * enter;
      const ub = um + (uB - um) * enter;
      const va = vm + (vA - vm) * enter;
      const vb = vm + (vB - vm) * enter;

      const quad = toSvgPoints([
        surfacePoint(ua, va, RIGHT_ROOF_CORNERS, cam),
        surfacePoint(ub, va, RIGHT_ROOF_CORNERS, cam),
        surfacePoint(ub, vb, RIGHT_ROOF_CORNERS, cam),
        surfacePoint(ua, vb, RIGHT_ROOF_CORNERS, cam),
      ]);

      // Glanz: Modul leuchtet kurz auf, wenn der Sweep vorbeiläuft
      const shineDist = Math.abs(um - shineU);
      const shine = interpolate(shineDist, [0, 0.12], [0.5, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });

      panels.push(
        <g key={`pv-${idx}`} opacity={enter}>
          <polygon
            points={quad}
            fill={idx % 2 === 0 ? PV_BLUE : PV_CELL}
            stroke="rgba(180,210,255,0.65)"
            strokeWidth={2.5}
            opacity={0.92}
          />
          {shine > 0.01 && <polygon points={quad} fill={WHITE} opacity={shine} />}
        </g>,
      );
    }
  }

  return <g>{panels}</g>;
};
