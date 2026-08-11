// ============================================================
// Top Fotografie — Job Endscreen (Fotograf / Vertriebler)
// Full-screen 9:16 portrait (1080×1920), 30fps, 8s
// Hook → Title + highlight → Benefits chips → CTA button
// All elements centered within Instagram safe zone (~8%–64%)
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  useVideoConfig,
  useCurrentFrame,
  spring,
  interpolate,
} from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/OpenSans";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";

loadFont();
const ci = loadBrand("top-fotografie", brandJson as any);

const PRIMARY = "#104697";
const DARK = "#0A2D5E";
const WHITE = "#FFFFFF";

const SMOOTH = { damping: 20, stiffness: 100, mass: 1, overshootClamping: true };
const PUNCH = { damping: 10, stiffness: 180, mass: 1 };

// --- Schema ---

export const jobEndscreenSchema = projectPropsSchema.extend({
  hook: z.string().describe("Hook-Frage (z.B. 'BIST DU FOTOGRAF?')"),
  mainTitle: z.string().describe("Haupttitel"),
  benefits: z.array(z.string()).describe("Benefits"),
  ctaText: z.string().describe("CTA Text"),
});

export type JobEndscreenProps = z.infer<typeof jobEndscreenSchema>;

// --- Default Props (Fotograf) ---

export const fotografEndscreenDefaults: JobEndscreenProps = {
  format: "portrait" as const,
  fps: 30 as const,
  durationInSeconds: 8,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  hook: "BIST DU FOTOGRAF?",
  mainTitle: "MOMENTE\nEINFANGEN",
  benefits: [
    "Leistungsorientierte Bezahlung",
    "Abwechslungsreiche Aufgaben",
    "Firmenwagen zur privaten Nutzung",
    "Eigenständige Organisation",
  ],
  ctaText: "Bewirb Dich jetzt in unter 1 Minute",
};

// --- Default Props (Vertriebler) ---

export const vertrieblerEndscreenDefaults: JobEndscreenProps = {
  format: "portrait" as const,
  fps: 30 as const,
  durationInSeconds: 8,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  hook: "BIST DU VERTRIEBLER?",
  mainTitle: "KUNDEN\nGEWINNEN",
  benefits: [
    "Spitzen Gehalt + Provision + Boni",
    "Firmenwagen zur privaten Nutzung",
    "Quereinstieg möglich",
    "mobiles Arbeiten",
  ],
  ctaText: "Bewirb Dich jetzt in unter 1 Minute",
};

// =============================================================
// Component
// =============================================================

export const TopJobEndscreen: React.FC<JobEndscreenProps> = ({
  review,
  hook,
  mainTitle,
  benefits,
  ctaText,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // --- Timings (in frames @ 30fps) ---
  const hookStart = 0;
  const titleStart = 30;
  const benefitsStart = 65;
  const ctaStart = 95;

  // --- Hook entrance ---
  const hookProgress = spring({
    frame: frame - hookStart,
    fps,
    config: PUNCH,
  });
  const hookScale = interpolate(hookProgress, [0, 1], [0.7, 1]);
  const hookOpacity = interpolate(frame, [hookStart, hookStart + 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Hook dims slightly when title appears
  const hookFade = interpolate(frame, [titleStart, titleStart + 15], [1, 0.6], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- Title entrance ---
  const titleProgress = spring({
    frame: frame - titleStart,
    fps,
    config: SMOOTH,
  });
  const titleOpacity = interpolate(
    frame,
    [titleStart, titleStart + 10],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const titleSlideY = Math.round(interpolate(titleProgress, [0, 1], [40, 0]));

  // Highlight box that sweeps behind title
  const highlightProgress = spring({
    frame: frame - (titleStart + 6),
    fps,
    config: { damping: 18, stiffness: 140, mass: 1, overshootClamping: true },
  });
  const highlightScaleX = interpolate(highlightProgress, [0, 1], [0, 1]);

  // --- CTA ---
  const ctaProgress = spring({
    frame: frame - ctaStart,
    fps,
    config: PUNCH,
  });
  const ctaScale = interpolate(ctaProgress, [0, 1], [0.8, 1]);
  const ctaOpacity = interpolate(
    frame,
    [ctaStart, ctaStart + 8],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  // No pulse — stays fixed after entrance
  const ctaPulse = 1;

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill
        style={{
          background: `linear-gradient(170deg, ${PRIMARY} 0%, ${DARK} 100%)`,
        }}
      >
        {/* Hook — top of safe zone */}
        <div
          style={{
            position: "absolute",
            top: "12%",
            left: 0,
            right: 0,
            textAlign: "center",
            padding: "0 48px",
            opacity: hookOpacity * hookFade,
            transform: `scale(${hookScale})`,
          }}
        >
          <div
            style={{
              fontFamily: "Open Sans",
              fontWeight: 800,
              fontSize: 56,
              color: WHITE,
              textTransform: "uppercase",
              letterSpacing: 2,
              textShadow: "0 2px 16px rgba(0,0,0,0.3)",
            }}
          >
            {hook}
          </div>
        </div>

        {/* Main Title with highlight box — centered */}
        <div
          style={{
            position: "absolute",
            top: "24%",
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            padding: "0 48px",
            opacity: titleOpacity,
            transform: `translateY(${titleSlideY}px)`,
          }}
        >
          <div style={{ position: "relative", display: "inline-block" }}>
            {/* Highlight box */}
            <div
              style={{
                position: "absolute",
                top: -8,
                left: -16,
                right: -16,
                bottom: -8,
                backgroundColor: WHITE,
                transform: `scaleX(${highlightScaleX})`,
                transformOrigin: "center center",
                borderRadius: 4,
              }}
            />
            {/* Title */}
            <div
              style={{
                position: "relative",
                fontFamily: "Open Sans",
                fontWeight: 900,
                fontSize: 82,
                color: highlightScaleX > 0.9 ? PRIMARY : WHITE,
                lineHeight: 0.95,
                textTransform: "uppercase",
                letterSpacing: 1,
                whiteSpace: "pre-line",
                textAlign: "center",
                transition: "color 0.2s ease",
              }}
            >
              {mainTitle}
            </div>
          </div>
        </div>

        {/* Benefits — 2×2 chip grid */}
        <div
          style={{
            position: "absolute",
            top: "40%",
            left: 0,
            right: 0,
            padding: "0 48px",
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: 12,
          }}
        >
          {benefits.map((benefit, i) => {
            const itemDelay = benefitsStart + i * 6;
            const itemProgress = spring({
              frame: frame - itemDelay,
              fps,
              config: SMOOTH,
            });
            const itemOpacity = interpolate(
              frame,
              [itemDelay, itemDelay + 8],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );
            const itemSlideY = Math.round(interpolate(itemProgress, [0, 1], [20, 0]));

            return (
              <div
                key={i}
                style={{
                  opacity: itemOpacity,
                  transform: `translateY(${itemSlideY}px)`,
                }}
              >
                <div
                  style={{
                    backgroundColor: "rgba(255,255,255,0.12)",
                    border: "1px solid rgba(255,255,255,0.2)",
                    borderRadius: 24,
                    padding: "12px 20px",
                    fontFamily: "Open Sans",
                    fontWeight: 600,
                    fontSize: 22,
                    color: WHITE,
                    whiteSpace: "nowrap",
                  }}
                >
                  {benefit}
                </div>
              </div>
            );
          })}
        </div>

        {/* CTA Button — bottom of safe zone */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            padding: "0 48px",
            opacity: ctaOpacity,
            transform: `scale(${ctaScale * ctaPulse})`,
          }}
        >
          <div
            style={{
              backgroundColor: WHITE,
              borderRadius: 14,
              padding: "22px 36px",
              boxShadow: "0 8px 30px rgba(0,0,0,0.25)",
              display: "inline-block",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontFamily: "Open Sans",
                fontWeight: 800,
                fontSize: 32,
                color: PRIMARY,
                letterSpacing: 0.5,
              }}
            >
              {ctaText}
            </div>
          </div>
        </div>

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
    </CIProvider>
  );
};
