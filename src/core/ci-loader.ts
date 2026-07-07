// ============================================================
// NIRO Motion Graphics — CI Loader
// Converts a simple brand.json into a full CorporateIdentity
// ============================================================

import type { CorporateIdentity } from "./types";

/**
 * A brand.json file has this simple structure:
 */
export interface BrandJSON {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
  };
  fonts: {
    heading: string;
    body: string;
  };
  logo: string;
  style: {
    borderRadius: number;
    animationSpeed: "slow" | "normal" | "fast";
  };
}

/**
 * Turn a brand.json object into a full CorporateIdentity.
 * Called once per client, usually at import time.
 */
export function loadBrand(
  slug: string,
  brand: BrandJSON
): CorporateIdentity {
  return {
    name: brand.name,
    slug,
    colors: {
      primary: brand.colors.primary,
      secondary: brand.colors.secondary,
      accent: brand.colors.accent,
      background: brand.colors.background,
      text: brand.colors.text,
    },
    fonts: {
      heading: {
        family: brand.fonts.heading,
        weight: "700",
        googleFont: true,
      },
      body: {
        family: brand.fonts.body,
        weight: "400",
        googleFont: true,
      },
    },
    logo: {
      path: brand.logo,
      safeZone: 40,
    },
    style: {
      borderRadius: brand.style.borderRadius,
      shadowIntensity: "medium",
      animationSpeed: brand.style.animationSpeed,
    },
  };
}
