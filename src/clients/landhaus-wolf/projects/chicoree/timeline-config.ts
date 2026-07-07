import type { TimelineEntry } from "../../timeline/types";

/**
 * Chicorée — Overlay Timeline
 *
 * Jeder Eintrag ist an einen SRT-Cue verankert (1-basiert).
 * offsetSec verschiebt relativ zum Cue-Start.
 * durationSec überschreibt den Default für den Component-Typ.
 */
export const TIMELINE: TimelineEntry[] = [
  // ===== INTRO (Cue 1: 0:00) =====
  {
    srtCue: 1,
    component: "SectionTitle",
    props: { title: "Chicorée", subtitle: "Karamellisiert fürs Gourmet" },
    durationSec: 4,
  },
  {
    srtCue: 1,
    component: "Callout",
    props: {
      text: "Gourmet?",
      subtext: "Chicorée im Restaurant",
      position: "top-right",
    },
    durationSec: 4,
  },

  // ===== STEP 1: ZUTATEN (Cue 2: 0:04) =====
  {
    srtCue: 2,
    offsetSec: 1,
    component: "StepBadge",
    props: { step: 1, label: "Zutaten" },
    durationSec: 4,
  },
  {
    srtCue: 2,
    offsetSec: 1,
    component: "SectionTitle",
    props: { title: "Besondere Zutaten", subtitle: "Aus der Schatzkammer" },
    durationSec: 4,
  },
  {
    srtCue: 3,
    offsetSec: 1,
    component: "IngredientList",
    props: {
      items: [
        "Weißer Portwein",
        "Orangensaft",
        "76er Riesling Auslese",
        "Zucker",
      ],
    },
    durationSec: 10,
  },

  // ===== STEP 2: SCHNEIDEN (Cue 5: 0:19) =====
  {
    srtCue: 5,
    offsetSec: 1,
    component: "StepBadge",
    props: { step: 2, label: "Schneiden" },
  },
  {
    srtCue: 5,
    offsetSec: 1,
    component: "SectionTitle",
    props: { title: "Vierteln & schneiden", subtitle: "Strunk entfernen" },
    durationSec: 3,
  },
  {
    srtCue: 6,
    component: "SectionTitle",
    props: { title: "Grob schneiden", subtitle: "Strunk vorher entfernen" },
    durationSec: 4,
  },

  // ===== STEP 3: KARAMELLISIEREN (Cue 7: 0:31) =====
  {
    srtCue: 7,
    component: "StepBadge",
    props: { step: 3, label: "Karamellisieren" },
  },
  {
    srtCue: 7,
    component: "SectionTitle",
    props: { title: "Zucker karamellisieren", subtitle: "Im Topf" },
    durationSec: 3,
  },
  {
    srtCue: 8,
    component: "Callout",
    props: {
      text: "Karamell",
      subtext: "Leicht karamellisieren",
      position: "top-right",
    },
  },

  // ===== STEP 4: ABLÖSCHEN (Cue 9: 0:39) =====
  {
    srtCue: 9,
    component: "StepBadge",
    props: { step: 4, label: "Ablöschen" },
  },
  {
    srtCue: 9,
    component: "SectionTitle",
    props: {
      title: "Ablöschen",
      subtitle: "Portwein · Orangensaft · Riesling",
    },
    durationSec: 3,
  },
  {
    srtCue: 10,
    component: "SectionTitle",
    props: {
      title: "Ablösch-Reihenfolge",
      subtitle: "Portwein · OJ · 76er Riesling",
    },
    durationSec: 4,
  },

  // ===== STEP 5: CHICORÉE ZUGEBEN (Cue 13: 1:00) =====
  {
    srtCue: 13,
    component: "StepBadge",
    props: { step: 5, label: "Chicorée zugeben" },
  },
  {
    srtCue: 13,
    component: "SectionTitle",
    props: {
      title: "Chicorée ins Karamell",
      subtitle: "Karamellschicht lösen",
    },
    durationSec: 3,
  },
  {
    srtCue: 14,
    component: "Callout",
    props: {
      text: "Garen",
      subtext: "Im Karamell garen",
      position: "bottom-right",
    },
  },

  // ===== ABSCHLUSS (Cue 15: 1:10) =====
  {
    srtCue: 15,
    component: "Callout",
    props: {
      text: "Ab Mittwoch!",
      subtext: "Im Gourmet Restaurant",
      position: "center",
    },
    durationSec: 5,
  },

  // ===== SIGN-OFF =====
  {
    srtCue: 15,
    offsetSec: 6,
    component: "BrandSignOff",
  },
];
