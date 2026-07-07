// ============================================================
// NIRO Motion Graphics — Core Type Definitions
// ============================================================

// --- Corporate Identity ---

export interface CIColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  text: string;
  success?: string;
  warning?: string;
  error?: string;
  muted?: string;
}

export interface CIFont {
  family: string;
  weight: string;
  style?: string;
  googleFont?: boolean;
  localPath?: string;
}

export interface CIFonts {
  heading: CIFont;
  body: CIFont;
  accent?: CIFont;
  mono?: CIFont;
}

export interface CILogo {
  path: string;
  safeZone: number;
  aspectRatio?: number;
}

export interface CIStyle {
  borderRadius: number;
  shadowIntensity: "none" | "light" | "medium" | "heavy";
  animationSpeed: "slow" | "normal" | "fast";
}

export interface CorporateIdentity {
  name: string;
  slug: string;
  colors: CIColors;
  fonts: CIFonts;
  logo: CILogo;
  style: CIStyle;
}

// --- Format & Rendering ---

export type VideoFormat = "landscape" | "portrait" | "portrait-4k" | "landscape-4k";
export type FPSOption = 24 | 25 | 30 | 60;

export interface FormatDimensions {
  width: number;
  height: number;
}

export interface ProjectConfig {
  format: VideoFormat;
  fps: FPSOption;
  durationInSeconds: number;
  transparent: boolean;
  clientSlug: string;
  projectSlug: string;
}

// --- Animation ---

export type Direction = "left" | "right" | "up" | "down";
export type AnimationMode = "word" | "character" | "line";
export type EasingPreset =
  | "linear"
  | "easeIn"
  | "easeOut"
  | "easeInOut"
  | "bounce"
  | "elastic"
  | "spring"
  | "smooth"
  | "emphasized"
  | "back";

export interface StaggerConfig {
  delayPerItem: number;
  initialDelay: number;
}

export interface SpringConfig {
  damping: number;
  mass: number;
  stiffness: number;
  overshootClamping: boolean;
}
