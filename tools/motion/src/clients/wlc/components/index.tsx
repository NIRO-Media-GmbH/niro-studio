// ============================================================
// WLC Würth-Logistik — Shared Client Components
// CI: Würth Rot #CC0000, Schwarz/Weiß, Wuerth Sans Black Cond
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
import { fitText } from "@remotion/layout-utils";

// --- Fonts (lokale Würth-TTFs) ---
//
// CI-Umstellung 09.09.2026: Der Kunde hat die Hausschrift von der alten
// Familie `Wuerth` (V1.30) auf `Wuerth Sans` (V1_000) gewechselt. Mapping
// nach optischem Abgleich — NICHT nach den OS/2-Gewichtszahlen, die in der
// alten Familie untypisch gesetzt sind (altes "Bold" trägt wght 500):
//   Extra Bold Cond (800) → BlackCond   — Headlines, condensed
//   Bold            (500) → Black       — Demi (600) rendert sichtbar
//                                         dünner als das alte Bold und
//                                         schwächt die Rollen-Bauchbinden
//   Book            (300) → Book
// Die Family-Strings sind bewusst eigene Aliase (interne Namen lauten
// "Wuerth Sans Black Condensed" o. ä.) — verhindert Kollision mit einer
// evtl. systemweit installierten Würth-Schrift.

export const FONT_XBDCN = "Wuerth Sans Black Cond";
export const FONT_BOLD = "Wuerth Sans Black";
export const FONT_BOOK = "Wuerth Sans Book";

// --- Metrik-Angleichung an die abgelöste Familie ---
//
// Die Overlays liegen über bereits geschnittenen und freigegebenen Videos —
// die Elemente MÜSSEN pixelgleich sitzen wie in der alten Fassung.
// Wuerth Sans hat aber eine andere Zeilenbox als die alte Wuerth-Familie:
//   alt (hhea, upem 2048): (2030 + 427 + 307) / 2048 = 1.3496 em
//   neu (hhea, upem 1000): ( 780 + 220 + 150) / 1000 = 1.1500 em
// Chrome zieht für `line-height: normal` die hhea-Werte (am Render
// gegengemessen: alt 1.3474 em, neu 1.1458 em). Ohne Ausgleich schrumpft
// deshalb JEDE Box, deren Höhe sich aus dem Text ergibt, um ~0.2 em, und
// die Baseline wandert nach oben — im V1-Splash gemessen: roter Kasten
// 12 px flacher, Schrift 13 px höher.
//
// Lösung: Der neuen Schrift beim Laden die hhea-Metriken des jeweils
// abgelösten Schnitts aufprägen (Prozent = Wert/upem der ALTEN Datei).
// Damit bleiben Zeilenboxen UND Baselines identisch — an allen Stellen,
// nicht nur dort, wo eine lineHeight gesetzt ist.
const FACES = [
  {
    family: FONT_XBDCN,
    file: "WuerthSans-BlackCond_V1_000.ttf",
    // löst Wuerth Extra Bold Cond ab: asc 2030, desc 427, gap 307 / 2048
    ascentOverride: "99.121%",
    descentOverride: "20.850%",
    lineGapOverride: "14.990%",
  },
  {
    family: FONT_BOLD,
    file: "WuerthSans-Black_V1_000.ttf",
    // löst Wuerth Bold ab: asc 1939, desc 464, gap 307 / 2048
    ascentOverride: "94.678%",
    descentOverride: "22.656%",
    lineGapOverride: "14.990%",
  },
  {
    family: FONT_BOOK,
    file: "WuerthSans-Book_V1_000.ttf",
    // löst Wuerth Book ab: asc 1978, desc 479, gap 307 / 2048
    ascentOverride: "96.582%",
    descentOverride: "23.389%",
    lineGapOverride: "14.990%",
  },
] as const;

// `loadFont` aus @remotion/fonts kann keine Metrik-Overrides — deshalb die
// FontFace-API direkt. Guard, weil der Modulcode auch in Node ausgewertet
// wird (getCompositions), wo es kein `document` gibt.
const fontsReady =
  typeof document === "undefined"
    ? Promise.resolve([])
    : Promise.all(
        FACES.map(async (f) => {
          const face = new FontFace(f.family, `url(${staticFile(`clients/wlc/fonts/${f.file}`)})`, {
            ascentOverride: f.ascentOverride,
            descentOverride: f.descentOverride,
            lineGapOverride: f.lineGapOverride,
          });
          await face.load();
          document.fonts.add(face);
          return face;
        })
      );

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
