// Schlagwort-Chips Video 04 + Sperrfenster (Spec 2026-09-16).
// Start = Wortanfang des Ankerworts (captions/funnel-v4.plan.json),
// offsetY = größtes y der überdeckten Sätze − 990.
import type { BlockedRange } from "../../Subtitles";
import type { Keyword } from "../../captionMix/keywords";

export const DURATION_SEC = 59.08;

export const BLOCKED: BlockedRange[] = [
  // 2026-09-11 exakt = Sequenzen von Craiss-Funnel (auf V4 ausgerichtet, per
  // Differenz animiert − ohne Animation bestätigt). Dauern als Literale, damit
  // Math.floor in freeWindows nicht an Rundungsresten einen Frame verliert.
  { startSec: 0.64, durationSec: 2.48 }, // Chef-Namenskarte "MICHAEL CRAISS"
  { startSec: 5.24, durationSec: 1.4 }, // Standort-Chip "MUEHLACKER"
  { startSec: 21.0, durationSec: 1.68 }, // Swipe-Transition
  { startSec: 23.76, durationSec: 3.56 }, // Namenskarte "EVA"
  { startSec: 32.48, durationSec: 3.04 }, // "KEIN LEBENSLAUF / KEIN ANSCHREIBEN"
  { startSec: 35.72, durationSec: 1.36 }, // Schritt 1 "TRAG DICH EIN"
  { startSec: 37.08, durationSec: 2.44 }, // Schritt 2 "TELEFONAT"
  { startSec: 39.56, durationSec: 3.96 }, // Phone-Chip "SEI ERREICHBAR"
  { startSec: 46.88, durationSec: 2.44 }, // Schritt 3 "PERSÖNLICHES KENNENLERNEN"
  { startSec: 50.32, durationSec: 2.6 }, // Outro "WORAUF WARTEST DU?"
  { startSec: 54.72, durationSec: DURATION_SEC - 54.72 }, // CTA
];

export const KEYWORDS: Keyword[] = [
  { text: "FAMILIENUNTERNEHMEN", startSec: 6.68, endSec: 8.18, offsetY: 160 }, // „Familienunternehmen" · cc-03 (nach Mühlacker-Chip)
  { text: "KEIN 08/15-JOB", startSec: 14.7, endSec: 16.46, offsetY: 160 }, // „0815-Arbeitsverhältnis" · cc-04ba
  { text: "BEI UNS ANKOMMEN", startSec: 17.56, endSec: 19.41, offsetY: 160 }, // „schauen" · cc-04bb
  { text: "SO EINFACH STARTEST DU", startSec: 30.1, endSec: 32.22, offsetY: 190 }, // „starten" · cc-08a
];
