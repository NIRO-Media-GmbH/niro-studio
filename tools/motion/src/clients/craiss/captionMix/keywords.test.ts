import { test } from "node:test";
import assert from "node:assert/strict";
import { shiftBlocked, shiftKeywords, validateKeywords, type Keyword } from "./keywords";

const kw = (over: Partial<Keyword>): Keyword => ({ text: "KINDERLEICHT", startSec: 5, endSec: 7, offsetY: 160, ...over });

test("gültige Liste hat keine Fehler", () => {
  assert.deepEqual(validateKeywords([kw({}), kw({ text: "NUR 10 MINUTEN", startSec: 7.3, endSec: 9 })], []), []);
});

test("zu langer Text", () => {
  const errs = validateKeywords([kw({ text: "X".repeat(33) })], []);
  assert.equal(errs.length, 1);
  assert.match(errs[0], /33 Zeichen/);
});

test("Dauer unter 1,5 s und über 3,5 s", () => {
  assert.match(validateKeywords([kw({ endSec: 6.4 })], [])[0], /Dauer 1\.40/);
  assert.match(validateKeywords([kw({ endSec: 8.6 })], [])[0], /Dauer 3\.60/);
});

test("Grenzwerte 1,5 s und 3,5 s sind erlaubt", () => {
  assert.deepEqual(validateKeywords([kw({ endSec: 6.5 })], []), []);
  assert.deepEqual(validateKeywords([kw({ endSec: 8.5 })], []), []);
});

test("Abstand unter 0,3 s zum vorigen Chip", () => {
  const errs = validateKeywords([kw({}), kw({ text: "B", startSec: 7.2, endSec: 9 })], []);
  assert.equal(errs.length, 1);
  assert.match(errs[0], /Abstand/);
});

test("Überlapp mit Sperrfenster", () => {
  const errs = validateKeywords([kw({})], [{ startSec: 6.5, durationSec: 2 }]);
  assert.equal(errs.length, 1);
  assert.match(errs[0], /Sperrfenster 6\.50–8\.50/);
});

test("Chip, der genau am Sperrfenster endet, ist erlaubt", () => {
  assert.deepEqual(validateKeywords([kw({})], [{ startSec: 7, durationSec: 1 }]), []);
});

test("shiftKeywords und shiftBlocked verschieben auf 2 Nachkommastellen", () => {
  assert.deepEqual(shiftKeywords([kw({ startSec: 12.86, endSec: 16.36 })], 1.36), [kw({ startSec: 14.22, endSec: 17.72 })]);
  assert.deepEqual(shiftBlocked([{ startSec: 7.84, durationSec: 3.76 }], 1.36), [{ startSec: 9.2, durationSec: 3.76 }]);
});
