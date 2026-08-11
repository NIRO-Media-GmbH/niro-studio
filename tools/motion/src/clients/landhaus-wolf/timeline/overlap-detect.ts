// ============================================================
// Landhaus Wolf — Overlap Detection
// Zone-basierte Kollisionserkennung für Timeline-Einträge
// ============================================================

import type { ResolvedSequence } from "./types";

export interface OverlapWarning {
  a: ResolvedSequence;
  b: ResolvedSequence;
  overlapSec: number;
}

/**
 * Get the screen zone for a resolved sequence.
 *
 * Zone layout:
 *   top-left:     StepBadge
 *   bottom-left:  SectionTitle (default position)
 *   top-right:    Callout(top-right), IngredientList
 *   bottom-right: Callout(bottom-right)
 *   center:       Callout(center), BrandSignOff
 *   lower-center: WordByWord(lower)
 */
function getZone(seq: ResolvedSequence): string {
  const p = seq.props as Record<string, unknown>;
  switch (seq.component) {
    case "StepBadge":
      return "top-left";
    case "SectionTitle":
      return p.position === "top" ? "top-left" : "bottom-left";
    case "Callout":
      return (p.position as string) ?? "center";
    case "IngredientList":
      return "top-right";
    case "BrandSignOff":
      return "center";
    case "WordByWord":
      return p.position === "lower" ? "lower-center" : "center";
    default:
      return "unknown";
  }
}

/**
 * Detect overlapping sequences within the same screen zone.
 * Cross-zone overlaps are intentionally ignored (e.g. StepBadge + Callout).
 */
export function detectOverlaps(
  sequences: ResolvedSequence[]
): OverlapWarning[] {
  const warnings: OverlapWarning[] = [];

  // Group by zone
  const zones = new Map<string, ResolvedSequence[]>();
  for (const seq of sequences) {
    const zone = getZone(seq);
    if (!zones.has(zone)) zones.set(zone, []);
    zones.get(zone)!.push(seq);
  }

  // Check pairs within each zone
  for (const [, group] of zones) {
    const sorted = [...group].sort((a, b) => a.startSec - b.startSec);
    for (let i = 0; i < sorted.length - 1; i++) {
      const a = sorted[i];
      const b = sorted[i + 1];
      const aEnd = a.startSec + a.durationSec;
      if (aEnd > b.startSec) {
        warnings.push({ a, b, overlapSec: aEnd - b.startSec });
      }
    }
  }

  return warnings;
}

/** Log overlap warnings to console (visible in Remotion Studio) */
export function logOverlaps(warnings: OverlapWarning[]): void {
  if (warnings.length === 0) return;
  console.warn(`[Timeline] ${warnings.length} Overlap(s) erkannt:`);
  for (const w of warnings) {
    console.warn(
      `  OVERLAP: "${w.a.label}" (${w.a.startSec.toFixed(1)}s–${(w.a.startSec + w.a.durationSec).toFixed(1)}s) ` +
        `überschneidet "${w.b.label}" (${w.b.startSec.toFixed(1)}s–${(w.b.startSec + w.b.durationSec).toFixed(1)}s) ` +
        `um ${w.overlapSec.toFixed(2)}s`
    );
  }
}
