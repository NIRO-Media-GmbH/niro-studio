// ============================================================
// Top Fotografie — Fototag Teaser (Glitch-Decode)
// Full-screen, 9:16 portrait (1080×1920), 30fps, 12s
// Steps decode with random chars, freeze before readable
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  useVideoConfig,
  useCurrentFrame,
  spring,
  interpolate,
  random,
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

const GLITCH_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#@%&*!?";

const STEPS = [
  { num: "01", text: "Vorbereitung" },
  { num: "02", text: "Fester Zeitplan" },
  { num: "03", text: "Klarer Ablauf" },
  { num: "04", text: "Abbau" },
];

function getGlitchText(
  original: string,
  progress: number,
  seed: string,
  frameNum: number,
): string {
  // progress 0 = all random, 1 = all revealed
  // We cap at 0.3 so it never fully reveals
  const revealFrac = Math.min(progress, 0.3);
  const chars = original.split("");
  return chars
    .map((char, ci) => {
      if (char === " ") return " ";
      const charThreshold = ci / chars.length;
      if (revealFrac > charThreshold) {
        // "Revealed" but still glitchy — show random char that's not the real one
        const r = random(`${seed}-${ci}-${Math.floor(frameNum / 3)}`);
        return GLITCH_CHARS[Math.floor(r * GLITCH_CHARS.length)];
      }
      const r = random(`${seed}-${ci}-${Math.floor(frameNum / 2)}`);
      return GLITCH_CHARS[Math.floor(r * GLITCH_CHARS.length)];
    })
    .join("");
}

// --- Schema ---

export const fototagGlitchSchema = projectPropsSchema.extend({
  headline: z.string().describe("Headline"),
});

export type FototagGlitchProps = z.infer<typeof fototagGlitchSchema>;

export const fototagGlitchDefaults: FototagGlitchProps = {
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

export const TopFototagGlitch: React.FC<FototagGlitchProps> = ({ review, headline }) => {
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

        {/* 4 Steps — glitch decode */}
        <div
          style={{
            position: "absolute",
            top: "30%",
            left: 0,
            right: 0,
            padding: "0 60px",
            display: "flex",
            flexDirection: "column",
            gap: 32,
          }}
        >
          {STEPS.map((step, i) => {
            const delay = 20 + i * 14;
            const localFrame = Math.max(0, frame - delay);
            const entrance = spring({ frame: localFrame, fps, config: SMOOTH });
            const opacity = interpolate(localFrame, [0, 8], [0, 1], {
              extrapolateRight: "clamp",
            });
            const slideX = Math.round(interpolate(entrance, [0, 1], [40, 0]));

            // Decode progress — ramps up but caps so text never resolves
            const decodeProgress = interpolate(localFrame, [0, 45], [0, 1], {
              extrapolateRight: "clamp",
            });

            const glitchedText = localFrame > 0
              ? getGlitchText(step.text, decodeProgress, `step-${i}`, frame)
              : "";

            // After initial decode burst, chars slow down (every 3rd frame)
            const isStable = localFrame > 50;
            const displayText = isStable
              ? getGlitchText(step.text, 0.3, `step-${i}-stable`, Math.floor(frame / 8))
              : glitchedText;

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

                {/* Glitched text */}
                <div
                  style={{
                    fontFamily: "Open Sans",
                    fontWeight: 700,
                    fontSize: 36,
                    color: isStable ? "rgba(255,255,255,0.5)" : WHITE,
                    letterSpacing: 3,
                    textTransform: "uppercase",
                  }}
                >
                  {displayText}
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom cursor blink */}
        <div
          style={{
            position: "absolute",
            bottom: "44%",
            left: 0,
            right: 0,
            textAlign: "center",
            opacity: interpolate(frame, [90, 105], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          <div
            style={{
              fontFamily: "Open Sans",
              fontWeight: 600,
              fontSize: 24,
              color: "rgba(255,255,255,0.4)",
              letterSpacing: 4,
              textTransform: "uppercase",
            }}
          >
            Decoding...{Math.floor(frame / 2) % 2 === 0 ? "\u2588" : ""}
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
