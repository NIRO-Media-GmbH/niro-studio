// ============================================================
// Top Fotografie — Fototag Teaser (Redacted)
// Full-screen, 9:16 portrait (1080×1920), 30fps, 12s
// Steps appear with redacted/censored text blocks
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

const STEPS = [
  { num: "01", text: "Vorbereitung", barWidth: 440 },
  { num: "02", text: "Fester Zeitplan", barWidth: 520 },
  { num: "03", text: "Klarer Ablauf", barWidth: 470 },
  { num: "04", text: "Abbau", barWidth: 300 },
];

// --- Schema ---

export const fototagRedactedSchema = projectPropsSchema.extend({
  headline: z.string().describe("Headline"),
});

export type FototagRedactedProps = z.infer<typeof fototagRedactedSchema>;

export const fototagRedactedDefaults: FototagRedactedProps = {
  format: "portrait" as const,
  fps: 30 as const,
  durationInSeconds: 12,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  headline: "4 Schritte zu deinem Fototag",
};

// --- Component ---

const SMOOTH = { damping: 20, stiffness: 100, mass: 1, overshootClamping: true };
const EXIT_LEAD = 15;

export const TopFototagRedacted: React.FC<FototagRedactedProps> = ({ review, headline }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Exit
  const exitFrame = durationInFrames - EXIT_LEAD;
  const exitProgress =
    frame >= exitFrame
      ? spring({ frame: frame - exitFrame, fps, config: { damping: 12, stiffness: 160, mass: 1 } })
      : 0;
  const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);

  // Headline
  const headEntrance = spring({ frame, fps, config: SMOOTH });
  const headOpacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const headSlideY = Math.round(interpolate(headEntrance, [0, 1], [40, 0]));

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill
        style={{
          background: `linear-gradient(170deg, ${PRIMARY} 0%, ${DARK} 100%)`,
          opacity: exitOpacity,
        }}
      >
        {/* Headline */}
        <div
          style={{
            position: "absolute",
            top: "10%",
            left: 0,
            right: 0,
            textAlign: "center",
            opacity: headOpacity,
            transform: `translateY(${headSlideY}px)`,
            padding: "0 48px",
          }}
        >
          <div
            style={{
              fontFamily: "Open Sans",
              fontWeight: 800,
              fontSize: 68,
              color: WHITE,
              lineHeight: 1.2,
              textTransform: "uppercase",
              letterSpacing: 2,
            }}
          >
            {headline}
          </div>
        </div>

        {/* 4 Steps — redacted */}
        <div
          style={{
            position: "absolute",
            top: "34%",
            left: 0,
            right: 0,
            padding: "0 48px",
            display: "flex",
            flexDirection: "column",
            gap: 44,
          }}
        >
          {STEPS.map((step, i) => {
            const delay = 20 + i * 14;
            const localFrame = Math.max(0, frame - delay);
            const entrance = spring({ frame: localFrame, fps, config: SMOOTH });
            const opacity = interpolate(localFrame, [0, 10], [0, 1], {
              extrapolateRight: "clamp",
            });
            const slideX = Math.round(interpolate(entrance, [0, 1], [50, 0]));

            // Redaction bar slides in from left
            const barEntrance = spring({
              frame: Math.max(0, localFrame - 4),
              fps,
              config: { damping: 18, stiffness: 140, mass: 1, overshootClamping: true },
            });
            const barWidth = Math.round(barEntrance * step.barWidth);

            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 24,
                  opacity,
                  transform: `translateX(${slideX}px)`,
                }}
              >
                {/* Step label */}
                <div
                  style={{
                    fontFamily: "Open Sans",
                    fontWeight: 800,
                    fontSize: 36,
                    color: "rgba(255,255,255,0.5)",
                    textTransform: "uppercase",
                    letterSpacing: 3,
                    minWidth: 200,
                  }}
                >
                  Schritt {step.num}
                </div>

                {/* Redacted bar */}
                <div
                  style={{
                    height: 44,
                    width: barWidth,
                    backgroundColor: "rgba(255,255,255,0.15)",
                    borderRadius: 4,
                    position: "relative",
                    overflow: "hidden",
                  }}
                >
                  {/* Shimmer effect */}
                  <div
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: `linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.08) 50%, transparent 100%)`,
                      transform: `translateX(${((frame + i * 20) % 90) / 90 * 200 - 100}%)`,
                    }}
                  />
                </div>
              </div>
            );
          })}
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
