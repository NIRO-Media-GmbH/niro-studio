// Schlagwort-Chips Video 02 + Sperrfenster (Spec 2026-09-16).
// Start = Wortanfang des Ankerworts (captions/arbeitsalltag-v3.plan.json),
// offsetY = größtes y der überdeckten Sätze − 990.
import type { BlockedRange } from "../../Subtitles";
import type { Keyword } from "../../captionMix/keywords";

export const DURATION_SEC = 74.08; // Neuexport 11.09. 18:42: 1853 Frames (Endshot +1s)

export const BLOCKED: BlockedRange[] = [
  { startSec: 0, durationSec: 3.0 }, // Hook „MEIN ARBEITSALLTAG / BEI CRAISS"
  { startSec: 61.6, durationSec: DURATION_SEC - 61.6 }, // CTA
];

export const KEYWORDS: Keyword[] = [
  { text: "JEDEN TAG ZU HAUSE", startSec: 6.74, endSec: 10.0, offsetY: 110 }, // „jeden" · cc-02
  { text: "NAH- UND FERNVERKEHR", startSec: 11.54, endSec: 13.04, offsetY: 210 }, // „Nah-" · cc-03
  { text: "ALLE INFOS PER TABLET", startSec: 21.18, endSec: 24.68, offsetY: 160 }, // „Tablet" · cc-05
  { text: "NEUER, SCHÖNER LKW", startSec: 30.82, endSec: 33.3, offsetY: 190 }, // „neu" · cc-06 + „Schöner Lkw." (y 1150/1180)
  { text: "WERKSTATT: NUR 10 MINUTEN", startSec: 44.06, endSec: 46.82, offsetY: 190 }, // „zehn" · cc-09
  { text: "24/7 ERREICHBAR", startSec: 48.12, endSec: 51.62, offsetY: 190 }, // „24/7" · cc-10
];
