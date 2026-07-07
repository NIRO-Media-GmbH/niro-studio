// ============================================================
// Bremsen Schneider — Azubi KFZ-Mechatroniker Overlay
// Whisper transcript + curated keywords & panels
// Video: 50.24s @ 25fps, 2160×3840
// ============================================================

import type { OverlayPosition } from "../../components";

export interface KeywordEntry {
  word: string;
  startSec: number;
  durationSec: number;
  position: OverlayPosition;
  offsetY?: number;
}

export interface PanelEntry {
  title: string;
  items?: string[];
  body?: string;
  startSec: number;
  durationSec: number;
  position: OverlayPosition;
  accentSide?: "left" | "top";
}

export interface EndCardEntry {
  startSec: number;
  durationSec: number;
  ctaText: string;
  website: string;
  phone?: string;
}

// --- Curated keywords synced to speech ---
export const KEYWORDS: KeywordEntry[] = [
  // Hook: "Wo verdient man als Azubi gut Kohle"
  { word: "AZUBI", startSec: 1.2, durationSec: 2.8, position: "bottom" },
  // "jeden Morgen anders"
  { word: "JEDEN TAG ANDERS", startSec: 6.8, durationSec: 3.5, position: "bottom" },
  // "Das Team ist cool"
  { word: "TEAM", startSec: 15.6, durationSec: 2.5, position: "bottom" },
  // "Jeder hilft jedem"
  { word: "JEDER HILFT JEDEM", startSec: 20.3, durationSec: 3.0, position: "bottom" },
  // "direkt von Anfang an dabei"
  { word: "VON ANFANG AN", startSec: 28.5, durationSec: 2.8, position: "center" },
  // "Theorie + Praxis"
  { word: "THEORIE & PRAXIS", startSec: 32.0, durationSec: 3.5, position: "center" },
  // "Augenhöhe" — after panel exits at 42.0
  { word: "AUGENHÖHE", startSec: 42.5, durationSec: 3.0, position: "bottom" },
];

// --- Info panels for key messages ---
export const PANELS: PanelEntry[] = [
  {
    title: "Deine Ausbildung",
    items: [
      "Wartung bis Spezialaufträge",
      "Theorie direkt in Praxis umsetzen",
      "Von Tag 1 richtig mit dabei",
    ],
    startSec: 10.5,
    durationSec: 4.5,
    position: "bottom",
    accentSide: "left",
  },
  {
    title: "Unternehmenskultur",
    items: [
      "Auf Augenhöhe",
      "Offene Kommunikation",
      "Starker Teamzusammenhalt",
    ],
    startSec: 37.0,
    durationSec: 5.0,
    position: "bottom",
    accentSide: "left",
  },
];

// --- End card ---
export const END_CARD: EndCardEntry = {
  startSec: 46.0,
  durationSec: 4.24,
  ctaText: "Jetzt bewerben!",
  website: "bremsen-schneider.de",
};
