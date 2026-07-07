// ============================================================
// WTN (Werkzeugtechnik Niederstetten) — Shared Constants
// Colors from the official WTN brand guide (not just the logo):
//   LIME  #D8DD53  — signature accent (emphasis, badges, CTA pills)
//   BLUE  #254478 / DARK_BLUE #131F32 / OFF_BLACK #0A121F — surfaces
//   LIGHT_BLUE #7A90A8 — muted accent  ·  OFF_WHITE #F6F7ED — text
// Font: "Robout" (local brand typeface, see fonts.ts).
// Claim: "Know-how perfektioniert."  ·  Ton: "Werde Teil der WTN Familie."
// ============================================================

export const LIME = "#D8DD53"; // signature accent
export const LIME_DEEP = "#B8BE3B"; // lime shadow / gradient end
export const BLUE = "#254478"; // surfaces
export const DARK_BLUE = "#131F32"; // primary card / pill bg
export const OFF_BLACK = "#0A121F"; // deepest bg / text
export const LIGHT_BLUE = "#7A90A8"; // muted accent / secondary text
export const OFF_WHITE = "#F6F7ED"; // primary text on dark
export const WHITE = "#FFFFFF";
export const INK = OFF_BLACK; // text token (kept for compatibility)

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

// The WTN signet is a grid of slanted bars leaning right. We echo that
// motif in reveals + accents. This is the shear used for accent bars.
export const SIGNET_SKEW = -12; // deg (matches the logo's forward lean)

// Spring configs. WTN brief = "fresh, cool, krank" → snappy, small
// overshoot (face-zone-safe).
export const PUNCH_SPRING = { damping: 13, stiffness: 210, mass: 1 };
export const SMOOTH_SPRING = { damping: 16, stiffness: 150, mass: 1 };
export const GENTLE_SPRING = { damping: 22, stiffness: 110, mass: 1 };
export const PULSE_SPRING = { damping: 10, stiffness: 220, mass: 0.9 };

// Soft lime glow used on emphasis words / logo reveal / badges
export const GLOW_LIME = "rgba(216,221,83,0.6)";

// Frosted dark-card shadow tuned to the navy palette
export const CARD_SHADOW =
  "0 18px 50px rgba(0,0,0,0.42), 0 4px 14px rgba(0,0,0,0.30)";

// Card background (navy, near-opaque so it reads over any footage)
export const CARD_BG = "rgba(19,31,50,0.92)"; // DARK_BLUE @ .92

// Exit animation lead (frames before a Sequence ends)
export const EXIT_LEAD = 9;
