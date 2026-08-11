// ============================================================
// WTN — SceneRenderer (word-synced)
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
import { HighlightPlain } from "./HighlightPlain";
import { ChipRow, type ChipSpec } from "./ChipRow";
import { StatPop } from "./StatPop";
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
      /** "plain" = free text without a box (for variety). Default "box". */
      variant?: "box" | "plain";
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
      kind: "stat";
      startSec: number;
      durationSec: number;
      value: number;
      prefix?: string;
      suffix?: string;
      label: string;
      /** ABSOLUTE second the number is fully spoken. */
      emphasisAtSec?: number;
      bottomRatio?: number;
    }
  | {
      kind: "cta";
      startSec: number;
      durationSec: number;
      headline: string;
      sub: string;
      emphasis?: string;
      claim?: string;
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
  const delay = (atSec: number, startSec: number) =>
    Math.max(0, Math.round((atSec - startSec) * fps));

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
            name = `Highlight${scene.variant === "plain" ? " (plain)" : ""}: ${scene.text}`;
            body =
              scene.variant === "plain" ? (
                <HighlightPlain
                  text={scene.text}
                  emphasis={scene.emphasis}
                  bottomRatio={scene.bottomRatio}
                  fontSizeRatio={scene.fontSizeRatio}
                />
              ) : (
                <HighlightPop
                  text={scene.text}
                  emphasis={scene.emphasis}
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
              delayFrames: delay(c.atSec, scene.startSec),
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
          case "stat": {
            name = `Stat: ${scene.prefix ?? ""}${scene.value}${scene.suffix ?? ""} ${scene.label}`;
            body = (
              <StatPop
                value={scene.value}
                prefix={scene.prefix}
                suffix={scene.suffix}
                label={scene.label}
                emphasisDelayFrames={
                  scene.emphasisAtSec != null
                    ? delay(scene.emphasisAtSec, scene.startSec)
                    : undefined
                }
                bottomRatio={scene.bottomRatio}
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
                claim={scene.claim}
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
