// ============================================================
// Landhaus Wolf — Timeline Renderer
// Rendert TimelineEntry[] → Remotion <Sequence> Elemente
// ============================================================

import React, { useMemo } from "react";
import { Sequence, useVideoConfig } from "remotion";
import type { SrtEntry, TimelineEntry, ResolvedSequence } from "./types";
import { DEFAULT_DURATIONS } from "./types";
import { detectOverlaps, logOverlaps } from "./overlap-detect";

import { SectionTitle } from "../components/SectionTitle";
import { StepBadge } from "../components/StepBadge";
import { Callout } from "../components/Callout";
import { IngredientList } from "../components/IngredientList";
import { BrandSignOff } from "../components/BrandSignOff";
import { WordByWord } from "../components/WordByWord";

const COMPONENT_MAP: Record<string, React.ComponentType<any>> = {
  SectionTitle,
  StepBadge,
  Callout,
  IngredientList,
  BrandSignOff,
  WordByWord,
};

interface TimelineRendererProps {
  srt: SrtEntry[];
  timeline: TimelineEntry[];
  /** Log overlap warnings to console. @default true */
  warnOverlaps?: boolean;
}

/**
 * Resolve timeline entries to absolute positions using SRT anchoring.
 */
function resolveTimeline(
  srt: SrtEntry[],
  timeline: TimelineEntry[]
): ResolvedSequence[] {
  const srtMap = new Map<number, SrtEntry>();
  for (const entry of srt) {
    srtMap.set(entry.index, entry);
  }

  return timeline.map((entry, i) => {
    const cue = srtMap.get(entry.srtCue);
    if (!cue) {
      console.error(
        `[Timeline] Entry ${i} referenziert srtCue ${entry.srtCue}, der nicht existiert.`
      );
      return {
        startSec: 0,
        durationSec: entry.durationSec ?? DEFAULT_DURATIONS[entry.component],
        component: entry.component,
        props: "props" in entry && entry.props ? entry.props : {},
        label: entry.label ?? `${entry.component}@cue${entry.srtCue}`,
      };
    }

    const startSec = cue.startSec + (entry.offsetSec ?? 0);
    const durationSec =
      entry.durationSec ?? DEFAULT_DURATIONS[entry.component];

    return {
      startSec,
      durationSec,
      component: entry.component,
      props: "props" in entry && entry.props ? entry.props : {},
      label:
        entry.label ??
        `${entry.component}@cue${entry.srtCue}` +
          (entry.offsetSec ? `+${entry.offsetSec}s` : ""),
    };
  });
}

export const TimelineRenderer: React.FC<TimelineRendererProps> = ({
  srt,
  timeline,
  warnOverlaps = true,
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);

  const resolved = useMemo(
    () => resolveTimeline(srt, timeline),
    [srt, timeline]
  );

  // Overlap detection (runs once per mount)
  useMemo(() => {
    if (warnOverlaps) {
      const warnings = detectOverlaps(resolved);
      logOverlaps(warnings);
    }
  }, [resolved, warnOverlaps]);

  return (
    <>
      {resolved.map((seq, i) => {
        const Component = COMPONENT_MAP[seq.component];
        if (!Component) return null;

        return (
          <Sequence
            key={`${seq.label}-${i}`}
            from={s(seq.startSec)}
            durationInFrames={s(seq.durationSec)}
            name={seq.label}
          >
            <Component {...seq.props} />
          </Sequence>
        );
      })}
    </>
  );
};
