// ============================================================
// MAN Truck & Bus — Wartezimmervideo Layout-System
// 16:9 (1920×1080), 25fps — Frames mit Alpha-Fenstern für 9:16-Footage,
// Opener, Kapitel-Trenner, Zitat-Inserts (stumme Fassung), Endcard.
// Frames sind 30s-Loops OHNE Entrance (Kapitelwechsel macht der Cutter
// per Blende/Trenner); Ambient-Drift ist sin-basiert und loopt nahtlos.
// Look wie MAN-LagerCTA: dunkel + MAN-Rot, weißes Logo, Condensed-Headlines.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Freeze,
  Img,
  OffthreadVideo,
  Sequence,
  useVideoConfig,
  useCurrentFrame,
  spring,
  interpolate,
  Easing,
  staticFile,
} from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";
import syncPlanJson from "./sync-plan.json";
import { Werkzeuge } from "./Werkzeuge";

const ci = loadBrand("man", brandJson as any);

// --- MAN Global Fonts (TTFs in /public/fonts/man, wie LagerCTA) ---
const MAN_FACES = [
  { family: "MAN Global", weight: 100, file: "MAN_Global-Thin.ttf" },
  { family: "MAN Global", weight: 300, file: "MAN_Global-Light.ttf" },
  { family: "MAN Global", weight: 400, file: "MAN_Global-Regular.ttf" },
  { family: "MAN Global", weight: 500, file: "MAN_Global-Medium.ttf" },
  { family: "MAN Global", weight: 700, file: "MAN_Global-Bold.ttf" },
  { family: "MAN Global Cond", weight: 300, file: "MAN_Global-LightCondensed.ttf" },
  { family: "MAN Global Cond", weight: 400, file: "MAN_Global-RegularCondensed.ttf" },
  { family: "MAN Global Cond", weight: 700, file: "MAN_Global-BoldCondensed.ttf" },
] as const;

if (typeof document !== "undefined") {
  for (const face of MAN_FACES) {
    const style = document.createElement("style");
    style.textContent = `@font-face { font-family: "${face.family}"; font-weight: ${face.weight}; font-display: block; src: url("${staticFile(
      `fonts/man/${face.file}`,
    )}") format("truetype"); }`;
    document.head.appendChild(style);
  }
}

const FONT_TITLE = '"MAN Global Cond", "Arial Narrow", sans-serif';
const FONT_BODY = '"MAN Global", sans-serif';

const MAN_RED = "#E30045";
const VENETIAN = "#720022";
const WHITE = "#FFFFFF";
const BASE = "#12000A";

// Design-Auflösung 1920×1080; Stage wird auf echte Canvas skaliert.
const BASE_W = 1920;
const BASE_H = 1080;

// Fenster exakt 9:16 — der Cutter legt das Hochkant-Footage 1:1 dahinter.
const WIN_W = 540;
const WIN_H = 960;
const WIN_Y = 60;
const WIN_R = 16;

type WinRect = { x: number; y: number; w: number; h: number };
const LAYOUTS: Record<string, { windows: WinRect[]; graphic: { x: number; w: number } }> = {
  solo: {
    windows: [{ x: 140, y: WIN_Y, w: WIN_W, h: WIN_H }],
    graphic: { x: 740, w: 1120 },
  },
  versetzt: {
    windows: [{ x: 1240, y: WIN_Y, w: WIN_W, h: WIN_H }],
    graphic: { x: 60, w: 1120 },
  },
  duo: {
    windows: [
      { x: 150, y: WIN_Y, w: WIN_W, h: WIN_H },
      { x: 1230, y: WIN_Y, w: WIN_W, h: WIN_H },
    ],
    graphic: { x: 690, w: 540 },
  },
};

// --- Helpers ---

const roundedRectPath = (r: WinRect, radius: number) =>
  `M ${r.x + radius} ${r.y}` +
  ` H ${r.x + r.w - radius} Q ${r.x + r.w} ${r.y} ${r.x + r.w} ${r.y + radius}` +
  ` V ${r.y + r.h - radius} Q ${r.x + r.w} ${r.y + r.h} ${r.x + r.w - radius} ${r.y + r.h}` +
  ` H ${r.x + radius} Q ${r.x} ${r.y + r.h} ${r.x} ${r.y + r.h - radius}` +
  ` V ${r.y + radius} Q ${r.x} ${r.y} ${r.x + radius} ${r.y} Z`;

/** Stage skaliert 1920×1080-Design auf echte Canvas-Größe. */
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

/** Nahtlos loopende Phase: k ganze Sinus-Perioden über die Comp-Dauer. */
const useLoopPhase = (k: number) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (2 * Math.PI * k * frame) / durationInFrames;
};

const ManLogo: React.FC<{ width: number; opacity?: number }> = ({ width, opacity = 1 }) => (
  <Img
    src={staticFile("clients/man/logo-weiss.png")}
    style={{ width, opacity }}
  />
);

// =============================================================
// 1) FRAME — Alpha-Panel mit Footage-Fenstern (30s-Loop)
// =============================================================

export const manWzFrameSchema = projectPropsSchema.extend({
  layout: z.enum(["solo", "versetzt", "duo"]).describe("Fenster-Layout"),
});
export type ManWzFrameProps = z.infer<typeof manWzFrameSchema>;

const frameDefaultsBase = {
  format: "landscape" as const,
  fps: 25 as const,
  durationInSeconds: 30,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
};
export const manWzFrameSoloDefaults: ManWzFrameProps = { ...frameDefaultsBase, layout: "solo" };
export const manWzFrameVersetztDefaults: ManWzFrameProps = { ...frameDefaultsBase, layout: "versetzt" };
export const manWzFrameDuoDefaults: ManWzFrameProps = { ...frameDefaultsBase, layout: "duo" };

export const ManWzFrame: React.FC<ManWzFrameProps> = ({ layout, review }) => {
  const { windows, graphic } = LAYOUTS[layout];
  const drift1 = Math.sin(useLoopPhase(1));
  const drift2 = Math.sin(useLoopPhase(2) + 1.3);

  const holes = windows.map((w) => roundedRectPath(w, WIN_R)).join(" ");
  const gx = graphic.x;
  const gw = graphic.w;
  const isDuo = layout === "duo";

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
        <Stage>
          {/* Panel mit ausgestanzten Fenstern (evenodd) */}
          <svg width={BASE_W} height={BASE_H} style={{ position: "absolute" }}>
            <defs>
              <linearGradient id="wzPanel" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor={BASE} />
                <stop offset="55%" stopColor="#1a0410" />
                <stop offset="100%" stopColor="#240614" />
              </linearGradient>
            </defs>
            <path
              d={`M 0 0 H ${BASE_W} V ${BASE_H} H 0 Z ${holes}`}
              fill="url(#wzPanel)"
              fillRule="evenodd"
            />
            {/* Fenster-Rahmen */}
            {windows.map((w, i) => (
              <g key={i}>
                <path
                  d={roundedRectPath(
                    { x: w.x - 3, y: w.y - 3, w: w.w + 6, h: w.h + 6 },
                    WIN_R + 3,
                  )}
                  fill="none"
                  stroke="rgba(255,255,255,0.28)"
                  strokeWidth={2}
                />
                {/* MAN-roter Akzent an der Unterkante */}
                <rect
                  x={w.x + 24}
                  y={w.y + w.h + 8}
                  width={w.w - 48}
                  height={5}
                  rx={2.5}
                  fill={MAN_RED}
                />
              </g>
            ))}
          </svg>

          {/* Grafikfläche: Logo + ruhige Akzente (Wartezimmer = unaufgeregt) */}
          <div
            style={{
              position: "absolute",
              left: gx,
              top: 0,
              width: gw,
              height: BASE_H,
            }}
          >
            {/* Logo */}
            <div
              style={{
                position: "absolute",
                top: isDuo ? 96 : 84,
                left: 0,
                right: 0,
                display: "flex",
                justifyContent: "center",
              }}
            >
              <ManLogo width={isDuo ? 220 : 280} opacity={0.95} />
            </div>

            {/* Vertikale rote Linie mit sanftem Drift */}
            <div
              style={{
                position: "absolute",
                top: isDuo ? 260 : 250,
                left: "50%",
                width: 4,
                height: isDuo ? 480 : 420,
                marginLeft: -2,
                borderRadius: 2,
                background: `linear-gradient(${MAN_RED}, ${VENETIAN})`,
                opacity: 0.85,
                transform: `translateY(${drift1 * 10}px)`,
              }}
            />

            {/* Dezente Punkt-Reihe unten */}
            <div
              style={{
                position: "absolute",
                bottom: 100,
                left: 0,
                right: 0,
                display: "flex",
                justifyContent: "center",
                gap: 18,
                opacity: 0.6 + 0.25 * drift2,
              }}
            >
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: 5,
                    background: i === 1 ? MAN_RED : "rgba(255,255,255,0.5)",
                  }}
                />
              ))}
            </div>
          </div>
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

// =============================================================
// 2) OPENER — „Willkommen bei Ihrem MAN Service" (6s, opak)
// =============================================================

export const manWzOpenerSchema = projectPropsSchema.extend({
  eyebrow: z.string().describe("Zeile über der Headline"),
  headline: z.string().describe("Headline (Condensed, groß)"),
});
export type ManWzOpenerProps = z.infer<typeof manWzOpenerSchema>;

export const manWzOpenerDefaults: ManWzOpenerProps = {
  format: "landscape" as const,
  fps: 25 as const,
  durationInSeconds: 6,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  eyebrow: "Willkommen bei",
  headline: "IHREM MAN SERVICE",
};

const SMOOTH = { damping: 20, stiffness: 100, mass: 1, overshootClamping: true };
const PUNCH = { damping: 16, stiffness: 170, mass: 1 };

export const ManWzOpener: React.FC<ManWzOpenerProps> = ({ eyebrow, headline, review }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sweep = spring({ frame, fps, config: SMOOTH, durationInFrames: 30 });
  const logoIn = spring({ frame: frame - 18, fps, config: PUNCH, durationInFrames: 28 });
  const textIn = spring({ frame: frame - 32, fps, config: SMOOTH, durationInFrames: 30 });
  const lineW = interpolate(frame, [48, 78], [0, 560], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: BASE }}>
        <Stage>
          {/* Diagonale rote Bahn zieht einmal durch */}
          <div
            style={{
              position: "absolute",
              top: -200,
              left: interpolate(sweep, [0, 1], [-2400, 2400]),
              width: 900,
              height: 1500,
              transform: "skewX(-14deg)",
              background: `linear-gradient(90deg, transparent, ${MAN_RED}22, transparent)`,
            }}
          />
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 34,
            }}
          >
            <div style={{ transform: `scale(${logoIn})`, opacity: logoIn }}>
              <ManLogo width={340} />
            </div>
            <div
              style={{
                opacity: textIn,
                transform: `translateY(${(1 - textIn) * 40}px)`,
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontFamily: FONT_BODY,
                  fontWeight: 400,
                  fontSize: 40,
                  color: "rgba(255,255,255,0.85)",
                  marginBottom: 10,
                }}
              >
                {eyebrow}
              </div>
              <div
                style={{
                  fontFamily: FONT_TITLE,
                  fontWeight: 700,
                  fontSize: 128,
                  letterSpacing: 2,
                  color: WHITE,
                  lineHeight: 1.02,
                }}
              >
                {headline}
              </div>
            </div>
            <div
              style={{
                width: lineW,
                height: 6,
                borderRadius: 3,
                background: MAN_RED,
              }}
            />
          </div>
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

// =============================================================
// 3) TRENNER — Kapitelwechsel-Wipe (2.5s, Alpha)
// =============================================================

export const manWzTrennerSchema = projectPropsSchema.extend({
  titel: z.string().describe("Kapitel-Titel"),
});
export type ManWzTrennerProps = z.infer<typeof manWzTrennerSchema>;

export const manWzTrennerDefaults: ManWzTrennerProps = {
  format: "landscape" as const,
  fps: 25 as const,
  durationInSeconds: 2.5,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  titel: "VOLLE KONZENTRATION",
};

export const ManWzTrenner: React.FC<ManWzTrennerProps> = ({ titel, review }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Panel: rein (0–0.5s), voll (0.5–1.7s), raus (1.7–2.5s)
  const inEnd = 0.5 * fps;
  const outStart = durationInFrames - 0.8 * fps;
  const x = interpolate(
    frame,
    [0, inEnd, outStart, durationInFrames],
    [-2300, 0, 0, 2300],
    { easing: Easing.inOut(Easing.cubic), extrapolateRight: "clamp" },
  );
  const textOp = interpolate(
    frame,
    [inEnd - 4, inEnd + 6, outStart - 6, outStart + 4],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
        <Stage>
          <div
            style={{
              position: "absolute",
              top: -160,
              left: x - 200,
              width: BASE_W + 400,
              height: BASE_H + 320,
              transform: "skewX(-8deg)",
              background: `linear-gradient(120deg, ${VENETIAN}, ${MAN_RED})`,
            }}
          />
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              opacity: textOp,
            }}
          >
            <div
              style={{
                fontFamily: FONT_TITLE,
                fontWeight: 700,
                fontSize: 104,
                letterSpacing: 3,
                color: WHITE,
                textAlign: "center",
                padding: "0 140px",
              }}
            >
              {titel}
            </div>
          </div>
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

// =============================================================
// 4) INSERT — Zitat-Karte für die stumme Fassung (Alpha)
// =============================================================

export const manWzInsertSchema = projectPropsSchema.extend({
  zitat: z.string().describe("Zitat (gekürzt, \\n für Umbruch)"),
  person: z.string().describe("Person"),
  rolle: z.string().describe("Rolle/Position"),
});
export type ManWzInsertProps = z.infer<typeof manWzInsertSchema>;

export const manWzInsertDefaults: ManWzInsertProps = {
  format: "landscape" as const,
  fps: 25 as const,
  durationInSeconds: 8,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  zitat: "Nichts passt schon —\nhundert Prozent und nichts anderes.",
  person: "Julia",
  rolle: "Nutzfahrzeugmechatronikerin",
};

export const ManWzInsert: React.FC<ManWzInsertProps> = ({ zitat, person, rolle, review }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const enter = spring({ frame, fps, config: SMOOTH, durationInFrames: 22 });
  const exitOp = interpolate(
    frame,
    [durationInFrames - 14, durationInFrames - 2],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
        <Stage>
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              bottom: 76,
              display: "flex",
              justifyContent: "center",
              opacity: enter * exitOp,
              transform: `translateY(${(1 - enter) * 46}px)`,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "stretch",
                gap: 0,
                maxWidth: 1480,
                background: "rgba(18,0,10,0.85)",
                borderRadius: 14,
                overflow: "hidden",
                boxShadow: "0 10px 40px rgba(0,0,0,0.45)",
              }}
            >
              <div style={{ width: 10, background: MAN_RED }} />
              <div style={{ padding: "30px 44px 26px 38px" }}>
                <div
                  style={{
                    fontFamily: FONT_BODY,
                    fontWeight: 500,
                    fontSize: 42,
                    lineHeight: 1.3,
                    color: WHITE,
                    whiteSpace: "pre-line",
                  }}
                >
                  „{zitat}“
                </div>
                <div
                  style={{
                    marginTop: 14,
                    fontFamily: FONT_BODY,
                    fontWeight: 400,
                    fontSize: 27,
                    color: "rgba(255,255,255,0.75)",
                  }}
                >
                  <span style={{ color: MAN_RED, fontWeight: 700 }}>{person}</span>
                  {"  ·  "}
                  {rolle}
                </div>
              </div>
            </div>
          </div>
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

// =============================================================
// 5) ENDCARD — Abbinder, blendet dunkel aus (Loop → Opener) (6s)
// =============================================================

export const manWzEndcardSchema = projectPropsSchema.extend({
  claim: z.string().describe("Abbinder-Zeile"),
});
export type ManWzEndcardProps = z.infer<typeof manWzEndcardSchema>;

export const manWzEndcardDefaults: ManWzEndcardProps = {
  format: "landscape" as const,
  fps: 25 as const,
  durationInSeconds: 6,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  claim: "Ihr MAN Service-Team",
};

export const ManWzEndcard: React.FC<ManWzEndcardProps> = ({ claim, review }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const logoIn = spring({ frame, fps, config: PUNCH, durationInFrames: 26 });
  const textIn = spring({ frame: frame - 14, fps, config: SMOOTH, durationInFrames: 26 });
  // Letzte Sekunde: Inhalt weich raus → endet auf dunkler Fläche wie Opener-Start
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 1 * fps, durationInFrames - 6],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: BASE }}>
        <Stage>
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 30,
              opacity: fadeOut,
            }}
          >
            <div style={{ transform: `scale(${logoIn})`, opacity: logoIn }}>
              <ManLogo width={320} />
            </div>
            <div
              style={{
                opacity: textIn,
                transform: `translateY(${(1 - textIn) * 30}px)`,
                fontFamily: FONT_BODY,
                fontWeight: 500,
                fontSize: 46,
                color: "rgba(255,255,255,0.92)",
              }}
            >
              {claim}
            </div>
            <div
              style={{
                width: 420 * textIn,
                height: 5,
                borderRadius: 2.5,
                background: MAN_RED,
              }}
            />
          </div>
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

// =============================================================
// 6) 16:9-MASTER — ManWz169Master (sync-plan-getrieben)
// Umbau 2026-07-24 (Davids Entscheidungen) + REVIEW 2 (12 Punkte, nachts)
// + REVIEW 3 (2026-07-25, 4 Restbefunde):
//   Nr. 1 EIN fester Takeaway-Grad 54 px (eine Ausnahmestufe 46 px),
//   Nr. 2 Plaketten-Hierarchie Name 58 / Rolle 30 px bei 80 % Weiß,
//   Nr. 3 Musik-Hit 76,0 s trägt jetzt Luminanz (helles MAN-Rot statt Vollton,
//         Wash mit sichtbaren Flanken neben dem Fenster),
//   Nr. 4 Fenster 540×960 vertikal zentriert (y=60) — Schatten läuft rundum aus.
// Fenster FEST rechts (x=1200, Rand 180), Grafikfläche links 64–1100.
// Layout-Spalte durchgehend bündig bei x=64 (Nr. 4): Logo links oben
// (200 px), darunter viel Luft, Kapitel-Headline ab y 352 (92 px / 80 px
// zweizeilig), Takeaway im Fluss darunter (Nr. 12: 56/52/48 px), Plakette
// y 824 — alles auf der Grafikfläche, kein Pixel über dem Video.
// KEINE beat-getriebene Text-Bewegung mehr (Nr. 2: typo-akzent/zeilen-shift
// ersatzlos raus; nur noch licht-akzent auf Licht-Opazität).
// Spotlights (9,5–22,3 / 64,6–89,9): Fenster gleitet zur Mitte (x→672,
// ×1,04), Abdunkelung + Vignette, roter Glow, Lichtstreifen (Flare 76,0),
// subtiler Werkzeug-Regen (Nr. 10) und roter Vektor-Löwe, dessen linke
// Kante mit dem Kopf IMMER frei rechts der Fenster-Einheit steht (Nr. 1).
// Spotlights sind text- UND logofrei (Nr. 9 — Branding-Beat entfernt).
// Fenster-Schatten weich/zweistufig statt hart (Nr. 11).
// Endcard (Nr. 7): Fenster blendet 134,0–134,6 KOMPLETT aus, danach
// Fullscreen-Endscreen 135,0–140,0, Ausklang in die Dunkelfläche bis
// 142,0 — Frame 3549 ≙ Frame 0 (Fenster-Fade-in 0,0–0,5 s).
// =============================================================

// --- sync-plan Typen (Struktur aus build_sync_plan.py, Stand 2026-07-24) ---
interface PlakettePlan169 {
  block: number;
  person: string; // nur Vorname (David Nr. 1)
  personVoll?: string;
  rolle: string;
  eintritt: { start: number; dauer: number; art: string };
  austritt: { start: number; dauer: number };
  frameVon: number;
  frameBis: number;
  ciattei: boolean;
}
interface TakeawayPlan169 {
  block: number;
  person: string;
  zeilen: string[];
  groessePx?: number;
  start: number;
  endeTon: number;
  endeStumm: number;
  austritt: { start: number; dauer: number };
  revealDauer: number;
  frameVon: number;
  frameBisTon: number;
  frameBisStumm: number;
  ciattei: boolean;
}
interface HeadlinePlan169 {
  id: string;
  kapitel: number;
  zeilen: string[];
  groessePx?: number;
  start: number;
  ende: number;
  einDauer: number;
  exitDauer: number;
  frameVon: number;
  frameBis: number;
}
interface SpotlightPlan169 {
  id: string;
  start: number;
  ende: number;
  frameVon: number;
  frameBis: number;
  textfrei?: boolean;
  logofrei?: boolean;
  beats: { typ: string; start: number; ende?: number; frame: number }[];
  werkzeugRegen?: {
    aktiv: boolean;
    opazitaet: [number, number] | number[];
    fallzeitSek: [number, number] | number[];
  };
}
interface BrandingPlan169 {
  aktiv?: boolean;
  start: number;
  ende: number;
  frameVon: number;
  frameBis: number;
  eyebrow: string;
  zeilen: string[];
}
interface EndcardEvent169 {
  typ: string; // "freeze" | "fenster-aus" | "hero" | "ausklang"
  start: number;
  ende: number;
  frame: number;
  fullscreen?: boolean;
  kartentext?: string;
  loewe?: { variante: string; drift?: boolean };
}
interface SyncPlan169 {
  meta: {
    fps: number;
    masterDauer: number;
    masterFrames: number;
    videoFrames: number;
    freezeBis: number;
    endcardStart: number;
    fensterAusEnde: number;
  };
  fenster: {
    x: number;
    y: number;
    breite: number;
    hoehe: number;
    einblendung: { start: number; dauer: number };
    ausblendung: { start: number; dauer: number };
    schatten: {
      stufe1: { blur: number; y: number; deckkraft: number };
      stufe2: { blur: number; y: number; deckkraft: number };
    };
  };
  plaketten: PlakettePlan169[];
  takeaways: TakeawayPlan169[];
  headlines: HeadlinePlan169[];
  spotlights: SpotlightPlan169[];
  branding: BrandingPlan169;
  dichte: { t: number; amp: number; phase: string }[];
  endcard: EndcardEvent169[];
  zwischenBeats: { start: number; dauer: number; typ: string; frame: number }[];
}

const PLAN169 = syncPlanJson as unknown as SyncPlan169;

// --- Geometrie (Design 1920×1080; David Nr. 8) ---
const ANTHRAZIT = "#2E3A46"; // Bühne
const ANTHRAZIT_TIEF = "#222C36"; // Versatz-Panel / Plakette
const SPOT_DUNKEL = "#171E26"; // Abdunkelung im Spotlight
// Fenster-Geometrie (Review 3 Nr. 4): vorher 576×1024 bei y=28 — oben/unten
// blieben nur 28 px, der weiche Schatten (Blur 220, y-Versatz 60) reichte
// rechnerisch 170 px über die Unterkante hinaus und wurde an der Canvas-Kante
// hart abgeschnitten. Jetzt 540×960 (9:16 exakt: 540·16 = 960·9 = 8640),
// VERTIKAL ZENTRIERT bei y=60 → rundum 60 px Luft; der Schatten (Stufe 2:
// Blur 120, y-Versatz 0 ⇒ Reichweite 60 px) läuft auf allen vier Seiten
// vollständig aus. Rechter Rand bleibt 180 px ⇒ x = 1920 − 180 − 540 = 1200.
const M_WIN_W = 540;
const M_WIN_H = 960;
const M_WIN_X = 1200; // FEST rechts (Rand rechts 180) — kein Travel mehr
const M_WIN_Y = 60; // vertikal zentriert: (1080 − 960) / 2
const M_WIN_X_SPOT = 690; // Bildmitte im Spotlight (960 − 540/2)
const M_SPOT_SCALE = 1.04;
const M_SPOT_GLIDE = 1.3; // Glide-Dauer (Easing.inOut(cubic))
const M_SPOT_RAND = 0.3; // Rückkehr endet ende−0,3 s (22,0 / 89,6)
const M_GRAF_X = 64; // Grafikfläche links 64–1100
const M_GRAF_W = 1036;
const M_FPS = 25;

// --- Layout-Raster links (Review 2 Nr. 4 + 12) -------------------------------
// EINE bündige Spalte ab x=64 (= linke Kante der Grafikfläche, 10 px innerhalb
// der 5-%-Safe-Zone von 54 px): Logo → Headline → Takeaway → Plakette.
// Vorher: Logo zentriert bei y 64, Headline y 260, Takeaway y 470 — David:
// „zu eng, überladen". Jetzt großzügige, konstante Abstände.
const M_TEXT_X = M_GRAF_X; // linke Textkante = Logokante (bündige Spalte)
const M_TEXT_W = M_GRAF_W - 36; // 1000 px → rechte Kante 1064, 100 px vor dem Fenster
const M_LOGO_Y = 72; // Logo-Oberkante
const M_LOGO_W = 200; // 200×115 (Seitenverhältnis 4167:2399) → Unterkante ≈ 187
const M_HEAD_Y = 352; // Headline-Oberkante (Review: „Richtung 340–380")
const M_HEAD_LH = 1.08; // Zeilenhöhe Headline
const M_HEAD_PX_1 = 92; // einzeilige Headline
const M_HEAD_PX_2 = 80; // zweizeilig (K1 „QUALITÄT OHNE/KOMPROMISSE", K3 „FASZINATION/NUTZFAHRZEUG")
const M_HEAD_GAP = 96; // Luft Headline-Unterkante → Takeaway-Oberkante
const M_TAKE_LH = 1.12; // Zeilenhöhe Takeaway
const M_TAKE_ZEILEN_GAP = 6;
// Review 3 Nr. 1: EIN fester Takeaway-Grad für alle 12 Blöcke. Vorher gab es
// drei Stufen (56 einzeilig / 52 zweizeilig / 48 im „engen" Fall) — gemessen
// sprang die Versalhöhe dadurch von 42 px (Block 1) auf 38–40 px (Blöcke 4/5/9),
// der Satz wirkte unruhig. Jetzt: 54 px für ALLE. Es gibt genau EINE
// Ausnahmestufe (46 px), die der Generator setzt, wenn eine Zeile breiter als
// die Spalte wäre — kein stufenloses Auto-Fit mehr.
const M_TAKE_PX = 54; // fester Grad für ALLE Takeaways
const M_TAKE_PX_AUSNAHME = 46; // EINZIGE Ausnahmestufe (vom Generator gesetzt)
// nutzbare Textbreite: Spalte 1000 px minus roter Balken (8) und Gap (28)
const M_TAKE_MAX_W = M_TEXT_W - 8 - 28; // = 964 px, rechte Kante 1064 < 1100
const M_PLAK_Y = 824; // Plaketten-Oberkante (unverändert)
// Plaketten-Hierarchie (Review 3 Nr. 2): Name dominiert, Rolle tritt zurück.
const M_PLAK_NAME_PX = 58;
const M_PLAK_NAME_LH = 1.05;
const M_PLAK_ROLLE_PX = 30;
const M_PLAK_ROLLE_LH = 1.15;
const M_PLAK_GAP = 6;
// 58·1,05 + 6 + 30·1,15 = 101,4 → +2×15,3 Innenabstand = 132 (Unterkante 956)
const M_PLAK_H = Math.round(
  M_PLAK_NAME_PX * M_PLAK_NAME_LH + M_PLAK_GAP + M_PLAK_ROLLE_PX * M_PLAK_ROLLE_LH + 30,
);

/** Headline-Grad je Zeilenzahl (zweizeilig kleiner → Kapitel 3 wirkt nicht überladen). */
const headPx169 = (zeilen: number, plan?: number) =>
  zeilen >= 2 ? M_HEAD_PX_2 : (plan ?? M_HEAD_PX_1);

/** Headline-Blockhöhe (für den Fluss zum Takeaway). */
const headBlockH169 = (zeilen: number, plan?: number) =>
  zeilen * headPx169(zeilen, plan) * M_HEAD_LH;

/** Takeaway-Oberkante: fließt unter der Headline des laufenden Kapitels. */
const takeY169 = (headZeilen: number, headPlanPx?: number) =>
  Math.round(M_HEAD_Y + headBlockH169(headZeilen, headPlanPx) + M_HEAD_GAP);

/** Kapitel-Headline, unter der ein Element zur Zeit tSec steht.
 *  Liefert Zeilenzahl + geplanten Grad — daraus ergeben sich Takeaway-
 *  Oberkante und -Schriftgrad. Fallback: einzeilig (K2/K4-Fall). */
const kapitelKopf169 = (tSec: number): { zeilen: number; px?: number } => {
  for (const h of PLAN169.headlines) {
    if (tSec >= h.start && tSec <= h.ende) {
      return { zeilen: h.zeilen.length, px: h.groessePx };
    }
  }
  return { zeilen: 1 };
};

const fr169 = (sec: number) => Math.round(sec * M_FPS);
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const easeGlide = Easing.inOut(Easing.cubic);

/** Spotlight-Hüllkurve 0..1: Glide rein ab start, Rückkehr endet ende−0,3 —
 *  treibt Fenster-Position/-Scale UND die komplette Ambience (Abdunkelung,
 *  Vignette, Glow, Streifen, Drift-Löwe, Logo-Ausblendung). */
const spotEnvAt169 = (tSec: number): number => {
  for (const s of PLAN169.spotlights) {
    const rueckEnde = s.ende - M_SPOT_RAND;
    const rueckStart = rueckEnde - M_SPOT_GLIDE;
    if (tSec < s.start || tSec > rueckEnde) continue;
    if (tSec < s.start + M_SPOT_GLIDE) return easeGlide((tSec - s.start) / M_SPOT_GLIDE);
    if (tSec > rueckStart) return easeGlide((rueckEnde - tSec) / M_SPOT_GLIDE);
    return 1;
  }
  return 0;
};

/** Flare-Hüllkurve (Musik-Hit 76,0): Streifen-Opazität ~3× + Glow-Boost,
 *  ~0,5 s weich rein/raus, Peak EXAKT auf dem Hit (Hüllkurve zentriert —
 *  vorher startete sie erst am Hit und war auf dem Hit-Frame unsichtbar). */
const flareAt169 = (tSec: number): number => {
  let v = 0;
  for (const s of PLAN169.spotlights) {
    for (const b of s.beats ?? []) {
      if (b.typ !== "flare") continue;
      const p = (tSec - b.start + 0.25) / 0.5;
      if (p > 0 && p < 1) v = Math.max(v, Math.sin(Math.PI * p));
    }
  }
  return v;
};

/** Dichte-Stufen als Amplituden-Hüllkurve (Ambient). */
const ampAt169 = (tSec: number): number =>
  interpolate(
    tSec,
    PLAN169.dichte.map((d) => d.t),
    PLAN169.dichte.map((d) => d.amp),
    CLAMP,
  );

/** Zwischen-Beat-Hüllkurve (0..1) für einen Beat-Typ zur Zeit tSec. */
const beatEnvAt169 = (tSec: number, typ: string): number => {
  let v = 0;
  for (const b of PLAN169.zwischenBeats) {
    if (b.typ !== typ) continue;
    const p = (tSec - b.start) / b.dauer;
    if (p > 0 && p < 1) v = Math.max(v, Math.sin(Math.PI * p));
  }
  return v;
};

/** **wort**-Markup → Schlüsselwort in MAN-Rot. */
const Markup169: React.FC<{ text: string }> = ({ text }) => (
  <>
    {text.split("**").map((seg, i) =>
      i % 2 === 1 ? (
        <span key={i} style={{ color: MAN_RED }}>
          {seg}
        </span>
      ) : (
        <React.Fragment key={i}>{seg}</React.Fragment>
      ),
    )}
  </>
);

// --- Vektor-Löwen (Phase 1, David Nr. 7) ---
// PNGs 1200×2400 mit großem Transparenz-Rand; sichtbare Silhouette
// (Alpha-BBox) 199–1094 × 506–1895, Kopf mit offenem Maul oben LINKS —
// alle loewe-links-Varianten blicken nach links = zur Bildmitte, wenn
// rechts platziert (David Nr. 3). Platzierung daher über die SICHTBARE
// Box (visX/visY/visH), nicht über die PNG-Leinwand.
const LION_VIS = { left: 199 / 1200, top: 506 / 2400, w: 895 / 1200, h: 1389 / 2400 };

const Loewe169: React.FC<{
  variante: "dunkel" | "rot" | "weiss";
  visX: number; // Canvas-x der sichtbaren linken Silhouetten-Kante
  visY: number; // Canvas-y der sichtbaren Oberkante
  visH: number; // sichtbare Silhouetten-Höhe
  shiftX?: number;
  opacity?: number;
  filter?: string; // z. B. "brightness(0.82)" für tieferes Rot
}> = ({ variante, visX, visY, visH, shiftX = 0, opacity = 1, filter }) => {
  const imgH = visH / LION_VIS.h;
  const imgW = imgH * 0.5; // PNG-Leinwand 1200×2400
  return (
    <Img
      src={staticFile(`clients/man/wz/loewe-links-${variante}.png`)}
      style={{
        position: "absolute",
        width: imgW,
        height: imgH,
        left: visX - imgW * LION_VIS.left,
        top: visY - imgH * LION_VIS.top,
        transform: `translateX(${shiftX}px)`,
        opacity,
        filter,
      }}
    />
  );
};

/** Kapitel-Headline (David Nr. 6): steht dauerhaft, Wechsel per Fade.
 *  Review 2 Nr. 2 (v4): ÜBERHAUPT KEINE X-Bewegung mehr an Text — der letzte
 *  translateX beim Headline-Wechsel ist raus. Eintritt = Fade + 12 px von
 *  unten, Austritt = reiner Fade (keinerlei Seitwärtsbewegung).
 *  Review 2 Nr. 4/12: y 352 statt 260, zweizeilig 80 px statt 92 px. */
const Headline169: React.FC<{ h: HeadlinePlan169 }> = ({ h }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = Math.max(8, h.frameBis - h.frameVon);
  const einF = Math.max(2, Math.round(h.einDauer * fps));
  const exitF = Math.max(2, Math.round(h.exitDauer * fps));
  const ein = interpolate(frame, [0, einF], [0, 1], {
    ...CLAMP,
    easing: Easing.out(Easing.cubic),
  });
  const aus = interpolate(frame, [total - exitF, total - 1], [1, 0], {
    ...CLAMP,
    easing: Easing.in(Easing.cubic),
  });
  const px = headPx169(h.zeilen.length, h.groessePx);
  return (
    <div
      style={{
        position: "absolute",
        left: M_TEXT_X,
        top: M_HEAD_Y,
        width: M_TEXT_W,
        opacity: ein * aus,
        transform: `translateY(${(1 - ein) * 12}px)`,
      }}
    >
      {h.zeilen.map((z, i) => (
        <div
          key={i}
          style={{
            fontFamily: FONT_TITLE,
            fontWeight: 700,
            fontSize: px,
            letterSpacing: 2,
            lineHeight: M_HEAD_LH,
            color: WHITE,
            textTransform: "uppercase",
          }}
        >
          <Markup169 text={z} />
        </div>
      ))}
    </div>
  );
};

/** Takeaway-Zeilen: roter Balken, Zeilen-Reveal (Maskenfahrt, kein X-Versatz).
 *  Review 3 Nr. 1: EIN fester Schriftgrad (54 px) für alle 12 Takeaways —
 *  die alte Dreistufigkeit 56/52/48 ist raus. Der Grad kommt fertig aus dem
 *  sync-plan (`groessePx`); der Generator vergibt 54 px und schaltet nur dann
 *  auf die EINE Ausnahmestufe 46 px, wenn eine Zeile in MAN Global Bold
 *  Condensed breiter als 964 px würde (nachgemessen: breiteste Zeile ist
 *  Block 7 „ARBEIT, DIE WACHSEN LÄSST" mit 656 px — KEIN Takeaway braucht
 *  die Ausnahme). Hier findet kein Auto-Fit statt.
 *  Oberkante fließt weiterhin unter der Headline: y 547 (einzeilige Headline)
 *  bzw. y 621 (zweizeilige Headline) — konstante 96 px Luft nach oben.
 *  Review 2 Nr. 2: kein beat-getriebener shiftX mehr. */
const Takeaway169: React.FC<{
  tw: TakeawayPlan169;
  stumm: boolean;
  headZeilen: number;
  headPlanPx?: number;
}> = ({ tw, stumm, headZeilen, headPlanPx }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bis = stumm ? tw.frameBisStumm : tw.frameBisTon;
  const total = Math.max(12, bis - tw.frameVon);
  const exitF = Math.max(2, Math.round((tw.austritt?.dauer ?? 0.4) * fps));
  const exit = interpolate(frame, [total - exitF, total - 1], [1, 0], CLAMP);
  const revealF = Math.max(4, Math.round(tw.revealDauer * fps));
  // Fester Grad aus dem Plan; nur 54 oder 46 sind zulässige Werte.
  const px = tw.groessePx === M_TAKE_PX_AUSNAHME ? M_TAKE_PX_AUSNAHME : M_TAKE_PX;
  return (
    <div
      style={{
        position: "absolute",
        left: M_TEXT_X,
        top: takeY169(headZeilen, headPlanPx),
        width: M_TEXT_W,
        display: "flex",
        alignItems: "stretch",
        gap: 28,
        opacity: exit,
      }}
    >
      <div style={{ width: 8, background: MAN_RED }} />
      {/* maxWidth = harte Spaltengrenze (964 px ⇒ rechte Kante 1064): reines
          Sicherheitsnetz, greift bei keinem der 12 Texte. */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: M_TAKE_ZEILEN_GAP,
          maxWidth: M_TAKE_MAX_W,
        }}
      >
        {tw.zeilen.map((z, i) => {
          const rv = spring({
            frame: frame - Math.round(i * 0.15 * fps),
            fps,
            config: SMOOTH,
            durationInFrames: revealF,
          });
          return (
            <div key={i} style={{ overflow: "hidden" }}>
              <div
                style={{
                  fontFamily: FONT_TITLE,
                  fontWeight: 700,
                  fontSize: px,
                  letterSpacing: 1,
                  lineHeight: M_TAKE_LH,
                  color: WHITE,
                  textTransform: "uppercase",
                  transform: `translateY(${(1 - rv) * 105}%)`,
                }}
              >
                <Markup169 text={z} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/** Sprecher-Plakette (y 824): nur Vorname + Rolle, komplett auf der
 *  Grafikfläche — kein Pixel über dem Video (David Nr. 1+2).
 *  Review 2 Nr. 6: Ein-/Austritt kommen sequenziell aus dem sync-plan
 *  (Pause ≥ 0,8 s); `exit` erreicht auf dem LETZTEN Sequence-Frame exakt 0,
 *  die nächste Plakette startet frühestens 20 Frames später → nie zwei
 *  gleichzeitig sichtbar, auch nicht für einen Frame.
 *  Review 2 Nr. 5: `rolle` kommt fest per Vorname aus dem Generator.
 *  Review 3 Nr. 2: Die Hierarchie war zu flach — Name 44 px Cond Bold
 *  (Versalhöhe 32–34 px) gegen Rolle 34 px Regular bei 92 % Weiß (≈26 px)
 *  las sich auf Distanz als „zwei gleich große Zeilen". Jetzt Name 58 px
 *  Cond Bold (Versalhöhe ≈ 42 px) gegen Rolle 30 px Regular bei 80 % Weiß
 *  (≈21 px): Größenverhältnis 1,93 : 1 statt 1,29 : 1, dazu deutlich
 *  geringerer Helligkeitswert der Rolle. Kastenhöhe 120 → 132 px
 *  (58·1,05 + 6 + 30·1,15 = 101,4 + 2×15,3 Innenabstand), Unterkante 956.
 *  Breitester Kasten (Louis/Lara/Hannes) = 508 px ⇒ rechte Kante 572,
 *  weit innerhalb der Grafikfläche (Fenster-Kantenbalken beginnt bei 1192). */
const Plakette169: React.FC<{ p: PlakettePlan169 }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = p.frameBis - p.frameVon;
  const enterF = Math.max(2, Math.round(p.eintritt.dauer * fps));
  const exitF = Math.max(2, Math.round(p.austritt.dauer * fps));
  const enter = spring({ frame, fps, config: SMOOTH, durationInFrames: enterF });
  const exit = interpolate(frame, [total - exitF, total - 1], [1, 0], CLAMP);
  return (
    <div
      style={{
        position: "absolute",
        top: M_PLAK_Y,
        left: M_TEXT_X,
        height: M_PLAK_H,
        display: "flex",
        alignItems: "stretch",
        background: "rgba(34,44,54,0.92)",
        borderRadius: 0,
        opacity: enter * exit,
        transform: `translateY(${(1 - enter) * 16}px)`,
      }}
    >
      <div style={{ width: 8, background: MAN_RED }} />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "0 36px",
          gap: M_PLAK_GAP,
        }}
      >
        <div
          style={{
            fontFamily: FONT_TITLE,
            fontWeight: 700,
            fontSize: M_PLAK_NAME_PX,
            letterSpacing: 1.5,
            lineHeight: M_PLAK_NAME_LH,
            color: WHITE,
            textTransform: "uppercase",
            whiteSpace: "nowrap",
          }}
        >
          {p.person.split(" ")[0]}
        </div>
        <div
          style={{
            fontFamily: FONT_BODY,
            fontWeight: 400,
            fontSize: M_PLAK_ROLLE_PX,
            letterSpacing: 0.3,
            lineHeight: M_PLAK_ROLLE_LH,
            color: "rgba(255,255,255,0.8)",
            whiteSpace: "nowrap",
          }}
        >
          {p.rolle}
        </div>
      </div>
    </div>
  );
};

// --- Spotlight-Ambience (Referenz: MAN-„Individual Lion S"-Kampagne) ---
// 4 vertikale Lichtstreifen, verschiedene Breiten, weiß + rot, stark
// weichgezeichnet, Zeitlupen-Drift; Opazität 0,06–0,18.
// Flare-Licht (Review 3 Nr. 3): helles MAN-Rot statt Vollton — Luminanz 129
// gegen ~33 Grundhelligkeit, Sättigung bleibt hoch (kein Weißblitz).
const FLARE_LICHT = "#FF5C82";
const SPOT_STREIFEN = [
  { x0: 240, v: 34, w: 120, farbe: WHITE, op: 0.1 },
  { x0: 620, v: -26, w: 56, farbe: MAN_RED, op: 0.16 },
  { x0: 1240, v: 20, w: 90, farbe: WHITE, op: 0.06 },
  { x0: 1600, v: -38, w: 40, farbe: MAN_RED, op: 0.18 },
];

// Spotlight-Löwe (Review 2 Nr. 1): Basis-x bei voller Hüllkurve, Weg-Zuschlag
// solange das Fenster noch rechts steht, symmetrische Drift-Amplitude.
// Review 3 Nr. 4: mit 540×960 endet das Versatz-Panel im Spotlight bei
// 960 + (24 + 540 − 270)·1,04 ≈ 1266, mit Panel-Blur (26 px) ≈ 1292.
const M_SPOT_LOEWE_X = 1380; // env=1 → sichtbare Kante 1350…1410 ⇒ ≥ 58 px Luft
const M_SPOT_LOEWE_WEG = 420; // env=0 → 1800 (Panel-Rechtskante dann 1764 + Blur)
const M_SPOT_LOEWE_DRIFT = 30; // ± Drift über die Spotlight-Dauer

// Werkzeug-Regen: der Plan schreibt die Zone „Grafikfläche links (x 0–1100)"
// vor. `breite` staucht die (deterministische) Instanz-Tabelle aus
// Werkzeuge.tsx genau in dieses Fenster — so bleibt die rechte Bildhälfte mit
// dem Löwen frei und die Teile fallen nur hinter Grafikfläche und Fenster.
const M_WERKZEUG_ZONE_W = 1100;

const Spotlight169: React.FC<{ s: SpotlightPlan169 }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tLok = frame / fps;
  const tAbs = s.start + tLok;
  const env = spotEnvAt169(tAbs);
  if (env <= 0.001) return null;
  const licht = beatEnvAt169(tAbs, "licht-akzent");
  // Review 3 Nr. 3: Der Flare hängt NICHT mehr an dieser Grund-Opazität —
  // er bekommt eigene Ebenen (siehe unten). Hier nur noch der Licht-Akzent.
  const streifenMul = 1 + 0.9 * licht;
  const dauer = s.ende - s.start;
  // Werkzeug-Deckkraft aus dem Plan (Korridor 0,04–0,09 → Mitte 0,065)
  const wz = s.werkzeugRegen;
  const werkzeugOp =
    wz?.aktiv === false
      ? 0
      : ((wz?.opazitaet?.[0] ?? 0.04) + (wz?.opazitaet?.[1] ?? 0.09)) / 2;
  return (
    <>
      {/* Abdunkelung Richtung #171E26 */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: SPOT_DUNKEL,
          opacity: 0.78 * env,
        }}
      />
      {/* weiche Vignette */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(11,17,23,0) 42%, rgba(11,17,23,0.6) 100%)",
          opacity: env,
        }}
      />
      {/* Lichtstreifen in Zeitlupe (Flare am Musik-Hit, Licht-Akzente) */}
      {SPOT_STREIFEN.map((st, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: st.x0 + st.v * tLok,
            top: -140,
            width: st.w,
            height: BASE_H + 280,
            background: st.farbe,
            filter: "blur(46px)",
            opacity: Math.min(0.35, st.op * streifenMul) * env,
          }}
        />
      ))}
      {/* tiefroter Glow steigt hinter dem Fenster auf */}
      <div
        style={{
          position: "absolute",
          left: 960 - 800,
          top: 540 - 800,
          width: 1600,
          height: 1600,
          background:
            "radial-gradient(circle, rgba(227,0,69,0.32) 0%, rgba(227,0,69,0) 62%)",
          opacity: env,
        }}
      />
      {/* MUSIK-HIT 76,0 s: ENTFERNT (David 2026-07-25 — „blitzt der Hintergrund
          kurz auf, das bitte entfernen"). Die Spotlights laufen jetzt
          durchgehend gleichmäßig; der Aktwechsel der Musik trägt den Moment
          allein, ohne visuellen Akzent. Der Plan-Eintrag vom Typ „flare" bleibt
          als Dokumentation im sync-plan, wird aber nicht mehr gerendert. */}
      {/* Werkzeug-Regen (Review 2 Nr. 10): sehr langsam herabsinkende
          Silhouetten, Deckkraft 4–9 %, weich mit der Spotlight-Hüllkurve
          ein-/ausgeblendet. Liegt IM Spotlight-Layer, also im z-Stack unter
          der Fenster-Einheit. Deterministisch (feste Instanz-Tabelle in
          Werkzeuge.tsx), `zyklen = dauer/26` hält das Tempo in beiden
          Spotlights identisch; am Wrap-Punkt ist jedes Teil ausgeblendet
          UND außerhalb des Bildes → kein Loop-Sprung. */}
      <Werkzeuge
        progress={tLok / dauer}
        opacity={werkzeugOp * env}
        farbe={WHITE}
        zyklen={dauer / 26}
        breite={M_WERKZEUG_ZONE_W}
        hoehe={BASE_H}
      />
      {/* Roter Vektor-Löwe: EDEL zurückgenommen (Kalibrierung 2026-07-24,
          David: „subtil dahinter", vorher wirkte er als aufgeklebter Sticker).
          — kein volles #E30045 mehr: 24 % Deckkraft auf dem abgedunkelten
            Grund (≈ #44172D, tiefes Dunkelrot), am Flare 76,0 kurz max 44 %;
          — REVIEW 2 Nr. 1: die LINKE Kante mit dem Kopf darf nie angeschnitten
            werden. Vorher stand visX=1195 hinter der Fenster-Einheit (deren
            rechte Panel-Kante im Spotlight bei ≈ 1280 liegt) → Kopf halb
            verdeckt. Jetzt wandert der Löwe mit der Fenster-Hüllkurve:
            visX = 1330 bei env=1 (20 px rechts der Panel-Kante 1280 + 30 px
            Drift-Reserve), und schiebt sich bei kleinerem env um bis zu
            470 px nach rechts, weil das Fenster dann noch weiter rechts steht
            (Panel-Rechtskante ≈ 1760 − 480·env). Mit shiftX ∈ [−30, +30]
            bleibt die sichtbare Silhouetten-Kante IMMER ≥ 1300 — Kopf/Maul
            (linke 55 % der Breite) stehen jederzeit frei. Rechts läuft er
            bewusst aus dem Bild (Silhouette ≈ 760 px breit ⇒ bis x ≈ 2060);
          — Größe bewusst NICHT hochgezogen: bei visH ≫ 1200 wird der Kopf
            oben angeschnitten und die Silhouette kippt in eine amorphe
            Masse, die das Bild dominiert. visH 1180 hält Kopf/Maul komplett
            im Bild, unten leichter Anschnitt;
          — blur(3px): nimmt die harte Vektorkante raus, der Löwe liest als
            unscharfe Tiefen-Ebene HINTER dem Fenster statt als Aufkleber. */}
      <Loewe169
        variante="rot"
        visX={M_SPOT_LOEWE_X + (1 - env) * M_SPOT_LOEWE_WEG}
        visY={20}
        visH={1180}
        shiftX={-M_SPOT_LOEWE_DRIFT + 2 * M_SPOT_LOEWE_DRIFT * (tLok / dauer)}
        opacity={0.24 * env}
        filter="brightness(0.82) blur(3px)"
      />
    </>
  );
};

// Review 2 Nr. 9: Der Branding-Beat („WILLKOMMEN BEI IHREM MAN SERVICE" +
// großes Logo, vormals 13,0–17,0 in Spotlight 1) ist ERSATZLOS entfernt.
// Beide Spotlights sind vollständig text- UND logofrei — auch das Zone-A-Logo
// blendet dort aus. Der Generator liefert `branding.aktiv = false` als Stub.

// --- Endcard-Hero: FULLSCREEN (Review 2 Nr. 7) -------------------------------
// Ab 134,6 s existiert kein Fenster mehr (kein Rahmen, kein Kantenbalken, kein
// Versatz-Panel, kein Schatten). Der Endscreen bespielt die ganze 1920×1080-
// Fläche: bündige Spalte links bei x=160 (Logo → Claim → roter Balken), Löwe
// WEISS rechts. Kein CTA (Guardrail 4). Der Löwe hält die Regel aus Nr. 1 ein:
// linke Kante mit Kopf vollständig im Bild, Anschnitt nur rechts/unten.
// Ausklang 140,0–142,0 in die Dunkelfläche ⇒ Frame 3549 ≙ Frame 0.
// Endcard (David 2026-07-26): Löwe BÜNDIG an der rechten Bildkante, Logo +
// Claim mittig in der verbleibenden Fläche links davon.
const M_HERO_LOEWE_H = 780; // Unterkante exakt 1080
const M_HERO_LOEWE_W = Math.round((M_HERO_LOEWE_H * 895) / 1389); // 503 (Alpha-BBox-Verhältnis)
const M_HERO_LOEWE_X = BASE_W - M_HERO_LOEWE_W; // 1417 → rechte Kante exakt 1920
const M_HERO_LOEWE_Y = 300;
const M_HERO_FREI_W = M_HERO_LOEWE_X; // 1417 nutzbare Breite links vom Löwen
const M_HERO_LOGO_Y = 322;
const M_HERO_LOGO_W = 300; // 300×173
const M_HERO_CLAIM_Y = 560;
const M_HERO_CLAIM_PX = 88;
const M_HERO_BAR_Y = 712;
const M_HERO_BAR_W = 440;

const EndcardHero169: React.FC<{
  kartentext: string;
  loewe?: { variante: string; drift?: boolean };
  drift: number;
  /** Sekunden ab Sequence-Start, ab denen in die Dunkelfläche ausgeklungen wird. */
  ausklangVon: number;
  ausklangDauer: number;
}> = ({ kartentext, loewe, drift, ausklangVon, ausklangDauer }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const logoIn = spring({ frame, fps, config: SMOOTH, durationInFrames: 18 });
  const textIn = spring({ frame: frame - 8, fps, config: SMOOTH, durationInFrames: 20 });
  const ausVon = Math.round(ausklangVon * fps);
  const ausBis = Math.round((ausklangVon + ausklangDauer) * fps);
  const exit = interpolate(frame, [ausVon, ausBis], [1, 0], {
    ...CLAMP,
    easing: Easing.inOut(Easing.cubic),
  });
  return (
    <div style={{ position: "absolute", inset: 0, opacity: exit }}>
      {/* Löwe bündig an der rechten Bildkante — bewusst OHNE Drift, sonst
          öffnet sich am Rand ein Spalt (David 2026-07-26). */}
      {loewe && (
        <Loewe169
          variante={loewe.variante === "rot" ? "rot" : "weiss"}
          visX={M_HERO_LOEWE_X}
          visY={M_HERO_LOEWE_Y}
          visH={M_HERO_LOEWE_H}
          shiftX={0}
          opacity={0.92 * logoIn}
        />
      )}
      {/* Logo + Claim + Balken mittig in der Fläche links vom Löwen */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: M_HERO_LOGO_Y,
          width: M_HERO_FREI_W,
          display: "flex",
          justifyContent: "center",
          opacity: logoIn,
          transform: `translateY(${(1 - logoIn) * 18}px)`,
        }}
      >
        <ManLogo width={M_HERO_LOGO_W} />
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: M_HERO_CLAIM_Y,
          width: M_HERO_FREI_W,
          textAlign: "center",
          opacity: textIn,
          transform: `translateY(${(1 - textIn) * 20}px)`,
          fontFamily: FONT_TITLE,
          fontWeight: 700,
          fontSize: M_HERO_CLAIM_PX,
          letterSpacing: 2,
          lineHeight: 1.08,
          color: WHITE,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
        }}
      >
        <Markup169 text={kartentext} />
      </div>
      <div
        style={{
          position: "absolute",
          left: (M_HERO_FREI_W - M_HERO_BAR_W * textIn) / 2,
          top: M_HERO_BAR_Y,
          width: M_HERO_BAR_W * textIn,
          height: 6,
          background: MAN_RED,
        }}
      />
    </div>
  );
};

// --- Schema / Defaults ---

export const manWz169MasterSchema = projectPropsSchema.extend({
  fassung: z.enum(["ton", "stumm"]).describe("Fassung: 'ton' oder 'stumm' (Wartezimmer, längere Standzeiten)"),
  ohneCiattei: z.boolean().describe("Ciattei-Elemente ausblenden (2023er Material, MAN-Freigabe offen)"),
});
export type ManWz169MasterProps = z.infer<typeof manWz169MasterSchema>;

export const manWz169MasterDefaults: ManWz169MasterProps = {
  format: "landscape" as const,
  fps: 25 as const,
  durationInSeconds: 142,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  fassung: "ton",
  ohneCiattei: false,
};

export const ManWz169Master: React.FC<ManWz169MasterProps> = ({
  fassung,
  ohneCiattei,
  review,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const stumm = fassung === "stumm";

  // --- Ambient-Ebene (ROOT, außerhalb aller Sequences; ganze Loop-Perioden) ---
  const amp = ampAt169(t);
  const phasePanel = useLoopPhase(6); // Panel-Modulation, 6 ganze Perioden
  const phaseDrift = useLoopPhase(2); // Löwen-/Element-Drift, 2 ganze Perioden
  // Review 2 Nr. 7 + 12 (v4): die rote Ambient-Wanderlinie ist ERSATZLOS raus.
  // Sie lief als 2-px-Strich über die volle Bildhöhe durch JEDEN Frame und
  // stand auf dem Fullscreen-Endscreen als verbotener Kantenbalken im Bild
  // (x≈1677). Ambient-Leben tragen jetzt nur noch Panel-Modulation und
  // Löwen-Drift — beide bewegen nichts Hartkantiges.
  const panelMod = amp * 0.05 * (0.5 + 0.5 * Math.sin(phasePanel));
  const drift = Math.sin(phaseDrift) * 14 * amp;

  // --- Fenster: fest rechts; nur der Spotlight-Glide bewegt es (David Nr. 8) ---
  const spot = spotEnvAt169(t);
  const winX = M_WIN_X + (M_WIN_X_SPOT - M_WIN_X) * spot;
  const winScale = 1 + (M_SPOT_SCALE - 1) * spot;

  // --- Review 2 Nr. 2: KEINE beat-getriebene Text-Bewegung mehr.
  //     'typo-akzent' und 'zeilen-shift' sind im Generator ersatzlos entfernt;
  //     der verbliebene 'licht-akzent' moduliert AUSSCHLIESSLICH die
  //     Streifen-Opazität im Spotlight (siehe Spotlight169) und bewegt nichts.

  // --- Fenster-Hüllkurve (Review 2 Nr. 7): Fade-in aus der Dunkelfläche
  //     (0,0–0,5 s, Loop-Naht) und vollständige Ausblendung 134,0–134,6 s.
  //     Danach existiert rechts NICHTS mehr — kein Dimmen, kein Restrahmen. ---
  const fensterEin = PLAN169.fenster.einblendung;
  const fensterAus = PLAN169.fenster.ausblendung;
  const winOp = Math.min(
    interpolate(t, [fensterEin.start, fensterEin.start + fensterEin.dauer], [0, 1], {
      ...CLAMP,
      easing: Easing.out(Easing.cubic),
    }),
    interpolate(t, [fensterAus.start, fensterAus.start + fensterAus.dauer], [1, 0], {
      ...CLAMP,
      easing: Easing.inOut(Easing.cubic),
    }),
  );

  // --- Endcard-Events ---
  const heroEv = PLAN169.endcard.find((e) => e.typ === "hero");
  const ausklangEv = PLAN169.endcard.find((e) => e.typ === "ausklang");
  const heroStart = heroEv ? heroEv.start : 135.0;
  const heroLoopEnde = ausklangEv ? ausklangEv.ende : PLAN169.meta.masterDauer;
  // Ausklang beginnt am Hero-Ende und ist 0,6 s vor dem Loop-Ende fertig,
  // damit die letzten Frames exakt die Dunkelfläche von Frame 0 zeigen.
  const ausklangVon = (ausklangEv ? ausklangEv.start : 140.0) - heroStart;
  const ausklangDauer = Math.max(0.4, heroLoopEnde - (ausklangEv ? ausklangEv.start : 140.0) - 0.6);

  // --- Logo Zone A: fährt mit dem Fenster hoch/runter, ist in beiden
  //     Spotlights AUS (Review 2 Nr. 9 — Spotlights sind text- UND logofrei)
  //     und ab der Endcard komplett weg (der Endscreen bringt sein eigenes). ---
  const logoOp = winOp * (1 - spot);

  // --- Dauerhafter dunkler Löwe: blendet für den Fullscreen-Endscreen aus und
  //     ist bis 141,6 s wieder da ⇒ Frame 3549 zeigt exakt den Zustand von
  //     Frame 0 (Dunkelfläche + Schattenriss-Löwe; die Wanderlinie, die früher
  //     Teil der Loop-Naht war, existiert nicht mehr). ---
  const heroMask = interpolate(
    t,
    [fensterAus.start, fensterAus.start + 0.8, heroLoopEnde - 1.4, heroLoopEnde - 0.4],
    [0, 1, 1, 0],
    CLAMP,
  );

  const schatten = PLAN169.fenster.schatten;
  const videoSrc = staticFile("clients/man/wz/wz-master-1080.mov");
  const videoFrames = PLAN169.meta.videoFrames; // 3349 (echte Framezahl der ProRes)
  const freezeBisF = fr169(PLAN169.meta.freezeBis); // 3365 = 134,6 s (Ende der Fenster-Ausblendung)

  // Face-Zone: feste Fensterposition rechts (nur noch rechts, David Nr. 8);
  // Relativwerte gelten im 576×1024-FENSTERRAUM (rechts gespiegelt).
  const faceZone169 = {
    left: (M_WIN_X + (1 - 0.37) * M_WIN_W) / BASE_W,
    right: (M_WIN_X + (1 - 0.07) * M_WIN_W) / BASE_W,
    top: (M_WIN_Y + 0.1 * M_WIN_H) / BASE_H,
    bottom: (M_WIN_Y + 0.5 * M_WIN_H) / BASE_H,
  };

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: ANTHRAZIT }}>
        <Stage>
          {/* ---------- Ambient-Wanderlinie: ENTFERNT (Review 2 Nr. 7 + 12, v4).
               Kein hartkantiges Element mehr über der Bühne — insbesondere
               nicht auf dem Fullscreen-Endscreen. ---------- */}

          {/* ---------- Dunkler Vektor-Löwe: dauerhaft subtil, TEILWEISE hinter
               Versatz-Panel+Fenster (Kalibrierung 2026-07-24, David: „dauerhaft
               subtil dahinter"). Vorher stand visX=1142 fast komplett unter dem
               Fenster (nur 22 px Rest) → in den Sprech-Blöcken gar nicht sichtbar.
               Jetzt visX=620: der KOMPLETTE Kopf mit Maul (0–55 % der Breite,
               0–22 % der Höhe der Silhouette) liegt frei auf der Grafikfläche,
               Rumpf/Läufe laufen ab x=1192 (Kantenbalken, Review 3 Nr. 4)
               hinter Fenster+Panel durch — die Silhouette endet bei 1425,
               also ≈233 px Überlappung — und unten aus dem Bild:
               „dahinter", nicht „daneben".
               visY=330 hält ihn unter der Headline (endet ~y 320) und rechts der
               Takeaways/Plakette, er berührt keinen Text.
               Ton-in-Ton: PNG #252F3A bei 68 % auf #2E3A46 ⇒ ≈ #29333F,
               ~13 % Kontrast zur Fläche — Schattenriss, nie Grafikelement. ---------- */}
          <Loewe169
            variante="dunkel"
            visX={620}
            visY={330}
            visH={1250}
            shiftX={Math.sin(phaseDrift) * 10}
            opacity={0.68 * (1 - heroMask)}
          />

          {/* ---------- Spotlight-Momente (Abdunkelung, Vignette, Streifen,
               Glow, Werkzeug-Regen, roter Löwe) — unter der Fenster-Einheit ---------- */}
          {PLAN169.spotlights.map((s) => (
            <Sequence
              key={s.id}
              name={`Spotlight ${s.id}`}
              from={s.frameVon}
              durationInFrames={Math.max(8, fr169(s.ende) - s.frameVon)}
            >
              <Spotlight169 s={s} />
            </Sequence>
          ))}

          {/* ---------- Fenster-Einheit: Schatten + Versatz-Panel + Kantenbalken
               + Video — gleitet/skaliert im Spotlight als Ganzes.
               Review 2 Nr. 7: `winOp` blendet die KOMPLETTE Einheit ein (0,0–0,5 s,
               Loop-Naht) und ab 134,0 s in 0,6 s vollständig aus. ---------- */}
          <div
            style={{
              position: "absolute",
              left: winX,
              top: M_WIN_Y,
              width: M_WIN_W,
              height: M_WIN_H,
              transform: `scale(${winScale})`,
              transformOrigin: "center center",
              opacity: winOp,
            }}
          >
            {/* Kein Schlagschatten mehr (David 2026-07-26): Die Fläche liegt nur
                noch als dunkler Grund unter dem Video, damit beim Ein-/Ausblenden
                nichts durchscheint. Tiefe entsteht allein über das weiche
                Versatz-Panel. */}
            <div
              style={{
                position: "absolute",
                left: 0,
                top: 0,
                width: M_WIN_W,
                height: M_WIN_H,
                background: "#0B1117",
              }}
            />
            {/* Versatz-Panel (#222C36, +24/+24) — jetzt WEICH: blur(26px) nimmt
                die harte Kante raus, das Panel liest als Tiefen-Ebene statt als
                zweiter Schlagschatten. Trägt weiter die Ambient-Modulation. */}
            <div
              style={{
                position: "absolute",
                left: 24,
                top: 24,
                width: M_WIN_W,
                height: M_WIN_H,
                background: ANTHRAZIT_TIEF,
                filter: "blur(26px)",
                opacity: 0.85,
              }}
            >
              {/* dunkle Ambient-Modulation (max ~6 %) — KEIN weißes Aufhellen
                  (Davids Linie: nichts pulsiert weiß) */}
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  background: "#000000",
                  opacity: panelMod,
                }}
              />
            </div>
            {/* Kantenbalken: IMMER konstant rot, Innenkante (links vom Fenster) */}
            <div
              style={{
                position: "absolute",
                left: -8,
                top: 0,
                width: 8,
                height: M_WIN_H,
                background: MAN_RED,
              }}
            />
            {/* Video-Fenster 540×960 (9:16 exakt), scharfkantig */}
            <div
              style={{
                position: "absolute",
                left: 0,
                top: 0,
                width: M_WIN_W,
                height: M_WIN_H,
                overflow: "hidden",
                background: "#0B1117",
                borderRadius: 0,
              }}
            >
              {/* Kein Freeze-Layer mehr (David 2026-07-26): Der frühere
                  <Freeze> hinter dem Videoende zeigte den ERSTEN Frame (Julia)
                  statt des letzten — die Freeze-Frame-Nummer war gegenüber der
                  verschobenen Sequence-Zeitachse außerhalb des gültigen
                  Bereichs. Jetzt endet der Video-Layer exakt mit dem Material;
                  die Fenster-Hüllkurve (winOp) blendet ihn über 1,0 s
                  (133,0–134,0 s) zu transparent ab, sodass nie ein Frame ohne
                  Quelle gezeigt wird. */}
              <Sequence durationInFrames={videoFrames}>
                <OffthreadVideo
                  src={videoSrc}
                  muted={stumm}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                />
              </Sequence>
            </div>
          </div>

          {/* ---------- Logo Zone A (IMMER Bilddatei, Guardrail 9).
               Review 2 Nr. 4: LINKSBÜNDIG bei x=64 (statt zentriert), 200 px
               statt 240 px, Oberkante y 72 → Unterkante ≈ 187. Darunter 165 px
               Luft bis zur Headline. `logoOp` = Fenster-Hüllkurve × (1−spot):
               blendet mit dem Fenster ein, ist in beiden Spotlights aus
               (Nr. 9) und ab der Endcard-Ausblendung komplett weg. ---------- */}
          <div
            style={{
              position: "absolute",
              left: M_GRAF_X,
              top: M_LOGO_Y,
              opacity: logoOp,
            }}
          >
            <ManLogo width={M_LOGO_W} opacity={0.95} />
          </div>

          {/* ---------- Kapitel-Headlines (dauerhaft, Slide+Fade — keine Wipes) ---------- */}
          {PLAN169.headlines.map((h) => (
            <Sequence
              key={h.id}
              name={`Headline K${h.kapitel}`}
              from={h.frameVon}
              durationInFrames={Math.max(8, h.frameBis - h.frameVon)}
            >
              <Headline169 h={h} />
            </Sequence>
          ))}

          {/* ---------- Takeaways (ohne Ciattei — der hängt hinter dem Flag).
               Jedes Takeaway kennt die Zeilenzahl seiner Kapitel-Headline und
               setzt daraus Oberkante + Schriftgrad (Review 2 Nr. 12). ---------- */}
          {PLAN169.takeaways
            .filter((tw) => !tw.ciattei)
            .map((tw) => (
              <Sequence
                key={`takeaway-${tw.block}`}
                name={`Takeaway ${tw.block}`}
                from={tw.frameVon}
                durationInFrames={Math.max(
                  12,
                  (stumm ? tw.frameBisStumm : tw.frameBisTon) - tw.frameVon,
                )}
              >
                <Takeaway169
                  tw={tw}
                  stumm={stumm}
                  headZeilen={kapitelKopf169(tw.start).zeilen}
                  headPlanPx={kapitelKopf169(tw.start).px}
                />
              </Sequence>
            ))}

          {/* ---------- Plaketten (ohne Ciattei) ---------- */}
          {PLAN169.plaketten
            .filter((p) => !p.ciattei)
            .map((p) => (
              <Sequence
                key={`plakette-${p.block}`}
                name={`Plakette ${p.block} ${p.person}`}
                from={p.frameVon}
                durationInFrames={Math.max(4, p.frameBis - p.frameVon)}
              >
                <Plakette169 p={p} />
              </Sequence>
            ))}

          {/* ---------- Review 2 Nr. 9: KEIN Branding-Beat mehr — die Spotlights
               sind text- und logofrei (der Generator liefert branding.aktiv=false). */}

          {/* ---------- Endcard-Hero FULLSCREEN (Review 2 Nr. 7, kein CTA —
               Guardrail 4). Läuft ab 135,0 s bis zum Loop-Ende 142,0 s: Hero
               steht bis 140,0 s, klingt dann in die Dunkelfläche aus. ---------- */}
          {heroEv && (
            <Sequence
              name="Endcard Hero (Fullscreen)"
              from={fr169(heroStart)}
              durationInFrames={Math.max(8, fr169(heroLoopEnde) - fr169(heroStart))}
            >
              <EndcardHero169
                kartentext={heroEv.kartentext ?? "IHR **MAN SERVICE-TEAM**"}
                loewe={heroEv.loewe}
                drift={drift}
                ausklangVon={ausklangVon}
                ausklangDauer={ausklangDauer}
              />
            </Sequence>
          )}

          {/* ---------- Ciattei: abtrennbare Sequences (Guardrail 7) ---------- */}
          {!ohneCiattei &&
            PLAN169.plaketten
              .filter((p) => p.ciattei)
              .map((p) => (
                <Sequence
                  key={`ciattei-plakette-${p.block}`}
                  name="Ciattei Plakette"
                  from={p.frameVon}
                  durationInFrames={Math.max(4, p.frameBis - p.frameVon)}
                >
                  <Plakette169 p={p} />
                </Sequence>
              ))}
          {!ohneCiattei &&
            PLAN169.takeaways
              .filter((tw) => tw.ciattei)
              .map((tw) => (
                <Sequence
                  key={`ciattei-takeaway-${tw.block}`}
                  name="Ciattei Takeaway"
                  from={tw.frameVon}
                  durationInFrames={Math.max(
                    12,
                    (stumm ? tw.frameBisStumm : tw.frameBisTon) - tw.frameVon,
                  )}
                >
                  <Takeaway169
                    tw={tw}
                    stumm={stumm}
                    headZeilen={kapitelKopf169(tw.start).zeilen}
                    headPlanPx={kapitelKopf169(tw.start).px}
                  />
                </Sequence>
              ))}
        </Stage>

        {review?.showGuides && (
          <ReviewOverlay
            showSafeZone={review.showSafeZone ?? true}
            /* Face-Zone nur solange das Fenster existiert (Review 2 Nr. 7) —
               ab 134,6 s ist der Endscreen fullscreen, es gibt kein Gesicht
               und keine Fenster-Geometrie mehr, auf die sich die Zone bezieht. */
            showFaceZone={(review.showFaceZone ?? true) && winOp > 0.01}
            showGrid={review.showGrid ?? false}
            faceZone={review.faceZone ?? faceZone169}
            guideOpacity={review.guideOpacity ?? 0.35}
          />
        )}
      </AbsoluteFill>
    </CIProvider>
  );
};
