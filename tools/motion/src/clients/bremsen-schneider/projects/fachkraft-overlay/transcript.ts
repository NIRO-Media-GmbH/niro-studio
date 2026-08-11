// ============================================================
// Bremsen Schneider — Fachkraft KFZ-Mechatroniker Overlay
// Whisper transcript + curated keywords & panels
// Video: 66.84s @ 25fps, 2160×3840
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
  // Hook: "Du bist KFZ-Mechatroniker und erst um 19 Uhr zu Hause"
  { word: "KFZ-MECHATRONIKER", startSec: 0.8, durationSec: 2.8, position: "bottom" },
  // "Mein Arbeitsalltag ist nie gleich"
  { word: "NIE GLEICH", startSec: 8.5, durationSec: 2.5, position: "bottom" },
  // "coole Truppe"
  { word: "COOLE TRUPPE", startSec: 12.8, durationSec: 2.5, position: "bottom" },
  // "besonders stolz auf das Team"
  { word: "STOLZ AUFS TEAM", startSec: 16.5, durationSec: 3.0, position: "bottom" },
  // "vielseitig interessant"
  { word: "VIELSEITIG", startSec: 33.0, durationSec: 2.5, position: "center" },
  // "Planung ist das A und O" — after VIELSEITIG exits at 35.5
  { word: "PLANUNG", startSec: 36.0, durationSec: 2.5, position: "center" },
  // "flexible Arbeitszeiten" — before panel at 44.5
  { word: "FLEXIBLE ZEITEN", startSec: 41.0, durationSec: 3.0, position: "bottom" },
  // "Familie öfter sehen" — before EndCard at 52.0 → move into earlier gap
  { word: "MEHR FAMILIE", startSec: 49.8, durationSec: 2.0, position: "bottom" },
];

// --- Info panels ---
export const PANELS: PanelEntry[] = [
  {
    title: "Dein Aufgabenfeld",
    items: [
      "LKW, Trailer, Kran",
      "Wohnmobile & Wohnwagen",
      "Komplettes Programm",
    ],
    startSec: 22.0,
    durationSec: 5.0,
    position: "bottom",
    accentSide: "left",
  },
  {
    title: "Deine Vorteile",
    items: [
      "Flexible Arbeitszeiten",
      "Starkes Team",
      "Offene Kommunikation",
    ],
    startSec: 44.5,
    durationSec: 5.0,
    position: "bottom",
    accentSide: "left",
  },
];

// --- End card ---
export const END_CARD: EndCardEntry = {
  startSec: 52.0,
  durationSec: 4.84,
  ctaText: "Jetzt bewerben!",
  website: "bremsen-schneider.de",
};
