// ============================================================
// WLC — Video 4 (Fachkraft-Aufstieg) + Video 5 (Wachstum)
// Overlays für die FERTIGEN Schnitte — v2 „mehr Punch" (David):
//   - Hooks mit Punch + Micro-Shake + rotem Highlight-Sweep auf
//     dem Schlüsselwort; Position pro Video (V5 unter der Face-Zone!)
//   - Splash: geschrägte Bars (Sport-Look, passt zum Wappen)
//   - V4: ZEITSTRAHL für den Werdegang (Linie + Pin-Nodes wie die
//     Map-Pins, Labels alternierend, „VOR 9 JAHREN" → „HEUTE")
//   - Captions in zwei Stilen: „keyword" (großes Wort + Subline)
//     und „bar" (Grau-Fläche mit roter Kante)
// Face-Zone (Default 8–45 % Höhe) bleibt frei: alle Elemente ≥ 58 %,
// außer V4-Hook (40 % — Gang-Shot ohne Gesicht; per Prop schiebbar).
// Timing aus Material/Transkript Fertige Videos/1.4.srt + 1.5.srt.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";
import { z } from "zod";
import { fitText } from "@remotion/layout-utils";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  FONT_BOLD,
  FONT_XBDCN,
  GRAU_55,
  GRAU_85,
  WUERTH_ROT,
  WUERTH_WEISS,
  useWlcFonts,
} from "../../components";

const PUNCH = { damping: 60, mass: 0.4, stiffness: 400, overshootClamping: true };

// --- Schemas ---

const hookLineSchema = z.object({
  text: z.string().describe("Hook-Zeile"),
  highlight: z.string().optional().describe("Schlüsselwort (roter Sweep)"),
  startSec: z.number().step(0.01).describe("Start (Sek)"),
  endSec: z.number().step(0.01).describe("Ende (Sek)"),
});

const splashSchema = z.object({
  name: z.string().describe("Name (rote Bar)"),
  role: z.string().describe("Rolle (graue Bar)"),
  startSec: z.number().step(0.01).describe("Start (Sek)"),
  endSec: z.number().step(0.01).describe("Ende (Sek)"),
});

const captionSchema = z.object({
  style: z.enum(["keyword", "bar"]).describe("Stil"),
  text: z.string().describe("Haupttext"),
  sub: z.string().optional().describe("Subline (nur keyword)"),
  startSec: z.number().step(0.01).describe("Start (Sek)"),
  endSec: z.number().step(0.01).describe("Ende (Sek)"),
});

const stationSchema = z.object({
  label: z.string().describe("Station"),
  sub: z.string().optional().describe("Zusatz (z. B. VOR 9 JAHREN)"),
  startSec: z.number().step(0.01).describe("Erscheint bei (Sek)"),
});

export const wlcTalkOverlaySchema = projectPropsSchema.extend({
  hookTop: z.number().min(0.1).max(0.85).step(0.01).describe("Hook-Y (Anteil Höhe)"),
  hookLines: z.array(hookLineSchema).describe("Hook-Zeilen"),
  splash: splashSchema.optional().describe("Personen-Splash"),
  captions: z.array(captionSchema).describe("Captions"),
  stations: z.array(stationSchema).describe("Zeitstrahl-Stationen (V4)"),
  tickerEndSec: z.number().step(0.1).describe("Zeitstrahl ausblenden bei (Sek)"),
});

export type WlcTalkOverlayProps = z.infer<typeof wlcTalkOverlaySchema>;

// --- Timings aus 1.4.srt (Video 4, ~48 s) ---

export const wlcV4OverlayDefaults: WlcTalkOverlayProps = {
  format: "portrait" as const,
  fps: 25 as const,
  // Neuer Export 29.07. inkl. Endcard-Nachlauf (Sprache unverändert bis ~48 s)
  durationInSeconds: 51.7,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  hookTop: 0.4,
  hookLines: [
    // Kundenwunsch 21.07. („den gleichen") — ACHTUNG: ElevenLabs-VO sagt
    // weiterhin „denselben", ggf. VO neu generieren
    { text: "WENN DU SEIT JAHREN DEN GLEICHEN GANG LÄUFST …", startSec: 0.12, endSec: 5.6 },
    { text: "… UND DICH FRAGST, OB'S DAS WAR …", highlight: "DAS WAR …", startSec: 2.8, endSec: 5.6 },
  ],
  splash: {
    // Kundenwunsch Runde 2 (Replay 0:21) + David 31.08.: GRUPPENLEITER.
    // bleibt, graue Bar bekommt Cornelias vollen Wortlaut
    // „WLC Würth-Logistik | Standort Kupferzell"
    name: "GRUPPENLEITER.",
    role: "WLC WÜRTH-LOGISTIK | STANDORT KUPFERZELL",
    startSec: 7.6,
    endSec: 11.8,
  },
  captions: [
    {
      style: "keyword",
      text: "WEITERENTWICKLUNG.",
      // Wortlaut Cornelia 21.07. (Kommentar 3)
      sub: "DIE GEFÖRDERT WIRD",
      startSec: 21.8,
      endSec: 27.8,
    },
  ],
  // Zeitstrahl weg (Kundenwunsch 30.07.) — Werdegang läuft nur im O-Ton
  stations: [],
  tickerEndSec: 0,
};

// --- Timings aus 1.5.srt (Video 5, ~68 s) ---

export const wlcV5OverlayDefaults: WlcTalkOverlayProps = {
  format: "portrait" as const,
  fps: 25 as const,
  // Neuer Schnitt 29.07.: Improve-Passage raus, Endcard-Nachlauf im Export
  durationInSeconds: 66.2,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  // Hook-Sprecher ist on camera → Hook UNTER der Face-Zone
  hookTop: 0.62,
  hookLines: [
    { text: "DU ARBEITEST IN EINEM KLEINEN LAGER …", highlight: "KLEINEN LAGER", startSec: 3.28, endSec: 7.8 },
    { text: "… UND WILLST TEIL VON ETWAS GROSSEM SEIN?", highlight: "GROSSEM", startSec: 5.2, endSec: 7.8 },
  ],
  splash: {
    name: "MARVIN.",
    role: "GRUPPENLEITER LAGERLOGISTIK · SEIT 9 JAHREN BEI WLC",
    startSec: 8.6,
    endSec: 13.0,
  },
  captions: [
    { style: "keyword", text: "FTS.", sub: "FAHRERLOSE TRANSPORTSYSTEME", startSec: 22.0, endSec: 25.2 },
    { style: "bar", text: "TEIL DER WÜRTH-GRUPPE", startSec: 39.6, endSec: 42.8 },
    // Kundenfeedback 21.07.: Improve ≠ Ergonomie. David hat „Improve" aus dem
    // O-Ton geschnitten — Card jetzt wortgenau auf der Ergonomie-Aussage
    // (52,0–56,8 s: „…den Mitarbeitern etwas Gutes zu tun")
    { style: "keyword", text: "ERGONOMIE.", sub: "DEN MITARBEITERN ETWAS GUTES TUN", startSec: 52.1, endSec: 57.6 },
  ],
  stations: [],
  tickerEndSec: 0,
};

// --- Helfer ---

const useInOut = (inF: number, outF: number) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fadeF = Math.round(fps * 0.16);
  if (frame < inF || frame > outF) return { visible: false, opacity: 0 };
  const opacity =
    interpolate(frame, [inF, inF + 2], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }) *
    interpolate(frame, [outF - fadeF, outF], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  return { visible: true, opacity };
};

const usePunchShake = (startF: number) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = Math.max(frame - startF, 0);
  const p = spring({ frame: local, fps, config: PUNCH });
  const scale = interpolate(p, [0, 1], [1.14, 1]);
  const shakeAmt = interpolate(local, [0, Math.round(fps * 0.22)], [4, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const shakeX = Math.sin(local * 2.1) * shakeAmt;
  const shakeY = Math.cos(local * 1.7) * shakeAmt * 0.5;
  return { scale, shakeX, shakeY };
};

// --- Hook-Zeile: Punch + Shake + roter Highlight-Sweep ---

const PunchLine: React.FC<{
  text: string;
  highlight?: string;
  inF: number;
  outF: number;
  fontSize: number;
}> = ({ text, highlight, inF, outF, fontSize }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { visible, opacity } = useInOut(inF, outF);
  const { scale, shakeX, shakeY } = usePunchShake(inF);

  const hlStart = inF + Math.round(fps * 0.3);
  const hlWipe = interpolate(frame, [hlStart, hlStart + Math.round(fps * 0.25)], [0, 1], {
    easing: Easing.bezier(0.6, 0, 0.4, 1),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  if (!visible) return null;

  const idx = highlight ? text.indexOf(highlight) : -1;
  const before = idx >= 0 ? text.slice(0, idx) : text;
  const hl = idx >= 0 ? highlight! : "";
  const after = idx >= 0 ? text.slice(idx + hl.length) : "";

  return (
    <div
      style={{
        fontFamily: FONT_XBDCN,
        fontWeight: "normal" as const,
        fontSize,
        color: WUERTH_WEISS,
        textAlign: "center",
        lineHeight: 1.14,
        opacity,
        transform: `translate(${shakeX}px, ${shakeY}px) scale(${scale})`,
        textShadow: "0 0 40px rgba(0,0,0,0.55), 0 4px 20px rgba(0,0,0,0.45)",
        whiteSpace: "nowrap",
      }}
    >
      {before}
      {hl && (
        <span style={{ position: "relative", display: "inline-block", padding: "0 0.14em" }}>
          <span
            style={{
              position: "absolute",
              inset: "0.02em -0.02em",
              backgroundColor: WUERTH_ROT,
              transform: `scaleX(${hlWipe})`,
              transformOrigin: "left",
            }}
          />
          <span style={{ position: "relative" }}>{hl}</span>
        </span>
      )}
      {after}
    </div>
  );
};

// --- Geschrägte Bar (Splash + „bar"-Captions) ---

const SkewBar: React.FC<{
  text: string;
  bg: string;
  inF: number;
  outF: number;
  fontSize: number;
  fontFamily?: string;
  redEdge?: boolean;
}> = ({ text, bg, inF, outF, fontSize, fontFamily = FONT_XBDCN, redEdge }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const { visible } = useInOut(inF, outF);
  const wipe =
    interpolate(frame, [inF, inF + Math.round(fps * 0.28)], [0, 1], {
      easing: Easing.bezier(0.6, 0, 0.4, 1),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }) *
    interpolate(frame, [outF - Math.round(fps * 0.2), outF], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  const { scale, shakeX, shakeY } = usePunchShake(inF);
  if (!visible) return null;
  return (
    <div
      style={{
        position: "relative",
        display: "inline-block",
        transform: `translate(${shakeX}px, ${shakeY}px) scale(${scale})`,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundColor: bg,
          transform: `skewX(-8deg) scaleX(${wipe})`,
          transformOrigin: "left",
          borderLeft: redEdge ? `${Math.max(3, width * 0.0055)}px solid ${WUERTH_ROT}` : undefined,
          boxShadow: "0 6px 24px rgba(0,0,0,0.35)",
        }}
      />
      <div
        style={{
          position: "relative",
          padding: `${height * 0.0075}px ${height * 0.018}px`,
          fontFamily,
          fontWeight: "normal" as const,
          fontSize,
          color: WUERTH_WEISS,
          textTransform: "uppercase",
          letterSpacing: "0.03em",
          opacity: wipe > 0.5 ? 1 : 0,
          whiteSpace: "nowrap",
        }}
      >
        {text}
      </div>
    </div>
  );
};

// --- Keyword-Card: großes Wort + Subline ---

const KeywordCard: React.FC<{
  text: string;
  sub?: string;
  inF: number;
  outF: number;
}> = ({ text, sub, inF, outF }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const { visible, opacity } = useInOut(inF, outF);
  const { scale, shakeX, shakeY } = usePunchShake(inF);
  const subOp = interpolate(frame, [inF + Math.round(fps * 0.25), inF + Math.round(fps * 0.45)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const subY = interpolate(frame, [inF + Math.round(fps * 0.25), inF + Math.round(fps * 0.45)], [14, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  if (!visible) return null;

  const mainSize = Math.min(
    fitText({
      text,
      withinWidth: width * 0.8,
      fontFamily: FONT_XBDCN,
      fontWeight: "normal",
    }).fontSize,
    height * 0.048
  );
  const endsWithDot = text.trim().endsWith(".");
  const body = endsWithDot ? text.trim().slice(0, -1) : text.trim();

  return (
    <div style={{ textAlign: "center", opacity }}>
      <div
        style={{
          fontFamily: FONT_XBDCN,
          fontWeight: "normal" as const,
          fontSize: mainSize,
          color: WUERTH_WEISS,
          lineHeight: 1.05,
          transform: `translate(${shakeX}px, ${shakeY}px) scale(${scale})`,
          textShadow: "0 0 40px rgba(0,0,0,0.55), 0 4px 20px rgba(0,0,0,0.45)",
          whiteSpace: "nowrap",
        }}
      >
        {body}
        {endsWithDot && <span style={{ color: WUERTH_WEISS }}>.</span>}
      </div>
      {sub && (
        <div
          style={{
            fontFamily: FONT_BOLD,
            fontSize: height * 0.0145,
            letterSpacing: "0.14em",
            color: "rgba(255,255,255,0.85)",
            textTransform: "uppercase",
            marginTop: height * 0.006,
            opacity: subOp,
            transform: `translateY(${subY}px)`,
            textShadow: "0 2px 14px rgba(0,0,0,0.5)",
          }}
        >
          {sub}
        </div>
      )}
    </div>
  );
};

// --- Zeitstrahl (V4-Werdegang) ---

const Timeline: React.FC<{
  stations: { label: string; sub?: string; startSec: number }[];
  endSec: number;
  top: number;
}> = ({ stations, endSec, top }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  const n = stations.length;
  if (n < 2) return null;

  const firstF = F(stations[0].startSec);
  const endF = F(endSec);
  if (frame < firstF - Math.round(fps * 0.3) || frame > endF) return null;

  const fadeOut = interpolate(frame, [endF - Math.round(fps * 0.24), endF], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Basislinie zeichnet sich kurz vor Station 1 auf
  const baseIn = interpolate(frame, [firstF - Math.round(fps * 0.3), firstF], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const pct = (i: number) => (i / (n - 1)) * 100;

  // Roter Fortschritt: fährt in den ~6 Frames VOR jedem Wort zur Node
  let progress = 0;
  for (let i = 1; i < n; i++) {
    const stF = F(stations[i].startSec);
    progress +=
      (pct(i) - pct(i - 1)) *
      interpolate(frame, [stF - 6, stF], [0, 1], {
        easing: Easing.out(Easing.quad),
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
  }

  const lineH = Math.max(3, height * 0.0022);

  // Kamera: konstanter Zoom, Fokus fährt smooth zum aktiven Posten
  // (Lesbarkeit — David 2026-07-16). Fokus-Fenster breiter als die
  // Fortschritts-Animation, damit die Fahrt weich wirkt.
  const ZOOM = 1.5;
  let camPct = 0;
  for (let i = 1; i < n; i++) {
    const stF = F(stations[i].startSec);
    camPct +=
      (pct(i) - pct(i - 1)) *
      interpolate(frame, [stF - 12, stF + 3], [0, 1], {
        easing: Easing.inOut(Easing.cubic),
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
  }
  const focusX = camPct / 100;
  const contW = width * 0.74;
  const camTx = (0.5 - focusX) * contW;

  return (
    <div
      style={{
        position: "absolute",
        top: `${top * 100}%`,
        left: "13%",
        right: "13%",
        opacity: fadeOut,
      }}
    >
      <div
        style={{
          position: "relative",
          width: "100%",
          transform: `translateX(${camTx}px) scale(${ZOOM})`,
          transformOrigin: `${focusX * 100}% 50%`,
        }}
      >
      {/* Basislinie + roter Fortschritt */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          height: lineH,
          backgroundColor: GRAU_55,
          transform: `scaleX(${baseIn})`,
          transformOrigin: "left",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 0,
          width: `${progress}%`,
          height: lineH * 1.6,
          top: -lineH * 0.3,
          backgroundColor: WUERTH_ROT,
        }}
      />

      {stations.map((st, i) => {
        const stF = F(st.startSec);
        if (frame < stF) return null;
        const pop = spring({ frame: frame - stF, fps, config: { damping: 14, mass: 0.5, stiffness: 300 } });
        const isLast = i === n - 1;
        const above = i % 2 === 0;
        const r = (isLast ? 13 : 9) * (height / 1920);
        // Kundenfeedback 21.07. („Kommisionierer abgeschnitten"): Labels
        // dürfen nie halb angeschnitten am Bildrand stehen — sie blenden
        // weich aus, sobald die Kamera sie aus dem Bild schiebt.
        const nodeX = (pct(i) / 100) * contW;
        const originPx = focusX * contW;
        const screenX = width * 0.13 + originPx + (nodeX - originPx) * ZOOM + camTx;
        const labelHalfW = ((height * 0.115) / 2) * ZOOM;
        // Opacity 0, sobald die Label-Box den Bildrand berührt (nie halbe Wörter)
        const edgeFade = interpolate(
          screenX,
          [labelHalfW + 10, labelHalfW + 10 + width * 0.085, width - labelHalfW - 10 - width * 0.085, width - labelHalfW - 10],
          [0, 1, 1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );
        return (
          <div
            key={`node-${i}`}
            style={{
              position: "absolute",
              left: `${pct(i)}%`,
              top: lineH / 2,
              transform: "translateX(-50%)",
            }}
          >
            {/* Node im Map-Pin-Look */}
            <div
              style={{
                position: "absolute",
                left: -r,
                top: -r,
                width: r * 2,
                height: r * 2,
                borderRadius: "50%",
                backgroundColor: WUERTH_ROT,
                transform: `scale(${pop})`,
                boxShadow: "0 3px 14px rgba(0,0,0,0.45)",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  inset: "30%",
                  borderRadius: "50%",
                  backgroundColor: WUERTH_WEISS,
                }}
              />
            </div>
            {/* Label (alternierend oben/unten) */}
            <div
              style={{
                position: "absolute",
                left: "50%",
                transform: `translateX(-50%) scale(${interpolate(pop, [0, 1], [1.15, 1])})`,
                ...(above
                  ? { bottom: r + height * 0.008 }
                  : { top: r + height * 0.008 }),
                width: height * 0.115,
                textAlign: "center",
                fontFamily: FONT_BOLD,
                fontWeight: "normal" as const,
                fontSize: height * 0.0125,
                lineHeight: 1.18,
                letterSpacing: "0.04em",
                color: WUERTH_WEISS,
                textTransform: "uppercase",
                textShadow: "0 2px 12px rgba(0,0,0,0.6)",
                opacity: Math.min(pop * 1.3, 1) * edgeFade,
              }}
            >
              <span
                style={
                  isLast
                    ? {
                        backgroundColor: WUERTH_ROT,
                        padding: `${height * 0.002}px ${height * 0.005}px`,
                        boxDecorationBreak: "clone" as const,
                        WebkitBoxDecorationBreak: "clone" as const,
                      }
                    : undefined
                }
              >
                {st.label}
              </span>
            </div>
            {/* Sub-Label auf der Gegenseite */}
            {st.sub && (
              <div
                style={{
                  position: "absolute",
                  left: "50%",
                  transform: "translateX(-50%)",
                  ...(above
                    ? { top: r + height * 0.008 }
                    : { bottom: r + height * 0.008 }),
                  fontFamily: FONT_BOLD,
                  fontSize: height * 0.0105,
                  letterSpacing: "0.1em",
                  color: "rgba(255,255,255,0.65)",
                  textTransform: "uppercase",
                  whiteSpace: "nowrap",
                  textShadow: "0 2px 12px rgba(0,0,0,0.6)",
                  opacity: Math.min(pop * 1.3, 1) * edgeFade,
                }}
              >
                {st.sub}
              </div>
            )}
          </div>
        );
      })}
      </div>
    </div>
  );
};

// --- Overlay-Komposition (V4 + V5 via defaultProps) ---

export const WlcTalkOverlay: React.FC<WlcTalkOverlayProps> = ({
  review,
  hookTop,
  hookLines,
  splash,
  captions,
  stations,
  tickerEndSec,
}) => {
  const fontsLoaded = useWlcFonts();
  const { fps, width, height } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);

  const longestHook = hookLines.reduce(
    (acc, l) => (l.text.length > acc.length ? l.text : acc),
    ""
  );
  const hookSize = longestHook
    ? Math.min(
        fitText({
          text: longestHook,
          withinWidth: width * 0.88,
          fontFamily: FONT_XBDCN,
          fontWeight: "normal",
        }).fontSize,
        height * 0.032
      )
    : 0;

  if (!fontsLoaded) return null;

  return (
    <AbsoluteFill>
      {/* Hook-Zeilen */}
      <div
        style={{
          position: "absolute",
          top: `${hookTop * 100}%`,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: hookSize * 0.45,
        }}
      >
        {hookLines.map((line, i) => (
          <PunchLine
            key={`hook-${i}`}
            text={line.text}
            highlight={line.highlight}
            inF={F(line.startSec)}
            outF={F(line.endSec)}
            fontSize={hookSize}
          />
        ))}
      </div>

      {/* Personen-Splash */}
      {splash && (
        <div
          style={{
            position: "absolute",
            top: "60%",
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: height * 0.007,
          }}
        >
          <SkewBar
            text={splash.name}
            bg={WUERTH_ROT}
            inF={F(splash.startSec)}
            outF={F(splash.endSec)}
            fontSize={height * 0.031}
          />
          <SkewBar
            text={splash.role}
            bg="rgba(38,38,38,0.94)"
            inF={F(splash.startSec) + 3}
            outF={F(splash.endSec)}
            fontSize={height * 0.015}
            fontFamily={FONT_BOLD}
          />
        </div>
      )}

      {/* Zeitstrahl (V4) */}
      <Timeline stations={stations} endSec={tickerEndSec} top={0.745} />

      {/* Captions */}
      <div
        style={{
          position: "absolute",
          top: "63%",
          width: "100%",
          display: "flex",
          justifyContent: "center",
        }}
      >
        {captions.map((cap, i) =>
          cap.style === "keyword" ? (
            <KeywordCard
              key={`cap-${i}`}
              text={cap.text}
              sub={cap.sub}
              inF={F(cap.startSec)}
              outF={F(cap.endSec)}
            />
          ) : (
            <SkewBar
              key={`cap-${i}`}
              text={cap.text}
              bg="rgba(38,38,38,0.92)"
              inF={F(cap.startSec)}
              outF={F(cap.endSec)}
              fontSize={height * 0.019}
              redEdge
            />
          )
        )}
      </div>

      {review?.showGuides && (
        <ReviewOverlay
          showSafeZone={review.showSafeZone ?? true}
          showFaceZone={review.showFaceZone ?? true}
          showGrid={review.showGrid ?? false}
          faceZone={review.faceZone}
          guideOpacity={review.guideOpacity ?? 0.35}
        />
      )}
    </AbsoluteFill>
  );
};

// ============================================================
// Job-Endcard (alle Videos) — Redesign nach Kundenfeedback 21.07.:
// „Zu viel mit Wappen und Logo" → zwei Varianten (brandStyle):
//   "wappen"  = nur das Team-Wappen, groß (kein Logo)
//   "logobox" = farbiges Logo im weißen Kasten (kein Wappen)
// Stellen UNTEREINANDER, jede Zeile mit (M/W/D). Steht NACH dem
// Video (kein Overlay).
// ============================================================

export const wlcJobEndcardSchema = projectPropsSchema.extend({
  brandStyle: z.enum(["wappen", "logobox"]).describe("Marken-Variante"),
  jobs: z.array(z.string()).describe("Stellen (untereinander, je mit m/w/d)"),
  standortLine: z.string().describe("Standort-Zeile"),
  ctaText: z.string().describe("CTA-Balken-Text"),
});

export type WlcJobEndcardProps = z.infer<typeof wlcJobEndcardSchema>;

export const wlcJobEndcardDefaults: WlcJobEndcardProps = {
  format: "portrait" as const,
  fps: 25 as const,
  durationInSeconds: 4,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  brandStyle: "wappen",
  jobs: [
    "FACHKRAFT LAGERLOGISTIK (M/W/D)",
    "LAGERMITARBEITER (M/W/D)",
    "AUSBILDUNG LAGERLOGISTIK (M/W/D)",
  ],
  standortLine: "",
  ctaText: "BEWIRB DICH JETZT.",
};

export const WlcJobEndcard: React.FC<WlcJobEndcardProps> = ({
  review,
  brandStyle,
  jobs,
  standortLine,
  ctaText,
}) => {
  const fontsLoaded = useWlcFonts();
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);

  const punchIn = (startFrame: number) => {
    const p = spring({ frame: Math.max(frame - startFrame, 0), fps, config: PUNCH });
    return {
      opacity: frame < startFrame ? 0 : 1,
      transform: `scale(${interpolate(p, [0, 1], [1.08, 1])})`,
    };
  };
  const ctaStart = F(1.0);
  const ctaWipe = interpolate(frame, [ctaStart, ctaStart + F(0.45)], [0, 1], {
    easing: Easing.bezier(0.6, 0, 0.4, 1),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const ctaFontSize = Math.min(
    fitText({
      text: ctaText,
      withinWidth: width * 0.62,
      fontFamily: FONT_XBDCN,
      fontWeight: "normal",
    }).fontSize,
    height * 0.042
  );
  // Stellen-Zeilen: einheitliche Größe = kleinste Fit-Größe aller Zeilen
  const jobSize = Math.min(
    height * 0.024,
    ...jobs.map(
      (j) =>
        fitText({ text: j, withinWidth: width * 0.86, fontFamily: FONT_XBDCN, fontWeight: "normal" }).fontSize
    )
  );
  const jobsTop = brandStyle === "wappen" ? 0.435 : 0.38;
  const ctaTop = jobsTop + jobs.length * 0.034 + (standortLine ? 0.03 : 0) + 0.045;

  if (!fontsLoaded) return null;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {/* CI-Hintergrund: Schwarz mit tiefem Würth-Rot-Verlauf + Vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(115% 85% at 50% 32%, #3A0000 0%, #160000 45%, #000000 78%)",
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(70% 45% at 50% 34%, ${WUERTH_ROT} 0%, transparent 70%)`,
          opacity: 0.14,
          filter: "blur(40px)",
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(130% 100% at 50% 50%, transparent 60%, rgba(0,0,0,0.6) 100%)",
        }}
      />

      {brandStyle === "wappen" ? (
        // Variante A: nur das Team-Wappen, groß
        <div
          style={{
            position: "absolute",
            top: "15.5%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
            ...punchIn(F(0.1)),
          }}
        >
          <Img src={staticFile("clients/wlc/wappen.png")} style={{ width: "30%" }} />
        </div>
      ) : (
        // Variante B: farbiges Logo im weißen Kasten
        <div
          style={{
            position: "absolute",
            top: "24%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
            ...punchIn(F(0.1)),
          }}
        >
          <div
            style={{
              backgroundColor: WUERTH_WEISS,
              padding: `${height * 0.022}px ${width * 0.05}px`,
              boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
            }}
          >
            <Img src={staticFile("clients/wlc/logo-pos.jpg")} style={{ width: width * 0.62 }} />
          </div>
        </div>
      )}

      {/* Stellen untereinander, je mit (M/W/D) */}
      <div
        style={{
          position: "absolute",
          top: `${jobsTop * 100}%`,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: height * 0.013,
        }}
      >
        {jobs.map((job, i) => (
          <div
            key={`job-${i}`}
            style={{
              fontFamily: FONT_XBDCN,
              fontWeight: "normal" as const,
              fontSize: jobSize,
              lineHeight: 1.1,
              letterSpacing: "0.02em",
              color: WUERTH_WEISS,
              textTransform: "uppercase",
              whiteSpace: "nowrap",
              borderLeft: `${Math.max(4, width * 0.006)}px solid ${WUERTH_ROT}`,
              paddingLeft: height * 0.012,
              ...punchIn(F(0.5) + i * F(0.14)),
            }}
          >
            {job}
          </div>
        ))}
        {standortLine && (
          <div
            style={{
              fontFamily: FONT_BOLD,
              fontSize: height * 0.015,
              letterSpacing: "0.12em",
              color: "rgba(255,255,255,0.75)",
              textTransform: "uppercase",
              marginTop: height * 0.004,
              ...punchIn(F(0.5) + jobs.length * F(0.14)),
            }}
          >
            {standortLine}
          </div>
        )}
      </div>

      <div
        style={{
          position: "absolute",
          top: `${ctaTop * 100}%`,
          width: "100%",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            position: "relative",
            overflow: "hidden",
            padding: `${height * 0.015}px ${width * 0.075}px`,
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundColor: WUERTH_ROT,
              transform: `scaleX(${ctaWipe})`,
              transformOrigin: "left",
            }}
          />
          <div
            style={{
              position: "relative",
              fontFamily: FONT_XBDCN,
              fontWeight: "normal" as const,
              fontSize: ctaFontSize,
              color: WUERTH_WEISS,
              textTransform: "uppercase",
              opacity: ctaWipe > 0.55 ? 1 : 0,
              whiteSpace: "nowrap",
            }}
          >
            {ctaText}
          </div>
        </div>
      </div>

      {review?.showGuides && (
        <ReviewOverlay
          showSafeZone={review.showSafeZone ?? true}
          showFaceZone={review.showFaceZone ?? false}
          showGrid={review.showGrid ?? false}
          faceZone={review.faceZone}
          guideOpacity={review.guideOpacity ?? 0.35}
        />
      )}
    </AbsoluteFill>
  );
};
