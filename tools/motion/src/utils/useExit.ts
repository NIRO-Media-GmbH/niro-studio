// ============================================================
// Shared Exit Animation Hook
// Fades + lifts an element away during the last frames of its
// Sequence. Kanonische Version für neue Kunden — die Kopien in
// src/clients/*/components/useExit.ts sind eingefrorene Alt-
// Varianten mit leicht abweichenden Werten und bleiben unberührt.
// ============================================================

import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

export interface ExitOptions {
  /** Frames vor Sequence-Ende, in denen der Exit läuft */
  exitFrames?: number;
  /** Pixel, um die das Element beim Exit nach unten rutscht */
  slidePx?: number;
}

export function useExit({ exitFrames = 12, slidePx = 24 }: ExitOptions = {}) {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exitStart = Math.max(0, durationInFrames - exitFrames);

  const exitOpacity = interpolate(frame, [exitStart, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const exitSlide = interpolate(
    frame,
    [exitStart, durationInFrames],
    [0, slidePx],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return { exitOpacity, exitSlide };
}
