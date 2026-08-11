// ============================================================
// Top Fotografie — Drei Fragen (Overlay)
// 3 Fragen an den Fotografen, als Overlay ueber Sprecher-Video
// 9:16 portrait (1080x1920), 30fps, transparent
// ============================================================
//
// Jede Einblendung: 10s sichtbar, 2s Gap dazwischen
//   Frage 1:   0s - 10s
//   Frage 2:  12s - 22s
//   Frage 3:  24s - 34s
//   Total:    34s

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
    title: "Referenzen",
    subtitle: "Frag nach echten Referenzen.",
    startSec: 0,
    durationSec: 10,
  },
  {
    num: "02",
    title: "Lieferzeit",
    subtitle: "Frag wie lange die Lieferung benötigt.",
    startSec: 12,
    durationSec: 10,
  },
  {
    num: "03",
    title: "Preis",
    subtitle: "Frag was im Preis alles enthalten ist.",
    startSec: 24,
    durationSec: 10,
  },
];

export const TOTAL_DURATION_SEC = 34;
