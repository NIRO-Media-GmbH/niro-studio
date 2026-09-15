// ============================================================
// Craiss Generation Logistik — "03 Viele Jahre, viele Geschichten"
// Satirisch/stereotypisch: mehrsprachige Begrüßung (PL/HU/RO/CZ),
// Kollegen-Aufzählung mit Flaggen (HU/CZ/RO/LT), polnischer Fluch
// bei ~28,5–29,2s (bleibt evtl. im Schnitt — kein Overlay dazu).
//
// Hook als LOWER-THIRD (Talking-Head-Opener) 0,24–2,72s.
// Flaggen-Reihe synchron zur Aufzählung 7,84–12,16s.
// CTA als OPAKE ENDCARD ab 40,84s: die Sprache läuft bis 40,8s und
// der letzte Shot (Büro ab 38,16s) ist ein Talking Head — es gibt
// keinen freien Endshot. Die Komposition verlängert das Video auf 46s.
//
// 9:16 portrait-4k (2160×3840), 25fps, 46s (Video: 40,76s / 1019 Frames).
// Schnittgrenzen vorn: 2,72 / 6,64 / 10,68 / 12,36s … letzter 38,16s.
// Gemeinsame Bausteine: ../../lib
// ============================================================

import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { CIProvider } from "../../../../core/ci-provider";
import { loadBrand } from "../../../../core/ci-loader";
import { projectPropsSchema } from "../../../../core/schemas";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import {
  Hook,
  Cta,
  FlagsRow,
  FootageCompare,
  hookSchema,
  ctaSchema,
  flagsSchema,
  footageSchema,
  CTA_TEXTS,
} from "../../lib";
import brandJson from "../../brand.json";
import { z } from "zod";

const ci = loadBrand("craiss", brandJson as any);

export const craissVieleJahreSchema = projectPropsSchema.extend({
  hook: hookSchema.describe("Hook"),
  flags: flagsSchema.describe("Flaggen (Kollegen-Aufzählung)"),
  cta: ctaSchema.describe("CTA (Endcard)"),
  footage: footageSchema.describe("Footage-Vergleich"),
});

export type CraissVieleJahreProps = z.infer<typeof craissVieleJahreSchema>;

// Stand 2026-09-11: Kunden-Schnitt V3 ohne Animation, 1291 Frames = 51,64s.
// Hook/Flaggen per Differenz gegen den animierten V3 bestätigt (unverändert),
// CTA liegt dort auf dem Drohnen-Endshot (Schnitt 46,68s) statt als Endcard
// hinter dem Video. Die Kopf-Angaben oben beziehen sich auf den alten V1.
const VIDEO_SECONDS = 51.64;

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
  hook: {
    headline: "VIELE JAHRE",
    chip: "VIELE GESCHICHTEN",
    startSec: 0.24,
    endSec: 2.72,
    offsetY: 0,
  },
  flags: {
    items: [
      { country: "HU" as const, label: "UNGARN", startSec: 7.84 },
      { country: "CZ" as const, label: "TSCHECHIEN", startSec: 8.64 },
      { country: "RO" as const, label: "RUMÄNIEN", startSec: 9.28 },
      // SRT sagt 9,76 — real beginnt das Wort nach einer Sprechpause erst
      // bei ~10,05–10,25 (Wellenform); Davids Feedback: 9,76 war zu früh.
      { country: "LT" as const, label: "LITAUEN", startSec: 10.08 },
    ],
    startSec: 7.84,
    // Litauen (ab 10,08) hält über den Schnitt bei 10,68 hinweg durch
    // „Alles." und geht während „Internationale" raus — im Close-up danach
    // bleibt das Kinn (~47%) knapp über der Flaggen-Oberkante (49%).
    endSec: 11.6,
    offsetY: 0,
  },
  cta: {
    ...CTA_TEXTS,
    startSec: 46.64,
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
  "projects/craiss-viele-jahre/ohne-Animation/proxy/03_Viele_Jahre_Viele_Geschichten_V3_ohneAnim_proxy.mp4";
const BASE_W = 1080;
const BASE_H = 1920;

export const CraissVieleJahre: React.FC<CraissVieleJahreProps> = ({
  review,
  hook,
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
        {/* Footage endet vor der Endcard — Sequence begrenzt auf Videolänge,
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
          <Sequence
            from={s(hook.startSec)}
            durationInFrames={s(hook.endSec) - s(hook.startSec)}
            name="Hook"
          >
            <Hook hook={hook} layout="lower" />
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
