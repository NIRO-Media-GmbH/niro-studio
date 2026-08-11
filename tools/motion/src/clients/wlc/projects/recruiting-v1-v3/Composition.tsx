// ============================================================
// WLC — Video 1 (Azubi POV), Video 2 (Erster Tag), Video 3
// (Reporter-Walk-Around) — Overlays für die FERTIGEN Schnitte.
// Timing aus Material/Transkript Fertige Videos/*.srt (Wort-Level).
//
// V1/V2 (WlcAzubiOverlay): sequenzielle Hook-Captions (Klischee-
//   Strecke aus dem Plan), Splashes, Keyword-Cards — inkl.
//   „GEKNECHTET"-Durchstreicher (V1) und „KEINE NUMMER." (V2).
// V3 (WlcReporterOverlay): Video ohne B-Roll → Eye Candy:
//   FULLSCREEN-Stations-Cards (x/4, roter Sweep), Benefits-Board
//   (Vollbild, Checks poppen auf Janas Wörter — „ZEUGNISPRÄMIE",
//   NIE „Notenprämie"!), Tätigkeiten-Chip-Stacks, Payoff-Klammer.
// Face-Zone (8–45 %) bleibt frei — alle Overlays ≥ 58 %;
// Fullscreen-Cards decken bewusst das ganze Bild (Interstitials).
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
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
  GRAU_85,
  RedSweep,
  WUERTH_ROT,
  WUERTH_WEISS,
  useWlcFonts,
} from "../../components";

const PUNCH = { damping: 60, mass: 0.4, stiffness: 400, overshootClamping: true };

// ============================================================
// Schemas
// ============================================================

const hookLineSchema = z.object({
  text: z.string().describe("Caption-Zeile"),
  highlight: z.string().optional().describe("Schlüsselwort (roter Sweep)"),
  startSec: z.number().step(0.01),
  endSec: z.number().step(0.01),
});

const splashSchema = z.object({
  name: z.string().describe("Name (rote Bar)"),
  role: z.string().describe("Rolle (graue Bar)"),
  startSec: z.number().step(0.01),
  endSec: z.number().step(0.01),
});

const captionSchema = z.object({
  style: z.enum(["keyword", "bar"]).describe("Stil"),
  text: z.string().describe("Haupttext"),
  sub: z.string().optional().describe("Subline (nur keyword)"),
  strikeAtSec: z.number().optional().describe("Durchstreichen bei (Sek)"),
  startSec: z.number().step(0.01),
  endSec: z.number().step(0.01),
});

export const wlcAzubiOverlaySchema = projectPropsSchema.extend({
  hookTop: z.number().min(0.1).max(0.85).step(0.01).describe("Caption-Y (Anteil Höhe)"),
  hookLines: z.array(hookLineSchema).describe("Caption-Sequenz"),
  splashes: z.array(splashSchema).describe("Personen-Splashes"),
  captions: z.array(captionSchema).describe("Captions"),
});

export type WlcAzubiOverlayProps = z.infer<typeof wlcAzubiOverlaySchema>;

const stationCardSchema = z.object({
  index: z.number().min(1).describe("Stations-Nr."),
  total: z.number().min(1).describe("Anzahl Stationen"),
  name: z.string().describe("Stationsname"),
  startSec: z.number().step(0.01),
  endSec: z.number().step(0.01),
});

const benefitItemSchema = z.object({
  label: z.string(),
  startSec: z.number().step(0.01).describe("Check poppt bei (Sek)"),
});

const chipSchema = z.object({
  label: z.string(),
  startSec: z.number().step(0.01),
});

const chipGroupSchema = z.object({
  chips: z.array(chipSchema),
  endSec: z.number().step(0.01).describe("Gruppe ausblenden bei (Sek)"),
});

export const wlcReporterOverlaySchema = wlcAzubiOverlaySchema.extend({
  stationCards: z.array(stationCardSchema).describe("FULLSCREEN-Stations-Cards"),
  benefitTitle: z.string().describe("Titel Benefits-Board"),
  benefitItems: z.array(benefitItemSchema).describe("Benefits (Checks)"),
  benefitStartSec: z.number().step(0.01),
  benefitEndSec: z.number().step(0.01),
  chipGroups: z.array(chipGroupSchema).describe("Tätigkeiten-Chips"),
});

export type WlcReporterOverlayProps = z.infer<typeof wlcReporterOverlaySchema>;

// ============================================================
// Defaults — V1 „POV: Was machst du nach der Schule?" (~61 s)
// ============================================================

export const wlcV1OverlayDefaults: WlcAzubiOverlayProps = {
  format: "portrait" as const,
  fps: 25 as const,
  durationInSeconds: 61,
  transparent: true,
  review: { showGuides: false, showSafeZone: true, showFaceZone: true, showGrid: false, guideOpacity: 0.35 },
  hookTop: 0.62,
  hookLines: [
    { text: "AUSBILDUNG IM LAGER?\nEHER SO.", startSec: 0.2, endSec: 2.2 },
    { text: "POV: LETZTES SCHULJAHR.\nALLE FRAGEN, WAS DU MACHST.", startSec: 2.3, endSec: 4.6 },
    { text: "MACHST DU ABI?", startSec: 4.7, endSec: 5.4 },
    { text: "LAGER? ECHT?", startSec: 5.4, endSec: 6.1 },
    { text: "KLINGT LANGWEILIG?", highlight: "LANGWEILIG?", startSec: 6.2, endSec: 7.1 },
    { text: "SPOILER:", highlight: "SPOILER:", startSec: 7.3, endSec: 8.3 },
    // CTA-Einblendung (Kundenwunsch 21.07., Kommentar 4 bei 0:45)
    { text: "DU WILLST DIE ZUKUNFT IN DER\nLOGISTIK MITGESTALTEN?", highlight: "ZUKUNFT", startSec: 45.2, endSec: 47.9 },
    { text: "DANN STARTE DEINE\nKARRIERE BEI WLC.", highlight: "KARRIERE", startSec: 48.0, endSec: 50.9 },
  ],
  splashes: [
    // Kundenkorrektur 21.07.: Name ist SAMED (nicht Hamid), Rollen-Wortlaut Cornelia
    { name: "SAMED.", role: "AUSZUBILDENDER IM 2. LEHRJAHR | FACHKRAFT FÜR LAGERLOGISTIK", startSec: 8.5, endSec: 12.5 },
    { name: "TORBEN.", role: "AUSZUBILDENDER IM 2. LEHRJAHR | FACHKRAFT FÜR LAGERLOGISTIK", startSec: 54.4, endSec: 58.4 },
  ],
  captions: [
    { style: "keyword", text: "NIEMALS LANGWEILIG.", startSec: 15.8, endSec: 18.5 },
    { style: "keyword", text: "STAPLERFÜHRERSCHEIN.", sub: "BEREITS IN DER AUSBILDUNG", startSec: 29.7, endSec: 33.0 },
    // O-Ton sagt „geknechtet" — Card-Wording „AUSGENUTZT" ist Kundenwunsch (Kommentar 8)
    { style: "keyword", text: "AUSGENUTZT.", sub: "NICHT BEI WLC.", strikeAtSec: 42.6, startSec: 40.2, endSec: 44.5 },
    { style: "keyword", text: "LAGER.", sub: "ABER BEI WLC.", startSec: 51.3, endSec: 54.0 },
  ],
};

// ============================================================
// Defaults — V2 „Mein erster Tag bei WLC" (~55 s)
// ============================================================

export const wlcV2OverlayDefaults: WlcAzubiOverlayProps = {
  format: "portrait" as const,
  fps: 25 as const,
  durationInSeconds: 55,
  transparent: true,
  review: { showGuides: false, showSafeZone: true, showFaceZone: true, showGrid: false, guideOpacity: 0.35 },
  hookTop: 0.62,
  hookLines: [
    { text: "AZUBIS KEHREN\nDOCH NUR …", highlight: "KEHREN", startSec: 0.3, endSec: 2.6 },
    { text: "WER HAT DIR\nDAS GESAGT?", startSec: 2.7, endSec: 5.0 },
    { text: "MEIN ERSTER TAG\nBEI WLC.", highlight: "ERSTER TAG", startSec: 6.0, endSec: 10.5 },
  ],
  splashes: [
    // Kundenkorrektur 21.07.: Name ist SAMED (nicht Hamid), Rollen-Wortlaut Cornelia
    { name: "SAMED.", role: "AUSZUBILDENDER IM 2. LEHRJAHR | FACHKRAFT FÜR LAGERLOGISTIK", startSec: 11.6, endSec: 15.6 },
    { name: "SEBASTIAN.", role: "TEAMLEITER HALBAUTOMATEN", startSec: 31.2, endSec: 35.0 },
    { name: "TORBEN.", role: "AUSZUBILDENDER IM 2. LEHRJAHR | FACHKRAFT FÜR LAGERLOGISTIK", startSec: 40.2, endSec: 43.4 },
  ],
  captions: [
    { style: "bar", text: "TAG 1: WILLKOMMENSVERANSTALTUNG.", startSec: 16.5, endSec: 21.0 },
    // Kundenwunsch (Kommentar 4): O-Ton „an die Hand genommen" bleibt, Slogan-Card drüber
    { style: "keyword", text: "MAN WIRD IMMER UNTERSTÜTZT.", startSec: 25.8, endSec: 29.6 },
    { style: "keyword", text: "KEINE NUMMER.", startSec: 44.8, endSec: 49.0 },
  ],
};

// ============================================================
// Defaults — V3 Reporter-Walk-Around (~118 s)
// ============================================================

export const wlcV3OverlayDefaults: WlcReporterOverlayProps = {
  format: "portrait" as const,
  fps: 25 as const,
  durationInSeconds: 118,
  transparent: true,
  review: { showGuides: false, showSafeZone: true, showFaceZone: true, showGrid: false, guideOpacity: 0.35 },
  hookTop: 0.62,
  hookLines: [
    { text: "KAUFMANN BEI WLC?\nNUR EXCEL?", highlight: "NUR EXCEL?", startSec: 0.3, endSec: 2.5 },
    // Payoff-Klammer (PFLICHT lt. Plan)
    { text: "WAS KAUFMANN BEI WLC\nWIRKLICH HEISST.", highlight: "WIRKLICH", startSec: 108.6, endSec: 113.0 },
  ],
  splashes: [
    // Wortlaut Cornelia 21.07. (Kommentar 3)
    { name: "JANA.", role: "2. LEHRJAHR | AUSZUBILDENDE FÜR KAUFFRAU IM GROSS- & AUSSENHANDELSMANAGEMENT", startSec: 19.2, endSec: 23.6 },
  ],
  captions: [
    { style: "bar", text: "ADELSHEIM.", startSec: 2.6, endSec: 5.0 },
  ],
  stationCards: [
    // +0,5 s Standzeit (Lesezeit, David 2026-07-15)
    { index: 1, total: 4, name: "MATERIALWIRTSCHAFT", startSec: 12.7, endSec: 14.7 },
    { index: 2, total: 4, name: "CONTROLLING", startSec: 32.2, endSec: 34.4 },
    { index: 3, total: 4, name: "MARKETING & SALES", startSec: 62.0, endSec: 64.2 },
    { index: 4, total: 4, name: "EMPFANG", startSec: 86.4, endSec: 88.6 },
  ],
  benefitTitle: "AZUBI-BENEFITS.",
  benefitItems: [
    { label: "30 TAGE URLAUB", startSec: 52.8 },
    { label: "ZEUGNISPRÄMIE", startSec: 54.6 },
    { label: "URLAUBS- & WEIHNACHTSGELD", startSec: 56.7 },
    // Kundenwunsch 21.07.: Wording wie bei Sina (V7)
    { label: "AZUBI-EVENTS", startSec: 59.1 },
  ],
  benefitStartSec: 51.6,
  benefitEndSec: 62.1,
  chipGroups: [
    {
      chips: [
        { label: "BONITÄTSPRÜFUNGEN", startSec: 36.8 },
        { label: "RECHNUNGSPRÜFUNG", startSec: 38.4 },
        { label: "JAHRESABSCHLUSS", startSec: 41.0 },
      ],
      endSec: 46.5,
    },
    {
      chips: [
        { label: "SOCIAL MEDIA", startSec: 67.9 },
        { label: "PRESSETEXTE", startSec: 69.6 },
        // Kundenwunsch 21.07. (Kommentar 6 bei 1:13)
        { label: "KREATIVES ARBEITEN", startSec: 71.6 },
      ],
      endSec: 76.0,
    },
    {
      chips: [
        { label: "ANGEBOTE", startSec: 78.0 },
        { label: "KUNDENBESUCHE", startSec: 81.5 },
      ],
      endSec: 85.5,
    },
    {
      chips: [
        { label: "KUNDENANMELDUNG", startSec: 96.4 },
        { label: "BESUCHERMANAGEMENT", startSec: 98.2 },
        { label: "BESPRECHUNGSZIMMER", startSec: 100.5 },
        { label: "FUHRPARKMANAGEMENT", startSec: 104.7 },
      ],
      endSec: 107.5,
    },
  ],
};

// ============================================================
// Bausteine
// ============================================================

const useInOut = (inF: number, outF: number) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fadeF = Math.round(fps * 0.16);
  if (frame < inF || frame > outF) return { visible: false, opacity: 0 };
  const opacity =
    interpolate(frame, [inF, inF + 2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) *
    interpolate(frame, [outF - fadeF, outF], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
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
  return {
    scale,
    shakeX: Math.sin(local * 2.1) * shakeAmt,
    shakeY: Math.cos(local * 1.7) * shakeAmt * 0.5,
  };
};

const PunchLine: React.FC<{
  text: string;
  highlight?: string;
  inF: number;
  outF: number;
}> = ({ text, highlight, inF, outF }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const { visible, opacity } = useInOut(inF, outF);
  const { scale, shakeX, shakeY } = usePunchShake(inF);
  const hlStart = inF + Math.round(fps * 0.3);
  const hlWipe = interpolate(frame, [hlStart, hlStart + Math.round(fps * 0.25)], [0, 1], {
    easing: Easing.bezier(0.6, 0, 0.4, 1),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  if (!visible) return null;

  // Headline-Block: \n-Umbrüche, Größe passt sich DIESER Caption an
  // (kurze Zeilen groß statt Untertitel-Einheitsgröße)
  const segs = text.split("\n");
  const longestSeg = segs.reduce((acc, s) => (s.length > acc.length ? s : acc), "");
  const fontSize = Math.min(
    fitText({ text: longestSeg, withinWidth: width * 0.9, fontFamily: FONT_XBDCN, fontWeight: "normal" }).fontSize,
    height * 0.05
  );

  const renderSeg = (seg: string, key: number) => {
    const idx = highlight ? seg.indexOf(highlight) : -1;
    const before = idx >= 0 ? seg.slice(0, idx) : seg;
    const hl = idx >= 0 ? highlight! : "";
    const after = idx >= 0 ? seg.slice(idx + hl.length) : "";
    return (
      <div key={`seg-${key}`} style={{ whiteSpace: "nowrap" }}>
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

  return (
    <div
      style={{
        fontFamily: FONT_XBDCN,
        fontWeight: "normal" as const,
        fontSize,
        color: WUERTH_WEISS,
        textAlign: "center",
        lineHeight: 1.12,
        opacity,
        transform: `translate(${shakeX}px, ${shakeY}px) scale(${scale})`,
        textShadow: "0 0 40px rgba(0,0,0,0.55), 0 4px 20px rgba(0,0,0,0.45)",
      }}
    >
      {segs.map(renderSeg)}
    </div>
  );
};

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
    <div style={{ position: "relative", display: "inline-block", transform: `translate(${shakeX}px, ${shakeY}px) scale(${scale})` }}>
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

const KeywordCard: React.FC<{
  text: string;
  sub?: string;
  strikeAtF?: number;
  inF: number;
  outF: number;
}> = ({ text, sub, strikeAtF, inF, outF }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const { visible, opacity } = useInOut(inF, outF);
  const { scale, shakeX, shakeY } = usePunchShake(inF);
  // Subline: bei Strike-Cards erst MIT dem Strike, sonst kurz nach dem Wort
  const subStart = strikeAtF ?? inF + Math.round(fps * 0.25);
  const subOp = interpolate(frame, [subStart, subStart + Math.round(fps * 0.2)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const strike = strikeAtF
    ? interpolate(frame, [strikeAtF, strikeAtF + Math.round(fps * 0.22)], [0, 1], {
        easing: Easing.bezier(0.6, 0, 0.4, 1),
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 0;
  if (!visible) return null;
  const mainSize = Math.min(
    fitText({ text, withinWidth: width * 0.8, fontFamily: FONT_XBDCN, fontWeight: "normal" }).fontSize,
    height * 0.048
  );
  const endsWithDot = text.trim().endsWith(".");
  const body = endsWithDot ? text.trim().slice(0, -1) : text.trim();
  return (
    <div style={{ textAlign: "center", opacity }}>
      <div
        style={{
          position: "relative",
          display: "inline-block",
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
        <span style={{ position: "relative", display: "inline-block" }}>
          {body}
          {strikeAtF !== undefined && (
            <div
              style={{
                position: "absolute",
                left: "-3%",
                width: "106%",
                top: "50%",
                height: Math.max(5, height * 0.005),
                transform: "translateY(-50%) rotate(-3deg)",
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  backgroundColor: WUERTH_ROT,
                  transform: `scaleX(${strike})`,
                  transformOrigin: "left",
                  boxShadow: "0 2px 10px rgba(0,0,0,0.5)",
                }}
              />
            </div>
          )}
        </span>
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
            textShadow: "0 2px 14px rgba(0,0,0,0.5)",
          }}
        >
          {sub}
        </div>
      )}
    </div>
  );
};

// --- V3: FULLSCREEN-Stations-Card ---

const StationCard: React.FC<{
  index: number;
  total: number;
  name: string;
  inF: number;
  outF: number;
}> = ({ index, total, name, inF, outF }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const punch = usePunchShake(inF + Math.round(fps * 0.2));
  if (frame < inF || frame > outF) return null;
  const ease = Easing.bezier(0.6, 0, 0.4, 1);
  const local = frame - inF;

  // Card wischt von rechts rein und nach links raus
  const slide = interpolate(
    frame,
    [inF, inF + Math.round(fps * 0.22), outF - Math.round(fps * 0.22), outF],
    [1, 0, 0, -1],
    { easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const nameSize = Math.min(
    fitText({ text: name, withinWidth: width * 0.84, fontFamily: FONT_XBDCN, fontWeight: "normal" }).fontSize,
    height * 0.06
  );

  // Doppel-Bande: Grau-Blade zuerst, Rot folgt (weiße Kante)
  const blade = interpolate(frame, [inF + Math.round(fps * 0.08), inF + Math.round(fps * 0.3)], [0, 1], {
    easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const bandWipe = interpolate(frame, [inF + Math.round(fps * 0.14), inF + Math.round(fps * 0.36)], [0, 1], {
    easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const metaOp = interpolate(frame, [inF + Math.round(fps * 0.22), inF + Math.round(fps * 0.36)], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Ghost-Nummer: treibt langsam größer (Ken-Burns)
  const ghostDrift = 1 + (local / fps) * 0.045;
  const ghostOp = interpolate(frame, [inF + 2, inF + Math.round(fps * 0.2)], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ transform: `translateX(${slide * 100}%)` }}>
      {/* Tiefe: Schwarz + dunkelroter Radial + Vignette */}
      <AbsoluteFill style={{ backgroundColor: "#000000" }} />
      <AbsoluteFill
        style={{
          background: "radial-gradient(110% 80% at 50% 42%, #2E0000 0%, #0E0000 50%, #000000 80%)",
        }}
      />

      {/* Ghost-Nummer hinter allem */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          width: "100%",
          textAlign: "center",
          transform: `translateY(-54%) scale(${ghostDrift})`,
          fontFamily: FONT_XBDCN,
          fontWeight: "normal" as const,
          fontSize: height * 0.42,
          lineHeight: 1,
          color: "#1C1C1C",
          opacity: ghostOp,
        }}
      >
        {String(index).padStart(2, "0")}
      </div>

      {/* Doppel-Bande */}
      <div
        style={{
          position: "absolute",
          top: "45.5%",
          height: "11%",
          left: "-6%",
          right: "-6%",
          backgroundColor: GRAU_85,
          transform: `skewY(-3deg) translateY(${height * 0.014}px) scaleX(${blade})`,
          transformOrigin: "left",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: "44%",
          height: "12%",
          left: "-6%",
          right: "-6%",
          backgroundColor: WUERTH_ROT,
          borderBottom: `${Math.max(3, height * 0.0028)}px solid ${WUERTH_WEISS}`,
          transform: `skewY(-3deg) scaleX(${bandWipe})`,
          transformOrigin: "left",
          boxShadow: "0 14px 50px rgba(0,0,0,0.55)",
        }}
      />

      {/* Stations-Fortschritt: Punkte + Label */}
      <div
        style={{
          position: "absolute",
          top: "37.5%",
          width: "100%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: height * 0.008,
          opacity: metaOp,
        }}
      >
        {Array.from({ length: total }, (_, i) => {
          const active = i + 1 === index;
          const done = i + 1 < index;
          const r = active ? height * 0.007 : height * 0.005;
          return (
            <div
              key={`dot-${i}`}
              style={{
                width: r * 2,
                height: r * 2,
                borderRadius: "50%",
                backgroundColor: active || done ? WUERTH_ROT : "rgba(255,255,255,0.28)",
                outline: active ? `${Math.max(2, height * 0.0016)}px solid ${WUERTH_WEISS}` : undefined,
                outlineOffset: active ? height * 0.002 : undefined,
              }}
            />
          );
        })}
        <span
          style={{
            marginLeft: height * 0.012,
            fontFamily: FONT_BOLD,
            fontSize: height * 0.0135,
            letterSpacing: "0.22em",
            color: "rgba(255,255,255,0.8)",
          }}
        >
          {`STATION ${index}/${total}`}
        </span>
      </div>

      {/* Stationsname */}
      <div
        style={{
          position: "absolute",
          top: "46%",
          width: "100%",
          textAlign: "center",
          fontFamily: FONT_XBDCN,
          fontWeight: "normal" as const,
          fontSize: nameSize,
          color: WUERTH_WEISS,
          transform: `translate(${punch.shakeX}px, ${punch.shakeY}px) scale(${punch.scale})`,
          textShadow: "0 6px 30px rgba(0,0,0,0.5)",
          whiteSpace: "nowrap",
        }}
      >
        {name}
      </div>
    </AbsoluteFill>
  );
};

// --- Benefits-/Listen-Board (Vollbild) v2 „mehr Punch":
// Red-Sweep-Entry, Dunkelrot-Tiefe, mitzählende Ghost-Nummer,
// Items sliden mit Badge-Bounce, roter Fortschrittsbalken, Drift.

const BenefitBoard: React.FC<{
  title: string;
  items: { label: string; startSec: number }[];
  inF: number;
  outF: number;
  numbered?: boolean;
}> = ({ title, items, inF, outF, numbered }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  // „(M/W/D)" wird wie in den WLC-Stellenanzeigen kleiner hinter den
  // Titel gesetzt (Quelle: Material/Info zur Stellenanzeigen)
  const splitMwd = (label: string) => {
    const m = label.match(/^(.*?)\s*\(M\/W\/D\)$/i);
    return m ? { main: m[1], mwd: true } : { main: label, mwd: false };
  };
  // Lange Einträge (z. B. „KAUFMANN FÜR GROSS- & AUSSENHANDELSMANAGEMENT")
  // automatisch einpassen — EINE Größe für alle Items (einheitlicher Look)
  const itemSize = Math.min(
    height * 0.026,
    ...items.map((it) => {
      const parts = splitMwd(it.label);
      return fitText({
        text: parts.main,
        withinWidth: (width * 0.72 - height * 0.05) * (parts.mwd ? 0.87 : 1),
        fontFamily: FONT_XBDCN,
        fontWeight: "normal",
      }).fontSize;
    })
  );
  const titlePunch = usePunchShake(inF + Math.round(fps * 0.28));

  // Zuletzt erschienenes Item (für Ghost-Zähler + Fortschritt)
  let reached = 0;
  for (let i = 0; i < items.length; i++) {
    if (frame >= F(items[i].startSec)) reached = i + 1;
  }
  const lastStartF = reached > 0 ? F(items[reached - 1].startSec) : inF;
  const ghostPop = spring({ frame: Math.max(frame - lastStartF, 0), fps, config: PUNCH });
  const progress = spring({ frame: Math.max(frame - lastStartF, 0), fps, config: { damping: 20, mass: 0.6, stiffness: 120 } });
  const progFrac = items.length
    ? (Math.max(reached - 1, 0) + progress) / items.length
    : 0;

  if (frame < inF || frame > outF) return null;

  const local = frame - inF;
  const sweepF = Math.round(fps * 0.5);
  const bgOp =
    interpolate(frame, [inF, inF + 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) *
    interpolate(frame, [outF - Math.round(fps * 0.22), outF], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exitScale = interpolate(frame, [outF - Math.round(fps * 0.22), outF], [1, 0.97], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const drift = 1 + (local / fps) * 0.0035;

  return (
    <AbsoluteFill style={{ opacity: bgOp }}>
      <AbsoluteFill style={{ backgroundColor: "rgba(0,0,0,0.93)" }} />
      <AbsoluteFill
        style={{
          background: "radial-gradient(110% 75% at 50% 30%, #2E0000 0%, #0E0000 55%, transparent 80%)",
        }}
      />

      <AbsoluteFill style={{ transform: `scale(${drift * exitScale})` }}>
        {/* Ghost-Zähler rechts unten, zählt mit */}
        {reached > 0 && (
          <div
            style={{
              position: "absolute",
              right: "-2%",
              bottom: "16%",
              fontFamily: FONT_XBDCN,
              fontWeight: "normal" as const,
              fontSize: height * 0.3,
              lineHeight: 1,
              color: "#1E1E1E",
              transform: `scale(${interpolate(ghostPop, [0, 1], [1.06, 1])})`,
            }}
          >
            {String(reached).padStart(2, "0")}
          </div>
        )}

        {/* Titel */}
        <div
          style={{
            position: "absolute",
            top: "22%",
            width: "100%",
            textAlign: "center",
            fontFamily: FONT_XBDCN,
            fontWeight: "normal" as const,
            fontSize: height * 0.038,
            color: WUERTH_WEISS,
            transform: `translate(${titlePunch.shakeX}px, ${titlePunch.shakeY}px) scale(${titlePunch.scale})`,
            opacity: frame >= inF + Math.round(fps * 0.28) ? 1 : 0,
          }}
        >
          {title.replace(/\.$/, "")}
          <span style={{ color: WUERTH_WEISS }}>.</span>
        </div>

        {/* Items */}
        <div
          style={{
            position: "absolute",
            top: "30%",
            left: "14%",
            right: "14%",
            display: "flex",
            flexDirection: "column",
            gap: height * 0.026,
          }}
        >
          {items.map((item, i) => {
            const stF = F(item.startSec);
            if (frame < stF) return null;
            const pop = spring({ frame: frame - stF, fps, config: { damping: 14, mass: 0.5, stiffness: 300 } });
            const isLatest = i === reached - 1;
            const r = height * 0.0155;
            return (
              <div
                key={`ben-${i}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: height * 0.016,
                  transform: `translateX(${interpolate(pop, [0, 1], [-36, 0])}px)`,
                  opacity: Math.min(pop * 1.4, 1) * (isLatest ? 1 : 0.82),
                }}
              >
                <div
                  style={{
                    width: r * 2,
                    height: r * 2,
                    borderRadius: "50%",
                    backgroundColor: WUERTH_ROT,
                    transform: `scale(${interpolate(pop, [0, 0.6, 1], [0.3, 1.18, 1])})`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    boxShadow: `0 0 ${r * 1.2}px rgba(200,16,46,0.45)`,
                  }}
                >
                  <span style={{ color: WUERTH_WEISS, fontFamily: FONT_BOLD, fontSize: numbered ? r * 0.95 : r * 1.15, lineHeight: 1 }}>
                    {numbered ? String(i + 1).padStart(2, "0") : "✓"}
                  </span>
                </div>
                <div
                  style={{
                    fontFamily: FONT_XBDCN,
                    fontWeight: "normal" as const,
                    fontSize: itemSize,
                    color: WUERTH_WEISS,
                    whiteSpace: "nowrap",
                  }}
                >
                  {splitMwd(item.label).main}
                  {splitMwd(item.label).mwd && (
                    <span
                      style={{
                        fontSize: itemSize * 0.55,
                        opacity: 0.85,
                        marginLeft: itemSize * 0.28,
                        letterSpacing: "0.04em",
                      }}
                    >
                      (M/W/D)
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Fortschrittsbalken */}
        <div
          style={{
            position: "absolute",
            bottom: "12.5%",
            left: "14%",
            right: "14%",
            height: Math.max(4, height * 0.0035),
            backgroundColor: "rgba(255,255,255,0.14)",
          }}
        >
          <div
            style={{
              width: `${Math.min(progFrac, 1) * 100}%`,
              height: "100%",
              backgroundColor: WUERTH_ROT,
              boxShadow: "0 0 14px rgba(200,16,46,0.6)",
            }}
          />
        </div>
      </AbsoluteFill>

      {/* Red-Sweep-Entry über allem */}
      {frame < inF + sweepF && (
        <AbsoluteFill>
          <RedSweep durationInFrames={sweepF} />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

// --- Fullscreen-Flash-Card v2: Weißblitz + rote Schräg-Bande + Zoom ---

const FlashCard: React.FC<{
  text: string;
  inF: number;
  outF: number;
}> = ({ text, inF, outF }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const punch = usePunchShake(inF + 1);
  if (frame < inF || frame > outF) return null;
  const bgOp =
    interpolate(frame, [inF, inF + 2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) *
    interpolate(frame, [outF - 3, outF], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const flash = interpolate(frame, [inF, inF + 2, inF + 6], [0, 0.85, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const local = frame - inF;
  const zoom = 1 + (local / fps) * 0.02;
  const bandWipe = interpolate(frame, [inF + 2, inF + Math.round(fps * 0.24)], [0, 1], {
    easing: Easing.bezier(0.6, 0, 0.4, 1),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const size = Math.min(
    fitText({ text, withinWidth: width * 0.84, fontFamily: FONT_XBDCN, fontWeight: "normal" }).fontSize,
    height * 0.058
  );
  const endsWithDot = text.trim().endsWith(".");
  const body = endsWithDot ? text.trim().slice(0, -1) : text.trim();
  return (
    <AbsoluteFill style={{ opacity: bgOp }}>
      <AbsoluteFill style={{ backgroundColor: "#000000" }} />
      <AbsoluteFill
        style={{
          background: "radial-gradient(90% 60% at 50% 50%, #2E0000 0%, #000000 75%)",
          transform: `scale(${zoom})`,
        }}
      />
      {/* Rote Schräg-Bande hinter dem Satz */}
      <div
        style={{
          position: "absolute",
          top: "44.5%",
          height: "11%",
          left: "-6%",
          right: "-6%",
          backgroundColor: WUERTH_ROT,
          borderBottom: `${Math.max(3, height * 0.0028)}px solid ${WUERTH_WEISS}`,
          transform: `skewY(-3deg) scaleX(${bandWipe}) scale(${zoom})`,
          transformOrigin: "left",
          boxShadow: "0 14px 50px rgba(0,0,0,0.55)",
        }}
      />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", transform: `scale(${zoom})` }}>
        <div
          style={{
            fontFamily: FONT_XBDCN,
            fontWeight: "normal" as const,
            fontSize: size,
            color: WUERTH_WEISS,
            transform: `translate(${punch.shakeX}px, ${punch.shakeY}px) scale(${punch.scale})`,
            whiteSpace: "nowrap",
            textShadow: "0 6px 30px rgba(0,0,0,0.5)",
          }}
        >
          {body}
          {endsWithDot && <span style={{ color: WUERTH_WEISS }}>.</span>}
        </div>
      </AbsoluteFill>
      {/* Weißblitz beim Einschlag */}
      <AbsoluteFill style={{ backgroundColor: "#FFFFFF", opacity: flash }} />
    </AbsoluteFill>
  );
};

// --- Tätigkeiten-Chip-Stack (links unten, wortgenau, bündig) ---

const ChipStack: React.FC<{
  chips: { label: string; startSec: number }[];
  outF: number;
}> = ({ chips, outF }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  const firstF = F(chips[0]?.startSec ?? 0);
  if (frame < firstF || frame > outF) return null;
  const fadeOut = interpolate(frame, [outF - Math.round(fps * 0.2), outF], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        top: "63%",
        left: "6%",
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        gap: height * 0.009,
        opacity: fadeOut,
        borderLeft: `${Math.max(4, width * 0.006)}px solid ${WUERTH_ROT}`,
        paddingLeft: height * 0.014,
      }}
    >
      {chips.map((chip, i) => {
        const stF = F(chip.startSec);
        if (frame < stF) return null;
        const pop = spring({ frame: frame - stF, fps, config: PUNCH });
        return (
          <div
            key={`chip-${i}`}
            style={{
              backgroundColor: "rgba(38,38,38,0.94)",
              padding: `${height * 0.006}px ${height * 0.016}px`,
              fontFamily: FONT_BOLD,
              fontWeight: "normal" as const,
              fontSize: height * 0.019,
              lineHeight: 1.1,
              color: WUERTH_WEISS,
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              whiteSpace: "nowrap",
              transform: `scale(${interpolate(pop, [0, 1], [1.12, 1])})`,
              transformOrigin: "left center",
              boxShadow: "0 4px 16px rgba(0,0,0,0.35)",
            }}
          >
            {chip.label}
          </div>
        );
      })}
    </div>
  );
};

// ============================================================
// Gemeinsamer Overlay-Kern (Hooks, Splashes, Captions)
// ============================================================

const OverlayCore: React.FC<{
  props: WlcAzubiOverlayProps;
}> = ({ props }) => {
  const { hookTop, hookLines, splashes, captions } = props;
  const { fps, width, height } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  // Rollen-Bar: lange Titel (z. B. Jana) automatisch einpassen
  const roleSize = (role: string) =>
    Math.min(
      height * 0.015,
      fitText({ text: role, withinWidth: width * 0.82, fontFamily: FONT_BOLD, fontWeight: "normal" }).fontSize
    );
  return (
    <>
      <div
        style={{
          position: "absolute",
          top: `${hookTop * 100}%`,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: height * 0.014,
        }}
      >
        {hookLines.map((line, i) => (
          <PunchLine
            key={`hook-${i}`}
            text={line.text}
            highlight={line.highlight}
            inF={F(line.startSec)}
            outF={F(line.endSec)}
          />
        ))}
      </div>

      {splashes.map((splash, i) => (
        <div
          key={`splash-${i}`}
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
          <SkewBar text={splash.name} bg={WUERTH_ROT} inF={F(splash.startSec)} outF={F(splash.endSec)} fontSize={height * 0.031} />
          <SkewBar
            text={splash.role}
            bg="rgba(38,38,38,0.94)"
            inF={F(splash.startSec) + 3}
            outF={F(splash.endSec)}
            fontSize={roleSize(splash.role)}
            fontFamily={FONT_BOLD}
          />
        </div>
      ))}

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
              strikeAtF={cap.strikeAtSec !== undefined ? F(cap.strikeAtSec) : undefined}
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
    </>
  );
};

// ============================================================
// Kompositionen
// ============================================================

export const WlcAzubiOverlay: React.FC<WlcAzubiOverlayProps> = (props) => {
  const fontsLoaded = useWlcFonts();
  if (!fontsLoaded) return null;
  return (
    <AbsoluteFill>
      <OverlayCore props={props} />
      {props.review?.showGuides && (
        <ReviewOverlay
          showSafeZone={props.review.showSafeZone ?? true}
          showFaceZone={props.review.showFaceZone ?? true}
          showGrid={props.review.showGrid ?? false}
          faceZone={props.review.faceZone}
          guideOpacity={props.review.guideOpacity ?? 0.35}
        />
      )}
    </AbsoluteFill>
  );
};

export const WlcReporterOverlay: React.FC<WlcReporterOverlayProps> = (props) => {
  const fontsLoaded = useWlcFonts();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  if (!fontsLoaded) return null;
  return (
    <AbsoluteFill>
      <OverlayCore props={props} />

      {/* Tätigkeiten-Chips */}
      {props.chipGroups.map((group, i) => (
        <ChipStack key={`group-${i}`} chips={group.chips} outF={F(group.endSec)} />
      ))}

      {/* Benefits-Board (Vollbild) */}
      <BenefitBoard
        title={props.benefitTitle}
        items={props.benefitItems}
        inF={F(props.benefitStartSec)}
        outF={F(props.benefitEndSec)}
      />

      {/* FULLSCREEN-Stations-Cards (zuoberst) */}
      {props.stationCards.map((card, i) => (
        <StationCard
          key={`station-${i}`}
          index={card.index}
          total={card.total}
          name={card.name}
          inF={F(card.startSec)}
          outF={F(card.endSec)}
        />
      ))}

      {props.review?.showGuides && (
        <ReviewOverlay
          showSafeZone={props.review.showSafeZone ?? true}
          showFaceZone={props.review.showFaceZone ?? true}
          showGrid={props.review.showGrid ?? false}
          faceZone={props.review.faceZone}
          guideOpacity={props.review.guideOpacity ?? 0.35}
        />
      )}
    </AbsoluteFill>
  );
};

// ============================================================
// Video 7 — Sina-only (Azubi Kupferzell), Final-Cut v2 (~83,3 s)
// 0 B-Roll → Animationen tragen das Video (David 2026-07-16):
// 3 Fullscreen-Momente (Berufe-Board nummeriert, Flash-Card
// „IMMER JEMAND DA.", Benefits-Board) + Hooks/Splash/Chips/Closer.
// Timing NEU aus Material/Transkript Fertige Videos/Nach Änderungen
// 2026-07-29/Video 7.srt: Anwendungsentwicklung-Passage geschnitten
// (Board bleibt 6 Berufe, jetzt alle wortgenau), ab ~21,5 s alles
// −1,3…−1,9 s. Closer-Card ersetzt durch Kunden-Slogan (Feedback
// 21.07., Kommentar 8); Berufe männliche Form, (M/W/D) im Titel.
// ============================================================

const boardSchema = z.object({
  title: z.string(),
  numbered: z.boolean().describe("Nummern statt Checks"),
  items: z.array(benefitItemSchema),
  startSec: z.number().step(0.01),
  endSec: z.number().step(0.01),
});

const flashSchema = z.object({
  text: z.string(),
  startSec: z.number().step(0.01),
  endSec: z.number().step(0.01),
});

export const wlcV7OverlaySchema = wlcAzubiOverlaySchema.extend({
  boards: z.array(boardSchema).describe("Fullscreen-Boards"),
  flashCards: z.array(flashSchema).describe("Fullscreen-Flash-Cards"),
  chipGroups: z.array(chipGroupSchema).describe("Chip-Stacks"),
});

export type WlcV7OverlayProps = z.infer<typeof wlcV7OverlaySchema>;

export const wlcV7OverlayDefaults: WlcV7OverlayProps = {
  format: "portrait" as const,
  fps: 25 as const,
  durationInSeconds: 83.3,
  transparent: true,
  review: { showGuides: false, showSafeZone: true, showFaceZone: true, showGrid: false, guideOpacity: 0.35 },
  hookTop: 0.62,
  hookLines: [
    { text: "WAS WÜRDEST DU MIT\n1.300 € IM MONAT MACHEN?", highlight: "1.300 €", startSec: 0.3, endSec: 5.4 },
    { text: "DAS VERDIENEN UNSERE AZUBIS —\nAB DEM 1. LEHRJAHR.", highlight: "1. LEHRJAHR.", startSec: 5.5, endSec: 8.2 },
    // Kunden-Slogan (Feedback 21.07., Kommentar 8) ersetzt „EIN GEILES
    // UNTERNEHMEN." — liegt wortnah auf „von Anfang an … integriert"
    { text: "UNSERE AZUBIS SIND VON ANFANG AN\nEIN VOLLWERTIGER TEIL DES TEAMS —", highlight: "VOLLWERTIGER TEIL", startSec: 73.8, endSec: 78.1 },
    { text: "MIT VERANTWORTUNG, VERTRAUEN UND\nECHTEN ENTWICKLUNGSMÖGLICHKEITEN.", highlight: "ENTWICKLUNGSMÖGLICHKEITEN.", startSec: 78.2, endSec: 81.2 },
  ],
  splashes: [
    { name: "SINA.", role: "AUSBILDUNGSLEITUNG · WLC", startSec: 21.5, endSec: 26.1 },
  ],
  captions: [
    { style: "keyword", text: "WILLKOMMEN IM TEAM.", startSec: 81.4, endSec: 83.2 },
  ],
  boards: [
    {
      // Titel-Wortlaute nach WLC-Stellenanzeigen (Material/Info zur
      // Stellenanzeigen, David 31.07.): volle Präpositionen („für"),
      // (m/w/d) je Beruf — im Board kleiner gesetzt wie in den Anzeigen
      title: "6 AUSBILDUNGSBERUFE.",
      numbered: true,
      items: [
        { label: "KAUFMANN FÜR GROSS- & AUSSENHANDELSMANAGEMENT (M/W/D)", startSec: 9.7 },
        { label: "KAUFMANN FÜR BÜROMANAGEMENT (M/W/D)", startSec: 12.5 },
        { label: "FACHKRAFT FÜR LAGERLOGISTIK (M/W/D)", startSec: 14.7 },
        { label: "MASCHINEN- & ANLAGENFÜHRER (M/W/D)", startSec: 16.5 },
        { label: "ELEKTRONIKER FÜR BETRIEBSTECHNIK (M/W/D)", startSec: 18.1 },
        { label: "FACHINFORMATIKER (M/W/D)", startSec: 20.1 },
      ],
      startSec: 8.5,
      endSec: 21.4,
    },
    {
      title: "AZUBI-BENEFITS.",
      numbered: false,
      items: [
        { label: "30 TAGE URLAUB", startSec: 52.4 },
        { label: "BILDUNGS- & PRÜFUNGSURLAUB", startSec: 55.9 },
        { label: "WEIHNACHTS- & URLAUBSGELD", startSec: 59.7 },
        { label: "AZUBI-EVENTS", startSec: 61.7 },
        { label: "AZUBI-PROJEKTE", startSec: 65.3 },
        { label: "ZEUGNISPRÄMIE", startSec: 67.8 },
      ],
      startSec: 50.2,
      endSec: 68.9,
    },
  ],
  flashCards: [
    { text: "IMMER JEMAND DA.", startSec: 48.3, endSec: 50.1 },
  ],
  chipGroups: [
    {
      chips: [
        { label: "AUSBILDUNGSTEAM", startSec: 30.4 },
        { label: "AUSBILDER", startSec: 32.1 },
        { label: "AUSBILDUNGSBEAUFTRAGTE IN JEDER ABTEILUNG", startSec: 34.9 },
        { label: "IMMER ANSPRECHBAR", startSec: 39.2 },
      ],
      endSec: 46.5,
    },
  ],
};

export const WlcV7Overlay: React.FC<WlcV7OverlayProps> = (props) => {
  const fontsLoaded = useWlcFonts();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  if (!fontsLoaded) return null;
  return (
    <AbsoluteFill>
      <OverlayCore props={props} />

      {props.chipGroups.map((group, i) => (
        <ChipStack key={`group-${i}`} chips={group.chips} outF={F(group.endSec)} />
      ))}

      {props.boards.map((board, i) => (
        <BenefitBoard
          key={`board-${i}`}
          title={board.title}
          items={board.items}
          inF={F(board.startSec)}
          outF={F(board.endSec)}
          numbered={board.numbered}
        />
      ))}

      {props.flashCards.map((card, i) => (
        <FlashCard key={`flash-${i}`} text={card.text} inF={F(card.startSec)} outF={F(card.endSec)} />
      ))}

      {props.review?.showGuides && (
        <ReviewOverlay
          showSafeZone={props.review.showSafeZone ?? true}
          showFaceZone={props.review.showFaceZone ?? true}
          showGrid={props.review.showGrid ?? false}
          faceZone={props.review.faceZone}
          guideOpacity={props.review.guideOpacity ?? 0.35}
        />
      )}
    </AbsoluteFill>
  );
};
