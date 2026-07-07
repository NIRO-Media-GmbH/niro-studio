// WTN — 1.2 "Technik, die du woanders nicht anfasst" — Overlay (9:16)
import React from "react";
import { AbsoluteFill } from "remotion";
import { z } from "zod";
import { projectPropsSchema } from "../../../../core/schemas";
import { SceneRenderer, VoicePreview } from "../../components";
import { SCENES } from "./scenes";

export const technikSchema = projectPropsSchema.extend({
  timeOffsetSec: z
    .number()
    .step(0.1)
    .describe("Globaler Zeit-Offset (Sek) zum Ausrichten aufs Footage"),
  previewVoice: z
    .boolean()
    .describe("Studio-Vorschau: Voiceover (Ton) für den Sync-Check"),
});

export type TechnikProps = z.infer<typeof technikSchema>;

export const technikDefaults: TechnikProps = {
  format: "portrait",
  fps: 25,
  durationInSeconds: 59.76,
  transparent: true,
  timeOffsetSec: 0,
  previewVoice: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    faceZone: { top: 0.08, bottom: 0.45, left: 0.18, right: 0.82 },
    guideOpacity: 0.35,
  },
};

export const WTNTechnik: React.FC<TechnikProps> = ({
  review,
  timeOffsetSec,
  previewVoice,
}) => {
  return (
    <AbsoluteFill>
      <VoicePreview src="wtn/vo/02-technik.wav" enabled={previewVoice} />
      <SceneRenderer
        scenes={SCENES}
        timeOffsetSec={timeOffsetSec}
        review={review}
      />
    </AbsoluteFill>
  );
};
