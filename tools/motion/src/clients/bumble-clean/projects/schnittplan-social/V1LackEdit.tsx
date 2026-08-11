// ============================================================
// BumbleClean — Schnittplan Social · V1 „Lack-Edit" Overlay
// 2160×3840 (portrait-4k), 25fps, 566 Frames (22,64 s) = exakte
// Länge von „Bumbleclean Video 1 Lack-Edit.mov".
// Alpha-Overlay (Ansatz „Silent Luxury", David 2026-08-09):
//   f010–f058  Hook „19 JAHRE ALTER LACK."
//   f065–f115  Mini-Chip „Politur · Stufe 1" unten links
//   f250–f266  Hexagon-Puls exakt auf dem Bass-Drop (10,12 s)
//   f317–f442  Glass-Chip „Einstufige Politur" (ohne Preis —
//              David 2026-08-09: Preis erst in der Endcard)
//   f444–f456  Waben-Silhouette im Gold-Flare des Schnitts
//   f461–f560  Endcard: Scrim-Abdunklung, 7 Logo-Waben (Stroke-Draw),
//              Wortmarke, Gold-Linie, Preis „ab 199 €" (website-belegt,
//              geprüft 2026-08-09), CTA — Auto bleibt frei
// Musik-Raster: Drop bei 10,12 s, Beat ≈ 0,64 s (Beat 7 = 14,60 s,
// Flare = Beat 12 bei 17,80 s). Timings NICHT verschieben, ohne den
// Schnitt zu prüfen.
// Alpha-Falle beachtet: Chips ohne overflow:hidden (kein Shimmer).
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  useVideoConfig,
  useCurrentFrame,
  spring,
  interpolate,
  Easing,
  staticFile,
} from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/Inter";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";

const ci = loadBrand("bumble-clean", brandJson as any);

const { fontFamily: INTER } = loadFont("normal", {
  weights: ["400", "600", "700", "800"],
  subsets: ["latin", "latin-ext"],
});

// --- CI (identisch zum Messevideo) ---
const GOLD = "#FFD700";
const GOLD_TIEF = "#C9A227";
const MUTED = "#CFCFCF";
const GLASS = "rgba(10,10,10,0.38)"; // dunkler als Messevideo: liegt auf Video, nicht auf Schwarz
const GLASS_BORDER = "rgba(255,255,255,0.22)";
const RADIUS = 24;

// --- Design-Raum 1080×1920, Stage skaliert auf 2160×3840 ---
const BASE_W = 1080;
const BASE_H = 1920;

const FPS = 25;
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const SMOOTH = { damping: 20, stiffness: 100, mass: 1, overshootClamping: true };
const POP = { damping: 14, stiffness: 160, mass: 1 };

// --- Timing (Frames @25fps, siehe Kopfkommentar) ---
const T = {
  hookIn: 10,
  hookOut: 58,
  chip1In: 65,
  chip1Out: 115,
  drop: 253, // 10,12 s
  chip2In: 317, // Beat 4 nach Drop (12,68 s)
  chip2Out: 442,
  flareIn: 444,
  flareOut: 456,
  endIn: 461, // 18,44 s — nach dem Gold-Flare
  fadeOutStart: 548,
  fadeOutEnd: 560,
} as const;

const Stage: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { width, height } = useVideoConfig();
  const scale = Math.min(width / BASE_W, height / BASE_H);
  return (
    <div
      style={{
        position: "absolute",
        width: BASE_W,
        height: BASE_H,
        left: (width - BASE_W * scale) / 2,
        top: (height - BASE_H * scale) / 2,
        transform: `scale(${scale})`,
        transformOrigin: "top left",
      }}
    >
      {children}
    </div>
  );
};

// --- Hexagon-Helpers (Waben-Motiv aus dem Logo) ---
const hexPath = (cx: number, cy: number, r: number) => {
  const pts = Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 180) * (60 * i - 30);
    return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
  });
  return `M ${pts.join(" L ")} Z`;
};

/** Umfang eines Hexagons (6 Kanten) für Stroke-Draw. */
const hexUmfang = (r: number) => 6 * r;

/** 7-Zellen-Logo-Wabe; zeichnet sich Zelle für Zelle (Stroke-Draw). */
const WabenEmblemDraw: React.FC<{
  r: number;
  progressFrame: number; // Frames seit Start des Draws
  stagger?: number;
  stroke?: string;
  strokeWidth?: number;
}> = ({ r, progressFrame, stagger = 3, stroke = GOLD_TIEF, strokeWidth = 3 }) => {
  const d = r * 1.78;
  const zellen = [
    [0, 0],
    [0, -d],
    [0, d],
    [d * 0.87, -d * 0.5],
    [d * 0.87, d * 0.5],
    [-d * 0.87, -d * 0.5],
    [-d * 0.87, d * 0.5],
  ];
  const umfang = hexUmfang(r * 0.82);
  return (
    <svg
      width={r * 6}
      height={r * 6}
      viewBox={`${-r * 3} ${-r * 3} ${r * 6} ${r * 6}`}
      style={{ display: "block" }}
    >
      {zellen.map(([x, y], i) => {
        const p = interpolate(progressFrame - i * stagger, [0, 14], [0, 1], {
          ...CLAMP,
          easing: Easing.out(Easing.cubic),
        });
        return (
          <path
            key={i}
            d={hexPath(x, y, r * 0.82)}
            fill="none"
            stroke={stroke}
            strokeWidth={strokeWidth}
            strokeDasharray={umfang}
            strokeDashoffset={umfang * (1 - p)}
            opacity={p > 0 ? 0.95 : 0}
            strokeLinecap="round"
          />
        );
      })}
    </svg>
  );
};

/** Statisches 7-Zellen-Emblem (für Flare-Blitz). */
const WabenEmblem: React.FC<{ r: number; stroke?: string; strokeWidth?: number }> = ({
  r,
  stroke = GOLD,
  strokeWidth = 3,
}) => (
  <WabenEmblemDraw r={r} progressFrame={999} stagger={0} stroke={stroke} strokeWidth={strokeWidth} />
);

/** Kleines Hexagon-Icon für Chips. */
const HexIcon: React.FC<{ size: number; color?: string }> = ({ size, color = GOLD }) => (
  <svg width={size} height={size} viewBox="-12 -12 24 24" style={{ display: "block" }}>
    <path d={hexPath(0, 0, 9)} fill="none" stroke={color} strokeWidth={2.2} />
  </svg>
);

// ============================================================
// Elemente
// ============================================================

/** 1) Hook-Zeile — Letter-Spacing-Einflug, mittig oben. */
const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < T.hookIn || frame > T.hookOut + 2) return null;
  const t = frame - T.hookIn;
  const inOp = interpolate(t, [0, 10], [0, 1], CLAMP);
  const outOp = interpolate(frame, [T.hookOut - 8, T.hookOut], [1, 0], CLAMP);
  const tracking = interpolate(t, [0, 26], [22, 9], {
    ...CLAMP,
    easing: Easing.out(Easing.cubic),
  });
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: 548,
        textAlign: "center",
        opacity: inOp * outOp,
        fontFamily: INTER,
        fontWeight: 600,
        fontSize: 54,
        letterSpacing: tracking,
        color: "rgba(255,255,255,0.92)",
        textShadow: "0 2px 28px rgba(0,0,0,0.6)",
      }}
    >
      19 JAHRE ALTER LACK.
    </div>
  );
};

/** 2) Mini-Chip „Politur · Stufe 1" unten links. */
const ChipStufe1: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.chip1In || frame > T.chip1Out + 2) return null;
  const chipIn = spring({ frame: frame - T.chip1In, fps, config: SMOOTH, durationInFrames: 18 });
  const outOp = interpolate(frame, [T.chip1Out - 8, T.chip1Out], [1, 0], CLAMP);
  return (
    <div
      style={{
        position: "absolute",
        left: 64,
        top: 1478,
        display: "flex",
        alignItems: "center",
        gap: 14,
        padding: "16px 26px",
        background: GLASS,
        border: `1px solid ${GLASS_BORDER}`,
        borderRadius: RADIUS,
        opacity: chipIn * outOp,
        transform: `translateY(${(1 - chipIn) * 22}px)`,
      }}
    >
      <HexIcon size={30} />
      <span
        style={{
          fontFamily: INTER,
          fontWeight: 600,
          fontSize: 30,
          letterSpacing: 3,
          color: "rgba(255,255,255,0.94)",
        }}
      >
        POLITUR · STUFE 1
      </span>
    </div>
  );
};

/** 3) Hexagon-Puls exakt auf dem Bass-Drop. */
const DropPuls: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < T.drop - 3 || frame > T.drop + 13) return null;
  const t = frame - (T.drop - 3);
  // Haupt-Wabe: springt auf und verklingt
  const scale = interpolate(t, [0, 14], [0.72, 1.3], {
    ...CLAMP,
    easing: Easing.out(Easing.cubic),
  });
  const op = interpolate(t, [0, 3, 14], [0, 0.55, 0], CLAMP);
  // Echo-Wabe, 2 Frames später, gegenläufig kleiner
  const scale2 = interpolate(t, [2, 16], [1.15, 0.85], {
    ...CLAMP,
    easing: Easing.out(Easing.cubic),
  });
  const op2 = interpolate(t, [2, 5, 16], [0, 0.28, 0], CLAMP);
  return (
    <div
      style={{
        position: "absolute",
        left: BASE_W / 2 - 400,
        top: BASE_H / 2 - 400,
        width: 800,
        height: 800,
      }}
    >
      <svg width={800} height={800} viewBox="-400 -400 800 800" style={{ position: "absolute" }}>
        <path
          d={hexPath(0, 0, 340)}
          fill="none"
          stroke={GOLD}
          strokeWidth={4}
          opacity={op}
          transform={`scale(${scale})`}
        />
        <path
          d={hexPath(0, 0, 340)}
          fill="none"
          stroke={GOLD_TIEF}
          strokeWidth={2.5}
          opacity={op2}
          transform={`scale(${scale2})`}
        />
      </svg>
    </div>
  );
};

/** 4) Glass-Chip „Einstufige Politur" + andockendes Preis-Badge. */
const PolitutChip: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.chip2In || frame > T.chip2Out + 2) return null;
  const chipIn = spring({ frame: frame - T.chip2In, fps, config: SMOOTH, durationInFrames: 20 });
  const outOp = interpolate(frame, [T.chip2Out - 10, T.chip2Out], [1, 0], CLAMP);
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: 1430,
        display: "flex",
        justifyContent: "center",
        opacity: outOp,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 22,
          padding: "20px 34px",
          background: GLASS,
          border: `1px solid ${GLASS_BORDER}`,
          borderRadius: RADIUS,
          opacity: chipIn,
          transform: `translateY(${(1 - chipIn) * 26}px)`,
        }}
      >
        <HexIcon size={34} />
        <span
          style={{
            fontFamily: INTER,
            fontWeight: 600,
            fontSize: 38,
            letterSpacing: 2,
            color: "rgba(255,255,255,0.95)",
            whiteSpace: "nowrap",
          }}
        >
          EINSTUFIGE POLITUR
        </span>
      </div>
    </div>
  );
};

/** 5) Waben-Silhouette im Gold-Flare des Schnitts (17,8 s). */
const FlareEmblem: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < T.flareIn || frame > T.flareOut + 1) return null;
  const t = frame - T.flareIn;
  const op = interpolate(t, [0, 5, 12], [0, 0.5, 0], CLAMP);
  const scale = interpolate(t, [0, 12], [1.05, 0.98], CLAMP);
  return (
    <div
      style={{
        position: "absolute",
        left: BASE_W / 2 - 132,
        top: 900 - 132,
        opacity: op,
        transform: `scale(${scale})`,
      }}
    >
      <WabenEmblem r={44} stroke={GOLD} strokeWidth={3.5} />
    </div>
  );
};

/** 6) Endcard auf dem Hero-Shot — obere Bildhälfte, Auto bleibt frei. */
const Endcard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.endIn) return null;
  const t = frame - T.endIn;
  const fadeOut = interpolate(frame, [T.fadeOutStart, T.fadeOutEnd], [1, 0], CLAMP);

  const markeIn = spring({ frame: t - 17, fps, config: SMOOTH, durationInFrames: 20 });
  const subIn = spring({ frame: t - 25, fps, config: SMOOTH, durationInFrames: 20 });
  const linieW = interpolate(t, [27, 41], [0, 220], {
    ...CLAMP,
    easing: Easing.out(Easing.cubic),
  });
  const preisIn = spring({ frame: t - 33, fps, config: POP, durationInFrames: 20 });
  const ctaIn = spring({ frame: t - 39, fps, config: SMOOTH, durationInFrames: 20 });
  const webIn = spring({ frame: t - 45, fps, config: SMOOTH, durationInFrames: 20 });
  const scrimIn = interpolate(t, [0, 14], [0, 1], CLAMP);

  return (
    <div style={{ position: "absolute", inset: 0, opacity: fadeOut }}>
      {/* Scrim: weiche Abdunklung hinter dem Textblock — Lesbarkeit auf
          hellen Haubenreflexen; läuft randlos aus (alpha-sicher, kein Rahmen) */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: scrimIn,
          background:
            "radial-gradient(ellipse 600px 560px at 50% 40%, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.32) 55%, rgba(0,0,0,0) 78%)",
        }}
      />

      {/* Waben-Emblem zeichnet sich Zelle für Zelle */}
      <div style={{ position: "absolute", left: BASE_W / 2 - 129, top: 424 }}>
        <WabenEmblemDraw r={43} progressFrame={t} stagger={3} strokeWidth={3} />
      </div>

      {/* Wortmarke */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 716,
          textAlign: "center",
          opacity: markeIn,
          transform: `translateY(${(1 - markeIn) * 18}px)`,
          fontFamily: INTER,
          fontWeight: 800,
          fontSize: 66,
          letterSpacing: 11,
          color: "rgba(255,255,255,0.97)",
          textShadow: "0 2px 30px rgba(0,0,0,0.55)",
        }}
      >
        BUMBLE CLEAN
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 806,
          textAlign: "center",
          opacity: subIn,
          fontFamily: INTER,
          fontWeight: 600,
          fontSize: 27,
          letterSpacing: 13,
          color: GOLD,
        }}
      >
        CAR DETAILING
      </div>

      {/* Gold-Linie */}
      <div
        style={{
          position: "absolute",
          left: BASE_W / 2 - linieW / 2,
          top: 878,
          width: linieW,
          height: 5,
          borderRadius: 2.5,
          background: `linear-gradient(90deg, ${GOLD}, ${GOLD_TIEF})`,
        }}
      />

      {/* Preis — nur hier, nicht im Mittelteil (David 2026-08-09) */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 930,
          textAlign: "center",
          opacity: preisIn,
          transform: `scale(${0.85 + 0.15 * preisIn})`,
          fontFamily: INTER,
          fontWeight: 700,
          fontSize: 36,
          letterSpacing: 2.5,
          color: GOLD,
          textShadow: "0 2px 24px rgba(0,0,0,0.7)",
        }}
      >
        EINSTUFIGE POLITUR · AB 199 €
      </div>

      {/* CTA */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 998,
          textAlign: "center",
          opacity: ctaIn,
          transform: `translateY(${(1 - ctaIn) * 14}px)`,
          fontFamily: INTER,
          fontWeight: 800,
          fontSize: 46,
          letterSpacing: 2,
          color: "#FFFFFF",
          textShadow: "0 2px 26px rgba(0,0,0,0.7)",
        }}
      >
        TERMIN PER DM
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 1068,
          textAlign: "center",
          opacity: webIn,
          fontFamily: INTER,
          fontWeight: 600,
          fontSize: 30,
          letterSpacing: 1.5,
          color: "rgba(255,255,255,0.88)",
          textShadow: "0 2px 22px rgba(0,0,0,0.65)",
        }}
      >
        bumble-clean.de · Bad Rappenau
      </div>
    </div>
  );
};

// ============================================================
// Schema / Defaults / Master
// ============================================================

export const v1LackEditSchema = projectPropsSchema.extend({
  videoDatei: z.string().describe("Dateiname des Schnitts (Preview-Unterlage)"),
  zeigeVideo: z
    .boolean()
    .describe("An = Video als Unterlage (nur Preview/Review); Aus = Alpha-Render"),
});
export type V1LackEditProps = z.infer<typeof v1LackEditSchema>;

export const v1LackEditDefaults: V1LackEditProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  durationInSeconds: 22.64, // 566 Frames — exakt wie der Schnitt
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  videoDatei: "Bumbleclean Video 1 Lack-Edit.mov",
  // Für die Studio-Preview an. ACHTUNG beim Alpha-Render:
  // --props='{"zeigeVideo":false}' setzen, sonst wird das Video eingebrannt!
  zeigeVideo: true,
};

export const BumbleCleanV1LackEdit: React.FC<V1LackEditProps> = ({
  videoDatei,
  zeigeVideo,
  review,
}) => {
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {zeigeVideo && (
          <OffthreadVideo
            src={staticFile(`projects/bumble-clean-schnittplan/${videoDatei}`)}
            muted
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        )}
        <Stage>
          <Hook />
          <ChipStufe1 />
          <DropPuls />
          <PolitutChip />
          <FlareEmblem />
          <Endcard />
        </Stage>
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
    </CIProvider>
  );
};
