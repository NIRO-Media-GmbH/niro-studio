// Schlagwort-Chips Video 03 + Sperrfenster (Spec 2026-09-16).
// *_V3 = Zeiten des Kunden-Schnitts V3 (Mix-Plan captions/viele-jahre-v3.plan.json).
// BLOCKED/KEYWORDS = Zeiten des aktuell gelieferten Schnitts (Phase B: + Verlängerung D).
import type { BlockedRange } from "../../Subtitles";
import { shiftBlocked, shiftKeywords, type Keyword } from "../../captionMix/keywords";
import introJson from "./intro-layout.json";

const SHIFT_SEC = introJson.shiftFrames / introJson.fps;
const r2 = (v: number) => Math.round(v * 100) / 100;

export const DURATION_SEC_V3 = 51.6;

export const BLOCKED_V3: BlockedRange[] = [
  { startSec: 0, durationSec: 2.72 }, // Hook „VIELE JAHRE / VIELE GESCHICHTEN" (Overlay 0,24–2,72)
  { startSec: 7.84, durationSec: 3.76 }, // Laender-Flaggen (Overlay 7,84–11,6)
  { startSec: 46.64, durationSec: DURATION_SEC_V3 - 46.64 }, // CTA (Overlay ab 46,64)
];

export const KEYWORDS_V3: Keyword[] = [
  // „FRÜHER SELBST KEIN DEUTSCH" (12,86–16,36 s, Tomasz) auf Kundenwunsch 18.09.2026 entfernt.
  { text: "KOMMUNIKATION? KEIN PROBLEM.", startSec: 25.24, endSec: 26.8, offsetY: 210 }, // „kein" · cc-10
  { text: "RESPEKTVOLL UND LERNBEREIT", startSec: 28.52, endSec: 30.8, offsetY: 110 }, // „respektvoll" · cc-11
  { text: "ÜBER 50 JAHRE BEI CRAISS", startSec: 32.5, endSec: 34.82, offsetY: 160 }, // „Fünfzig" · cc-13
  { text: "TROTZ RENTE AM STEUER", startSec: 36.24, endSec: 39.74, offsetY: 160 }, // „Rente" · cc-14
  { text: "DU BIST KEINE ZAHL.", startSec: 44.24, endSec: 45.74, offsetY: 190 }, // „Du" · cc-16
];

// Neuer Schnitt (Kopie „Claude 03 Begrüßung …"): alles hinter der Montage + D
export const DURATION_SEC = r2(DURATION_SEC_V3 + SHIFT_SEC);
export const BLOCKED: BlockedRange[] = [
  { startSec: 0, durationSec: introJson.titleChip.toFrame / introJson.fps }, // Begrüßung, Wischer, Titel-Chip
  ...shiftBlocked([BLOCKED_V3[1]], SHIFT_SEC), // Laender-Flaggen
  { startSec: r2(46.64 + SHIFT_SEC), durationSec: r2(DURATION_SEC - (46.64 + SHIFT_SEC)) }, // CTA
];
export const KEYWORDS: Keyword[] = shiftKeywords(KEYWORDS_V3, SHIFT_SEC);
