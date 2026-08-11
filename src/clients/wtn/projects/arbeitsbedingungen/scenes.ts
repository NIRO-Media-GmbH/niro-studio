// WTN — 1.4 "Arbeitsbedingungen & Wir-Gefühl" (9:16, 25fps, ~61.3s)
// Word-synced (transcripts/04-arbeitsbedingungen.words.json).
// Testimonial: flache Hierarchie, "Chef wird geduzt", große Familie.
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  {
    kind: "highlight",
    startSec: 1.3,
    durationSec: 3.6,
    text: "Nicht wetterabhängig",
    emphasis: "wetterabhängig",
    emphasisAtSec: 2.5,
  },
  {
    kind: "highlight",
    startSec: 12.9,
    durationSec: 3.4,
    text: "Jeder hilft jedem",
    emphasis: "jedem",
    emphasisAtSec: 14.26,
    variant: "plain",
  },
  {
    kind: "highlight",
    startSec: 28.4,
    durationSec: 3.6,
    text: "Der Chef wird geduzt",
    emphasis: "geduzt",
    emphasisAtSec: 30.08,
  },
  {
    kind: "highlight",
    startSec: 43.2,
    durationSec: 3.2,
    text: "Wie eine große Familie",
    emphasis: "Familie",
    emphasisAtSec: 44.84,
  },
  {
    kind: "cta",
    startSec: 56.0,
    durationSec: 5.32,
    headline: "Nicht wie überall. Sondern WTN",
    sub: "Jetzt bewerben",
    emphasis: "WTN",
  },
];
