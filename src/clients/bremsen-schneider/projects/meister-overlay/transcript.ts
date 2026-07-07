// ============================================================
// Bremsen Schneider — Meister KFZ-Mechatroniker Overlay
// Whisper transcript + curated keywords & panels
// Video: 73.84s @ 25fps, 2160×3840
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
  // Hook: "KFZ-Meister" + "geiles Team"
  { word: "KFZ-MEISTER", startSec: 0.7, durationSec: 2.5, position: "bottom" },
  // "Briefing am Morgen" — before panel at 13.0
  { word: "BRIEFING", startSec: 10.0, durationSec: 2.5, position: "bottom" },
  // "Ruhe statt Hektik" — after panel exits at 18.0
  { word: "RUHE STATT HEKTIK", startSec: 18.5, durationSec: 2.8, position: "bottom" },
  // "40 Tonnen auf der Straße"
  { word: "40 TONNEN", startSec: 23.0, durationSec: 2.5, position: "center" },
  // "alles funktioniert"
  { word: "SICHERHEIT", startSec: 27.5, durationSec: 2.5, position: "center" },
  // "moderne Diagnosetools"
  { word: "DIAGNOSETOOLS", startSec: 30.6, durationSec: 3.0, position: "center" },
  // "vielseitig interessant" — before panel at 44.0
  { word: "VIELSEITIG", startSec: 40.5, durationSec: 3.0, position: "bottom" },
  // "Respekt vor deiner Zeit" — after panel exits at 49.0
  { word: "RESPEKT", startSec: 49.5, durationSec: 2.5, position: "bottom" },
  // "wohlfühlen" — after RESPEKT exits at 52.0
  { word: "WOHLFÜHLEN", startSec: 52.5, durationSec: 2.5, position: "bottom" },
  // "Top-Leistungen" — before EndCard at 60.0
  { word: "TOP-LEISTUNGEN", startSec: 56.5, durationSec: 3.0, position: "bottom" },
];

// --- Info panels ---
export const PANELS: PanelEntry[] = [
  {
    title: "Dein Arbeitsalltag",
    items: [
      "Klare Abläufe & Briefings",
      "Moderne Diagnosetools",
      "Checklisten-gestütztes Arbeiten",
    ],
    startSec: 13.0,
    durationSec: 5.0,
    position: "bottom",
    accentSide: "left",
  },
  {
    title: "Dein Fuhrpark",
    items: [
      "LKW & Trailer",
      "Kran & Spezialfahrzeuge",
      "Wohnmobile & Wohnwagen",
    ],
    startSec: 34.0,
    durationSec: 5.0,
    position: "center",
    accentSide: "left",
  },
  {
    title: "Unser Versprechen",
    items: [
      "Kurze Wege, starkes Team",
      "Respekt vor deiner Zeit",
      "Kultur auf Augenhöhe",
    ],
    startSec: 44.0,
    durationSec: 5.0,
    position: "bottom",
    accentSide: "left",
  },
];

// --- End card ---
export const END_CARD: EndCardEntry = {
  startSec: 60.0,
  durationSec: 5.0,
  ctaText: "Jetzt bewerben!",
  website: "bremsen-schneider.de",
};
