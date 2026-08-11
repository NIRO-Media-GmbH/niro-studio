// WTN — 1.1 "Dein erster Tag bei WTN" (9:16, 25fps, ~52.5s)
// Word-synced. All *AtSec are ABSOLUTE video seconds from the
// ElevenLabs word index (transcripts/01-erster-tag.words.json).
// Testimonial: Azubi über Einstieg, Augenhöhe, "große Familie".
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  {
    kind: "highlight",
    startSec: 20.2,
    durationSec: 3.4,
    text: "Auf Augenhöhe",
    emphasis: "Augenhöhe",
    emphasisAtSec: 22.44,
    variant: "plain",
  },
  {
    kind: "highlight",
    startSec: 29.6,
    durationSec: 3.2,
    text: "Direkt ins Praktische",
    emphasis: "Praktische",
    emphasisAtSec: 31.48,
  },
  {
    kind: "highlight",
    startSec: 36.5,
    durationSec: 3.4,
    text: "Wie eine große Familie",
    emphasis: "Familie",
    emphasisAtSec: 38.12,
    variant: "plain",
  },
  {
    kind: "highlight",
    startSec: 41.4,
    durationSec: 3.3,
    text: "Arbeiten mit Metall",
    emphasis: "Metall",
    emphasisAtSec: 43.88,
  },
  {
    kind: "cta",
    startSec: 46.5,
    durationSec: 6.0,
    headline: "Dein erster Tag bei WTN",
    sub: "Jetzt bewerben",
    emphasis: "WTN",
  },
];
