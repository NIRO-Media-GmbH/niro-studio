// ============================================================
// CraneRig — Szene „Kran" (Spezialfahrzeug neben der Halle)
// Line-Art-Autokran: Fahrzeug, Teleskopausleger, Seil + Korb.
// Der Ausleger folgt der Beschichtungskante (wipeU) über das Dach.
// ============================================================

import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { EASING_PRESETS } from "../../../../../utils/easing";
import { REM_RED, CRANE_BASE, CRANE_TIP } from "../constants";
import type { CameraState, Projected, Vec3 } from "../projection";
import { project3D } from "../projection";

const appleEase = EASING_PRESETS.appleEase;
const STROKE = "rgba(255,255,255,0.55)";
const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

interface CraneRigProps {
  cam: CameraState;
  drawProgress: number; // 0→1 Line-Draw des Krans
  wipeU: number;        // Beschichtungsfortschritt (u entlang Firstrichtung)
}

function edgeLen(a: Projected, b: Projected): number {
  return Math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2);
}

const DrawnLine: React.FC<{
  a: Projected;
  b: Projected;
  progress: number;
  stroke?: string;
  width?: number;
  opacity?: number;
}> = ({ a, b, progress, stroke = STROKE, width = 4, opacity = 1 }) => {
  if (progress <= 0) return null;
  const l = edgeLen(a, b);
  return (
    <line
      x1={a.x} y1={a.y} x2={b.x} y2={b.y}
      stroke={stroke}
      strokeWidth={width}
      strokeLinecap="round"
      strokeDasharray={l}
      strokeDashoffset={l * (1 - progress)}
      opacity={opacity}
    />
  );
};

export const CraneRig: React.FC<CraneRigProps> = ({ cam, drawProgress, wipeU }) => {
  const frame = useCurrentFrame();

  const [bx, , bz] = CRANE_BASE;
  const tipY = CRANE_TIP[1];

  // Auslegerspitze wandert mit der Beschichtungskante entlang der Halle (z-Achse)
  const tipZ = interpolate(wipeU, [0, 1], [-460, 420], clamp);
  const bob = Math.sin(frame * 0.07) * 4; // leichtes Wippen des Seils

  // --- 3D-Punkte ---
  const truckH = 65;
  const p = (v: Vec3) => project3D(v, cam);

  // Fahrzeug (Kastenumriss)
  const t1 = p([bx - 115, 0, bz - 140]);
  const t2 = p([bx + 115, 0, bz - 140]);
  const t3 = p([bx + 115, 0, bz + 140]);
  const t4 = p([bx - 115, 0, bz + 140]);
  const u1 = p([bx - 115, truckH, bz - 140]);
  const u2 = p([bx + 115, truckH, bz - 140]);
  const u3 = p([bx + 115, truckH, bz + 140]);
  const u4 = p([bx - 115, truckH, bz + 140]);

  // Drehkranz + Ausleger
  const pivot = p([bx, truckH + 25, bz]);
  const pivotTop = p([bx, truckH + 50, bz]);
  const tip = p([0, tipY, tipZ]);
  // Parallelgurt des Teleskopauslegers (leicht versetzt)
  const tipLow = p([0, tipY - 26, tipZ]);
  const pivotLow = p([bx, truckH + 4, bz]);

  // Seil + Arbeitskorb unter der Spitze
  const hookTop = p([0, tipY - 8, tipZ]);
  const hook = p([0, 268, tipZ]);
  const basketA = p([-34, 268, tipZ - 30]);
  const basketB = p([34, 268, tipZ - 30]);
  const basketC = p([34, 240, tipZ - 30]);
  const basketD = p([-34, 240, tipZ - 30]);

  // --- Draw-Staffelung ---
  const stage = (from: number, to: number) =>
    interpolate(drawProgress, [from, to], [0, 1], { ...clamp, easing: appleEase });

  const truckProg = stage(0, 0.4);
  const boomProg = stage(0.3, 0.75);
  const cableProg = stage(0.7, 1);

  return (
    <g>
      {/* Fahrzeug */}
      <DrawnLine a={t1} b={t2} progress={truckProg} />
      <DrawnLine a={t2} b={t3} progress={truckProg} />
      <DrawnLine a={t3} b={t4} progress={truckProg} />
      <DrawnLine a={t4} b={t1} progress={truckProg} />
      <DrawnLine a={t1} b={u1} progress={truckProg} />
      <DrawnLine a={t2} b={u2} progress={truckProg} />
      <DrawnLine a={t3} b={u3} progress={truckProg} />
      <DrawnLine a={t4} b={u4} progress={truckProg} />
      <DrawnLine a={u1} b={u2} progress={truckProg} />
      <DrawnLine a={u2} b={u3} progress={truckProg} />
      <DrawnLine a={u3} b={u4} progress={truckProg} />
      <DrawnLine a={u4} b={u1} progress={truckProg} />

      {/* Drehkranz */}
      <DrawnLine a={pivot} b={pivotTop} progress={truckProg} width={6} />

      {/* Teleskopausleger — REM-Rot mit hellem Unterzug (hebt sich vom roten Dach ab) */}
      <DrawnLine a={pivotTop} b={tip} progress={boomProg} stroke="rgba(220,235,255,0.9)" width={11} opacity={0.85} />
      <DrawnLine a={pivotTop} b={tip} progress={boomProg} stroke={REM_RED} width={6} opacity={1} />
      <DrawnLine a={pivotLow} b={tipLow} progress={boomProg} stroke={STROKE} width={3.5} opacity={0.7} />

      {/* Seil + Korb (wippt leicht) */}
      <g transform={`translate(0 ${bob})`}>
        <DrawnLine a={hookTop} b={hook} progress={cableProg} width={2.5} opacity={0.8} />
        <DrawnLine a={basketA} b={basketB} progress={cableProg} width={4} />
        <DrawnLine a={basketB} b={basketC} progress={cableProg} width={4} />
        <DrawnLine a={basketC} b={basketD} progress={cableProg} width={4} />
        <DrawnLine a={basketD} b={basketA} progress={cableProg} width={4} />
        {cableProg > 0.5 && (
          <circle cx={hook.x} cy={hook.y} r={7} fill={REM_RED} opacity={cableProg} />
        )}
      </g>
    </g>
  );
};
