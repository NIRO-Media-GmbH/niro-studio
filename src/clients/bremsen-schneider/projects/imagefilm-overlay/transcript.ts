// ============================================================
// Bremsen Schneider — Recruiting Imagefilm Overlay
// Whisper transcript + curated keywords & panels
// Video: 80.16s @ 25fps, 2160×3840
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
  // "Willkommen bei Bremsenschneider"
  { word: "BREMSENSCHNEIDER", startSec: 0.9, durationSec: 2.5, position: "center" },
  // "Stimmen der Mitarbeiter" — after panel exits at 10.0
  { word: "ECHTE STIMMEN", startSec: 10.5, durationSec: 2.5, position: "center" },
  // "Jeder hilft jedem" — after ECHTE STIMMEN exits at 13.0
  { word: "JEDER HILFT JEDEM", startSec: 13.5, durationSec: 3.0, position: "bottom" },
  // "Erster Tag war echt cool" — before panel at 24.5
  { word: "TAG 1", startSec: 21.5, durationSec: 2.5, position: "bottom" },
  // "flexible Arbeitszeiten" — after panel exits at 29.5
  { word: "FLEXIBLE ZEITEN", startSec: 30.0, durationSec: 3.0, position: "bottom" },
  // "Wille zu lernen"
  { word: "WILLE ZU LERNEN", startSec: 33.5, durationSec: 3.0, position: "bottom" },
  // "neueste Modelle bis Oldtimer"
  { word: "VIELFALT", startSec: 38.0, durationSec: 2.5, position: "center" },
  // "75 Jahre" — after panel exits at 46.5
  { word: "75 JAHRE", startSec: 47.0, durationSec: 3.0, position: "center" },
  // "Spaß macht"
  { word: "SPASS", startSec: 56.9, durationSec: 2.0, position: "bottom" },
  // "spezialisieren"
  { word: "SPEZIALISIERUNG", startSec: 62.5, durationSec: 2.5, position: "bottom" },
];

// --- Info panels ---
export const PANELS: PanelEntry[] = [
  {
    title: "Das sagen unsere Leute",
    body: "Echte Stimmen, echte Erfahrungen — kein Recruiting-Blabla.",
    startSec: 5.5,
    durationSec: 4.5,
    position: "center",
    accentSide: "top",
  },
  {
    title: "Dein Start bei uns",
    items: [
      "Vom ersten Tag voll dabei",
      "Flexible Arbeitszeiten",
      "Starkes Team um dich herum",
    ],
    startSec: 24.5,
    durationSec: 5.0,
    position: "bottom",
    accentSide: "left",
  },
  {
    title: "Unser Fuhrpark",
    items: [
      "Neueste Modelle bis Oldtimer",
      "Über 75 Jahre Erfahrung",
      "Spezialisierung möglich",
    ],
    startSec: 41.0,
    durationSec: 5.5,
    position: "center",
    accentSide: "left",
  },
];

// --- End card ---
export const END_CARD: EndCardEntry = {
  startSec: 66.0,
  durationSec: 6.0,
  ctaText: "Jetzt bewerben!",
  website: "bremsen-schneider.de",
};
