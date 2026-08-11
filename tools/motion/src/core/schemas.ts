// ============================================================
// NIRO Motion Graphics — Zod Schemas
// Powers Studio visual editing + type validation
// ============================================================

import { z } from "zod";
import { zColor, zTextarea } from "@remotion/zod-types";

// --- Base Schemas ---

export const formatSchema = z.enum(["landscape", "portrait", "portrait-4k", "landscape-4k"]);
export const fpsSchema = z.union([
  z.literal(24),
  z.literal(25),
  z.literal(30),
  z.literal(60),
]);
export const directionSchema = z.enum(["left", "right", "up", "down"]);
export const animationModeSchema = z.enum(["word", "character", "line"]);

// --- CI Schemas ---

export const ciColorsSchema = z.object({
  primary: zColor(),
  secondary: zColor(),
  accent: zColor(),
  background: zColor(),
  text: zColor(),
});

// --- Spring Config Schema ---

export const springConfigSchema = z.object({
  damping: z.number().min(1).max(200),
  mass: z.number().min(0.1).max(10),
  stiffness: z.number().min(1).max(500),
  overshootClamping: z.boolean(),
});

// --- Stagger Schema ---

export const staggerSchema = z.object({
  delayPerItem: z.number().min(0).max(60),
  initialDelay: z.number().min(0).max(120),
});

// --- Review Overlay Schema ---

export const faceZoneSchema = z.object({
  top: z.number().min(0).max(1).step(0.01).describe("Oben (0-1)"),
  bottom: z.number().min(0).max(1).step(0.01).describe("Unten (0-1)"),
  left: z.number().min(0).max(1).step(0.01).describe("Links (0-1)"),
  right: z.number().min(0).max(1).step(0.01).describe("Rechts (0-1)"),
});

export const reviewConfigSchema = z.object({
  showGuides: z.boolean().describe("Review-Overlay anzeigen"),
  showSafeZone: z.boolean().describe("Safe Zone anzeigen"),
  showFaceZone: z.boolean().describe("Gesichts-Zone anzeigen"),
  showGrid: z.boolean().describe("Drittel-Raster anzeigen"),
  faceZone: faceZoneSchema.optional().describe("Benutzerdefinierte Gesichts-Zone"),
  guideOpacity: z.number().min(0.05).max(1).step(0.05).describe("Guide Transparenz"),
});

// --- Project-Level Schema (used in calculateMetadata) ---

export const projectPropsSchema = z.object({
  format: formatSchema,
  fps: fpsSchema,
  durationInSeconds: z.number().min(0.5).max(300),
  transparent: z.boolean(),
  review: reviewConfigSchema.optional().describe("Review-Overlay Einstellungen"),
});

// --- Text Component Schemas ---

export const fadeInTextSchema = z.object({
  text: zTextarea(),
  mode: animationModeSchema,
  stagger: staggerSchema,
  fontSizeRatio: z.number().min(0.01).max(0.2),
  color: zColor().optional(),
  fontWeight: z.string(),
  textAlign: z.enum(["left", "center", "right"]),
  direction: directionSchema,
  distance: z.number().min(0).max(200),
});

export const typewriterTextSchema = z.object({
  text: zTextarea(),
  charsPerSecond: z.number().min(1).max(100),
  cursorColor: zColor(),
  cursorWidth: z.number().min(1).max(10),
  showCursorAfterComplete: z.boolean(),
  fontSizeRatio: z.number().min(0.01).max(0.2),
  color: zColor().optional(),
  fontWeight: z.string(),
});

export const slideInTextSchema = z.object({
  text: zTextarea(),
  direction: directionSchema,
  distance: z.number().min(10).max(2000),
  delay: z.number().min(0).max(120),
  fontSizeRatio: z.number().min(0.01).max(0.2),
  color: zColor().optional(),
  fontWeight: z.string(),
  textAlign: z.enum(["left", "center", "right"]),
});

export const scaleTextSchema = z.object({
  text: zTextarea(),
  fromScale: z.number().min(0).max(5),
  toScale: z.number().min(0.1).max(5),
  delay: z.number().min(0).max(120),
  fontSizeRatio: z.number().min(0.01).max(0.2),
  color: zColor().optional(),
  fontWeight: z.string(),
});

// --- Background Component Schemas ---

export const gradientBackgroundSchema = z.object({
  colors: z.array(zColor()).min(2).max(5),
  type: z.enum(["linear", "radial"]),
  animate: z.boolean(),
  rotationSpeed: z.number().min(0).max(10),
  startAngle: z.number().min(0).max(360),
});

export const particleFieldSchema = z.object({
  count: z.number().min(5).max(500),
  minSize: z.number().min(0.5).max(10),
  maxSize: z.number().min(1).max(20),
  color: zColor(),
  speed: z.number().min(0.1).max(5),
  seed: z.string(),
  opacity: z.number().min(0.1).max(1),
});

export const noiseBackgroundSchema = z.object({
  gridSize: z.number().min(5).max(50),
  speed: z.number().min(0.001).max(0.1),
  color: zColor(),
  opacity: z.number().min(0.05).max(1),
  seed: z.string(),
});

export const waveBackgroundSchema = z.object({
  layers: z.number().min(1).max(6),
  amplitude: z.number().min(10).max(200),
  frequency: z.number().min(0.001).max(0.05),
  colors: z.array(zColor()).min(1).max(6),
  speed: z.number().min(0.5).max(5),
});

// --- Shape Component Schemas ---

export const animatedCircleSchema = z.object({
  radius: z.number().min(5).max(500),
  fill: zColor().optional(),
  stroke: zColor().optional(),
  strokeWidth: z.number().min(0).max(20),
  animateIn: z.enum(["scale", "draw", "fade"]),
  delay: z.number().min(0).max(120),
});

export const animatedRectSchema = z.object({
  rectWidth: z.number().min(5).max(1920),
  rectHeight: z.number().min(5).max(1920),
  fill: zColor().optional(),
  stroke: zColor().optional(),
  strokeWidth: z.number().min(0).max(20),
  cornerRadius: z.number().min(0).max(100),
  animateIn: z.enum(["scale", "draw", "fade"]),
  delay: z.number().min(0).max(120),
});

export const pathDrawSchema = z.object({
  path: z.string(),
  strokeColor: zColor().optional(),
  strokeWidth: z.number().min(1).max(20),
  delay: z.number().min(0).max(120),
  durationInSeconds: z.number().min(0.2).max(10),
  viewBox: z.string(),
});

// --- Effect Component Schemas ---

export const logoRevealSchema = z.object({
  mode: z.enum(["scale", "fade", "mask", "slide"]),
  delay: z.number().min(0).max(120),
  size: z.number().min(0.05).max(0.8),
  springDamping: z.number().min(1).max(50),
});

// --- Template Schemas ---

export const socialPostSchema = projectPropsSchema.extend({
  headline: zTextarea(),
  bodyText: zTextarea(),
  ctaText: z.string(),
  backgroundType: z.enum(["gradient", "solid", "particles", "wave"]),
  primaryColor: zColor().optional(),
  secondaryColor: zColor().optional(),
  accentColor: zColor().optional(),
});

export const logoIntroSchema = projectPropsSchema.extend({
  companyName: z.string(),
  tagline: z.string().optional(),
  revealMode: z.enum(["scale", "fade", "mask", "slide"]),
  showParticles: z.boolean(),
  primaryColor: zColor().optional(),
  secondaryColor: zColor().optional(),
});

export const textSlideshowSchema = projectPropsSchema.extend({
  slides: z.array(
    z.object({
      text: zTextarea(),
      subtext: zTextarea().optional(),
    })
  ),
  transitionType: z.enum(["fade", "slide", "wipe"]),
  primaryColor: zColor().optional(),
  accentColor: zColor().optional(),
});

export const productShowcaseSchema = projectPropsSchema.extend({
  productName: z.string(),
  tagline: zTextarea(),
  features: z.array(z.string()),
  primaryColor: zColor().optional(),
  accentColor: zColor().optional(),
  backgroundType: z.enum(["gradient", "solid", "particles"]),
});

export const minimalTypographySchema = projectPropsSchema.extend({
  lines: z.array(zTextarea()),
  fontWeight: z.string(),
  textColor: zColor().optional(),
  backgroundColor: zColor().optional(),
  animationStyle: z.enum(["fade", "slide", "scale", "typewriter"]),
});
