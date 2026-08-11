// ============================================================
// Top Fotografie — Drei Tipps (Overlay)
// 3 Tipps zur Studio-Auswahl, als Overlay ueber Sprecher-Video
// 9:16 portrait (1080x1920), 30fps, transparent
// ============================================================
//
// Jede Einblendung: 10s sichtbar, 2s Gap dazwischen
//   Tipp 1:   0s - 10s
//   Tipp 2:  12s - 22s
//   Tipp 3:  24s - 34s
//   Total:   34s

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
    title: "Gewinnspiele",
    subtitle: "Fallt nicht auf Foto-Gewinnspiele herein.",
    startSec: 0,
    durationSec: 10,
  },
  {
    num: "02",
    title: "Expertise",
    subtitle: "Ein gutes Studio hat Expertise in allen Bereichen.",
    startSec: 12,
    durationSec: 10,
  },
  {
    num: "03",
    title: "Ansprechpartner",
    subtitle: "Ein persönlicher Ansprechpartner sollte selbstverständlich sein.",
    startSec: 24,
    durationSec: 10,
  },
];

export const TOTAL_DURATION_SEC = 34;
