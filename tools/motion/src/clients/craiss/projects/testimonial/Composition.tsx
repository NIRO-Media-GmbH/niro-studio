// ============================================================
// Craiss Generation Logistik — "05 Testimonial Video"
// Fahrer-Testimonial (Zusammenschnitt). Stand v3 (2026-09-11): Timing auf
// den Kunden-Schnitt V2 (NAS-Export ohne Animation, 1324 Frames = 52,96s).
// - Hook „ICH MAG MEINE ARBEIT." + Chip „LKW-FAHRER BEI CRAISS"
// - Zitat-Chips wortgetreu; „KEIN STRESS." entfällt (Kundenfeedback)
// - Flaggen-Staffel zur Kollegen-Aufzählung (wie Video 03)
// - Serien-CTA ab 46,64s auf dem Drohnen-Endshot (Schnitt 46,52s)
// - Ruhige Bewegung (SOFT-Feder, kurze Wege) wie Video 04 (Kundenfeedback)
//
// 9:16 portrait-4k (2160×3840), 25fps.
// Schnitte u. a.: 1,16 / 2,36 / 3,52 / 5,88 / 7,16 / 8,92 / … / 30,88 /
// 35,28 / 37,24 / 38,96 / 43,0 / 44,68 / 46,52 [Drohne].
// Gemeinsame Bausteine: ../../lib
// ============================================================

import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  Cta,
  Endcard,
  FlagsRow,
  FootageCompare,
  Hook,
  hookSchema,
  ctaSchema,
  flagsSchema,
  footageSchema,
  CTA_TEXTS,
  SOFT,
  FONT_BOLD,
  RED,
  WHITE,
} from "../../lib";
import brandJson from "../../brand.json";
import { z } from "zod";

const ci = loadBrand("craiss", brandJson as any);

const chipSchema = z.object({
  text: z.string().describe("Text"),
  startSec: z.number().step(0.04).describe("Start (Sek)"),
  endSec: z.number().step(0.04).describe("Ende inkl. Ausblenden (Sek)"),
  offsetY: z.number().step(1).describe("Y-Offset (px, Basis 1920)"),
});

export const craissTestimonialSchema = projectPropsSchema.extend({
  hook: hookSchema.describe("Hook (Headline + Chip)"),
  chips: z.array(chipSchema).describe("Zitat-Chips"),
  flags: flagsSchema.describe("Flaggen (Kollegen-Aufzählung)"),
  cta: ctaSchema.describe("CTA / Endcard"),
  ctaOpaque: z.boolean().describe("Endcard opak (Preview) statt transparent"),
  footage: footageSchema.describe("Footage-Vergleich"),
});

export type CraissTestimonialProps = z.infer<typeof craissTestimonialSchema>;

// Kunden-Schnitt V2, Neuexport 11.09. 18:46: 1315 Frames à 25fps = 52,6s.
// Gegenüber dem Export von 14:36 sind bei 16,96s 13 Frames („Kein Stress")
// herausgeschnitten → alles ab dort 0,52s früher (Bild-Abgleich Frame für Frame).
const VIDEO_SECONDS = 52.6;

export const craissTestimonialDefaults: CraissTestimonialProps = {
  format: "portrait-4k" as const,
  fps: 25 as const,
  durationInSeconds: VIDEO_SECONDS,
  transparent: true,
  review: {
    showGuides: false,
    showSafeZone: true,
    showFaceZone: true,
    showGrid: false,
    guideOpacity: 0.35,
  },
  hook: {
    // Gesprochener Opener „Ich mag meine Arbeit." 0,08–1,08.
    headline: "ICH MAG MEINE ARBEIT.",
    chip: "LKW-FAHRER BEI CRAISS",
    startSec: 0.24,
    endSec: 2.28,
    // Kundenfeedback „Texteinblendungen zu hoch": +60 wie Evas
    // Einblendungen in Video 04 — Headline sitzt unter dem Kragen (vorher 50).
    offsetY: 110,
  },
  // Zeiten und Höhen aus dem Kunden-Schnitt V2 übernommen (Differenz
  // animierter Schnitt minus Export ohne Animation, 2026-09-11): der
  // Cutter hat „JEDER TAG…" um 120 und „DIE FREIHEIT…" um 84 px tiefer
  // gesetzt und ab ~20 s alles um 47 Frames nach vorn gezogen.
  // „KEIN STRESS." entfällt (Kundenfeedback: Fokus reduzieren, nicht
  // zusätzlich einblenden).
  chips: [
    { text: "JEDER TAG IST EIN GUTER TAG.", startSec: 3.32, endSec: 5.8, offsetY: 120 },
    { text: "DIE FREIHEIT. DIE RUHE.", startSec: 6.88, endSec: 8.8, offsetY: 84 },
    // ab hier −0,52s (Neuexport 18:46, siehe VIDEO_SECONDS)
    { text: "JEDEN TAG ZU HAUSE.", startSec: 28.44, endSec: 30.32, offsetY: 0 },
    { text: "BEI CRAISS PASST'S.", startSec: 34.88, endSec: 36.6, offsetY: 0 },
  ],
  flags: {
    items: [
      { country: "HU" as const, label: "UNGARN", startSec: 39.64 },
      { country: "CZ" as const, label: "TSCHECHIEN", startSec: 40.44 },
      { country: "RO" as const, label: "RUMÄNIEN", startSec: 41.08 },
      { country: "LT" as const, label: "LITAUEN", startSec: 42.04 },
    ],
    startSec: 39.64,
    // LT hält über den Schnitt bei 42,48, raus vor dem Schnitt bei 44,16
    endSec: 43.52,
    offsetY: 0,
  },
  cta: {
    ...CTA_TEXTS,
    // Drohnen-Endshot ab 46,0 — CTA 3 Frames danach
    startSec: 46.12,
    offsetY: 0,
  },
  ctaOpaque: false,
  footage: {
    showInStudio: true,
    simulateBlur: false,
    renderInExport: false,
  },
};

export const craissTestimonialPreviewDefaults: CraissTestimonialProps = {
  ...craissTestimonialDefaults,
  transparent: false,
  // V2 endet auf der Drohne (kein schwarzer End-Shot mehr) → transparenter CTA
  ctaOpaque: false,
  footage: {
    showInStudio: true,
    simulateBlur: false,
    renderInExport: true,
  },
};

const FOOTAGE_SRC = "projects/craiss-testimonial/ohne-Animation/proxy/05_Testimonial_Video_V2_ohneAnim_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

// =============================================================
// Roter Text-Chip (Hook / Zitate) — kompakt, Lower-Third
// =============================================================

const RedChip: React.FC<{ chip: z.infer<typeof chipSchema> }> = ({ chip }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  const durFrames = F(chip.endSec - chip.startSec);

  // Ruhig (Kundenfeedback „hüpft zu stark"): SOFT-Feder, kaum Skalierung
  const inP = spring({ frame, fps, config: SOFT });
  const scale = interpolate(inP, [0, 1], [0.95, 1]);
  const inOp = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outOp = interpolate(frame, [durFrames - F(0.32), durFrames - 2], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const op = inOp * outOp;
  if (op <= 0) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 990 + chip.offsetY,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          backgroundColor: RED,
          borderRadius: 6,
          padding: "14px 34px",
          fontFamily: FONT_BOLD,
          fontSize: 42,
          letterSpacing: 2,
          color: WHITE,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          boxShadow: "0 6px 24px rgba(0,0,0,0.35)",
          opacity: op,
          transform: `scale(${scale})`,
        }}
      >
        {chip.text}
      </div>
    </div>
  );
};

// =============================================================
// Composition
// =============================================================

export const CraissTestimonial: React.FC<CraissTestimonialProps> = ({
  review,
  hook,
  chips,
  flags,
  cta,
  ctaOpaque,
  footage,
}) => {
  const { fps, width, durationInFrames } = useVideoConfig();
  const s = (sec: number) => Math.round(sec * fps);
  const S = width / BASE_W;

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
        {/* Footage endet vor Kompositionsende — Sequence begrenzt,
            damit OffthreadVideo nie hinter das Medienende seekt. */}
        <Sequence from={0} durationInFrames={s(VIDEO_SECONDS)} name="Footage">
          <FootageCompare src={FOOTAGE_SRC} footage={footage} ctaStartSec={999} />
        </Sequence>

        {/* Layout-Bühne 1080×1920 → uniform skaliert */}
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
          <Sequence from={s(hook.startSec)} durationInFrames={s(hook.endSec) - s(hook.startSec)} name="Hook">
            <Hook hook={hook} layout="lower" calm />
          </Sequence>

          {chips.map((chip, i) => (
            <Sequence key={i} from={s(chip.startSec)} durationInFrames={s(chip.endSec) - s(chip.startSec)} name={`Chip: ${chip.text}`}>
              <RedChip chip={chip} />
            </Sequence>
          ))}

          <Sequence from={s(flags.startSec)} durationInFrames={s(flags.endSec) - s(flags.startSec)} name="Flaggen">
            <FlagsRow flags={flags} calm />
          </Sequence>

          <Sequence from={s(cta.startSec)} durationInFrames={durationInFrames - s(cta.startSec)} name="Endcard">
            {ctaOpaque ? <Endcard cta={cta} /> : <Cta cta={cta} />}
          </Sequence>
        </div>

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
