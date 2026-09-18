// ============================================================
// Rappold Video 2 — Layout (Zeilenbau Untertitel, Maße der Grafiken)
// Maße aus den Open-Sans-Laufweiten (metriken.ts) — Renderer und Prüfungen
// nutzen dieselben Werte.
// ============================================================
import { TEXT_BREITE } from "../../lib";
import { textBreite, umbrechen, type Schnitt } from "../../metriken";
import type { Wort } from "./daten-generiert";
import type { Grafik } from "./grafik-plan";
import type { HeroFarbe, Satz } from "./untertitel-plan";

export const UT_PX = 62;
export const UT_ZEILENHOEHE = 1.18;
export const UT_BREITE = 920;
export const UT_UNTERKANTE = 1460;
export const HERO_PX_MAX = 150;
export const HERO_ZEILENHOEHE = 1.08;
export const HERO_SPERRUNG = -0.02;
export const TITEL_ZEILENHOEHE = 1.08;
export const KICKER_PX = 34;
export const KICKER_SPERRUNG = 0.18;
export const KICKER_ABSTAND = 12;
export const LINIE_W = 64;
export const LINIE_H = 8;
export const LINIE_ABSTAND = 16;
export const UNTERZEILE_PX = 44;
export const UNTERZEILE_SPERRUNG = 0.12;
export const UNTERZEILE_ABSTAND = 8;

export type Zeile = { worte: number[]; hero: HeroFarbe | null; px: number };

const bereich = (von: number, bisExkl: number) => Array.from({ length: Math.max(0, bisExkl - von) }, (_, k) => von + k);

export const seitenBereich = (satz: Satz, seite: number): [number, number] => [satz.seiten[seite], satz.seiten[seite + 1] ?? satz.bis + 1];

export const anzeigeText = (worte: Wort[], satz: Satz, i: number, hero: boolean): string => {
  let t = worte[i].text;
  if (satz.gross && i === satz.von) t = t.charAt(0).toUpperCase() + t.slice(1);
  return hero ? t.replace(/[,:;]+$/, "").toUpperCase() : t;
};

// Blau hervorgehobene Grundzeilen-Wörter stehen im Schnitt 800 (bessere Lesbarkeit der Farbe)
export const wortSchnitt = (satz: Satz, i: number): Schnitt => (satz.blau?.includes(i) ? "800" : "600");

export const seitenZeilen = (satz: Satz, seite: number, worte: Wort[]): Zeile[] => {
  const [a, b] = seitenBereich(satz, seite);
  const hero = satz.hero?.find((h) => h.von >= a && h.bis < b);
  const teile: { idx: number[]; hero: HeroFarbe | null }[] = hero
    ? [
        { idx: bereich(a, hero.von), hero: null },
        { idx: bereich(hero.von, hero.bis + 1), hero: hero.farbe },
        { idx: bereich(hero.bis + 1, b), hero: null },
      ].filter((t) => t.idx.length > 0)
    : [{ idx: bereich(a, b), hero: null }];
  const zeilen: Zeile[] = [];
  for (const t of teile) {
    if (t.hero) {
      const text = t.idx.map((i) => anzeigeText(worte, satz, i, true)).join(" ");
      const px = Math.min(HERO_PX_MAX, Math.floor(TEXT_BREITE / textBreite(text, "800", 1, HERO_SPERRUNG)));
      zeilen.push({ worte: t.idx, hero: t.hero, px });
    } else {
      const texte = t.idx.map((i) => anzeigeText(worte, satz, i, false));
      const schnitte = t.idx.map((i) => wortSchnitt(satz, i));
      for (const z of umbrechen(texte, schnitte, UT_PX, UT_BREITE)) zeilen.push({ worte: z.map((k) => t.idx[k]), hero: null, px: UT_PX });
    }
  }
  return zeilen;
};

export const zeilenHoehe = (z: Zeile): number => z.px * (z.hero ? HERO_ZEILENHOEHE : UT_ZEILENHOEHE);
export const seitenHoehe = (zeilen: Zeile[]): number => zeilen.reduce((s, z) => s + zeilenHoehe(z), 0);
// Lage steht je Seite fest — sichtbarer Text bewegt sich nie
export const seitenUnterkante = (satz: Satz, seite: number): number => satz.unterkanteJeSeite?.[seite] ?? UT_UNTERKANTE;
export const seitenOben = (zeilen: Zeile[], unterkante: number): number => unterkante - seitenHoehe(zeilen);

export const grafikHoehe = (g: Grafik): number =>
  (g.kicker ? KICKER_PX * 1.2 + KICKER_ABSTAND : 0) +
  (g.ohneLinie ? 0 : LINIE_H + LINIE_ABSTAND) +
  g.zeilen.reduce((s, z) => s + z.px * TITEL_ZEILENHOEHE, 0) +
  (g.unterzeile ? UNTERZEILE_ABSTAND + UNTERZEILE_PX * 1.25 : 0);

export const grafikBreite = (g: Grafik): number =>
  Math.max(
    ...g.zeilen.map((z) => textBreite(z.segmente.map((s) => s.text).join(""), "800", z.px, HERO_SPERRUNG)),
    g.kicker ? textBreite(g.kicker, "600", KICKER_PX, KICKER_SPERRUNG) : 0,
    g.unterzeile ? textBreite(g.unterzeile.map((s) => s.text).join(""), "600", UNTERZEILE_PX, UNTERZEILE_SPERRUNG) : 0,
  );
