// ============================================================
// REM Dachbeschichtung V2 Premium — Main Composition
// Same as V2 but with rim light on the house
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
  SLIDES,
  CAMERA_KEYFRAMES,
  HOUSE_BASE_SCALE,
  INTRO_DUR,
  OUTRO_DUR,
  TOTAL_FRAMES,
} from "./constants";

// Scene components
import { MinimalHouse } from "./components/MinimalHouse";
import { RainEffect } from "./components/RainEffect";
import { WeatheringEffect } from "./components/WeatheringEffect";
import { MossEffect } from "./components/MossEffect";
import { CoatingWipe } from "./components/CoatingWipe";
import { WaterProtection } from "./components/WaterProtection";
import { FinaleEffect } from "./components/FinaleEffect";
import { SlideText } from "./components/SlideText";
import { AmbientBackground } from "./components/AmbientBackground";

// --- Schema & Defaults ---

export const remDachV2PremiumSchema = projectPropsSchema.extend({});
export type RemDachV2PremiumProps = z.infer<typeof remDachV2PremiumSchema>;

export const remDachV2PremiumDefaults: RemDachV2PremiumProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: 45.5,
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

  // House position: right for problem scenes (1-3), left for solution scenes (4-6)
  // Static on each side, smooth glide only during text-free gap (frames 475-515)
  const cx = interpolate(frame, [475, 515], [W * 0.72, W * 0.20], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: smooth,
  });

  // Clamp to keyframe range
  if (frame <= kfs[0].frame) {
    return {
      yaw: kfs[0].yaw * DEG2RAD,
      pitch: kfs[0].pitch * DEG2RAD,
      scale: kfs[0].scale * HOUSE_BASE_SCALE,
      cx,
      cy: H * 0.62,
    };
  }
  if (frame >= kfs[kfs.length - 1].frame) {
    const last = kfs[kfs.length - 1];
    return {
      yaw: last.yaw * DEG2RAD,
      pitch: last.pitch * DEG2RAD,
      scale: last.scale * HOUSE_BASE_SCALE,
      cx,
      cy: H * 0.62,
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
    cx,
    cy: H * 0.62,
  };
}

// --- Main Component ---

export const RemDachbeschichtungV2Premium: React.FC<RemDachV2PremiumProps> = (props) => {
  const frame = useCurrentFrame();

  // === Camera State ===
  const baseCam = getCameraState(frame);

  // Add subtle organic noise — dampened near snap transitions
  const transitionFrames = [85, 195, 210, 320, 335, 495, 510, 670, 685, 908, 923];
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

  // === Intro / Outro Build Progress ===
  const buildProgress = Math.min(
    interpolate(frame, [0, INTRO_DUR], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: appleEase,
    }),
    interpolate(frame, [TOTAL_FRAMES - OUTRO_DUR, TOTAL_FRAMES], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: appleEase,
    }),
  );

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
    <AbsoluteFill style={{ backgroundColor: props.transparent ? "transparent" : BG }}>
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
          {/* Animated radial gradients — multiple layers for richness */}
          <radialGradient
            id="bgGrad1"
            cx={`${50 + Math.sin(frame * 0.02) * 15}%`}
            cy={`${50 + Math.cos(frame * 0.015) * 12}%`}
            r="70%"
          >
            <stop offset="0%" stopColor="#1C1C48" />
            <stop offset="12%" stopColor="#171740" />
            <stop offset="25%" stopColor="#131336" />
            <stop offset="40%" stopColor="#0F0F2C" />
            <stop offset="55%" stopColor="#0B0B22" />
            <stop offset="70%" stopColor="#08081A" />
            <stop offset="85%" stopColor="#050512" />
            <stop offset="100%" stopColor="#020208" />
          </radialGradient>
          <radialGradient
            id="bgGrad2"
            cx={`${35 + Math.cos(frame * 0.012) * 20}%`}
            cy={`${60 + Math.sin(frame * 0.018) * 15}%`}
            r="50%"
          >
            <stop offset="0%" stopColor="#1A1245" stopOpacity="0.4" />
            <stop offset="40%" stopColor="#0E0A2A" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#020206" stopOpacity="0" />
          </radialGradient>
          <radialGradient
            id="bgGrad3"
            cx={`${65 + Math.sin(frame * 0.025) * 12}%`}
            cy={`${40 + Math.cos(frame * 0.02) * 10}%`}
            r="45%"
          >
            <stop offset="0%" stopColor="#0D1A3A" stopOpacity="0.3" />
            <stop offset="50%" stopColor="#060E25" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#020206" stopOpacity="0" />
          </radialGradient>
          {/* Noise dither — generates monochrome grain at low alpha, composited over gradient */}
          <filter id="noiseGrain" x="0" y="0" width="100%" height="100%" colorInterpolationFilters="sRGB">
            <feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="4" stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
            <feComponentTransfer>
              <feFuncA type="linear" slope="0.035" />
            </feComponentTransfer>
          </filter>
        </defs>

        {/* Animated gradient background — layered for smooth depth */}
        <g opacity={buildProgress}>
          <rect x="0" y="0" width={W} height={H} fill="url(#bgGrad1)" />
          <rect x="0" y="0" width={W} height={H} fill="url(#bgGrad2)" />
          <rect x="0" y="0" width={W} height={H} fill="url(#bgGrad3)" />
          <rect x="0" y="0" width={W} height={H} filter="url(#noiseGrain)" />
        </g>

        {/* Vignette */}
        <g opacity={buildProgress}>
          <AmbientBackground />
        </g>

        {/* Persistent house — line-drawing intro/outro */}
        <MinimalHouse
          cam={cam}
          roofColor={roofColor}
          coatingProgress={coatingProgress}
          buildProgress={buildProgress}
        />

        {/* Scene effect layers — multiplied with buildProgress */}
        {s1Fade * buildProgress > 0.01 && (
          <g opacity={s1Fade * buildProgress}>
            <RainEffect sceneProgress={s1Prog} cam={cam} />
          </g>
        )}
        {s2Fade * buildProgress > 0.01 && (
          <g opacity={s2Fade * buildProgress}>
            <WeatheringEffect sceneProgress={s2Prog} cam={cam} />
          </g>
        )}
        {s3Fade * buildProgress > 0.01 && (
          <g opacity={s3Fade * buildProgress}>
            <MossEffect sceneProgress={s3Prog} cam={cam} />
          </g>
        )}
        {s4Fade * buildProgress > 0.01 && (
          <g opacity={s4Fade * buildProgress}>
            <CoatingWipe coatingProgress={coatingProgress} cam={cam} />
          </g>
        )}
        {s5Fade * buildProgress > 0.01 && (
          <g opacity={s5Fade * buildProgress}>
            <WaterProtection sceneProgress={s5Prog} cam={cam} />
          </g>
        )}
        {s6Fade * buildProgress > 0.01 && (
          <g opacity={s6Fade * buildProgress}>
            <FinaleEffect sceneProgress={s6Prog} cam={cam} showSparkles={false} />
          </g>
        )}

        {/* Text layers — multiplied with buildProgress */}
        {[s1Fade, s2Fade, s3Fade, s4Fade, s5Fade, s6Fade].map((fade, i) =>
          fade * buildProgress > 0.01 ? (
            <g key={`slide-${i}`} opacity={fade * buildProgress}>
              <SlideText {...SLIDES[i]} />
            </g>
          ) : null,
        )}
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
