// ============================================================
// Top Fotografie — Die 5 Typen von Schulleitern
// Transparent overlay (ProRes 4444 with Alpha)
// 9:16 portrait (1080×1920), 30fps, 117s
// Punchy scale-in with bounce — Social Media Style
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
import {
  INTRO,
  TYPEN,
  CTA,
  TOTAL_DURATION_SEC,
} from "./transcript";
import type { SceneEntry, IntroEntry, CtaEntry } from "./transcript";
import brandJson from "../../brand.json";

loadFont();
const ci = loadBrand("top-fotografie", brandJson as any);

// --- Brand Colors ---
const PRIMARY = "#104697";
const SECONDARY = "#9D9D9C";
const WHITE = "#FFFFFF";

// --- Spring Configs ---
const PUNCH_SPRING = { damping: 8, stiffness: 180, mass: 1 };
const SMOOTH_SPRING = { damping: 14, stiffness: 120, mass: 1 };
const EXIT_SPRING = { damping: 12, stiffness: 160, mass: 1 };

// --- Exit timing ---
const EXIT_LEAD = 12; // frames before sequence end

// --- Schemas ---

const introSchema = z.object({
  mainText: z.string().describe("Haupttext"),
  subText: z.string().describe("Untertitel"),
  startSec: z.number().step(0.1).describe("Start (Sek)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sek)"),
});

const typSchema = z.object({
  label: z.string().describe("Label (z.B. 'TYP 1 — Der Misstrauische')"),
  startSec: z.number().step(0.1).describe("Start (Sek)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sek)"),
});

const ctaSchema = z.object({
  headline: z.string().describe("CTA Headline"),
  subline: z.string().describe("CTA Subline"),
  website: z.string().describe("Website"),
  startSec: z.number().step(0.1).describe("Start (Sek)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sek)"),
});

export const schulleiterTypenSchema = projectPropsSchema.extend({
  intro: introSchema.describe("Intro"),
  typen: z.array(typSchema).describe("Typ-Labels"),
  cta: ctaSchema.describe("CTA End-Card"),
});

export type SchulleiterTypenProps = z.infer<typeof schulleiterTypenSchema>;

// --- Default Props ---

export const schulleiterTypenDefaults: SchulleiterTypenProps = {
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
  intro: { ...INTRO },
  typen: TYPEN.map((t) => ({ ...t })),
  cta: { ...CTA },
};

// =============================================================
// Sub-Components
// =============================================================

/** Punchy scale-in label tag for each "Typ" */
const TypLabel: React.FC<{ label: string }> = ({ label }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // --- Entrance ---
  const entranceScale = spring({
    frame,
    fps,
    config: PUNCH_SPRING,
  });

  const entranceOpacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateRight: "clamp",
  });

  // --- Exit ---
  const exitFrame = durationInFrames - EXIT_LEAD;
  const exitProgress =
    frame >= exitFrame
      ? spring({
          frame: frame - exitFrame,
          fps,
          config: EXIT_SPRING,
        })
      : 0;

  const exitScale = interpolate(exitProgress, [0, 1], [1, 0.3]);
  const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);

  const scale = entranceScale * exitScale;
  const opacity = entranceOpacity * exitOpacity;

  // Parse "TYP X" and rest
  const dashIndex = label.indexOf("\u2014");
  const typNumber = dashIndex > 0 ? label.slice(0, dashIndex).trim() : "";
  const typName = dashIndex > 0 ? label.slice(dashIndex + 1).trim() : label;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "flex-start",
        padding: "0 54px",
        paddingBottom: "48%",
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          opacity,
          transformOrigin: "left center",
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 16,
          }}
        >
          <div
            style={{
              backgroundColor: PRIMARY,
              color: WHITE,
              fontFamily: "Open Sans",
              fontWeight: 800,
              fontSize: 42,
              padding: "8px 24px",
              borderRadius: 8,
              letterSpacing: 2,
              textTransform: "uppercase",
              boxShadow: `0 4px 24px rgba(16, 70, 151, 0.5)`,
            }}
          >
            {typNumber}
          </div>
          <div
            style={{
              fontFamily: "Open Sans",
              fontWeight: 700,
              fontSize: 38,
              color: WHITE,
              textShadow:
                "0 2px 12px rgba(0,0,0,0.7), 0 0 4px rgba(0,0,0,0.5)",
              letterSpacing: 1,
            }}
          >
            {typName}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Intro title card */
const IntroTitle: React.FC<{ mainText: string; subText: string }> = ({
  mainText,
  subText,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // --- Entrance ---
  const mainScale = spring({ frame, fps, config: PUNCH_SPRING });
  const mainOpacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateRight: "clamp",
  });

  const subDelay = 10;
  const subScale = spring({
    frame: Math.max(0, frame - subDelay),
    fps,
    config: SMOOTH_SPRING,
  });
  const subOpacity = interpolate(
    frame,
    [subDelay, subDelay + 8],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // --- Exit ---
  const exitFrame = durationInFrames - EXIT_LEAD;
  const exitProgress =
    frame >= exitFrame
      ? spring({ frame: frame - exitFrame, fps, config: EXIT_SPRING })
      : 0;

  const exitScale = interpolate(exitProgress, [0, 1], [1, 0.3]);
  const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Main text */}
      <div
        style={{
          transform: `scale(${mainScale * exitScale})`,
          opacity: mainOpacity * exitOpacity,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: "Open Sans",
            fontWeight: 800,
            fontSize: 72,
            color: WHITE,
            textTransform: "uppercase",
            letterSpacing: 4,
            textShadow:
              "0 4px 24px rgba(0,0,0,0.7), 0 0 8px rgba(16,70,151,0.6)",
          }}
        >
          {mainText}
        </div>
      </div>

      {/* Sub text */}
      <div
        style={{
          transform: `scale(${subScale * exitScale})`,
          opacity: subOpacity * exitOpacity,
          marginTop: 16,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: "Open Sans",
            fontWeight: 600,
            fontSize: 34,
            color: WHITE,
            textShadow: "0 2px 12px rgba(0,0,0,0.6)",
            backgroundColor: "rgba(16, 70, 151, 0.4)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
            padding: "12px 32px",
            borderRadius: 8,
          }}
        >
          {subText}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** CTA End Card */
const CtaCard: React.FC<{
  headline: string;
  subline: string;
  website: string;
}> = ({ headline, subline, website }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // --- Entrance ---
  const cardScale = spring({ frame, fps, config: SMOOTH_SPRING });
  const cardOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });

  const websiteDelay = 14;
  const websiteScale = spring({
    frame: Math.max(0, frame - websiteDelay),
    fps,
    config: PUNCH_SPRING,
  });
  const websiteOpacity = interpolate(
    frame,
    [websiteDelay, websiteDelay + 6],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // --- Exit ---
  const exitFrame = durationInFrames - EXIT_LEAD;
  const exitProgress =
    frame >= exitFrame
      ? spring({ frame: frame - exitFrame, fps, config: EXIT_SPRING })
      : 0;

  const exitScale = interpolate(exitProgress, [0, 1], [1, 0.3]);
  const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Card container */}
      <div
        style={{
          transform: `scale(${cardScale * exitScale})`,
          opacity: cardOpacity * exitOpacity,
          textAlign: "center",
          backgroundColor: "rgba(16, 70, 151, 0.85)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          padding: "48px 40px",
          borderRadius: 16,
          maxWidth: "85%",
          boxShadow: "0 8px 40px rgba(0,0,0,0.4)",
        }}
      >
        <div
          style={{
            fontFamily: "Open Sans",
            fontWeight: 800,
            fontSize: 44,
            color: WHITE,
            marginBottom: 12,
            letterSpacing: 1,
          }}
        >
          {headline}
        </div>
        <div
          style={{
            fontFamily: "Open Sans",
            fontWeight: 400,
            fontSize: 30,
            color: "rgba(255,255,255,0.85)",
          }}
        >
          {subline}
        </div>
      </div>

      {/* Website badge */}
      <div
        style={{
          transform: `scale(${websiteScale * exitScale})`,
          opacity: websiteOpacity * exitOpacity,
          marginTop: 28,
        }}
      >
        <div
          style={{
            fontFamily: "Open Sans",
            fontWeight: 700,
            fontSize: 36,
            color: WHITE,
            backgroundColor: PRIMARY,
            padding: "12px 36px",
            borderRadius: 50,
            boxShadow: `0 4px 20px rgba(16, 70, 151, 0.6)`,
            letterSpacing: 1,
          }}
        >
          {website}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// =============================================================
// Main Composition
// =============================================================

export const TopFotografieSchulleiterTypen: React.FC<
  SchulleiterTypenProps
> = ({ review, intro, typen, cta }) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.floor(sec * fps);

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {/* Intro */}
        <Sequence
          from={s(intro.startSec)}
          durationInFrames={s(intro.durationSec)}
          name="Intro"
        >
          <IntroTitle mainText={intro.mainText} subText={intro.subText} />
        </Sequence>

        {/* 5 Typen Labels */}
        {typen.map((typ, i) => (
          <Sequence
            key={`typ-${i}`}
            from={s(typ.startSec)}
            durationInFrames={s(typ.durationSec)}
            name={typ.label}
          >
            <TypLabel label={typ.label} />
          </Sequence>
        ))}

        {/* CTA End Card */}
        <Sequence
          from={s(cta.startSec)}
          durationInFrames={s(cta.durationSec)}
          name="CTA"
        >
          <CtaCard
            headline={cta.headline}
            subline={cta.subline}
            website={cta.website}
          />
        </Sequence>

        {/* Review overlay */}
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
