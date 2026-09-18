// Schlagwort-Chips Video 05 + Sperrfenster (Spec 2026-09-16).
// Start = Wortanfang des Ankerworts (captions/testimonial-v2.plan.json),
// offsetY = größtes y der überdeckten Sätze − 990.
import type { BlockedRange } from "../../Subtitles";
import type { Keyword } from "../../captionMix/keywords";

export const DURATION_SEC = 52.56; // Neuexport 11.09. 18:46: 1315 Frames

export const BLOCKED: BlockedRange[] = [
  // 2026-09-11: Mix-Look zeigt nur ganze Sätze → Sperren exakt = Sequenzen von
  // Craiss-Testimonial v3 (Hook, Chips, Flaggen, CTA; Dauern als Literale).
  { startSec: 0, durationSec: 2.28 }, // Hook „ICH MAG MEINE ARBEIT / LKW-FAHRER BEI CRAISS"
  { startSec: 3.32, durationSec: 2.48 }, // Zitat „JEDER TAG IST EIN GUTER TAG."
  { startSec: 6.88, durationSec: 1.92 }, // Zitat „DIE FREIHEIT. DIE RUHE."
  // „KEIN STRESS." entfaellt ab Overlay v3 (Kundenfeedback) — kein Sperrfenster.
  // ab 16,96s −0,52s (Neuexport 18:46 ohne „Kein Stress")
  { startSec: 28.44, durationSec: 1.88 }, // Zitat „JEDEN TAG ZU HAUSE."
  { startSec: 34.88, durationSec: 1.72 }, // Zitat „BEI CRAISS PASST'S."
  { startSec: 39.64, durationSec: 3.88 }, // Laender-Flaggen (HU/CZ/RO/LT)
  { startSec: 46.12, durationSec: DURATION_SEC - 46.12 }, // CTA auf dem Drohnen-Endshot
];

export const KEYWORDS: Keyword[] = [
  { text: "KINDHEITSTRAUM LKW", startSec: 10.94, endSec: 12.84, offsetY: 160 }, // „Bei (Kleine)" · cc-04a (Adrian)
  { text: "WERKSTATT: NUR 10 MINUTEN", startSec: 20.52, endSec: 22.02, offsetY: 160 }, // „zehn" · cc-05 (Jakub)
  { text: "TROTZ RENTE AM STEUER", startSec: 32.68, endSec: 34.84, offsetY: 190 }, // „Rente" · cc-08 (Opa Didi)
];
