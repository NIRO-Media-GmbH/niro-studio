// ============================================================
// Top Fotografie — Drei Versprechen
// Expanding list overlay · Timing-Daten
// Video: 9:16 portrait (1080×1920), 30fps, transparent
// ============================================================
//
// Timing: each item appears after 5s, box expands downward
//   Item 1:  0s  (box appears with first item)
//   Item 2:  5s  (box expands, second item fades in)
//   Item 3: 10s  (box expands again, third item fades in)
//   Hold:   15s  (all three visible)
//   Out:    ~18s
//   Total:  20s

export interface ListItem {
  text: string;
  startSec: number;
}

export const ITEMS: ListItem[] = [
  {
    text: "Kein Kind verl\u00E4sst unser Set ohne ein Foto, auf das es stolz sein kann.",
    startSec: 0,
  },
  {
    text: "Kein Ablauf ohne klaren Plan.",
    startSec: 5,
  },
  {
    text: "Keine Lieferung, mit der wir selbst nicht zufrieden sind.",
    startSec: 10,
  },
];

export const TOTAL_DURATION_SEC = 20;
