// ============================================================
// NIRO Motion Graphics — Easing Presets
// Named presets for prompt-friendly usage
// ============================================================

import { Easing } from "remotion";

export const EASING_PRESETS = {
  // Standard
  linear: Easing.linear,
  easeIn: Easing.in(Easing.cubic),
  easeOut: Easing.out(Easing.cubic),
  easeInOut: Easing.inOut(Easing.cubic),

  // Dramatic
  easeInQuart: Easing.in(Easing.poly(4)),
  easeOutQuart: Easing.out(Easing.poly(4)),
  easeInOutQuart: Easing.inOut(Easing.poly(4)),

  // Expressive
  bounce: Easing.bounce,
  elastic: Easing.elastic(1),
  back: Easing.out(Easing.back(1.7)),

  // Motion Design (Material / Apple)
  smooth: Easing.bezier(0.4, 0, 0.2, 1),
  emphasized: Easing.bezier(0.2, 0, 0, 1),
  decelerate: Easing.bezier(0, 0, 0.2, 1),
  accelerate: Easing.bezier(0.4, 0, 1, 1),
  appleEase: Easing.bezier(0.25, 0.1, 0.25, 1),
} as const;

export type EasingPresetName = keyof typeof EASING_PRESETS;

export function getEasing(name: EasingPresetName): (t: number) => number {
  return EASING_PRESETS[name];
}
