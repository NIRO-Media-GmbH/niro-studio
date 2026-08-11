// ============================================================
// WLC Würth-Logistik — Shared Client Components
// CI: Würth Rot #CC0000, Schwarz/Weiß, Wuerth Global Extra Bold Cond
// (Titel, immer Versalien) — Quelle: CD-Richtlinien 2025
// ============================================================

import React, { useEffect, useState } from "react";
import {
  AbsoluteFill,
  Easing,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { loadFont } from "@remotion/fonts";
import { fitText } from "@remotion/layout-utils";

// --- Fonts (lokale Würth-TTFs) ---

export const FONT_XBDCN = "Wuerth Global Extra Bold Cond";
export const FONT_BOLD = "Wuerth Global Bold";
export const FONT_BOOK = "Wuerth Global Book";

const fontsReady = Promise.all([
  loadFont({ family: FONT_XBDCN, url: staticFile("clients/wlc/fonts/WuerthExtraBoldCond.ttf") }),
  loadFont({ family: FONT_BOLD, url: staticFile("clients/wlc/fonts/WuerthBold.ttf") }),
  loadFont({ family: FONT_BOOK, url: staticFile("clients/wlc/fonts/WuerthBook.ttf") }),
]);

/**
 * Blockiert den Render, bis alle Würth-Fonts geladen sind.
 * Wichtig: erst nach `true` layouten (fitText misst sonst den Fallback-Font).
 */
export const useWlcFonts = (): boolean => {
  const [loaded, setLoaded] = useState(false);
  const [handle] = useState(() => delayRender("WLC Würth-Fonts laden"));
  useEffect(() => {
    let active = true;
    fontsReady.then(() => {
      if (active) {
        setLoaded(true);
        continueRender(handle);
      }
    });
    return () => {
      active = false;
    };
  }, [handle]);
  return loaded;
};

// --- CI-Farbkonstanten ---

export const WUERTH_ROT = "#CC0000";
export const WUERTH_SCHWARZ = "#000000";
export const WUERTH_WEISS = "#FFFFFF";
export const GRAU_25 = "#BFBFBF";
export const GRAU_40 = "#999999";
export const GRAU_55 = "#737373";
export const GRAU_70 = "#4D4D4D";
export const GRAU_85 = "#262626";

// ============================================================
// WlcWord — Vollbild-Versal-Wort mit Drum-Hit-Punch-In
// ============================================================

export const WlcWord: React.FC<{
  word: string;
  color?: string;
  maxWidthRatio?: number;
  maxFontRatio?: number;
  offsetY?: number;
}> = ({ word, color = WUERTH_WEISS, maxWidthRatio = 0.84, maxFontRatio = 0.19, offsetY = 0 }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const { fontSize } = fitText({
    text: word,
    withinWidth: width * maxWidthRatio,
    fontFamily: FONT_XBDCN,
    fontWeight: "normal",
  });
  const size = Math.min(fontSize, height * maxFontRatio);

  // Drum-Hit: harter Punch von 1.14 -> 1.0, danach langsamer Drift auf 1.035
  const punch = spring({
    frame,
    fps,
    config: { damping: 60, mass: 0.4, stiffness: 400, overshootClamping: true },
  });
  const punchScale = interpolate(punch, [0, 1], [1.14, 1]);
  const drift = interpolate(frame, [fps * 0.4, fps * 3], [1, 1.035], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(frame, [0, 2], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          fontFamily: FONT_XBDCN,
          fontWeight: "normal" as const,
          fontSize: size,
          color,
          letterSpacing: "0.01em",
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          opacity,
          transform: `translateY(${offsetY}px) scale(${punchScale * drift})`,
          textShadow: "0 0 60px rgba(0,0,0,0.55), 0 6px 28px rgba(0,0,0,0.45)",
        }}
      >
        {word}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================
// RedSweep — Premium-CI-Transition zwischen den 6s-Blöcken
// Zweischichtiger, leicht gescherter Wipe: Grau-85-Blade führt,
// Würth-Rot folgt mit weißer Kante. Deckt den Frame kurz voll ab
// (darunter wechselt der Cutter das Footage-Thema).
// ============================================================

export const RedSweep: React.FC<{
  durationInFrames: number;
}> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  const ease = Easing.bezier(0.6, 0, 0.4, 1);
  const skew = -12;
  // Überbreite, damit die Scherung keine Lücken an den Rändern lässt
  const panelW = width * 1.6;
  const half = durationInFrames / 2;

  // Beide Panels laufen von rechts außen nach links außen durch;
  // Rot führt, Grau folgt versetzt (sichtbar als dunkle Kante hinter Rot).
  const progress = (offset: number) =>
    interpolate(frame, [offset, half + offset, durationInFrames + offset], [1.05, 0, -1.05], {
      easing: ease,
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });

  const redX = progress(0) * panelW;
  const grauX = progress(3) * panelW;

  const panel = (x: number, bg: string, edge?: boolean): React.CSSProperties => ({
    position: "absolute",
    top: "-10%",
    left: `${(width - panelW) / 2}px`,
    width: panelW,
    height: "120%",
    background: bg,
    transform: `translateX(${x}px) skewX(${skew}deg)`,
    borderLeft: edge ? `${Math.max(3, width * 0.004)}px solid ${WUERTH_WEISS}` : undefined,
    borderRight: edge ? `${Math.max(3, width * 0.004)}px solid ${WUERTH_WEISS}` : undefined,
  });

  return (
    <AbsoluteFill>
      <div style={panel(grauX, GRAU_85)} />
      <div style={panel(redX, WUERTH_ROT, true)} />
    </AbsoluteFill>
  );
};

// ============================================================
// WlcStatement — Zeile des Auflösungs-Trios ("MEIN WEG." …)
// Punkt am Satzende in WEISS (Kundenfeedback 21.07.: keine roten
// Punkte am Satzende, wenn Text weiß ist — gilt global).
// ============================================================

export const WlcStatement: React.FC<{
  text: string;
  fontSize: number;
  delayFrames: number;
}> = ({ text, fontSize, delayFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - delayFrames;

  const punch = spring({
    frame: Math.max(local, 0),
    fps,
    config: { damping: 60, mass: 0.4, stiffness: 400, overshootClamping: true },
  });
  const scale = interpolate(punch, [0, 1], [1.12, 1]);
  const opacity = local < 0 ? 0 : interpolate(local, [0, 2], [0, 1], { extrapolateRight: "clamp" });

  const endsWithDot = text.trim().endsWith(".");
  const body = endsWithDot ? text.trim().slice(0, -1) : text.trim();

  return (
    <div
      style={{
        fontFamily: FONT_XBDCN,
        fontWeight: "normal" as const,
        fontSize,
        color: WUERTH_WEISS,
        letterSpacing: "0.01em",
        textTransform: "uppercase",
        whiteSpace: "nowrap",
        lineHeight: 1.12,
        opacity,
        transform: `scale(${scale})`,
        textShadow: "0 0 60px rgba(0,0,0,0.55), 0 6px 28px rgba(0,0,0,0.45)",
      }}
    >
      {body}
      {endsWithDot && <span style={{ color: WUERTH_WEISS }}>.</span>}
    </div>
  );
};
