// ============================================================
// NIRO Motion Graphics — Design Tokens / Theme
// All sizes are relative to canvas dimensions for responsiveness
// ============================================================

export const DEFAULT_THEME = {
  spacing: {
    xs: 8,
    sm: 16,
    md: 24,
    lg: 40,
    xl: 64,
    xxl: 96,
  },
  /** Font size ratios relative to canvas height */
  typography: {
    h1: 0.08,
    h2: 0.06,
    h3: 0.045,
    body: 0.035,
    caption: 0.025,
    label: 0.02,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 16,
    xl: 24,
    full: 9999,
  },
  animation: {
    defaultStagger: 3,
    defaultSpringDamping: 14,
    defaultSpringStiffness: 120,
    defaultSpringMass: 1,
    defaultFadeDurationSeconds: 0.3,
  },
} as const;
