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
export const TOTAL_FRAMES = 925;

// --- Scene Timing ---
export const OVERLAP = 30;

export const SCENES = {
  weather:    { start: 0,   end: 125, dur: 125 },
  weathering: { start: 125, end: 250, dur: 125 },
  moss:       { start: 250, end: 425, dur: 175 },
  coating:    { start: 425, end: 600, dur: 175 },
  water:      { start: 600, end: 775, dur: 175 },
  finale:     { start: 775, end: 925, dur: 150 },
} as const;

export const SCENES_OV = {
  weather:    { start: 0,   end: 140, dur: 140 },
  weathering: { start: 110, end: 265, dur: 155 },
  moss:       { start: 235, end: 440, dur: 205 },
  coating:    { start: 410, end: 615, dur: 205 },
  water:      { start: 585, end: 790, dur: 205 },
  finale:     { start: 760, end: 925, dur: 165 },
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
  { frame: 0,   yaw: -35, pitch: 22, scale: 0.80 },
  { frame: 10,  yaw: -35, pitch: 22, scale: 0.85 },
  { frame: 120, yaw: -32, pitch: 23, scale: 0.87 },
  // Scene 2 — SNAP close + rotated, drift toward scene 3 (-yaw)
  { frame: 135, yaw: 15,  pitch: 30, scale: 0.95 },
  { frame: 245, yaw: 12,  pitch: 29, scale: 0.93 },
  // Scene 3 — SNAP opposite side for moss, drift toward scene 4 (+yaw)
  { frame: 260, yaw: -50, pitch: 28, scale: 0.95 },
  { frame: 420, yaw: -45, pitch: 30, scale: 0.97 },
  // Scene 4 — SNAP elevated for coating (both slopes visible), drift toward scene 5 (+yaw)
  { frame: 435, yaw: 12,  pitch: 35, scale: 0.88 },
  { frame: 595, yaw: 17,  pitch: 33, scale: 0.86 },
  // Scene 5 — SNAP side view for water, drift toward scene 6 (-yaw)
  { frame: 610, yaw: 40,  pitch: 20, scale: 0.95 },
  { frame: 770, yaw: 35,  pitch: 21, scale: 0.93 },
  // Scene 6 — SNAP back for finale, gentle settle
  { frame: 785, yaw: -20, pitch: 25, scale: 0.90 },
  { frame: 925, yaw: -20, pitch: 25, scale: 0.90 },
] as const;

// Base scale multiplier for the house (pixels per unit)
export const HOUSE_BASE_SCALE = 1.8;

// --- Text ---
// Text synced to voiceover SRT (offset 60s, 25fps)
export const TEXT = {
  scene1: {
    // "Das Problem?" @f5, "Sauerer Regen, Sonne und Frost..." @f42
    line1: { words: ["Ihr", "Dach."], startFrame: 5, y: 500, fontSize: 120, x: 200 },
    line2: { words: ["Regen.", "Sonne.", "Frost."], startFrame: 42, y: 620, fontSize: 80, color: WHITE_60, x: 200 },
    exitFrame: 110,
  },
  scene2: {
    // "...verwittern" @f116, "Feuchtigkeit auf" @f184
    line1: { words: ["Verwitterung."], startFrame: 130, y: 500, fontSize: 100, x: 200 },
    line2: { words: ["Feuchtigkeit", "dringt", "ein."], startFrame: 184, y: 630, fontSize: 80, staggerFrames: 12, x: 200 },
    exitFrame: 240,
  },
  scene3: {
    // "Algen, Moos und Flechten" @f273, "langfristig an" @f343
    line1: { words: ["Moos.", "Algen.", "Flechten."], startFrame: 273, y: 500, fontSize: 100, x: 200 },
    line2: { words: ["Langfristiger", "Schaden."], startFrame: 343, y: 630, fontSize: 70, color: "rgba(255,255,255,0.5)", x: 200 },
    exitFrame: 405,
  },
  scene4: {
    // "Unsere Lösung?" @f413, "professionelle Dachbeschichtung" @f451
    line1: { words: ["Professionelle"], startFrame: 440, y: 480, fontSize: 90, x: 200 },
    line2: { words: ["Dachbeschichtung."], startFrame: 455, y: 610, fontSize: 120, color: REM_RED, fontWeight: 700, glow: true, x: 200 },
    exitFrame: 560,
  },
  scene5: {
    // "Oberfläche...glatt" @f499-580, "Regenwasser abläuft" @f580
    line1: { words: ["Glatte", "Oberfläche."], startFrame: 615, y: 500, fontSize: 100, x: 200 },
    line2: { words: ["Wasser", "läuft", "ab.", "Atmungsaktiv."], startFrame: 660, y: 630, fontSize: 70, x: 200 },
    exitFrame: 760,
  },
  scene6: {
    // "trotzdem nach außen" @f789, "Atmungsaktiv..." @f850
    line1: { words: ["REM", "Malerfachbetrieb"], startFrame: 790, y: 480, fontSize: 80, letterSpacing: 2, x: 200 },
    line2: { words: ["rem-maler.de"], startFrame: 820, y: 590, fontSize: 60, color: REM_RED, x: 200 },
    line3: { words: ["Jetzt", "Angebot", "anfragen", "\u2192"], startFrame: 855, y: 690, fontSize: 50, color: "rgba(255,255,255,0.7)", x: 200 },
  },
} as const;
