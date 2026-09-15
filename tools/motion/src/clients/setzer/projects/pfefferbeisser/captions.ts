// ============================================================
// Setzer — Video 6 „Pfefferbeisser" (Prozess-Reel)
// Untertitel-Daten (Sekunden; Ausspielung 30 fps), t = 0 ist der erste Frame des Schnitts.
//
// Grundlage: „Subtitle 1 Video 6 Pfefferbeiser.srt" (Zeitbasis
// 01:00:00 = 0,000 s). ASR-Korrekturen auf Original-Zeiten:
//   „Pfefferbeiser"        -> Pfefferbeißer (im Untertitel PFEFFERBEISSER)
//   „Seitendarm 2022"      -> Saitendarm 20/22 (Schafsaitling-Kaliber —
//                             GEGEN DEN TON PRÜFEN, s. Protokoll)
//   „Mischautomatenwolf"   -> Mischautomaten-Wolf (vermutl. Mischwolf —
//                             ebenfalls gegen den Ton prüfen)
//   „24-7 Stores"          -> steht NICHT im Untertitel; der Kasten trägt
//                             das offizielle 24/7-Shop-Logo (Website-Wording)
//
// Dopplungs-Regel (David 2026-08-12), ganze Sinneinheiten:
//   - „aus der Schulter oder aus dem Schlegel für unsere Pfefferbeißer"
//     tragen die drei Chips im Intro — kein Untertitel 2,3–5,4 s.
//   - „Immer trocknen rauchen trocknen rauchen" trägt der Wechsel-Beat —
//     kein Untertitel 56,5–59,3 s.
//   - „oder in unseren 24/7 Stores" trägt der Shop-Logo-Kasten.
//
// Layout: max. 2 Zeilen pro Seite, Zeilen erscheinen als Ganzes,
// höchstens ein Akzentwort pro Seite. `sizeScale` verkleinert einzelne
// Seiten mit unteilbar langen Wörtern (Fleischerei-Fachgeschäften).
// ============================================================

export interface CaptionWord {
  text: string;
  startSec: number;
  endSec: number;
  accent?: boolean;
}

export interface CaptionPage {
  startSec: number;
  endSec: number;
  lines: CaptionWord[][];
  /** Schriftgrad-Faktor für Seiten mit unteilbar langen Wörtern */
  sizeScale?: number;
}

const w = (text: string, startSec: number, endSec: number, accent = false): CaptionWord => ({
  text,
  startSec,
  endSec,
  accent,
});

export const PAGES: CaptionPage[] = [
  // Intro
  {
    startSec: 0.033,
    endSec: 2.32,
    lines: [
      [w("JETZT HABEN WIR HIER", 0.033, 0.833)],
      [w("UNSER", 0.833, 1.166), w("SCHWEINEFLEISCH", 1.166, 2.3, true)],
    ],
  },
  // 2,3–5,4: Chips SCHULTER / SCHLEGEL / PFEFFERBEISSER — kein Untertitel.

  // Gewürze
  {
    startSec: 5.666,
    endSec: 6.9,
    lines: [[w("UNSERE", 5.666, 6.033)], [w("GEWÜRZMISCHUNG", 6.3, 6.766, true)]],
  },
  {
    startSec: 6.933,
    endSec: 8.78,
    lines: [
      [w("WO WIR NOCH SELBER", 6.933, 7.533)],
      [w("ZUSAMMENWIEGEN.", 7.533, 8.633)],
    ],
  },

  // Mischen
  {
    startSec: 9.566,
    endSec: 11.0,
    lines: [[w("MACHEN DAS ALLES", 9.566, 10.199)], [w("ZUSAMMEN REIN,", 10.199, 10.866)]],
  },
  {
    startSec: 11.166,
    endSec: 13.03,
    lines: [
      [w("LASSEN DAS IN UNSEREN", 11.166, 11.966)],
      [w("MISCHAUTOMATEN-WOLF", 11.966, 13.033, true)],
    ],
  },
  {
    startSec: 13.033,
    endSec: 13.9,
    lines: [[w("REINFAHREN.", 13.033, 13.699)]],
  },

  // (Maschinen-Pause 13,9–19,1 — Footage trägt allein)
  {
    startSec: 19.166,
    endSec: 20.95,
    lines: [[w("UND STARTEN DANN", 19.166, 20.0)], [w("DAS VERMENGEN.", 20.0, 20.733)]],
  },

  // Füllwolf
  {
    startSec: 22.733,
    endSec: 23.68,
    lines: [[w("WIR HABEN EINEN", 22.733, 23.166)], [w("FÜLLWOLF.", 23.166, 23.566, true)]],
  },
  {
    startSec: 23.699,
    endSec: 26.05,
    lines: [
      [w("DAS HEISST, DIE SACHEN", 23.699, 25.366)],
      [w("WERDEN NOCHMAL", 25.366, 26.066)],
    ],
  },
  {
    startSec: 26.066,
    endSec: 27.4,
    lines: [[w("FEINER GEWOLFT DADURCH.", 26.066, 27.133)]],
  },

  {
    startSec: 29.199,
    endSec: 30.95,
    lines: [
      [w("JETZT HABEN WIR UNSERE", 29.199, 30.099)],
      [w("PFEFFERBEISSER", 30.099, 30.8, true)],
    ],
  },
  {
    startSec: 31.133,
    endSec: 31.85,
    lines: [[w("GROB GEWOLFT.", 31.133, 31.8)]],
  },
  {
    startSec: 31.85,
    endSec: 33.95,
    lines: [
      [w("JETZT KOMMT ER IN DEN", 31.85, 32.5)],
      [w("FÜLLER MIT DEM FÜLLWOLF", 32.5, 33.833)],
    ],
  },
  {
    startSec: 34.166,
    endSec: 36.1,
    lines: [
      [w("UND WIRD DADURCH", 34.166, 34.9)],
      [w("NOCHMAL NEU GEWOLFT,", 34.9, 36.166)],
    ],
  },
  {
    startSec: 36.166,
    endSec: 38.28,
    lines: [
      [w("DASS ES NOCH BESSER", 36.166, 36.966)],
      [w("MITEINANDER VERMISCHT.", 36.966, 38.199)],
    ],
  },

  // Saitendarm
  {
    startSec: 38.3,
    endSec: 40.15,
    lines: [[w("HIER SEHT IHR", 38.3, 38.833)], [w("UNSEREN FÜLLWOLF.", 38.833, 40.033)]],
  },
  {
    startSec: 40.4,
    endSec: 42.4,
    lines: [
      [w("DAS IST WIEDER EIN", 40.4, 41.066)],
      [w("SAITENDARM 20/22,", 41.066, 42.433)],
    ],
  },
  {
    startSec: 42.433,
    endSec: 43.9,
    lines: [[w("EIN", 42.433, 42.966), w("SCHAFSDARM.", 42.966, 43.599, true)]],
  },
  {
    startSec: 44.233,
    endSec: 45.03,
    lines: [[w("UND DA FÜLLEN WIR JETZT", 44.233, 45.033)]],
  },
  {
    startSec: 45.033,
    endSec: 46.3,
    lines: [[w("UNSERE PFEFFERBEISSER", 45.033, 45.699)], [w("REIN.", 45.699, 46.033)]],
  },

  // (Füll-Pause 46,3–50,7)

  // Räuchern
  {
    startSec: 50.8,
    endSec: 53.6,
    lines: [
      [w("UNSERE PFEFFERBEISSER", 50.8, 51.8)],
      [w("WERDEN ÜBER", 51.8, 53.0), w("BUCHENHOLZ", 53.0, 53.633, true)],
    ],
  },
  {
    startSec: 53.633,
    endSec: 56.3,
    lines: [
      [w("ÜBER NACHT ANGERAUCHT,", 53.633, 55.0)],
      [w("IMMER IM INTERVALL.", 55.0, 56.133)],
    ],
  },

  // 56,5–59,3: Wechsel-Beat TROCKNEN ⇄ RAUCHEN — kein Untertitel.

  // Outro
  {
    startSec: 59.699,
    endSec: 61.35,
    lines: [
      [w("UND DANN KÖNNT IHR SIE", 59.699, 60.5)],
      [w("IMMER AM NÄCHSTEN TAG", 60.5, 61.366)],
    ],
  },
  {
    startSec: 61.366,
    endSec: 63.3,
    sizeScale: 0.8,
    lines: [
      [w("FRISCH IN UNSEREN", 61.366, 62.033, true)],
      [w("FLEISCHEREI-FACHGESCHÄFTEN", 62.033, 63.333)],
    ],
  },
  {
    startSec: 63.333,
    endSec: 64.4,
    lines: [[w("ABHOLEN", 63.333, 64.333)]],
  },
  // 64,4–66,7: Shop-Logo-Kasten trägt „oder in unseren 24/7 Stores".
];

// --- Animations-Beats (Sekunden) ---

export const BEATS = {
  /** Intro-Kaskade: drei Chips nacheinander, wie gesprochen */
  chipSchulter: { start: 2.55, end: 6.25 },
  chipSchlegel: { start: 3.45, end: 6.25 },
  chipTitel: { start: 4.3, end: 6.25 },

  /** Waagen-Icon (Gewürze selbst wiegen) — nur Icon, kein Text */
  waage: { start: 6.15, end: 8.95 },

  /** Rotierendes Vermengen-Icon — nur Icon */
  mixer: { start: 18.9, end: 21.2 },

  /** Räucher-Icon: Scheite + Flamme + Rauch — nur Icon */
  rauch: { start: 50.85, end: 56.35 },

  /** TROCKNEN ⇄ RAUCHEN, aktiver Chip wechselt auf den Wortzeiten */
  toggle: { start: 56.45, end: 59.45 },

  /** Offizielles 24/7-Shop-Logo */
  shops: { start: 64.45, end: 66.75 },

  /** Marken-Outro: Logo + Claim */
  hero: { start: 66.9, end: 68.7 },
} as const;

/** Wortzeiten des Wechsel-Beats (gesprochen) */
export const TOGGLE_WORDS: { word: "TROCKNEN" | "RAUCHEN"; atSec: number }[] = [
  { word: "TROCKNEN", atSec: 56.566 },
  { word: "RAUCHEN", atSec: 57.333 },
  { word: "TROCKNEN", atSec: 57.9 },
  { word: "RAUCHEN", atSec: 58.633 },
];

/** Laufzeit: letztes Wort endet 66,37 s, danach Shop-Kasten + Outro. */
export const DURATION_SEC = 68.9;
