// Seniorenstiftung — Küchenhilfe (9:16, 25fps, 38.8s)
// v2: word-synced. atSec/emphasisAtSec = ABSOLUTE video seconds.
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  {
    kind: "highlight",
    startSec: 0.3,
    durationSec: 1.9,
    text: "So dankbar",
    emphasis: "dankbar",
    emphasisAtSec: 0.7,
  },
  {
    kind: "highlight",
    startSec: 14.8,
    durationSec: 2.3,
    text: "Willkommen & gesehen",
    emphasis: "gesehen",
    emphasisAtSec: 15.88,
  },
  {
    kind: "chips",
    startSec: 17.8,
    durationSec: 4.8,
    chips: [
      { label: "Früh- & Spätschichten", atSec: 18.0, icon: "uhr" },
      { label: "Teilzeit", atSec: 19.5, icon: "kalender" },
      { label: "Feste Abläufe", atSec: 20.54, icon: "check" },
    ],
  },
  {
    kind: "highlight",
    startSec: 23.1,
    durationSec: 2.3,
    text: "Genau die Struktur",
    emphasis: "Struktur",
    emphasisAtSec: 23.3,
  },
  {
    kind: "highlight",
    startSec: 27.0,
    durationSec: 2.2,
    text: "Eine Aufgabe mit echtem Sinn",
    emphasis: "Sinn",
    emphasisAtSec: 28.66,
  },
  // "Offenes Team" (29.6-31.8) REMOVED: frontal close-up fills the
  // frame — any pill would cover her mouth (scrub check 2026-07-03).
  // Her smiling delivery carries the moment on its own.
  {
    kind: "cta",
    startSec: 32.8,
    durationSec: 6.0,
    headline: "Küchen- & Servicekraft werden",
    sub: "Bewirb dich jetzt",
    emphasis: "Küchen- & Servicekraft",
  },
];
