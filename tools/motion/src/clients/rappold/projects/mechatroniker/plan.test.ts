import { test } from "node:test";
import assert from "node:assert/strict";
import { GRENZE_UNTEN, KINN_ABSTAND, TEXT_BREITE } from "../../lib";
import { EINSTELLUNGEN, FPS, SCHNITT_FRAMES, WORTE } from "./daten-generiert";
import { DAUER_FRAMES, GRAFIKEN } from "./grafik-plan";
import { grafikBreite, grafikHoehe, seitenBereich, seitenOben, seitenUnterkante, seitenZeilen } from "./layout";
import { ausblendFrames, seitenFenster, sichtbareSaetze, VORLAUF_SEK, wortDeckkraft } from "./timing";
import { SAETZE } from "./untertitel-plan";

const MIN_LUECKE = 16;
const STIRN_ABSTAND = 60; // Text über dem Gesicht: Unterkante so weit über der Stirn
const PLAN = sichtbareSaetze(SAETZE, WORTE, FPS);
const einstellungAm = (f: number) => EINSTELLUNGEN.find((x) => x.von <= f && f < x.bis);

type Block = { id: string; oben: number; unten: number; untertitel: boolean };
const KARTE = (() => {
  const karte = new Map<number, Block[]>();
  const add = (f: number, b: Block) => karte.set(f, [...(karte.get(f) ?? []), b]);
  for (const { satz, fenster } of PLAN) {
    seitenFenster(satz, WORTE, fenster, FPS).forEach((sf, k) => {
      const unten = seitenUnterkante(satz, k);
      const oben = seitenOben(seitenZeilen(satz, k, WORTE), unten);
      for (let f = sf.von; f < sf.bis; f++) add(f, { id: `${satz.id}/${k}`, oben, unten, untertitel: true });
    });
  }
  for (const g of GRAFIKEN) for (let f = g.von; f < g.bis; f++) add(f, { id: g.id, oben: g.y, unten: g.y + grafikHoehe(g), untertitel: false });
  return karte;
})();

test("jedes Wort gehört genau einem Satz, Text stimmt", () => {
  let erwartet = 0;
  for (const s of SAETZE) {
    assert.equal(s.von, erwartet, `${s.id} beginnt bei ${s.von}, erwartet ${erwartet}`);
    assert.equal(
      WORTE.slice(s.von, s.bis + 1)
        .map((w) => w.text)
        .join(" "),
      s.text,
      s.id,
    );
    erwartet = s.bis + 1;
  }
  assert.equal(erwartet, WORTE.length);
});

test("Seiten, Heroes und blaue Wörter sind gültig", () => {
  for (const s of SAETZE) {
    assert.equal(s.seiten[0], s.von, s.id);
    s.seiten.forEach((p, k) => k > 0 && assert.ok(p > s.seiten[k - 1] && p <= s.bis, s.id));
    const heroSeiten = new Set<number>();
    for (const h of s.hero ?? []) {
      const seite = s.seiten.filter((p) => p <= h.von).length - 1;
      const ende = (s.seiten[seite + 1] ?? s.bis + 1) - 1;
      assert.ok(h.von <= h.bis && h.bis <= ende, `${s.id}: Hero über Seitengrenze`);
      assert.ok(!heroSeiten.has(seite), `${s.id}: zwei Heroes auf Seite ${seite}`);
      heroSeiten.add(seite);
    }
    for (const i of s.blau ?? []) {
      assert.ok(i >= s.von && i <= s.bis, `${s.id}: blaues Wort ${i} außerhalb`);
      assert.ok(!(s.hero ?? []).some((h) => i >= h.von && i <= h.bis), `${s.id}: blaues Wort ${i} ist schon Hero`);
    }
    s.seiten.forEach((_, k) => {
      const z = seitenZeilen(s, k, WORTE);
      assert.ok(z.some((l) => l.hero) ? z.length <= 3 : z.length <= 2, `${s.id}/${k}: ${z.length} Zeilen`);
    });
  }
});

test("Gesichter frei: Text unter Kinn + 110 px oder über der Stirn", () => {
  for (const [f, bloecke] of KARTE) {
    if (f >= SCHNITT_FRAMES) continue;
    const e = einstellungAm(f)!;
    if (e.kinnY === null || e.gesichtOben === null) continue;
    for (const b of bloecke) {
      const frei: boolean = b.oben >= e.kinnY + KINN_ABSTAND || b.unten <= e.gesichtOben - STIRN_ABSTAND;
      assert.ok(frei, `${b.id} @${f} (${e.id} ${e.motiv}): Block ${Math.round(b.oben)}–${Math.round(b.unten)}, Gesicht ${e.gesichtOben}–${e.kinnY}`);
    }
  }
});

test("Grenzen: unten, Breite, Dauer", () => {
  for (const g of GRAFIKEN) {
    assert.ok(g.von < g.bis && g.bis <= DAUER_FRAMES, g.id);
    assert.ok(g.y + grafikHoehe(g) <= GRENZE_UNTEN, `${g.id} zu tief`);
    assert.ok(grafikBreite(g) <= TEXT_BREITE, `${g.id} zu breit: ${Math.round(grafikBreite(g))}`);
  }
  for (const s of SAETZE) s.seiten.forEach((_, k) => assert.ok(seitenUnterkante(s, k) <= GRENZE_UNTEN, s.id));
});

test("keine Überlappung gleichzeitig sichtbarer Blöcke", () => {
  for (const [f, bloecke] of KARTE) {
    for (let i = 0; i < bloecke.length; i++) {
      for (let j = i + 1; j < bloecke.length; j++) {
        const [a, b] = [bloecke[i], bloecke[j]];
        const frei: boolean = a.unten + MIN_LUECKE <= b.oben || b.unten + MIN_LUECKE <= a.oben;
        assert.ok(frei, `@${f}: ${a.id} [${Math.round(a.oben)}–${Math.round(a.unten)}] ↔ ${b.id} [${Math.round(b.oben)}–${Math.round(b.unten)}]`);
      }
    }
  }
});

test("Untertitel springen nicht: Unterkante wechselt nur auf einem Schnitt", () => {
  const schnitte = new Set(EINSTELLUNGEN.map((e) => e.von));
  let letzte: number | null = null;
  for (let f = 0; f < DAUER_FRAMES; f++) {
    const ut = (KARTE.get(f) ?? []).filter((b) => b.untertitel);
    if (ut.length === 0) continue;
    assert.equal(new Set(ut.map((b) => b.unten)).size, 1, `@${f}: zwei Untertitel-Lagen gleichzeitig`);
    const unten = ut[0].unten;
    if (letzte !== null && unten !== letzte) assert.ok(schnitte.has(f), `@${f} (${ut[0].id}): Lagewechsel ${letzte} → ${unten} ohne Schnitt`);
    letzte = unten;
  }
});

test("blaue Untertitel-Wörter nur auf Personen-Einstellungen (dunkle Shirts)", () => {
  for (const { satz, fenster } of PLAN) {
    seitenFenster(satz, WORTE, fenster, FPS).forEach((sf, k) => {
      const [a, b] = seitenBereich(satz, k);
      if (!(satz.blau ?? []).some((i) => i >= a && i < b)) return;
      for (let f = sf.von; f < Math.min(sf.bis, SCHNITT_FRAMES); f++) {
        const e = einstellungAm(f)!;
        assert.ok(e.typ !== "broll", `${satz.id}/${k} @${f}: blaues Wort über B-Roll (${e.id} ${e.motiv})`);
      }
    });
  }
});

test("(M/W/D) an jedem Berufstitel", () => {
  for (const g of GRAFIKEN.filter((x) => x.zeilen.some((z) => z.segmente.some((s) => s.text.includes("MECHATRONIKER"))))) {
    assert.ok(g.unterzeile?.some((s) => s.text === "(M/W/D)"), g.id);
  }
});

test("ausgeblendete Sätze nennen ihre Grafik", () => {
  for (const s of SAETZE.filter((x) => x.aus)) assert.ok(GRAFIKEN.some((g) => g.id === s.aus), `${s.id}: ${s.aus}`);
});

test("kein Flackern: erstes Wort jeder Seite steht ab dem ersten Seiten-Frame voll, nie vor dem Wortanfang", () => {
  for (const { satz, fenster } of PLAN) {
    seitenFenster(satz, WORTE, fenster, FPS).forEach((sf, k) => {
      const [a] = seitenBereich(satz, k);
      assert.ok(sf.von >= Math.round((WORTE[a].start - VORLAUF_SEK) * FPS), `${satz.id}/${k}: Seite vor ihrem ersten Wort`);
      for (let f = sf.von; f < sf.bis; f++) {
        assert.equal(wortDeckkraft(WORTE[a].start, true, f, FPS), 1, `${satz.id}/${k} @${f}: erstes Wort nicht voll sichtbar`);
      }
    });
  }
});

test("nie während laufender Sprache ausblenden", () => {
  for (const { satz, fenster } of PLAN) {
    const n = ausblendFrames(satz, WORTE, fenster, FPS);
    if (n === 0) continue; // harter Wechsel
    const ausblendStart = (fenster.bis - n) / FPS;
    assert.ok(ausblendStart >= WORTE[satz.bis].end - 1e-6, `${satz.id}: Ausblenden ab ${ausblendStart.toFixed(2)} s, letztes Wort endet ${WORTE[satz.bis].end} s`);
  }
});
