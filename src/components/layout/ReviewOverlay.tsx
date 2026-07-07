// ============================================================
// NIRO Motion Graphics — Review Overlay
// Visual guide overlay for Safe Zone + Face Zone compliance.
// Toggle via review.showGuides in Remotion Studio props.
// ============================================================

import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { getSafeZonePixels, getFaceZonePixels } from "../../core/format-utils";
import type { VideoFormat } from "../../core/types";

interface ReviewOverlayProps {
  showSafeZone?: boolean;
  showFaceZone?: boolean;
  showGrid?: boolean;
  faceZone?: { top: number; bottom: number; left: number; right: number };
  guideOpacity?: number;
  format?: VideoFormat;
}

export const ReviewOverlay: React.FC<ReviewOverlayProps> = ({
  showSafeZone = true,
  showFaceZone = true,
  showGrid = false,
  faceZone,
  guideOpacity = 0.35,
  format: formatOverride,
}) => {
  const { width, height } = useVideoConfig();
  const detectedFormat: VideoFormat = width < height ? "portrait" : "landscape";
  const format = formatOverride ?? detectedFormat;

  const actualDims = { width, height };
  const sz = getSafeZonePixels(format, actualDims);
  const fz = getFaceZonePixels(format, faceZone, actualDims);

  return (
    <AbsoluteFill style={{ pointerEvents: "none", zIndex: 9999 }}>
      {/* ---- Safe Zone ---- */}
      {showSafeZone && (
        <>
          {/* Top unsafe */}
          <div style={{ position: "absolute", top: 0, left: 0, width, height: sz.top, backgroundColor: `rgba(255, 0, 0, ${guideOpacity * 0.15})` }} />
          {/* Bottom unsafe */}
          <div style={{ position: "absolute", top: sz.top + sz.height, left: 0, width, height: height - sz.top - sz.height, backgroundColor: `rgba(255, 0, 0, ${guideOpacity * 0.15})` }} />
          {/* Left unsafe */}
          <div style={{ position: "absolute", top: sz.top, left: 0, width: sz.left, height: sz.height, backgroundColor: `rgba(255, 0, 0, ${guideOpacity * 0.15})` }} />
          {/* Right unsafe */}
          <div style={{ position: "absolute", top: sz.top, left: sz.left + sz.width, width: width - sz.left - sz.width, height: sz.height, backgroundColor: `rgba(255, 0, 0, ${guideOpacity * 0.15})` }} />
          {/* Safe zone border */}
          <div style={{ position: "absolute", top: sz.top, left: sz.left, width: sz.width, height: sz.height, border: `2px dashed rgba(0, 255, 100, ${guideOpacity})`, boxSizing: "border-box" }} />
          {/* Label */}
          <div style={{ position: "absolute", top: sz.top - 20, left: sz.left, fontSize: 12, fontFamily: "monospace", color: `rgba(0, 255, 100, ${Math.min(guideOpacity + 0.2, 1)})`, fontWeight: "bold" }}>
            SAFE ZONE
          </div>
        </>
      )}

      {/* ---- Face Zone ---- */}
      {showFaceZone && (
        <>
          <div style={{ position: "absolute", top: fz.top, left: fz.left, width: fz.width, height: fz.height, border: `2px solid rgba(255, 60, 60, ${Math.min(guideOpacity + 0.1, 1)})`, backgroundColor: `rgba(255, 60, 60, ${guideOpacity * 0.12})`, boxSizing: "border-box" }} />
          {/* Hatch pattern */}
          <svg style={{ position: "absolute", top: fz.top, left: fz.left, width: fz.width, height: fz.height, opacity: guideOpacity * 0.3 }}>
            <defs>
              <pattern id="review-hatch" patternUnits="userSpaceOnUse" width="12" height="12">
                <path d="M0 12L12 0" stroke="rgba(255,60,60,0.5)" strokeWidth="1" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#review-hatch)" />
          </svg>
          {/* Label */}
          <div style={{ position: "absolute", top: fz.top + 6, left: fz.left + 8, fontSize: 12, fontFamily: "monospace", color: `rgba(255, 60, 60, ${Math.min(guideOpacity + 0.3, 1)})`, fontWeight: "bold" }}>
            GESICHTS-ZONE — NICHT VERDECKEN
          </div>
        </>
      )}

      {/* ---- Rule-of-Thirds Grid ---- */}
      {showGrid && (
        <>
          {[1 / 3, 2 / 3].map((frac) => (
            <React.Fragment key={`h-${frac}`}>
              <div style={{ position: "absolute", top: sz.top + sz.height * frac, left: sz.left, width: sz.width, height: 1, backgroundColor: `rgba(255, 255, 255, ${guideOpacity * 0.4})` }} />
            </React.Fragment>
          ))}
          {[1 / 3, 2 / 3].map((frac) => (
            <React.Fragment key={`v-${frac}`}>
              <div style={{ position: "absolute", top: sz.top, left: sz.left + sz.width * frac, width: 1, height: sz.height, backgroundColor: `rgba(255, 255, 255, ${guideOpacity * 0.4})` }} />
            </React.Fragment>
          ))}
        </>
      )}
    </AbsoluteFill>
  );
};
