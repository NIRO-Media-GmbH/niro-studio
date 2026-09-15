// ============================================================
// Dold Holzwerke — Recruiting Endcard
// Logo groß + CTA „Jetzt in unter 1 Minute bewerben"
// 9:16 portrait, 10s @ 30fps — Overlay für unscharfen Drohnenshot
// Bewusst simpel: Logo → Slogan → CTA-Pille, alles weiche Fades.
// Nach ~2 s steht alles — hinten beliebig kürzbar (kein Outro)
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { z } from "zod";
import { loadFont as loadRoboto } from "@remotion/google-fonts/Roboto";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import brandJson from "../../brand.json";

const ci = loadBrand("dold", brandJson as any);
const { fontFamily: robotoFamily } = loadRoboto();

// --- Colors ---
const GREEN = "#00694D";
const WHITE = "#FFFFFF";

// --- Spring configs ---
const SMOOTH_SPRING = { damping: 18, stiffness: 120, mass: 1 };
const GENTLE_SPRING = { damping: 22, stiffness: 100, mass: 1 };
const SNAPPY_SPRING = { damping: 14, stiffness: 160, mass: 1 };

// --- Schema ---
const posSchema = z.object({ x: z.number(), y: z.number() });

export const doldEndcardSchema = projectPropsSchema.extend({
  logoColor: z.enum(["white", "green"]).describe("Logo-Farbe (weiß auf Footage, grün auf hell)"),
  ctaStyle: z.enum(["white", "green"]).describe("CTA-Pille: weiß mit grüner Schrift oder grün mit weißer"),
  logoWidth: z.number().min(200).max(940),
  markShiftX: z.number().describe("Optischer Ausgleich: nur die dold-Marke horizontal (px, negativ = links)"),
  logoPos: posSchema,
  showSlogan: z.boolean(),
  jobEyebrow: z.string().describe("Kleine Zeile über dem Jobtitel, z. B. Wir suchen"),
  jobTitle: z.string().describe("Gesuchte Rolle — leer lassen blendet den Job-Block aus"),
  jobSuffix: z.string().describe("Zusatz hinter der Rolle, z. B. (m/w/d)"),
  jobPos: posSchema,
  ctaText: z.string(),
  ctaPos: posSchema,
  website: z.string(),
  websitePos: posSchema,
});

export type Props = z.infer<typeof doldEndcardSchema>;

export const doldEndcardDefaults: Props = {
  format: "portrait" as const,
  fps: 30 as const,
  durationInSeconds: 10,
  transparent: false,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  logoColor: "white" as const,
  ctaStyle: "white" as const,
  logoWidth: 660,
  // Optischer Ausgleich der Schräglage, Wert per Abnahme 2026-08-20 (+30 px bei 660er Breite)
  markShiftX: 30,
  logoPos: { x: 0, y: 0 },
  showSlogan: true,
  jobEyebrow: "Wir suchen",
  jobTitle: "Baggerfahrer",
  jobSuffix: "(m/w/d)",
  jobPos: { x: 0, y: 0 },
  ctaText: "Jetzt in unter 1 Minute bewerben",
  ctaPos: { x: 0, y: 0 },
  website: "dold-holzwerke.com",
  websitePos: { x: 0, y: 0 },
};

// ============================================================
// Logo-Pfade — 1:1 aus dem Original-SVG (dold-logo-1.svg, viewBox 0 0 113 80)
// ============================================================
const MARK = {
  barTop: "M107.443 0L104.809 9.488L18.8711 9.57L21.2311 0H107.443Z",
  slash: "M64.0021 66.9805L54.5391 67.0355L69.1161 12.7695L78.4981 12.8245L64.0021 66.9805Z",
  barBottom: "M88.563 70.3438L85.937 79.9157L0 79.9987L2.352 70.3438H88.563Z",
  letterO:
    "M52.064 63.2651C51.48 65.4061 49.272 67.1421 47.131 67.1421L33.81 67.1301C31.669 67.1301 29.386 65.0791 29.934 63.2531L38.419 32.6021C39.002 30.4611 41.211 28.7261 43.353 28.7261L56.554 28.7031C58.695 28.7031 60.978 30.5491 60.431 32.5791L52.064 63.2651ZM49.308 40.0661C49.566 39.1091 48.97 38.3301 47.979 38.3281C46.987 38.3241 45.974 39.0961 45.716 40.0531L41.46 55.8561C41.203 56.8131 41.797 57.5911 42.79 57.5951C43.782 57.5981 44.795 56.8261 45.053 55.8691L49.308 40.0661Z",
  letterD1:
    "M26.0916 67.1415L8.61155 67.1295C6.47055 67.1295 4.18755 65.0785 4.73455 63.2525L13.2205 32.6015C13.8035 30.4605 16.0126 28.7255 18.1536 28.7255L26.6376 28.7025L31.1776 12.7695H40.7785L26.0916 67.1415ZM23.5616 40.0655C23.8196 39.1085 23.2246 38.3295 22.2316 38.3275C21.2396 38.3235 20.2265 39.0955 19.9685 40.0525L15.7125 55.8555C15.4545 56.8125 16.0495 57.5905 17.0415 57.5945C18.0335 57.5975 19.0465 56.8255 19.3055 55.8685L23.5616 40.0655Z",
  letterD2:
    "M89.4099 67.1415L71.9309 67.1295C69.7899 67.1295 67.5079 65.0785 68.0549 63.2525L76.5399 32.6015C77.1229 30.4605 79.3319 28.7255 81.4739 28.7255L89.9579 28.7025L94.4979 12.7695H104.099L89.4099 67.1415ZM86.8799 40.0655C87.1379 39.1085 86.5429 38.3295 85.5509 38.3275C84.5589 38.3235 83.5469 39.0955 83.2869 40.0525L79.0319 55.8555C78.7739 56.8125 79.3699 57.5905 80.3629 57.5945C81.3539 57.5975 82.3669 56.8255 82.6249 55.8685L86.8799 40.0655Z",
  reg:
    "M105.382 16.3673C106.104 14.2313 108.367 12.6562 110.415 12.6562C112.444 12.6562 113.644 14.2313 112.923 16.3673C112.195 18.5233 109.931 20.0982 107.904 20.0982C105.855 20.0982 104.654 18.5223 105.382 16.3673ZM108.113 19.4783C109.797 19.4783 111.571 18.1593 112.175 16.3673C112.771 14.6053 111.889 13.2762 110.206 13.2762C108.502 13.2762 106.725 14.6053 106.13 16.3673C105.525 18.1583 106.41 19.4783 108.113 19.4783ZM107.647 18.5222H106.997L108.446 14.2302H110.081C111.095 14.2302 111.47 14.6043 111.185 15.4513C110.925 16.2193 110.331 16.5542 109.673 16.6322L110.256 18.5222H109.527L109.023 16.6623H108.274L107.647 18.5222ZM109.239 16.1112C109.789 16.1112 110.296 16.0712 110.518 15.4122C110.698 14.8802 110.249 14.7822 109.796 14.7822H108.91L108.462 16.1112H109.239Z",
};

// Slogan „INNOVATION IN HOLZ" — 1:1 aus dold-logo.svg (x 140–320, y 33.8–46.6)
const SLOGAN_LETTERS = [
  "M140.262,46.601l3.579-12.714h2.173l-3.578,12.714H140.262z",
  "M153.613,46.601l-1.923-5.371l-1.186-3.58c-0.018,0-0.038,0.018-0.056,0.018l-2.48,8.934h-2.174 l3.597-12.714h1.991c0.5,1.388,0.981,2.777,2.396,6.851l0.71,2.119c0.018,0,0.016,0.018,0.034,0.018l2.522-8.988h2.138 l-3.579,12.714H153.613z",
  "M166.774,46.601l-1.923-5.371l-1.186-3.58c-0.018,0-0.038,0.018-0.057,0.018l-2.48,8.934h-2.174 l3.598-12.714h1.991c0.499,1.388,0.98,2.777,2.396,6.851l0.711,2.119c0.018,0,0.016,0.018,0.035,0.018l2.521-8.988h2.137 l-3.578,12.714H166.774z",
  "M183.428,38.143c-0.052,0.585-0.795,3.015-1.003,3.727c-0.858,2.923-2.56,4.841-5.665,4.841 c-3.271,0-4.373-2.01-3.912-4.365c0.053-0.604,0.818-3.088,1.023-3.764c0.777-2.612,2.264-4.786,5.607-4.786 C182.291,33.795,183.922,35.623,183.428,38.143z M176.092,38.472l-1.001,3.507c-0.374,1.353-0.169,2.759,1.933,2.759 c1.662,0,2.664-1.225,3.146-2.759c0.204-0.657,1.024-3.36,1.071-3.891c0.225-1.315-0.527-2.338-2.043-2.338 C177.298,35.75,176.459,37.193,176.092,38.472z",
  "M188.209,46.601h-1.717l-0.66-12.714h2.266l0.147,5.828l0.034,3.379h0.091l1.921-3.379l3.415-5.828h2.375 L188.209,46.601z",
  "M201.254,46.601l-0.156-2.812h-4.64l-1.78,2.812h-2.339l8.219-12.714h1.899l1.062,12.714H201.254z M200.866,39.331l-0.073-2.704h-0.037l-1.547,2.648l-1.6,2.631h3.379L200.866,39.331z",
  "M211.721,35.805l-3.045,10.796h-2.156l3.027-10.796h-3.471l0.551-1.918h9.116l-0.552,1.918H211.721z",
  "M213.833,46.601l3.579-12.714h2.174l-3.578,12.714H213.833z",
  "M230.676,38.143c-0.052,0.585-0.794,3.015-1.003,3.727c-0.858,2.923-2.56,4.841-5.666,4.841 c-3.27,0-4.373-2.01-3.911-4.365c0.053-0.604,0.818-3.088,1.023-3.764c0.777-2.612,2.264-4.786,5.607-4.786 C229.539,33.795,231.17,35.623,230.676,38.143z M223.34,38.472l-1.002,3.507c-0.373,1.353-0.168,2.759,1.934,2.759 c1.662,0,2.664-1.225,3.145-2.759c0.205-0.657,1.025-3.36,1.072-3.891c0.225-1.315-0.527-2.338-2.043-2.338 C224.547,35.75,223.707,37.193,223.34,38.472z",
  "M239.016,46.601l-1.923-5.371l-1.186-3.58c-0.019,0-0.038,0.018-0.056,0.018l-2.48,8.934h-2.174 l3.597-12.714h1.991c0.5,1.388,0.981,2.777,2.396,6.851l0.71,2.119c0.019,0,0.017,0.018,0.034,0.018l2.522-8.988h2.138 l-3.578,12.714H239.016z",
  "M249.906,46.601l3.578-12.714h2.174l-3.578,12.714H249.906z",
  "M263.257,46.601l-1.924-5.371l-1.185-3.58c-0.019,0-0.038,0.018-0.057,0.018l-2.48,8.934h-2.174 l3.598-12.714h1.99c0.5,1.388,0.981,2.777,2.396,6.851l0.71,2.119c0.019,0,0.017,0.018,0.034,0.018l2.523-8.988h2.137 l-3.579,12.714H263.257z",
  "M281.125,46.601l1.535-5.443h-4.787l-1.535,5.443h-2.174l3.598-12.714h2.154l-1.488,5.333h4.786 l1.507-5.333h2.156l-3.578,12.714H281.125z",
  "M297.969,38.143c-0.051,0.585-0.793,3.015-1.002,3.727c-0.857,2.923-2.561,4.841-5.666,4.841 c-3.27,0-4.373-2.01-3.91-4.365c0.052-0.604,0.818-3.088,1.022-3.764c0.777-2.612,2.263-4.786,5.606-4.786 C296.833,33.795,298.463,35.623,297.969,38.143z M290.633,38.472l-1.001,3.507c-0.374,1.353-0.169,2.759,1.933,2.759 c1.662,0,2.664-1.225,3.146-2.759c0.205-0.657,1.025-3.36,1.071-3.891c0.225-1.315-0.526-2.338-2.042-2.338 C291.84,35.75,291.001,37.193,290.633,38.472z",
  "M298.491,46.601l3.597-12.714h2.156l-3.02,10.705h6.175l-0.542,2.01H298.491z",
  "M308.336,46.601l0.529-1.882l8.288-8.914H311.6l0.533-1.918h8.129l-0.502,1.772l-8.307,8.933h5.79 l-0.56,2.01H308.336z",
];

const clamp01 = (v: number) => interpolate(v, [0, 1], [0, 1], {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});

// ============================================================
// DOLD-Marke — als Ganzes: weicher Fade + minimales Aufziehen
// ============================================================
const DoldMark: React.FC<{
  width: number;
  color: string;
  progress: number;
}> = ({ width, color, progress }) => (
  <svg
    viewBox="0 0 113 80"
    style={{ width, height: "auto", display: "block", overflow: "visible" }}
  >
    <g
      style={{
        opacity: clamp01(progress),
        transform: `scale(${interpolate(progress, [0, 1], [0.96, 1])})`,
        transformBox: "fill-box",
        transformOrigin: "center",
      }}
    >
      <path d={MARK.barTop} fill={color} />
      <path d={MARK.barBottom} fill={color} />
      <path d={MARK.letterD1} fill={color} />
      <path d={MARK.letterO} fill={color} />
      <path d={MARK.slash} fill={color} />
      <path d={MARK.letterD2} fill={color} />
      <path d={MARK.reg} fill={color} />
    </g>
  </svg>
);

// ============================================================
// Slogan „INNOVATION IN HOLZ" — eine Zeile, weicher Fade
// ============================================================
const DoldSlogan: React.FC<{
  width: number;
  color: string;
  progress: number;
}> = ({ width, color, progress }) => (
  <svg
    viewBox="139.5 33.2 181.5 14"
    style={{ width, height: "auto", display: "block", overflow: "visible" }}
  >
    <g
      style={{
        opacity: clamp01(progress),
        transform: `translateY(${interpolate(progress, [0, 1], [3, 0])}px)`,
      }}
    >
      {SLOGAN_LETTERS.map((d, i) => (
        <path key={i} d={d} fill={color} />
      ))}
    </g>
  </svg>
);

// ============================================================
// Stand-in-Hintergrund — Platzhalter für den unscharfen Drohnenshot
// (nur wenn transparent=false; Lieferung erfolgt als Alpha-Overlay)
// ============================================================
const StandInBackground: React.FC = () => (
  <AbsoluteFill style={{ background: "linear-gradient(165deg, #3A5748 0%, #22392E 55%, #14261D 100%)" }}>
    <div
      style={{
        position: "absolute",
        top: -200,
        left: -150,
        width: 900,
        height: 700,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(180,205,180,0.35), transparent 70%)",
        filter: "blur(90px)",
      }}
    />
    <div
      style={{
        position: "absolute",
        bottom: -100,
        right: -200,
        width: 800,
        height: 800,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(30,60,40,0.8), transparent 70%)",
        filter: "blur(80px)",
      }}
    />
    <AbsoluteFill
      style={{ background: "radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.35) 100%)" }}
    />
  </AbsoluteFill>
);

// ============================================================
// Main Composition
// ============================================================
export const DoldEndcard: React.FC<Props> = ({
  review,
  transparent,
  logoColor,
  ctaStyle,
  logoWidth,
  markShiftX,
  logoPos,
  showSlogan,
  jobEyebrow,
  jobTitle,
  jobSuffix,
  jobPos,
  ctaText,
  ctaPos,
  website,
  websitePos,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const markColor = logoColor === "white" ? WHITE : GREEN;
  const pillBg = ctaStyle === "white" ? WHITE : GREEN;
  const pillText = ctaStyle === "white" ? GREEN : WHITE;

  // --- Animation delays (frames @ 30fps) — Pille ab ~0,9 s, ab ~2,2 s steht alles ---
  const LOGO_DELAY = 4;
  const SLOGAN_DELAY = 12;
  const JOB_DELAY = 20;
  const CTA_DELAY = 28;
  const CTA_TEXT_DELAY = 32;
  const WEBSITE_DELAY = 38;

  const logoProg = spring({ frame, fps, config: GENTLE_SPRING, delay: LOGO_DELAY });
  const sloganProg = spring({ frame, fps, config: GENTLE_SPRING, delay: SLOGAN_DELAY });
  const jobProg = spring({ frame, fps, config: GENTLE_SPRING, delay: JOB_DELAY });
  const ctaPillProg = spring({ frame, fps, config: SMOOTH_SPRING, delay: CTA_DELAY });
  const ctaTextProg = spring({ frame, fps, config: SNAPPY_SPRING, delay: CTA_TEXT_DELAY });
  const websiteProg = spring({ frame, fps, config: GENTLE_SPRING, delay: WEBSITE_DELAY });

  const sloganWidth = Math.round(logoWidth * 0.94);

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill>
        {!transparent && <StandInBackground />}

        {/* ===== Inhalt komplett in der Reels-Safe-Zone (oben 7 % bis 57,5 %),
                 darin vertikal zentriert ===== */}
        <div
          style={{
            position: "absolute",
            top: "7%",
            left: "5%",
            right: "5%",
            height: "50.5%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {/* Logo-Block: Marke + Slogan */}
          <div
            style={{
              transform: `translate(${logoPos.x}px, ${logoPos.y}px)`,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 48,
              filter: "drop-shadow(0 6px 30px rgba(0,0,0,0.30))",
            }}
          >
            <div style={{ transform: `translateX(${markShiftX}px)` }}>
              <DoldMark width={logoWidth} color={markColor} progress={logoProg} />
            </div>
            {showSlogan && (
              <DoldSlogan width={sloganWidth} color={markColor} progress={sloganProg} />
            )}
          </div>

          {/* Job-Ansage: kleine Zeile + gesuchte Rolle */}
          {jobTitle !== "" && (
            <>
              <div style={{ height: 60 }} />
              <div
                style={{
                  transform: `translate(${jobPos.x}px, ${jobPos.y + interpolate(jobProg, [0, 1], [10, 0])}px)`,
                  opacity: clamp01(jobProg),
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 10,
                  textShadow: "0 2px 15px rgba(0,0,0,0.25)",
                }}
              >
                <div
                  style={{
                    fontFamily: robotoFamily,
                    fontSize: 26,
                    fontWeight: 700,
                    color: markColor,
                    letterSpacing: 7,
                    textTransform: "uppercase",
                    opacity: 0.85,
                  }}
                >
                  {jobEyebrow}
                </div>
                <div
                  style={{
                    fontFamily: robotoFamily,
                    fontSize: 52,
                    fontWeight: 900,
                    color: markColor,
                    letterSpacing: 2,
                    textTransform: "uppercase",
                    whiteSpace: "nowrap",
                    display: "flex",
                    alignItems: "baseline",
                    gap: 16,
                  }}
                >
                  <span>{jobTitle}</span>
                  {jobSuffix !== "" && (
                    <span style={{ fontSize: 30, fontWeight: 500, textTransform: "none" }}>
                      {jobSuffix}
                    </span>
                  )}
                </div>
              </div>
            </>
          )}

          {/* CTA-Pille (Hintergrund ragt 20/44 px über den Text hinaus) */}
          <div style={{ height: jobTitle !== "" ? 64 : 84 }} />
          <div style={{ position: "relative", transform: `translate(${ctaPos.x}px, ${ctaPos.y}px)` }}>
            <div
              style={{
                position: "absolute",
                inset: "-20px -44px",
                backgroundColor: pillBg,
                borderRadius: 60,
                transform: `scaleX(${clamp01(ctaPillProg)})`,
                boxShadow: "0 6px 30px rgba(0,0,0,0.25)",
              }}
            />
            <div
              style={{
                position: "relative",
                fontFamily: robotoFamily,
                fontSize: 36,
                fontWeight: 900,
                color: pillText,
                letterSpacing: 1.5,
                textTransform: "uppercase",
                textAlign: "center",
                whiteSpace: "nowrap",
                opacity: clamp01(ctaTextProg),
              }}
            >
              {ctaText}
            </div>
          </div>

          {/* Website */}
          {website !== "" && (
            <>
              <div style={{ height: 56 }} />
              <div
                style={{
                  transform: `translate(${websitePos.x}px, ${websitePos.y + interpolate(websiteProg, [0, 1], [12, 0])}px)`,
                  fontFamily: robotoFamily,
                  fontSize: 30,
                  fontWeight: 500,
                  color: markColor,
                  letterSpacing: 3,
                  opacity: clamp01(websiteProg) * 0.9,
                  textShadow: "0 2px 15px rgba(0,0,0,0.25)",
                }}
              >
                {website}
              </div>
            </>
          )}
        </div>

        {/* Review overlay */}
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
    </CIProvider>
  );
};
