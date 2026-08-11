// ============================================================
// Förch Messevideos — REC-Overlay (Video 2 Hook)
// Handy-Kamera-Sucher-Look: blinkender REC-Punkt, Batterie,
// Eck-Klammern, laufender Timecode. Transparentes Alpha-Overlay
// (ProRes 4444) über das Hook-Footage. 9:16 (1080×1920), 25fps, 5s.
// Bewusst KEINE CI-Farben — neutrale Kamera-UI (Weiß/Rot).
// ============================================================

import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/Inter";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";

const { fontFamily } = loadFont();

// --- Schema ---

export const foerchRecOverlaySchema = projectPropsSchema.extend({
  blinkHz: z.number().min(0.2).max(4).step(0.1).describe("Blinkfrequenz REC-Punkt (Hz)"),
  showTimecode: z.boolean().describe("Timecode oben mittig anzeigen"),
  uiScale: z.number().min(0.5).max(2).step(0.05).describe("Größe aller UI-Elemente"),
});

export type FoerchRecOverlayProps = z.infer<typeof foerchRecOverlaySchema>;

// --- Default Props ---

export const foerchRecOverlayDefaults: FoerchRecOverlayProps = {
  format: "portrait" as const,
  fps: 25 as const,
  durationInSeconds: 5,
  transparent: true,
  blinkHz: 1,
  showTimecode: true,
  uiScale: 1,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
};

// --- Bausteine ---

const WHITE = "#FFFFFF";
const REC_RED = "#FF3B30";
const SHADOW = "0px 1px 6px rgba(0,0,0,0.55)";
const STROKE_SHADOW = "drop-shadow(0px 1px 3px rgba(0,0,0,0.5))";

/** L-förmige Sucher-Klammer; via rotate in alle vier Ecken gedreht. */
const CornerBracket: React.FC<{ rotate: number; style: React.CSSProperties }> = ({
  rotate,
  style,
}) => (
  <svg
    width={104}
    height={104}
    viewBox="0 0 104 104"
    style={{ position: "absolute", transform: `rotate(${rotate}deg)`, filter: STROKE_SHADOW, ...style }}
  >
    <path
      d="M 3 40 L 3 3 L 40 3"
      fill="none"
      stroke={WHITE}
      strokeWidth={6}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const Battery: React.FC = () => (
  <svg width={78} height={36} viewBox="0 0 78 36" style={{ filter: STROKE_SHADOW }}>
    <rect x={2} y={2} width={64} height={32} rx={8} fill="none" stroke={WHITE} strokeWidth={4} />
    <rect x={69} y={12} width={7} height={12} rx={3} fill={WHITE} />
    <rect x={8} y={8} width={38} height={20} rx={4} fill={WHITE} />
  </svg>
);

/** Timecode HH:MM:SS:FF aus aktueller Frame-Position. */
const formatTimecode = (frame: number, fps: number): string => {
  const totalSeconds = Math.floor(frame / fps);
  const ff = frame % fps;
  const ss = totalSeconds % 60;
  const mm = Math.floor(totalSeconds / 60) % 60;
  const hh = Math.floor(totalSeconds / 3600);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(hh)}:${p(mm)}:${p(ss)}:${p(ff)}`;
};

// --- Composition ---

export const FoerchRecOverlay: React.FC<FoerchRecOverlayProps> = ({
  review,
  blinkHz,
  showTimecode,
  uiScale,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Harter On/Off-Blink (authentische Kamera-UI, kein Fade)
  const dotOn = Math.floor((frame / fps) * blinkHz * 2) % 2 === 0;

  // Reels-Safe-Zone beginnt bei 7% (134px): REC-Zeile knapp darunter.
  // Face Zone (Default) beginnt bei 8%/x216: REC+Punkt enden vor x216,
  // Batterie liegt rechts außerhalb (x>864). Timecode unten mittig
  // (Camcorder-Look) — außerhalb der Face Zone, bewusst unterhalb der
  // Reels-Safe-Zone (dekorativ, Abweichung im Protokoll dokumentiert).
  const MARGIN_X = 84;
  const TOP_Y = 150;
  const BRACKET_INSET = 64;
  const TC_BOTTOM = 116;

  return (
    <AbsoluteFill style={{ fontFamily }}>
      <AbsoluteFill
        style={{ transform: `scale(${uiScale})`, transformOrigin: "center center" }}
      >
        {/* REC + blinkender Punkt, oben links */}
        <div
          style={{
            position: "absolute",
            top: TOP_Y,
            left: MARGIN_X,
            display: "flex",
            alignItems: "center",
            gap: 16,
          }}
        >
          <span
            style={{
              color: WHITE,
              fontSize: 36,
              fontWeight: 600,
              letterSpacing: 3,
              textShadow: SHADOW,
              lineHeight: 1,
            }}
          >
            REC
          </span>
          <div
            style={{
              width: 24,
              height: 24,
              borderRadius: "50%",
              backgroundColor: REC_RED,
              opacity: dotOn ? 1 : 0,
              boxShadow: "0px 1px 6px rgba(0,0,0,0.35)",
            }}
          />
        </div>

        {/* Timecode, unten mittig (Camcorder-Look) */}
        {showTimecode && (
          <div
            style={{
              position: "absolute",
              bottom: TC_BOTTOM,
              left: 0,
              right: 0,
              textAlign: "center",
              color: WHITE,
              fontSize: 34,
              fontWeight: 500,
              letterSpacing: 2,
              fontFeatureSettings: '"tnum"',
              textShadow: SHADOW,
              lineHeight: 1,
            }}
          >
            {formatTimecode(frame, fps)}
          </div>
        )}

        {/* Batterie, oben rechts */}
        <div style={{ position: "absolute", top: TOP_Y - 2, right: MARGIN_X }}>
          <Battery />
        </div>

        {/* Sucher-Klammern in den vier Ecken */}
        <CornerBracket rotate={0} style={{ top: BRACKET_INSET, left: BRACKET_INSET }} />
        <CornerBracket rotate={90} style={{ top: BRACKET_INSET, right: BRACKET_INSET }} />
        <CornerBracket rotate={270} style={{ bottom: BRACKET_INSET, left: BRACKET_INSET }} />
        <CornerBracket rotate={180} style={{ bottom: BRACKET_INSET, right: BRACKET_INSET }} />
      </AbsoluteFill>

      {review?.showGuides && (
        <ReviewOverlay
          showSafeZone={review.showSafeZone ?? true}
          showFaceZone={review.showFaceZone ?? true}
          showGrid={review.showGrid ?? false}
          faceZone={review.faceZone}
          guideOpacity={review.guideOpacity ?? 0.35}
        />
      )}
    </AbsoluteFill>
  );
};
