import { test } from "node:test";
import assert from "node:assert/strict";
import { textBreite, umbrechen } from "./metriken";

test("Laufweite entspricht der fontTools-Messung", () => {
  // gemessen 16.09.: KFZ-MECHATRONIKER = 10,971 em im Schnitt 800
  assert.ok(Math.abs(textBreite("KFZ-MECHATRONIKER", "800", 100) - 1097.1) < 1);
  assert.ok(textBreite("AB", "800", 100, 0.1) > textBreite("AB", "800", 100));
});

test("Umbruch: passt → eine Zeile, sonst ausgewogene zwei Zeilen", () => {
  assert.deepEqual(umbrechen(["Bin", "seit", "2013"], "600", 56, 920), [[0, 1, 2]]);
  const worte = "Also wenn du Schrauber bist und Bock auf eine moderne Werkstatt".split(" ");
  const zeilen = umbrechen(worte, "600", 56, 920);
  assert.equal(zeilen.length, 2);
  const breite = (z: number[]) => textBreite(z.map((i) => worte[i]).join(" "), "600", 56);
  assert.ok(Math.abs(breite(zeilen[0]) - breite(zeilen[1])) < 260, "Zeilen etwa gleich lang");
  assert.ok(zeilen.every((z) => breite(z) <= 920));
});

test("Umbruch: nie nach Artikel/Präposition/Zahl, lieber nach Komma", () => {
  const text = (satz: string) => {
    const worte = satz.split(" ");
    return umbrechen(worte, "600", 56, 920).map((z) => z.map((i) => worte[i]).join(" "));
  };
  assert.deepEqual(text("Früher dauerte es halt eine Stunde bis anderthalb."), ["Früher dauerte es halt", "eine Stunde bis anderthalb."]);
  assert.deepEqual(text("Also es ist wirklich so, ich freue mich auf die Arbeit."), ["Also es ist wirklich so,", "ich freue mich auf die Arbeit."]);
  // Regel statt fester Trennung: Zeile 1 endet nie auf Bindewort oder Zahl
  assert.deepEqual(text("und Bock auf eine moderne Werkstatt hast,"), ["und Bock", "auf eine moderne Werkstatt hast,"]);
  for (const satz of ["Bin seit 2013 hier im Autohaus Rappold.", "wenn du mal zwei Stunden länger brauchst.", "Und auch mit der Geschäftsleitung,"]) {
    const [erste] = text(satz);
    const letztes = erste.split(" ").pop()!;
    assert.ok(!/^(der|die|das|den|dem|ein|eine|im|in|mit|zwei|\d+)$/i.test(letztes), `${satz} → „${erste}"`);
  }
});

test("Umbruch mit Schnitt je Wort: fette Wörter werden breiter gerechnet", () => {
  const worte = "Also wenn du Schrauber bist".split(" ");
  const normal = umbrechen(worte, "600", 62, 600);
  const fett = umbrechen(worte, ["600", "600", "600", "800", "600"], 62, 600);
  const breite = (z: number[][], s: ("600" | "800")[]) => z.map((l) => l.reduce((b, i) => b + textBreite(worte[i], s[i], 62), 0));
  assert.ok(fett.length >= normal.length);
  assert.ok(breite(fett, ["600", "600", "600", "800", "600"]).every((b) => b <= 600));
});
