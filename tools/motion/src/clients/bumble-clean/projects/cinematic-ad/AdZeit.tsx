// ============================================================
// BumbleClean — Cinematic Ad „Was die Zeit nimmt"
// 1080×1920 (portrait, Video ist nativ 1080p), 25fps,
// 1255 Frames (50,2 s) = exakte Länge von
// „Cinemtatic Werbeanzeige.mov" (2026-08 Cinematic Ad).
//
// Overlay-Philosophie (Rev. 2, David 2026-08-29: „präsenter,
// dynamisch, CI, darf Screen füllen; Sound-Hinweis raus"):
// Die VO-Zeilen sind große Kinetic-Typo-Statements — Wort für
// Wort synchron zu den Whisper-Wort-Timestamps aufpoppend,
// Inter 800 Uppercase, Schlüsselwörter in Gold, zentriert mit
// weichem Radial-Scrim. KEINE Grafik in der stummen Strecke
// (17,8–35,9 s). Endcard: Aufbau exakt auf dem gesprochenen
// „BumbleClean" (f1025 = 41,0 s), Claim + „TERMIN BUCHEN →"
// auf der Musik-Auflösung (f1115 = 44,6 s), Fade mit Video-Fade.
// Wort-Anker aus faster-whisper — Timings nicht verschieben,
// ohne den Schnitt neu zu prüfen.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  useVideoConfig,
  useCurrentFrame,
  spring,
  interpolate,
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
  BASE_H,
  Stage,
  WabenEmblemDraw,
} from "../../shared/motion-kit";

const ci = loadBrand("bumble-clean", brandJson as any);

const { fontFamily: INTER } = loadFont("normal", {
  weights: ["400", "500", "600", "700", "800"],
  subsets: ["latin", "latin-ext"],
});

// --- Timing (Frames @25fps, Anker aus Whisper/Waveform) ---
const T = {
  endIn: 1025, // gesprochenes „BumbleClean" (41,0 s)
  claimIn: 1115, // Musik-Auflösung (44,6 s)
  buttonIn: 1135,
  webIn: 1155,
  fadeOutStart: 1235, // Video faded selbst ab ~49,4 s
  fadeOutEnd: 1247,
} as const;

// --- Kinetic-Typo: Wort-Anker in Sekunden (faster-whisper) ---
type Wort = { text: string; at: number; gold?: boolean; br?: boolean };
type Zeile = { out: number; size: number; worte: Wort[] };

const ZEILEN: Zeile[] = [
  {
    // „Schon klar — das hier ist Werbung." (Sprechpause nach „klar")
    out: 9.65,
    size: 76,
    worte: [
      { text: "SCHON", at: 6.62 },
      { text: "KLAR —", at: 7.0 },
      { text: "DAS", at: 8.17, br: true },
      { text: "HIER", at: 8.33 },
      { text: "IST", at: 8.55 },
      { text: "WERBUNG.", at: 8.83, gold: true },
    ],
  },
  {
    out: 12.6,
    size: 64,
    worte: [
      { text: "ABER", at: 10.05 },
      { text: "DIE", at: 10.31 },
      { text: "KRATZER", at: 10.7 },
      { text: "IN", at: 10.91, br: true },
      { text: "DEINEM", at: 11.25 },
      { text: "LACK", at: 11.51 },
      { text: "SIND", at: 11.79, br: true },
      { text: "ECHT.", at: 12.13, gold: true },
    ],
  },
  {
    out: 15.0,
    size: 64,
    worte: [
      { text: "UND", at: 12.79 },
      { text: "DEIN", at: 12.95 },
      { text: "MITGENOMMENES", at: 13.01, br: true },
      { text: "INTERIEUR", at: 13.83, gold: true, br: true },
      { text: "AUCH.", at: 14.3 },
    ],
  },
  {
    out: 17.8, // raus vor dem Schwarz-Atemloch (18,0)
    size: 84,
    worte: [
      { text: "ES", at: 15.38 },
      { text: "IST", at: 15.63 },
      { text: "ZEIT,", at: 15.81, gold: true },
      { text: "ETWAS", at: 16.11, br: true },
      { text: "DAGEGEN", at: 16.47 },
      { text: "ZU", at: 16.89, br: true },
      { text: "TUN.", at: 17.2 },
    ],
  },
  {
    out: 39.85, // raus vor Endcard-Aufbau (41,0)
    size: 56,
    worte: [
      { text: "EIN", at: 36.02 },
      { text: "FAHRZEUG", at: 36.16 },
      { text: "IST", at: 36.6 },
      { text: "ERST", at: 36.86 },
      { text: "FERTIG,", at: 37.06, br: true },
      { text: "WENN", at: 37.94 },
      { text: "JEDES", at: 38.2 },
      { text: "DETAIL", at: 38.64, gold: true },
      { text: "STIMMT.", at: 39.1 },
    ],
  },
];

/** Große Kinetic-Typo-Zeile — Wörter poppen synchron zum Sprecher. */
const WortZeile: React.FC<{ zeile: Zeile }> = ({ zeile }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fromF = Math.round(zeile.worte[0].at * 25) - 2;
  const outF = Math.round(zeile.out * 25);
  if (frame < fromF || frame > outF + 2) return null;
  const exitOp = interpolate(frame, [outF - 7, outF], [1, 0], CLAMP);
  const scrimOp = interpolate(frame, [fromF, fromF + 8], [0, 0.36], CLAMP) * exitOp;

  // Wörter in Anzeige-Zeilen gruppieren (br = Umbruch VOR dem Wort)
  const rows: Wort[][] = [[]];
  for (const w of zeile.worte) {
    if (w.br && rows[rows.length - 1].length > 0) rows.push([]);
    rows[rows.length - 1].push(w);
  }

  return (
    <>
      {/* Radial-Scrim hinter dem Typo-Block — Lesbarkeit auf hellen Shots */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: scrimOp,
          background:
            "radial-gradient(ellipse 640px 520px at 50% 46%, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.45) 55%, rgba(0,0,0,0) 78%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 60,
          right: 60,
          top: 0,
          height: BASE_H * 0.92,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: Math.round(zeile.size * 0.28),
          opacity: exitOp,
        }}
      >
        {rows.map((row, ri) => (
          <div
            key={ri}
            style={{
              display: "flex",
              gap: Math.round(zeile.size * 0.34),
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            {row.map((w, wi) => {
              const wf = Math.round(w.at * 25) - 2;
              const pop = spring({ frame: frame - wf, fps, config: POP, durationInFrames: 14 });
              return (
                <span
                  key={wi}
                  style={{
                    fontFamily: INTER,
                    fontWeight: 800,
                    fontSize: zeile.size,
                    letterSpacing: 2.5,
                    lineHeight: 1.08,
                    color: w.gold ? GOLD : "rgba(255,255,255,0.97)",
                    opacity: pop,
                    transform: `translateY(${(1 - pop) * 26}px) scale(${0.92 + 0.08 * pop})`,
                    textShadow: w.gold
                      ? "0 2px 30px rgba(0,0,0,0.75), 0 0 46px rgba(255,215,0,0.28)"
                      : "0 2px 30px rgba(0,0,0,0.75)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {w.text}
                </span>
              );
            })}
          </div>
        ))}
      </div>
    </>
  );
};

/** Endcard — Aufbau auf dem gesprochenen „BumbleClean". */
const Endcard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.endIn) return null;
  const t = frame - T.endIn;
  const fadeOut = interpolate(frame, [T.fadeOutStart, T.fadeOutEnd], [1, 0], CLAMP);

  const markeIn = spring({ frame: t - 10, fps, config: SMOOTH, durationInFrames: 18 });
  const subIn = spring({ frame: t - 15, fps, config: SMOOTH, durationInFrames: 18 });
  const claimIn = spring({ frame: frame - T.claimIn, fps, config: SMOOTH, durationInFrames: 18 });
  const buttonIn = spring({ frame: frame - T.buttonIn, fps, config: POP, durationInFrames: 18 });
  const webIn = spring({ frame: frame - T.webIn, fps, config: SMOOTH, durationInFrames: 18 });
  const scrimIn = interpolate(t, [0, 12], [0, 1], CLAMP);

  // Button-Puls: einmal bei ~47,5 s (f1188), dezent
  const puls = 1 + 0.04 * Math.exp(-Math.pow((frame - 1188) / 6, 2));

  return (
    <div style={{ position: "absolute", inset: 0, opacity: fadeOut }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: scrimIn,
          background:
            "radial-gradient(ellipse 620px 620px at 50% 38%, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.3) 55%, rgba(0,0,0,0) 78%)",
        }}
      />

      {/* Waben-Emblem zeichnet sich auf dem gesprochenen Markennamen */}
      <div style={{ position: "absolute", left: BASE_W / 2 - 120, top: 430 }}>
        <WabenEmblemDraw r={40} progressFrame={t} stagger={2} strokeWidth={3} />
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 706,
          textAlign: "center",
          opacity: markeIn,
          transform: `translateY(${(1 - markeIn) * 16}px)`,
          fontFamily: INTER,
          fontWeight: 800,
          fontSize: 62,
          letterSpacing: 10,
          color: "rgba(255,255,255,0.97)",
          textShadow: "0 2px 28px rgba(0,0,0,0.6)",
        }}
      >
        BUMBLE CLEAN
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 790,
          textAlign: "center",
          opacity: subIn,
          fontFamily: INTER,
          fontWeight: 600,
          fontSize: 25,
          letterSpacing: 12,
          color: GOLD,
        }}
      >
        CAR DETAILING
      </div>

      {/* Claim auf der Musik-Auflösung */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 872,
          textAlign: "center",
          opacity: claimIn,
          transform: `translateY(${(1 - claimIn) * 12}px)`,
          fontFamily: INTER,
          fontWeight: 700,
          fontSize: 33,
          letterSpacing: 3,
          color: "rgba(255,255,255,0.94)",
          textShadow: "0 2px 22px rgba(0,0,0,0.7)",
        }}
      >
        SHOWROOM-FINISH. OHNE KOMPROMISSE.
      </div>

      {/* CTA-Button-Look (deckungsgleich mit Meta-Button-Ziel) */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 952,
          display: "flex",
          justifyContent: "center",
          opacity: buttonIn,
          transform: `scale(${(0.9 + 0.1 * buttonIn) * puls})`,
        }}
      >
        <div
          style={{
            background: `linear-gradient(180deg, ${GOLD}, ${GOLD_TIEF})`,
            borderRadius: 16,
            padding: "20px 44px",
            fontFamily: INTER,
            fontWeight: 800,
            fontSize: 34,
            letterSpacing: 2,
            color: "#0e0e0e",
            boxShadow: "0 10px 40px rgba(0,0,0,0.45)",
          }}
        >
          TERMIN BUCHEN&nbsp;→
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 1056,
          textAlign: "center",
          opacity: webIn,
          fontFamily: INTER,
          fontWeight: 600,
          fontSize: 27,
          letterSpacing: 1.5,
          color: "rgba(255,255,255,0.85)",
          textShadow: "0 2px 18px rgba(0,0,0,0.6)",
        }}
      >
        bumble-clean.de · Bad Rappenau
      </div>
    </div>
  );
};

// --- Schema / Defaults / Master ---

export const adZeitSchema = projectPropsSchema.extend({
  videoDatei: z.string().describe("Dateiname des Schnitts (Preview-Unterlage)"),
  zeigeVideo: z
    .boolean()
    .describe("An = Video als Unterlage (nur Preview/Review); Aus = Alpha-Render"),
});
export type AdZeitProps = z.infer<typeof adZeitSchema>;

export const adZeitDefaults: AdZeitProps = {
  format: "portrait" as const, // Video ist nativ 1080×1920
  fps: 25 as const,
  durationInSeconds: 50.2, // 1255 Frames — exakt wie der Schnitt
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  videoDatei: "Cinemtatic Werbeanzeige.mov",
  // Für die Studio-Preview an. ACHTUNG beim Alpha-Render:
  // --props='{"zeigeVideo":false}' setzen, sonst wird das Video eingebrannt!
  zeigeVideo: true,
};

export const BumbleCleanAdZeit: React.FC<AdZeitProps> = ({ videoDatei, zeigeVideo, review }) => {
  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {zeigeVideo && (
          <OffthreadVideo
            src={staticFile(`projects/bumble-clean-cinematic-ad/${videoDatei}`)}
            muted
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        )}
        <Stage>
          {ZEILEN.map((z, i) => (
            <WortZeile key={i} zeile={z} />
          ))}
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
