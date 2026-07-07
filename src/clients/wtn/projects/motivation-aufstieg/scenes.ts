// WTN — 1.5 "Motivation & Aufstieg" (9:16, 25fps, ~63.8s)
// Word-synced (transcripts/05-motivation-aufstieg.words.json).
// Testimonial: Ausbildung → Meister → Produktionsleiter, Weiterbildung.
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  {
    kind: "highlight",
    startSec: 3.6,
    durationSec: 3.2,
    text: "Alle Wege stehen offen",
    emphasis: "offen",
    emphasisAtSec: 5.18,
    variant: "plain",
  },
  {
    kind: "highlight",
    startSec: 9.5,
    durationSec: 3.4,
    text: "WTN bildet dich weiter",
    emphasis: "weiter",
    emphasisAtSec: 10.78,
  },
  {
    kind: "highlight",
    startSec: 16.9,
    durationSec: 3.0,
    text: "Jetzt: der Meister",
    emphasis: "Meister",
    emphasisAtSec: 18.12,
  },
  {
    kind: "stat",
    startSec: 27.0,
    durationSec: 3.0,
    value: 20,
    prefix: "über ",
    label: "Mitarbeiter im Team",
    emphasisAtSec: 28.34,
  },
  {
    kind: "chips",
    startSec: 30.0,
    durationSec: 4.6,
    fontSizeRatio: 0.028,
    chips: [
      { label: "Drehen", atSec: 30.38, icon: "zahnrad" },
      { label: "Fräsen", atSec: 30.92, icon: "werkzeug" },
      { label: "HSC-Fräsen", atSec: 32.0, icon: "praezision" },
      { label: "CAD / CAM", atSec: 33.24, icon: "technik" },
    ],
  },
  {
    kind: "highlight",
    startSec: 37.5,
    durationSec: 3.6,
    text: "Gelernt als Werkzeugmechaniker",
    emphasis: "Werkzeugmechaniker",
    emphasisAtSec: 38.68,
  },
  {
    kind: "highlight",
    startSec: 53.4,
    durationSec: 3.6,
    text: "Aufgestiegen zum Produktionsleiter",
    emphasis: "Produktionsleiter",
    emphasisAtSec: 55.84,
    variant: "plain",
  },
  {
    kind: "cta",
    startSec: 57.4,
    durationSec: 6.36,
    headline: "Wie weit du gehst, entscheidest du",
    sub: "Deine Ausbildung bei WTN",
    emphasis: "entscheidest du",
  },
];
