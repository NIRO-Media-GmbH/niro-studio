// ============================================================
// NIRO Motion Graphics — Color Utilities
// ============================================================

/**
 * Convert hex color to rgba string.
 */
export function hexToRgba(hex: string, alpha: number = 1): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Lighten or darken a hex color by a given amount (-255 to 255).
 */
export function adjustBrightness(hex: string, amount: number): string {
  const num = parseInt(hex.slice(1), 16);
  const r = Math.min(255, Math.max(0, (num >> 16) + amount));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00ff) + amount));
  const b = Math.min(255, Math.max(0, (num & 0x0000ff) + amount));
  return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)}`;
}

/**
 * Generate box-shadow CSS based on intensity level.
 */
export function getShadow(
  intensity: "none" | "light" | "medium" | "heavy",
  color?: string
): string {
  const shadowColor = color ?? "rgba(0, 0, 0, 0.15)";
  switch (intensity) {
    case "none":
      return "none";
    case "light":
      return `0 2px 8px ${shadowColor}`;
    case "medium":
      return `0 4px 16px ${shadowColor}`;
    case "heavy":
      return `0 8px 32px ${shadowColor}, 0 2px 8px ${shadowColor}`;
  }
}
