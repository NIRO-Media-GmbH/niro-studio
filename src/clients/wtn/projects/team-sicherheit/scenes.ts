// WTN — 1.3 "Team & sicherer Ausbildungsberuf" (9:16, 25fps, ~62s)
// Word-synced (transcripts/03-team-sicherheit.words.json).
// Testimonial: Teil vom Team, sicherer Ausbildungsberuf, Vielfalt.
// Finale: Stat-Doppel "30 Jahre · 58 Ausbildungen".
import type { Scene } from "../../components";

export const SCENES: Scene[] = [
  {
    kind: "highlight",
    startSec: 1.6,
    durationSec: 3.2,
    text: "Direkt Teil vom Team",
    emphasis: "Team",
    emphasisAtSec: 3.52,
    variant: "plain",
  },
  {
    kind: "highlight",
    startSec: 12.4,
    durationSec: 3.6,
    text: "Ein sicherer Ausbildungsberuf",
    emphasis: "sicherer",
    emphasisAtSec: 13.42,
  },
  {
    kind: "chips",
    startSec: 19.5,
    durationSec: 4.4,
    fontSizeRatio: 0.028,
    chips: [
      { label: "Vielfalt an Technologien", atSec: 19.92, icon: "technik" },
      { label: "Vielfalt an Wissen", atSec: 21.86, icon: "buch" },
    ],
  },
  {
    kind: "highlight",
    startSec: 45.4,
    durationSec: 3.4,
    text: "Ein sicherer Arbeitsplatz",
    emphasis: "sicherer",
    emphasisAtSec: 47.34,
  },
  {
    kind: "stat",
    startSec: 50.2,
    durationSec: 2.2,
    value: 30,
    suffix: "",
    label: "Jahre WTN",
    emphasisAtSec: 51.36,
  },
  {
    kind: "stat",
    startSec: 52.4,
    durationSec: 2.7,
    value: 58,
    label: "Ausbildungen",
    emphasisAtSec: 53.68,
  },
  {
    kind: "cta",
    startSec: 55.1,
    durationSec: 6.94,
    headline: "Der nächste Platz wartet auf dich",
    sub: "Jetzt bewerben",
    emphasis: "wartet auf dich",
  },
];
