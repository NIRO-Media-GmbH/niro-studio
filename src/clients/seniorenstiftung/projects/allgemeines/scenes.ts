// Seniorenstiftung — Allgemeines Video (9:16, 25fps, 56.64s)
// v2: word-synced. atSec/emphasisAtSec = ABSOLUTE video seconds.
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  {
    kind: "highlight",
    startSec: 3.9,
    durationSec: 2.8,
    text: "Einen guten Arbeitgeber spürt man jeden Tag",
    emphasis: "spürt",
    emphasisAtSec: 6.1,
  },
  {
    kind: "highlight",
    startSec: 6.9,
    durationSec: 2.7,
    text: "Mitten in Prenzlauer Berg",
    emphasis: "Prenzlauer Berg",
    emphasisAtSec: 7.58,
  },
  {
    kind: "highlight",
    startSec: 19.9,
    durationSec: 2.0,
    text: "Mehr als ein Job",
    emphasis: "Job",
    emphasisAtSec: 21.08,
  },
  {
    kind: "chips",
    startSec: 22.4,
    durationSec: 7.5,
    chips: [
      { label: "Entwicklung", atSec: 22.64, icon: "stufen" },
      { label: "Klare Einarbeitung", atSec: 24.08, icon: "check" },
      { label: "Ein Team", atSec: 25.38, icon: "team" },
      { label: "Sinn", atSec: 29.24, icon: "herz" },
    ],
  },
  {
    kind: "highlight",
    startSec: 32.3,
    durationSec: 3.6,
    text: "Ein Lächeln zaubern",
    emphasis: "Lächeln",
    emphasisAtSec: 32.72,
  },
  {
    kind: "chips",
    startSec: 36.1,
    durationSec: 4.5,
    // Small chips → 2 rows of 3, block stays clear of the walking
    // server's face in this shot (scrub check 2026-07-03).
    fontSizeRatio: 0.024,
    chips: [
      { label: "Pflege", atSec: 36.3, icon: "puls" },
      { label: "Ausbildung", atSec: 36.98, icon: "buch" },
      { label: "Küche", atSec: 37.82, icon: "teller" },
      { label: "Service", atSec: 38.36, icon: "glanz" },
      { label: "Reinigung", atSec: 39.08, icon: "tropfen" },
      { label: "Betreuung", atSec: 39.94, icon: "haende" },
    ],
  },
  {
    kind: "highlight",
    startSec: 44.0,
    durationSec: 3.0,
    text: "Geborgen fühlen",
    emphasis: "Geborgen",
    emphasisAtSec: 44.24,
  },
  {
    kind: "cta",
    startSec: 47.5,
    durationSec: 9.14,
    headline: "Werde Teil der Seniorenstiftung",
    sub: "Jetzt bewerben",
    emphasis: "Seniorenstiftung",
  },
];
