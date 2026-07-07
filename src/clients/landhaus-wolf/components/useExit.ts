import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

/** Shared exit animation — fade out + slide down in the last N frames */
export const useExit = (exitFrames = 12) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exitStart = Math.max(0, durationInFrames - exitFrames);
  const exitEnd = Math.max(exitStart + 1, durationInFrames);
  const exitProg = interpolate(frame, [exitStart, exitEnd], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitSlide = interpolate(exitProg, [0, 1], [14, 0]);
  return { exitProg, exitSlide };
};
