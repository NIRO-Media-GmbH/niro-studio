// ============================================================
// Sauber Entsorgen — Reel 1 (9:16) "Haushaltsauflösung"
// Transparent alpha overlay (ProRes 4444) over a centered
// talking-head reel. 1080×1920, 25fps, ~61s.
// Graphics CENTERED, placed in the reels safe band (below the
// face zone, above the IG UI).
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/Inter";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  KeywordLowerThird,
  ServiceChips,
  StepCard,
  IntroCard,
  CTACard,
  type ServiceIconName,
} from "../../components";
import { SCENES } from "./transcript";
import brandJson from "../../brand.json";

loadFont();
const ci = loadBrand("sauber-entsorgen", brandJson as any);

// --- Schema ---

export const reel1Schema = projectPropsSchema.extend({
  timeOffsetSec: z
    .number()
    .step(0.1)
    .describe("Globaler Zeit-Offset (Sek) zum Ausrichten aufs Footage"),
});

export type Reel1Props = z.infer<typeof reel1Schema>;

// --- Default Props ---

export const reel1Defaults: Reel1Props = {
  format: "portrait" as const,
  fps: 25 as const,
  durationInSeconds: 61,
  transparent: true,
  timeOffsetSec: 0,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    // Reels default: face upper-center. Adjust to the real footage if needed.
    faceZone: { top: 0.08, bottom: 0.45, left: 0.18, right: 0.82 },
    guideOpacity: 0.35,
  },
};

// --- Portrait layout constants (centered, within the reels safe band) ---
const CUE_BOTTOM = 0.44; // cue/chips sit just below mid-screen
const STEP_ANCHOR = 0.5;
const INTRO_ANCHOR = 0.44;
const CTA_ANCHOR = 0.46;

// --- Composition ---

export const SauberEntsorgenReel1: React.FC<Reel1Props> = ({
  review,
  timeOffsetSec,
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.max(0, Math.floor((sec + timeOffsetSec) * fps));

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {SCENES.map((scene, i) => {
          const from = s(scene.startSec);
          const durationInFrames = Math.floor(scene.durationSec * fps);
          const key = `scene-${i}-${scene.kind}`;

          let name: string = scene.kind;
          let body: React.ReactNode = null;

          switch (scene.kind) {
            case "cue":
              name = `Cue: ${scene.word}`;
              body = (
                <KeywordLowerThird
                  word={scene.word}
                  icon={scene.icon as ServiceIconName}
                  align="center"
                  bottomRatio={CUE_BOTTOM}
                  fontSizeRatio={0.038}
                />
              );
              break;
            case "chips":
              name = `Chips: ${scene.chips.map((c) => c.label).join(" · ")}`;
              body = (
                <ServiceChips
                  chips={scene.chips}
                  align="center"
                  bottomRatio={CUE_BOTTOM}
                  staggerFrames={scene.staggerFrames}
                  fontSizeRatio={0.028}
                />
              );
              break;
            case "step":
              name = `Step ${scene.number}: ${scene.title}`;
              body = (
                <StepCard
                  number={scene.number}
                  title={scene.title}
                  subtitle={scene.subtitle}
                  icon={scene.icon as ServiceIconName}
                  align="center"
                  anchorY={STEP_ANCHOR}
                  fontSizeRatio={0.03}
                />
              );
              break;
            case "intro":
              name = `Intro: ${scene.name}`;
              body = (
                <IntroCard
                  name={scene.name}
                  role={scene.role}
                  company={scene.company}
                  align="center"
                  anchorY={INTRO_ANCHOR}
                  fontSizeRatio={0.04}
                />
              );
              break;
            case "cta":
              name = `CTA: ${scene.headline}`;
              body = (
                <CTACard
                  headline={scene.headline}
                  phone={scene.phone}
                  closing={scene.closing}
                  align="center"
                  anchorY={CTA_ANCHOR}
                  fontSizeRatio={0.038}
                />
              );
              break;
          }

          return (
            <Sequence key={key} from={from} durationInFrames={durationInFrames} name={name}>
              {body}
            </Sequence>
          );
        })}

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
