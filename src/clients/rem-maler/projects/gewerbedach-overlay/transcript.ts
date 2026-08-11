// ============================================================
// REM Gewerbedach — Testimonial-Overlay
// 16:9, 25fps, ~105s. Transparentes Alpha-Overlay über das
// Sprecher-/Interview-Footage.
//
// Timeline t=0 entspricht SRT-Timecode 01:00:00,000
// (Transcribe REM Gewerbedach Reinigung.srt — Kunden-O-Ton).
// Mit `timeOffsetSec` lässt sich das gesamte Overlay im Schnitt
// verschieben, falls das Footage anders liegt.
//
// Kundenfeedback 2026-07-08 eingearbeitet:
// - negativ = Rot, positiv = Grün (tone pro Element)
// - nur noch Einblendungen mit Mehrwert; Vergleiche als
//   Rot/Grün-Gegenüberstellung statt einzelner Cues
//
// Kundenfeedback 2026-07-22 eingearbeitet (v3):
// - REM muss von Anfang an erkennbar sein → BrandIntro-Karte
//   (R-Monogramm + „REM Malerfachbetrieb") 0,5–4,4 s, endet
//   bevor der erste Cue kommt; Szene 2 nennt REM im Text.
//   (Der O-Ton selbst nennt „die Firma REM" erst bei 42,8 s.)
//
// Sprechpause 57,8–69,7 s bleibt bewusst leer (B-Roll/Sprecher pur).
// ============================================================

import type { ChipItem, CueTone, ListItem, RemIconName } from "../../components/overlay";

type CueScene = {
  kind: "cue";
  startSec: number;
  durationSec: number;
  word: string;
  icon: RemIconName;
  tone?: CueTone;
  offsetY?: number;
};

type ChipsScene = {
  kind: "chips";
  startSec: number;
  durationSec: number;
  chips: ChipItem[];
  bottomRatio?: number;
  staggerFrames?: number;
};

type ListScene = {
  kind: "list";
  startSec: number;
  durationSec: number;
  heading?: string;
  items: ListItem[];
  anchorY?: number;
  staggerFrames?: number;
};

type BrandScene = {
  kind: "brand";
  startSec: number;
  durationSec: number;
};

export type Scene = CueScene | ChipsScene | ListScene | BrandScene;

export const SCENES: Scene[] = [
  // --- 0) Absender: REM (0.5–4.4) — BRAND ---
  // Marke von Anfang an erkennbar; Exit vor dem ersten Cue (4.6).
  { kind: "brand", startSec: 0.5, durationSec: 3.9 },

  // --- 1) Zustand des Dachs (4.6–11.0) — NEGATIV ---
  // „Also es war fast keine Farbe sichtbar … höchste Zeit, dass neu lackiert wird."
  { kind: "cue", startSec: 4.6, durationSec: 6.2, word: "Fast keine Farbe sichtbar", icon: "farbe", tone: "neg" },

  // --- 2) Schnelle Reaktion (11.9–18.5) — POSITIV ---
  // „Innerhalb einer Woche … hat sich dann der Chef bei mir gemeldet"
  // (v3: „REM-Chef" — Firma auch im ersten inhaltlichen Cue verankern)
  { kind: "cue", startSec: 12.1, durationSec: 6.3, word: "REM-Chef meldete sich innerhalb 1 Woche", icon: "telefon", tone: "pos" },

  // --- 3) Vergleich Angebot (18.8–26.8) — Grün vs. Rot ---
  // „Das Angebot ging fix." (18.8) / „…drei, vier Wochen gedauert" (24.4)
  {
    kind: "list",
    startSec: 18.9,
    durationSec: 7.7,
    heading: "Angebot",
    anchorY: 0.24,
    staggerFrames: 133, // Item 2 fällt auf „drei, vier Wochen" (24.4 s)
    items: [
      { label: "REM: Angebot ging fix", icon: "dokument", tone: "pos" },
      { label: "Andere: 3–4 Wochen", icon: "kalender", tone: "neg" },
    ],
  },

  // --- 4) Kommunikation (26.8–30.6) — POSITIV ---
  { kind: "cue", startSec: 26.9, durationSec: 3.5, word: "Kommunikation: gut", icon: "chat", tone: "pos" },

  // --- 5) Preis-Leistung (31.4–36.4) — POSITIV ---
  { kind: "cue", startSec: 31.6, durationSec: 4.7, word: "Preis-Leistung: sehr gut", icon: "euro", tone: "pos" },

  // --- 6) Vergleich Einrüstung (36.8–50.5) — Rot vs. Grün ---
  // „…ist die ganze Halle eingerüstet" (36.9) /
  // „…hat ein Spezialfahrzeug, so ein Kraner … arbeiten vom Kran aus" (42.0)
  {
    kind: "list",
    startSec: 36.9,
    durationSec: 13.6,
    heading: "Einrüstung",
    anchorY: 0.24,
    staggerFrames: 126, // Item 2 fällt auf „Spezialfahrzeug … Kraner" (42.1 s)
    items: [
      { label: "Andere: ganze Halle einrüsten", icon: "geruest", tone: "neg" },
      { label: "REM: Arbeiten vom Kran aus", icon: "kran", tone: "pos" },
    ],
  },

  // --- 7) Ersparnis (53.2–57.8) — POSITIV ---
  // „Eingerüst gespart und … wesentlich günstiger gewesen"
  { kind: "cue", startSec: 53.3, durationSec: 4.4, word: "Ohne Gerüst: wesentlich günstiger", icon: "euro", tone: "pos" },

  // --- Sprechpause 57.8–69.7: kein Overlay ---

  // --- 8) Gewährleistung (69.7–78.6) — POSITIV ---
  {
    kind: "list",
    startSec: 69.9,
    durationSec: 8.6,
    heading: "Gewährleistung",
    anchorY: 0.24,
    staggerFrames: 92, // Item 2 fällt auf „Der Farbhersteller…" (73.8 s)
    items: [
      { label: "5 Jahre auf die Arbeitsausführung", icon: "schild", tone: "pos" },
      { label: "20 Jahre auf die Farbe (Hersteller)", icon: "farbe", tone: "pos" },
    ],
  },

  // --- 9) Ergebnis (79.8–88.2) — POSITIV ---
  { kind: "cue", startSec: 80.0, durationSec: 4.3, word: "Ergebnis: sehr zufrieden", icon: "stern", tone: "pos" },
  // „Gegenüber vorher … jetzt sind das Welten."
  { kind: "cue", startSec: 84.6, durationSec: 3.8, word: "Vorher / Nachher: Welten", icon: "vergleich", tone: "pos" },

  // --- 10) Photovoltaik (93.9–98.0) — POSITIV ---
  // „…die Photovoltaikanlage auch noch mal richtig gereinigt."
  { kind: "cue", startSec: 93.9, durationSec: 4.1, word: "Photovoltaik mitgereinigt", icon: "solar", tone: "pos" },

  // --- 11) Fazit (101.4–103.4+) — POSITIV ---
  // „…kann ich die Firma weiterempfehlen."
  { kind: "cue", startSec: 101.4, durationSec: 3.5, word: "Klare Weiterempfehlung", icon: "daumen", tone: "pos" },
];
