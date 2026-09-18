// ============================================================
// Craiss Video 03 — Intro-Layout (aus dem Resolve-Umbau) und Wischer-Timing.
// Voll deckend auf cutFrame − 1 und cutFrame; Einlauf ease-in, Auslauf ease-out.
// ============================================================
import { z } from "zod";

export const countrySchema = z.enum(["PL", "HU", "RO", "CZ", "CRAISS"]);

export const wipeSchema = z.object({
  country: countrySchema,
  cutFrame: z.number().int(),
  inFrames: z.number().int().min(0),
  outFrames: z.number().int().min(1),
});

export const introLayoutSchema = z
  .object({
    fps: z.literal(25),
    shiftFrames: z.number().int().min(0),
    montageFrames: z.number().int(),
    wipes: z.array(wipeSchema).length(5),
    greetings: z.array(z.object({ text: z.string(), fromFrame: z.number().int() })).length(4),
    helloToFrame: z.number().int(),
    titleChip: z.object({ text: z.string(), fromFrame: z.number().int(), toFrame: z.number().int(), offsetY: z.number() }),
  })
  .passthrough();

export type Wipe = z.infer<typeof wipeSchema>;
export type IntroLayout = z.infer<typeof introLayoutSchema>;

// Panel-Versatz in Bildbreiten: 1 = rechts draußen, 0 = deckt voll, −1 = links draußen, null = unsichtbar.
export const wipeOffset = (frame: number, w: Wipe): number | null => {
  const holdStart = w.cutFrame - 1;
  if (frame >= holdStart && frame <= w.cutFrame) return 0;
  if (frame < holdStart) {
    const k = frame - (holdStart - w.inFrames) + 1; // 1..inFrames
    if (k < 1) return null;
    const p = k / (w.inFrames + 1);
    return 1 - p * p;
  }
  const k = frame - w.cutFrame; // 1..outFrames
  if (k > w.outFrames) return null;
  const p = k / (w.outFrames + 1);
  return -(1 - (1 - p) * (1 - p));
};

export const greetingIndexAt = (frame: number, greetings: { fromFrame: number }[]): number => {
  let idx = -1;
  greetings.forEach((g, i) => {
    if (frame >= g.fromFrame) idx = i;
  });
  return idx;
};

export const introEndFrame = (layout: IntroLayout): number =>
  Math.max(...layout.wipes.map((w) => w.cutFrame + w.outFrames)) + 1;
