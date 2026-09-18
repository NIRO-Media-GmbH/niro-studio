// ============================================================
// Vollbild-Flagge für die Wischer in Video 03 (Farben wie FLAG_RECTS).
// Streifen 2 px überlappend und crispEdges → keine Haarlinien im Alpha.
// ============================================================
import React from "react";
import { BASE_H, BASE_W, RED } from "../lib";
import type { Wipe } from "./wipeTiming";

const W = BASE_W;
const H = BASE_H;
const O = 2;

const Band: React.FC<{ x: number; y: number; w: number; h: number; fill: string }> = ({ x, y, w, h, fill }) => (
  <rect x={x} y={y} width={w} height={h} fill={fill} shapeRendering="crispEdges" />
);

const PANELS: Record<Wipe["country"], React.ReactElement> = {
  PL: (
    <>
      <Band x={0} y={0} w={W} h={H / 2 + O} fill="#FFFFFF" />
      <Band x={0} y={H / 2} w={W} h={H / 2} fill="#DC143C" />
    </>
  ),
  HU: (
    <>
      <Band x={0} y={0} w={W} h={H / 3 + O} fill="#CD2A3E" />
      <Band x={0} y={H / 3} w={W} h={H / 3 + O} fill="#FFFFFF" />
      <Band x={0} y={(2 * H) / 3} w={W} h={H / 3} fill="#436F4D" />
    </>
  ),
  RO: (
    <>
      <Band x={0} y={0} w={W / 3 + O} h={H} fill="#002B7F" />
      <Band x={W / 3} y={0} w={W / 3 + O} h={H} fill="#FCD116" />
      <Band x={(2 * W) / 3} y={0} w={W / 3} h={H} fill="#CE1126" />
    </>
  ),
  CZ: (
    <>
      <Band x={0} y={0} w={W} h={H / 2 + O} fill="#FFFFFF" />
      <Band x={0} y={H / 2} w={W} h={H / 2} fill="#D7141A" />
      <polygon points={`0,0 ${W / 2},${H / 2} 0,${H}`} fill="#11457E" />
    </>
  ),
  CRAISS: <Band x={0} y={0} w={W} h={H} fill={RED} />,
};

export const FlagPanel: React.FC<{ country: Wipe["country"]; offset: number }> = ({ country, offset }) => (
  <svg
    width={W}
    height={H}
    viewBox={`0 0 ${W} ${H}`}
    style={{ position: "absolute", top: 0, left: 0, transform: `translateX(${offset * W}px)` }}
  >
    {PANELS[country]}
  </svg>
);
