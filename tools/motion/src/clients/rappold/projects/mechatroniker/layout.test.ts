import { test } from "node:test";
import assert from "node:assert/strict";
import {
  anzeigeText,
  grafikHoehe,
  KICKER_ABSTAND,
  KICKER_PX,
  LINIE_ABSTAND,
  LINIE_H,
  seitenOben,
  seitenUnterkante,
  seitenZeilen,
  TITEL_ZEILENHOEHE,
  UT_BREITE,
  UT_UNTERKANTE,
  wortSchnitt,
} from "./layout";
import { textBreite } from "../../metriken";
import type { Satz } from "./untertitel-plan";
import type { Grafik } from "./grafik-plan";

const W = "Man hat viel Platz, man kann sich ausbreiten,".split(" ").map((text, i) => ({ text, start: i, end: i + 0.5 }));

test("Anzeige: Hero versal ohne Komma, Übergabe mit großem Anfang", () => {
  const s: Satz = { id: "x", text: "", von: 0, bis: 6, seiten: [0], gross: true };
  assert.equal(anzeigeText(W, s, 0, false), "Man");
  assert.equal(anzeigeText(W, s, 3, true), "PLATZ");
  assert.equal(anzeigeText(W, { ...s, von: 1 }, 1, false), "Hat");
});

test("Seite mit Hero in der Mitte: Grundzeile, Hero, Grundzeile", () => {
  const s: Satz = { id: "x", text: "", von: 0, bis: 6, seiten: [0], hero: [{ von: 2, bis: 3, farbe: "weiss" }] };
  const z = seitenZeilen(s, 0, W);
  assert.deepEqual(
    z.map((l) => l.hero),
    [null, "weiss", null],
  );
  assert.deepEqual(z[1].worte, [2, 3]);
  assert.equal(z[1].px, 150);
  assert.ok(seitenOben(z, 1440) < 1440 - 150);
});

test("Unterkante je Seite: Standard oder Override, fest über die Seite", () => {
  const s: Satz = { id: "x", text: "", von: 0, bis: 6, seiten: [0, 4], unterkanteJeSeite: { 1: 1083 } };
  assert.equal(seitenUnterkante(s, 0), UT_UNTERKANTE);
  assert.equal(seitenUnterkante(s, 1), 1083);
});

test("Blaue Wörter: fett gerechnet, Zeilen passen trotzdem in die Breite", () => {
  const s: Satz = { id: "x", text: "", von: 0, bis: 7, seiten: [0], blau: [3] };
  assert.equal(wortSchnitt(s, 3), "800");
  assert.equal(wortSchnitt(s, 2), "600");
  for (const z of seitenZeilen(s, 0, W)) {
    const b = z.worte.reduce((sum, i, n) => sum + textBreite(W[i].text, wortSchnitt(s, i), z.px) + (n ? textBreite(" ", "600", z.px) : 0), 0);
    assert.ok(b <= UT_BREITE, `Zeile ${Math.round(b)} px`);
  }
});

test("Grafik: Höhe aus Bausteinen, ohne Linie kürzer", () => {
  const g: Grafik = { id: "g", von: 0, bis: 100, y: 850, ausrichtung: "links", kicker: "K", zeilen: [{ segmente: [{ text: "T", farbe: "weiss" }], px: 100 }] };
  const kicker = KICKER_PX * 1.2 + KICKER_ABSTAND;
  assert.equal(Math.round(grafikHoehe(g)), Math.round(kicker + LINIE_H + LINIE_ABSTAND + 100 * TITEL_ZEILENHOEHE));
  assert.equal(Math.round(grafikHoehe({ ...g, ohneLinie: true })), Math.round(kicker + 100 * TITEL_ZEILENHOEHE));
});
