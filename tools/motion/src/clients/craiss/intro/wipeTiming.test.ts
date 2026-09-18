import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { greetingIndexAt, introEndFrame, introLayoutSchema, wipeOffset, type Wipe } from "./wipeTiming";

const HU: Wipe = { country: "HU", cutFrame: 30, inFrames: 4, outFrames: 4 };

test("Einlauf beginnt inFrames vor dem Halten, davor unsichtbar", () => {
  assert.equal(wipeOffset(24, HU), null);
  assert.ok(wipeOffset(25, HU)! > 0.9);
});

test("hält auf cutFrame − 1 und cutFrame voll deckend", () => {
  assert.equal(wipeOffset(29, HU), 0);
  assert.equal(wipeOffset(30, HU), 0);
});

test("Einlauf und Auslauf fallen monoton", () => {
  const ein = [25, 26, 27, 28].map((f) => wipeOffset(f, HU)!);
  ein.forEach((v, i) => {
    assert.ok(v > 0 && v < 1);
    if (i) assert.ok(v < ein[i - 1]);
  });
  const aus = [31, 32, 33, 34].map((f) => wipeOffset(f, HU)!);
  aus.forEach((v, i) => {
    assert.ok(v < 0 && v > -1);
    if (i) assert.ok(v < aus[i - 1]);
  });
  assert.equal(wipeOffset(35, HU), null);
});

test("erster Wischer ohne Einlauf deckt Frame 0", () => {
  const PL: Wipe = { country: "PL", cutFrame: 0, inFrames: 0, outFrames: 4 };
  assert.equal(wipeOffset(0, PL), 0);
  assert.ok(wipeOffset(1, PL)! < 0);
  assert.equal(wipeOffset(5, PL), null);
});

test("roter Wischer: 6 Frames Einlauf, 2 Frames Auslauf", () => {
  const R: Wipe = { country: "CRAISS", cutFrame: 100, inFrames: 6, outFrames: 2 };
  assert.equal(wipeOffset(92, R), null);
  assert.ok(wipeOffset(93, R)! > 0);
  assert.ok(wipeOffset(102, R)! < 0);
  assert.equal(wipeOffset(103, R), null);
});

test("greetingIndexAt", () => {
  const g = [{ fromFrame: 0 }, { fromFrame: 29 }, { fromFrame: 55 }];
  assert.equal(greetingIndexAt(0, g), 0);
  assert.equal(greetingIndexAt(28, g), 0);
  assert.equal(greetingIndexAt(29, g), 1);
  assert.equal(greetingIndexAt(80, g), 2);
});

test("intro-layout.json passt zum Schema und ist in sich stimmig", () => {
  const datei = path.join(__dirname, "../projects/viele-jahre/intro-layout.json");
  const L = introLayoutSchema.parse(JSON.parse(fs.readFileSync(datei, "utf8")));
  assert.equal(L.wipes[0].cutFrame, 0);
  assert.equal(L.wipes[4].cutFrame, L.montageFrames);
  L.greetings.forEach((g, i) => assert.equal(g.fromFrame, i === 0 ? 0 : L.wipes[i].cutFrame - 1));
  assert.equal(L.helloToFrame, L.montageFrames - 1);
  assert.equal(L.titleChip.toFrame, 131 + L.shiftFrames);
  assert.equal(introEndFrame(L), L.montageFrames + L.wipes[4].outFrames + 1);
});
