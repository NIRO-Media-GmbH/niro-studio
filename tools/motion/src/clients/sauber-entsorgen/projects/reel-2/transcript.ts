// ============================================================
// Sauber Entsorgen — Reel 2 (9:16) "Gewerbe / deutschlandweit"
// 1080×1920, 25fps, ~45s. Transparent alpha overlay.
// Centered talking-head reel → graphics CENTERED in the reels band.
// Timeline t=0 = SRT timecode 01:00:00,000.
// ============================================================

import type { ChipItem, ServiceIconName } from "../../components";

type CueScene = {
  kind: "cue";
  startSec: number;
  durationSec: number;
  word: string;
  icon: ServiceIconName;
};

type ChipsScene = {
  kind: "chips";
  startSec: number;
  durationSec: number;
  chips: ChipItem[];
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
};

type IntroScene = {
  kind: "intro";
  startSec: number;
  durationSec: number;
  name: string;
  role: string;
  company: string;
};

type CtaScene = {
  kind: "cta";
  startSec: number;
  durationSec: number;
  headline: string;
  phone: string;
  closing?: string;
};

export type Scene = CueScene | ChipsScene | StepScene | IntroScene | CtaScene;

export const SCENES: Scene[] = [
  // 1) Problem-Setup (Stichtag / Zeitdruck)
  { kind: "cue", startSec: 0.1, durationSec: 2.7, word: "Zum Stichtag besenrein", icon: "glanz" },
  { kind: "cue", startSec: 2.9, durationSec: 2.3, word: "Die Zeit wird knapp", icon: "express" },

  // 2) Intro
  {
    kind: "intro",
    startSec: 5.9,
    durationSec: 3.3,
    role: "Wir sind",
    name: "Sauber Entsorgen",
    company: "Deutschlandweit für Gewerbe",
  },

  // 3) Anlässe (B2B)
  { kind: "cue", startSec: 11.8, durationSec: 2.5, word: "Verkaufs- & vermietungsfähig", icon: "check" },
  {
    kind: "chips",
    startSec: 14.5,
    durationSec: 2.2,
    staggerFrames: 13,
    chips: [
      { label: "Firma", icon: "firma" },
      { label: "Praxis", icon: "dokument" },
    ],
  },
  {
    kind: "chips",
    startSec: 16.8,
    durationSec: 2.4,
    staggerFrames: 13,
    chips: [
      { label: "Nach Auszug", icon: "umzug" },
      { label: "Nach Insolvenz", icon: "firma" },
    ],
  },
  { kind: "cue", startSec: 19.4, durationSec: 2.4, word: "Wir übernehmen das – zuverlässig", icon: "partner" },

  // 4) Ablauf / Vorteile
  { kind: "cue", startSec: 25.7, durationSec: 2.3, word: "In wenigen Tagen fertig", icon: "kalender" },
  { kind: "cue", startSec: 28.05, durationSec: 1.95, word: "Zertifizierte Entsorgung", icon: "schild" },
  { kind: "cue", startSec: 30.0, durationSec: 1.9, word: "Nachweis für Ihre Akten", icon: "dokument" },
  { kind: "cue", startSec: 32.0, durationSec: 1.9, word: "Sensible Unterlagen?", icon: "schloss" },
  { kind: "cue", startSec: 33.9, durationSec: 2.7, word: "DSGVO-konform mit Protokoll", icon: "schild" },

  // 5) CTA
  {
    kind: "cta",
    startSec: 40.8,
    durationSec: 4.0,
    headline: "Jetzt eintragen",
    phone: "+49 170 6910315",
    closing: "Wir freuen uns auf dein Projekt.",
  },
];
