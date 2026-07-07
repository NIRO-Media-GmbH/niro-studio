// ============================================================
// NIRO Motion Graphics — Font Loader
// Handles both Google Fonts and custom local fonts
// ============================================================

import type { CIFont, CIFonts } from "./types";

const loadedFonts = new Map<string, string>();

/**
 * Load a single CI font. Returns the CSS font-family string.
 * Caches loaded fonts to avoid duplicate loading.
 */
export function loadCIFont(font: CIFont): string {
  const cacheKey = `${font.family}-${font.weight}-${font.style ?? "normal"}`;
  if (loadedFonts.has(cacheKey)) return loadedFonts.get(cacheKey)!;

  // For Google Fonts, we rely on the component-level imports
  // using @remotion/google-fonts. The font-loader returns
  // the family name for CSS usage.
  loadedFonts.set(cacheKey, font.family);
  return font.family;
}

/**
 * Load all CI fonts. Returns a record of role -> CSS font-family.
 */
export function loadAllCIFonts(
  fonts: CIFonts
): Record<string, string> {
  const result: Record<string, string> = {};
  result.heading = loadCIFont(fonts.heading);
  result.body = loadCIFont(fonts.body);
  if (fonts.accent) result.accent = loadCIFont(fonts.accent);
  if (fonts.mono) result.mono = loadCIFont(fonts.mono);
  return result;
}
