// ============================================================
// Sauber Entsorgen — Exit Animation Hook
// Fades + lifts an element away during the last frames of its Sequence
// ============================================================

import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { EXIT_LEAD } from "./constants";

export function useExit(exitFrames = EXIT_LEAD) {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exitStart = Math.max(0, durationInFrames - exitFrames);

  const exitOpacity = interpolate(
    frame,
    [exitStart, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const exitSlide = interpolate(
    frame,
    [exitStart, durationInFrames],
    [0, 26],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return { exitOpacity, exitSlide };
}
