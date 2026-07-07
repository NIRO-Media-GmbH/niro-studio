// ============================================================
// Sauber Entsorgen — Shared Constants
// Brand colors sampled from the logo SVG (#3B5998 / #9CA3AF)
// ============================================================

export const BLUE = "#3B5998"; // primary (logo)
export const BLUE_LIGHT = "#5B86D6"; // accent / glow
export const GRAY = "#9CA3AF"; // secondary (logo)
export const INK = "#2B3140"; // anthracite text
export const WHITE = "#FFFFFF";

// Safe zone boundaries (fractional, for 16:9 landscape — title-safe)
export const SAFE = {
  top: 0.05,
  bottom: 0.93,
  left: 0.05,
  right: 0.95,
} as const;

// Spring configs
export const SNAP_SPRING = { damping: 11, stiffness: 200, mass: 1 };
export const SMOOTH_SPRING = { damping: 15, stiffness: 130, mass: 1 };
export const PUNCH_SPRING = { damping: 9, stiffness: 190, mass: 1 };
export const GENTLE_SPRING = { damping: 22, stiffness: 110, mass: 1 };

// Exit animation lead (frames before scene end)
export const EXIT_LEAD = 9;
