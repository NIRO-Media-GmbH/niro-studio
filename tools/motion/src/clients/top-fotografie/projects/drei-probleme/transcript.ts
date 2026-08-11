// ============================================================
// Top Fotografie — Drei Probleme (Overlay)
// 3 Gruende warum Schulfotos oft schlecht sind
// 9:16 portrait (1080x1920), 30fps, transparent
// ============================================================
//
// Jede Einblendung: 10s sichtbar, 2s Gap dazwischen
//   Problem 1:   0s - 10s
//   Problem 2:  12s - 22s
//   Problem 3:  24s - 34s
//   Total:      34s

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
    title: "Licht",
    subtitle: "Lieblos ausgeleuchtet, jedes Gesicht wirkt blass.",
    startSec: 0,
    durationSec: 10,
  },
  {
    num: "02",
    title: "Bindung",
    subtitle: "Keine Bindung zu den Kindern.",
    startSec: 12,
    durationSec: 10,
  },
  {
    num: "03",
    title: "Zeitdruck",
    subtitle: "Zeitdruck und schlechte Planung.",
    startSec: 24,
    durationSec: 10,
  },
];

export const TOTAL_DURATION_SEC = 34;
