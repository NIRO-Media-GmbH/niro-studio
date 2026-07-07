// Seniorenstiftung — Putzfachkraft Overlay (transparent, 9:16)
import React from "react";
import { AbsoluteFill } from "remotion";
import { z } from "zod";
import { projectPropsSchema } from "../../../../core/schemas";
import { SceneRenderer, FootagePreview } from "../../components";
import { SCENES } from "./scenes";

export const putzfachkraftSchema = projectPropsSchema.extend({
  timeOffsetSec: z.number().step(0.1).describe("Globaler Zeit-Offset (Sek)"),
  previewFootage: z
    .boolean()
    .describe("Studio-Vorschau: Footage (Proxy, mit Ton) hinter dem Overlay"),
});

export type PutzfachkraftProps = z.infer<typeof putzfachkraftSchema>;

export const putzfachkraftDefaults: PutzfachkraftProps = {
  format: "portrait",
  fps: 25,
  durationInSeconds: 52.32,
  transparent: true,
  timeOffsetSec: 0,
  previewFootage: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    faceZone: { top: 0.08, bottom: 0.45, left: 0.18, right: 0.82 },
    guideOpacity: 0.35,
  },
};

export const PutzfachkraftOverlay: React.FC<PutzfachkraftProps> = ({
  review,
  timeOffsetSec,
  previewFootage,
}) => {
  return (
    <AbsoluteFill>
      <FootagePreview
        src="projects/seniorenstiftung-recruiting/proxy/putzfachkraft.mp4"
        enabled={previewFootage}
      />
      <SceneRenderer
        scenes={SCENES}
        timeOffsetSec={timeOffsetSec}
        review={review}
      />
    </AbsoluteFill>
  );
};
