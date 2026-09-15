// ============================================================
// MAN Truck & Bus — Recruiting CTA Endslide
// "Fachkraft für Lagerlogistik" — Ausbildung
// 9:16 portrait (1080×1920), 30fps, 8s
// KRANK: heftige Springs, Glow-Pulse, Micro-Shake, schnelle Chip-Einflüge
// Animierter MAN-Grafik-Hintergrund (kein Foto), CTA-Fokus
// Look angelehnt an die MAN Still-Ads (dunkel + MAN-Rot, weißes Logo,
// rote Pill-Badges/Chips, große Condensed-Headline)
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Img,
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

const ci = loadBrand("man", brandJson as any);

// --- Local MAN Global font injection (TTFs in /public/fonts/man) ---
const MAN_FACES = [
  { family: "MAN Global", weight: 300, file: "MAN_Global-Light.ttf" },
  { family: "MAN Global", weight: 400, file: "MAN_Global-Regular.ttf" },
  { family: "MAN Global", weight: 500, file: "MAN_Global-Medium.ttf" },
  { family: "MAN Global", weight: 700, file: "MAN_Global-Bold.ttf" },
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

// --- Brand colors ---
const MAN_RED = "#E30045";
const VENETIAN = "#720022";
const WHITE = "#FFFFFF";
const BASE = "#12000A";

// --- Base design resolution (everything is authored at 1080×1920, then
// uniformly scaled to the real canvas so 4K looks identical, not tiny) ---
const BASE_W = 1080;
const BASE_H = 1920;

// --- Spring configs ---
// Snappy entrance, but high enough damping to land cleanly WITHOUT
// the back-and-forth overshoot wobble after settling.
const PUNCH = { damping: 16, stiffness: 170, mass: 1 };
const HARD = { damping: 17, stiffness: 200, mass: 0.9 };
const SMOOTH = { damping: 20, stiffness: 100, mass: 1, overshootClamping: true };

// --- Deterministic PRNG (mulberry32) for particle field ---
const mulberry32 = (seed: number) => () => {
  let t = (seed += 0x6d2b79f5);
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const PARTICLE_COUNT = 46;
const PARTICLES = (() => {
  const rnd = mulberry32(20260618);
  return Array.from({ length: PARTICLE_COUNT }, () => ({
    x: rnd(),
    y: rnd(),
    size: 1.5 + rnd() * 4.5,
    speed: 0.15 + rnd() * 0.7,
    drift: (rnd() - 0.5) * 0.04,
    phase: rnd() * Math.PI * 2,
    opacity: 0.12 + rnd() * 0.45,
  }));
})();

// =============================================================
// SCHEMA
// =============================================================

export const manLagerCtaSchema = projectPropsSchema.extend({
  eyebrow: z.string().describe("Eyebrow / Badge oben"),
  headline: z.string().describe("Headline (zweizeilig, \\n für Umbruch)"),
  beruf2: z.string().describe("Zweiter Beruf, gleichwertig unter dem ersten (\\n für Umbruch, leer = entfällt)"),
  headlineSuffix: z.string().describe("Kleiner Zusatz, z.B. (m/w/d)"),
  benefits: z.array(z.string()).max(6).describe("Benefit-Chips (leer = Block entfällt)"),
  ctaText: z.string().describe("CTA Button Text"),
  subText: z.string().describe("Sub-Text unter CTA"),
});

export type ManLagerCtaProps = z.infer<typeof manLagerCtaSchema>;

// --- Default Props ---
export const manLagerCtaDefaults: ManLagerCtaProps = {
  format: "portrait" as const,
  fps: 30 as const,
  durationInSeconds: 10,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  eyebrow: "STARTE DEINE AUSBILDUNG",
  headline: "FACHKRAFT FÜR\nLAGERLOGISTIK",
  beruf2: "Kaufmann/frau\nim Einzelhandel", // Kundenwunsch 2026-08-13, gleichwertig zu Beruf 1
  headlineSuffix: "(m/w/d)",
  // Kundenwunsch 2026-08-13: Benefits ganz raus, Standort raus
  benefits: [],
  ctaText: "Jetzt in unter 1 Min. bewerben",
  subText: "Ohne Lebenslauf!",
};

// =============================================================
// Animated graphic background
// =============================================================

const Background: React.FC<{ frame: number; fps: number; introFrames: number }> = ({
  frame,
  fps,
  introFrames,
}) => {
  // Authored in the 1080×1920 base space (parent applies the resolution scale).
  const width = BASE_W;
  const height = BASE_H;

  // --- Intro reveal (0 → 1 across the intro): iris + whoosh ---
  // Hold fully empty briefly, then ease the BG in over the rest of the intro.
  const startHold = Math.round(introFrames * 0.12);
  const reveal = interpolate(frame, [startHold, introFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const irisR = interpolate(reveal, [0, 1], [0, 165]);
  const revealScale = interpolate(reveal, [0, 1], [1.14, 1]);
  const revealBlur = interpolate(reveal, [0, 1], [34, 0]);
  // Diagonal light streak that whips across as it reveals
  const sweepX = interpolate(reveal, [0, 1], [-width * 0.6, width * 1.25]);
  const sweepOp = interpolate(reveal, [0.05, 0.4, 0.95], [0, 0.9, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Bloom flash right as the reveal lands
  const flash = interpolate(reveal, [0.62, 0.84, 1], [0, 0.6, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Big radial MAN-red glow that breathes
  const glowIn = spring({ frame, fps, config: { damping: 30, stiffness: 60, mass: 1 } });
  const pulse = 0.5 + 0.5 * Math.sin(frame / 26);
  const glowScale = interpolate(glowIn, [0, 1], [0.6, 1]) * (0.92 + pulse * 0.16);
  const glowOpacity = interpolate(glowIn, [0, 1], [0, 0.85]) * (0.7 + pulse * 0.3);

  // Slowly drifting grid
  const gridShift = (frame * 0.4) % 70;

  // Diagonal sweeping streaks
  const streak1 = ((frame * 6) % (width + 700)) - 350;
  const streak2 = ((frame * 4 + 400) % (width + 700)) - 350;

  return (
    <AbsoluteFill
      style={{
        clipPath: `circle(${irisR}% at 50% 38%)`,
        WebkitClipPath: `circle(${irisR}% at 50% 38%)`,
        transform: `scale(${revealScale})`,
        filter: revealBlur > 0.1 ? `blur(${revealBlur}px)` : undefined,
      }}
    >
      {/* Solid opaque base so the revealed CTA fully covers (no footage bleed) */}
      <AbsoluteFill style={{ backgroundColor: BASE }} />
      {/* Tinted radial */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(120% 90% at 50% 38%, ${VENETIAN} 0%, ${BASE} 58%, #08000400 100%)`,
        }}
      />

      {/* Drifting grid */}
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${MAN_RED}22 1px, transparent 1px), linear-gradient(90deg, ${MAN_RED}22 1px, transparent 1px)`,
          backgroundSize: "70px 70px",
          backgroundPosition: `${gridShift}px ${gridShift}px`,
          maskImage: "radial-gradient(80% 70% at 50% 42%, #000 0%, transparent 75%)",
          WebkitMaskImage: "radial-gradient(80% 70% at 50% 42%, #000 0%, transparent 75%)",
          opacity: 0.5,
        }}
      />

      {/* Diagonal streaks */}
      {[streak1, streak2].map((sx, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            top: -200,
            left: sx,
            width: i === 0 ? 120 : 60,
            height: height + 400,
            background: `linear-gradient(180deg, transparent, ${MAN_RED}${i === 0 ? "33" : "22"}, transparent)`,
            transform: "rotate(18deg)",
            filter: "blur(6px)",
          }}
        />
      ))}

      {/* Central glow */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "40%",
          width: width * 1.5,
          height: width * 1.5,
          transform: `translate(-50%, -50%) scale(${glowScale})`,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${MAN_RED} 0%, ${MAN_RED}88 24%, transparent 60%)`,
          opacity: glowOpacity * 0.55,
          filter: "blur(20px)",
          mixBlendMode: "screen",
        }}
      />

      {/* Floating particles */}
      {PARTICLES.map((p, i) => {
        const t = frame / fps;
        const py = (p.y - t * p.speed * 0.08) % 1;
        const yy = (py < 0 ? py + 1 : py) * height;
        const xx =
          p.x * width + Math.sin(frame * 0.03 + p.phase) * 22 + frame * p.drift * 6;
        const tw = 0.5 + 0.5 * Math.sin(frame * 0.08 + p.phase);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: ((xx % width) + width) % width,
              top: yy,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              background: WHITE,
              opacity: p.opacity * tw,
              boxShadow: `0 0 ${p.size * 2}px ${MAN_RED}`,
            }}
          />
        );
      })}

      {/* Vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(120% 100% at 50% 50%, transparent 55%, rgba(0,0,0,0.55) 100%)",
        }}
      />

      {/* Intro: sweeping light streak */}
      <div
        style={{
          position: "absolute",
          top: -200,
          left: sweepX,
          width: 240,
          height: height + 400,
          background: `linear-gradient(180deg, transparent, ${WHITE}aa, ${MAN_RED}, transparent)`,
          transform: "rotate(18deg)",
          filter: "blur(16px)",
          opacity: sweepOp,
          mixBlendMode: "screen",
        }}
      />
      {/* Intro: bloom flash on landing */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(70% 55% at 50% 38%, ${MAN_RED} 0%, transparent 70%)`,
          opacity: flash,
          mixBlendMode: "screen",
        }}
      />
    </AbsoluteFill>
  );
};

// =============================================================
// Component
// =============================================================

export const ManLagerCta: React.FC<ManLagerCtaProps> = ({
  review,
  eyebrow,
  headline,
  beruf2,
  headlineSuffix,
  benefits,
  ctaText,
  subText,
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();

  // Resolution scale: layout authored at 1080×1920, scaled up to real canvas
  // (e.g. ×2 at 4K) so element sizes stay proportional instead of looking tiny.
  const S = width / BASE_W;

  // --- Intro transition (transparent → BG reveal), fps-relative ---
  const INTRO_SEC = 2;
  const INTRO = Math.round(INTRO_SEC * fps);
  const F = (sec: number) => Math.round(sec * fps);

  // --- Titel-Zeilen: beide Ausbildungen visuell gleichwertig (Kundenwunsch 2026-08-13) ---
  // Sequenz: Beruf 1 · roter „+"-Trenner · Beruf 2; Highlight auf der letzten Zeile JEDES Berufs.
  const beruf1Zeilen = headline.split("\n");
  const beruf2Zeilen = beruf2 !== "" ? beruf2.split("\n") : [];
  const titelZeilen = [
    ...beruf1Zeilen.map((text, i) => ({ text, highlight: i === beruf1Zeilen.length - 1, separator: false })),
    ...(beruf2Zeilen.length > 0 ? [{ text: "+", highlight: false, separator: true }] : []),
    ...beruf2Zeilen.map((text, i) => ({ text, highlight: i === beruf2Zeilen.length - 1, separator: false })),
  ];

  // --- Timings (CTA content starts AFTER the intro) ---
  const logoStart = INTRO + 0;
  const eyebrowStart = INTRO + F(0.33);
  const headlineStart = INTRO + F(0.8);
  const chipsStart = INTRO + F(2.33);
  // Ohne Benefit-Chips rückt der CTA zeitlich und räumlich nach oben
  const hatChips = benefits.length > 0;
  const titelEnde = headlineStart + (titelZeilen.length - 1) * F(0.4); // Start der letzten Titel-Zeile
  const ctaStart = hatChips ? INTRO + F(3.53) : Math.max(INTRO + F(2.53), titelEnde + F(0.8));
  const subStart = ctaStart + F(0.47);

  // --- Logo ---
  const logoP = spring({ frame: frame - logoStart, fps, config: PUNCH });
  const logoScale = interpolate(logoP, [0, 1], [0.6, 1]);
  const logoOp = interpolate(frame, [logoStart, logoStart + 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // --- Eyebrow badge (width sweep + content fade) ---
  const ebP = spring({ frame: frame - eyebrowStart, fps, config: HARD });
  const ebScaleX = interpolate(ebP, [0, 1], [0, 1]);
  const ebContentOp = interpolate(
    frame,
    [eyebrowStart + 6, eyebrowStart + 14],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // --- Titel-Zeilen (smash-in with decaying micro-shake) ---
  const lineAnim = (idx: number) => {
    const start = headlineStart + idx * F(0.4);
    const p = spring({ frame: frame - start, fps, config: HARD });
    const op = interpolate(frame, [start, start + F(0.23)], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const scale = interpolate(p, [0, 1], [1.18, 1]);
    // Subtle impact-shake that decays quickly (no lingering wobble)
    const shakeAmt = interpolate(frame - start, [0, F(0.23)], [4, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    const shakeX = Math.sin((frame - start) * 2.1) * shakeAmt;
    const shakeY = Math.cos((frame - start) * 1.7) * shakeAmt * 0.5;
    return { op, scale, shakeX, shakeY };
  };

  // Highlight-Sweep je markierter Titel-Zeile (eigener Start pro Zeile)
  const hlScaleXFor = (idx: number) => {
    const start = headlineStart + idx * F(0.4) + F(0.13);
    const p = spring({ frame: frame - start, fps, config: { damping: 16, stiffness: 150, mass: 1, overshootClamping: true } });
    return interpolate(p, [0, 1], [0, 1]);
  };
  // Suffix (m/w/d) nach der letzten Titel-Zeile — gilt für beide Berufe
  const suffixStart = titelEnde + F(0.46);

  // --- CTA ---
  const ctaP = spring({ frame: frame - ctaStart, fps, config: PUNCH });
  const ctaScale = interpolate(ctaP, [0, 1], [0.78, 1]);
  const ctaOp = interpolate(frame, [ctaStart, ctaStart + 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Continuous glow pulse after entrance
  const ctaGlow = ctaP > 0.6 ? 0.5 + 0.5 * Math.sin(frame / 11) : 0;

  // --- Sub text ---
  const subOp = interpolate(frame, [subStart, subStart + F(0.4)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
        {/* Resolution-scaled stage: authored at 1080×1920, scaled to canvas */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: BASE_W,
            height: BASE_H,
            transform: `scale(${S})`,
            transformOrigin: "top left",
          }}
        >
          <Background frame={frame} fps={fps} introFrames={INTRO} />

        {/* ===== Logo ===== */}
        <div
          style={{
            position: "absolute",
            top: "9%",
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            opacity: logoOp,
            transform: `scale(${logoScale})`,
          }}
        >
          <Img
            src={staticFile("clients/man/logo-weiss.png")}
            style={{ width: 200, height: "auto", filter: "drop-shadow(0 4px 20px rgba(0,0,0,0.5))" }}
          />
        </div>

        {/* ===== Eyebrow badge ===== */}
        <div
          style={{
            position: "absolute",
            top: "18%",
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
          }}
        >
          <div style={{ position: "relative", display: "inline-flex" }}>
            <div
              style={{
                position: "absolute",
                inset: 0,
                backgroundColor: MAN_RED,
                borderRadius: 999,
                transform: `scaleX(${ebScaleX})`,
                transformOrigin: "center",
                boxShadow: `0 6px 26px ${MAN_RED}66`,
              }}
            />
            <div
              style={{
                position: "relative",
                padding: "14px 30px",
                fontFamily: FONT_BODY,
                fontWeight: 700,
                fontSize: 30,
                letterSpacing: 2,
                color: WHITE,
                textTransform: "uppercase",
                opacity: ebContentOp,
                whiteSpace: "nowrap",
              }}
            >
              {eyebrow}
            </div>
          </div>
        </div>

        {/* ===== Headline ===== */}
        <div
          style={{
            position: "absolute",
            top: "22%",
            left: 0,
            right: 0,
            padding: "0 56px",
            textAlign: "center",
          }}
        >
          {titelZeilen.map((z, idx) => {
            const a = lineAnim(idx);
            if (z.separator) {
              return (
                <div
                  key={idx}
                  style={{
                    position: "relative",
                    margin: "2px 0",
                    opacity: a.op,
                    transform: `translate(${a.shakeX}px, ${a.shakeY}px) scale(${a.scale})`,
                  }}
                >
                  <span
                    style={{
                      fontFamily: FONT_TITLE,
                      fontWeight: 700,
                      fontSize: 54,
                      lineHeight: 1.0,
                      color: WHITE,
                      textShadow: "0 4px 24px rgba(0,0,0,0.45)",
                    }}
                  >
                    {z.text}
                  </span>
                </div>
              );
            }
            return (
              <div
                key={idx}
                style={{
                  position: "relative",
                  display: "block",
                  opacity: a.op,
                  transform: `translate(${a.shakeX}px, ${a.shakeY}px) scale(${a.scale})`,
                }}
              >
                {z.highlight && (
                  <div
                    style={{
                      position: "absolute",
                      top: "10%",
                      bottom: "8%",
                      left: "50%",
                      width: "104%",
                      marginLeft: "-52%",
                      backgroundColor: MAN_RED,
                      borderRadius: 8,
                      transform: `scaleX(${hlScaleXFor(idx)})`,
                      transformOrigin: "center",
                      boxShadow: `0 8px 34px ${MAN_RED}77`,
                    }}
                  />
                )}
                <span
                  style={{
                    position: "relative",
                    fontFamily: FONT_TITLE,
                    fontWeight: 700,
                    fontSize: 96,
                    lineHeight: 1.05,
                    letterSpacing: -1,
                    color: WHITE,
                    textTransform: "uppercase",
                    whiteSpace: "nowrap",
                    textShadow: "0 4px 24px rgba(0,0,0,0.45)",
                  }}
                >
                  {z.text}
                </span>
              </div>
            );
          })}
          {/* suffix — gilt für beide Berufe */}
          <div
            style={{
              marginTop: 10,
              fontFamily: FONT_BODY,
              fontWeight: 500,
              fontSize: 30,
              letterSpacing: 3,
              color: "rgba(255,255,255,0.65)",
              textTransform: "uppercase",
              opacity: interpolate(
                frame,
                [suffixStart, suffixStart + F(0.33)],
                [0, 1],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                },
              ),
            }}
          >
            {headlineSuffix}
          </div>
        </div>

        {/* ===== Benefit chips ===== */}
        {hatChips && (
        <div
          style={{
            position: "absolute",
            top: "47%",
            left: 0,
            right: 0,
            padding: "0 70px",
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: 16,
          }}
        >
          {benefits.map((b, i) => {
            const start = chipsStart + i * F(0.167);
            const p = spring({ frame: frame - start, fps, config: HARD });
            const op = interpolate(frame, [start, start + 7], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const scale = interpolate(p, [0, 1], [0.6, 1]);
            const ty = interpolate(p, [0, 1], [34, 0]);
            return (
              <div
                key={i}
                style={{
                  opacity: op,
                  transform: `translateY(${ty}px) scale(${scale})`,
                  backgroundColor: MAN_RED,
                  borderRadius: 999,
                  padding: "16px 28px",
                  fontFamily: FONT_BODY,
                  fontWeight: 700,
                  fontSize: 30,
                  color: WHITE,
                  whiteSpace: "nowrap",
                  boxShadow: `0 8px 24px ${MAN_RED}44`,
                }}
              >
                {b}
              </div>
            );
          })}
        </div>
        )}

        {/* ===== CTA button ===== */}
        <div
          style={{
            position: "absolute",
            top: hatChips ? "66%" : "56%",
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            padding: "0 56px",
            opacity: ctaOp,
            transform: `scale(${ctaScale})`,
          }}
        >
          <div
            style={{
              backgroundColor: WHITE,
              borderRadius: 18,
              padding: "26px 44px",
              textAlign: "center",
              boxShadow: `0 10px 40px rgba(0,0,0,0.4), 0 0 ${30 + ctaGlow * 40}px ${MAN_RED}${ctaGlow > 0.5 ? "cc" : "88"}`,
            }}
          >
            <div
              style={{
                fontFamily: FONT_TITLE,
                fontWeight: 700,
                fontSize: 40,
                letterSpacing: 0.5,
                color: MAN_RED,
                textTransform: "uppercase",
              }}
            >
              {ctaText}
            </div>
          </div>
        </div>

        {/* ===== Sub text ===== */}
        <div
          style={{
            position: "absolute",
            top: hatChips ? "74%" : "64%",
            left: 0,
            right: 0,
            textAlign: "center",
            padding: "0 56px",
            opacity: subOp,
          }}
        >
          <div
            style={{
              fontFamily: FONT_BODY,
              fontWeight: 500,
              fontStyle: "italic",
              fontSize: 30,
              color: "rgba(255,255,255,0.82)",
            }}
          >
            {subText}
          </div>
        </div>
        </div>
        {/* end resolution-scaled stage */}

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
