// ============================================================
// REM Malerfachbetrieb — Overlay Shared Constants
// CI aus brand.json / rem-maler.de: REM-Rot auf hellen Karten,
// kantige Ecken (borderRadius ~0), Inter.
// ============================================================

export const RED = "#D83C31"; // primary — auch Ton für NEGATIVE Aussagen
export const RED_LIGHT = "#F05545"; // accent / glow
export const GREEN = "#2E9E5B"; // Ton für POSITIVE Aussagen
export const GREEN_LIGHT = "#43C97A";
export const INK = "#1A1A2E"; // dunkles Anthrazit (Text)
export const GRAY = "#8A8F98"; // neutral
export const WHITE = "#FFFFFF";

// Kantiger REM-Look: kleine Radien statt Pillen
export const RADIUS = 8;
export const BADGE_RADIUS = 6;

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
