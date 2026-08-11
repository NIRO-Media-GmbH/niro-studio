// ============================================================
// REM Dachbeschichtung V2 — Main Composition
// Orchestrates all scenes, 3D camera, and render layers
// ============================================================

import React from "react";
import { z } from "zod";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  interpolateColors,
} from "remotion";
import { noise2D } from "@remotion/noise";
import { projectPropsSchema } from "../../../../core/schemas";
import { EASING_PRESETS } from "../../../../utils/easing";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import type { CameraState } from "./projection";

// Constants
import {
  W,
  H,
  BG,
  TERRACOTTA,
  TERRACOTTA_DIRTY,
  SCENES,
  SCENES_OV,
  OVERLAP,
  TEXT,
  CAMERA_KEYFRAMES,
  HOUSE_BASE_SCALE,
} from "./constants";

// Scene components
import { MinimalHouse } from "./components/MinimalHouse";
import { RainEffect } from "./components/RainEffect";
import { WeatheringEffect } from "./components/WeatheringEffect";
import { MossEffect } from "./components/MossEffect";
import { CoatingWipe } from "./components/CoatingWipe";
import { WaterProtection } from "./components/WaterProtection";
import { FinaleEffect } from "./components/FinaleEffect";
import { TextReveal } from "./components/TextReveal";
import { AmbientBackground } from "./components/AmbientBackground";

// --- Schema & Defaults ---

export const remDachV2Schema = projectPropsSchema.extend({});
export type RemDachV2Props = z.infer<typeof remDachV2Schema>;

export const remDachV2Defaults: RemDachV2Props = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 37,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
};

// --- Helpers ---

const appleEase = EASING_PRESETS.appleEase;
const emphasized = EASING_PRESETS.emphasized;
const smooth = EASING_PRESETS.smooth;
const DEG2RAD = Math.PI / 180;

function sceneFade(
  frame: number,
  start: number,
  end: number,
  overlap: number,
  isFirst: boolean,
  isLast: boolean,
): number {
  const fadeIn = isFirst
    ? 1
    : interpolate(frame, [start, start + overlap], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: appleEase,
      });
  const fadeOut = isLast
    ? 1
    : interpolate(frame, [end - overlap, end], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: appleEase,
      });
  return Math.min(fadeIn, fadeOut);
}

/**
 * Interpolate camera state from keyframes at the given frame.
 */
function getCameraState(frame: number): CameraState {
  const kfs = CAMERA_KEYFRAMES;

  // Clamp to keyframe range
  if (frame <= kfs[0].frame) {
    return {
      yaw: kfs[0].yaw * DEG2RAD,
      pitch: kfs[0].pitch * DEG2RAD,
      scale: kfs[0].scale * HOUSE_BASE_SCALE,
      cx: W * 0.6,
      cy: H * 0.58,
    };
  }
  if (frame >= kfs[kfs.length - 1].frame) {
    const last = kfs[kfs.length - 1];
    return {
      yaw: last.yaw * DEG2RAD,
      pitch: last.pitch * DEG2RAD,
      scale: last.scale * HOUSE_BASE_SCALE,
      cx: W * 0.6,
      cy: H * 0.58,
    };
  }

  // Find surrounding keyframes
  let i = 0;
  while (i < kfs.length - 1 && kfs[i + 1].frame <= frame) i++;
  const a = kfs[i];
  const b = kfs[i + 1];

  const yaw = interpolate(frame, [a.frame, b.frame], [a.yaw, b.yaw], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });
  const pitch = interpolate(frame, [a.frame, b.frame], [a.pitch, b.pitch], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });
  const scale = interpolate(frame, [a.frame, b.frame], [a.scale, b.scale], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  return {
    yaw: yaw * DEG2RAD,
    pitch: pitch * DEG2RAD,
    scale: scale * HOUSE_BASE_SCALE,
    cx: W * 0.6,
    cy: H * 0.58,
  };
}

// --- Main Component ---

export const RemDachbeschichtungV2: React.FC<RemDachV2Props> = (props) => {
  const frame = useCurrentFrame();

  // === Camera State ===
  const baseCam = getCameraState(frame);

  // Add subtle organic noise — dampened near snap transitions
  const transitionFrames = [10, 120, 135, 245, 260, 420, 435, 595, 610, 770, 785];
  let minTransDist = Infinity;
  for (const tf of transitionFrames) {
    minTransDist = Math.min(minTransDist, Math.abs(frame - tf));
  }
  const noiseScale = Math.min(1, minTransDist / 25);
  // Fade noise out during finale so house settles
  const finaleFade = interpolate(frame, [SCENES.finale.start, SCENES.finale.start + 30], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const noiseAmp = 0.3 * DEG2RAD * noiseScale * finaleFade;
  const cam: CameraState = {
    ...baseCam,
    yaw: baseCam.yaw + noise2D("camYaw", frame * 0.015, 0) * noiseAmp,
    pitch: baseCam.pitch + noise2D("camPitch", 0, frame * 0.015) * noiseAmp,
  };

  // === State Machine ===

  // 1. Roof color: cream -> grey-weathered during weathering scene
  const roofColor = interpolateColors(
    frame,
    [
      0,
      SCENES.weathering.start,
      SCENES.weathering.start + 60,
      SCENES.weathering.end,
    ],
    [TERRACOTTA, TERRACOTTA, TERRACOTTA_DIRTY, TERRACOTTA_DIRTY],
  );

  // 2. Coating progress: 0->1 during coating scene
  const coatingProgress = interpolate(
    frame,
    [SCENES.coating.start + 15, SCENES.coating.end - 40],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: emphasized,
    },
  );

  // === Scene Fade Opacities ===

  const s1Fade = sceneFade(frame, SCENES_OV.weather.start, SCENES_OV.weather.end, OVERLAP, true, false);
  const s2Fade = sceneFade(frame, SCENES_OV.weathering.start, SCENES_OV.weathering.end, OVERLAP, false, false);
  const s3Fade = sceneFade(frame, SCENES_OV.moss.start, SCENES_OV.moss.end, OVERLAP, false, false);
  const s4Fade = sceneFade(frame, SCENES_OV.coating.start, SCENES_OV.coating.end, OVERLAP, false, false);
  const s5Fade = sceneFade(frame, SCENES_OV.water.start, SCENES_OV.water.end, OVERLAP, false, false);
  const s6Fade = sceneFade(frame, SCENES_OV.finale.start, SCENES_OV.finale.end, OVERLAP, false, true);

  // === Scene Progress Values ===

  const s1Prog = interpolate(frame, [SCENES.weather.start, SCENES.weather.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s2Prog = interpolate(frame, [SCENES.weathering.start, SCENES.weathering.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s3Prog = interpolate(frame, [SCENES.moss.start, SCENES.moss.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s5Prog = interpolate(frame, [SCENES.water.start, SCENES.water.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s6Prog = interpolate(frame, [SCENES.finale.start, SCENES.finale.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // === Render ===

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width={W}
        height={H}
        style={{ width: "100%", height: "100%" }}
      >
        <defs>
          <filter id="textGlow">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Ambient background */}
        <AmbientBackground />

        {/* Persistent house */}
        <MinimalHouse
          cam={cam}
          roofColor={roofColor}
          coatingProgress={coatingProgress}
        />

        {/* Scene effect layers */}
        {s1Fade > 0.01 && (
          <g opacity={s1Fade}>
            <RainEffect sceneProgress={s1Prog} cam={cam} />
          </g>
        )}
        {s2Fade > 0.01 && (
          <g opacity={s2Fade}>
            <WeatheringEffect sceneProgress={s2Prog} cam={cam} />
          </g>
        )}
        {s3Fade > 0.01 && (
          <g opacity={s3Fade}>
            <MossEffect sceneProgress={s3Prog} cam={cam} />
          </g>
        )}
        {s4Fade > 0.01 && (
          <g opacity={s4Fade}>
            <CoatingWipe coatingProgress={coatingProgress} cam={cam} />
          </g>
        )}
        {s5Fade > 0.01 && (
          <g opacity={s5Fade}>
            <WaterProtection sceneProgress={s5Prog} cam={cam} />
          </g>
        )}
        {s6Fade > 0.01 && (
          <g opacity={s6Fade}>
            <FinaleEffect sceneProgress={s6Prog} cam={cam} showSparkles={false} />
          </g>
        )}

        {/* Text layers — temporarily disabled for no-text render
        {s1Fade > 0.01 && (
          <g opacity={s1Fade}>
            <TextReveal {...TEXT.scene1.line1} exitFrame={TEXT.scene1.exitFrame} />
            <TextReveal {...TEXT.scene1.line2} exitFrame={TEXT.scene1.exitFrame} />
          </g>
        )}
        {s2Fade > 0.01 && (
          <g opacity={s2Fade}>
            <TextReveal {...TEXT.scene2.line1} exitFrame={TEXT.scene2.exitFrame} />
            <TextReveal {...TEXT.scene2.line2} exitFrame={TEXT.scene2.exitFrame} />
          </g>
        )}
        {s3Fade > 0.01 && (
          <g opacity={s3Fade}>
            <TextReveal {...TEXT.scene3.line1} exitFrame={TEXT.scene3.exitFrame} />
            <TextReveal {...TEXT.scene3.line2} exitFrame={TEXT.scene3.exitFrame} />
          </g>
        )}
        {s4Fade > 0.01 && (
          <g opacity={s4Fade}>
            <TextReveal {...TEXT.scene4.line1} exitFrame={TEXT.scene4.exitFrame} />
            <TextReveal {...TEXT.scene4.line2} exitFrame={TEXT.scene4.exitFrame} />
          </g>
        )}
        {s5Fade > 0.01 && (
          <g opacity={s5Fade}>
            <TextReveal {...TEXT.scene5.line1} exitFrame={TEXT.scene5.exitFrame} />
            <TextReveal {...TEXT.scene5.line2} exitFrame={TEXT.scene5.exitFrame} />
          </g>
        )}
        {s6Fade > 0.01 && (
          <g opacity={s6Fade}>
            <TextReveal {...TEXT.scene6.line1} />
            <TextReveal {...TEXT.scene6.line2} />
            <TextReveal {...TEXT.scene6.line3} />
          </g>
        )}
        */}
      </svg>

      {props.review?.showGuides && (
        <ReviewOverlay
          format={props.format}
          showSafeZone={props.review.showSafeZone}
          showFaceZone={props.review.showFaceZone}
          showGrid={props.review.showGrid}
          faceZone={props.review.faceZone}
          guideOpacity={props.review.guideOpacity}
        />
      )}
    </AbsoluteFill>
  );
};
