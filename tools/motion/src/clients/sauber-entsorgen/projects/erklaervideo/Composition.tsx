// ============================================================
// Sauber Entsorgen — Erklärvideo (Full Overlay)
// Transparent alpha overlay (ProRes 4444) over the GF footage.
// 16:9 landscape (1920×1080), 25fps, ~121s.
// GF on the right → all graphics anchored left; face zone = right half.
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
  StackList,
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

export const erklaervideoSchema = projectPropsSchema.extend({
  timeOffsetSec: z
    .number()
    .step(0.1)
    .describe("Globaler Zeit-Offset (Sek) zum Ausrichten aufs Footage"),
});

export type ErklaervideoProps = z.infer<typeof erklaervideoSchema>;

// --- Default Props ---

export const erklaervideoDefaults: ErklaervideoProps = {
  format: "landscape" as const,
  fps: 25 as const,
  durationInSeconds: 121,
  transparent: true,
  timeOffsetSec: 0,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    // GF on the right (golden ratio) — keep the right half clear.
    faceZone: { top: 0.04, bottom: 0.99, left: 0.5, right: 1.0 },
    guideOpacity: 0.35,
  },
};

// --- Composition ---

export const SauberEntsorgenErklaervideo: React.FC<ErklaervideoProps> = ({
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
                  align="left"
                  offsetY={scene.offsetY}
                />
              );
              break;
            case "chips":
              name = `Chips: ${scene.chips.map((c) => c.label).join(" · ")}`;
              body = (
                <ServiceChips
                  chips={scene.chips}
                  align="left"
                  bottomRatio={scene.bottomRatio}
                  staggerFrames={scene.staggerFrames}
                />
              );
              break;
            case "list":
              name = `List: ${scene.heading ?? scene.items.map((it) => it.label).join(", ")}`;
              body = (
                <StackList
                  heading={scene.heading}
                  items={scene.items}
                  anchorY={scene.anchorY}
                  staggerFrames={scene.staggerFrames}
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
                  anchorY={scene.anchorY}
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
                  anchorY={scene.anchorY}
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
                  anchorY={scene.anchorY}
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
