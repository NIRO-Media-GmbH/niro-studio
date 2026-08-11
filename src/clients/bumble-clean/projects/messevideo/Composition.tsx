// ============================================================
// BumbleClean — Messevideo 16:9-Master
// 1920×1080, 25fps, 4607 Frames (03:04:07) = exakte Länge des
// 9:16-Hauptvideos. Fenster 540×960 fest rechts (MAN-WZ-Geometrie),
// links Grafikfläche mit Logo + 6 rotierenden Info-Slides.
// Messe-Kontext: läuft stumm im Dauerloop — große Typo, ruhige
// Bewegung, Loop-Naht weich (Slide-Zyklus, sin-Drifts mit ganzen
// Perioden). CI: Schwarz #050505, Gold #FFD700, Glass-Panels,
// Radius 24, Inter (alles von bumble-clean.de abgeleitet).
// ============================================================

import React from "react";
import {
  AbsoluteFill,
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

// --- CI-Konstanten (bumble-clean.de) ---
const GOLD = "#FFD700";
const GOLD_TIEF = "#C9A227";
const GOLD_HELL = "#FFE27A";
const BG = "#050505";
const MUTED = "#CFCFCF";
const GLASS = "rgba(255,255,255,0.06)";
const GLASS_BORDER = "rgba(255,255,255,0.18)";
const RADIUS = 24;
const SCHATTEN = "0 24px 80px rgba(0,0,0,0.55)";

// --- Geometrie (Design 1920×1080, Fenster nach MAN-WZ-Muster) ---
const BASE_W = 1920;
const BASE_H = 1080;
const WIN_W = 540; // 9:16 exakt: 540·16 = 960·9
const WIN_H = 960;
const WIN_X = 1200; // fest rechts, Rand 180
const WIN_Y = 60; // vertikal zentriert
const GRAF_X = 64; // Grafikfläche links 64–1100
const GRAF_W = 1036;
const TEXT_W = 1000; // rechte Textkante 1064 → 136 px Luft zum Fenster

const LOGO_Y = 60;
// Logo: KI-Upscale (Higgsfield 4k) des 297-px-Website-Assets. Alpha wurde
// Luma-basiert rekonstruiert (×3, Klipp — Goldkerne opak, Kanten weich);
// mixBlendMode funktioniert hier NICHT (Stage-Stacking-Context isoliert das
// Img von der Bühne → Blend griff nie, schwarzer Kasten). David: größer.
const LOGO_W = 340;
const SLIDE_Y = 336; // Eyebrow-Oberkante
const FOOTER_Y = 984; // Safe Zone unten: 1080 − 54 = 1026

const FPS = 25;
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const SMOOTH = { damping: 20, stiffness: 100, mass: 1, overshootClamping: true };

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

// --- Info-Slides (Inhalte 1:1 von bumble-clean.de) ---

type SlideItem = { text: string; preis?: string };
type Slide = {
  eyebrow: string;
  headline: string[];
  sub?: string;
  sterne?: boolean;
  items: SlideItem[];
};

const SLIDES: Slide[] = [
  {
    eyebrow: "CAR DETAILING · BAD RAPPENAU",
    headline: ["SHOWROOM-FINISH"],
    sub: "Für Fahrzeuge, die Eindruck hinterlassen.",
    items: [],
  },
  {
    eyebrow: "AUFBEREITUNG IM PAKET",
    headline: ["UNSERE PAKETE"],
    items: [
      { text: "Quick Fix", preis: "ab 149 €" },
      { text: "Basic Care", preis: "ab 249 €" },
      { text: "Premium Care", preis: "ab 349 €" },
    ],
  },
  {
    eyebrow: "GANZ NACH BEDARF",
    headline: ["EINZELLEISTUNGEN"],
    items: [
      { text: "Motorraumreinigung", preis: "ab 49 €" },
      { text: "Lederpflege", preis: "ab 59 €" },
      { text: "Innenreinigung", preis: "ab 99 €" },
      { text: "Nanoversiegelung", preis: "ab 199 €" },
    ],
  },
  // Steinschlag-Slide entfernt (David 2026-08-01): Leistung steht nicht auf
  // der Website — es dürfen NUR Website-belegte Inhalte verwendet werden.
  {
    eyebrow: "WARUM BUMBLECLEAN",
    headline: ["5,0 AUF GOOGLE"],
    sterne: true,
    sub: "„Wir behandeln jedes Auto,\nals wäre es unser eigenes.“",
    items: [],
  },
  {
    eyebrow: "BESUCHEN SIE UNS",
    headline: ["BUMBLE-CLEAN.DE"],
    items: [
      { text: "Riemenstraße 13 · 74906 Bad Rappenau" },
      { text: "Telefon & WhatsApp: 01551 0015990" },
      { text: "Mo–Fr 8–20 Uhr · Sa 9–14 Uhr" },
    ],
  },
];

/** Slide-Fenster: jede Slide läuft 2× pro Loop (~15 s Takt). Das Video hat
 *  keine Dramaturgie — die Grafik trägt allein, Besucher steigen jederzeit
 *  ein; Davids Regel: nie >5 s völlig still. Rest-Frames auf den letzten Slot. */
const RUNDEN = 2;
const SLOTS = SLIDES.length * RUNDEN;
const slideFrames = (durationInFrames: number, slot: number) => {
  const je = Math.floor(durationInFrames / SLOTS);
  const von = slot * je;
  const bis = slot === SLOTS - 1 ? durationInFrames : von + je;
  return { von, dauer: bis - von };
};

// --- Hexagon-Helpers (Waben-Motiv aus dem Logo) ---

const hexPath = (cx: number, cy: number, r: number) => {
  const pts = Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 180) * (60 * i - 30);
    return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
  });
  return `M ${pts.join(" L ")} Z`;
};

// Deterministische Ambient-Waben (kein Random — Remotion/Loop-Determinismus).
const AMBIENT_HEX = [
  { x: 180, y: 210, r: 64, k: 1, op: 0.07 },
  { x: 420, y: 120, r: 38, k: 2, op: 0.05 },
  { x: 90, y: 620, r: 90, k: 1, op: 0.05 },
  { x: 340, y: 860, r: 48, k: 3, op: 0.06 },
  { x: 660, y: 960, r: 70, k: 2, op: 0.05 },
  { x: 940, y: 150, r: 52, k: 2, op: 0.06 },
  { x: 1060, y: 760, r: 40, k: 3, op: 0.05 },
  { x: 800, y: 300, r: 30, k: 1, op: 0.04 },
] as const;

const AmbientWaben: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <svg width={BASE_W} height={BASE_H} style={{ position: "absolute" }}>
      {AMBIENT_HEX.map((h, i) => {
        const phase = (2 * Math.PI * h.k * frame) / durationInFrames;
        const dy = Math.sin(phase + i * 1.7) * 14;
        return (
          <path
            key={i}
            d={hexPath(h.x, h.y + dy, h.r)}
            fill="none"
            stroke={GOLD}
            strokeWidth={1.5}
            opacity={h.op}
          />
        );
      })}
    </svg>
  );
};

/** Logo-Wabe (7 Hexagone) für den Video-Platzhalter. */
const WabenEmblem: React.FC<{ cx: number; cy: number; r: number }> = ({ cx, cy, r }) => {
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
  return (
    <svg
      width={r * 6}
      height={r * 6}
      viewBox={`${-r * 3} ${-r * 3} ${r * 6} ${r * 6}`}
      style={{ display: "block" }}
    >
      {zellen.map(([x, y], i) => (
        <path
          key={i}
          d={hexPath(x, y, r * 0.82)}
          fill="none"
          stroke={GOLD_TIEF}
          strokeWidth={2.5}
          opacity={0.9}
        />
      ))}
    </svg>
  );
};

const Stern: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{ display: "block" }}>
    <path
      d="M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.4L12 17.4l-5.8 3-1.1-6.4L.4 9.4l6.5-.9z"
      fill={GOLD}
    />
  </svg>
);

// --- Slide-Renderer ---

const InfoSlide: React.FC<{ slide: Slide }> = ({ slide }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const exit = interpolate(frame, [durationInFrames - 15, durationInFrames - 2], [1, 0], CLAMP);
  const eyebrowIn = spring({ frame, fps, config: SMOOTH, durationInFrames: 16 });
  const headIn = spring({ frame: frame - 6, fps, config: SMOOTH, durationInFrames: 20 });
  const linieW = interpolate(frame, [14, 34], [0, 220], {
    ...CLAMP,
    easing: Easing.out(Easing.cubic),
  });
  // Nie >5 s still: Gold-Linie pulst im 5-s-Zyklus, Shimmer streicht
  // alle ~7,6 s über die Chips (2× pro Slide-Slot).
  const linieOp = 0.8 + 0.2 * Math.sin((2 * Math.PI * frame) / 125);

  const headPx = slide.headline.length >= 2 ? 76 : 84;
  const headH = slide.headline.length * headPx * 1.08;
  const inhaltY = SLIDE_Y + 54 + headH + 46;

  return (
    <div style={{ position: "absolute", inset: 0, opacity: exit }}>
      {/* Eyebrow */}
      <div
        style={{
          position: "absolute",
          left: GRAF_X,
          top: SLIDE_Y,
          opacity: eyebrowIn,
          transform: `translateY(${(1 - eyebrowIn) * 14}px)`,
          fontFamily: INTER,
          fontWeight: 700,
          fontSize: 30,
          letterSpacing: 6,
          color: GOLD,
        }}
      >
        {slide.eyebrow}
      </div>

      {/* Headline */}
      <div
        style={{
          position: "absolute",
          left: GRAF_X,
          top: SLIDE_Y + 54,
          width: TEXT_W,
          opacity: headIn,
          transform: `translateY(${(1 - headIn) * 18}px)`,
        }}
      >
        {slide.headline.map((z, i) => (
          <div
            key={i}
            style={{
              fontFamily: INTER,
              fontWeight: 800,
              fontSize: headPx,
              letterSpacing: 1,
              lineHeight: 1.08,
              color: "#FFFFFF",
              textTransform: "uppercase",
            }}
          >
            {z}
          </div>
        ))}
        {/* Gold-Linie unter der Headline */}
        <div
          style={{
            marginTop: 22,
            width: linieW,
            height: 5,
            borderRadius: 2.5,
            background: `linear-gradient(90deg, ${GOLD}, ${GOLD_TIEF})`,
            opacity: linieOp,
          }}
        />
      </div>

      {/* Sterne-Reihe (Social-Proof-Slide) */}
      {slide.sterne && (
        <div
          style={{
            position: "absolute",
            left: GRAF_X,
            top: inhaltY,
            display: "flex",
            gap: 18,
          }}
        >
          {[0, 1, 2, 3, 4].map((i) => {
            const sIn = spring({
              frame: frame - 16 - i * 4,
              fps,
              config: { damping: 14, stiffness: 160, mass: 1 },
              durationInFrames: 20,
            });
            // sanftes Atmen, phasenversetzt (4-s-Zyklus)
            const puls = 1 + 0.05 * Math.sin((2 * Math.PI * (frame - i * 12)) / 100);
            return (
              <div key={i} style={{ transform: `scale(${sIn * puls})`, opacity: sIn }}>
                <Stern size={64} />
              </div>
            );
          })}
        </div>
      )}

      {/* Subline */}
      {slide.sub && (
        <div
          style={{
            position: "absolute",
            left: GRAF_X,
            top: inhaltY + (slide.sterne ? 110 : 0),
            width: TEXT_W,
            opacity: interpolate(frame, [18, 34], [0, 1], CLAMP),
            transform: `translateY(${interpolate(frame, [18, 34], [16, 0], CLAMP)}px)`,
            fontFamily: INTER,
            fontWeight: 400,
            fontSize: 46,
            lineHeight: 1.35,
            color: MUTED,
            whiteSpace: "pre-line",
          }}
        >
          {slide.sub}
        </div>
      )}

      {/* Glass-Chips */}
      {slide.items.map((item, i) => {
        const chipIn = spring({
          frame: frame - 16 - i * 5,
          fps,
          config: SMOOTH,
          durationInFrames: 20,
        });
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: GRAF_X,
              top: inhaltY + i * 112,
              width: TEXT_W,
              boxSizing: "border-box",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 24,
              padding: "22px 36px",
              background: GLASS,
              border: `1px solid ${GLASS_BORDER}`,
              borderRadius: RADIUS,
              opacity: chipIn,
              transform: `translateY(${(1 - chipIn) * 24}px)`,
            }}
          >
            <div
              style={{
                fontFamily: INTER,
                fontWeight: 600,
                fontSize: 40,
                color: "#FFFFFF",
                whiteSpace: "nowrap",
              }}
            >
              {item.text}
            </div>
            {item.preis && (
              <div
                style={{
                  fontFamily: INTER,
                  fontWeight: 800,
                  fontSize: 42,
                  color: GOLD,
                  whiteSpace: "nowrap",
                }}
              >
                {item.preis}
              </div>
            )}
            {/* Gold-Shimmer: schmaler Lichtstreifen, ~7,6-s-Zyklus, je Chip versetzt */}
            {(() => {
              const zyklus = 190;
              const sh = (((frame - 40 - i * 10) % zyklus) + zyklus) % zyklus;
              if (sh >= 34) return null;
              const shX = interpolate(sh, [0, 34], [-40, 110], CLAMP);
              return (
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    borderRadius: RADIUS,
                    overflow: "hidden",
                    pointerEvents: "none",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: -24,
                      bottom: -24,
                      width: 130,
                      left: `${shX}%`,
                      transform: "skewX(-18deg)",
                      background:
                        "linear-gradient(90deg, transparent, rgba(255,215,0,0.16), transparent)",
                    }}
                  />
                </div>
              );
            })()}
          </div>
        );
      })}
    </div>
  );
};

// --- Video-Platzhalter (bis der finale Schnitt in Material/Video liegt) ---

const VideoPlatzhalter: React.FC<{ videoDatei: string }> = ({ videoDatei }) => (
  <AbsoluteFill
    style={{
      background: "#0A0A0A",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: 28,
    }}
  >
    <WabenEmblem cx={0} cy={0} r={44} />
    <div
      style={{
        fontFamily: INTER,
        fontWeight: 700,
        fontSize: 30,
        letterSpacing: 4,
        color: GOLD_TIEF,
      }}
    >
      MESSE-VIDEO 9:16
    </div>
    <div
      style={{
        fontFamily: INTER,
        fontWeight: 400,
        fontSize: 19,
        color: "rgba(255,255,255,0.45)",
        textAlign: "center",
        lineHeight: 1.5,
        padding: "0 40px",
      }}
    >
      Material/Video/{videoDatei}
      <br />
      dann Prop „videoVorhanden" aktivieren
    </div>
  </AbsoluteFill>
);

// --- Schema / Defaults ---

export const bumbleCleanMesseSchema = projectPropsSchema.extend({
  videoDatei: z
    .string()
    .describe("Dateiname des 9:16-Hauptvideos in Material/Video/"),
  videoVorhanden: z
    .boolean()
    .describe("Aus = Platzhalter im Fenster (solange der Schnitt fehlt)"),
});
export type BumbleCleanMesseProps = z.infer<typeof bumbleCleanMesseSchema>;

export const bumbleCleanMesseDefaults: BumbleCleanMesseProps = {
  format: "landscape" as const,
  fps: 25 as const,
  durationInSeconds: 184.28, // 4607 Frames = 03:04:07 @ 25fps
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  videoDatei: "messe-video-916.mp4",
  videoVorhanden: false,
};

// --- Master ---

export const BumbleCleanMesseMaster: React.FC<BumbleCleanMesseProps> = ({
  videoDatei,
  videoVorhanden,
  review,
}) => {
  const { durationInFrames } = useVideoConfig();

  // Atmender Gold-Glow hinter dem Fenster (ganze Perioden → Loop-naht sauber)
  const glow = 0.08 + 0.04 * Math.sin(useLoopPhase(2));

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: BG }}>
        <Stage>
          {/* Ambient: Waben-Motiv, sehr dezent */}
          <AmbientWaben />

          {/* Gold-Glow hinter dem Fenster */}
          <div
            style={{
              position: "absolute",
              left: WIN_X + WIN_W / 2 - 700,
              top: WIN_Y + WIN_H / 2 - 700,
              width: 1400,
              height: 1400,
              background: `radial-gradient(circle, rgba(255,215,0,${glow}) 0%, rgba(255,215,0,0) 60%)`,
            }}
          />

          {/* Fenster-Einheit: 9:16-Video, Radius 24, Gold-Rahmen */}
          <div
            style={{
              position: "absolute",
              left: WIN_X,
              top: WIN_Y,
              width: WIN_W,
              height: WIN_H,
              borderRadius: RADIUS,
              boxShadow: SCHATTEN,
            }}
          >
            <div
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: RADIUS,
                overflow: "hidden",
                background: "#0A0A0A",
              }}
            >
              {videoVorhanden ? (
                <Sequence durationInFrames={durationInFrames}>
                  <OffthreadVideo
                    src={staticFile(`projects/bumble-clean-messevideo/${videoDatei}`)}
                    muted
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                </Sequence>
              ) : (
                <VideoPlatzhalter videoDatei={videoDatei} />
              )}
            </div>
            {/* Gold-Rahmen über dem Video */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: RADIUS,
                border: "1.5px solid rgba(255,215,0,0.45)",
                pointerEvents: "none",
              }}
            />
            {/* Gold-Akzent an der Unterkante (WZ-Frame-Muster) */}
            <div
              style={{
                position: "absolute",
                left: 24,
                bottom: -14,
                width: WIN_W - 48,
                height: 5,
                borderRadius: 2.5,
                background: `linear-gradient(90deg, ${GOLD}, ${GOLD_TIEF})`,
              }}
            />
          </div>

          {/* Logo oben links (Quell-PNG quadratisch mit Transparenz-Rand,
              sichtbarer Streifen ≈ mittleres Drittel → top kompensiert) */}
          <div
            style={{
              position: "absolute",
              left: GRAF_X,
              top: LOGO_Y - Math.round(LOGO_W * 0.33),
              width: LOGO_W,
              height: LOGO_W,
            }}
          >
            <Img
              src={staticFile("clients/bumble-clean/logo-4x.png")}
              style={{ width: LOGO_W, opacity: 0.95 }}
            />
          </div>

          {/* Rotierende Info-Slides (2 Runden pro Loop) */}
          {Array.from({ length: SLOTS }, (_, slot) => {
            const s = SLIDES[slot % SLIDES.length];
            const { von, dauer } = slideFrames(durationInFrames, slot);
            return (
              <Sequence key={slot} name={`Slide ${(slot % SLIDES.length) + 1}.${Math.floor(slot / SLIDES.length) + 1}: ${s.eyebrow}`} from={von} durationInFrames={dauer}>
                <InfoSlide slide={s} />
              </Sequence>
            );
          })}

          {/* Konstanter Footer */}
          <div
            style={{
              position: "absolute",
              left: GRAF_X,
              top: FOOTER_Y,
              display: "flex",
              alignItems: "baseline",
              gap: 18,
            }}
          >
            <span
              style={{
                fontFamily: INTER,
                fontWeight: 700,
                fontSize: 28,
                letterSpacing: 2,
                color: GOLD,
              }}
            >
              BUMBLE-CLEAN.DE
            </span>
            <span
              style={{
                fontFamily: INTER,
                fontWeight: 400,
                fontSize: 24,
                color: "rgba(255,255,255,0.55)",
              }}
            >
              Premium Fahrzeugaufbereitung · Bad Rappenau
            </span>
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
