// ============================================================
// Craiss Untertitel-Mix — Plan-Schema und Prüfregeln
// Ein Cue = ein Satz. Spec: docs/superpowers/specs/2026-09-11-craiss-untertitel-mix-design.md
// ============================================================
import { z } from "zod";
import { BLOCK_HEIGHT, BOTTOM_LIMIT, BOX_LINE_H, CHIN_GAP, resolveBlock, wordboxLines } from "./layout";

export const zoneSchema = z.enum(["top", "side-l", "side-r", "chest"]);
export const treatmentSchema = z.enum(["rail", "hero-white", "hero-red", "hero-blue", "wordbox"]);
export const tokenSchema = z.object({ text: z.string(), start: z.number(), end: z.number() });
export const glassSchema = z.object({
  text: z.string(),
  startSec: z.number(),
  zone: zoneSchema,
  y: z.number().optional(),
});
export const planCueSchema = z.object({
  id: z.string(),
  start: z.number(),
  end: z.number(),
  tokens: z.array(tokenSchema).min(1),
  pages: z.array(z.number().int()).min(1),
  treatment: treatmentSchema,
  heroIndex: z.number().int().optional(),
  heroCount: z.number().int().min(1).optional(),
  boxIndices: z.array(z.number().int()).optional(),
  zone: zoneSchema,
  y: z.number().optional(),
  chinY: z.number().optional(),
  glass: glassSchema.nullable().optional(),
});
export const captionPlanSchema = z.object({ video: z.string(), cues: z.array(planCueSchema) });

export type Zone = z.infer<typeof zoneSchema>;
export type Treatment = z.infer<typeof treatmentSchema>;
export type PlanToken = z.infer<typeof tokenSchema>;
export type PlanCue = z.infer<typeof planCueSchema>;
export type CaptionPlan = z.infer<typeof captionPlanSchema>;

export const HERO_TREATMENTS: ReadonlySet<Treatment> = new Set(["hero-white", "hero-red", "hero-blue"]);

const pageOf = (pages: number[], index: number) => pages.filter((p) => p <= index).length - 1;

// Grundzeile einer Seite ohne die Aufzählungs-Wörter — die stehen schon im
// Kasten (UT-Korrektur 2026-09-11: „Autowäsche" war doppelt sichtbar).
export const pageTokensWithoutBox = (cue: PlanCue, from: number, to: number): PlanToken[] =>
  cue.tokens.slice(from, to).filter((_, i) => !cue.boxIndices?.includes(from + i));

export const validatePlan = (plan: CaptionPlan): string[] => {
  const errors: string[] = [];
  let lastHero: Treatment | null = null;
  let glassCount = 0;

  plan.cues.forEach((cue, i) => {
    const prev = plan.cues[i - 1];
    if (prev && cue.start < prev.end - 0.001) errors.push(`${cue.id}: überlappt ${prev.id}`);

    const pagesOk =
      cue.pages[0] === 0 &&
      cue.pages.every((p, k) => k === 0 || p > cue.pages[k - 1]) &&
      cue.pages.every((p) => p < cue.tokens.length);
    if (!pagesOk) errors.push(`${cue.id}: pages ungültig`);

    if (HERO_TREATMENTS.has(cue.treatment)) {
      const from = cue.heroIndex;
      const count = cue.heroCount ?? 1;
      if (from === undefined || from < 0 || from + count > cue.tokens.length) {
        errors.push(`${cue.id}: heroIndex fehlt oder außerhalb`);
      } else if (pagesOk && pageOf(cue.pages, from) !== pageOf(cue.pages, from + count - 1)) {
        errors.push(`${cue.id}: Hero-Wortgruppe liegt über einer Seitengrenze`);
      }
      if (lastHero === cue.treatment) errors.push(`${cue.id}: gleiche Hero-Variante wie der vorige Hero-Satz`);
      lastHero = cue.treatment;
    }

    if (cue.boxIndices?.some((b) => b < 0 || b >= cue.tokens.length)) errors.push(`${cue.id}: boxIndices außerhalb`);

    const box = resolveBlock(cue.zone, cue.y);
    // Wort-Kasten ohne Aufzählung: große Wörter können umbrechen → Zeilen schätzen
    const highlightBox = cue.treatment === "wordbox" && !(cue.boxIndices && cue.boxIndices.length > 0);
    const height = highlightBox
      ? Math.max(
          ...cue.pages.map((p, k) =>
            wordboxLines(cue.tokens.slice(p, cue.pages[k + 1] ?? cue.tokens.length).map((t) => t.text), box.width),
          ),
        ) * BOX_LINE_H
      : BLOCK_HEIGHT[cue.treatment];
    const bottom = box.top + height;
    if (bottom > BOTTOM_LIMIT) errors.push(`${cue.id}: Unterkante ${bottom} > ${BOTTOM_LIMIT}`);
    if (cue.chinY !== undefined && box.top < cue.chinY + CHIN_GAP) {
      errors.push(`${cue.id}: Oberkante ${box.top} zu nah am Kinn (${cue.chinY} + ${CHIN_GAP})`);
    }

    if (cue.glass) {
      glassCount++;
      if (cue.glass.startSec < cue.start || cue.glass.startSec >= cue.end) errors.push(`${cue.id}: Glas-Start außerhalb des Satzes`);
    }
  });

  if (glassCount > 2) errors.push(`Glas-Wörter: ${glassCount} > 2`);
  return errors;
};
