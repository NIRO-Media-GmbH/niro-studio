// Schlagwort-Chips Video 01 + Sperrfenster (Spec 2026-09-16).
// Start = Wortanfang des Ankerworts (captions/erster-tag-v3.plan.json),
// offsetY = größtes y der überdeckten Sätze − 990.
import type { BlockedRange } from "../../Subtitles";
import type { Keyword } from "../../captionMix/keywords";

export const DURATION_SEC = 29.6;
const CTA_START = 24.32;

// Hook (0,24–3,6 s) und CTA (ab 24,32 s) wie in Craiss-ErsterTag
export const BLOCKED: BlockedRange[] = [
  { startSec: 0.24, durationSec: 3.6 - 0.24 },
  { startSec: CTA_START, durationSec: DURATION_SEC - CTA_START },
];

export const KEYWORDS: Keyword[] = [
  { text: "KINDERLEICHT – FÜR JUNG UND ALT", startSec: 8.5, endSec: 11.73, offsetY: 190 }, // „kinderleicht" · cc-02 + cc-03 (y 900/1180)
  { text: "WIR WEISEN DICH EIN", startSec: 14.02, endSec: 16.47, offsetY: 240 }, // „eingewiesen" · cc-05
  { text: "FRAGEN? EINFACH ANRUFEN.", startSec: 16.9, endSec: 19.84, offsetY: 260 }, // „Fragen" · cc-06
];
