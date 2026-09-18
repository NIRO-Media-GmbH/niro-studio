import { test } from "node:test";
import assert from "node:assert/strict";
import { ausblendFrames, einblendung, satzFenster, seitenFenster, seitenIndex } from "./timing";
import type { Satz } from "./untertitel-plan";

const W = [
  { text: "Eins", start: 1.0, end: 1.2 },
  { text: "zwei", start: 1.5, end: 1.7 },
  { text: "drei.", start: 1.6, end: 2.0 },
  { text: "Vier.", start: 2.6, end: 3.0 },
];
const satz: Satz = { id: "a", text: "Eins zwei drei.", von: 0, bis: 2, seiten: [0, 2] };
const naechster: Satz = { id: "b", text: "Vier.", von: 3, bis: 3, seiten: [3] };

test("Satzfenster: Vorlauf 0,08 s, Nachlauf 0,6 s, gekappt vor dem nächsten Satz", () => {
  assert.deepEqual(satzFenster(satz, W, null, 25), { von: 23, bis: 65 });
  assert.deepEqual(satzFenster(satz, W, naechster, 25), { von: 23, bis: 62 });
  assert.deepEqual(satzFenster({ ...satz, nachlaufSek: 0.1 }, W, null, 25), { von: 23, bis: 53 });
});

test("Seitenwechsel wartet, bis das letzte Wort der Seite 0,4 s stand", () => {
  assert.equal(seitenIndex(satz, W, 1.7), 0);
  assert.equal(seitenIndex(satz, W, 1.83), 1);
  assert.deepEqual(seitenFenster(satz, W, { von: 23, bis: 65 }, 25), [
    { von: 23, bis: 46 },
    { von: 46, bis: 65 },
  ]);
});

test("Wort-Einblendung: nie vor Wortanfang − 0,08 s, ab dort sofort sichtbar, voll nach 5 Frames", () => {
  assert.equal(einblendung(2.0, 47, 25), 0);
  assert.equal(einblendung(2.0, 48, 25), 0.2);
  assert.equal(einblendung(2.0, 52, 25), 1);
});

test("Seitenwechsel-Override: fester Zeitpunkt, aber nie vor Wortanfang − 0,08 s", () => {
  const mitOverride: Satz = { ...satz, wechselSek: { 1: 1.56 } };
  assert.equal(seitenIndex(mitOverride, W, 1.55), 0);
  assert.equal(seitenIndex(mitOverride, W, 1.56), 1);
  const zuFrueh: Satz = { ...satz, wechselSek: { 1: 1.0 } };
  assert.equal(seitenIndex(zuFrueh, W, 1.3), 0, "Override vor Wortanfang − Vorlauf wird angehoben");
});

test("Ausblenden nur nach dem letzten Wort, sonst harter Wechsel", () => {
  // letztes Wort endet 2,0 s = Frame 50
  assert.equal(ausblendFrames(satz, W, { von: 23, bis: 65 }, 25), 5);
  assert.equal(ausblendFrames(satz, W, { von: 23, bis: 53 }, 25), 3);
  assert.equal(ausblendFrames(satz, W, { von: 23, bis: 49 }, 25), 0);
});
