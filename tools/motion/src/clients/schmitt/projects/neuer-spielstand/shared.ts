// Gemeinsame Bausteine für „Neuer Spielstand“: CI, Schrift, Asset-Pfade, Easing
import { Easing, staticFile } from "remotion";
import { loadFont } from "@remotion/google-fonts/BarlowCondensed";
import { loadBrand } from "../../../../core/ci-loader";
import brandJson from "../../brand.json";

export const ci = loadBrand("schmitt", brandJson as any);
export const { fontFamily } = loadFont("normal", {
  weights: ["500", "600", "700", "800"],
  subsets: ["latin", "latin-ext"],
});

// Assets: public/projects/schmitt-ki-game-video → Charge/Material/Video
export const asset = (p: string) => staticFile(`projects/schmitt-ki-game-video/${p}`);

export const easeOut = Easing.bezier(0.2, 0.7, 0.2, 1);
export const easeIn = Easing.bezier(0.55, 0, 0.9, 0.4);
export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
// CSS-`scale` immer als String: React 18 hängt an Zahlen „px“ an, der Wert wäre ungültig
export const sc = (n: number) => String(n);
export const NAVY = "#131B2E";
