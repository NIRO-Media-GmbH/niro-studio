// WTN — 1.2 "Technik, die du woanders nicht anfasst" (9:16, 25fps, ~59.8s)
// Word-synced (transcripts/02-technik.words.json).
// Testimonial: moderner Maschinenpark, PECM/Rodieren/HSC/3D-Druck.
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  {
    kind: "highlight",
    startSec: 9.0,
    durationSec: 3.5,
    text: "Selber etwas herstellen",
    emphasis: "herstellen",
    emphasisAtSec: 11.96,
  },
  {
    kind: "highlight",
    startSec: 20.4,
    durationSec: 3.2,
    text: "Neue Techniken",
    emphasis: "Techniken",
    emphasisAtSec: 21.96,
    variant: "plain",
  },
  {
    kind: "highlight",
    startSec: 27.3,
    durationSec: 3.4,
    text: "Moderner Maschinenpark",
    emphasis: "Maschinenpark",
    emphasisAtSec: 29.48,
  },
  {
    kind: "chips",
    startSec: 37.8,
    durationSec: 8.2,
    fontSizeRatio: 0.026,
    chips: [
      { label: "PECM", atSec: 38.78, icon: "funke" },
      { label: "Erodieren", atSec: 39.82, icon: "zahnrad" },
      { label: "HSC-Fräsen", atSec: 41.34, icon: "werkzeug" },
      { label: "3D-Druck", atSec: 42.86, icon: "drucker3d" },
    ],
  },
  {
    kind: "highlight",
    startSec: 51.4,
    durationSec: 3.4,
    text: "Kein Zuschauen",
    emphasis: "Zuschauen",
    emphasisAtSec: 54.28,
    variant: "plain",
  },
  {
    kind: "cta",
    startSec: 55.1,
    durationSec: 4.66,
    headline: "Technik, die du woanders nicht anfasst",
    sub: "Jetzt bewerben",
    emphasis: "woanders",
  },
];
