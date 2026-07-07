// ============================================================
// REM Dachbeschichtung V2 — Constants
// Minimalist / Apple-style animation with 3D camera orbit
// ============================================================

import type { Vec3 } from "./projection";

// --- Colors ---
export const BG = "#0D0D1A";
export const REM_RED = "#D83C31";
export const WHITE = "#FFFFFF";
export const WHITE_60 = "rgba(255,255,255,0.6)";
export const WHITE_30 = "rgba(255,255,255,0.3)";
export const WHITE_05 = "rgba(255,255,255,0.05)";
export const CREAM = "#F5E6D0";
export const GREY_WEATHERED = "#6B6B5A";
export const TERRACOTTA = "#B85C38";
export const TERRACOTTA_DIRTY = "#6B4432";
export const MOSS_GREEN = "#4A7A42";
export const LICHEN_GREEN = "#6B8A42";
export const WATER_BLUE = "#5AADFF";

// --- Canvas ---
export const W = 3840;
export const H = 2160;
export const FPS = 25;
export const INTRO_DUR = 75;
export const OUTRO_DUR = 75;
export const TOTAL_FRAMES = 1138;

// --- Scene Timing ---
export const OVERLAP = 30;

export const SCENES = {
  weather:    { start: 75,  end: 200, dur: 125 },
  weathering: { start: 200, end: 325, dur: 125 },
  moss:       { start: 325, end: 500, dur: 175 },
  coating:    { start: 500, end: 675, dur: 175 },
  water:      { start: 675, end: 913, dur: 238 },
  finale:     { start: 913, end: 1063, dur: 150 },
} as const;

export const SCENES_OV = {
  weather:    { start: 75,  end: 215, dur: 140 },
  weathering: { start: 185, end: 340, dur: 155 },
  moss:       { start: 310, end: 515, dur: 205 },
  coating:    { start: 485, end: 690, dur: 205 },
  water:      { start: 660, end: 928, dur: 268 },
  finale:     { start: 898, end: 1063, dur: 165 },
} as const;

// --- 3D House Geometry ---
const HOUSE_WIDTH = 220;
const HOUSE_DEPTH = 320;
const WALL_HEIGHT = 260;
const ROOF_PEAK = 170;

export const HOUSE_VERTS: Record<string, Vec3> = {
  // Ground corners
  gFL: [-HOUSE_WIDTH, 0, -HOUSE_DEPTH],
  gFR: [HOUSE_WIDTH, 0, -HOUSE_DEPTH],
  gBR: [HOUSE_WIDTH, 0, HOUSE_DEPTH],
  gBL: [-HOUSE_WIDTH, 0, HOUSE_DEPTH],
  // Wall top corners
  wFL: [-HOUSE_WIDTH, WALL_HEIGHT, -HOUSE_DEPTH],
  wFR: [HOUSE_WIDTH, WALL_HEIGHT, -HOUSE_DEPTH],
  wBR: [HOUSE_WIDTH, WALL_HEIGHT, HOUSE_DEPTH],
  wBL: [-HOUSE_WIDTH, WALL_HEIGHT, HOUSE_DEPTH],
  // Ridge endpoints
  rF: [0, WALL_HEIGHT + ROOF_PEAK, -HOUSE_DEPTH],
  rB: [0, WALL_HEIGHT + ROOF_PEAK, HOUSE_DEPTH],
};

export interface HouseFace {
  verts: string[];
  type: "wall" | "roof" | "gable";
}

// Vertex winding: counter-clockwise when viewed from outside
export const HOUSE_FACES: HouseFace[] = [
  // Walls
  { verts: ["gFL", "gFR", "wFR", "wFL"], type: "wall" },  // front
  { verts: ["gFR", "gBR", "wBR", "wFR"], type: "wall" },  // right
  { verts: ["gBR", "gBL", "wBL", "wBR"], type: "wall" },  // back
  { verts: ["gBL", "gFL", "wFL", "wBL"], type: "wall" },  // left
  // Gable triangles
  { verts: ["wFL", "wFR", "rF"],         type: "gable" },  // front gable
  { verts: ["wBR", "wBL", "rB"],         type: "gable" },  // back gable
  // Roof slopes
  { verts: ["wFL", "rF", "rB", "wBL"],   type: "roof" },   // left roof
  { verts: ["wFR", "rF", "rB", "wBR"],   type: "roof" },   // right roof (reversed winding)
];

// Roof surface corners for surfacePoint() — left slope
// Order: [topLeft, topRight, bottomRight, bottomLeft]
// "top" = ridge, "bottom" = eave
export const LEFT_ROOF_CORNERS: Vec3[] = [
  HOUSE_VERTS.rF,   // top-left (ridge front)
  HOUSE_VERTS.rB,   // top-right (ridge back)
  HOUSE_VERTS.wBL,  // bottom-right (eave back)
  HOUSE_VERTS.wFL,  // bottom-left (eave front)
];

export const RIGHT_ROOF_CORNERS: Vec3[] = [
  HOUSE_VERTS.rF,   // top-left (ridge front)
  HOUSE_VERTS.rB,   // top-right (ridge back)
  HOUSE_VERTS.wBR,  // bottom-right (eave back)
  HOUSE_VERTS.wFR,  // bottom-left (eave front)
];

// --- Camera Keyframes ---
// Yaw/pitch in degrees (converted to radians at runtime)
// Drift during holds leads INTO the next snap direction (prevents velocity reversal).
export const CAMERA_KEYFRAMES = [
  // Scene 1 — opening 3/4 view, drift toward scene 2 (+yaw)
  { frame: 75,   yaw: -35, pitch: 22, scale: 0.80 },
  { frame: 85,   yaw: -35, pitch: 22, scale: 0.85 },
  { frame: 195,  yaw: -32, pitch: 23, scale: 0.87 },
  // Scene 2 — SNAP close + rotated, drift toward scene 3 (-yaw)
  { frame: 210,  yaw: 15,  pitch: 30, scale: 0.95 },
  { frame: 320,  yaw: 12,  pitch: 29, scale: 0.93 },
  // Scene 3 — SNAP opposite side for moss, drift toward scene 4 (+yaw)
  { frame: 335,  yaw: -50, pitch: 28, scale: 0.95 },
  { frame: 495,  yaw: -45, pitch: 30, scale: 0.97 },
  // Scene 4 — SNAP elevated for coating (both slopes visible), drift toward scene 5 (+yaw)
  { frame: 510,  yaw: 12,  pitch: 35, scale: 0.88 },
  { frame: 670,  yaw: 17,  pitch: 33, scale: 0.86 },
  // Scene 5 — SNAP side view for water, drift toward scene 6 (-yaw)
  { frame: 685,  yaw: 40,  pitch: 20, scale: 0.95 },
  { frame: 908,  yaw: 35,  pitch: 21, scale: 0.93 },
  // Scene 6 — SNAP back for finale, gentle settle
  { frame: 923,  yaw: -20, pitch: 25, scale: 0.90 },
  { frame: 1063, yaw: -20, pitch: 25, scale: 0.90 },
] as const;

// Base scale multiplier for the house (pixels per unit)
export const HOUSE_BASE_SCALE = 1.8;

// --- Slide Text (structured: tag + headline + bullets) ---
export const SLIDES = [
  {
    tag: "Ursachen",
    headline: ["Warum leidet", "Ihr Dach?"],
    bullets: ["Saurer Regen", "UV-Strahlung", "Frost & Temperaturschwankungen"],
    startFrame: 83,
    exitFrame: 183,
    x: 350,
    y: 580,
  },
  {
    tag: "Verwitterung",
    headline: ["Die Oberfläche", "gibt nach"],
    bullets: ["Ziegel werden porös & rau", "Feuchtigkeit dringt ein", "Risse entstehen"],
    startFrame: 208,
    exitFrame: 310,
    x: 350,
    y: 580,
  },
  {
    tag: "Befall",
    headline: ["Idealer", "Nährboden"],
    bullets: ["Algen siedeln sich an", "Moos & Flechten folgen", "Substanz wird angegriffen"],
    startFrame: 333,
    exitFrame: 480,
    x: 350,
    y: 580,
  },
  {
    tag: "Lösung",
    headline: ["REM", "Dachbeschichtung"],
    bullets: ["Professionelle Versiegelung", "Schützt von außen & innen", "Langfristig wirksam"],
    startFrame: 513,
    exitFrame: 653,
    x: 1750,
    y: 580,
  },
  {
    tag: "Wasser perlt ab",
    headline: ["Glatt. Dicht.", "Trocken."],
    bullets: ["Wasser läuft sofort ab", "Kein Bewuchs mehr möglich", "Trotzdem atmungsaktiv"],
    startFrame: 685,
    exitFrame: 893,
    x: 1750,
    y: 580,
  },
  {
    tag: "Ergebnis",
    headline: ["Ihr Dach.", "Dauerhaft geschützt."],
    bullets: ["Professionell & erprobt", "Atmungsaktiv & wasserabweisend", "REM Dachbeschichtung"],
    startFrame: 926,
    exitFrame: undefined,
    x: 1750,
    y: 580,
  },
];
