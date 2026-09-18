import { test } from "node:test";
import assert from "node:assert/strict";
import { validateKeywords } from "./keywords";
import * as v01 from "../projects/erster-tag/schlagwoerter";
import * as v02 from "../projects/arbeitsalltag/schlagwoerter";
import * as v03 from "../projects/viele-jahre/schlagwoerter";
import * as v04 from "../projects/funnel/schlagwoerter";
import * as v05 from "../projects/testimonial/schlagwoerter";

const VIDEOS = { "01": v01, "02": v02, "03": v03, "04": v04, "05": v05 };

for (const [id, v] of Object.entries(VIDEOS)) {
  test(`Schlagwörter ${id} halten die Regeln`, () => {
    assert.deepEqual(validateKeywords(v.KEYWORDS, v.BLOCKED), []);
  });
}

// 03: 5 statt 6 seit 18.09.2026 („FRÜHER SELBST KEIN DEUTSCH" auf Kundenwunsch raus).
test("Anzahl Chips wie freigegeben (3/6/5/4/3)", () => {
  assert.deepEqual(
    Object.values(VIDEOS).map((v) => v.KEYWORDS.length),
    [3, 6, 5, 4, 3],
  );
});
