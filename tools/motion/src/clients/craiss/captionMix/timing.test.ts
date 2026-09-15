import { test } from "node:test";
import assert from "node:assert/strict";
import { activeTokenIndex, cueWindow, currentPageIndex, pageTokenRange, revealProgress } from "./timing";

const FPS = 25;
const cue = { start: 4.0, end: 6.0, tokens: [{ end: 4.5 }, { end: 5.4 }] };

test("Satz komplett im freien Fenster → sichtbar, am Fensterende gekappt", () => {
  assert.deepEqual(cueWindow(cue, [{ from: 90, to: 145 }], FPS), { from: 100, to: 145 });
});

test("Satzanfang oder letztes Wort unter einer Grafik → Satz entfällt", () => {
  assert.equal(cueWindow(cue, [{ from: 105, to: 200 }], FPS), null);
  assert.equal(cueWindow(cue, [{ from: 90, to: 130 }], FPS), null);
});

test("Wort-Einblendung: 0 vor Wortanfang−0,08 s, 1 nach 5 Frames", () => {
  assert.equal(revealProgress(2.0, 47, FPS), 0);
  assert.equal(revealProgress(2.0, 48, FPS), 0);
  assert.equal(revealProgress(2.0, 53, FPS), 1);
});

test("Seitenwechsel wartet, bis das letzte Wort der Seite 0,4 s stand", () => {
  const toks = [{ start: 1.0 }, { start: 1.5 }, { start: 1.6 }, { start: 2.6 }];
  assert.equal(currentPageIndex([0, 2], toks, 1.7), 0);
  assert.equal(currentPageIndex([0, 2], toks, 1.83), 1);
});

test("aktives Wort und aktuelle Seite", () => {
  const toks = [{ start: 1.0 }, { start: 1.5 }, { start: 2.0 }, { start: 2.6 }];
  assert.equal(activeTokenIndex(toks, 0.9), -1);
  assert.equal(activeTokenIndex(toks, 1.49), 1);
  assert.equal(currentPageIndex([0, 2], toks, 1.9), 0);
  assert.equal(currentPageIndex([0, 2], toks, 1.93), 1);
  assert.deepEqual(pageTokenRange([0, 2], 4, 0), [0, 2]);
  assert.deepEqual(pageTokenRange([0, 2], 4, 1), [2, 4]);
});
