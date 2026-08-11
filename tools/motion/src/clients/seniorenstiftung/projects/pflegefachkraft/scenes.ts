// Seniorenstiftung — Pflegefachkraft (9:16, 25fps, 55.72s)
// v2: word-synced. All atSec/emphasisAtSec are ABSOLUTE video seconds
// from the ElevenLabs word index (transcripts/words-index.json).
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  {
    kind: "highlight",
    startSec: 2.0,
    durationSec: 2.5,
    text: "Mehr als Aufgaben",
    emphasis: "Aufgaben",
    emphasisAtSec: 3.44,
  },
  {
    kind: "chips",
    startSec: 5.1,
    // Ends BEFORE the cut at ~11.3s — the next shot has a low-seated
    // face that the chip block would cover (scrub check 2026-07-03).
    durationSec: 6.0,
    fontSizeRatio: 0.026,
    chips: [
      { label: "Menschen", atSec: 5.32, icon: "herz" },
      { label: "Vertrauen", atSec: 6.66, icon: "haende" },
      { label: "Nähe", atSec: 8.16, icon: "glanz" },
      { label: "Team", atSec: 9.88, icon: "team" },
    ],
  },
  {
    kind: "highlight",
    startSec: 22.8,
    durationSec: 2.5,
    text: "Ein Arbeitsplatz mit Perspektive",
    emphasis: "Perspektive",
    emphasisAtSec: 23.96,
  },
  {
    kind: "chips",
    startSec: 25.5,
    durationSec: 3.5,
    chips: [
      { label: "Fort- & Weiterbildung", atSec: 25.74, icon: "buch" },
      { label: "Klare Einarbeitung", atSec: 27.24, icon: "check" },
    ],
  },
  {
    kind: "highlight",
    startSec: 30.6,
    durationSec: 2.8,
    text: "Geborgenheit & Liebe",
    emphasis: "Geborgenheit",
    emphasisAtSec: 30.8,
  },
  {
    kind: "chips",
    startSec: 38.1,
    durationSec: 5.9,
    chips: [
      { label: "Respekt", atSec: 38.32, icon: "haende" },
      { label: "Kommunikation", atSec: 39.16, icon: "sprechblase" },
      { label: "Team", atSec: 40.92, icon: "team" },
    ],
  },
  {
    kind: "cta",
    startSec: 48.2,
    durationSec: 7.52,
    headline: "Werde Pflegefachkraft",
    sub: "Jetzt bewerben",
    emphasis: "Pflegefachkraft",
  },
];
