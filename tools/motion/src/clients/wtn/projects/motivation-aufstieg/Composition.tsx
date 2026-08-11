// WTN — 1.5 "Motivation & Aufstieg" — Overlay (9:16)
import React from "react";
import { AbsoluteFill } from "remotion";
import { z } from "zod";
import { projectPropsSchema } from "../../../../core/schemas";
import { SceneRenderer, VoicePreview } from "../../components";
import { SCENES } from "./scenes";

export const motivationAufstiegSchema = projectPropsSchema.extend({
  timeOffsetSec: z
    .number()
    .step(0.1)
    .describe("Globaler Zeit-Offset (Sek) zum Ausrichten aufs Footage"),
  previewVoice: z
    .boolean()
    .describe("Studio-Vorschau: Voiceover (Ton) für den Sync-Check"),
});

export type MotivationAufstiegProps = z.infer<typeof motivationAufstiegSchema>;

export const motivationAufstiegDefaults: MotivationAufstiegProps = {
  format: "portrait",
  fps: 25,
  durationInSeconds: 63.76,
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

export const WTNMotivationAufstieg: React.FC<MotivationAufstiegProps> = ({
  review,
  timeOffsetSec,
  previewVoice,
}) => {
  return (
    <AbsoluteFill>
      <VoicePreview
        src="projects/wtn-5x-ads/05-motivation-aufstieg.wav"
        enabled={previewVoice}
      />
      <SceneRenderer
        scenes={SCENES}
        timeOffsetSec={timeOffsetSec}
        review={review}
      />
    </AbsoluteFill>
  );
};
