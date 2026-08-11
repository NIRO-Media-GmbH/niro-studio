// ============================================================
// REM Gewerbedach-Reinigung — Main Composition
// Testimonial-synchron: Szenen & Texte folgen dem Kunden-O-Ton
// (Transcribe REM Gewerbedach Reinigung.srt, 1h-Timecode-Offset)
// Stil: identisch zu Dachbeschichtung V2 Premium (Line-Art, Rim Light)
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
  GREY_WEATHERED,
  GREY_DIRTY,
  SCENES,
  SCENES_OV,
  OVERLAP,
  GLIDE,
  SLIDES,
  CAMERA_KEYFRAMES,
  HOUSE_BASE_SCALE,
  INTRO_DUR,
  OUTRO_DUR,
  TOTAL_FRAMES,
} from "./constants";

// Scene components
import { MinimalHouse } from "./components/MinimalHouse";
import { WeatheringEffect } from "./components/WeatheringEffect";
import { CoatingWipe } from "./components/CoatingWipe";
import { CraneRig } from "./components/CraneRig";
import { PVPanels } from "./components/PVPanels";
import { FinaleEffect } from "./components/FinaleEffect";
import { SlideText } from "./components/SlideText";
import { AmbientBackground } from "./components/AmbientBackground";

// --- Schema & Defaults ---

export const remGewerbedachSchema = projectPropsSchema.extend({});
export type RemGewerbedachProps = z.infer<typeof remGewerbedachSchema>;

export const remGewerbedachDefaults: RemGewerbedachProps = {
  format: "landscape-4k" as const,
  fps: 25 as const,
  durationInSeconds: TOTAL_FRAMES / 25, // 106 s — O-Ton endet bei 103,44 s
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

  // Halle rechts für Szenen 1–4 (Text links), Glide in der Sprechpause,
  // danach links (Text rechts)
  const cx = interpolate(frame, [GLIDE.start, GLIDE.end], [W * 0.72, W * 0.22], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: smooth,
  });

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

export const RemGewerbedachReinigung: React.FC<RemGewerbedachProps> = (props) => {
  const frame = useCurrentFrame();

  // === Camera State ===
  const baseCam = getCameraState(frame);

  // Subtiles organisches Rauschen — an Snap-Übergängen gedämpft
  const transitionFrames = [280, 298, 770, 785, 1030, 1047, 1459, 1650, 1743, 1975, 1996, 2451, 2458, 2466];
  let minTransDist = Infinity;
  for (const tf of transitionFrames) {
    minTransDist = Math.min(minTransDist, Math.abs(frame - tf));
  }
  const noiseScale = Math.min(1, minTransDist / 25);
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

  // 1. Dachfarbe: verwittertes Grau, dunkelt während der Zustandsszene nach
  const roofColor = interpolateColors(
    frame,
    [0, SCENES.weathering.start, SCENES.weathering.start + 80, SCENES.weathering.end],
    [GREY_WEATHERED, GREY_WEATHERED, GREY_DIRTY, GREY_DIRTY],
  );

  // 2. Beschichtung (REM-Rot) läuft während der Kran-Szene über das Dach
  const coatingProgress = interpolate(
    frame,
    [SCENES.kran.start + 75, SCENES.kran.end - 40],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: emphasized,
    },
  );

  // 3. Kran zeichnet sich zu Szenenbeginn, verschwindet mit der Szene
  const craneDraw = interpolate(frame, [SCENES.kran.start, SCENES.kran.start + 75], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  // === Scene Fade Opacities ===

  const s1Fade = sceneFade(frame, SCENES_OV.weathering.start, SCENES_OV.weathering.end, OVERLAP, true, false);
  const s2Fade = sceneFade(frame, SCENES_OV.angebot.start, SCENES_OV.angebot.end, OVERLAP, false, false);
  const s3Fade = sceneFade(frame, SCENES_OV.preis.start, SCENES_OV.preis.end, OVERLAP, false, false);
  const s4Fade = sceneFade(frame, SCENES_OV.kran.start, SCENES_OV.kran.end, OVERLAP, false, false);
  const s5Fade = sceneFade(frame, SCENES_OV.garantie.start, SCENES_OV.garantie.end, OVERLAP, false, false);
  const s6Fade = sceneFade(frame, SCENES_OV.ergebnis.start, SCENES_OV.ergebnis.end, OVERLAP, false, false);
  const s7Fade = sceneFade(frame, SCENES_OV.finale.start, SCENES_OV.finale.end, OVERLAP, false, true);

  // === Scene Progress Values ===

  const s1Prog = interpolate(frame, [SCENES.weathering.start, SCENES.weathering.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s7Prog = interpolate(frame, [SCENES.finale.start, SCENES.finale.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

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
          <filter id="noiseGrain" x="0" y="0" width="100%" height="100%" colorInterpolationFilters="sRGB">
            <feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="4" stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
            <feComponentTransfer>
              <feFuncA type="linear" slope="0.035" />
            </feComponentTransfer>
          </filter>
        </defs>

        {/* Animated gradient background */}
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

        {/* Persistente Halle — Line-Draw Intro/Outro */}
        <MinimalHouse
          cam={cam}
          roofColor={roofColor}
          coatingProgress={coatingProgress}
          buildProgress={buildProgress}
        />

        {/* Szene 1 — Zustand: Risse + Staub */}
        {s1Fade * buildProgress > 0.01 && (
          <g opacity={s1Fade * buildProgress}>
            <WeatheringEffect sceneProgress={s1Prog} cam={cam} />
          </g>
        )}

        {/* Szene 4 — Kran + Beschichtungskante */}
        {s4Fade * buildProgress > 0.01 && (
          <g opacity={s4Fade * buildProgress}>
            <CraneRig cam={cam} drawProgress={craneDraw} wipeU={coatingProgress} />
            <CoatingWipe coatingProgress={coatingProgress} cam={cam} />
          </g>
        )}

        {/* Szene 6 — Ergebnis: PV-Module + Glanz */}
        {s6Fade * buildProgress > 0.01 && (
          <g opacity={s6Fade * buildProgress}>
            <PVPanels cam={cam} />
          </g>
        )}

        {/* Szene 7 — Finale: Sparkles */}
        {s7Fade * buildProgress > 0.01 && (
          <g opacity={s7Fade * buildProgress}>
            <FinaleEffect sceneProgress={s7Prog} cam={cam} showSparkles={true} />
          </g>
        )}

        {/* Text layers — wortsynchron zum O-Ton */}
        {[s1Fade, s2Fade, s3Fade, s4Fade, s5Fade, s6Fade, s7Fade].map((fade, i) =>
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
