// ============================================================
// REM Gewerbedach-Reinigung — Constants
// Testimonial-synced Animation (Kunden-O-Ton, 25 fps)
// Timing-Quelle: Transcribe REM Gewerbedach Reinigung.srt
// (SRT-Timecodes haben 1h-Offset; Frame = (t − 1h) × 25)
// ============================================================

import type { Vec3 } from "./projection";

// --- Colors ---
export const BG = "#0D0D1A";
export const REM_RED = "#D83C31";
export const WHITE = "#FFFFFF";
export const WHITE_60 = "rgba(255,255,255,0.6)";
export const WHITE_30 = "rgba(255,255,255,0.3)";
export const WHITE_05 = "rgba(255,255,255,0.05)";
export const GREY_WEATHERED = "#6B6B5A";
export const GREY_DIRTY = "#55554A";
export const PV_BLUE = "#16324F";
export const PV_CELL = "#1E4468";

// Legacy-Aliase (von kopierten Komponenten referenziert)
export const TERRACOTTA = GREY_WEATHERED;
export const TERRACOTTA_DIRTY = GREY_DIRTY;

// --- Canvas ---
export const W = 3840;
export const H = 2160;
export const FPS = 25;
export const INTRO_DUR = 75;
export const OUTRO_DUR = 75;
export const TOTAL_FRAMES = 2650; // 106 s — O-Ton endet bei 103,44 s

// --- Scene Timing (frames, synchron zum O-Ton) ---
export const OVERLAP = 30;

// weathering = Zustand ("fast keine Farbe sichtbar")
// angebot    = schnelle Reaktion & Angebot
// preis      = Preis-Leistung im Vergleich
// kran       = Spezialfahrzeug, Beschichtung ohne Gerüst
// (Sprechpause 57,8–69,7 s → Kamerafahrt, kein Text)
// garantie   = Gewährleistung
// ergebnis   = Zufriedenheit + PV-Reinigung
// finale     = Weiterempfehlung
export const SCENES = {
  weathering: { start: 6,    end: 280,  dur: 274 },
  angebot:    { start: 298,  end: 770,  dur: 472 },
  preis:      { start: 785,  end: 1030, dur: 245 },
  kran:       { start: 1047, end: 1459, dur: 412 },
  garantie:   { start: 1743, end: 1975, dur: 232 },
  ergebnis:   { start: 1996, end: 2451, dur: 455 },
  finale:     { start: 2458, end: 2575, dur: 117 },
} as const;

export const SCENES_OV = {
  weathering: { start: 6,    end: 295 },
  angebot:    { start: 283,  end: 785 },
  preis:      { start: 770,  end: 1045 },
  kran:       { start: 1032, end: 1474 },
  garantie:   { start: 1728, end: 1990 },
  ergebnis:   { start: 1981, end: 2466 },
  finale:     { start: 2443, end: 2575 },
} as const;

// Kamerafahrt in der Sprechpause
export const GLIDE = { start: 1500, end: 1650 } as const;

// --- 3D Hallen-Geometrie (Gewerbehalle: breit, flach geneigtes Dach) ---
const HALL_WIDTH = 340;
const HALL_DEPTH = 520;
const WALL_HEIGHT = 200;
const ROOF_PEAK = 55;

export const HOUSE_VERTS: Record<string, Vec3> = {
  // Ground corners
  gFL: [-HALL_WIDTH, 0, -HALL_DEPTH],
  gFR: [HALL_WIDTH, 0, -HALL_DEPTH],
  gBR: [HALL_WIDTH, 0, HALL_DEPTH],
  gBL: [-HALL_WIDTH, 0, HALL_DEPTH],
  // Wall top corners
  wFL: [-HALL_WIDTH, WALL_HEIGHT, -HALL_DEPTH],
  wFR: [HALL_WIDTH, WALL_HEIGHT, -HALL_DEPTH],
  wBR: [HALL_WIDTH, WALL_HEIGHT, HALL_DEPTH],
  wBL: [-HALL_WIDTH, WALL_HEIGHT, HALL_DEPTH],
  // Ridge endpoints
  rF: [0, WALL_HEIGHT + ROOF_PEAK, -HALL_DEPTH],
  rB: [0, WALL_HEIGHT + ROOF_PEAK, HALL_DEPTH],
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

// Roof surface corners for surfacePoint()
// Order: [topLeft, topRight, bottomRight, bottomLeft]; "top" = ridge
export const LEFT_ROOF_CORNERS: Vec3[] = [
  HOUSE_VERTS.rF,
  HOUSE_VERTS.rB,
  HOUSE_VERTS.wBL,
  HOUSE_VERTS.wFL,
];

export const RIGHT_ROOF_CORNERS: Vec3[] = [
  HOUSE_VERTS.rF,
  HOUSE_VERTS.rB,
  HOUSE_VERTS.wBR,
  HOUSE_VERTS.wFR,
];

// --- Kran-Geometrie (Spezialfahrzeug vor der Halle, Ausleger über dem Dach) ---
export const CRANE_BASE: Vec3 = [-HALL_WIDTH - 280, 0, -HALL_DEPTH - 130];
export const CRANE_TIP: Vec3 = [0, WALL_HEIGHT + ROOF_PEAK + 165, 0];

// --- Camera Keyframes ---
// Yaw/pitch in Grad; Drift innerhalb der Szene führt in die nächste Snap-Richtung.
export const CAMERA_KEYFRAMES = [
  // Zustand — 3/4-Ansicht, Verwitterung sichtbar
  { frame: 75,   yaw: -35, pitch: 24, scale: 0.80 },
  { frame: 85,   yaw: -35, pitch: 24, scale: 0.85 },
  { frame: 280,  yaw: -31, pitch: 25, scale: 0.87 },
  // Angebot — SNAP näher, ruhiger Halt (textlastige Szene)
  { frame: 298,  yaw: 18,  pitch: 28, scale: 0.90 },
  { frame: 770,  yaw: 13,  pitch: 27, scale: 0.92 },
  // Preis — SNAP Gegenseite
  { frame: 785,  yaw: -50, pitch: 26, scale: 0.93 },
  { frame: 1030, yaw: -45, pitch: 27, scale: 0.94 },
  // Kran — SNAP erhöht, Dach + Kran im Bild
  { frame: 1047, yaw: 27,  pitch: 32, scale: 0.78 },
  { frame: 1459, yaw: 32,  pitch: 30, scale: 0.80 },
  // Sprechpause — ruhig zurückdrehen
  { frame: 1650, yaw: -28, pitch: 24, scale: 0.86 },
  // Garantie — Halt
  { frame: 1743, yaw: -28, pitch: 24, scale: 0.86 },
  { frame: 1975, yaw: -24, pitch: 25, scale: 0.88 },
  // Ergebnis — SNAP erhöht für PV-Fläche
  { frame: 1996, yaw: 16,  pitch: 34, scale: 0.82 },
  { frame: 2451, yaw: 20,  pitch: 32, scale: 0.84 },
  // Finale — SNAP zurück, ruhiges Settle
  { frame: 2466, yaw: -20, pitch: 25, scale: 0.88 },
  { frame: 2650, yaw: -20, pitch: 25, scale: 0.88 },
] as const;

// Base scale multiplier (Halle ist größer als das Einfamilienhaus der V2)
export const HOUSE_BASE_SCALE = 1.45;

// --- Slides (Texte ausschließlich aus dem O-Ton, wortgenau getimt) ---
// bulletFrames: absolute Startframes je Bullet = Zeitpunkt der Aussage im O-Ton
export const SLIDES = [
  {
    // 0,2–11,0 s: „Zustand … befriedigend … fast keine Farbe sichtbar … höchste Zeit"
    tag: "Ausgangslage",
    headline: ["Kaum noch", "Farbe sichtbar."],
    bullets: ["Zustand: „befriedigend“", "Höchste Zeit für neue Lackierung"],
    bulletFrames: [40, 215],
    startFrame: 10,
    exitFrame: 278,
    x: 350,
    y: 580,
  },
  {
    // 11,9–30,6 s: „Innerhalb einer Woche … Chef gemeldet … Angebot ging fix …
    // andere drei, vier Wochen … Kommunikation war gut"
    tag: "Reaktion",
    headline: ["Innerhalb", "einer Woche."],
    bullets: [
      "Der Chef meldete sich persönlich",
      "Angebot ging fix",
      "Andere Anbieter: 3–4 Wochen",
      "Austausch & Kommunikation: gut",
    ],
    bulletFrames: [340, 471, 519, 672],
    startFrame: 298,
    exitFrame: 768,
    x: 350,
    y: 480,
  },
  {
    // 31,4–41,0 s: „Preis-Leistungsverhältnis sehr gut … andere: ganze Halle eingerüstet"
    tag: "Vergleich",
    headline: ["Preis-Leistung:", "sehr gut."],
    bullets: ["Mehrere Firmen im Vergleich", "Andere: ganze Halle einrüsten"],
    bulletFrames: [820, 921],
    startFrame: 785,
    exitFrame: 1028,
    x: 350,
    y: 580,
  },
  {
    // 41,9–57,8 s: „Spezialfahrzeug, so ein Kraner … ohne Einrüstung … vom Kran aus …
    // Eingerüst gespart … wesentlich günstiger"
    tag: "Spezialfahrzeug",
    headline: ["Arbeiten", "vom Kran aus."],
    bullets: [
      "Kein Gerüst erforderlich",
      "Einrüstung komplett gespart",
      "Wesentlich günstiger",
    ],
    bulletFrames: [1187, 1331, 1397],
    startFrame: 1050,
    exitFrame: 1457,
    x: 350,
    y: 520,
  },
  {
    // 69,7–78,6 s: „fünf Jahre Gewährleistung auf die Arbeitsausführung …
    // Farbhersteller … 20 Jahre auf die Farbe"
    tag: "Gewährleistung",
    headline: ["Garantie", "inklusive."],
    bullets: [
      "5 Jahre auf die Arbeitsausführung",
      "20 Jahre auf die Farbe (Hersteller)",
    ],
    bulletFrames: [1771, 1845],
    startFrame: 1743,
    exitFrame: 1978,
    x: 1750,
    y: 580,
  },
  {
    // 79,8–98,0 s: „vom Ergebnis sehr zufrieden … vorher/nachher …
    // Photovoltaikanlage auch noch mal richtig gereinigt"
    tag: "Ergebnis",
    headline: ["Sehr", "zufrieden."],
    bullets: [
      "Vorher–Nachher: klarer Unterschied",
      "Photovoltaik gleich mitgereinigt",
    ],
    bulletFrames: [2113, 2216],
    startFrame: 1998,
    exitFrame: 2448,
    x: 1750,
    y: 580,
  },
  {
    // 98,3–103,4 s: „Preis-Leistungsverhältnis und Arbeitsausführung …
    // kann ich die Firma weiterempfehlen"
    tag: "Fazit",
    headline: ["Klare", "Weiterempfehlung."],
    bullets: ["Preis-Leistungsverhältnis", "Saubere Arbeitsausführung"],
    bulletFrames: [2486, 2504],
    startFrame: 2460,
    exitFrame: 2568,
    x: 1750,
    y: 580,
  },
];
