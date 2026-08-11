// ============================================================
// REM Overlay — BrandIntro
// Absender-Karte für den Videoanfang: R-Monogramm (Vektor) +
// „REM Malerfachbetrieb" + Kontextzeile. Etabliert die Marke,
// bevor der erste inhaltliche Cue erscheint (Kundenfeedback
// 2026-07-22: REM muss von Anfang an erkennbar sein).
// Gleiche Position/Animatik wie KeywordLowerThird.
// ============================================================

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import {
  RED,
  RED_LIGHT,
  INK,
  GRAY,
  SAFE,
  RADIUS,
  PUNCH_SPRING,
  SMOOTH_SPRING,
} from "./constants";
import { useExit } from "./useExit";
import { RemMark } from "./RemMark";

const { fontFamily } = loadFont();

interface BrandIntroProps {
  /** Kontextzeile unter dem Firmennamen (default: "Kundenstimme · Gewerbedach") */
  subline?: string;
  /** Distance from bottom as fraction of height (default: 0.09) */
  bottomRatio?: number;
  /** Font size as fraction of height (default: 0.05) */
  fontSizeRatio?: number;
  /** X offset in pixels */
  offsetX?: number;
  /** Y offset in pixels (positive = lower) */
  offsetY?: number;
}

export const BrandIntro: React.FC<BrandIntroProps> = ({
  subline = "Kundenstimme · Gewerbedach",
  bottomRatio = 0.09,
  fontSizeRatio = 0.05,
  offsetX = 0,
  offsetY = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();
  const { exitOpacity, exitSlide } = useExit();

  // --- Auto-scale wie KeywordLowerThird (Textbreite an Zone anpassen) ---
  const name = "REM Malerfachbetrieb";
  const baseFontSize = Math.round(height * fontSizeRatio);
  const maxWidth = width * 0.43;
  const estCharW = baseFontSize * 0.66;
  const estFixed = baseFontSize * 3.6; // Padding + Monogramm
  const estTotal = name.length * estCharW + estFixed;
  const scaleFactor = estTotal > maxWidth ? maxWidth / estTotal : 1;
  const fontSize = Math.round(baseFontSize * scaleFactor);
  const markSize = Math.round(fontSize * 2.2);
  const pad = Math.round(fontSize * 0.55);
  const gap = Math.round(fontSize * 0.55);
  const underlineHeight = Math.max(5, Math.round(fontSize * 0.08));

  // --- Card entrance: spring up + fade ---
  const enter = spring({ frame, fps, config: PUNCH_SPRING });
  const enterY = interpolate(enter, [0, 1], [46, 0]);
  const enterOpacity = interpolate(enter, [0, 0.4], [0, 1], {
    extrapolateRight: "clamp",
  });

  // --- Monogramm pop (slightly delayed) ---
  const markPop = spring({ frame: frame - 2, fps, config: PUNCH_SPRING });
  const markScale = interpolate(markPop, [0, 1], [0.4, 1]);

  // --- Firmenname clip-path reveal from left ---
  const revealFrames = Math.min(
    Math.floor(durationInFrames * 0.35),
    Math.floor(fps * 0.7),
  );
  const revealPct = interpolate(frame - 4, [0, revealFrames], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // --- Roter Unterstrich nach dem Reveal ---
  const underlineProg = spring({
    frame: frame - 4 - revealFrames,
    fps,
    config: SMOOTH_SPRING,
  });

  // --- Subline fade-in nach dem Namen ---
  const sublineOpacity = interpolate(
    frame - 4 - revealFrames,
    [0, Math.floor(fps * 0.3)],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const bottomPx = Math.round(height * bottomRatio) - offsetY;

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottomPx,
        left: Math.round(width * SAFE.left) + offsetX,
        opacity: enterOpacity * exitOpacity,
      }}
    >
      <div style={{ transform: `translateY(${enterY - exitSlide}px)` }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap,
            padding: `${pad}px ${Math.round(pad * 1.3)}px`,
            backgroundColor: "rgba(255,255,255,0.95)",
            borderRadius: RADIUS,
            borderLeft: `${Math.max(5, Math.round(fontSize * 0.12))}px solid ${RED}`,
            boxShadow:
              "0 18px 50px rgba(26,26,46,0.30), 0 4px 14px rgba(26,26,46,0.18)",
            backdropFilter: "blur(6px)",
            WebkitBackdropFilter: "blur(6px)",
          }}
        >
          {/* R-Monogramm — Original-Vektor mit REM-Verlauf */}
          <div
            style={{
              width: markSize,
              height: markSize,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              transform: `scale(${markScale})`,
            }}
          >
            <RemMark size={markSize} />
          </div>

          {/* Firmenname + Unterstrich + Kontextzeile */}
          <div style={{ paddingRight: Math.round(pad * 0.3) }}>
            <div
              style={{
                clipPath: `inset(0 ${100 - revealPct}% 0 0)`,
                fontFamily,
                fontSize,
                fontWeight: 800,
                letterSpacing: -Math.round(fontSize * 0.01),
                lineHeight: 1.3,
                paddingBottom: Math.round(fontSize * 0.06),
                whiteSpace: "nowrap",
              }}
            >
              <span style={{ color: RED, fontWeight: 900 }}>REM</span>
              <span style={{ color: INK }}> Malerfachbetrieb</span>
            </div>
            <div
              style={{
                height: underlineHeight,
                width: `${underlineProg * 100}%`,
                background: `linear-gradient(90deg, ${RED}, ${RED_LIGHT})`,
                borderRadius: 2,
                boxShadow: `0 0 16px ${RED_LIGHT}88`,
              }}
            />
            <div
              style={{
                marginTop: Math.round(fontSize * 0.22),
                fontFamily,
                fontSize: Math.round(fontSize * 0.52),
                fontWeight: 600,
                color: GRAY,
                letterSpacing: Math.round(fontSize * 0.02),
                textTransform: "uppercase",
                opacity: sublineOpacity,
                whiteSpace: "nowrap",
              }}
            >
              {subline}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
