// ============================================================
// Craiss Untertitel-Mix — Timing (Sichtbarkeit, Wort-Einblendung, Seiten)
// ============================================================
import { freeWindows, type BlockedRange } from "../Subtitles";

export { freeWindows, type BlockedRange };

export const LEAD_SEC = 0.08; // Wort erscheint so viel vor seinem Anfang
export const REVEAL_FRAMES = 5;

export type FrameWindow = { from: number; to: number };

// Ganze Sinneinheiten: sichtbar nur, wenn der Satz vom Anfang bis zum Ende
// des letzten Worts in EINEM freien Fenster liegt. Der Nachlauf nach dem
// letzten Wort darf am Fensterende gekappt werden.
export const cueWindow = (
  cue: { start: number; end: number; tokens: { end: number }[] },
  windows: FrameWindow[],
  fps: number,
): FrameWindow | null => {
  const from = Math.round(cue.start * fps);
  const lastWordEnd = Math.round(cue.tokens[cue.tokens.length - 1].end * fps);
  const to = Math.round(cue.end * fps);
  const w = windows.find((win) => win.from <= from && lastWordEnd <= win.to);
  return w ? { from, to: Math.min(to, w.to) } : null;
};

export const revealProgress = (tokenStart: number, frame: number, fps: number): number => {
  const at = Math.round((tokenStart - LEAD_SEC) * fps);
  return Math.min(1, Math.max(0, (frame - at) / REVEAL_FRAMES));
};

export const activeTokenIndex = (tokens: { start: number }[], t: number): number => {
  let idx = -1;
  tokens.forEach((tok, i) => {
    if (t >= tok.start - 0.02) idx = i;
  });
  return idx;
};

// Mindeststandzeit des letzten Worts einer Seite, bevor die nächste Seite kommt
// (UT-Korrektur 2026-09-11: „ja" stand nur 2 Frames). Die nächste Seite
// erscheint dann etwas später — nie ein Wort vor seinem Anfang.
export const MIN_LAST_WORD_SEC = 0.4;

export const currentPageIndex = (pages: number[], tokens: { start: number }[], t: number): number => {
  let idx = 0;
  pages.forEach((p, k) => {
    if (k === 0) return;
    const switchAt = Math.max(tokens[p].start - LEAD_SEC, tokens[p - 1].start - LEAD_SEC + MIN_LAST_WORD_SEC);
    if (t >= switchAt) idx = k;
  });
  return idx;
};

export const pageTokenRange = (pages: number[], tokenCount: number, pageIdx: number): [number, number] => [
  pages[pageIdx],
  pages[pageIdx + 1] ?? tokenCount,
];
