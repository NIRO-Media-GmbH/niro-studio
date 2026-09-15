// ============================================================
// Setzer — „Unterschied Fleischkäse vs. Leberkäse"
// Untertitel-Daten, 24 fps, t = 0 ist der erste Frame des Schnitts.
//
// Grundlage: der gelieferte SRT-Export (Zeitbasis 01:00:00 = 0,000 s).
// Die ASR darin ist stellenweise falsch verstanden; hier stehen die
// korrigierten Wörter auf den Original-Zeiten:
//   Lebercase / Levo Case                -> Leberkäs
//   Fleischcase                          -> Fleischkäs
//   „einen Bahnverlässt"                 -> „Bayern verlässt"
//   „sieht Sarah ganz anders aus"        -> „sieht die Sache ganz anders aus"
//   Fleischerleitsetzen                  -> Fleischerleitsätzen (O-Ton, s. u.)
//   „24 Sieben Märkten"                  -> steht NICHT im Untertitel
//
// Zwei bewusste Eingriffe (Projektregeln aus dem Schnittplan):
//  1. Nico sagt „24/7 Märkte", die Website führt „24/7 Shops". Der O-Ton
//     bleibt unangetastet, aber der geschriebene Text folgt der Website —
//     deshalb trägt der Keyword-Kasten „24/7 SHOPS" und der Untertitel
//     lässt die Stelle aus (David-Regel 2026-08-01).
//  2. Was ein Kasten/Stempel inhaltlich schon sagt, fliegt aus dem
//     Untertitel — und zwar immer als ganze Sinneinheit, nie als Satzteil
//     (David-Regel 2026-08-12). Betroffen: die beiden Produktnamen im Hook,
//     das Prädikat „ist natürlich keine Leber drin", der Satz „Wir haben
//     natürlich keine Leber drin" (trägt der Zähler), das Schlusswort
//     „Fleischkäse" und die CTA-Antworten.
//
// „Fleischerleitsätzen" bleibt wörtlich stehen, weil es O-Ton ist. Fachlich
// heißt die Quelle „Leitsätze für Fleisch und Fleischerzeugnisse" — deshalb
// wird der Begriff auch nicht als Grafik verstärkt.
//
// Layout-Regel: **maximal zwei Zeilen pro Seite**. Alles darüber wird zur
// Textwand und deckt im Hochformat den halben Oberkörper zu.
// ============================================================

export interface CaptionWord {
  text: string;
  startSec: number;
  endSec: number;
  /** auf rotem Kasten hervorheben — höchstens einmal pro Seite */
  accent?: boolean;
}

export interface CaptionPage {
  startSec: number;
  endSec: number;
  lines: CaptionWord[][];
}

const w = (text: string, startSec: number, endSec: number, accent = false): CaptionWord => ({
  text,
  startSec,
  endSec,
  accent,
});

// --- Untertitelseiten ---

export const PAGES: CaptionPage[] = [
  // 1 — Hook. „Leberkäse oder Fleischkäse" tragen die beiden Chips.
  {
    startSec: 0.099,
    endSec: 2.9,
    lines: [
      [w("WAS IST EIGENTLICH", 0.099, 0.533)],
      [w("DER", 0.533, 0.699), w("UNTERSCHIED?", 0.699, 1.3, true)],
    ],
  },

  // 2 — Antwort, erste Hälfte. Das Prädikat übernimmt der Stempel.
  {
    startSec: 3.233,
    endSec: 5.8,
    lines: [
      [w("IM ORIGINAL", 3.233, 3.9)],
      [w("BAYERISCHEN", 3.9, 4.633), w("LEBERKÄS", 4.633, 5.199, true)],
    ],
  },

  // 3a — Twist, erste Hälfte.
  {
    startSec: 6.8,
    endSec: 8.11,
    lines: [
      [w("SOBALD MAN", 6.8, 7.333)],
      [w("BAYERN", 7.333, 7.75, true), w("VERLÄSST,", 7.75, 8.133)],
    ],
  },

  // 3b — Twist, zweite Hälfte.
  {
    startSec: 8.133,
    endSec: 9.55,
    lines: [
      [w("SIEHT DIE SACHE", 8.133, 8.533)],
      [w("GANZ ANDERS AUS.", 8.533, 9.266)],
    ],
  },

  // 4a — Die Quelle.
  {
    startSec: 9.666,
    endSec: 11.21,
    lines: [
      [w("LAUT DEN DEUTSCHEN", 9.666, 10.0)],
      [w("FLEISCHERLEITSÄTZEN", 10.266, 11.233)],
    ],
  },

  // 4b — Der Geltungsbereich.
  {
    startSec: 11.233,
    endSec: 12.34,
    lines: [
      [w("MUSS", 11.233, 11.366), w("AUSSERHALB", 11.366, 11.933, true)],
      [w("VON BAYERN", 11.933, 12.366)],
    ],
  },

  // 4c — Die Regel.
  {
    startSec: 12.366,
    endSec: 14.35,
    lines: [
      [w("IN LEBERKÄSE NATÜRLICH", 12.366, 13.166)],
      [w("LEBER DRIN SEIN.", 13.5, 14.4, true)],
    ],
  },

  // 5 — Auflösung. „Fleischkäse" trägt die große Type.
  {
    startSec: 14.4,
    endSec: 15.4,
    lines: [[w("DESWEGEN HEISST", 14.4, 14.666)], [w("ER BEI UNS", 15.033, 15.433)]],
  },

  // 6 — „Wir haben natürlich keine Leber drin" läuft komplett über den
  //     0-%-Zähler. Kein Untertitel, sonst steht dasselbe zweimal im Bild.

  // 7a — Region, erste Hälfte.
  {
    startSec: 18.333,
    endSec: 19.51,
    lines: [[w("BEI UNS IST NUR", 18.333, 19.0)], [w("DAS BESTE", 19.133, 19.533)]],
  },

  // 7b — Region, zweite Hälfte. Kein Akzent auf REGION —
  //      das Wort trägt schon das Herkunfts-Badge.
  {
    startSec: 19.533,
    endSec: 21.1,
    lines: [
      [w("FLEISCH", 19.533, 19.966, true)],
      [w("AUS DER REGION DRIN.", 19.966, 20.833)],
    ],
  },

  // 8a — SB-Ware. Die Stelle „in den 24/7 Märkten" trägt der Kasten.
  {
    startSec: 21.366,
    endSec: 22.86,
    lines: [
      [w("IHR KÖNNT IHN AUCH", 21.366, 21.933)],
      [w("SO", 21.933, 22.133), w("VERPACKT", 22.133, 22.633, true), w("BEI UNS", 22.633, 22.9)],
    ],
  },

  // 8b — Satzende nach dem Kasten.
  {
    startSec: 24.366,
    endSec: 24.95,
    lines: [[w("... KAUFEN.", 24.366, 24.733)]],
  },

  // 9 — CTA-Frage. Die Antworten tragen die Chips, den Aufruf die Sprechblase.
  {
    startSec: 29.0,
    endSec: 29.82,
    lines: [[w("WAS IST ES", 29.0, 29.3)], [w("FÜR EUCH?", 29.4, 29.666, true)]],
  },
];

// --- Animations-Beats (Sekunden) ---
// Jeder Beat ist eine eigene Bewegungsart, damit sich nichts wiederholt.

export const BEATS = {
  /** 1 · Zwei Chips fahren gegeneinander, VS-Plakette springt dazwischen */
  vsLeberkaes: { start: 1.28, end: 3.3 },
  vsFleischkaes: { start: 2.02, end: 3.3 },
  vsBadge: { start: 2.42, end: 3.3 },

  /** 2 · Metzger-Stempel schlägt auf */
  stempel: { start: 5.85, end: 7.05 },

  /** 3 · Grenzlinie wischt durch, Pfeil zieht raus (rein grafisch) */
  grenze: { start: 7.2, end: 9.5 },

  /** 4 · rote Linie zieht sich unter das Band */
  regelLinie: { start: 11.3, end: 14.4 },

  /** 5 · FLEISCHKÄSE landet, roter Balken wischt dahinter */
  auflösung: { start: 15.35, end: 16.75 },

  /** 6 · Zähler läuft von 100 auf 0 */
  zaehler: { start: 16.55, end: 18.35 },

  /** 7 · Herkunfts-Badge fährt von links ein */
  hohenlohe: { start: 19.4, end: 21.15 },

  /** 8 · Keyword-Kasten mit Uhr */
  shops: { start: 22.75, end: 25.0 },

  /** 9 · Hero: Laib wird gezeichnet, angeschnitten, Logo darunter */
  hero: { start: 25.1, end: 28.95 },

  /** 10 · Antwort-Chips + Kommentar-Blase */
  pollChips: { start: 29.75, end: 32.2 },
  pollBubble: { start: 30.6, end: 32.2 },
} as const;

/** Laufzeit des Schnitts. Letztes Wort endet bei 31,966 s. */
export const DURATION_SEC = 32.2;
