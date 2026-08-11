// ============================================================
// Sauber Entsorgen — Leistungen-Overlay
// 12s @ 25fps (300 frames), 16:9 transparent alpha overlay.
// Curated keywords + chip groups synced to the GF's speech.
//
// Transkript:
//   "Wir übernehmen Haushaltsauflösungen und Nachlassauflösungen,
//    einzelne Keller, Dachböden, Garagen, genau wie Firmen und
//    Insolvenzauflösungen. Und wenn es auch mal schnell gehen muss,
//    auch natürlich kurzfristig."
// ============================================================

import type { Align, ChipItem, ServiceIconName } from "../../components";

export interface KeywordEntry {
  word: string;
  icon: ServiceIconName;
  startSec: number;
  durationSec: number;
  align?: Align;
  offsetX?: number;
  offsetY?: number;
}

export interface ChipGroupEntry {
  startSec: number;
  durationSec: number;
  chips: ChipItem[];
  offsetX?: number;
  offsetY?: number;
}

// --- Lower-third keywords synced to speech ---
export const KEYWORDS: KeywordEntry[] = [
  { word: "Haushaltsauflösungen", icon: "haus", startSec: 0.0, durationSec: 2.2, align: "left" },
  { word: "Nachlassauflösungen", icon: "nachlass", startSec: 2.2, durationSec: 1.6, align: "left" },
  { word: "Firmen- & Insolvenzauflösungen", icon: "firma", startSec: 6.6, durationSec: 2.6, align: "left" },
  { word: "Kurzfristig & schnell", icon: "express", startSec: 9.2, durationSec: 2.8, align: "left" },
];

// --- Chip groups (multiple icons revealed together, staggered) ---
export const CHIP_GROUPS: ChipGroupEntry[] = [
  {
    startSec: 3.8,
    durationSec: 2.8,
    chips: [
      { label: "Keller", icon: "keller" },
      { label: "Dachboden", icon: "dachboden" },
      { label: "Garage", icon: "garage" },
    ],
  },
];
