// ============================================================
// Client: NIRO Demo — Project: Recruiting-Overlay-Test
// End-to-End-Test des neuen Werkzeugkastens (19.09.2026):
// Alpha-Overlay 9:16 (ProRes 4444) für ein Recruiting-Reel —
//   1. Lower Third nach Craft-Referenz (Balken → Name → Rolle, Hold, Exit)
//   2. O-Ton-Zitatkarte (Lesereihenfolge, eine Hervorhebung via Remocn
//      MarkerHighlight, Autor zuletzt)
//   3. Endcard (Remocn SoftBlurIn + PerCharacterRise)
// Motion-Personality: Corporate (Easing „emphasized", Spring damping 20,
// kein Overshoot, Enter ≈ 10 f, Exit ≈ 8 f, Stagger 4 f).
// Alle Elemente liegen im Band unter der Face Zone und in der Safe Zone
// (9:16: y ≈ 45–57,5 % der Höhe) — geprüft mit review.showGuides.
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import { z } from "zod";
import { loadFont as loadRoboto } from "@remotion/google-fonts/Roboto";
import { CIProvider, useCI } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { getOverlayBandPixels } from "../../../../core/format-utils";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { EASING_PRESETS } from "../../../../utils/easing";
import { useExit } from "../../../../utils/useExit";
import brandJson from "../../brand.json";

// --- Remocn ---
import { MarkerHighlight } from "@/components/remocn/marker-highlight";
import { SoftBlurIn } from "@/components/remocn/soft-blur-in";
import { PerCharacterRise } from "@/components/remocn/per-character-rise";

const ci = loadBrand("niro-demo", brandJson as any);

// --- Fonts: Meutas lokal (Titel), Roboto (Fließtext) ---
const { fontFamily: robotoFamily } = loadRoboto("normal", { weights: ["400", "500"], subsets: ["latin"] });
for (const face of [
  { weight: 500, file: "Meutas-Medium.otf" },
  { weight: 700, file: "Meutas-Bold.otf" },
  { weight: 800, file: "Meutas-ExtraBold.otf" },
]) {
  const style = document.createElement("style");
  style.textContent = `@font-face { font-family: "Meutas"; font-weight: ${face.weight}; src: url("${staticFile(`fonts/${face.file}`)}") format("opentype"); }`;
  document.head.appendChild(style);
}
const FONT_TITLE = '"Meutas", sans-serif';
const FONT_BODY = `${robotoFamily}, sans-serif`;
const ROOT_STYLE = { "--font-geist-sans": FONT_TITLE } as React.CSSProperties;

// --- Motion-Personality: Corporate ---
const CORP = {
  spring: { damping: 20, stiffness: 170, mass: 0.7 }, // settelt in ~10 f, kein Overshoot
  ease: EASING_PRESETS.emphasized, // cubic-bezier(0.2, 0, 0, 1)
  stagger: 4,
  exitFrames: 8,
} as const;

// =============================================================
// SCHEMA
// =============================================================

const timingSchema = z.object({
  startSec: z.number().step(0.1).describe("Start (Sekunden)"),
  durationSec: z.number().step(0.1).describe("Dauer (Sekunden)"),
});

export const recruitingOverlayTestSchema = projectPropsSchema.extend({
  lowerThird: timingSchema.extend({
    name: z.string().describe("Name"),
    role: z.string().describe("Rolle / Position"),
  }),
  quote: timingSchema.extend({
    line1: z.string().describe("Zitat Zeile 1"),
    line2Before: z.string().describe("Zeile 2 vor der Hervorhebung (Leerzeichen am Ende)"),
    line2Highlight: z.string().describe("Hervorhebung (wörtlich aus dem O-Ton)"),
    line2After: z.string().describe("Zeile 2 nach der Hervorhebung"),
    author: z.string().describe("Autor · Rolle · Firma"),
  }),
  endCard: timingSchema.extend({
    cta: z.string().describe("CTA"),
    website: z.string().describe("Website"),
  }),
});

type RecruitingOverlayTestProps = z.infer<typeof recruitingOverlayTestSchema>;

export const recruitingOverlayTestDefaults: RecruitingOverlayTestProps = {
  format: "portrait",
  fps: 30,
  durationInSeconds: 14,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  lowerThird: { startSec: 0.5, durationSec: 5, name: "Lena Hoffmann", role: "Kfz-Mechatronikerin · 2. Lehrjahr" },
  quote: {
    startSec: 6,
    durationSec: 4.5,
    line1: "„Hier lernt man jeden Tag was Neues —",
    line2Before: "und das ",
    line2Highlight: "Team steht hinter dir",
    line2After: ".“",
    author: "Lena Hoffmann · Auszubildende · NIRO Demo GmbH",
  },
  endCard: { startSec: 11, durationSec: 3, cta: "Jetzt bewerben", website: "niro-demo.de/ausbildung" },
};

// =============================================================
// BAUSTEINE
// =============================================================

/** Corporate-Enter: Spring 0→1 ab delay, Exit über useExit (schneller als Enter). */
function useCorpEnterExit(delay: number) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - delay, fps, config: CORP.spring });
  const { exitOpacity, exitSlide } = useExit({ exitFrames: CORP.exitFrames, slidePx: 16 });
  return { enter, opacity: enter * exitOpacity, exitSlide };
}

/** Band unter der Face Zone, innerhalb der Safe Zone — dort leben alle Overlays (Hausfunktion in format-utils). */
function useOverlayBand() {
  const { width, height } = useVideoConfig();
  return getOverlayBandPixels("portrait", undefined, { width, height });
}

// --- 1. Lower Third (nach references/iart/lower-thirds--lower-third-component.md) ---

const LowerThird: React.FC<{ name: string; role: string }> = ({ name, role }) => {
  const c = useCI();
  const { width } = useVideoConfig();
  const band = useOverlayBand();
  const bar = useCorpEnterExit(0);
  const nameA = useCorpEnterExit(CORP.stagger);
  const roleA = useCorpEnterExit(CORP.stagger * 2);
  const nameSize = Math.round(width * 0.052);
  const roleSize = Math.round(nameSize / 1.7); // Name ≥ 1,6× Rolle
  const slide = (enter: number) => interpolate(enter, [0, 1], [-28, 0]);

  return (
    <div
      style={{
        position: "absolute",
        left: band.left,
        top: band.top + Math.round(band.height * 0.18),
        opacity: bar.opacity,
        transform: `translate(${slide(bar.enter)}px, ${bar.exitSlide}px)`,
      }}
    >
      <div
        style={{
          background: "rgba(26, 33, 29, 0.86)", // ci.secondary mit Alpha — Lesbarkeit über jedem Footage
          borderLeft: `${Math.round(width * 0.006)}px solid ${c.colors.primary}`,
          borderRadius: Math.round(width * 0.008),
          padding: `${Math.round(width * 0.014)}px ${Math.round(width * 0.024)}px ${Math.round(width * 0.016)}px`,
        }}
      >
        <div
          style={{
            opacity: nameA.opacity,
            transform: `translateX(${slide(nameA.enter)}px)`,
            fontFamily: FONT_TITLE,
            fontWeight: 800,
            fontSize: nameSize,
            lineHeight: 1.1,
            color: "#FFFFFF",
            letterSpacing: "-0.01em",
            whiteSpace: "nowrap",
          }}
        >
          {name}
        </div>
        <div
          style={{
            opacity: roleA.opacity,
            transform: `translateX(${slide(roleA.enter)}px)`,
            fontFamily: FONT_BODY,
            fontWeight: 500,
            fontSize: roleSize,
            lineHeight: 1.25,
            marginTop: Math.round(roleSize * 0.2),
            color: c.colors.primary,
            whiteSpace: "nowrap",
          }}
        >
          {role}
        </div>
      </div>
    </div>
  );
};

// --- 2. Zitatkarte (nach references/iart/testimonial-video.md: Lesereihenfolge, eine Hervorhebung, Autor zuletzt) ---

const QuoteCard: React.FC<{
  line1: string;
  line2Before: string;
  line2Highlight: string;
  line2After: string;
  author: string;
}> = ({ line1, line2Before, line2Highlight, line2After, author }) => {
  const c = useCI();
  const { width } = useVideoConfig();
  const band = useOverlayBand();
  const card = useCorpEnterExit(0);
  const l1 = useCorpEnterExit(CORP.stagger * 2);
  const l2 = useCorpEnterExit(CORP.stagger * 3); // Lesereihenfolge: Zeile 2 nach Zeile 1
  const author_ = useCorpEnterExit(CORP.stagger * 2 + 34); // nach der Marker-Feder (Marker startet bei 15 f in der Komponente)
  const quoteSize = Math.round(width * 0.04);
  const authorSize = Math.round(width * 0.024);
  const rise = (enter: number) => interpolate(enter, [0, 1], [18, 0]);

  return (
    <div
      style={{
        position: "absolute",
        left: band.left,
        width: band.width,
        top: band.top,
        height: band.height,
        opacity: card.opacity,
        transform: `translateY(${rise(card.enter) + card.exitSlide}px)`,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(26, 33, 29, 0.86)",
          borderRadius: Math.round(width * 0.012),
        }}
      />
      {/* Zeile 1 */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: Math.round(band.height * 0.14),
          textAlign: "center",
          opacity: l1.opacity,
          transform: `translateY(${rise(l1.enter)}px)`,
          fontFamily: FONT_TITLE,
          fontWeight: 700,
          fontSize: quoteSize,
          lineHeight: 1.15,
          color: "#FFFFFF",
        }}
      >
        {line1}
      </div>
      {/* Zeile 2 mit Marker — Remocn MarkerHighlight füllt seinen Container, deshalb eigene Box */}
      <Sequence from={CORP.stagger * 3} layout="none">
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: Math.round(band.height * 0.36),
            height: Math.round(band.height * 0.3),
            opacity: l2.opacity,
            transform: `translateY(${rise(l2.enter)}px)`,
          }}
        >
          <MarkerHighlight
            before={line2Before}
            highlight={line2Highlight}
            after={line2After}
            markerColor={c.colors.primary}
            baseColor="#FFFFFF"
            highlightedTextColor={c.colors.secondary}
            fontSize={quoteSize}
            fontWeight={700}
          />
        </div>
      </Sequence>
      {/* Autor zuletzt — der Beweis */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: Math.round(band.height * 0.13),
          textAlign: "center",
          opacity: author_.opacity,
          transform: `translateY(${rise(author_.enter)}px)`,
          fontFamily: FONT_BODY,
          fontWeight: 400,
          fontSize: authorSize,
          color: "rgba(255,255,255,0.7)",
        }}
      >
        {author}
      </div>
    </div>
  );
};

// --- 3. Endcard (Remocn SoftBlurIn + PerCharacterRise, Exit über useExit) ---

const EndCard: React.FC<{ cta: string; website: string }> = ({ cta, website }) => {
  const c = useCI();
  const { width } = useVideoConfig();
  const band = useOverlayBand();
  const { exitOpacity, exitSlide } = useExit({ exitFrames: CORP.exitFrames, slidePx: 16 });

  return (
    <div
      style={{
        position: "absolute",
        left: band.left,
        width: band.width,
        top: band.top,
        height: band.height,
        opacity: exitOpacity,
        transform: `translateY(${exitSlide}px)`,
      }}
    >
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: Math.round(band.height * 0.55) }}>
        <SoftBlurIn text={cta} fontSize={Math.round(width * 0.075)} color="#FFFFFF" fontWeight={800} />
      </div>
      <Sequence from={CORP.stagger * 3} layout="none">
        <div style={{ position: "absolute", left: 0, right: 0, top: Math.round(band.height * 0.55), height: Math.round(band.height * 0.4) }}>
          <PerCharacterRise text={website} fontSize={Math.round(width * 0.036)} color={c.colors.primary} fontWeight={600} />
        </div>
      </Sequence>
    </div>
  );
};

// =============================================================
// KOMPOSITION
// =============================================================

export const RecruitingOverlayTest: React.FC<RecruitingOverlayTestProps> = ({ lowerThird, quote, endCard, review }) => {
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.round(sec * fps);

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={ROOT_STYLE}>
        <Sequence from={s(lowerThird.startSec)} durationInFrames={s(lowerThird.durationSec)} name="Lower Third">
          <LowerThird name={lowerThird.name} role={lowerThird.role} />
        </Sequence>

        <Sequence from={s(quote.startSec)} durationInFrames={s(quote.durationSec)} name="Zitatkarte">
          <QuoteCard
            line1={quote.line1}
            line2Before={quote.line2Before}
            line2Highlight={quote.line2Highlight}
            line2After={quote.line2After}
            author={quote.author}
          />
        </Sequence>

        <Sequence from={s(endCard.startSec)} durationInFrames={s(endCard.durationSec)} name="Endcard">
          <EndCard cta={endCard.cta} website={endCard.website} />
        </Sequence>

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
