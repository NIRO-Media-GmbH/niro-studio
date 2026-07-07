// ============================================================
// Landhaus Wolf — SRT Parser
// Parst Standard-SRT Dateien in typisierte Einträge
// ============================================================

import type { SrtEntry } from "./types";
import { t } from "../components/srt-helpers";

/**
 * Parse a full SRT file string into typed entries.
 * Synchronous — runs at module-level import time.
 *
 * SRT format:
 *   <index>\n
 *   <start> --> <end>\n
 *   <text line 1>\n
 *   [<text line 2>\n]
 *   \n
 */
export function parseSrt(srtContent: string): SrtEntry[] {
  const blocks = srtContent.trim().split(/\n\n+/);
  const entries: SrtEntry[] = [];

  for (const block of blocks) {
    const lines = block.trim().split("\n");
    if (lines.length < 3) continue;

    const index = parseInt(lines[0], 10);
    if (isNaN(index)) continue;

    const timecodeMatch = lines[1].match(
      /(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})/
    );
    if (!timecodeMatch) continue;

    const startSec = t(timecodeMatch[1]);
    const endSec = t(timecodeMatch[2]);
    const text = lines.slice(2).join(" ").trim();

    entries.push({ index, startSec, endSec, text });
  }

  return entries;
}
