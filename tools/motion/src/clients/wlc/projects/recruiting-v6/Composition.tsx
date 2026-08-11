// ============================================================
// WLC — Recruiting Video 6 „Alles Lager. Alles hier."
// Motion-Graphics-Paket (4 Kompositionen):
//   1. WlcV6WortBattle  — Antonym-Overlay, 6s-Blöcke (3s/Wort),
//      Red-Sweep-Transition zwischen den Blöcken (Alpha-Overlay)
//   2. WlcV6Trio        — „ALLES LAGER. ALLES WIR. ALLES HIER." (Alpha)
//   3. WlcV6BeweisCard  — Map 12 Standorte + „SEIT 1996…" (Vollbild)
//   4. WlcV6Outro       — Map (Zoom auf Region) → CTA, EIN Take (Vollbild)
// CI: WLC CD-Richtlinien 2025. TABU: kein „Deutschland"-Wording.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { fitText } from "@remotion/layout-utils";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  FONT_BOLD,
  FONT_BOOK,
  FONT_XBDCN,
  GRAU_85,
  RedSweep,
  WUERTH_ROT,
  WUERTH_WEISS,
  WlcStatement,
  WlcWord,
  useWlcFonts,
} from "../../components";

// ============================================================
// 1. WORT-BATTLE (Antonym-Vergleiche)
// ============================================================

const pairSchema = z.object({
  a: z.string().describe("Wort 1 (z. B. LAUT)"),
  b: z.string().describe("Wort 2 (z. B. LEISE)"),
});

export const wlcWortBattleSchema = projectPropsSchema.extend({
  pairs: z.array(pairSchema).describe("Antonym-Paare"),
  wordSec: z.number().min(0.5).max(10).step(0.1).describe("Dauer pro Wort (Sek)"),
  transitionSec: z.number().min(0).max(3).step(0.1).describe("Transition zwischen Blöcken (Sek)"),
  wordOffsetY: z.number().step(1).describe("Y-Offset der Wörter (px)"),
});

export type WlcWortBattleProps = z.infer<typeof wlcWortBattleSchema>;

const V6_PAIRS = [
  { a: "LAUT", b: "LEISE" },
  { a: "SCHNELL", b: "GENAU" },
  { a: "HAND", b: "MASCHINE" },
  { a: "DRINNEN", b: "DRAUSSEN" },
  { a: "TONNEN", b: "GRAMM" },
  { a: "ALLEIN", b: "TEAM" },
];

// 6 Blöcke à 6s + 5 Transitions à 1s = 41s
export const wlcWortBattleDefaults: WlcWortBattleProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  durationInSeconds: 41,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  pairs: V6_PAIRS,
  wordSec: 3,
  transitionSec: 1,
  wordOffsetY: 0,
};

export const WlcV6WortBattle: React.FC<WlcWortBattleProps> = ({
  review,
  pairs,
  wordSec,
  transitionSec,
  wordOffsetY,
}) => {
  const fontsLoaded = useWlcFonts();
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.round(sec * fps);

  const blockSec = wordSec * 2;
  const blockStart = (i: number) => i * (blockSec + transitionSec);

  if (!fontsLoaded) return null;

  return (
    <AbsoluteFill>
      {pairs.map((pair, i) => {
        const start = blockStart(i);
        const isLast = i === pairs.length - 1;
        return (
          <React.Fragment key={`block-${i}`}>
            <Sequence
              from={s(start)}
              durationInFrames={s(wordSec)}
              name={`${i + 1}A: ${pair.a}`}
            >
              <WlcWord word={pair.a} offsetY={wordOffsetY} />
            </Sequence>
            <Sequence
              from={s(start + wordSec)}
              durationInFrames={s(wordSec)}
              name={`${i + 1}B: ${pair.b}`}
            >
              <WlcWord word={pair.b} offsetY={wordOffsetY} />
            </Sequence>
            {/* Transition überdeckt die Blockgrenze: startet mit Blockende */}
            {!isLast && transitionSec > 0 && (
              <Sequence
                from={s(start + blockSec)}
                durationInFrames={s(transitionSec)}
                name={`Transition ${i + 1}→${i + 2}`}
              >
                <RedSweep durationInFrames={s(transitionSec)} />
              </Sequence>
            )}
          </React.Fragment>
        );
      })}

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
// 2. AUFLÖSUNGS-TRIO
// ============================================================

export const wlcTrioSchema = projectPropsSchema.extend({
  statements: z.array(z.string()).describe("Statements (nacheinander)"),
  statementIntervalSec: z.number().min(0.5).max(10).step(0.1).describe("Abstand zwischen Statements (Sek)"),
});

export type WlcTrioProps = z.infer<typeof wlcTrioSchema>;

export const wlcTrioDefaults: WlcTrioProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  durationInSeconds: 8,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  // Kundenfeedback 21.07.: neuer Claim (ersetzt „Alles Lager. Alles Wir.
  // Alles Hier."), Zeilen enger, Punkte weiß (via WlcStatement)
  statements: ["MEIN WEG.", "MEINE ENTWICKLUNG.", "MEINE ZUKUNFT BEI WLC."],
  statementIntervalSec: 2.4,
};

export const WlcV6Trio: React.FC<WlcTrioProps> = ({
  review,
  statements,
  statementIntervalSec,
}) => {
  const fontsLoaded = useWlcFonts();
  const { fps, width, height } = useVideoConfig();

  const longest = statements.reduce(
    (acc, t) => (t.length > acc.length ? t : acc),
    ""
  );
  const { fontSize } = fitText({
    text: longest,
    withinWidth: width * 0.8,
    fontFamily: FONT_XBDCN,
    fontWeight: "normal",
  });
  const size = Math.min(fontSize, height * 0.09);

  if (!fontsLoaded) return null;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        // Kundenfeedback 21.07.: Slogans enger zusammensetzen
        gap: size * 0.2,
      }}
    >
      {statements.map((text, i) => (
        <WlcStatement
          key={`stmt-${i}`}
          text={text}
          fontSize={size}
          delayFrames={Math.round(i * statementIntervalSec * fps)}
        />
      ))}

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
// 3. BEWEIS-CARD (Map + Pins + „SEIT 1996…")
// ============================================================

const pinSchema = z.object({
  x: z.number().describe("X (Map-Koordinate 0–1000)"),
  y: z.number().describe("Y (Map-Koordinate 0–1360)"),
  highlight: z.boolean().optional().describe("Hervorheben (größerer Pin)"),
});

export const wlcBeweisCardSchema = projectPropsSchema.extend({
  headlineTop: z.string().describe("Headline Zeile 1"),
  headlineBottom: z.string().describe("Headline Zeile 2"),
  pins: z.array(pinSchema).describe("Standort-Pins (6 belegte; Anzahl 6/10/12 mit Kunde klären)"),
  showLogo: z.boolean().describe("Würth|WLC-Logo unten zeigen"),
});

export type WlcBeweisCardProps = z.infer<typeof wlcBeweisCardSchema>;

// Vereinfachte Landes-Silhouette (Bounding: 0–1000 / 0–1360).
// ENTWURF — Feinschliff, sobald finale Map-Grafik/Standortliste da ist.
const MAP_OUTLINE =
  "M276,10 L385,45 L467,115 L581,98 L679,168 L821,80 L908,203 L930,290 " +
  "L952,482 L963,552 L996,683 L974,726 L908,735 L767,813 L679,848 L723,883 " +
  "L865,1058 L829,1133 L778,1268 L778,1302 L690,1302 L592,1337 L570,1334 " +
  "L527,1311 L481,1360 L418,1311 L360,1292 L298,1285 L188,1309 L185,1233 " +
  "L210,1133 L257,1058 L123,1023 L55,976 L49,918 L36,831 L16,749 L0,700 " +
  "L25,604 L14,569 L91,534 L123,482 L134,412 L134,307 L145,297 Z";

// Recherche 2026-07-15 (wlc-online.com → Standorte): 6 belegte Standorte,
// alle in Hohenlohe/Heilbronn-Franken. Konzept sagt „12", Intralogistik-BW
// „10" (3 Haupt + 7 Außenlager, unbenannt) — Zahl VOR Live-Gang mit
// Cornelia klären. Koordinaten: lineare Lat/Lon-Projektion in die Map-Box.
const VERIFIED_PINS = [
  { x: 384, y: 988, highlight: true }, // Adelsheim (Hauptsitz)
  { x: 417, y: 1019, highlight: true }, // Kupferzell (zentrales Außenlager)
  { x: 377, y: 1017 }, // Neuenstadt am Kocher
  { x: 416, y: 1009 }, // Kemmeten (Künzelsau)
  { x: 397, y: 1023 }, // Öhringen
  { x: 458, y: 1034 }, // Crailsheim
];

export const wlcBeweisCardDefaults: WlcBeweisCardProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  durationInSeconds: 4,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  headlineTop: "SEIT 1996.",
  headlineBottom: "WLC. WÜRTH-LOGISTIK.",
  pins: VERIFIED_PINS,
  showLogo: true,
};

const MapPin: React.FC<{
  x: number;
  y: number;
  highlight?: boolean;
  delayFrames: number;
  sizeFactor?: number;
}> = ({ x, y, highlight, delayFrames, sizeFactor = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = Math.max(frame - delayFrames, 0);
  const visible = frame >= delayFrames;

  const drop = spring({
    frame: local,
    fps,
    config: { damping: 14, mass: 0.5, stiffness: 300 },
  });
  const r = (highlight ? 15 : 10) * sizeFactor * drop;
  const ringR = interpolate(local, [0, fps * 0.6], [0, (highlight ? 46 : 32) * sizeFactor], {
    extrapolateRight: "clamp",
  });
  const ringOpacity = interpolate(local, [0, fps * 0.6], [0.8, 0], {
    extrapolateRight: "clamp",
  });

  if (!visible) return null;
  return (
    <>
      <circle cx={x} cy={y} r={ringR} fill="none" stroke={WUERTH_ROT} strokeWidth={4} opacity={ringOpacity} />
      <circle cx={x} cy={y} r={r} fill={WUERTH_ROT} />
      <circle cx={x} cy={y} r={r * 0.4} fill={WUERTH_WEISS} opacity={drop} />
    </>
  );
};

export const WlcV6BeweisCard: React.FC<WlcBeweisCardProps> = ({
  review,
  headlineTop,
  headlineBottom,
  pins,
  showLogo,
}) => {
  const fontsLoaded = useWlcFonts();
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const mapOpacity = interpolate(frame, [0, fps * 0.4], [0, 1], {
    extrapolateRight: "clamp",
  });
  const mapScale = interpolate(frame, [0, fps * 0.4], [1.04, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });

  const headlineDelay = Math.round(fps * 1.2);
  const punch = spring({
    frame: Math.max(frame - headlineDelay, 0),
    fps,
    config: { damping: 60, mass: 0.4, stiffness: 400, overshootClamping: true },
  });
  const headlineOpacity = frame < headlineDelay ? 0 : 1;
  const headlineScale = interpolate(punch, [0, 1], [1.1, 1]);

  const { fontSize: topSize } = fitText({
    text: headlineTop,
    withinWidth: width * 0.62,
    fontFamily: FONT_XBDCN,
    fontWeight: "normal",
  });
  const { fontSize: bottomSize } = fitText({
    text: headlineBottom,
    withinWidth: width * 0.82,
    fontFamily: FONT_XBDCN,
    fontWeight: "normal",
  });
  const hlTop = Math.min(topSize, height * 0.075);
  const hlBottom = Math.min(bottomSize, height * 0.055);

  const logoOpacity = interpolate(frame, [fps * 1.6, fps * 2.1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const pinStagger = Math.round(fps * 0.08);
  const pinBase = Math.round(fps * 0.5);

  // Lupe: Alle belegten Standorte liegen eng in Hohenlohe/Heilbronn-Franken.
  // Ein Detail-Kreis oben rechts vergrößert die Cluster-Region (Faktor k),
  // damit sich die Pins auffächern — Deutschland-Kontext bleibt sichtbar.
  const CLUSTER = { x: 417, y: 1015 };
  const LENS = { x: 740, y: 470, r: 250, k: 3.4 };
  const lensP = spring({
    frame: Math.max(frame - Math.round(fps * 1.7), 0),
    fps,
    config: { damping: 18, mass: 0.6, stiffness: 220 },
  });
  const lensVisible = frame >= Math.round(fps * 1.7);
  // Verbindungslinie Cluster → Lupenrand
  const dx = LENS.x - CLUSTER.x;
  const dy = LENS.y - CLUSTER.y;
  const dLen = Math.hypot(dx, dy);
  const edge = {
    x: LENS.x - (dx / dLen) * LENS.r,
    y: LENS.y - (dy / dLen) * LENS.r,
  };
  const lensPin = (p: { x: number; y: number }) => ({
    x: LENS.x + (p.x - CLUSTER.x) * LENS.k,
    y: LENS.y + (p.y - CLUSTER.y) * LENS.k,
  });
  const lensPinBase = Math.round(fps * 2.0);

  if (!fontsLoaded) return null;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {/* Headline */}
      <div
        style={{
          position: "absolute",
          top: "9%",
          width: "100%",
          textAlign: "center",
          opacity: headlineOpacity,
          transform: `scale(${headlineScale})`,
        }}
      >
        <div
          style={{
            fontFamily: FONT_XBDCN,
            fontWeight: "normal" as const,
            fontSize: hlTop,
            color: WUERTH_WEISS,
            lineHeight: 1.05,
          }}
        >
          {headlineTop.replace(/\.$/, "")}
          <span style={{ color: WUERTH_WEISS }}>.</span>
        </div>
        <div
          style={{
            fontFamily: FONT_XBDCN,
            fontWeight: "normal" as const,
            fontSize: hlBottom,
            color: WUERTH_WEISS,
            lineHeight: 1.15,
          }}
        >
          {headlineBottom}
        </div>
      </div>

      {/* Map + Pins + Lupe */}
      <div
        style={{
          position: "absolute",
          top: "24%",
          left: "50%",
          transform: `translateX(-50%) scale(${mapScale})`,
          opacity: mapOpacity,
          width: "68%",
        }}
      >
        <svg viewBox="-40 -40 1080 1440" style={{ width: "100%", display: "block" }}>
          <path d={MAP_OUTLINE} fill={GRAU_85} stroke={GRAU_85} strokeWidth={8} strokeLinejoin="round" />
          {pins.map((pin, i) => (
            <MapPin
              key={`pin-${i}`}
              x={pin.x}
              y={pin.y}
              highlight={pin.highlight}
              delayFrames={pinBase + i * pinStagger}
            />
          ))}

          {/* Lupe: vergrößerte Cluster-Region */}
          {lensVisible && (
            <g opacity={Math.min(lensP * 1.2, 1)}>
              <line
                x1={CLUSTER.x}
                y1={CLUSTER.y}
                x2={edge.x}
                y2={edge.y}
                stroke={WUERTH_WEISS}
                strokeWidth={3}
                opacity={0.7}
              />
              <g transform={`translate(${LENS.x} ${LENS.y}) scale(${lensP}) translate(${-LENS.x} ${-LENS.y})`}>
                <circle
                  cx={LENS.x}
                  cy={LENS.y}
                  r={LENS.r}
                  fill="#000000"
                  fillOpacity={0.88}
                  stroke={WUERTH_WEISS}
                  strokeWidth={4}
                />
                {pins.map((pin, i) => {
                  const p = lensPin(pin);
                  return (
                    <MapPin
                      key={`lens-pin-${i}`}
                      x={p.x}
                      y={p.y}
                      highlight={pin.highlight}
                      delayFrames={lensPinBase + i * pinStagger}
                      sizeFactor={1.4}
                    />
                  );
                })}
              </g>
            </g>
          )}
        </svg>
      </div>

      {/* Logo */}
      {showLogo && (
        <div
          style={{
            position: "absolute",
            bottom: "8%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
            opacity: logoOpacity,
          }}
        >
          <Img
            src={staticFile("clients/wlc/logo-white.png")}
            style={{ width: "52%" }}
          />
        </div>
      )}

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
// 4. OUTRO (Map → CTA, EIN fließender Take)
// Phase 1: „SEIT 1996." + Landes-Silhouette, Pins droppen als
//   Regional-Cluster, Kamera zoomt in die Region (Pins fächern auf).
// Phase 2: Zoom läuft weiter durch (Zoom-Through), Map löst sich
//   auf → Team-Wappen + Logo + Claim-Zeile + roter CTA-Balken.
//   Keine Hashtags im Bild (gehören in die Post-Copy — David).
// CI strikt: Schwarz/Weiß/Würth-Rot, Grau 85 nur als Kartenfläche,
// harte Versalien, keine Effekt-Deko (David-Feedback 2026-07-15:
// v2 „MAN-Style" war zu überladen, Firmenname nur im Logo).
// ============================================================

const PUNCH = { damping: 60, mass: 0.4, stiffness: 400, overshootClamping: true };

export const wlcOutroSchema = projectPropsSchema.extend({
  headline: z.string().describe("Headline Phase 1 (über der Karte)"),
  pins: z.array(pinSchema).describe("Standort-Pins (6 belegte; 6/10/12 mit Kunde klären)"),
  zoomFactor: z.number().min(1).max(6).step(0.1).describe("Zoom in die Region"),
  mapSec: z.number().min(2).max(10).step(0.1).describe("Dauer Map-Phase bis Übergang (Sek)"),
  ctaText: z.string().describe("CTA-Zeile (roter Balken)"),
  claim: z.string().describe("Claim-Zeile über dem CTA"),
  brandStyle: z.enum(["wappen", "logobox"]).describe("Marken-Variante (Feedback 21.07.: Wappen ODER Logo im weißen Kasten)"),
  jobs: z.array(z.string()).describe("Optional: Stellen untereinander (je mit m/w/d) — Feedback 21.07."),
});

export type WlcOutroProps = z.infer<typeof wlcOutroSchema>;

export const wlcOutroDefaults: WlcOutroProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  durationInSeconds: 8,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  headline: "SEIT 1996.",
  pins: VERIFIED_PINS,
  zoomFactor: 2.3,
  mapSec: 3.2,
  ctaText: "BEWIRB DICH JETZT.",
  // Kundenfeedback 21.07.: neuer Claim
  claim: "MEIN WEG. MEINE ENTWICKLUNG. MEINE ZUKUNFT BEI WLC.",
  brandStyle: "wappen",
  jobs: [],
};

export const WlcV6Outro: React.FC<WlcOutroProps> = ({
  review,
  headline,
  pins,
  zoomFactor,
  mapSec,
  ctaText,
  claim,
  brandStyle,
  jobs,
}) => {
  const fontsLoaded = useWlcFonts();
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);

  // --- Phase-1-Timing ---
  const headlineStart = F(0.2);
  const mapInStart = F(0.3);
  const pinBase = F(0.9);
  const pinStagger = F(0.08);
  const zoomStart = F(1.7);
  const zoomEnd = F(mapSec);
  // Übergang: Zoom läuft weiter, während Map + Headline ausblenden
  const fadeStart = F(mapSec);
  const fadeEnd = F(mapSec + 0.5);

  // --- Phase-2-Timing ---
  const wappenStart = F(mapSec + 0.25);
  const logoStart = F(mapSec + 0.45);
  const claimStart = F(mapSec + 0.75);
  const ctaStart = F(mapSec + 1.05);

  // --- Map ---
  const mapOpacityIn = interpolate(frame, [mapInStart, mapInStart + F(0.4)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const mapFadeOut = interpolate(frame, [fadeStart, fadeEnd], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Zoom: 1 → zoomFactor bis Phasenende, danach Push-Through weiter
  const zoomP = interpolate(frame, [zoomStart, zoomEnd], [0, 1], {
    easing: Easing.bezier(0.5, 0, 0.3, 1),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const pushP = interpolate(frame, [fadeStart, fadeEnd], [0, 1], {
    easing: Easing.in(Easing.quad),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const zoomScale = 1 + zoomP * (zoomFactor - 1) + pushP * 0.9;

  // Zoom-Ziel: Schwerpunkt der Pins (dynamisch — funktioniert auch mit 10/12)
  const cx = pins.reduce((s, p) => s + p.x, 0) / Math.max(pins.length, 1);
  const cy = pins.reduce((s, p) => s + p.y, 0) / Math.max(pins.length, 1);
  const originX = ((cx + 40) / 1080) * 100;
  const originY = ((cy + 40) / 1440) * 100;

  // Pins: konstante Bildschirmgröße trotz Zoom (Radius / Zoom) —
  // dadurch fächern sie sich beim Reinzoomen sichtbar auf
  const pinSize = 1 / zoomScale;

  // --- Headline Phase 1 ---
  const hlPunch = spring({ frame: Math.max(frame - headlineStart, 0), fps, config: PUNCH });
  const hlOpacity = (frame < headlineStart ? 0 : 1) * mapFadeOut;
  const hlScale = interpolate(hlPunch, [0, 1], [1.1, 1]);
  const { fontSize: hlFit } = fitText({
    text: headline,
    withinWidth: width * 0.6,
    fontFamily: FONT_XBDCN,
    fontWeight: "normal",
  });
  const hlSize = Math.min(hlFit, height * 0.075);

  // --- Phase 2 (Logo, CTA, Hashtags) ---
  const punchIn = (startFrame: number) => {
    const p = spring({ frame: Math.max(frame - startFrame, 0), fps, config: PUNCH });
    return {
      opacity: frame < startFrame ? 0 : 1,
      transform: `scale(${interpolate(p, [0, 1], [1.08, 1])})`,
    };
  };
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
  const claimFontSize = Math.min(
    fitText({
      text: claim,
      withinWidth: width * 0.74,
      fontFamily: FONT_BOLD,
      fontWeight: "normal",
    }).fontSize,
    height * 0.021
  );
  // Optionale Stellen-Liste (Feedback 21.07.) schiebt Claim hoch + CTA runter
  const claimTop = jobs.length > 0 ? 0.408 : 0.43;
  const jobsTop = 0.452;
  const ctaTop = jobs.length > 0 ? jobsTop + jobs.length * 0.027 + 0.02 : 0.495;
  const jobFontSize = Math.min(
    height * 0.017,
    ...jobs.map(
      (j) => fitText({ text: j, withinWidth: width * 0.8, fontFamily: FONT_XBDCN, fontWeight: "normal" }).fontSize
    )
  );
  // Claim-Segmente: Punkte in Würth-Rot (Anbindung ans Trio)
  const claimParts = claim
    .split(".")
    .map((s) => s.trim())
    .filter(Boolean);

  if (!fontsLoaded) return null;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {/* Phase 1: Headline */}
      <div
        style={{
          position: "absolute",
          top: "11%",
          width: "100%",
          textAlign: "center",
          opacity: hlOpacity,
          transform: `scale(${hlScale})`,
        }}
      >
        <div
          style={{
            fontFamily: FONT_XBDCN,
            fontWeight: "normal" as const,
            fontSize: hlSize,
            color: WUERTH_WEISS,
            lineHeight: 1.05,
          }}
        >
          {headline.replace(/\.$/, "")}
          <span style={{ color: WUERTH_WEISS }}>.</span>
        </div>
      </div>

      {/* Phase 1: Map mit Kamera-Zoom (Fenster clippt den Zoom) */}
      <div
        style={{
          position: "absolute",
          top: "18%",
          bottom: "10%",
          left: 0,
          right: 0,
          overflow: "hidden",
          opacity: mapOpacityIn * mapFadeOut,
          maskImage:
            "linear-gradient(180deg, transparent 0%, black 7%, black 93%, transparent 100%)",
          WebkitMaskImage:
            "linear-gradient(180deg, transparent 0%, black 7%, black 93%, transparent 100%)",
        }}
      >
        <div
          style={{
            width: "68%",
            margin: "0 auto",
            transform: `scale(${zoomScale})`,
            transformOrigin: `${originX}% ${originY}%`,
          }}
        >
          <svg viewBox="-40 -40 1080 1440" style={{ width: "100%", display: "block" }}>
            <path d={MAP_OUTLINE} fill={GRAU_85} stroke={GRAU_85} strokeWidth={8} strokeLinejoin="round" />
            {pins.map((pin, i) => (
              <MapPin
                key={`pin-${i}`}
                x={pin.x}
                y={pin.y}
                highlight={pin.highlight}
                delayFrames={pinBase + i * pinStagger}
                sizeFactor={pinSize}
              />
            ))}
          </svg>
        </div>
      </div>

      {/* Phase 2: Marke — Kundenfeedback 21.07. „zu viel Wappen+Logo":
          entweder NUR Wappen groß oder NUR Logo im weißen Kasten */}
      {brandStyle === "wappen" ? (
        <div
          style={{
            position: "absolute",
            top: "22%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
            ...punchIn(wappenStart),
          }}
        >
          <Img src={staticFile("clients/wlc/wappen.png")} style={{ width: "26%" }} />
        </div>
      ) : (
        <div
          style={{
            position: "absolute",
            top: "31%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
            ...punchIn(logoStart),
          }}
        >
          <div
            style={{
              backgroundColor: WUERTH_WEISS,
              padding: `${height * 0.02}px ${width * 0.045}px`,
              boxShadow: "0 12px 50px rgba(0,0,0,0.5)",
            }}
          >
            <Img src={staticFile("clients/wlc/logo-pos.jpg")} style={{ width: width * 0.5 }} />
          </div>
        </div>
      )}

      {/* Phase 2: Claim-Zeile (weiße Punkte wie im Trio — Feedback 21.07.) */}
      <div
        style={{
          position: "absolute",
          top: `${claimTop * 100}%`,
          width: "100%",
          textAlign: "center",
          fontFamily: FONT_BOLD,
          fontSize: claimFontSize,
          letterSpacing: "0.09em",
          color: WUERTH_WEISS,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          ...punchIn(claimStart),
        }}
      >
        {claimParts.map((part, i) => (
          <React.Fragment key={`claim-${i}`}>
            {i > 0 && " "}
            {part}
            <span style={{ color: WUERTH_WEISS }}>.</span>
          </React.Fragment>
        ))}
      </div>

      {/* Phase 2 optional: Stellen untereinander, je (M/W/D) — Feedback 21.07. */}
      {jobs.length > 0 && (
        <div
          style={{
            position: "absolute",
            top: `${jobsTop * 100}%`,
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: height * 0.009,
          }}
        >
          {jobs.map((job, i) => (
            <div
              key={`job-${i}`}
              style={{
                fontFamily: FONT_XBDCN,
                fontWeight: "normal" as const,
                fontSize: jobFontSize,
                lineHeight: 1.1,
                letterSpacing: "0.02em",
                color: WUERTH_WEISS,
                textTransform: "uppercase",
                whiteSpace: "nowrap",
                borderLeft: `${Math.max(4, width * 0.005)}px solid ${WUERTH_ROT}`,
                paddingLeft: height * 0.01,
                ...punchIn(F(mapSec + 0.9) + i * F(0.1)),
              }}
            >
              {job}
            </div>
          ))}
        </div>
      )}

      {/* Phase 2: CTA-Balken (Würth-Rot, weiße Versalien, Wipe von links) */}
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
