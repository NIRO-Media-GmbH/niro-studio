// ============================================================
// Autohaus Rappold · Video 2 „Kfz-Mechatroniker" — Grafiken + Untertitel „Freie Typo"
// Spec: docs/superpowers/specs/2026-09-16-rappold-video2-animation-design.md
// Zeiten = Frames im Schnitt V1 (1440 Frames) + 5 s CTA-Karte (Farbfläche, Übergang von Hannes).
// ============================================================
import "../../fonts";
import React from "react";
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile, useVideoConfig } from "remotion";
import { z } from "zod";
import { zColor } from "@remotion/zod-types";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { getDimensions } from "../../../../core/format-utils";
import { projectPropsSchema } from "../../../../core/schemas";
import { BASE_H, BASE_W, BLAU } from "../../lib";
import { SCHNITT_FRAMES } from "./daten-generiert";
import { Endcard } from "./Endcard";
import { DAUER_FRAMES } from "./grafik-plan";
import { Grafiken } from "./Grafiken";
import { Untertitel } from "./Untertitel";

export const rappoldV2Schema = projectPropsSchema.extend({
  zeigeSchnitt: z.boolean().describe("Schnitt V1 darunter (nur Vorschau)"),
  zeigeGrafiken: z.boolean().describe("Grafiken + Endcard"),
  zeigeUntertitel: z.boolean().describe("Untertitel"),
  endcardUrl: z.string().describe("URL auf der CTA-Karte"),
  endcardFarbe: zColor().describe("Farbe der CTA-Karte"),
});
export type RappoldV2Props = z.infer<typeof rappoldV2Schema>;

export const rappoldV2VorschauDefaults: RappoldV2Props = {
  format: "portrait",
  fps: 25,
  durationInSeconds: DAUER_FRAMES / 25,
  transparent: false,
  review: { showGuides: false, showSafeZone: true, showFaceZone: true, showGrid: false, guideOpacity: 0.35 },
  zeigeSchnitt: true,
  zeigeGrafiken: true,
  zeigeUntertitel: true,
  endcardUrl: "autohaus-rappold.de/karriere",
  endcardFarbe: BLAU,
};

// Lieferung: EINE Alpha-Datei mit allen Grafiken + Untertiteln (wie Craiss „Alpha-Komplett")
export const rappoldV2AlphaDefaults: RappoldV2Props = {
  ...rappoldV2VorschauDefaults,
  format: "portrait-4k",
  transparent: true,
  zeigeSchnitt: false,
};

export const calculateRappoldV2 = ({ props }: { props: RappoldV2Props }) => ({
  ...getDimensions(props.format),
  fps: 25,
  durationInFrames: DAUER_FRAMES,
});

export const RappoldV2Mechatroniker: React.FC<RappoldV2Props> = (p) => {
  const { width } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: p.transparent ? "transparent" : "#000" }}>
      {p.zeigeSchnitt ? (
        <Sequence durationInFrames={SCHNITT_FRAMES} name="Schnitt V1">
          <OffthreadVideo src={staticFile("projects/rappold-recruiting/Video2_V1_proxy.mp4")} style={{ width: "100%", height: "100%" }} />
        </Sequence>
      ) : null}
      <div style={{ position: "absolute", left: 0, top: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
        {p.zeigeGrafiken ? <Endcard url={p.endcardUrl} farbe={p.endcardFarbe} /> : null}
        {p.zeigeGrafiken ? <Grafiken /> : null}
        {p.zeigeUntertitel ? <Untertitel /> : null}
      </div>
      {p.review?.showGuides ? (
        <ReviewOverlay
          showSafeZone={p.review.showSafeZone}
          showFaceZone={p.review.showFaceZone}
          showGrid={p.review.showGrid}
          faceZone={p.review.faceZone}
          guideOpacity={p.review.guideOpacity}
        />
      ) : null}
    </AbsoluteFill>
  );
};
