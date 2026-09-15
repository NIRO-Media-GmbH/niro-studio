import { test } from "node:test";
import assert from "node:assert/strict";
import { buildPlanFromPages, splitCueAt } from "./buildPlan";

const page = (start: number, end: number, words: string[]) => ({
  start,
  end,
  tokens: words.map((text, i) => ({ text, start: start + 0.08 + i * 0.3, end: start + 0.3 + i * 0.3 })),
});

test("Seiten werden bis zum Satzende zu einem Cue zusammengefasst", () => {
  const plan = buildPlanFromPages("v", [
    page(1.0, 2.0, ["Keiner", "hat", "Probleme,", "egal"]),
    page(2.0, 3.1, ["ob", "jung", "oder", "alt."]),
    page(3.2, 4.0, ["Jeder", "kommt", "klar", "damit."]),
  ]);
  assert.equal(plan.cues.length, 2);
  assert.deepEqual(plan.cues[0].pages, [0, 4]);
  assert.equal(plan.cues[0].tokens.length, 8);
  assert.equal(plan.cues[0].id, "cc-01");
  assert.equal(plan.cues[1].id, "cc-02");
  assert.equal(plan.cues[0].treatment, "rail");
  assert.equal(plan.cues[0].zone, "chest");
});

test("splitCueAt teilt einen Satz an einem Wortindex und rechnet pages um", () => {
  const plan = buildPlanFromPages("v", [
    page(1.0, 2.0, ["Wenn", "du", "starten", "möchtest,"]),
    page(2.0, 3.2, ["ist", "das", "ganz", "einfach:"]),
    page(3.2, 4.4, ["Du", "musst", "keinen", "Lebenslauf."]),
  ]);
  const atPage = splitCueAt(plan, "cc-01", 8);
  assert.deepEqual(atPage.cues.map((c) => c.id), ["cc-01a", "cc-01b"]);
  assert.equal(atPage.cues[0].tokens.length, 8);
  assert.deepEqual(atPage.cues[0].pages, [0, 4]);
  assert.deepEqual(atPage.cues[1].pages, [0]);
  assert.equal(atPage.cues[1].start, 3.2);
  assert.equal(atPage.cues[0].end, 3.2);

  const midPage = splitCueAt(plan, "cc-01", 6);
  assert.deepEqual(midPage.cues[0].pages, [0, 4]);
  assert.deepEqual(midPage.cues[1].pages, [0, 2]);
  assert.equal(midPage.cues[1].treatment, "rail");
});

test("Satzende wird auf den Beginn des nächsten Satzes gekappt", () => {
  const plan = buildPlanFromPages("v", [page(1.0, 2.6, ["Du", "bist", "keine", "Zahl."]), page(2.5, 3.5, ["Das", "ist", "wichtig."])]);
  assert.equal(plan.cues[0].end, 2.5);
});
