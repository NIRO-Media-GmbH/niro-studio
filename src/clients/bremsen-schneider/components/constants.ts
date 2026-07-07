// ============================================================
// Bremsen Schneider — Shared Constants
// ============================================================

export const BLUE = "#006BBB";
export const DARK_BLUE = "#004A82";
export const YELLOW = "#F0D309";
export const WHITE = "#FFFFFF";

// Safe zone boundaries (fractional, for 9:16)
export const SAFE = {
  top: 0.07,
  bottom: 0.575,
  left: 0.05,
  right: 0.95,
} as const;

// Spring configs
export const SNAP_SPRING = { damping: 10, stiffness: 200, mass: 1 };
export const SMOOTH_SPRING = { damping: 14, stiffness: 120, mass: 1 };
export const PUNCH_SPRING = { damping: 8, stiffness: 180, mass: 1 };
export const GENTLE_SPRING = { damping: 22, stiffness: 100, mass: 1 };

// Exit animation lead (frames before scene end)
export const EXIT_LEAD = 10;
