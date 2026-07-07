// ============================================================
// Top Fotografie — Fototag Teaser (Blur-Reveal)
// Full-screen, 9:16 portrait (1080×1920), 30fps, 12s
// Numbers clear, descriptions blurred — teaser only
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
  { num: "01", text: "Vorbereitung" },
  { num: "02", text: "Fester Zeitplan" },
  { num: "03", text: "Klarer Ablauf" },
  { num: "04", text: "Abbau" },
];

// --- Schema ---

export const fototagBlurSchema = projectPropsSchema.extend({
  headline: z.string().describe("Headline"),
});

export type FototagBlurProps = z.infer<typeof fototagBlurSchema>;

export const fototagBlurDefaults: FototagBlurProps = {
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

export const TopFototagBlur: React.FC<FototagBlurProps> = ({ review, headline }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Exit
  const exitFrame = durationInFrames - EXIT_LEAD;
  const exitProgress =
    frame >= exitFrame
      ? spring({ frame: frame - exitFrame, fps, config: { damping: 12, stiffness: 160, mass: 1 } })
      : 0;
  const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);

  // Headline entrance
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
            top: "12%",
            left: 0,
            right: 0,
            textAlign: "center",
            opacity: headOpacity,
            transform: `translateY(${headSlideY}px)`,
            padding: "0 60px",
          }}
        >
          <div
            style={{
              fontFamily: "Open Sans",
              fontWeight: 800,
              fontSize: 52,
              color: WHITE,
              lineHeight: 1.25,
              textTransform: "uppercase",
              letterSpacing: 2,
            }}
          >
            {headline}
          </div>
        </div>

        {/* 4 Steps — numbers clear, text blurred */}
        <div
          style={{
            position: "absolute",
            top: "30%",
            left: 0,
            right: 0,
            padding: "0 60px",
            display: "flex",
            flexDirection: "column",
            gap: 28,
          }}
        >
          {STEPS.map((step, i) => {
            const delay = 20 + i * 12;
            const localFrame = Math.max(0, frame - delay);
            const entrance = spring({ frame: localFrame, fps, config: SMOOTH });
            const opacity = interpolate(localFrame, [0, 10], [0, 1], {
              extrapolateRight: "clamp",
            });
            const slideX = Math.round(interpolate(entrance, [0, 1], [50, 0]));

            // Text gets progressively slightly less blurred per step but never readable
            const blurAmount = 12 - i * 1.5;

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
                {/* Number — clear */}
                <div
                  style={{
                    fontFamily: "Open Sans",
                    fontWeight: 800,
                    fontSize: 64,
                    color: "rgba(255,255,255,0.2)",
                    minWidth: 100,
                  }}
                >
                  {step.num}
                </div>

                {/* Text — blurred */}
                <div
                  style={{
                    fontFamily: "Open Sans",
                    fontWeight: 700,
                    fontSize: 38,
                    color: WHITE,
                    filter: `blur(${blurAmount}px)`,
                    userSelect: "none",
                  }}
                >
                  {step.text}
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom hint */}
        <div
          style={{
            position: "absolute",
            bottom: "46%",
            left: 0,
            right: 0,
            textAlign: "center",
            opacity: interpolate(frame, [80, 95], [0, 0.6], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          <div
            style={{
              fontFamily: "Open Sans",
              fontWeight: 600,
              fontSize: 26,
              color: "rgba(255,255,255,0.6)",
              letterSpacing: 3,
              textTransform: "uppercase",
            }}
          >
            Dranbleiben...
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
