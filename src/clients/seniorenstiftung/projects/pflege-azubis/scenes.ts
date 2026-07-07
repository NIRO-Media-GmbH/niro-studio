// Seniorenstiftung — Pflege Azubis (9:16, 25fps, 57.0s)
// v2: word-synced. atSec/emphasisAtSec = ABSOLUTE video seconds.
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  {
    kind: "highlight",
    startSec: 3.7,
    durationSec: 2.8,
    text: "Wirklich gebraucht werden",
    emphasis: "gebraucht",
    emphasisAtSec: 4.34,
  },
  {
    kind: "chips",
    startSec: 19.9,
    durationSec: 5.7,
    // Compact: keeps the block low, clear of the second nurse's face
    // in the corridor shot (scrub check 2026-07-03).
    fontSizeRatio: 0.026,
    chips: [
      { label: "Im Alltag", atSec: 20.1, icon: "kalender" },
      { label: "Mit Menschen", atSec: 21.44, icon: "herz" },
      { label: "Im Team", atSec: 22.4, icon: "team" },
      { label: "Schritt für Schritt", atSec: 23.56, icon: "stufen" },
    ],
  },
  {
    kind: "chips",
    startSec: 34.6,
    durationSec: 6.3,
    fontSizeRatio: 0.026,
    chips: [
      { label: "Blutdruck messen", atSec: 34.82, icon: "puls" },
      { label: "Puls messen", atSec: 35.62, icon: "herz" },
      { label: "Umgang mit Menschen", atSec: 38.5, icon: "haende" },
    ],
  },
  {
    kind: "highlight",
    startSec: 43.3,
    durationSec: 3.6,
    text: "Ein Lächeln zaubern",
    emphasis: "Lächeln",
    emphasisAtSec: 43.76,
  },
  {
    kind: "highlight",
    startSec: 47.8,
    durationSec: 1.9,
    text: "Haus mit Garten",
    emphasis: "Garten",
    emphasisAtSec: 49.02,
  },
  {
    kind: "cta",
    startSec: 50.0,
    durationSec: 7.0,
    headline: "Starte deine Ausbildung",
    sub: "Jetzt bewerben",
    emphasis: "Ausbildung",
  },
];
