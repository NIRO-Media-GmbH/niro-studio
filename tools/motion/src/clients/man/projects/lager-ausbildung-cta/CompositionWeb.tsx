// ============================================================
// MAN Truck & Bus — Recruiting-CTA Endcard „Fachkraft für Lagerlogistik"
// im MAN-Web-Look des Wartezimmervideos (Kundenwunsch 2026-08-13):
// Anthrazit-Fläche, Radius 0, Rot nur als Akzent, Cond-Bold-Versalien,
// dunkler Löwe links (Blick nach rechts — MAN-Auflage 2026-07-29),
// Claim „GROSSES BEWEGEN MIT MAN", QR jobs.man.eu.
// 9:16, authored 1080×1920, uniform auf Canvas skaliert (4K via --scale=2).
// Text bewegt sich nur in Y (Fade + von unten), nichts pulsiert weiß.
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Img,
  useVideoConfig,
  useCurrentFrame,
  spring,
  interpolate,
  staticFile,
} from "remotion";
import { z } from "zod";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";

const ci = loadBrand("man", brandJson as any);

// --- MAN Global font injection (TTFs in /public/fonts/man) ---
const MAN_FACES = [
  { family: "MAN Global", weight: 400, file: "MAN_Global-Regular.ttf" },
  { family: "MAN Global", weight: 500, file: "MAN_Global-Medium.ttf" },
  { family: "MAN Global", weight: 700, file: "MAN_Global-Bold.ttf" },
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

// --- man.eu-Design-Tokens (Wartezimmervideo v2) ---
const ANTHRAZIT = "#2E3A46";
const MAN_RED = "#E30045";
const WHITE = "#FFFFFF";

// --- Basis-Layout 1080×1920, uniform skaliert ---
const BASE_W = 1080;
const BASE_H = 1920;
const COL_X = 110; // linke Textspalte

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const SMOOTH = { damping: 20, stiffness: 100, mass: 1, overshootClamping: true };

// --- Löwen-Platzierung über sichtbare BBox (Messwerte Wartezimmer Task 2) ---
const LION_VIS_R = { left: 107 / 1200, top: 507 / 2400, w: 895 / 1200, h: 1388 / 2400 };

const LoeweDunkel: React.FC<{
  visX: number;
  visY: number;
  visH: number;
  shiftX?: number;
  opacity?: number;
}> = ({ visX, visY, visH, shiftX = 0, opacity = 1 }) => {
  const imgH = visH / LION_VIS_R.h;
  const imgW = imgH * 0.5; // PNG-Leinwand 1200×2400
  return (
    <Img
      src={staticFile("clients/man/wz/loewe-rechts-dunkel.png")}
      style={{
        position: "absolute",
        width: imgW,
        height: imgH,
        left: visX - imgW * LION_VIS_R.left,
        top: visY - imgH * LION_VIS_R.top,
        transform: `translateX(${shiftX}px)`,
        opacity,
      }}
    />
  );
};

// ** … ** → MAN-Rot (wie Markup169 im Wartezimmervideo)
const Markup: React.FC<{ text: string }> = ({ text }) => (
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

// =============================================================
// SCHEMA
// =============================================================

export const manLagerCtaWebSchema = projectPropsSchema.extend({
  kicker: z.string().describe("Kicker-Zeile über der Headline"),
  headline: z.string().describe("Berufstitel (\\n für Umbruch)"),
  headlineSuffix: z.string().describe("Zusatz, z. B. (m/w/d) — Pflicht bei Job-CTAs"),
  benefits: z.array(z.string()).max(6).describe("Benefit-Zeilen (leer = Block entfällt)"),
  claimZeilen: z
    .array(z.string())
    .min(1)
    .max(3)
    .describe("Claim-Zeilen, **…** = rot"),
  ctaText: z.string().describe("CTA-Zeile unter dem roten Balken"),
  ctaSub: z.string().describe("Sub-Zeile unter dem CTA (leer = entfällt)"),
  zeigeQr: z.boolean().describe("QR-Code jobs.man.eu anzeigen"),
  qrLabel: z.string().describe("Label unter dem QR-Code"),
});

export type ManLagerCtaWebProps = z.infer<typeof manLagerCtaWebSchema>;

export const manLagerCtaWebDefaults: ManLagerCtaWebProps = {
  format: "portrait" as const,
  fps: 30 as const,
  durationInSeconds: 10,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: false,
    showGrid: false,
    guideOpacity: 0.35,
  },
  kicker: "STARTE DEINE AUSBILDUNG",
  headline: "FACHKRAFT FÜR\nLAGERLOGISTIK",
  headlineSuffix: "(m/w/d)",
  benefits: [
    "Attraktive Vergütung",
    "30 Tage Urlaub",
    "Kostenloses iPad",
    "36h Woche",
  ],
  claimZeilen: ["GROSSES BEWEGEN", "**MIT MAN**"],
  // Wording aus den laufenden Lager-Kampagnen-Ads (Screens von David 2026-08-13)
  ctaText: "JETZT IN UNTER 1 MIN. BEWERBEN",
  ctaSub: "IN KARLSRUHE – OHNE LEBENSLAUF!",
  zeigeQr: false, // Davids Vorgabe 2026-08-13: kein QR im Lager-CTA
  qrLabel: "JOBS.MAN.EU",
};

// =============================================================
// Komposition
// =============================================================

export const ManLagerCtaWeb: React.FC<ManLagerCtaWebProps> = ({
  review,
  kicker,
  headline,
  headlineSuffix,
  benefits,
  claimZeilen,
  ctaText,
  ctaSub,
  zeigeQr,
  qrLabel,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, durationInFrames } = useVideoConfig();
  const S = width / BASE_W;
  const F = (sec: number) => Math.round(sec * fps);

  // Eintritt: Fade + 18 px von unten, weich, ohne Overshoot
  const rein = (start: number, dist = 18) => {
    const p = spring({ frame: frame - start, fps, config: SMOOTH, durationInFrames: 22 });
    return { opacity: p, transform: `translateY(${(1 - p) * dist}px)` };
  };

  // --- Timings (gestaffelt, alles steht nach ~4 s) ---
  const bgIn = interpolate(frame, [0, F(0.4)], [0, 1], CLAMP);
  const logoStart = F(0.3);
  const kickerStart = F(0.65);
  const headStart = F(0.85);
  const suffixStart = F(1.35);
  const benefitsStart = F(1.6);
  const claimStart = F(2.5);
  const barStart = F(2.75);
  const ctaStart = F(3.05);
  const qrStart = F(3.3);

  // Roter Balken wächst in der Breite (Fläche, kein Text → X erlaubt)
  const barP = spring({ frame: frame - barStart, fps, config: SMOOTH, durationInFrames: 20 });

  // Löwe: sehr langsamer Drift über die volle Laufzeit — nie ganz statisch
  const lionShift = interpolate(frame, [0, durationInFrames], [0, 10]);

  const headLines = headline.split("\n");

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
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
          {/* ===== Anthrazit-Fläche + Löwe (Ton-in-Ton, links, Blick rechts) ===== */}
          <AbsoluteFill style={{ backgroundColor: ANTHRAZIT, opacity: bgIn }}>
            <LoeweDunkel visX={-170} visY={480} visH={1500} shiftX={lionShift} opacity={0.68} />
          </AbsoluteFill>

          {/* ===== Logo (immer Bilddatei) ===== */}
          <div style={{ position: "absolute", left: COL_X, top: 190, ...rein(logoStart) }}>
            <Img src={staticFile("clients/man/logo-weiss.png")} style={{ width: 280 }} />
          </div>

          {/* ===== Kicker ===== */}
          <div
            style={{
              position: "absolute",
              left: COL_X,
              top: 388,
              fontFamily: FONT_TITLE,
              fontWeight: 700,
              fontSize: 40,
              letterSpacing: 4,
              color: "rgba(255,255,255,0.78)",
              textTransform: "uppercase",
              ...rein(kickerStart),
            }}
          >
            {kicker}
          </div>

          {/* ===== Berufstitel ===== */}
          <div style={{ position: "absolute", left: COL_X, top: 462, width: 900 }}>
            {headLines.map((line, i) => (
              <div
                key={i}
                style={{
                  fontFamily: FONT_TITLE,
                  fontWeight: 700,
                  fontSize: 116,
                  lineHeight: 1.05,
                  letterSpacing: 1,
                  color: WHITE,
                  textTransform: "uppercase",
                  whiteSpace: "nowrap",
                  ...rein(headStart + i * F(0.2)),
                }}
              >
                {line}
              </div>
            ))}
            <div
              style={{
                marginTop: 14,
                fontFamily: FONT_BODY,
                fontWeight: 500,
                fontSize: 36,
                letterSpacing: 3,
                color: "rgba(255,255,255,0.65)",
                ...rein(suffixStart, 12),
              }}
            >
              {headlineSuffix}
            </div>
          </div>

          {/* ===== Benefits — man.eu-Listen-Token: roter Vertikal-Balken ===== */}
          {benefits.length > 0 && (
            <div style={{ position: "absolute", left: COL_X, top: 840 }}>
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  top: 6,
                  width: 6,
                  height: benefits.length * 58 - 14,
                  background: MAN_RED,
                  opacity: interpolate(frame, [benefitsStart, benefitsStart + F(0.3)], [0, 1], CLAMP),
                }}
              />
              {benefits.map((b, i) => (
                <div
                  key={i}
                  style={{
                    paddingLeft: 34,
                    height: 58,
                    display: "flex",
                    alignItems: "center",
                    fontFamily: FONT_BODY,
                    fontWeight: 500,
                    fontSize: 36,
                    color: "rgba(255,255,255,0.92)",
                    ...rein(benefitsStart + i * F(0.13), 14),
                  }}
                >
                  {b}
                </div>
              ))}
            </div>
          )}

          {/* ===== Claim + roter Balken + CTA (wie Wartezimmer-Endcard) ===== */}
          <div style={{ position: "absolute", left: COL_X, top: 1170, width: 900 }}>
            {claimZeilen.map((z, i) => (
              <div
                key={i}
                style={{
                  fontFamily: FONT_TITLE,
                  fontWeight: 700,
                  fontSize: 74,
                  lineHeight: 1.1,
                  letterSpacing: 2,
                  color: WHITE,
                  textTransform: "uppercase",
                  whiteSpace: "nowrap",
                  ...rein(claimStart + i * F(0.17)),
                }}
              >
                <Markup text={z} />
              </div>
            ))}
            <div
              style={{
                marginTop: 34,
                width: 320 * barP,
                height: 6,
                background: MAN_RED,
              }}
            />
            <div
              style={{
                marginTop: 30,
                fontFamily: FONT_TITLE,
                fontWeight: 700,
                fontSize: 46,
                letterSpacing: 4,
                color: WHITE,
                textTransform: "uppercase",
                whiteSpace: "nowrap",
                ...rein(ctaStart, 14),
              }}
            >
              {ctaText}
            </div>
            {ctaSub !== "" && (
              <div
                style={{
                  marginTop: 14,
                  fontFamily: FONT_BODY,
                  fontWeight: 500,
                  fontSize: 32,
                  letterSpacing: 2,
                  color: "rgba(255,255,255,0.65)",
                  textTransform: "uppercase",
                  whiteSpace: "nowrap",
                  ...rein(ctaStart + F(0.2), 12),
                }}
              >
                {ctaSub}
              </div>
            )}
          </div>

          {/* ===== QR rechts neben den Benefits (Ziel jobs.man.eu) ===== */}
          {zeigeQr && (
            <div style={{ position: "absolute", left: 690, top: 836, ...rein(qrStart, 16) }}>
              <Img
                src={staticFile("clients/man/wz/qr-jobs-man-eu.png")}
                style={{ width: 280, height: 280, display: "block" }}
              />
              <div
                style={{
                  marginTop: 16,
                  width: 280,
                  textAlign: "center",
                  fontFamily: FONT_TITLE,
                  fontWeight: 700,
                  fontSize: 28,
                  letterSpacing: 3,
                  color: WHITE,
                }}
              >
                {qrLabel}
              </div>
            </div>
          )}
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
