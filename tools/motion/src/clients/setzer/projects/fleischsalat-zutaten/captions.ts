// ============================================================
// Setzer — Video 4 „Fleischsalat Zutaten" (Prozess-Reel, 131,8 s)
// Untertitel- und Beat-Daten (Sekunden), t = 0 ist der erste Frame
// des Schnitts. Ausspielung 30 fps (wie Video 6 — GEGEN DEN SCHNITT
// PRÜFEN, Framerate ist pro Setzer-Video verschieden).
//
// Grundlage: Scribe-Worttranskript des fertigen Schnitts
// (`_intern/video4_scribe_words.json`, Charge 2026-08 Dreh 18.08).
// Die Premiere-UT-SRT war unbrauchbar (Verhörer + japanische
// Halluzinationen) — siehe Protokoll 2026-09-01.
//
// ASR-Korrekturen auf Originalzeiten. Von David am Ton bestätigt
// (Feedback 01.09.): „was da DRIN ist" (4,2 s), „frisch in DEN
// VERKAUF" (27,9 s), „dass HIER dann jeder" (71,2 s), „frisch in die
// FILIALE" (100,0 s) — Scribe hatte 2× „Theke" verhört. Weiter offen:
//   3× „Leola"        -> Lyoner (12,9 / 36,7 / 60,3 s)
//   „will"            -> füllen (24,6 s; alternativ „wiegen")
//   „vertan"          -> verteilt (69,8 s)
//   „Unumgänglich"    -> Unhygienisch (74,2 s)
// „Fleischwurst" (15,5 s): Chip auf Davids Ansage KOMPLETT RAUS —
// die Passage läuft ohne Grafik und ohne UT.
//
// Dopplungs-Regel (David 2026-08-12), ganze Sinneinheiten:
//   - Zutaten-Aufzählung 5,26–19,60 s trägt die Checkliste
//     (inkl. Subzeilen „ÖL · WASSER · GEWÜRZE", „AUCH IN DER THEKE",
//     „Z. B. SENF") — kein Untertitel in diesem Fenster.
//   - Live-Zugabe 35,12–47,22 s: Abhak-Animation auf Davids Ansage
//     raus (01.09.) — das Fenster läuft jetzt als normaler Untertitel.
//   - „Wir vermischen jetzt das fünf Minuten lang" trägt der
//     5-MIN-Timer (63,86–65,64 s) — Untertitel erst ab den
//     dass-Sätzen.
//   - „auf 250 g und auf 125 g portioniert" tragen die zwei
//     Becher-Chips (104,60–108,94 s).
//   - „Jetzt haben wir hier unsere 250 g …" / „kommen 250 g raus"
//     trägt der zurückkehrende 250-g-Chip (Puls auf 119,30 s).
//   - Outro-Satz ab 127,56 s trägt das Marken-Outro (Logo + Claim).
//
// Layout: max. 2 Zeilen pro Seite, Zeilen erscheinen als Ganzes,
// höchstens ein Akzentwort pro Seite, `sizeScale` für lange Zeilen.
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
  // --- Hook ---
  {
    startSec: 0.06,
    endSec: 2.02,
    sizeScale: 0.93,
    lines: [
      [w("WAS BEDEUTET EIGENTLICH", 0.06, 0.78)],
      [w("HAUSGEMACHTER", 0.8, 1.43), w("FLEISCHSALAT", 1.48, 2.0, true)],
    ],
  },
  {
    startSec: 2.04,
    endSec: 2.75,
    lines: [[w("BEI SETZER?", 2.04, 2.6)]],
  },
  {
    startSec: 2.77,
    endSec: 4.6,
    sizeScale: 0.92,
    lines: [
      [w("ICH ZEIGE EUCH TRANSPARENT,", 2.77, 3.88)],
      [w("WAS DA DRIN IST.", 3.92, 4.48)],
    ],
  },

  // 5,26–19,60: Zutaten-Checkliste baut sich auf — kein Untertitel.

  // --- Ablauf ---
  {
    startSec: 20.1,
    endSec: 21.4,
    sizeScale: 0.9,
    lines: [[w("SO, JETZT MACHEN WIR WEITER.", 20.1, 21.28)]],
  },
  {
    startSec: 21.58,
    endSec: 23.66,
    lines: [
      [w("WIR FÜHREN ALLE", 21.58, 22.24)],
      [w("ZUTATEN ZUSAMMEN,", 22.26, 23.64)],
    ],
  },
  {
    startSec: 23.68,
    endSec: 24.54,
    lines: [[w("VERMISCHEN DAS DANN,", 23.68, 24.5)]],
  },
  {
    startSec: 24.56,
    endSec: 26.32,
    lines: [
      [w("FÜLLEN ES DANN IN DIE", 24.56, 25.28)],
      [w("PORTIONSBECHER", 25.32, 26.24, true)],
    ],
  },
  {
    startSec: 26.36,
    endSec: 29.4,
    lines: [
      [w("UND DANN IST ES JEDEN TAG", 26.36, 27.42)],
      [w("FRISCH IN DEN VERKAUF.", 27.54, 28.16)],
    ],
  },

  // --- Live-Zugabe (Abhak-Animation raus, David 01.09.) ---
  {
    startSec: 35.12,
    endSec: 38.26,
    sizeScale: 0.88,
    lines: [
      [w("JETZT HABEN WIR UNSERE LYONER,", 35.12, 37.12)],
      [w("UNSERE MAYONNAISE DRIN.", 37.22, 38.2)],
    ],
  },
  {
    startSec: 38.3,
    endSec: 40.64,
    sizeScale: 0.85,
    lines: [
      [w("JETZT KOMMEN NOCH UNSERE", 38.3, 39.04)],
      [w("GESCHNITTENE ESSIGGURKEN DAZU.", 39.1, 40.58)],
    ],
  },
  {
    startSec: 42.32,
    endSec: 44.08,
    lines: [
      [w("JETZT HABEN WIR", 42.32, 42.74)],
      [w("ALLE ZUTATEN DRIN.", 42.82, 44.06)],
    ],
  },
  {
    startSec: 44.1,
    endSec: 45.71,
    lines: [
      [w("JETZT KOMMEN NOCH", 44.1, 44.64)],
      [w("UNSERE GEWÜRZE DAZU", 44.7, 45.7)],
    ],
  },
  {
    startSec: 45.74,
    endSec: 47.3,
    lines: [
      [w("UND DANN WIRD", 45.74, 46.03)],
      [w("DAS ALLES VERMENGT.", 46.04, 47.22)],
    ],
  },

  // --- Abwiegen ---
  {
    startSec: 49.86,
    endSec: 51.4,
    sizeScale: 0.9,
    lines: [[w("BEI UNS IST ALLES ABGEWOGEN.", 49.86, 51.36)]],
  },
  {
    startSec: 51.41,
    endSec: 53.6,
    lines: [
      [w("DESWEGEN KRATZEN WIR", 51.41, 52.25)],
      [w("AUCH ALLES AUS,", 52.32, 53.54)],
    ],
  },
  {
    startSec: 53.81,
    endSec: 55.76,
    sizeScale: 0.9,
    lines: [
      [w("SONST PASST DAS", 53.81, 54.39), w("VERHÄLTNIS", 54.4, 54.78, true)],
      [w("WIEDER NICHT MEHR.", 54.82, 55.74)],
    ],
  },

  // --- Von Hand vs. Maschine (Icons tragen kein Wort — UT läuft) ---
  {
    startSec: 55.78,
    endSec: 58.0,
    sizeScale: 0.88,
    lines: [
      [w("BEI UNS WIRD DER FLEISCHSALAT", 55.78, 57.06)],
      [w("NOCH", 57.07, 57.17), w("VON HAND", 57.2, 57.59, true), w("GEMISCHT.", 57.6, 57.98)],
    ],
  },
  {
    startSec: 58.02,
    endSec: 61.44,
    sizeScale: 0.85,
    lines: [
      [w("MIT DER MASCHINE MACHT MAN", 58.02, 59.18)],
      [w("DIE STRUKTUR DER LYONER KAPUTT.", 59.22, 61.4)],
    ],
  },
  {
    startSec: 61.45,
    endSec: 63.12,
    lines: [
      [w("DESWEGEN MISCHEN WIR", 61.45, 62.1)],
      [w("ALLES VON HAND.", 62.12, 63.08)],
    ],
  },

  // 63,86–65,64: „fünf Minuten lang" trägt der Timer — UT ab dass-Satz.
  {
    startSec: 65.96,
    endSec: 68.47,
    sizeScale: 0.95,
    lines: [
      [w("DASS ALLES SCHÖN", 65.96, 66.76)],
      [w("MITEINANDER VERMISCHT IST,", 66.78, 68.46)],
    ],
  },
  {
    startSec: 68.48,
    endSec: 70.5,
    lines: [
      [w("DASS ÜBERALL", 68.48, 69.22)],
      [w("ALLES VERTEILT IST", 69.32, 70.42)],
    ],
  },
  {
    startSec: 70.66,
    endSec: 73.75,
    sizeScale: 0.88,
    lines: [
      [w("UND DASS HIER DANN JEDER DEN", 70.66, 72.38)],
      [w("GLEICHEN FLEISCHSALAT KRIEGT.", 72.42, 73.7)],
    ],
  },

  // --- Hygiene ---
  {
    startSec: 74.16,
    endSec: 75.92,
    sizeScale: 0.9,
    lines: [
      [w("UNHYGIENISCH OHNE HANDSCHUHE", 74.16, 75.36)],
      [w("IST ES NICHT,", 75.38, 75.88)],
    ],
  },
  {
    startSec: 76.22,
    endSec: 79.65,
    sizeScale: 0.88,
    lines: [
      [w("WEIL WIR WASCHEN UNSERE HÄNDE", 76.22, 77.84)],
      [w("NACH JEDEM ARBEITSSCHRITT.", 78.38, 79.6)],
    ],
  },
  {
    startSec: 80.54,
    endSec: 83.8,
    lines: [
      [w("WIR DESINFIZIEREN", 80.54, 81.98)],
      [w("NACH JEDEM ARBEITSSCHRITT", 82.02, 83.72)],
    ],
  },
  {
    startSec: 84.2,
    endSec: 86.8,
    sizeScale: 0.92,
    lines: [
      [w("UND ES IST WISSENSCHAFTLICH", 84.2, 86.16)],
      [w("BEWIESEN,", 86.28, 86.76)],
    ],
  },
  {
    startSec: 87.16,
    endSec: 88.4,
    lines: [
      [w("DASS WENN WIR", 87.16, 87.64)],
      [w("HANDSCHUHE TRAGEN,", 87.68, 88.35)],
    ],
  },
  {
    startSec: 88.42,
    endSec: 90.72,
    sizeScale: 0.95,
    lines: [
      [w("DASS VIEL MEHR BAKTERIEN", 88.42, 89.52)],
      [w("AN DER HAND HAFTEN BLEIBEN", 89.56, 90.71)],
    ],
  },
  {
    startSec: 90.74,
    endSec: 91.55,
    lines: [[w("WIE OHNE.", 90.74, 91.52)]],
  },

  // --- Rekap ---
  {
    startSec: 91.56,
    endSec: 93.13,
    lines: [
      [w("WIE IHR GESEHEN HABT,", 91.56, 92.26)],
      [w("WIRD DER FLEISCHSALAT", 92.28, 93.12)],
    ],
  },
  {
    startSec: 93.14,
    endSec: 94.98,
    lines: [[w("DURCHGEMISCHT VON HAND.", 93.14, 94.94)]],
  },
  {
    startSec: 95.0,
    endSec: 96.8,
    lines: [
      [w("ALS NÄCHSTES WIRD ER", 95.0, 95.69)],
      [w("IN DIE BECHER ABGEFÜLLT", 95.7, 96.76)],
    ],
  },
  {
    startSec: 96.82,
    endSec: 100.45,
    sizeScale: 0.88,
    lines: [
      [w("UND KOMMT DANN FÜR EUCH JEDEN", 96.82, 97.92)],
      [w("MORGEN", 97.96, 98.26), w("FRISCH", 98.3, 98.48, true), w("IN DIE FILIALE.", 98.54, 100.44)],
    ],
  },

  // --- Füllmaschine ---
  {
    startSec: 100.46,
    endSec: 102.8,
    sizeScale: 0.8,
    lines: [
      [w("JETZT HABEN WIR UNSEREN FERTIGEN", 100.46, 102.18)],
      [w("FLEISCHSALAT IN DIE MULDE.", 102.2, 102.74)],
    ],
  },
  {
    startSec: 102.82,
    endSec: 104.52,
    lines: [
      [w("DAS WIRD JETZT IN DIE", 102.82, 103.44)],
      [w("FÜLLMASCHINE GEMACHT,", 103.52, 104.47)],
    ],
  },

  // 104,60–108,94: Becher-Chips tragen „auf 250 g und auf 125 g
  // portioniert" — kein Untertitel.
  // 113,44–116,72: Rückkehr des 250-g-Chips trägt den Satz.

  {
    startSec: 117.18,
    endSec: 118.92,
    lines: [
      [w("GEHEN WIR DRUNTER,", 117.18, 117.96)],
      [w("DRÜCKEN EINMAL DRAUF,", 118.0, 118.88)],
    ],
  },
  // 119,02–120,66: „kommen 250 g raus" — Puls des Chips.

  // --- Deckel ---
  {
    startSec: 123.9,
    endSec: 126.22,
    sizeScale: 0.92,
    lines: [
      [w("DANN MACHEN WIR UNSEREN", 123.9, 124.64)],
      [w("FLEISCHSALATDECKEL", 124.7, 125.6, true), w("DRAUF.", 125.64, 126.18)],
    ],
  },

  // 127,56–131,32: Outro-Satz trägt das Marken-Outro.
];

// --- Zutaten-Checkliste ---

export interface ChecklistRow {
  /** Zeile in Versalien (Grafik trägt die Aufzählung) */
  label: string;
  /** Icon-Schlüssel (Zuordnung in der Komposition) */
  icon: "gurke" | "mayo" | "lyoner" | "gewuerz";
  /** Wortzeit im Aufbau-Fenster */
  appearAt: number;
  /** kleine rote Subzeile (O-Ton-Wörter) */
  sub?: string;
  /** Wortzeit der Subzeile */
  subAt?: number;
}

export const CHECKLIST_ROWS: ChecklistRow[] = [
  { label: "ESSIGGURKEN", icon: "gurke", appearAt: 5.94 },
  {
    label: "MAYONNAISE",
    icon: "mayo",
    appearAt: 8.16,
    sub: "ÖL · WASSER · GEWÜRZE",
    subAt: 9.24,
  },
  {
    label: "LYONER",
    icon: "lyoner",
    appearAt: 12.9,
    sub: "AUCH IN DER THEKE",
    subAt: 13.7,
  },
  // „Fleischwurst" (16,3 s) auf Davids Ansage komplett raus (01.09.).
  {
    label: "GEWÜRZE",
    icon: "gewuerz",
    appearAt: 17.52,
    sub: "Z. B. SENF",
    subAt: 18.58,
  },
];

// --- Animations-Beats (Sekunden) ---

export const BEATS = {
  /** Checkliste: Chips stapeln sich auf den Wortzeiten */
  checklistBuild: { start: 5.4, end: 19.85 },

  /** Waagen-Icon (alles abgewogen) — nur Icon, kein Text */
  waage: { start: 49.95, end: 55.85 },

  /** HAND ✓ vs. MASCHINE ✗ — nur Icons; X auf „kaputt", Puls auf „von Hand" */
  vs: { start: 55.95, end: 63.25 },
  vsStrikeAt: 60.75,
  vsHandPulseAt: 61.55,

  /** 5-MIN-Timer — trägt „fünf Minuten lang" */
  timer: { start: 63.9, end: 73.9 },

  /** Hände waschen / desinfizieren — nur Icons, nacheinander */
  wasch: { start: 76.45, end: 80.25 },
  spray: { start: 80.55, end: 83.95 },

  /** Zwei Becher-Chips 250 g / 125 g */
  grams: { start: 104.7, end: 110.0 },
  gram250At: 104.75,
  gram125At: 106.3,

  /** Rückkehr des 250-g-Chips bei der Becher-Demo, Puls auf „250 g raus" */
  demo: { start: 114.45, end: 121.0 },
  demoPulseAt: 119.3,

  /** Marken-Outro: Logo + Claim */
  hero: { start: 127.7, end: 131.7 },
} as const;

/** Schnittlänge: Audio-Export ist 131,776 s; letztes Wort endet 131,32 s. */
export const DURATION_SEC = 131.78;
