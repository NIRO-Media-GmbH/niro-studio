import { test } from "node:test";
import assert from "node:assert/strict";
import { captionPlanSchema, pageTokensWithoutBox, validatePlan, type PlanCue } from "./plan";

const tok = (text: string, start: number) => ({ text, start, end: start + 0.3 });
const cue = (over: Partial<PlanCue>): PlanCue => ({
  id: "cc-01",
  start: 1,
  end: 3,
  tokens: [tok("Das", 1.08), tok("ist", 1.4), tok("kinderleicht", 1.8), tok("gebaut.", 2.3)],
  pages: [0],
  treatment: "rail",
  zone: "chest",
  glass: null,
  ...over,
});

test("gültiger Plan parst und hat keine Fehler", () => {
  const plan = captionPlanSchema.parse({ video: "x", cues: [cue({})] });
  assert.deepEqual(validatePlan(plan), []);
});

test("Aufzählungs-Wörter fehlen in der Grundzeile ihrer Seite (keine Doppelung)", () => {
  const c = cue({ treatment: "wordbox", boxIndices: [2], tokens: [tok("wo", 1), tok("ist", 1.2), tok("Büro,", 1.4), tok("wo", 1.8)], pages: [0, 3] });
  assert.deepEqual(pageTokensWithoutBox(c, 0, 3).map((t) => t.text), ["wo", "ist"]);
  assert.deepEqual(pageTokensWithoutBox(c, 3, 4).map((t) => t.text), ["wo"]);
  assert.equal(pageTokensWithoutBox({ ...c, boxIndices: undefined }, 0, 3).length, 3);
});

test("Wort-Kasten mit drei Zeilen reicht unter die Plattform-UI → Fehler", () => {
  const lang = cue({ treatment: "wordbox", y: 1180, tokens: [tok("Wenn", 1), tok("bei", 1.2), tok("diesem", 1.4), tok("Telefonat", 1.8)] });
  assert.match(validatePlan({ video: "x", cues: [lang] }).join("\n"), /Unterkante/);
  const kurz = cue({ treatment: "wordbox", y: 1180, tokens: [tok("Lkw", 1), tok("ist", 1.2), tok("neu.", 1.4)] });
  assert.deepEqual(validatePlan({ video: "x", cues: [kurz] }), []);
});

test("Hero ohne heroIndex ist ein Fehler", () => {
  const errs = validatePlan({ video: "x", cues: [cue({ treatment: "hero-white" })] });
  assert.match(errs.join("\n"), /heroIndex/);
});

test("zwei Hero-Sätze hintereinander mit gleicher Variante sind ein Fehler", () => {
  const errs = validatePlan({
    video: "x",
    cues: [
      cue({ id: "cc-01", treatment: "hero-red", heroIndex: 2 }),
      cue({ id: "cc-02", start: 3, end: 5, treatment: "rail" }),
      cue({ id: "cc-03", start: 5, end: 7, treatment: "hero-red", heroIndex: 2 }),
    ],
  });
  assert.match(errs.join("\n"), /cc-03: gleiche Hero-Variante/);
});

test("Hero über eine Seitengrenze ist ein Fehler", () => {
  const errs = validatePlan({ video: "x", cues: [cue({ treatment: "hero-blue", heroIndex: 1, heroCount: 2, pages: [0, 2] })] });
  assert.match(errs.join("\n"), /Seitengrenze/);
});

test("mehr als zwei Glas-Wörter sind ein Fehler", () => {
  const glass = { text: "IMMER", startSec: 1.5, zone: "top" as const };
  const errs = validatePlan({
    video: "x",
    cues: [1, 2, 3].map((n) => cue({ id: `cc-0${n}`, start: n * 2, end: n * 2 + 1.9, glass: { ...glass, startSec: n * 2 + 0.5 } })),
  });
  assert.match(errs.join("\n"), /Glas-Wörter: 3 > 2/);
});

test("Oberkante zu nah am Kinn und Unterkante zu tief sind Fehler", () => {
  assert.match(validatePlan({ video: "x", cues: [cue({ y: 800, chinY: 720 })] }).join("\n"), /zu nah am Kinn/);
  assert.match(validatePlan({ video: "x", cues: [cue({ y: 1400 })] }).join("\n"), /Unterkante 1530 > 1500/);
});

test("überlappende Sätze und ungültige pages sind Fehler", () => {
  const errs = validatePlan({ video: "x", cues: [cue({ id: "cc-01" }), cue({ id: "cc-02", start: 2.5, end: 4, pages: [1] })] });
  assert.match(errs.join("\n"), /cc-02: überlappt cc-01/);
  assert.match(errs.join("\n"), /cc-02: pages ungültig/);
});
