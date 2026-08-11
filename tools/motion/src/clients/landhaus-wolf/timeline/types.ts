// ============================================================
// Landhaus Wolf — Timeline Types
// SRT-gesteuerte Overlay-Timeline Typen
// ============================================================

// ---- SRT Entry (parsed from .srt file) ----

export interface SrtEntry {
  /** 1-based SRT cue index */
  index: number;
  /** Start time in seconds */
  startSec: number;
  /** End time in seconds */
  endSec: number;
  /** Subtitle text (multiline joined with space) */
  text: string;
}

// ---- Timeline Entry (discriminated union by component) ----

interface BaseEntry {
  /** Anchor to an SRT cue index (1-based). Overlay starts at this cue's startSec. */
  srtCue: number;
  /**
   * Offset in seconds from the SRT cue start.
   * Positive = delay after cue start. Negative = before cue start.
   * @default 0
   */
  offsetSec?: number;
  /**
   * Duration in seconds. If omitted, uses DEFAULT_DURATIONS for this component.
   */
  durationSec?: number;
  /**
   * Optional label for debugging overlap warnings.
   * If omitted, auto-generated from component + srtCue.
   */
  label?: string;
}

export interface SectionTitleEntry extends BaseEntry {
  component: "SectionTitle";
  props: {
    title: string;
    subtitle?: string;
    position?: "bottom" | "top";
  };
}

export interface StepBadgeEntry extends BaseEntry {
  component: "StepBadge";
  props: {
    step: number;
    label: string;
  };
}

export interface CalloutEntry extends BaseEntry {
  component: "Callout";
  props: {
    text: string;
    subtext?: string;
    position?: "center" | "bottom-right" | "top-right";
  };
}

export interface IngredientListEntry extends BaseEntry {
  component: "IngredientList";
  props: {
    items: string[];
    title?: string;
  };
}

export interface BrandSignOffEntry extends BaseEntry {
  component: "BrandSignOff";
  props?: Record<string, never>;
}

export interface WordByWordEntry extends BaseEntry {
  component: "WordByWord";
  props: {
    text: string;
    highlightColor?: string;
    position?: "center" | "lower";
  };
}

export type TimelineEntry =
  | SectionTitleEntry
  | StepBadgeEntry
  | CalloutEntry
  | IngredientListEntry
  | BrandSignOffEntry
  | WordByWordEntry;

// ---- Default durations per component type (seconds) ----

export const DEFAULT_DURATIONS: Record<TimelineEntry["component"], number> = {
  StepBadge: 5,
  SectionTitle: 3,
  Callout: 4,
  IngredientList: 8,
  BrandSignOff: 6,
  WordByWord: 4,
};

// ---- Resolved sequence (internal, after SRT anchoring) ----

export interface ResolvedSequence {
  /** Absolute start in seconds */
  startSec: number;
  /** Duration in seconds */
  durationSec: number;
  /** Component type */
  component: TimelineEntry["component"];
  /** Props to pass to the component */
  props: Record<string, unknown>;
  /** Debug label */
  label: string;
}
