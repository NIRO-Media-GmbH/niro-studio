// Laufweiten Open Sans v29 (em) aus den Website-WOFF-Dateien (fontTools, 16.09.2026).
// Grundlage für Zeilenumbruch und Maß-Prüfungen ohne Browser.
import LAUFWEITEN from "./laufweiten.json";

export type Schnitt = "600" | "800";
const ERSATZ_EM = 0.62;
const tabelle = LAUFWEITEN as Record<Schnitt, Record<string, number>>;

export const textBreite = (text: string, schnitt: Schnitt, px: number, sperrungEm = 0): number => {
  let em = 0;
  let n = 0;
  for (const c of text) {
    em += tabelle[schnitt][c] ?? ERSATZ_EM;
    n++;
  }
  return (em + sperrungEm * n) * px;
};

// Zeilenbreite = Wörter (je eigener Schnitt) + Leerzeichen im Grundschnitt
const zeilenBreite = (worte: string[], von: number, bis: number, schnitte: Schnitt[], px: number, sperrungEm: number) => {
  let b = 0;
  for (let i = von; i < bis; i++) b += textBreite(worte[i], schnitte[i], px, sperrungEm) + (i > von ? textBreite(" ", schnitte[von], px, sperrungEm) : 0);
  return b;
};

// Kein Zeilenende nach Artikel, Präposition, Konjunktion oder Zahl (sonst „eine / Stunde")
const KLEBT_AN_NAECHSTEM = new Set(
  "der die das den dem des ein eine einer einen einem kein keine im in am an auf aus mit zu zur zum beim vom von bei für bis und oder dass weil wenn zwei drei vier fünf".split(" "),
);
const STRAFE_PX = 400;
const KOMMA_BONUS_PX = 150;

// Gieriger Umbruch; ergibt das genau zwei Zeilen, wird der Bruch nach Breite,
// Wortbindung und Satzzeichen neu gesetzt.
export const umbrechen = (worte: string[], schnitt: Schnitt | Schnitt[], px: number, maxBreite: number, sperrungEm = 0): number[][] => {
  const schnitte = Array.isArray(schnitt) ? schnitt : worte.map(() => schnitt);
  const starts: number[] = [0];
  for (let i = 1; i < worte.length; i++) {
    if (zeilenBreite(worte, starts[starts.length - 1], i + 1, schnitte, px, sperrungEm) > maxBreite) starts.push(i);
  }
  if (starts.length === 2) {
    let besterBruch = starts[1];
    let besteKosten = Infinity;
    for (let k = 1; k < worte.length; k++) {
      const a = zeilenBreite(worte, 0, k, schnitte, px, sperrungEm);
      const b = zeilenBreite(worte, k, worte.length, schnitte, px, sperrungEm);
      if (a > maxBreite || b > maxBreite) continue;
      const letztes = worte[k - 1];
      // Adjektiv vor großgeschriebenem Nomen („moderne / Werkstatt") bleibt ebenfalls zusammen
      const adjektiv = /^[a-zäöüß]+(e|en|er|es|em)$/.test(letztes) && /^[A-ZÄÖÜ]/.test(worte[k]);
      const klebt = KLEBT_AN_NAECHSTEM.has(letztes.toLowerCase()) || /^\d+$/.test(letztes) || adjektiv;
      const kosten = Math.max(a, b) + (klebt ? STRAFE_PX : 0) - (/[,;:.]["“]?$/.test(letztes) ? KOMMA_BONUS_PX : 0);
      if (kosten < besteKosten) {
        besteKosten = kosten;
        besterBruch = k;
      }
    }
    starts[1] = besterBruch;
  }
  return starts.map((s, k) => Array.from({ length: (starts[k + 1] ?? worte.length) - s }, (_, j) => s + j));
};
