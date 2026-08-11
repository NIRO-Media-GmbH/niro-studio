// ============================================================
// NIRO Motion Graphics — Animation Helper Functions
// Reusable animation patterns for all components
// ============================================================

import { interpolate, spring } from "remotion";
import type { EasingPresetName } from "./easing";
import { getEasing } from "./easing";
import type { Direction } from "../core/types";

/**
 * Convert seconds to frames (FPS-independent timing).
 */
export function secondsToFrames(seconds: number, fps: number): number {
  return Math.round(seconds * fps);
}

/**
 * Spring animation with sensible motion graphics defaults.
 * Returns 0→1 with natural easing.
 */
export function motionSpring(
  frame: number,
  fps: number,
  options?: {
    delay?: number;
    damping?: number;
    mass?: number;
    stiffness?: number;
    overshootClamping?: boolean;
  }
): number {
  return spring({
    frame: frame - (options?.delay ?? 0),
    fps,
    config: {
      damping: options?.damping ?? 14,
      mass: options?.mass ?? 1,
      stiffness: options?.stiffness ?? 120,
      overshootClamping: options?.overshootClamping ?? false,
    },
  });
}

/**
 * Staggered spring for arrays of elements.
 * Each element starts `staggerDelay` frames after the previous.
 */
export function staggeredSpring(
  frame: number,
  fps: number,
  index: number,
  staggerDelay: number = 3,
  initialDelay: number = 0,
  springConfig?: {
    damping?: number;
    mass?: number;
    stiffness?: number;
  }
): number {
  return motionSpring(frame, fps, {
    delay: initialDelay + index * staggerDelay,
    ...springConfig,
  });
}

/**
 * Fade in/out envelope. Returns opacity 0→1→1→0.
 */
export function fadeInOut(
  frame: number,
  fps: number,
  durationInFrames: number,
  fadeInSeconds: number = 0.3,
  fadeOutSeconds: number = 0.3,
  easing: EasingPresetName = "smooth"
): number {
  const fadeInFrames = secondsToFrames(fadeInSeconds, fps);
  const fadeOutFrames = secondsToFrames(fadeOutSeconds, fps);
  const easingFn = getEasing(easing);

  return interpolate(
    frame,
    [0, fadeInFrames, durationInFrames - fadeOutFrames, durationInFrames],
    [0, 1, 1, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: easingFn,
    }
  );
}

/**
 * Calculate slide offset for a given direction.
 * Returns {x, y} displacement that animates from `distance` to 0.
 */
export function slideOffset(
  frame: number,
  fps: number,
  direction: Direction,
  distance: number = 200,
  delay: number = 0
): { x: number; y: number } {
  const progress = motionSpring(frame, fps, { delay, damping: 14 });
  const remaining = distance * (1 - progress);

  switch (direction) {
    case "left":
      return { x: -remaining, y: 0 };
    case "right":
      return { x: remaining, y: 0 };
    case "up":
      return { x: 0, y: remaining };
    case "down":
      return { x: 0, y: -remaining };
  }
}

/**
 * Speed multiplier based on CI animation speed setting.
 */
export function getSpeedMultiplier(
  speed: "slow" | "normal" | "fast"
): number {
  const map = { slow: 1.5, normal: 1, fast: 0.7 };
  return map[speed];
}
