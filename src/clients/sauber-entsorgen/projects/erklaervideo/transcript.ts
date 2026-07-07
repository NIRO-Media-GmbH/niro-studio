// ============================================================
// Sauber Entsorgen — Erklärvideo (Full Overlay)
// 16:9, 25fps, ~121s. Transparent alpha overlay over GF footage.
// GF sits on the RIGHT (golden ratio) → all graphics anchored LEFT.
//
// Timeline t=0 corresponds to SRT timecode 01:00:00,000.
// Use the `timeOffsetSec` prop to nudge the whole overlay if the
// editor places it at a different sequence timecode.
// (The clean script runs 01:00:00–01:02:00; everything after
//  01:03:16 in the SRT is outtakes and is intentionally ignored.)
// ============================================================

import type { ChipItem, ListItem, ServiceIconName } from "../../components";

type CueScene = {
  kind: "cue";
  startSec: number;
  durationSec: number;
  word: string;
  icon: ServiceIconName;
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

type StepScene = {
  kind: "step";
  startSec: number;
  durationSec: number;
  number: string;
  title: string;
  subtitle?: string;
  icon: ServiceIconName;
  anchorY?: number;
};

type IntroScene = {
  kind: "intro";
  startSec: number;
  durationSec: number;
  name: string;
  role: string;
  company: string;
  anchorY?: number;
};

type CtaScene = {
  kind: "cta";
  startSec: number;
  durationSec: number;
  headline: string;
  phone: string;
  closing?: string;
  anchorY?: number;
};

export type Scene =
  | CueScene
  | ChipsScene
  | ListScene
  | StepScene
  | IntroScene
  | CtaScene;

export const SCENES: Scene[] = [
  // --- 1) Was geräumt wird (0–5.6) ---
  {
    kind: "chips",
    startSec: 0.2,
    durationSec: 5.4,
    staggerFrames: 18,
    chips: [
      { label: "Wohnung", icon: "wohnung" },
      { label: "Haus", icon: "haus" },
      { label: "Gewerbeobjekt", icon: "gewerbe" },
    ],
  },

  // --- 2) Anlässe / Lebenssituationen (5.9–12.3) ---
  {
    kind: "list",
    startSec: 5.9,
    durationSec: 6.4,
    heading: "Zum Beispiel",
    anchorY: 0.22,
    staggerFrames: 30,
    items: [
      { label: "Trauerfall", icon: "herz" },
      { label: "Umzug ins Heim", icon: "umzug" },
      { label: "Neuanfang", icon: "sonne" },
      { label: "Frisch gekaufte Immobilie", icon: "schluessel" },
      { label: "Firmenauflösung", icon: "firma" },
    ],
  },

  // --- 3) Überforderung (12.9–18.5) ---
  { kind: "cue", startSec: 12.9, durationSec: 2.2, word: "Berge von Sachen", icon: "nachlass" },
  { kind: "cue", startSec: 15.2, durationSec: 1.5, word: "Wer macht das?", icon: "frage" },
  { kind: "cue", startSec: 16.8, durationSec: 1.7, word: "Worauf muss ich achten?", icon: "auge" },

  // --- 4) Lösung (18.7–22.4) ---
  { kind: "cue", startSec: 18.7, durationSec: 3.6, word: "Professioneller Partner an deiner Seite", icon: "partner" },

  // --- 5) Intro Tobias (22.9–30.0) ---
  {
    kind: "intro",
    startSec: 22.9,
    durationSec: 4.0,
    role: "Dein Partner",
    name: "Tobias",
    company: "Sauber Entsorgen",
    anchorY: 0.56,
  },
  {
    kind: "chips",
    startSec: 26.9,
    durationSec: 3.1,
    bottomRatio: 0.12,
    staggerFrames: 16,
    chips: [
      { label: "Idar-Oberstein", icon: "pin" },
      { label: "Region & bundesweit", icon: "karte" },
    ],
  },

  // --- 6) Persönlich (30.4–34.0) ---
  {
    kind: "list",
    startSec: 30.4,
    durationSec: 3.6,
    anchorY: 0.34,
    staggerFrames: 50,
    items: [
      { label: "Fester Ansprechpartner", icon: "partner", tone: "pos" },
      { label: "Kein anonymes Callcenter", icon: "cross", tone: "neg" },
    ],
  },

  // --- 7) Leistungen (34.6–46.0) — the original 12s block ---
  { kind: "cue", startSec: 34.6, durationSec: 1.6, word: "Haushaltsauflösungen", icon: "haus" },
  { kind: "cue", startSec: 36.3, durationSec: 1.5, word: "Nachlassauflösungen", icon: "nachlass" },
  {
    kind: "chips",
    startSec: 38.0,
    durationSec: 2.3,
    staggerFrames: 12,
    chips: [
      { label: "Keller", icon: "keller" },
      { label: "Dachboden", icon: "dachboden" },
      { label: "Garage", icon: "garage" },
    ],
  },
  { kind: "cue", startSec: 40.9, durationSec: 1.9, word: "Firmen- & Insolvenzauflösungen", icon: "firma" },
  { kind: "cue", startSec: 43.3, durationSec: 2.6, word: "Kurzfristig & schnell", icon: "express" },

  // --- 8) Zielgruppen (47.2–56.7) ---
  {
    kind: "list",
    startSec: 47.2,
    durationSec: 6.0,
    heading: "Für wen?",
    anchorY: 0.24,
    staggerFrames: 28,
    items: [
      { label: "Privatpersonen", icon: "person" },
      { label: "Unternehmen", icon: "firma" },
      { label: "Hausverwaltungen", icon: "haus" },
      { label: "Makler", icon: "schluessel" },
    ],
  },
  { kind: "cue", startSec: 54.0, durationSec: 2.7, word: "Klarer, nachvollziehbarer Ablauf", icon: "check" },

  // --- 9) Ablauf 1–3 (57.2–79.2) ---
  { kind: "cue", startSec: 57.2, durationSec: 1.4, word: "So läuft's ab", icon: "check" },
  {
    kind: "step",
    startSec: 58.2,
    durationSec: 5.9,
    number: "1",
    title: "Besichtigung",
    subtitle: "Kostenlos & unverbindlich",
    icon: "auge",
    anchorY: 0.42,
  },
  {
    kind: "step",
    startSec: 64.4,
    durationSec: 8.0,
    number: "2",
    title: "Festpreis-Angebot",
    subtitle: "Keine versteckten Kosten",
    icon: "preis",
    anchorY: 0.42,
  },
  {
    kind: "step",
    startSec: 72.6,
    durationSec: 6.6,
    number: "3",
    title: "Fester Termin",
    subtitle: "In 1–3 Tagen · im Notfall schneller",
    icon: "kalender",
    anchorY: 0.42,
  },

  // --- 10) Durchführung (82.5–89.5) ---
  {
    kind: "list",
    startSec: 82.5,
    durationSec: 7.0,
    heading: "Keinen Finger rühren",
    anchorY: 0.24,
    staggerFrames: 38,
    items: [
      { label: "Wir tragen & verladen alles", icon: "lkw" },
      { label: "Sauber & getrennt entsorgt", icon: "entsorgung" },
      { label: "Über zertifizierte Betriebe", icon: "schild", tone: "pos" },
    ],
  },

  // --- 11) Umwelt / Recht (89.3–96.1) ---
  { kind: "cue", startSec: 89.3, durationSec: 1.6, word: "Umweltgerecht & legal", icon: "umwelt" },
  { kind: "cue", startSec: 91.0, durationSec: 2.2, word: "Rechtlich auf der sicheren Seite", icon: "schild" },
  { kind: "cue", startSec: 93.3, durationSec: 2.7, word: "Wichtig für Firmen & Hausverwaltungen", icon: "firma" },

  // --- 12) Übergabe (96.6–105.5) ---
  { kind: "cue", startSec: 96.6, durationSec: 2.0, word: "Besenrein übergeben", icon: "glanz" },
  {
    kind: "chips",
    startSec: 98.6,
    durationSec: 3.0,
    staggerFrames: 16,
    chips: [
      { label: "Übergabe", icon: "check" },
      { label: "Verkauf", icon: "preis" },
      { label: "Renovierung", icon: "haus" },
    ],
  },
  { kind: "cue", startSec: 102.3, durationSec: 3.2, word: "Diskret & respektvoll", icon: "schloss" },

  // --- 13) CTA (108.6–120.6) ---
  {
    kind: "cta",
    startSec: 108.6,
    durationSec: 12.0,
    headline: "Kostenloses Vor-Ort-Angebot",
    phone: "+49 170 6910315",
    closing: "Du musst da nicht allein durch.",
    anchorY: 0.3,
  },
];
