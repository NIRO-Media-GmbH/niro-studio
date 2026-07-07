// ============================================================
// Sauber Entsorgen — Reel 1 (9:16) "Haushaltsauflösung"
// 1080×1920, 25fps, ~61s. Transparent alpha overlay.
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
  // 1) Problem-Setup
  {
    kind: "chips",
    startSec: 0.24,
    durationSec: 3.6,
    staggerFrames: 13,
    chips: [
      { label: "Wohnung", icon: "wohnung" },
      { label: "Haus", icon: "haus" },
      { label: "Garage", icon: "garage" },
    ],
  },
  { kind: "cue", startSec: 3.9, durationSec: 2.6, word: "Wie schaffst du das allein?", icon: "frage" },

  // 2) Intro
  {
    kind: "intro",
    startSec: 6.9,
    durationSec: 3.0,
    role: "Wir sind",
    name: "Sauber Entsorgen",
    company: "aus Idar-Oberstein",
  },
  { kind: "cue", startSec: 9.7, durationSec: 2.6, word: "Wir räumen weg, was weg muss", icon: "lkw" },

  // 3) Anlässe
  { kind: "cue", startSec: 18.6, durationSec: 2.8, word: "Neues Haus, alte Sachen?", icon: "schluessel" },
  {
    kind: "chips",
    startSec: 21.7,
    durationSec: 2.8,
    staggerFrames: 14,
    chips: [
      { label: "Keller", icon: "keller" },
      { label: "Dachboden", icon: "dachboden" },
    ],
  },
  { kind: "cue", startSec: 25.1, durationSec: 2.0, word: "Haushaltsauflösung", icon: "haus" },
  {
    kind: "chips",
    startSec: 27.1,
    durationSec: 2.5,
    staggerFrames: 14,
    chips: [
      { label: "Nach Umzug", icon: "umzug" },
      { label: "Nach Trauerfall", icon: "herz" },
    ],
  },
  { kind: "cue", startSec: 29.8, durationSec: 1.5, word: "Wir sind für dich da", icon: "partner" },

  // 4) Ablauf
  {
    kind: "step",
    startSec: 31.4,
    durationSec: 4.1,
    number: "1",
    title: "Besichtigung",
    subtitle: "Kostenlos & unverbindlich",
    icon: "auge",
  },
  {
    kind: "step",
    startSec: 35.7,
    durationSec: 2.5,
    number: "2",
    title: "Festpreis – schriftlich",
    icon: "preis",
  },
  {
    kind: "step",
    startSec: 38.4,
    durationSec: 3.0,
    number: "3",
    title: "Fertig in 1–3 Tagen",
    icon: "kalender",
  },

  // 5) Versprechen
  { kind: "cue", startSec: 41.5, durationSec: 2.3, word: "Keinen Finger rühren", icon: "lkw" },
  { kind: "cue", startSec: 43.9, durationSec: 2.4, word: "Besenrein & korrekt entsorgt", icon: "glanz" },
  { kind: "cue", startSec: 46.4, durationSec: 1.5, word: "Mit Nachweis", icon: "dokument" },
  { kind: "cue", startSec: 48.1, durationSec: 2.5, word: "Nichts muss dir peinlich sein", icon: "herz" },
  { kind: "cue", startSec: 50.7, durationSec: 1.9, word: "Diskret & ohne Urteil", icon: "schloss" },
  { kind: "cue", startSec: 52.6, durationSec: 2.6, word: "Wir haben schon alles gesehen", icon: "auge" },

  // 6) CTA
  {
    kind: "cta",
    startSec: 55.4,
    durationSec: 5.6,
    headline: "Jetzt eintragen",
    phone: "+49 170 6910315",
    closing: "Wir freuen uns auf dein Projekt.",
  },
];
