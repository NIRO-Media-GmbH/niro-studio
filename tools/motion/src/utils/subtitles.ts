// ============================================================
// Shared SRT Utilities
// Parst Standard-SRT-Dateien in typisierte Einträge — für alle
// Kunden mit untertitel-/timeline-gesteuerten Kompositionen.
// (Herkunft: src/clients/landhaus-wolf/timeline/, dort jetzt
// re-exportiert.)
// ============================================================

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

/** SRT-Timecode ("00:01:23,456") → Sekunden */
export const srtTimeToSeconds = (srtTime: string): number => {
  const [h, m, rest] = srtTime.split(":");
  const [s, ms] = rest.split(",");
  return Number(h) * 3600 + Number(m) * 60 + Number(s) + Number(ms) / 1000;
};

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

    const startSec = srtTimeToSeconds(timecodeMatch[1]);
    const endSec = srtTimeToSeconds(timecodeMatch[2]);
    const text = lines.slice(2).join(" ").trim();

    entries.push({ index, startSec, endSec, text });
  }

  return entries;
}
