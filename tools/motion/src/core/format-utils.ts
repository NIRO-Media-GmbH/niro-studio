// ============================================================
// NIRO Motion Graphics — Format & Dimension Utilities
// ============================================================

import type { VideoFormat, FormatDimensions, FPSOption } from "./types";

export const FORMAT_DIMENSIONS: Record<VideoFormat, FormatDimensions> = {
  landscape: { width: 1920, height: 1080 },
  portrait: { width: 1080, height: 1920 },
  "portrait-4k": { width: 2160, height: 3840 },
  "landscape-4k": { width: 3840, height: 2160 },
};

export function getDimensions(format: VideoFormat): FormatDimensions {
  return FORMAT_DIMENSIONS[format];
}

/**
 * Used as calculateMetadata callback on <Composition>.
 * Dynamically sets width, height, fps, and durationInFrames from props.
 */
export function getCalculateMetadata(props: {
  format: VideoFormat;
  fps: FPSOption;
  durationInSeconds: number;
}) {
  const dims = getDimensions(props.format);
  return {
    width: dims.width,
    height: dims.height,
    fps: props.fps,
    durationInFrames: Math.ceil(props.durationInSeconds * props.fps),
  };
}

/**
 * Responsive size: scales a base value relative to canvas dimensions.
 * Useful for consistent sizing across formats.
 */
export function responsiveSize(
  baseSize: number,
  format: VideoFormat,
  dimension: "width" | "height" = "width"
): number {
  const dims = getDimensions(format);
  const reference = 1920;
  return Math.round(baseSize * (dims[dimension] / reference));
}

/**
 * Returns safe area margins (5% of smallest dimension).
 */
export function getSafeArea(format: VideoFormat) {
  const dims = getDimensions(format);
  const margin = Math.round(Math.min(dims.width, dims.height) * 0.05);
  return { top: margin, right: margin, bottom: margin, left: margin };
}

// ---- Face Zone (Gesichts-Schutzzone) ----
// Default covers the upper-center area typical for talking-head reels.
// Configurable per-project if the face is in a different position.

export interface FaceZone {
  /** Fraction from top where face zone starts (0-1) */
  top: number;
  /** Fraction from top where face zone ends (0-1) */
  bottom: number;
  /** Fraction from left where face zone starts (0-1) */
  left: number;
  /** Fraction from left where face zone ends (0-1) */
  right: number;
}

const DEFAULT_FACE_ZONE: FaceZone = {
  top: 0.08,
  bottom: 0.45,
  left: 0.20,
  right: 0.80,
};

export function getDefaultFaceZone(): FaceZone {
  return { ...DEFAULT_FACE_ZONE };
}

export function getFaceZonePixels(format: VideoFormat, faceZone?: FaceZone, actualDims?: { width: number; height: number }) {
  const dims = actualDims ?? getDimensions(format);
  const fz = faceZone ?? DEFAULT_FACE_ZONE;
  return {
    top: Math.round(dims.height * fz.top),
    left: Math.round(dims.width * fz.left),
    width: Math.round(dims.width * (fz.right - fz.left)),
    height: Math.round(dims.height * (fz.bottom - fz.top)),
  };
}

// ---- Instagram Reels / 9:16 Safe Zone ----
// Based on Instagram/TikTok UI overlays:
//   Top ~10%  → status bar, back button, audio label
//   Bottom ~40% → CTA, captions, share/like/comment buttons
//   Sides ~5%  → edge clipping on some devices
// The "safe" content area is roughly the middle 50% of the screen.

export interface ReelsSafeZone {
  /** Fraction from top where safe area starts (0-1) */
  top: number;
  /** Fraction from top where safe area ends (0-1) */
  bottom: number;
  /** Fraction of horizontal padding on each side (0-1) */
  horizontalPad: number;
}

const REELS_SAFE_ZONE: ReelsSafeZone = {
  top: 0.07,
  bottom: 0.575,
  horizontalPad: 0.05,
};

/**
 * Returns the Instagram Reels safe zone as fractional values (0-1).
 * Only meaningful for portrait (9:16) format.
 */
export function getReelsSafeZone(): ReelsSafeZone {
  return { ...REELS_SAFE_ZONE };
}

/**
 * Returns the safe zone as pixel values for a given format.
 * For portrait → Instagram Reels safe zone.
 * For landscape → uniform 5% margins.
 */
export function getSafeZonePixels(format: VideoFormat, actualDims?: { width: number; height: number }) {
  const dims = actualDims ?? getDimensions(format);

  if (format === "portrait" || format === "portrait-4k") {
    const sz = REELS_SAFE_ZONE;
    return {
      top: Math.round(dims.height * sz.top),
      bottom: Math.round(dims.height * (1 - sz.bottom)),
      left: Math.round(dims.width * sz.horizontalPad),
      right: Math.round(dims.width * sz.horizontalPad),
      width: Math.round(dims.width * (1 - 2 * sz.horizontalPad)),
      height: Math.round(dims.height * (sz.bottom - sz.top)),
    };
  }

  const margin = Math.round(Math.min(dims.width, dims.height) * 0.05);
  return {
    top: margin,
    bottom: margin,
    left: margin,
    right: margin,
    width: dims.width - 2 * margin,
    height: dims.height - 2 * margin,
  };
}
