import { test } from "node:test";
import assert from "node:assert/strict";
import { resolveBlock, wordboxLines, BASE_W, MARGIN_X, SIDE_WIDTH, ZONE_DEFAULT_TOP } from "./layout";

test("Wort-Kasten-Zeilen: Wortbreiten-Schätzung wie gerendert (Kontaktbögen 11.09.)", () => {
  assert.equal(wordboxLines(["Mich", "auf", "dich."]), 1);
  assert.equal(wordboxLines(["Ich", "freue", "mich", "auf", "dich."]), 2);
  assert.equal(wordboxLines(["Wenn", "bei", "diesem", "Telefonat"]), 3);
});

test("top: volle Breite, zentriert, Standardhöhe", () => {
  assert.deepEqual(resolveBlock("top"), { top: ZONE_DEFAULT_TOP.top, left: MARGIN_X, width: BASE_W - 2 * MARGIN_X, align: "center" });
});

test("side-l links bündig, side-r rechts bündig", () => {
  assert.deepEqual(resolveBlock("side-l"), { top: 700, left: 54, width: SIDE_WIDTH, align: "left" });
  assert.deepEqual(resolveBlock("side-r"), { top: 700, left: 1080 - 54 - SIDE_WIDTH, width: SIDE_WIDTH, align: "right" });
});

test("y überschreibt die Standardhöhe", () => {
  assert.equal(resolveBlock("chest", 1234).top, 1234);
  assert.equal(resolveBlock("chest").top, 1150);
});
