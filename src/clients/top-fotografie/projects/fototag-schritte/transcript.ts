// ============================================================
// Top Fotografie — Fototag Schritte (Overlay)
// 4 steps with title + subtitle overlay on speaker video
// 9:16 portrait (1080×1920), 30fps, transparent
// ============================================================
//
// Each step: 15s visible, 2s gap between
//   Step 1:   0s – 15s
//   Step 2:  17s – 32s
//   Step 3:  34s – 49s
//   Step 4:  51s – 66s
//   Total:   66s

export interface StepEntry {
  num: string;
  title: string;
  subtitle: string;
  startSec: number;
  durationSec: number;
}

export const STEPS: StepEntry[] = [
  {
    num: "01",
    title: "Vorbereitung",
    subtitle: "Aufbau, Equipment & Zeitplan stehen bevor die erste Klasse kommt.",
    startSec: 0,
    durationSec: 15,
  },
  {
    num: "02",
    title: "Fester Zeitplan",
    subtitle: "Jede Klasse hat ein festes Zeitfenster. Kein Warten, kein Durcheinander.",
    startSec: 17,
    durationSec: 15,
  },
  {
    num: "03",
    title: "Klarer Ablauf",
    subtitle: "Wir f\u00FChren die Kinder. Kein Lehrer muss nebenher f\u00FCr Ruhe sorgen.",
    startSec: 34,
    durationSec: 15,
  },
  {
    num: "04",
    title: "Abbau",
    subtitle: "Fertig, weg \u2014 ohne den Schulbetrieb l\u00E4nger zu st\u00F6ren als n\u00F6tig.",
    startSec: 51,
    durationSec: 15,
  },
];

export const TOTAL_DURATION_SEC = 66;
