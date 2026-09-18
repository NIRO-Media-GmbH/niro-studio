// ============================================================
// Craiss Generation Logistik — "03 Viele Jahre, viele Geschichten"
// Satirisch/stereotypisch: mehrsprachige Begrüßung (PL/HU/RO/CZ),
// Kollegen-Aufzählung mit Flaggen (HU/CZ/RO/LT), polnischer Fluch
// bei ~28,5–29,2s (bleibt evtl. im Schnitt — kein Overlay dazu).
//
// Seit 2026-09-16 (Kundenfeedback): Intro mit Flaggen-Wischern über das
// ganze Bild, groß HALLO + Begrüßung je Sprache, Titel-Chip „VIELE SPRACHEN.
// EIN TEAM." statt Hook „VIELE JAHRE / VIELE GESCHICHTEN". Die Begrüßungs-
// Montage ist im Schnitt (Resolve-Kopie „Claude 03 Begrüßung …") um D Frames
// länger; alles dahinter liegt + D. Schnittframes aus intro-layout.json.
//
// 9:16 portrait-4k (2160×3840), 25fps.
// Gemeinsame Bausteine: ../../lib, ../../intro
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  Cta,
  FlagsRow,
  FootageCompare,
  RedChip,
  chipSchema,
  ctaSchema,
  flagsSchema,
  footageSchema,
  CTA_TEXTS,
} from "../../lib";
import { GreetingIntro } from "../../intro/GreetingIntro";
import { introEndFrame, introLayoutSchema } from "../../intro/wipeTiming";
import brandJson from "../../brand.json";
import introJson from "./intro-layout.json";
import { z } from "zod";

const ci = loadBrand("craiss", brandJson as any);

const INTRO = introLayoutSchema.parse(introJson);
export const INTRO_SHIFT_FRAMES = INTRO.shiftFrames;
const SHIFT_SEC = INTRO.shiftFrames / INTRO.fps;
const r2 = (v: number) => Math.round(v * 100) / 100;

export const craissVieleJahreSchema = projectPropsSchema.extend({
  titleChip: chipSchema.describe("Titel-Chip nach der Begrüßung"),
  flags: flagsSchema.describe("Flaggen (Kollegen-Aufzählung)"),
  cta: ctaSchema.describe("CTA (Endcard)"),
  footage: footageSchema.describe("Footage-Vergleich"),
});

export type CraissVieleJahreProps = z.infer<typeof craissVieleJahreSchema>;

// Kunden-Schnitt V3 hatte 1291 Frames (51,64 s); die Kopie „Claude 03 Begrüßung"
// ist um D Frames länger (Begrüßungs-Montage mit Luft für die Wischer).
const VIDEO_SECONDS = (1291 + INTRO.shiftFrames) / INTRO.fps;
export const VIELE_JAHRE_SECONDS = VIDEO_SECONDS;

export const craissVieleJahreDefaults: CraissVieleJahreProps = {
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
  titleChip: {
    text: INTRO.titleChip.text,
    startSec: INTRO.titleChip.fromFrame / INTRO.fps,
    endSec: INTRO.titleChip.toFrame / INTRO.fps,
    offsetY: INTRO.titleChip.offsetY,
  },
  flags: {
    items: [
      { country: "HU" as const, label: "UNGARN", startSec: r2(7.84 + SHIFT_SEC) },
      { country: "CZ" as const, label: "TSCHECHIEN", startSec: r2(8.64 + SHIFT_SEC) },
      { country: "RO" as const, label: "RUMÄNIEN", startSec: r2(9.28 + SHIFT_SEC) },
      // SRT sagt 9,76 — real beginnt das Wort nach einer Sprechpause erst
      // bei ~10,05–10,25 (Wellenform); Davids Feedback: 9,76 war zu früh.
      { country: "LT" as const, label: "LITAUEN", startSec: r2(10.08 + SHIFT_SEC) },
    ],
    startSec: r2(7.84 + SHIFT_SEC),
    // Litauen hält über den Schnitt (alt 10,68) hinweg durch „Alles." und geht
    // während „Internationale" raus — im Close-up danach bleibt das Kinn (~47%)
    // knapp über der Flaggen-Oberkante (49%).
    endSec: r2(11.6 + SHIFT_SEC),
    offsetY: 0,
  },
  cta: {
    ...CTA_TEXTS,
    startSec: r2(46.64 + SHIFT_SEC),
    offsetY: 0,
  },
  footage: {
    showInStudio: true,
    simulateBlur: false,
    renderInExport: false,
  },
};

export const craissVieleJahrePreviewDefaults: CraissVieleJahreProps = {
  ...craissVieleJahreDefaults,
  transparent: false,
  footage: {
    showInStudio: true,
    simulateBlur: false,
    renderInExport: true,
  },
};

const FOOTAGE_SRC =
  "projects/craiss-viele-jahre/ohne-Animation/proxy/03_Viele_Jahre_Viele_Geschichten_Begruessung_ohneAnim_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

export const CraissVieleJahre: React.FC<CraissVieleJahreProps> = ({
  review,
  titleChip,
  flags,
  cta,
  footage,
}) => {
  const { fps, width, durationInFrames } = useVideoConfig();
  const s = (sec: number) => Math.round(sec * fps);
  const S = width / BASE_W;

  return (
    <CIProvider ci={ci}>
      <AbsoluteFill style={{ backgroundColor: "transparent" }}>
        {/* Footage endet mit dem Schnitt — Sequence begrenzt auf Videolänge,
            damit OffthreadVideo nie hinter das Medienende seekt. */}
        <Sequence from={0} durationInFrames={s(VIDEO_SECONDS)} name="Footage">
          <FootageCompare src={FOOTAGE_SRC} footage={footage} ctaStartSec={cta.startSec} />
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
          <Sequence from={0} durationInFrames={introEndFrame(INTRO)} name="Begrüßung + Flaggen-Wischer">
            <GreetingIntro layout={INTRO} />
          </Sequence>

          <Sequence
            from={s(titleChip.startSec)}
            durationInFrames={s(titleChip.endSec) - s(titleChip.startSec)}
            name="Titel-Chip"
          >
            <RedChip chip={titleChip} />
          </Sequence>

          <Sequence
            from={s(flags.startSec)}
            durationInFrames={s(flags.endSec) - s(flags.startSec)}
            name="Flaggen"
          >
            <FlagsRow flags={flags} />
          </Sequence>

          <Sequence
            from={s(cta.startSec)}
            durationInFrames={durationInFrames - s(cta.startSec)}
            name="CTA-Endcard"
          >
            {/* Transparent (Davids Wunsch) — Hintergrund macht er im Schnitt.
                Standard-Serien-CTA wie Video 01/02, liest sich auf jedem Grund. */}
            <Cta cta={cta} />
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
