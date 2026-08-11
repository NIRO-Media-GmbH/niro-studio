// ============================================================
// REM Dachbeschichtung — Constants & Configuration
// ============================================================

// --- Brand Colors ---
export const RED = "#D83C31";
export const RED_LIGHT = "#F05545";
export const RED_DARK = "#A52D24";
export const DARK_BG = "#0D0D1A";
export const DARK_NAVY = "#141428";
export const WHITE = "#FFFFFF";
export const WARM_GOLD = "#8B6914";
export const WARM_GOLD_LIGHT = "#9A7818";
export const WARM_GOLD_DARK = "#6B4F0A";
export const GREY_WEATHERED = "#5A5A3A";
export const GREY_WEATHERED_DARK = "#4A4A2A";
export const MOSS_GREEN = "#3D6B35";
export const MOSS_GREEN_LIGHT = "#5A9C4F";
export const MOSS_DARK = "#2A4D25";
export const LICHEN_YELLOW = "#8B7D3C";
export const WATER_BLUE = "#4A9EFF";
export const WATER_BLUE_LIGHT = "#88D0FF";

// --- House Wall Colors ---
export const WALL_CREAM = "#E8D5B5";
export const WALL_LIGHT = "#F0E0C8";
export const WALL_DARK = "#C4A882";
export const WALL_SHADOW = "#A08060";
export const WINDOW_BLUE = "#1A2040";
export const WINDOW_HIGHLIGHT = "#2A3560";
export const DOOR_BROWN = "#8B5E3C";
export const DOOR_DARK = "#6B4525";

// --- Canvas (4K 16:9) ---
export const CANVAS = { width: 3840, height: 2160 } as const;
export const FPS = 25;

// --- Clay Material Colors ---
export const CLAY_HIGHLIGHT = "rgba(255,255,255,0.35)";
export const CLAY_SHADOW = "rgba(0,0,0,0.4)";
export const CLAY_RIM = "rgba(255,255,255,0.15)";
export const CLAY_PARTICLE_SHADOW = "rgba(0,0,0,0.3)";

// --- Roof Geometry (Gable / Satteldach) ---
// Isometric view from front-right: visible front slope + right gable
export const ROOF = {
  // Front slope — main visible tilted surface (tiles, coating, all effects)
  // This is also used as `points` by scene components for bounding box
  frontSlope: [
    { x: 0.225, y: 0.185 },   // ridge-left (peak, with overhang)
    { x: 0.81, y: 0.185 },    // ridge-right (peak, with overhang)
    { x: 0.775, y: 0.44 },    // eave-right (front, with overhang)
    { x: 0.19, y: 0.44 },     // eave-left (front, with overhang)
  ],
  // Right roof overhang past gable (thin visible edge of roof thickness)
  rightOverhang: [
    { x: 0.81, y: 0.185 },    // ridge-right (shared with frontSlope)
    { x: 0.855, y: 0.37 },    // back-eave-right (past gable)
    { x: 0.775, y: 0.44 },    // eave-right (shared with frontSlope)
  ],
  // Ridge cap 3D thickness offsets
  ridgeCap: { offsetY: -0.018, offsetX: 0.008 },
  // Eave fascia depth below front eave line
  eaveDepth: 0.02,
  cornerRadius: 0.005,
} as const;

// --- House Geometry ---
// Walls, windows, door — positioned relative to roof bottom edge
export const HOUSE = {
  // Front wall (vertical face, drops from roof bottom edge)
  frontWall: [
    { x: 0.205, y: 0.42 },   // top-left (= roof BL)
    { x: 0.765, y: 0.42 },   // top-right (= roof BR)
    { x: 0.765, y: 0.74 },   // bottom-right
    { x: 0.205, y: 0.74 },   // bottom-left
  ],
  // Right side wall (isometric depth face, darker)
  rightWall: [
    { x: 0.765, y: 0.42 },   // top-left (= frontWall TR)
    { x: 0.83, y: 0.36 },    // top-right (depth offset)
    { x: 0.83, y: 0.68 },    // bottom-right
    { x: 0.765, y: 0.74 },   // bottom-left (= frontWall BR)
  ],
  // Gable wall triangle (above right wall, below roof peak)
  gableWall: [
    { x: 0.765, y: 0.42 },   // bottom-front (= rightWall TL)
    { x: 0.83, y: 0.36 },    // bottom-back (= rightWall TR)
    { x: 0.7975, y: 0.19 },  // peak (center of wall top, elevated to ridge)
  ],
  // Windows on front wall (2 windows)
  windows: [
    { x: 0.30, y: 0.50, w: 0.085, h: 0.10 },
    { x: 0.58, y: 0.50, w: 0.085, h: 0.10 },
  ],
  // Side window on right wall
  sideWindow: { x: 0.78, y: 0.46, w: 0.03, h: 0.08 },
  // Door on front wall (centered)
  door: { x: 0.44, y: 0.57, w: 0.065, h: 0.17 },
  // Ground shadow
  shadowY: 0.80,
} as const;

// Tile grid
export const TILE_GRID = {
  rows: 3,
  cols: 12,
} as const;

// Helper: convert roof ratios to absolute pixels
export function roofPixels(w: number, h: number) {
  return {
    // `points` = frontSlope for backward compat (scene components use this)
    points: ROOF.frontSlope.map((p) => ({ x: p.x * w, y: p.y * h })),
    frontSlope: ROOF.frontSlope.map((p) => ({ x: p.x * w, y: p.y * h })),
    rightOverhang: ROOF.rightOverhang.map((p) => ({ x: p.x * w, y: p.y * h })),
    ridgeCapOffsetY: ROOF.ridgeCap.offsetY * h,
    ridgeCapOffsetX: ROOF.ridgeCap.offsetX * w,
    eaveDepth: ROOF.eaveDepth * h,
    cornerRadius: ROOF.cornerRadius * w,
  };
}

// Helper: convert house ratios to absolute pixels
export function housePixels(w: number, h: number) {
  return {
    frontWall: HOUSE.frontWall.map((p) => ({ x: p.x * w, y: p.y * h })),
    rightWall: HOUSE.rightWall.map((p) => ({ x: p.x * w, y: p.y * h })),
    gableWall: HOUSE.gableWall.map((p) => ({ x: p.x * w, y: p.y * h })),
    windows: HOUSE.windows.map((win) => ({
      x: win.x * w, y: win.y * h, w: win.w * w, h: win.h * h,
    })),
    sideWindow: {
      x: HOUSE.sideWindow.x * w, y: HOUSE.sideWindow.y * h,
      w: HOUSE.sideWindow.w * w, h: HOUSE.sideWindow.h * h,
    },
    door: {
      x: HOUSE.door.x * w, y: HOUSE.door.y * h,
      w: HOUSE.door.w * w, h: HOUSE.door.h * h,
    },
    shadowY: HOUSE.shadowY * h,
  };
}

// SVG polygon string from points
export function pointsToSvg(pts: { x: number; y: number }[]): string {
  return pts.map((p) => `${p.x},${p.y}`).join(" ");
}

// --- Spring Configs ---
export const SPRING_PREMIUM = { damping: 18, stiffness: 100 };
export const SPRING_SMOOTH = { damping: 14, stiffness: 120 };
export const SPRING_PUNCHY = { damping: 10, stiffness: 180 };
export const SPRING_BOUNCE = { damping: 6, stiffness: 260 };
export const SPRING_GENTLE = { damping: 22, stiffness: 60 };
// Clay-style bouncy springs
export const SPRING_CLAY = { damping: 8, stiffness: 140, mass: 1.2 };
export const SPRING_JELLY = { damping: 6, stiffness: 200, mass: 0.8 };

// --- Scene Timing (frames at 25fps) ---
// Original non-overlapping timing (used for roof state machine)
export const SCENES = {
  weather: { start: 0, end: 125, dur: 125 },      // 0-5s
  weathering: { start: 125, end: 250, dur: 125 },  // 5-10s
  moss: { start: 250, end: 425, dur: 175 },        // 10-17s
  coating: { start: 425, end: 600, dur: 175 },     // 17-24s
  waterProof: { start: 600, end: 775, dur: 175 },  // 24-31s
  finale: { start: 775, end: 925, dur: 150 },      // 31-37s
} as const;

// Overlapping timing for smooth cross-fade transitions (30 frame overlap)
export const OVERLAP = 30;
export const SCENES_OVERLAP = {
  weather:    { start: 0,   end: 155, dur: 155 },
  weathering: { start: 95,  end: 280, dur: 185 },
  moss:       { start: 220, end: 455, dur: 235 },
  coating:    { start: 395, end: 630, dur: 235 },
  waterProof: { start: 570, end: 805, dur: 235 },
  finale:     { start: 745, end: 925, dur: 180 },
} as const;
