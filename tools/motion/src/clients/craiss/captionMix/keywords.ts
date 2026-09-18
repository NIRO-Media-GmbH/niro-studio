// ============================================================
// Craiss Schlagwort-Chips — Schema und Prüfregeln
// Spec: docs/superpowers/specs/2026-09-16-craiss-schlagwoerter-begruessung-design.md
// ============================================================
import { z } from "zod";
import type { BlockedRange } from "../Subtitles";

export const KEYWORD_MAX_CHARS = 32;
export const KEYWORD_MIN_SEC = 1.5;
export const KEYWORD_MAX_SEC = 3.5;
export const KEYWORD_MIN_GAP_SEC = 0.3;
const EPS = 0.005;

export const keywordSchema = z.object({
  text: z.string(),
  startSec: z.number(),
  endSec: z.number(),
  offsetY: z.number(),
});

export type Keyword = z.infer<typeof keywordSchema>;

const r2 = (v: number) => Math.round(v * 100) / 100;

export const shiftKeywords = (list: Keyword[], sec: number): Keyword[] =>
  list.map((k) => ({ ...k, startSec: r2(k.startSec + sec), endSec: r2(k.endSec + sec) }));

export const shiftBlocked = (list: BlockedRange[], sec: number): BlockedRange[] =>
  list.map((b) => ({ ...b, startSec: r2(b.startSec + sec) }));

export const validateKeywords = (list: Keyword[], blocked: BlockedRange[]): string[] => {
  const errors: string[] = [];
  list.forEach((k, i) => {
    const name = `„${k.text}"`;
    const chars = [...k.text].length;
    if (chars > KEYWORD_MAX_CHARS) errors.push(`${name}: ${chars} Zeichen > ${KEYWORD_MAX_CHARS}`);
    const dur = k.endSec - k.startSec;
    if (dur < KEYWORD_MIN_SEC - EPS || dur > KEYWORD_MAX_SEC + EPS) {
      errors.push(`${name}: Dauer ${dur.toFixed(2)} s außerhalb ${KEYWORD_MIN_SEC}–${KEYWORD_MAX_SEC} s`);
    }
    const prev = list[i - 1];
    if (prev && k.startSec < prev.endSec + KEYWORD_MIN_GAP_SEC - EPS) {
      errors.push(`${name}: Abstand zu „${prev.text}" < ${KEYWORD_MIN_GAP_SEC} s`);
    }
    for (const b of blocked) {
      const bEnd = b.startSec + b.durationSec;
      if (k.startSec < bEnd - EPS && k.endSec > b.startSec + EPS) {
        errors.push(`${name}: überlappt Sperrfenster ${b.startSec.toFixed(2)}–${bEnd.toFixed(2)} s`);
      }
    }
  });
  return errors;
};
