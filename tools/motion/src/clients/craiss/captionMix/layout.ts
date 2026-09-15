// ============================================================
// Craiss Untertitel-Mix — Zonen und Grenzwerte (Basis 1080×1920)
// Spec: docs/superpowers/specs/2026-09-11-craiss-untertitel-mix-design.md
// ============================================================
import type { Treatment, Zone } from "./plan";

export const BASE_W = 1080;
export const MARGIN_X = 54;
export const SIDE_WIDTH = 620;
export const BOTTOM_LIMIT = 1500; // darunter liegt die Plattform-UI
export const CHIN_GAP = 110; // Mindestabstand Oberkante ↔ Kinn

// top 18–32 %, side 30–55 %, chest = Nahaufnahme Brusthöhe
export const ZONE_DEFAULT_TOP: Record<Zone, number> = {
  top: 400,
  "side-l": 700,
  "side-r": 700,
  chest: 1150,
};

// Geschätzte Blockhöhen (px) für die Unterkanten-Prüfung
export const BLOCK_HEIGHT: Record<Treatment, number> = {
  rail: 130, // zwei Zeilen Grundzeile
  "hero-white": 300, // Grundzeile + Hero 130 px + Grundzeile
  "hero-red": 260,
  "hero-blue": 220,
  wordbox: 280, // Grundzeile + Kastenwort bzw. zwei Kastenzeilen
};

// Wort-Kasten im Hervorhebungs-Modus: Zeilenzahl per Wortbreiten-Schätzung
// (Laski Slab Black 110 px, Versalien; an den Kontaktbögen 11.09. kalibriert:
// „MICH AUF DICH" passt in eine Zeile, „ICH FREUE MICH" nicht).
export const BOX_CHAR_W = 70;
export const BOX_WORD_PAD = 32; // 16 px Innenabstand links/rechts je Wort
export const BOX_SPACE = 30;
export const BOX_LINE_H = 129; // 110 × 1,1 + 8 px Außenabstand

export const wordboxLines = (words: string[], maxWidth: number = BASE_W - 2 * MARGIN_X): number => {
  let lines = 1;
  let line = 0;
  for (const word of words) {
    const width = word.replace(/[.,!?;:"„“”]+/g, "").length * BOX_CHAR_W + BOX_WORD_PAD;
    const add = line === 0 ? width : width + BOX_SPACE;
    if (line > 0 && line + add > maxWidth) {
      lines++;
      line = width;
    } else {
      line += add;
    }
  }
  return lines;
};

export type Align = "center" | "left" | "right";
export type BlockBox = { top: number; left: number; width: number; align: Align };

export const resolveBlock = (zone: Zone, y?: number): BlockBox => {
  const top = y ?? ZONE_DEFAULT_TOP[zone];
  if (zone === "side-l") return { top, left: MARGIN_X, width: SIDE_WIDTH, align: "left" };
  if (zone === "side-r") return { top, left: BASE_W - MARGIN_X - SIDE_WIDTH, width: SIDE_WIDTH, align: "right" };
  return { top, left: MARGIN_X, width: BASE_W - 2 * MARGIN_X, align: "center" };
};
