// ============================================================
// REM Dachbeschichtung — Scene Phase Hook
// Provides normalized 0→1 progress within a scene
// ============================================================

import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { SCENES, FPS } from "./constants";

type SceneName = keyof typeof SCENES;

interface ScenePhase {
  /** 0→1 linear progress through the scene */
  progress: number;
  /** Current frame relative to scene start (0-based) */
  localFrame: number;
  /** Whether this scene is currently active */
  active: boolean;
  /** Scene duration in frames */
  duration: number;
  /** Enter progress: 0→1 over first enterFrames */
  enterProg: number;
  /** Exit progress: 0→1 over last exitFrames */
  exitProg: number;
}

export function useScenePhase(
  sceneName: SceneName,
  enterFrames: number = 15,
  exitFrames: number = 15
): ScenePhase {
  const frame = useCurrentFrame();
  const scene = SCENES[sceneName];

  const localFrame = frame - scene.start;
  const active = frame >= scene.start && frame < scene.end;

  const progress = interpolate(frame, [scene.start, scene.end], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const enterProg = interpolate(localFrame, [0, enterFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const exitProg = interpolate(
    localFrame,
    [scene.dur - exitFrames, scene.dur],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return {
    progress,
    localFrame,
    active,
    duration: scene.dur,
    enterProg,
    exitProg,
  };
}
