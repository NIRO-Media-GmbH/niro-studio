// ============================================================
// Craiss Untertitel-Mix — Caption-Seiten (2–5 Wörter) → Satz-Cues
// Standard: Grundzeile auf Brusthöhe; Treatments setzt man danach von Hand.
// ============================================================
import type { CaptionPage } from "../Subtitles";
import type { CaptionPlan, PlanCue } from "./plan";

const SENTENCE_END = /[.!?]["“”]?$/;

export const buildPlanFromPages = (video: string, pages: CaptionPage[]): CaptionPlan => {
  const cues: PlanCue[] = [];
  let group: CaptionPage[] = [];

  const flush = () => {
    if (group.length === 0) return;
    const starts: number[] = [];
    let n = 0;
    for (const p of group) {
      starts.push(n);
      n += p.tokens.length;
    }
    cues.push({
      id: `cc-${String(cues.length + 1).padStart(2, "0")}`,
      start: group[0].start,
      end: group[group.length - 1].end,
      tokens: group.flatMap((p) => p.tokens),
      pages: starts,
      treatment: "rail",
      zone: "chest",
      glass: null,
    });
    group = [];
  };

  for (const page of pages) {
    group.push(page);
    if (SENTENCE_END.test(page.tokens[page.tokens.length - 1].text)) flush();
  }
  flush();

  for (let i = 0; i < cues.length - 1; i++) cues[i].end = Math.min(cues[i].end, cues[i + 1].start);
  return { video, cues };
};

// Teilt einen (zu langen) Satz an einer Sinngrenze in zwei Cues „<id>a"/„<id>b".
// Beide Teile starten als Grundzeile; Hero/Kasten/Glas werden danach neu gesetzt.
export const splitCueAt = (plan: CaptionPlan, id: string, at: number): CaptionPlan => {
  const i = plan.cues.findIndex((c) => c.id === id);
  if (i < 0) throw new Error(`splitCueAt: ${id} fehlt`);
  const cue = plan.cues[i];
  if (at <= 0 || at >= cue.tokens.length) throw new Error(`splitCueAt: Index ${at} außerhalb von ${id}`);

  const r3 = (x: number) => Math.round(x * 1000) / 1000;
  const secondStart = r3(cue.tokens[at].start - 0.08);
  const base = { ...cue, treatment: "rail" as const, heroIndex: undefined, heroCount: undefined, boxIndices: undefined, glass: null };

  const first: PlanCue = {
    ...base,
    id: `${id}a`,
    tokens: cue.tokens.slice(0, at),
    pages: cue.pages.filter((p) => p < at),
    end: r3(Math.min(cue.tokens[at - 1].end + 0.6, secondStart)),
  };
  const second: PlanCue = {
    ...base,
    id: `${id}b`,
    start: secondStart,
    tokens: cue.tokens.slice(at),
    pages: [0, ...cue.pages.filter((p) => p > at).map((p) => p - at)],
  };
  return { ...plan, cues: [...plan.cues.slice(0, i), first, second, ...plan.cues.slice(i + 1)] };
};
