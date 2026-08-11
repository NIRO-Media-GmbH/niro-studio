// ============================================================
// REM Gewerbedach — Testimonial-Overlay (Full Overlay)
// Transparentes Alpha-Overlay (ProRes 4444) über das Interview-
// Footage. 16:9 landscape (1920×1080), 25fps, ~105s.
// Sprecher rechts angenommen → Grafiken links verankert;
// Face Zone = rechte Hälfte (per review.faceZone anpassbar).
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/Inter";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  BrandIntro,
  KeywordLowerThird,
  ServiceChips,
  StackList,
} from "../../components/overlay";
import { SCENES } from "./transcript";

loadFont();

// --- Schema ---

export const remGewerbedachOverlaySchema = projectPropsSchema.extend({
  timeOffsetSec: z
    .number()
    .step(0.1)
    .describe("Globaler Zeit-Offset (Sek) zum Ausrichten aufs Footage"),
});

export type RemGewerbedachOverlayProps = z.infer<typeof remGewerbedachOverlaySchema>;

// --- Default Props ---

export const remGewerbedachOverlayDefaults: RemGewerbedachOverlayProps = {
  format: "landscape" as const,
  fps: 25 as const,
  durationInSeconds: 105,
  transparent: true,
  timeOffsetSec: 0,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    // Sprecher rechts — rechte Hälfte freihalten.
    faceZone: { top: 0.04, bottom: 0.99, left: 0.5, right: 1.0 },
    guideOpacity: 0.35,
  },
};

// --- Composition ---

export const RemGewerbedachOverlay: React.FC<RemGewerbedachOverlayProps> = ({
  review,
  timeOffsetSec,
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.max(0, Math.floor((sec + timeOffsetSec) * fps));

  return (
    <AbsoluteFill>
      {SCENES.map((scene, i) => {
        const from = s(scene.startSec);
        const durationInFrames = Math.floor(scene.durationSec * fps);
        const key = `scene-${i}-${scene.kind}`;

        let name: string = scene.kind;
        let body: React.ReactNode = null;

        switch (scene.kind) {
          case "brand":
            name = "Brand: REM Malerfachbetrieb";
            body = <BrandIntro />;
            break;
          case "cue":
            name = `Cue: ${scene.word}`;
            body = (
              <KeywordLowerThird
                word={scene.word}
                icon={scene.icon}
                tone={scene.tone}
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
  );
};
