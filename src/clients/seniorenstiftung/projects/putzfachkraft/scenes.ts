// Seniorenstiftung — Putzfachkraft / Reinigungskraft (9:16, 25fps, 52.32s)
// v2: word-synced. atSec/emphasisAtSec = ABSOLUTE video seconds.
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  {
    kind: "highlight",
    startSec: 0.1,
    durationSec: 3.1,
    text: "Manche Arbeit fällt erst auf, wenn sie fehlt",
    emphasis: "fehlt",
    emphasisAtSec: 2.38,
  },
  {
    kind: "chips",
    startSec: 3.6,
    durationSec: 5.3,
    chips: [
      { label: "Saubere Zimmer", atSec: 3.84, icon: "glanz" },
      { label: "Gepflegte Flure", atSec: 5.08, icon: "check" },
      { label: "Wohlfühlen", atSec: 7.68, icon: "herz" },
    ],
  },
  {
    kind: "chips",
    startSec: 23.2,
    durationSec: 3.8,
    chips: [
      { label: "Respekt", atSec: 23.46, icon: "haende" },
      { label: "Hygiene", atSec: 24.26, icon: "tropfen" },
      { label: "Verantwortung", atSec: 25.62, icon: "schild" },
    ],
  },
  {
    kind: "highlight",
    startSec: 28.6,
    durationSec: 4.3,
    text: "Ein Team, das zusammenhält",
    emphasis: "zusammenhält",
    emphasisAtSec: 28.86,
  },
  {
    kind: "highlight",
    startSec: 33.6,
    durationSec: 7.7,
    text: "Deine Arbeit wird gesehen",
    emphasis: "wird gesehen",
    emphasisAtSec: 34.42,
  },
  {
    kind: "cta",
    startSec: 42.3,
    durationSec: 10.02,
    headline: "Werde Reinigungskraft",
    sub: "Jetzt bewerben",
    emphasis: "Reinigungskraft",
  },
];
