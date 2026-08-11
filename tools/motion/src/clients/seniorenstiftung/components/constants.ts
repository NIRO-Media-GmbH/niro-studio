// ============================================================
// Seniorenstiftung Prenzlauer Berg — Shared Constants
// Primary color = exact logo teal (#0E7EBE).
// ============================================================

export const TEAL = "#0E7EBE"; // primary (logo)
export const TEAL_DARK = "#0B5E8F"; // deep variant
export const TEAL_LIGHT = "#3AA5D8"; // accent / glow
export const INK = "#1E2A32"; // dark text
export const WHITE = "#FFFFFF";

// Reels safe zone (fractional). Content lives BELOW the face zone,
// ABOVE the IG/TikTok bottom UI. See CLAUDE.md safe-zone system.
export const SAFE = {
  top: 0.07,
  bottom: 0.575,
  left: 0.05,
  right: 0.95,
} as const;

// Default vertical anchor for overlay pills: element bottom at this
// fraction of height from the bottom (~mid-screen, clear of face zone).
export const CONTENT_BOTTOM = 0.42;

// Spring configs (calm, premium — small overshoot, face-zone-safe)
export const PUNCH_SPRING = { damping: 12, stiffness: 190, mass: 1 };
export const SMOOTH_SPRING = { damping: 16, stiffness: 130, mass: 1 };
export const GENTLE_SPRING = { damping: 22, stiffness: 110, mass: 1 };
// v2: warm default enter — softer than PUNCH, still lively
export const WARM_SPRING = { damping: 16, stiffness: 150, mass: 1 };
// v2: emphasis pulse (short, springy, subtle overshoot)
export const PULSE_SPRING = { damping: 10, stiffness: 210, mass: 0.9 };

// v2: soft teal glow used on emphasis words / logo reveal
export const GLOW_TEAL = "rgba(58,165,216,0.55)";

// Exit animation lead (frames before a Sequence ends)
export const EXIT_LEAD = 9;
