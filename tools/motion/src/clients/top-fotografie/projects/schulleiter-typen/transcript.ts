// ============================================================
// Top Fotografie — Die 5 Typen von Schulleitern
// Humor-Sketch Overlay · Timing-Daten
// Video: 9:16 portrait (1080×1920), 30fps, transparent
// ============================================================
//
// Timing layout (15s per element, 2s gap between):
//   Intro:       0s – 15s
//   Typ 1:      17s – 32s
//   Typ 2:      34s – 49s
//   Typ 3:      51s – 66s
//   Typ 4:      68s – 83s
//   Typ 5:      85s – 100s
//   CTA:       102s – 117s
//   Total:     117s

export interface SceneEntry {
  label: string;
  startSec: number;
  durationSec: number;
}

export interface IntroEntry {
  mainText: string;
  subText: string;
  startSec: number;
  durationSec: number;
}

export interface CtaEntry {
  headline: string;
  subline: string;
  website: string;
  startSec: number;
  durationSec: number;
}

// --- Intro ---
export const INTRO: IntroEntry = {
  mainText: "Die 5 Typen",
  subText: "von Schulleitern beim Erstgespräch",
  startSec: 0,
  durationSec: 15,
};

// --- 5 Typen ---
export const TYPEN: SceneEntry[] = [
  {
    label: "TYP 1 \u2014 Der Misstrauische",
    startSec: 17,
    durationSec: 15,
  },
  {
    label: "TYP 2 \u2014 Der Enthusiast",
    startSec: 34,
    durationSec: 15,
  },
  {
    label: "TYP 3 \u2014 Der Preisverhandler",
    startSec: 51,
    durationSec: 15,
  },
  {
    label: "TYP 4 \u2014 Der \u00DCberforderte",
    startSec: 68,
    durationSec: 15,
  },
  {
    label: "TYP 5 \u2014 Der Perfekte",
    startSec: 85,
    durationSec: 15,
  },
];

// --- CTA End Card ---
export const CTA: CtaEntry = {
  headline: "Für jeden Typ die Geduld.",
  subline: "Und am Ende das perfekte Foto.",
  website: "top-yp.de",
  startSec: 102,
  durationSec: 15,
};

// Total duration
export const TOTAL_DURATION_SEC = 117;
