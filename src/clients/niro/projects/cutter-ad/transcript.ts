// ============================================================
// NIRO — Cutter Ad (9:16) Recruiting-Untertitel
// 1080×1920, 25fps, transparentes Alpha-Overlay über den Schnitt.
// Timeline t=0 = SRT-Timecode 01:00:00,000 (Premiere-Stunden-Offset).
//
// Quelle: projects/NIRO/Cutter Ad/CUTTER Ad.srt (word-level).
// Multi-Wort-Cues wurden proportional zur Zeichenlänge gesplittet.
//
// Vom Kunden (David, 2026-08-07) bestätigte Transkript-Korrekturen:
//   0:07  "Freizeitabend zum Task noch eigentlich ein Hauptjob"
//         → "Freizeit abends und hast noch eigentlich ein Hauptjob"
//   0:30  "mit dem Drehen fertig haben hier suchen eben Leute"
//         → "mit dem Drehen fertig. Wir suchen eben Leute"
// Stille Fixes: "Daran ist"→"Dann ist", "durch Gas zu geben"→"Gas zu
// geben", "trage ich dich"→"trag dich", "freuen wir uns sich"→"dich",
// "Niro"→"NIRO", Zusammenschreibungen (weiterzuentwickeln, dazuzulernen).
// ============================================================

export type CaptionWord = {
  text: string;
  startSec: number;
  /** Akzentfarbe (NIRO-Grün) statt Weiß */
  accent?: boolean;
  /** Wort im Satz größer setzen (Mixed-Size-Look) */
  big?: boolean;
};

export type CaptionPage = {
  /**
   * flow = Standard-Wortgruppe, punch = Power-Wort/-Phrase groß,
   * kicker = kleine Versalzeile oben + große Hauptzeile darunter
   */
  style: "flow" | "punch" | "kicker";
  startSec: number;
  endSec: number;
  words: CaptionWord[];
  /** Nur bei style "kicker": Wörter der kleinen Versalzeile */
  kicker?: CaptionWord[];
  /** Font-Größe überschreiben (px), z. B. für sehr lange Wörter */
  sizePx?: number;
  /** Page im Band nach oben ausrichten (macht Platz fürs Name-Insert) */
  alignTop?: boolean;
};

export type StackItem = { text: string; startSec: number };

// --- Untertitel-Pages ---

export const PAGES: CaptionPage[] = [
  {
    style: "flow", startSec: 0.099, endSec: 1.199,
    words: [
      { text: "Du", startSec: 0.099 },
      { text: "machst", startSec: 0.233 },
      { text: "was", startSec: 0.5 },
      { text: "mit", startSec: 0.666 },
      { text: "Videos", startSec: 0.833, accent: true, big: true },
    ],
  },
  {
    // Kundenwunsch 2026-08-07: "semi-" im Untertitel weglassen
    style: "flow", startSec: 1.199, endSec: 3.099,
    words: [
      { text: "und", startSec: 1.199 },
      { text: "das", startSec: 1.633 },
      { text: "professionell,", startSec: 1.866, accent: true, big: true },
    ],
  },
  {
    style: "flow", startSec: 3.099, endSec: 5.866,
    words: [
      { text: "sei", startSec: 3.099 },
      { text: "es", startSec: 3.259 },
      { text: "als", startSec: 3.366 },
      { text: "angestellter", startSec: 3.533 },
      { text: "Videograf", startSec: 4.166, accent: true },
      { text: "oder", startSec: 4.666 },
      { text: "Freelancer", startSec: 5.166, accent: true },
    ],
  },
  {
    style: "flow", startSec: 5.866, endSec: 8.733,
    words: [
      { text: "oder", startSec: 5.866 },
      { text: "irgendwie", startSec: 6.599 },
      { text: "in", startSec: 7.036 },
      { text: "deiner", startSec: 7.133 },
      { text: "Freizeit", startSec: 7.4 },
      { text: "abends", startSec: 8.162 },
    ],
  },
  {
    style: "flow", startSec: 8.733, endSec: 10.8,
    words: [
      { text: "und", startSec: 8.733 },
      { text: "hast", startSec: 8.9 },
      { text: "noch", startSec: 9.099 },
      { text: "eigentlich", startSec: 9.266 },
      { text: "ein", startSec: 9.533 },
      { text: "Hauptjob.", startSec: 9.633, accent: true, big: true },
    ],
  },
  {
    style: "flow", startSec: 10.8, endSec: 12.333,
    words: [
      { text: "Dann", startSec: 10.8 },
      { text: "ist", startSec: 10.99 },
      { text: "dieses", startSec: 11.133 },
      { text: "Video", startSec: 11.333 },
      { text: "hier", startSec: 11.633 },
      { text: "möglicherweise", startSec: 11.733 },
    ],
  },
  {
    // Hook-Abschluss als eigener Mehrwort-Punch
    style: "punch", startSec: 12.333, endSec: 13.099, sizePx: 88,
    words: [
      { text: "genau", startSec: 12.333, accent: true },
      { text: "für", startSec: 12.533, accent: true },
      { text: "dich.", startSec: 12.699, accent: true },
    ],
  },
  {
    style: "flow", startSec: 13.099, endSec: 14.033, alignTop: true,
    words: [
      { text: "Ich", startSec: 13.099 },
      { text: "bin", startSec: 13.3 },
      { text: "David,", startSec: 13.466 },
    ],
  },
  {
    style: "flow", startSec: 14.033, endSec: 15.266, alignTop: true,
    words: [
      { text: "einer", startSec: 14.033 },
      { text: "der", startSec: 14.166 },
      { text: "Gründer", startSec: 14.3 },
      { text: "und", startSec: 14.533 },
      { text: "Geschäftsführer", startSec: 14.633 },
    ],
  },
  {
    style: "flow", startSec: 15.266, endSec: 16.466, alignTop: true,
    words: [
      { text: "von", startSec: 15.266 },
      { text: "NIRO.", startSec: 15.433, accent: true, big: true },
    ],
  },
  {
    style: "flow", startSec: 16.466, endSec: 17.966,
    words: [
      { text: "Wir", startSec: 16.466 },
      { text: "sind", startSec: 16.566 },
      { text: "eine", startSec: 16.766 },
      { text: "Marketingagentur", startSec: 16.966, big: true },
    ],
  },
  {
    style: "flow", startSec: 17.966, endSec: 19.333,
    words: [
      { text: "mit", startSec: 17.966 },
      { text: "verschiedenen", startSec: 18.3 },
      { text: "Schwerpunkten,", startSec: 18.699 },
    ],
  },
  {
    style: "flow", startSec: 19.333, endSec: 22.233, sizePx: 54,
    words: [
      { text: "unter", startSec: 19.333 },
      { text: "anderem", startSec: 19.666 },
      { text: "eben", startSec: 20.0 },
      { text: "der", startSec: 20.366 },
      { text: "In-House-Video-Produktion", startSec: 20.466, accent: true },
    ],
  },
  {
    // Kicker-Lockup: kleine Versalzeile baut auf, Hauptwort poppt
    style: "kicker", startSec: 22.233, endSec: 23.966,
    kicker: [
      { text: "und", startSec: 22.233 },
      { text: "da", startSec: 22.366 },
      { text: "suchen", startSec: 22.533 },
      { text: "wir", startSec: 22.733 },
    ],
    words: [{ text: "Verstärkung.", startSec: 22.833, accent: true }],
  },
  {
    style: "flow", startSec: 23.966, endSec: 25.566,
    words: [
      { text: "Da", startSec: 23.966 },
      { text: "hinten", startSec: 24.233 },
      { text: "sieht", startSec: 24.366 },
      { text: "man", startSec: 24.533 },
      { text: "gerade", startSec: 24.666 },
      { text: "noch", startSec: 24.8 },
      { text: "Jan,", startSec: 24.966 },
    ],
  },
  {
    style: "flow", startSec: 25.566, endSec: 26.699,
    words: [
      { text: "der", startSec: 25.566 },
      { text: "räumt", startSec: 25.666 },
      { text: "gerade", startSec: 25.933 },
      { text: "die", startSec: 26.033 },
      { text: "Sachen", startSec: 26.199 },
      { text: "ein.", startSec: 26.333 },
    ],
  },
  {
    style: "flow", startSec: 26.699, endSec: 28.099,
    words: [
      { text: "Wir", startSec: 26.699 },
      { text: "sind", startSec: 26.756 },
      { text: "hier", startSec: 26.8 },
      { text: "gerade", startSec: 27.0 },
      { text: "bei", startSec: 27.166 },
      { text: "einem", startSec: 27.333 },
      { text: "unserer", startSec: 27.566 },
      { text: "Kunden", startSec: 27.833 },
    ],
  },
  {
    style: "flow", startSec: 28.099, endSec: 30.5,
    words: [
      { text: "im", startSec: 28.099 },
      { text: "Schwarzwald", startSec: 28.266, accent: true },
      { text: "mit", startSec: 28.866 },
      { text: "dem", startSec: 29.466 },
      { text: "Drehen", startSec: 29.599 },
      { text: "fertig.", startSec: 29.9 },
    ],
  },
  {
    style: "flow", startSec: 30.5, endSec: 31.733,
    words: [
      { text: "Wir", startSec: 30.5 },
      { text: "suchen", startSec: 30.733 },
      { text: "eben", startSec: 30.9 },
      { text: "Leute,", startSec: 31.133 },
    ],
  },
  {
    style: "flow", startSec: 31.733, endSec: 33.95,
    words: [
      { text: "die", startSec: 31.733 },
      { text: "Lust", startSec: 32.033 },
      { text: "haben,", startSec: 32.233 },
      { text: "sich", startSec: 32.433 },
      { text: "weiterzuentwickeln,", startSec: 32.633 },
    ],
  },
  {
    style: "flow", startSec: 33.95, endSec: 35.366,
    words: [
      { text: "die", startSec: 33.95 },
      { text: "Lust", startSec: 34.133 },
      { text: "haben,", startSec: 34.3 },
      { text: "Gas", startSec: 34.466, accent: true },
      { text: "zu", startSec: 34.9, accent: true },
      { text: "geben,", startSec: 35.099, accent: true },
    ],
  },
  {
    style: "flow", startSec: 35.366, endSec: 36.4,
    words: [{ text: "dazuzulernen", startSec: 35.366 }],
  },
  {
    style: "flow", startSec: 36.4, endSec: 38.0,
    words: [
      { text: "und", startSec: 36.4 },
      { text: "auch", startSec: 36.733 },
      { text: "eine", startSec: 37.0 },
      { text: "coole", startSec: 37.166 },
      { text: "Dienstleistung", startSec: 37.4 },
    ],
  },
  {
    style: "flow", startSec: 38.0, endSec: 38.848,
    words: [
      { text: "einfach", startSec: 38.0 },
      { text: "zu", startSec: 38.166 },
      { text: "erbringen,", startSec: 38.4 },
    ],
  },
  {
    style: "flow", startSec: 38.848, endSec: 39.599,
    words: [
      { text: "wo", startSec: 38.848 },
      { text: "man", startSec: 38.933 },
      { text: "einfach", startSec: 39.099 },
      { text: "sieht,", startSec: 39.3 },
    ],
  },
  {
    style: "flow", startSec: 39.599, endSec: 40.566,
    words: [
      { text: "dass", startSec: 39.599 },
      { text: "sie", startSec: 39.733 },
      { text: "das", startSec: 39.866 },
      { text: "Leben", startSec: 40.0 },
      { text: "der", startSec: 40.233 },
      { text: "Leute", startSec: 40.366 },
    ],
  },
  {
    style: "punch", startSec: 40.566, endSec: 41.833,
    words: [{ text: "verändert.", startSec: 40.566, accent: true }],
  },
  {
    style: "flow", startSec: 41.833, endSec: 43.933,
    words: [
      { text: "Dadurch,", startSec: 41.833 },
      { text: "dass", startSec: 42.3 },
      { text: "eben", startSec: 42.533 },
      { text: "durch", startSec: 42.833 },
      { text: "unsere", startSec: 43.066 },
      { text: "Anzeigen", startSec: 43.366 },
    ],
  },
  {
    style: "flow", startSec: 43.933, endSec: 45.599,
    words: [
      { text: "die", startSec: 43.933 },
      { text: "Leute", startSec: 44.366 },
      { text: "andere", startSec: 44.599 },
      { text: "Jobs", startSec: 44.966, accent: true },
      { text: "finden", startSec: 45.3, accent: true },
    ],
  },
  {
    style: "flow", startSec: 45.599, endSec: 46.966,
    words: [
      { text: "und", startSec: 45.599 },
      { text: "glücklicher", startSec: 45.866, accent: true, big: true },
      { text: "werden,", startSec: 46.666 },
    ],
  },
  {
    style: "flow", startSec: 46.966, endSec: 49.3,
    words: [
      { text: "weil", startSec: 46.966 },
      { text: "sie", startSec: 47.166 },
      { text: "bei", startSec: 47.266 },
      { text: "besseren", startSec: 47.4 },
      { text: "Arbeitgebern", startSec: 47.8 },
      { text: "arbeiten.", startSec: 48.3 },
    ],
  },
  {
    style: "flow", startSec: 49.3, endSec: 51.333,
    words: [
      { text: "Und", startSec: 49.3 },
      { text: "das", startSec: 49.699 },
      { text: "würdest", startSec: 50.366 },
      { text: "du", startSec: 50.699 },
      { text: "halt", startSec: 50.8 },
      { text: "jeden", startSec: 50.9 },
      { text: "Tag", startSec: 51.066 },
    ],
  },
  {
    style: "flow", startSec: 51.333, endSec: 53.233,
    words: [
      { text: "sehen", startSec: 51.333 },
      { text: "und", startSec: 51.599 },
      { text: "mitbekommen.", startSec: 51.866 },
    ],
  },
  {
    style: "kicker", startSec: 53.233, endSec: 55.699,
    kicker: [
      { text: "Gleichzeitig", startSec: 53.233 },
      { text: "würdest", startSec: 53.866 },
      { text: "du", startSec: 54.436 },
    ],
    words: [
      { text: "sehr", startSec: 54.599 },
      { text: "viel", startSec: 54.766 },
      { text: "rumkommen.", startSec: 54.933, accent: true },
    ],
  },
  {
    style: "flow", startSec: 55.699, endSec: 57.066,
    words: [
      { text: "Wir", startSec: 55.699 },
      { text: "haben", startSec: 55.743 },
      { text: "verschiedene", startSec: 55.8 },
      { text: "Kunden:", startSec: 56.066 },
    ],
  },
  // 57.066–61.866 → Stack (siehe STACK unten)
  {
    style: "flow", startSec: 61.866, endSec: 64.133,
    words: [
      { text: "Schau", startSec: 61.866 },
      { text: "gerne", startSec: 62.066 },
      { text: "einfach", startSec: 62.266 },
      { text: "mal", startSec: 62.566 },
      { text: "auf", startSec: 62.666 },
      { text: "der", startSec: 62.8 },
      { text: "Seite", startSec: 62.9 },
      { text: "vorbei.", startSec: 63.166 },
    ],
  },
  {
    style: "flow", startSec: 64.133, endSec: 65.266,
    words: [
      { text: "Schau", startSec: 64.133 },
      { text: "dir", startSec: 64.279 },
      { text: "ein", startSec: 64.366 },
      { text: "paar", startSec: 64.441 },
      { text: "Beispiele", startSec: 64.566, accent: true },
      { text: "an", startSec: 65.033 },
    ],
  },
  {
    style: "flow", startSec: 65.266, endSec: 66.333,
    words: [
      { text: "und", startSec: 65.266 },
      { text: "wenn", startSec: 65.488 },
      { text: "du", startSec: 65.785 },
      { text: "meinst,", startSec: 65.933 },
      { text: "dass", startSec: 66.183 },
    ],
  },
  {
    style: "flow", startSec: 66.333, endSec: 68.033,
    words: [
      { text: "du", startSec: 66.333 },
      { text: "in", startSec: 66.466 },
      { text: "dieser", startSec: 66.533 },
      { text: "Qualität", startSec: 66.666, accent: true, big: true },
      { text: "auch", startSec: 67.133 },
      { text: "Sachen", startSec: 67.3 },
    ],
  },
  {
    style: "flow", startSec: 68.033, endSec: 68.945,
    words: [
      { text: "delivern", startSec: 68.033, accent: true, big: true },
      { text: "kannst,", startSec: 68.466 },
    ],
  },
  {
    style: "flow", startSec: 68.945, endSec: 70.233,
    words: [
      { text: "dann", startSec: 68.945 },
      { text: "trag", startSec: 69.199 },
      { text: "dich", startSec: 69.4 },
      { text: "gerne", startSec: 69.566 },
      { text: "unten", startSec: 69.666, accent: true },
      { text: "ein", startSec: 69.933, accent: true },
    ],
  },
  {
    style: "flow", startSec: 70.233, endSec: 71.633,
    words: [
      { text: "und", startSec: 70.233 },
      { text: "dann", startSec: 70.866 },
      { text: "freuen", startSec: 71.066 },
      { text: "wir", startSec: 71.4 },
      { text: "uns,", startSec: 71.517 },
    ],
  },
  {
    style: "flow", startSec: 71.633, endSec: 73.0,
    words: [
      { text: "dich", startSec: 71.633 },
      { text: "persönlich", startSec: 71.733, accent: true },
      { text: "kennenzulernen.", startSec: 72.099 },
    ],
  },
];

// --- Stack: Kundenbranchen (57.066–61.866) ---

export const STACK_START_SEC = 57.066;
export const STACK_END_SEC = 61.866;
export const STACK: StackItem[] = [
  { text: "Holzbranche", startSec: 57.066 },
  { text: "Lebensmittelindustrie", startSec: 58.199 },
  { text: "Handwerk", startSec: 59.733 },
  { text: "Autohäuser", startSec: 61.0 },
];

// --- Name-Insert (während der Vorstellung) ---

export const NAME_INSERT_START_SEC = 13.3;
export const NAME_INSERT_END_SEC = 17.2;

// --- CTA-Finale (nach dem letzten Wort) ---

export const CTA_START_SEC = 73.2;

export const TOTAL_DURATION_SEC = 77;
