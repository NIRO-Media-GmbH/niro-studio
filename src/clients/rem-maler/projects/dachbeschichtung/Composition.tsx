// ============================================================
// REM Dachbeschichtung — Main Composition
// 37s Premium 3D Clay/Toy Animation: Roof transformation story
// 4K (3840×2160) at 25fps = 925 Frames
// Smooth cross-fade transitions between scenes
// ============================================================

import React from "react";
import { z } from "zod";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  interpolateColors,
  spring,
} from "remotion";
import { noise2D } from "@remotion/noise";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  IsometricRoof,
  RainSystem,
  CrackSystem,
  MossGrowth,
  CoatingWipe,
  WaterBeading,
  VaporSystem,
  SparkleStars,
} from "../../components";
import {
  SCENES,
  SCENES_OVERLAP,
  OVERLAP,
  WARM_GOLD,
  WARM_GOLD_LIGHT,
  WARM_GOLD_DARK,
  GREY_WEATHERED,
  GREY_WEATHERED_DARK,
  RED,
  RED_LIGHT,
  DARK_BG,
  DARK_NAVY,
} from "../../components/constants";
import { EASING_PRESETS } from "../../../../utils/easing";

// --- Schema ---
export const remDachbeschichtungSchema = projectPropsSchema.extend({});
export type RemDachbeschichtungProps = z.infer<typeof remDachbeschichtungSchema>;

export const remDachbeschichtungDefaults: RemDachbeschichtungProps = {
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

// Cross-fade helper: returns 0→1→1→0 across the scene with overlap fades
function sceneFade(
  frame: number,
  sceneStart: number,
  sceneEnd: number,
  overlapFrames: number,
  isFirst: boolean = false,
  isLast: boolean = false
): number {
  const fadeIn = isFirst
    ? 1
    : interpolate(frame, [sceneStart, sceneStart + overlapFrames], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
  const fadeOut = isLast
    ? 1
    : interpolate(frame, [sceneEnd - overlapFrames, sceneEnd], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
  return Math.min(fadeIn, fadeOut);
}

// --- Composition ---
export const RemDachbeschichtung: React.FC<RemDachbeschichtungProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // === ROOF STATE MACHINE ===
  // (uses original SCENES for roof state, SCENES_OVERLAP for effect sequences)

  // 1. Draw-in (frames 0-40)
  const drawProgress = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 80 },
  });

  // 2. Fill opacity (fades in after outline)
  const fillOpacity = interpolate(frame, [20, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASING_PRESETS.smooth,
  });

  // 3. Roof color transitions: Gold → Grey (via coating it becomes Red)
  const roofColor = interpolateColors(
    frame,
    [0, SCENES.weather.end, SCENES.weathering.start + 30, SCENES.weathering.end],
    [WARM_GOLD, WARM_GOLD, WARM_GOLD_DARK, GREY_WEATHERED]
  );

  const tileAccent = interpolateColors(
    frame,
    [0, SCENES.weather.end, SCENES.weathering.start + 30, SCENES.weathering.end],
    [WARM_GOLD_LIGHT, WARM_GOLD_LIGHT, WARM_GOLD, GREY_WEATHERED_DARK]
  );

  // 4. Noise/weathering texture
  const noiseOpacity = interpolate(
    frame,
    [SCENES.weathering.start, SCENES.weathering.end, SCENES.coating.start, SCENES.coating.end],
    [0, 0.6, 0.6, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // 5. Coating wipe progress (Scene 4)
  const coatingProgress = interpolate(
    frame,
    [SCENES.coating.start + 20, SCENES.coating.end - 20],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.emphasized }
  );

  // 6. Glow intensity (Scene 6)
  const glowIntensity = interpolate(
    frame,
    [SCENES.finale.start, SCENES.finale.end],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.decelerate }
  );

  // 7. Camera shake (Scene 2)
  const shakeActive =
    frame >= SCENES.weathering.start + 50 && frame <= SCENES.weathering.start + 70;
  const shakeIntensity = shakeActive ? 6 : 0;
  const shake = {
    x: noise2D("shakeX", frame * 0.5, 0) * shakeIntensity,
    y: noise2D("shakeY", 0, frame * 0.5) * shakeIntensity,
  };

  // 8. Specular sweep (Scene 5)
  const specularPos = interpolate(
    frame,
    [SCENES.waterProof.start + 30, SCENES.waterProof.end - 30],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.smooth }
  );

  // 9. Background color shift
  const bgColor = interpolateColors(
    frame,
    [SCENES.coating.start, SCENES.coating.end],
    [DARK_BG, DARK_NAVY]
  );

  // 10. Slow zoom for finale
  const zoomScale = interpolate(
    frame,
    [SCENES.finale.start, SCENES.finale.end],
    [1, 1.08],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASING_PRESETS.appleEase }
  );

  // === SCENE FADE OPACITIES (smooth cross-fade transitions) ===
  const SO = SCENES_OVERLAP;
  const weatherFade = sceneFade(frame, SO.weather.start, SO.weather.end, OVERLAP, true, false);
  const weatheringFade = sceneFade(frame, SO.weathering.start, SO.weathering.end, OVERLAP, false, false);
  const mossFade = sceneFade(frame, SO.moss.start, SO.moss.end, OVERLAP, false, false);
  const coatingFade = sceneFade(frame, SO.coating.start, SO.coating.end, OVERLAP, false, false);
  const waterProofFade = sceneFade(frame, SO.waterProof.start, SO.waterProof.end, OVERLAP, false, false);
  const finaleFade = sceneFade(frame, SO.finale.start, SO.finale.end, OVERLAP, false, true);

  // Scene local frames (using overlap timing)
  const scene1Local = frame - SO.weather.start;
  const scene1Prog = interpolate(frame, [SO.weather.start, SO.weather.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const scene2Local = frame - SO.weathering.start;
  const scene2Prog = interpolate(frame, [SO.weathering.start, SO.weathering.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const scene3Local = frame - SO.moss.start;
  const scene3Prog = interpolate(frame, [SO.moss.start, SO.moss.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const scene4Local = frame - SO.coating.start;

  const scene5Local = frame - SO.waterProof.start;
  const scene5Prog = interpolate(frame, [SO.waterProof.start, SO.waterProof.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const scene6Local = frame - SO.finale.start;
  const scene6Prog = interpolate(frame, [SO.finale.start, SO.finale.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: bgColor }}>
      {/* Zoom wrapper for finale */}
      <AbsoluteFill
        style={{
          transform: `scale(${zoomScale})`,
          transformOrigin: "50% 45%",
        }}
      >
        {/* === PERSISTENT ROOF === */}
        <IsometricRoof
          drawProgress={drawProgress}
          fillOpacity={fillOpacity}
          roofColor={roofColor}
          tileAccent={tileAccent}
          noiseOpacity={noiseOpacity}
          coatingProgress={coatingProgress}
          coatingColor={RED}
          coatingAccent={RED_LIGHT}
          glowIntensity={glowIntensity}
          shake={shake}
          specularPos={specularPos}
        />

        {/* === SCENE 1: Weather (cross-fades out) === */}
        <Sequence from={SO.weather.start} durationInFrames={SO.weather.dur}>
          <AbsoluteFill style={{ opacity: weatherFade }}>
            <RainSystem progress={scene1Prog} localFrame={scene1Local} />
          </AbsoluteFill>
        </Sequence>

        {/* === SCENE 2: Weathering / Cracks (cross-fades in/out) === */}
        <Sequence from={SO.weathering.start} durationInFrames={SO.weathering.dur}>
          <AbsoluteFill style={{ opacity: weatheringFade }}>
            <CrackSystem progress={scene2Prog} localFrame={scene2Local} />
          </AbsoluteFill>
        </Sequence>

        {/* === SCENE 3: Moss Growth (cross-fades in/out) === */}
        <Sequence from={SO.moss.start} durationInFrames={SO.moss.dur}>
          <AbsoluteFill style={{ opacity: mossFade }}>
            <MossGrowth progress={scene3Prog} localFrame={scene3Local} />
          </AbsoluteFill>
        </Sequence>

        {/* === SCENE 4: Coating Wipe — MONEY SHOT (cross-fades in/out) === */}
        <Sequence from={SO.coating.start} durationInFrames={SO.coating.dur}>
          <AbsoluteFill style={{ opacity: coatingFade }}>
            <CoatingWipe wipeProgress={coatingProgress} localFrame={scene4Local} />
          </AbsoluteFill>
        </Sequence>

        {/* === SCENE 5: Water Beading + Vapor (cross-fades in/out) === */}
        <Sequence from={SO.waterProof.start} durationInFrames={SO.waterProof.dur}>
          <AbsoluteFill style={{ opacity: waterProofFade }}>
            <WaterBeading progress={scene5Prog} localFrame={scene5Local} />
            <VaporSystem progress={scene5Prog} localFrame={scene5Local} />
          </AbsoluteFill>
        </Sequence>

        {/* === SCENE 6: Finale — Perfect Roof (fades in, stays) === */}
        <Sequence from={SO.finale.start} durationInFrames={SO.finale.dur}>
          <AbsoluteFill style={{ opacity: finaleFade }}>
            <SparkleStars progress={scene6Prog} localFrame={scene6Local} />
          </AbsoluteFill>
        </Sequence>
      </AbsoluteFill>

      {/* Review overlay (conditional, never in export) */}
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
