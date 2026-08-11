// ============================================================
// Top Fotografie — Drei Fragen (Overlay)
// Transparent overlay (ProRes 4444 with Alpha)
// 9:16 portrait (1080x1920), 30fps, 34s
// 3 Fragen mit Nummer, Titel und Untertitel
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Sequence,
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
import { STEPS, TOTAL_DURATION_SEC } from "./transcript";
import brandJson from "../../brand.json";

loadFont();
const ci = loadBrand("top-fotografie", brandJson as any);

const WHITE = "#FFFFFF";

const ENTER_SPRING = { damping: 20, stiffness: 100, mass: 1, overshootClamping: true };
const EXIT_SPRING = { damping: 12, stiffness: 160, mass: 1 };
const EXIT_LEAD = 12;

// --- Schema ---

const stepSchema = z.object({
  num: z.string().describe("Nummer"),
  title: z.string().describe("Titel"),
  subtitle: z.string().describe("Untertitel"),
  startSec: z.number().step(0.1).describe("Start (Sek)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sek)"),
});

export const dreiFragenSchema = projectPropsSchema.extend({
  steps: z.array(stepSchema).describe("Fragen"),
});

export type DreiFragenProps = z.infer<typeof dreiFragenSchema>;

export const dreiFragenDefaults: DreiFragenProps = {
  format: "portrait" as const,
  fps: 30 as const,
  durationInSeconds: TOTAL_DURATION_SEC,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  steps: STEPS.map((s) => ({ ...s })),
};

// --- Step Card ---

const StepCard: React.FC<{ num: string; title: string; subtitle: string }> = ({
  num,
  title,
  subtitle,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const enterProgress = spring({ frame, fps, config: ENTER_SPRING });
  const enterOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });
  const enterSlideY = Math.round(interpolate(enterProgress, [0, 1], [40, 0]));

  const exitFrame = durationInFrames - EXIT_LEAD;
  const exitProgress =
    frame >= exitFrame
      ? spring({ frame: frame - exitFrame, fps, config: EXIT_SPRING })
      : 0;
  const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);
  const exitSlideY = Math.round(interpolate(exitProgress, [0, 1], [0, -30]));

  const subDelay = 10;
  const subProgress = spring({
    frame: Math.max(0, frame - subDelay),
    fps,
    config: ENTER_SPRING,
  });
  const subOpacity = interpolate(frame, [subDelay, subDelay + 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const subSlideY = Math.round(interpolate(subProgress, [0, 1], [20, 0]));

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "flex-start",
        padding: "0 48px",
        paddingBottom: "44%",
      }}
    >
      <div
        style={{
          transform: `translateY(${enterSlideY + exitSlideY}px)`,
          opacity: enterOpacity * exitOpacity,
          width: "100%",
        }}
      >
        <div
          style={{
            background:
              "linear-gradient(135deg, rgba(16, 70, 151, 0.88) 0%, rgba(12, 52, 112, 0.92) 100%)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            borderRadius: 20,
            padding: "28px 32px",
            boxShadow:
              "0 12px 48px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 18,
              marginBottom: 14,
            }}
          >
            <div
              style={{
                minWidth: 52,
                height: 52,
                borderRadius: 14,
                backgroundColor: "rgba(255,255,255,0.15)",
                border: "1.5px solid rgba(255,255,255,0.25)",
                color: WHITE,
                fontFamily: "Open Sans",
                fontWeight: 800,
                fontSize: 24,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              {num}
            </div>

            <div
              style={{
                fontFamily: "Open Sans",
                fontWeight: 800,
                fontSize: 36,
                color: WHITE,
                textTransform: "uppercase",
                letterSpacing: 1,
              }}
            >
              {title}
            </div>
          </div>

          <div
            style={{
              height: 1,
              backgroundColor: "rgba(255,255,255,0.15)",
              marginBottom: 14,
              opacity: subOpacity,
            }}
          />

          <div
            style={{
              opacity: subOpacity,
              transform: `translateY(${subSlideY}px)`,
            }}
          >
            <div
              style={{
                fontFamily: "Open Sans",
                fontWeight: 500,
                fontSize: 28,
                color: "rgba(255,255,255,0.85)",
                lineHeight: 1.4,
              }}
            >
              {subtitle}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// --- Main Composition ---

export const TopFotografieDreiFragen: React.FC<DreiFragenProps> = ({
  review,
  steps,
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {steps.map((step, i) => (
          <Sequence
            key={`step-${i}`}
            from={s(step.startSec)}
            durationInFrames={s(step.durationSec)}
            name={`Frage ${step.num}: ${step.title}`}
          >
            <StepCard num={step.num} title={step.title} subtitle={step.subtitle} />
          </Sequence>
        ))}

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
