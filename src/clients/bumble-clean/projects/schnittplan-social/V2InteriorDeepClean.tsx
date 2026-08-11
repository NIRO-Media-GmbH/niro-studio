// ============================================================
// BumbleClean — Schnittplan Social · V2 „Interior-Deep-Clean"
// 2160×3840 (portrait-4k), 25fps, 1262 Frames (50,48 s) = exakte
// Länge von „Bumbleclean Video 2 Interior-Deep-Clean.mov".
// Alpha-Overlay, Designsprache wie V1 (Silent Luxury), Bausteine
// aus shared/motion-kit.
//   f012–f088   Hook „WAIT FOR THE RESULT" + Punkte-Loop (Wunsch
//               David 2026-08-09: Wait-for-result vor dem Edit)
//   f113–f163   Chip „⬡ INTERIOR DEEP CLEAN"
//   f455–f515   Chip „⬡ MATTEN · TIEFENREINIGUNG" (Tisch-Block)
//   f913–f929   Hexagon-Puls auf dem Drop (36,64 s)
//   f918–f950   „THE RESULT." Gold-Pop — Payoff des Hooks; endet
//               vor dem Leuchtkasten-Logo-Shot (~38 s)
//   f1184–f1254 Endcard kompakt (Schluss-Shot nur ~2,9 s):
//               Scrim, Waben-Draw, Wortmarke, Preis „ab 119 €"
//               (website-belegt 2026-08-09), CTA, Fade-out
// Schnitt-Anker: Drop-Cut bei 36,64 s; Result-Cuts auf dem Beat;
// letzter Schnitt 47,6 s → ruhiger Lenkrad-Shot bis 50,48 s.
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
import {
  GOLD,
  GOLD_TIEF,
  CLAMP,
  SMOOTH,
  POP,
  BASE_W,
  Stage,
  WabenEmblemDraw,
  HexPuls,
  GlassChip,
} from "../../shared/motion-kit";

const ci = loadBrand("bumble-clean", brandJson as any);

const { fontFamily: INTER } = loadFont("normal", {
  weights: ["400", "600", "700", "800"],
  subsets: ["latin", "latin-ext"],
});

// --- Timing (Frames @25fps) ---
const T = {
  hookIn: 12,
  hookOut: 88, // raus vor Cut bei 3,56 s
  chip1In: 113,
  chip1Out: 163,
  chip2In: 455,
  chip2Out: 515,
  drop: 916, // 36,64 s — Schnitt in die Result-Phase
  resultIn: 918,
  resultOut: 950, // weg vor Leuchtkasten-Shot (~38 s)
  endIn: 1184, // 47,36 s — weicher Einstieg in den Schluss-Shot
  fadeOutStart: 1240,
  fadeOutEnd: 1254,
} as const;

/** Hook „WAIT FOR THE RESULT" mit nacheinander aufpoppenden Punkten. */
const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < T.hookIn || frame > T.hookOut + 2) return null;
  const t = frame - T.hookIn;
  const inOp = interpolate(t, [0, 10], [0, 1], CLAMP);
  const outOp = interpolate(frame, [T.hookOut - 8, T.hookOut], [1, 0], CLAMP);
  const tracking = interpolate(t, [0, 26], [20, 8], {
    ...CLAMP,
    easing: Easing.out(Easing.cubic),
  });
  // Punkte-Loop: alle 10 Frames ein Punkt mehr, Zyklus 30 Frames
  const zyklus = ((t % 30) + 30) % 30;
  const punkte = Math.min(3, Math.floor(zyklus / 10) + 1);
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
      WAIT FOR THE RESULT
      <span style={{ letterSpacing: 4 }}>
        {".".repeat(punkte)}
        <span style={{ opacity: 0 }}>{".".repeat(3 - punkte)}</span>
      </span>
    </div>
  );
};

/** Chips unten links (Positionen wie V1). */
const Chips: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const chip = (from: number, to: number, text: string) => {
    if (frame < from || frame > to + 2) return null;
    const inSpring = spring({ frame: frame - from, fps, config: SMOOTH, durationInFrames: 18 });
    const outOp = interpolate(frame, [to - 8, to], [1, 0], CLAMP);
    return (
      <div style={{ position: "absolute", left: 64, top: 1478 }}>
        <GlassChip
          text={text}
          opacity={inSpring * outOp}
          translateY={(1 - inSpring) * 22}
          fontFamily={INTER}
        />
      </div>
    );
  };
  return (
    <>
      {chip(T.chip1In, T.chip1Out, "INTERIOR DEEP CLEAN")}
      {chip(T.chip2In, T.chip2Out, "MATTEN · TIEFENREINIGUNG")}
    </>
  );
};

/** Drop-Puls + „THE RESULT." — Payoff des Anfangs-Hooks. */
const DropResult: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <>
      {frame >= T.drop - 3 && frame <= T.drop + 13 && <HexPuls t={frame - (T.drop - 3)} />}
      {frame >= T.resultIn && frame <= T.resultOut + 1 && (
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 848,
            textAlign: "center",
            opacity:
              spring({ frame: frame - T.resultIn, fps, config: POP, durationInFrames: 16 }) *
              interpolate(frame, [T.resultOut - 6, T.resultOut], [1, 0], CLAMP),
            transform: `scale(${
              0.82 +
              0.18 * spring({ frame: frame - T.resultIn, fps, config: POP, durationInFrames: 16 })
            })`,
            fontFamily: INTER,
            fontWeight: 800,
            fontSize: 72,
            letterSpacing: 4,
            color: GOLD,
            textShadow: "0 2px 34px rgba(0,0,0,0.7)",
          }}
        >
          THE RESULT.
        </div>
      )}
    </>
  );
};

/** Endcard kompakt — Schluss-Shot ist nur ~2,9 s lang. */
const Endcard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.endIn) return null;
  const t = frame - T.endIn;
  const fadeOut = interpolate(frame, [T.fadeOutStart, T.fadeOutEnd], [1, 0], CLAMP);

  const markeIn = spring({ frame: t - 6, fps, config: SMOOTH, durationInFrames: 16 });
  const subIn = spring({ frame: t - 10, fps, config: SMOOTH, durationInFrames: 16 });
  const linieW = interpolate(t, [10, 22], [0, 220], {
    ...CLAMP,
    easing: Easing.out(Easing.cubic),
  });
  const preisIn = spring({ frame: t - 13, fps, config: POP, durationInFrames: 16 });
  const ctaIn = spring({ frame: t - 17, fps, config: SMOOTH, durationInFrames: 16 });
  const webIn = spring({ frame: t - 21, fps, config: SMOOTH, durationInFrames: 16 });
  const scrimIn = interpolate(t, [0, 10], [0, 1], CLAMP);

  return (
    <div style={{ position: "absolute", inset: 0, opacity: fadeOut }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: scrimIn,
          background:
            "radial-gradient(ellipse 600px 560px at 50% 40%, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.32) 55%, rgba(0,0,0,0) 78%)",
        }}
      />

      <div style={{ position: "absolute", left: BASE_W / 2 - 129, top: 424 }}>
        <WabenEmblemDraw r={43} progressFrame={t} stagger={2} strokeWidth={3} />
      </div>

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
        INNENAUFBEREITUNG · AB 119 €
      </div>

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

// --- Schema / Defaults / Master ---

export const v2InteriorSchema = projectPropsSchema.extend({
  videoDatei: z.string().describe("Dateiname des Schnitts (Preview-Unterlage)"),
  zeigeVideo: z
    .boolean()
    .describe("An = Video als Unterlage (nur Preview/Review); Aus = Alpha-Render"),
});
export type V2InteriorProps = z.infer<typeof v2InteriorSchema>;

export const v2InteriorDefaults: V2InteriorProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  durationInSeconds: 50.48, // 1262 Frames — exakt wie der Schnitt
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  videoDatei: "Bumbleclean Video 2 Interior-Deep-Clean.mov",
  // Für die Studio-Preview an. ACHTUNG beim Alpha-Render:
  // --props='{"zeigeVideo":false}' setzen, sonst wird das Video eingebrannt!
  zeigeVideo: true,
};

export const BumbleCleanV2Interior: React.FC<V2InteriorProps> = ({
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
          <Chips />
          <DropResult />
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
