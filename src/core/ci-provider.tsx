// ============================================================
// NIRO Motion Graphics — Corporate Identity Provider
// Wrap compositions in <CIProvider ci={clientCI}> to make
// brand colors, fonts, logo available to all children via useCI()
// ============================================================

import React, { createContext, useContext, useMemo } from "react";
import type { CorporateIdentity, CIColors, CIFonts, CIStyle } from "./types";

// --- Default CI (beautiful defaults when no client is active) ---

export const defaultCI: CorporateIdentity = {
  name: "Default",
  slug: "default",
  colors: {
    primary: "#3B82F6",
    secondary: "#1E293B",
    accent: "#F59E0B",
    background: "#FFFFFF",
    text: "#0F172A",
    muted: "#94A3B8",
  },
  fonts: {
    heading: { family: "Inter", weight: "700", googleFont: true },
    body: { family: "Inter", weight: "400", googleFont: true },
  },
  logo: { path: "", safeZone: 40 },
  style: {
    borderRadius: 8,
    shadowIntensity: "medium",
    animationSpeed: "normal",
  },
};

// --- Context ---

const CIContext = createContext<CorporateIdentity>(defaultCI);

export const CIProvider: React.FC<{
  ci?: CorporateIdentity;
  children: React.ReactNode;
}> = ({ ci, children }) => {
  const value = useMemo(() => ci ?? defaultCI, [ci]);
  return <CIContext.Provider value={value}>{children}</CIContext.Provider>;
};

// --- Hooks ---

export const useCI = (): CorporateIdentity => useContext(CIContext);
export const useCIColors = (): CIColors => useCI().colors;
export const useCIFonts = (): CIFonts => useCI().fonts;
export const useCIStyle = (): CIStyle => useCI().style;
