// ============================================================
// Seniorenstiftung — SceneRenderer (v2, word-synced)
// Maps a Scene[] to <Sequence>s and draws the ReviewOverlay.
// Word timestamps in scenes are ABSOLUTE video seconds (from the
// ElevenLabs word index); this renderer converts them to frames
// relative to each scene's start. Shared by all 5 compositions.
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { reviewConfigSchema } from "../../../core/schemas";
import { ReviewOverlay } from "../../../components/layout/ReviewOverlay";
import { HighlightPop } from "./HighlightPop";
import { ChipRow, type ChipSpec } from "./ChipRow";
import { CTASlide } from "./CTASlide";
import type { ChipIconName } from "./Icons";

export type Scene =
  | {
      kind: "highlight";
      startSec: number;
      durationSec: number;
      text: string;
      emphasis?: string;
      /** ABSOLUTE second the emphasis word is spoken (word index). */
      emphasisAtSec?: number;
      bottomRatio?: number;
      fontSizeRatio?: number;
    }
  | {
      kind: "chips";
      startSec: number;
      durationSec: number;
      /** atSec = ABSOLUTE second the chip's word is spoken. */
      chips: { label: string; atSec: number; icon?: ChipIconName }[];
      bottomRatio?: number;
      fontSizeRatio?: number;
    }
  | {
      kind: "cta";
      startSec: number;
      durationSec: number;
      headline: string;
      sub: string;
      emphasis?: string;
      anchorY?: number;
    };

interface SceneRendererProps {
  scenes: Scene[];
  timeOffsetSec: number;
  review?: z.infer<typeof reviewConfigSchema>;
}

export const SceneRenderer: React.FC<SceneRendererProps> = ({
  scenes,
  timeOffsetSec,
  review,
}) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) =>
    Math.max(0, Math.floor((sec + timeOffsetSec) * fps));

  return (
    <AbsoluteFill>
      {scenes.map((scene, i) => {
        const from = s(scene.startSec);
        const durationInFrames = Math.floor(scene.durationSec * fps);
        const key = `scene-${i}-${scene.kind}`;
        let name: string = scene.kind;
        let body: React.ReactNode = null;

        switch (scene.kind) {
          case "highlight": {
            name = `Highlight: ${scene.text}`;
            const emphasisDelayFrames =
              scene.emphasisAtSec != null
                ? Math.max(
                    0,
                    Math.round((scene.emphasisAtSec - scene.startSec) * fps),
                  )
                : undefined;
            body = (
              <HighlightPop
                text={scene.text}
                emphasis={scene.emphasis}
                emphasisDelayFrames={emphasisDelayFrames}
                bottomRatio={scene.bottomRatio}
                fontSizeRatio={scene.fontSizeRatio}
              />
            );
            break;
          }
          case "chips": {
            name = `Chips: ${scene.chips.map((c) => c.label).join(" · ")}`;
            const chips: ChipSpec[] = scene.chips.map((c) => ({
              label: c.label,
              icon: c.icon,
              delayFrames: Math.max(
                0,
                Math.round((c.atSec - scene.startSec) * fps),
              ),
            }));
            body = (
              <ChipRow
                chips={chips}
                bottomRatio={scene.bottomRatio}
                fontSizeRatio={scene.fontSizeRatio}
              />
            );
            break;
          }
          case "cta":
            name = `CTA: ${scene.headline}`;
            body = (
              <CTASlide
                headline={scene.headline}
                sub={scene.sub}
                emphasis={scene.emphasis}
                anchorY={scene.anchorY}
              />
            );
            break;
        }

        return (
          <Sequence
            key={key}
            from={from}
            durationInFrames={durationInFrames}
            name={name}
          >
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
