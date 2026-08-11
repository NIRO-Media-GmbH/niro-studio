// ============================================================
// NIRO Motion Graphics — SafeZone Container
// Automatically constrains children to the platform-safe area.
// For portrait (9:16) → Instagram Reels safe zone.
// For landscape → uniform 5% margins.
// ============================================================

import React from "react";
import { useVideoConfig } from "remotion";
import { getSafeZonePixels } from "../../core/format-utils";
import type { VideoFormat } from "../../core/types";

interface SafeZoneProps {
  children: React.ReactNode;
  /** Override auto-detected format */
  format?: VideoFormat;
  /** Show a debug overlay of the safe zone bounds (red border) */
  debug?: boolean;
  /** Additional CSS for the container */
  style?: React.CSSProperties;
  /** Align content within the safe zone */
  align?: "start" | "center" | "end";
  /** Justify content within the safe zone */
  justify?: "start" | "center" | "end" | "between" | "around";
}

export const SafeZone: React.FC<SafeZoneProps> = ({
  children,
  format: formatOverride,
  debug = false,
  style,
  align = "center",
  justify = "start",
}) => {
  const { width, height } = useVideoConfig();

  // Auto-detect format from canvas dimensions
  const detectedFormat: VideoFormat =
    width < height ? "portrait" : "landscape";
  const format = formatOverride ?? detectedFormat;

  const sz = getSafeZonePixels(format);

  const justifyMap: Record<string, string> = {
    start: "flex-start",
    center: "center",
    end: "flex-end",
    between: "space-between",
    around: "space-around",
  };

  return (
    <div
      style={{
        position: "absolute",
        top: sz.top,
        left: sz.left,
        width: sz.width,
        height: sz.height,
        display: "flex",
        flexDirection: "column",
        alignItems: align === "start" ? "flex-start" : align === "end" ? "flex-end" : "center",
        justifyContent: justifyMap[justify] ?? "flex-start",
        overflow: "hidden",
        ...(debug
          ? {
              border: "2px solid rgba(255, 0, 0, 0.6)",
              backgroundColor: "rgba(255, 0, 0, 0.05)",
            }
          : {}),
        ...style,
      }}
    >
      {children}
    </div>
  );
};
