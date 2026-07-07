// ============================================================
// Bremsen Schneider — Whisper JSON Parser
// Parses whisper-cpp --output-json-full output into typed data
// ============================================================

export interface WhisperWord {
  text: string;
  startSec: number;
  endSec: number;
}

export interface WhisperSegment {
  startSec: number;
  endSec: number;
  text: string;
  words: WhisperWord[];
}

/** Parse whisper-cpp --output-json-full format */
export function parseWhisperJson(json: {
  transcription: Array<{
    offsets: { from: number; to: number };
    text: string;
    tokens: Array<{
      text: string;
      offsets: { from: number; to: number };
      p: number;
    }>;
  }>;
}): WhisperSegment[] {
  return json.transcription.map((seg) => ({
    startSec: seg.offsets.from / 1000,
    endSec: seg.offsets.to / 1000,
    text: seg.text.trim(),
    words: (seg.tokens || [])
      .filter((t) => !t.text.match(/^\[.*\]$/) && t.text.trim().length > 0)
      .map((t) => ({
        text: t.text.trim(),
        startSec: t.offsets.from / 1000,
        endSec: t.offsets.to / 1000,
      })),
  }));
}
